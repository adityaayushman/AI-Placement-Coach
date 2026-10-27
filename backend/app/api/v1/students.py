"""Student-owned profile and activity data (Phase 1 profile, Phase 3 activity)."""

import csv
import io
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, status
from sqlalchemy import select

from app.db.base import Base
from app.db.models import AcademicRecord, Certification, CodingActivity, Project, StudentProfile
from app.deps import DB, Student
from app.schemas.common import (
    AcademicIn,
    AcademicOut,
    CertificationIn,
    CertificationOut,
    CodingIn,
    CodingOut,
    ProfileIn,
    ProfileOut,
    ProjectIn,
    ProjectOut,
)
from app.services import academics
from app.services.governance import log_event
from app.services.rescoring import request_rescore

router = APIRouter(prefix="/me", tags=["students"])


def get_profile(db: DB, user_id: int) -> StudentProfile:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    if profile is None:
        profile = StudentProfile(user_id=user_id)
        db.add(profile)
        db.flush()
    return profile


@router.get("/profile", response_model=ProfileOut)
def read_profile(user: Student, db: DB) -> StudentProfile:
    profile = get_profile(db, user.id)
    db.commit()
    return profile


@router.put("/profile", response_model=ProfileOut)
def update_profile(body: ProfileIn, user: Student, db: DB) -> StudentProfile:
    profile = get_profile(db, user.id)
    for key, value in body.model_dump().items():
        setattr(profile, key, value)
    log_event(db, user.id, "profile_updated")
    db.commit()
    request_rescore(user.id)
    return profile


def _list(db: DB, model: type[Any], user_id: int) -> list[Any]:
    return list(db.scalars(select(model).where(model.user_id == user_id).order_by(model.id)))


def _create(db: DB, model: type[Base], user_id: int, data: dict[str, Any], event: str) -> Any:
    row = model(user_id=user_id, **data)
    db.add(row)
    log_event(db, user_id, event, **{k: v for k, v in data.items() if k != "description"})
    db.commit()
    request_rescore(user_id)
    return row


def _delete(db: DB, model: type[Any], user_id: int, row_id: int) -> None:
    row = db.get(model, row_id)
    if row is None or row.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    db.delete(row)
    db.commit()
    request_rescore(user_id)


@router.get("/academics", response_model=list[AcademicOut])
def list_academics(user: Student, db: DB) -> list[Any]:
    return _list(db, AcademicRecord, user.id)


@router.post("/academics", response_model=AcademicOut, status_code=201)
def add_academic(body: AcademicIn, user: Student, db: DB) -> Any:
    return _create(db, AcademicRecord, user.id, body.model_dump(), "academic_added")


@router.delete("/academics/{row_id}", status_code=204)
def delete_academic(row_id: int, user: Student, db: DB) -> None:
    _delete(db, AcademicRecord, user.id, row_id)


@router.get("/coding", response_model=list[CodingOut])
def list_coding(user: Student, db: DB) -> list[Any]:
    return _list(db, CodingActivity, user.id)


@router.post("/coding", response_model=CodingOut, status_code=201)
def add_coding(body: CodingIn, user: Student, db: DB) -> Any:
    return _create(db, CodingActivity, user.id, body.model_dump(), "coding_logged")


@router.post("/coding/import", response_model=list[CodingOut], status_code=201)
async def import_coding(file: UploadFile, user: Student, db: DB) -> list[Any]:
    """CSV with header: platform,problems_solved[,contest_rating]."""
    raw = await file.read(256 * 1024 + 1)
    if len(raw) > 256 * 1024:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "CSV larger than 256 KB")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        items = [
            CodingIn(
                platform=r["platform"],
                problems_solved=int(r["problems_solved"]),
                contest_rating=int(r["contest_rating"]) if r.get("contest_rating") else None,
            )
            for r in reader
        ]
    except (KeyError, ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Bad CSV: {exc}") from None
    rows = [CodingActivity(user_id=user.id, **i.model_dump()) for i in items[:500]]
    db.add_all(rows)
    log_event(db, user.id, "coding_imported", rows=len(rows))
    db.commit()
    request_rescore(user.id)
    return rows


@router.post("/academics/import", response_model=list[AcademicOut], status_code=201)
async def import_academics(file: UploadFile, user: Student, db: DB) -> list[Any]:
    """CSV with header: term,gpa[,backlogs]. Updates CGPA and backlogs on the profile."""
    rows = await academics.read_csv(file)
    items = [academics.parse_row(r, i) for i, r in enumerate(rows[:100], start=2)]
    if not items:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "CSV has no rows")
    created = academics.apply(db, user.id, items)
    log_event(db, user.id, "academics_imported", rows=len(created))
    db.commit()
    request_rescore(user.id)
    return created


@router.delete("/coding/{row_id}", status_code=204)
def delete_coding(row_id: int, user: Student, db: DB) -> None:
    _delete(db, CodingActivity, user.id, row_id)


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(user: Student, db: DB) -> list[Any]:
    return _list(db, Project, user.id)


@router.post("/projects", response_model=ProjectOut, status_code=201)
def add_project(body: ProjectIn, user: Student, db: DB) -> Any:
    return _create(db, Project, user.id, body.model_dump(), "project_added")


@router.delete("/projects/{row_id}", status_code=204)
def delete_project(row_id: int, user: Student, db: DB) -> None:
    _delete(db, Project, user.id, row_id)


@router.get("/certifications", response_model=list[CertificationOut])
def list_certifications(user: Student, db: DB) -> list[Any]:
    return _list(db, Certification, user.id)


@router.post("/certifications", response_model=CertificationOut, status_code=201)
def add_certification(body: CertificationIn, user: Student, db: DB) -> Any:
    return _create(db, Certification, user.id, body.model_dump(), "certification_added")


@router.delete("/certifications/{row_id}", status_code=204)
def delete_certification(row_id: int, user: Student, db: DB) -> None:
    _delete(db, Certification, user.id, row_id)
