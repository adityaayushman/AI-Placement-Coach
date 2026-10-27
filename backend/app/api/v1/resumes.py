from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import JobDescription, Resume, ResumeAnalysis
from app.deps import DB, CurrentUser, Staff, Student
from app.ml.resume.analyzer import analyze
from app.ml.resume.parsing import ParseError, detect_sections, extract_text
from app.schemas.common import ORM
from app.services.governance import log_event, require_consent
from app.services.rescoring import request_rescore
from app.services.scanning import ensure_clean
from app.services.storage import get_storage

router = APIRouter(tags=["resumes"])


class ResumeOut(ORM):
    id: int
    filename: str
    version: int
    sections: dict[str, str]


class AnalysisOut(ORM):
    id: int
    resume_id: int
    jd_id: int | None
    ats_score: float
    ats_report: dict[str, Any]
    match_scores: dict[str, Any]
    skill_gaps: list[dict[str, Any]]
    skills_found: list[str]


class JDIn(BaseModel):
    company: str
    role: str
    type: str = "product"
    text: str
    required_skills: list[dict[str, Any]] = []


class JDOut(JDIn, ORM):
    id: int


async def read_upload(file: UploadFile, allowed: set[str]) -> tuple[str, bytes]:
    limit = get_settings().upload_max_mb * 1024 * 1024
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, f"Allowed: {sorted(allowed)}")
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large")
    if not data:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty file")
    ensure_clean(data)
    return suffix, data


@router.post("/resumes", response_model=AnalysisOut, status_code=201)
async def upload_resume(
    file: UploadFile, user: Student, db: DB, jd_id: int | None = Form(default=None)
) -> ResumeAnalysis:
    require_consent(db, user.id, "resume")
    suffix, data = await read_upload(file, {".pdf", ".docx", ".txt"})
    try:
        text = extract_text(suffix, data)
    except ParseError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from None
    version = db.scalar(select(func.max(Resume.version)).where(Resume.user_id == user.id)) or 0
    resume = Resume(
        user_id=user.id,
        filename=Path(file.filename or "resume").name[:200],
        storage_path=get_storage().save(data, suffix),
        parsed_text=text,
        sections=detect_sections(text),
        version=version + 1,
    )
    db.add(resume)
    db.flush()
    analysis = _analyze(db, user.id, resume, jd_id)
    log_event(db, user.id, "resume_uploaded", version=resume.version, ats=analysis.ats_score)
    db.commit()
    request_rescore(user.id)
    return analysis


def _analyze(db: DB, user_id: int, resume: Resume, jd_id: int | None) -> ResumeAnalysis:
    jd = db.get(JobDescription, jd_id) if jd_id else None
    if jd_id and jd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job description not found")
    jd_dict = (
        {
            "company": jd.company,
            "type": jd.type,
            "text": jd.text,
            "required_skills": jd.required_skills,
        }
        if jd
        else None
    )
    report = analyze(resume.parsed_text, jd_dict)
    analysis = ResumeAnalysis(
        user_id=user_id,
        resume_id=resume.id,
        jd_id=jd.id if jd else None,
        ats_score=report["ats_score"],
        ats_report={
            k: report[k] for k in ("ats_checks", "fixes", "sections", "embedder", "skill_evidence")
        }
        | {"keyword_coverage": report.get("keyword_coverage")},
        match_scores=report.get("match_scores", {}),
        skill_gaps=report.get("skill_gaps", []),
        skills_found=report["skills_found"],
    )
    db.add(analysis)
    db.flush()
    return analysis


@router.post("/resumes/{resume_id}/analyze", response_model=AnalysisOut, status_code=201)
def reanalyze(resume_id: int, user: Student, db: DB, jd_id: int | None = None) -> ResumeAnalysis:
    require_consent(db, user.id, "resume")
    resume = db.get(Resume, resume_id)
    if resume is None or resume.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Resume not found")
    analysis = _analyze(db, user.id, resume, jd_id)
    db.commit()
    request_rescore(user.id)
    return analysis


@router.get("/resumes", response_model=list[ResumeOut])
def list_resumes(user: Student, db: DB) -> list[Resume]:
    require_consent(db, user.id, "resume")
    return list(db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.id)))


@router.get("/resumes/analyses/latest", response_model=AnalysisOut | None)
def latest_analysis(user: Student, db: DB) -> ResumeAnalysis | None:
    require_consent(db, user.id, "resume")
    return db.scalar(
        select(ResumeAnalysis)
        .where(ResumeAnalysis.user_id == user.id)
        .order_by(ResumeAnalysis.id.desc())
        .limit(1)
    )


@router.get("/jobs", response_model=list[JDOut])
def list_jobs(db: DB, _: CurrentUser) -> list[JobDescription]:
    return list(db.scalars(select(JobDescription).order_by(JobDescription.company)))


@router.post("/jobs", response_model=JDOut, status_code=201)
def create_job(body: JDIn, _: Staff, db: DB) -> JobDescription:
    jd = JobDescription(**body.model_dump())
    db.add(jd)
    db.commit()
    return jd


@router.delete("/jobs/{jd_id}", status_code=204)
def delete_job(jd_id: int, _: Staff, db: DB) -> None:
    jd = db.get(JobDescription, jd_id)
    if jd is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(jd)
    db.commit()
