"""Composite Placement Readiness Score (0-100) and the feature vector behind it."""

from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.db.models import (
    AssessmentAttempt,
    Certification,
    CodingActivity,
    Event,
    InterviewAnswer,
    InterviewSession,
    Project,
    ReadinessScore,
    ResumeAnalysis,
    StudentProfile,
)
from app.ml.readiness import model as readiness
from app.ml.resume.taxonomy import skill_weight
from app.services.knowledge import mastery_map, target_skills

# Weights per company type; stored with every score for auditability.
WEIGHTS: dict[str, dict[str, float]] = {
    "product": {
        "predictor": 0.30,
        "resume": 0.15,
        "mastery": 0.25,
        "interview": 0.15,
        "consistency": 0.15,
    },
    "service": {
        "predictor": 0.30,
        "resume": 0.15,
        "mastery": 0.20,
        "interview": 0.20,
        "consistency": 0.15,
    },
}


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def build_features(db: Session, user_id: int) -> tuple[dict[str, float | None], dict[str, Any]]:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    company_type = profile.target_company_type if profile else "product"
    projects = list(db.scalars(select(Project).where(Project.user_id == user_id)))
    coding = list(db.scalars(select(CodingActivity).where(CodingActivity.user_id == user_id)))
    attempts = list(
        db.scalars(select(AssessmentAttempt.score).where(AssessmentAttempt.user_id == user_id))
    )
    analysis = db.scalar(
        select(ResumeAnalysis)
        .where(ResumeAnalysis.user_id == user_id)
        .order_by(ResumeAnalysis.id.desc())
        .limit(1)
    )
    answers = [
        a.scores.get("overall", 0)
        for a in db.scalars(
            select(InterviewAnswer)
            .join(InterviewSession)
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewAnswer.id.desc())
            .limit(10)
        )
    ]
    certs = (
        db.scalar(
            select(func.count()).select_from(Certification).where(Certification.user_id == user_id)
        )
        or 0
    )
    ratings = [c.contest_rating for c in coding if c.contest_rating]

    features: dict[str, float | None] = {
        "cgpa": profile.cgpa if profile else None,
        "backlogs": float(profile.backlogs) if profile else None,
        "tenth_pct": profile.tenth_pct if profile else None,
        "twelfth_pct": profile.twelfth_pct if profile else None,
        "internships": float(profile.internships) if profile else None,
        "project_count": float(len(projects)),
        "project_complexity": _mean([float(p.complexity) for p in projects]),
        "certifications": float(certs),
        # Platforms report cumulative totals; take the max entry per platform.
        "problems_solved": float(
            sum(
                max(c.problems_solved for c in coding if c.platform == plat)
                for plat in {c.platform for c in coding}
            )
        ),
        "quiz_avg": _mean(list(attempts)),
        "resume_score": analysis.ats_score if analysis else None,
        "interview_avg": _mean(answers),
        "company_type_product": 1.0 if company_type == "product" else 0.0,
    }
    context = {
        "company_type": company_type,
        "max_contest_rating": max(ratings) if ratings else None,
        "resume_keyword_coverage": (analysis.ats_report or {}).get("keyword_coverage")
        if analysis
        else None,
    }
    return features, context


def _consistency(db: Session, user_id: int) -> float | None:
    since = utcnow() - timedelta(days=28)
    stamps = list(
        db.scalars(
            select(Event.created_at).where(Event.user_id == user_id, Event.created_at >= since)
        )
    )
    stamps += list(
        db.scalars(
            select(AssessmentAttempt.created_at).where(
                AssessmentAttempt.user_id == user_id, AssessmentAttempt.created_at >= since
            )
        )
    )
    if not stamps:
        return None
    active_days = len({s.date() for s in stamps})
    return min(100.0, active_days / 12 * 100)  # ~3 active days a week = full marks


def compute(db: Session, user_id: int) -> ReadinessScore:
    features, ctx = build_features(db, user_id)
    company_type = ctx["company_type"]
    pred = readiness.predict(features)

    mastery = mastery_map(db, user_id)
    observed = [s for s in target_skills(company_type) if s in mastery]
    mastery_score = (
        100
        * sum(mastery[s] * skill_weight(s, company_type) for s in observed)
        / sum(skill_weight(s, company_type) for s in observed)
        if observed
        else None
    )
    resume = features["resume_score"]
    if resume is not None and ctx["resume_keyword_coverage"] is not None:
        resume = 0.6 * resume + 40 * ctx["resume_keyword_coverage"]

    components: dict[str, float | None] = {
        "predictor": 100 * pred["probability"],
        "resume": resume,
        "mastery": mastery_score,
        "interview": features["interview_avg"],
        "consistency": _consistency(db, user_id),
    }
    base = WEIGHTS[company_type]
    present = {k: v for k, v in components.items() if v is not None}
    total_w = sum(base[k] for k in present)
    weights = {k: round(base[k] / total_w, 4) for k in present}
    score = round(sum(weights[k] * present[k] for k in present), 1)

    row = ReadinessScore(
        user_id=user_id,
        score=score,
        probability=pred["probability"],
        components={
            "values": {k: (round(v, 1) if v is not None else None) for k, v in components.items()},
            "missing": [k for k, v in components.items() if v is None],
            "company_type": company_type,
            "features": features,
            "data_source": pred["data_source"],
        },
        weights=weights,
        model_version=pred["model_version"],
        attributions=pred["attributions"][:8],
    )
    db.add(row)
    db.flush()
    return row


def diff(current: ReadinessScore, previous: ReadinessScore | None) -> dict[str, Any]:
    if previous is None:
        return {"score": None, "components": {}}
    cur, prev = current.components["values"], previous.components["values"]
    return {
        "score": round(current.score - previous.score, 1),
        "components": {
            k: round(cur[k] - prev[k], 1)
            for k in cur
            if cur.get(k) is not None and prev.get(k) is not None and abs(cur[k] - prev[k]) >= 0.1
        },
    }
