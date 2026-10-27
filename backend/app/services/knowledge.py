"""DB-facing side of mastery tracking and recommendations."""

from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.db.models import (
    LearningResource,
    Recommendation,
    ResumeAnalysis,
    SkillMastery,
    StudentProfile,
)
from app.ml.knowledge import bkt
from app.ml.knowledge.recommender import rank
from app.ml.resume.taxonomy import COMPANY_WEIGHTS, TAXONOMY, category_of


def mastery_map(db: Session, user_id: int) -> dict[str, float]:
    rows = db.scalars(select(SkillMastery).where(SkillMastery.user_id == user_id))
    return {r.skill: r.p_known for r in rows}


def observe(db: Session, user_id: int, skill: str, correct: bool) -> float:
    row = db.scalar(
        select(SkillMastery).where(SkillMastery.user_id == user_id, SkillMastery.skill == skill)
    )
    if row is None:
        row = SkillMastery(user_id=user_id, skill=skill, p_known=bkt.DEFAULT.p_init, n_obs=0)
        db.add(row)
    row.p_known = bkt.update(row.p_known, correct)
    row.n_obs += 1
    row.updated_at = utcnow()
    return row.p_known


def nudge(db: Session, user_id: int, skill: str) -> None:
    row = db.scalar(
        select(SkillMastery).where(SkillMastery.user_id == user_id, SkillMastery.skill == skill)
    )
    if row is None:
        row = SkillMastery(user_id=user_id, skill=skill, p_known=bkt.DEFAULT.p_init, n_obs=0)
        db.add(row)
    row.p_known = bkt.learn_only(row.p_known)
    row.updated_at = utcnow()


def target_skills(company_type: str) -> list[str]:
    """Skills from categories the company type weights at least moderately."""
    weights = COMPANY_WEIGHTS.get(company_type, COMPANY_WEIGHTS["product"])
    return [s for s in TAXONOMY if weights.get(category_of(s), 0) >= 0.5]


def refresh_recommendations(db: Session, user_id: int) -> list[Recommendation]:
    profile = db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    company_type = profile.target_company_type if profile else "product"
    latest = db.scalar(
        select(ResumeAnalysis)
        .where(ResumeAnalysis.user_id == user_id)
        .order_by(ResumeAnalysis.id.desc())
        .limit(1)
    )
    gaps = {g["skill"] for g in latest.skill_gaps} if latest else set()
    # From recommendation rows rather than `events`, so the loop works without analytics consent.
    ignored = Counter(
        db.scalars(
            select(Recommendation.skill).where(
                Recommendation.user_id == user_id, Recommendation.status == "ignored"
            )
        )
    )
    ranked = rank(
        mastery_map(db, user_id),
        list(gaps) + target_skills(company_type),
        company_type,
        resume_gaps=gaps,
        ignored={k: v for k, v in ignored.items() if k},
    )
    # Replace open items; keep accepted/completed/ignored history.
    for rec in db.scalars(
        select(Recommendation).where(
            Recommendation.user_id == user_id, Recommendation.status == "open"
        )
    ):
        db.delete(rec)
    out = []
    for r in ranked:
        resource = db.scalar(
            select(LearningResource).where(LearningResource.skill == r.skill).limit(1)
        )
        rec = Recommendation(
            user_id=user_id,
            skill=r.skill,
            resource_id=resource.id if resource else None,
            reason=r.reason,
            priority=round(r.priority, 4),
        )
        db.add(rec)
        out.append(rec)
    db.flush()
    return out
