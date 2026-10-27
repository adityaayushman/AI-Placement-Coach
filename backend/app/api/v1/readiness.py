from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.db.models import ReadinessScore
from app.deps import DB, Student
from app.schemas.common import ORM
from app.services.aggregator import diff
from app.workers.tasks import rescore_student

router = APIRouter(prefix="/me/readiness", tags=["readiness"])


class ScoreOut(ORM):
    id: int
    score: float
    probability: float | None
    components: dict[str, Any]
    weights: dict[str, float]
    model_version: str
    attributions: list[dict[str, Any]]
    created_at: Any


class ReadinessOut(BaseModel):
    latest: ScoreOut | None
    history: list[dict[str, Any]]
    change: dict[str, Any]


@router.get("", response_model=ReadinessOut)
def get_readiness(user: Student, db: DB) -> ReadinessOut:
    rows = list(
        db.scalars(
            select(ReadinessScore)
            .where(ReadinessScore.user_id == user.id)
            .order_by(ReadinessScore.id.desc())
            .limit(60)
        )
    )
    if not rows:
        return ReadinessOut(latest=None, history=[], change={"score": None, "components": {}})
    return ReadinessOut(
        latest=ScoreOut.model_validate(rows[0]),
        history=[{"at": r.created_at.isoformat(), "score": r.score} for r in reversed(rows)],
        change=diff(rows[0], rows[1] if len(rows) > 1 else None),
    )


@router.post("/refresh", response_model=ReadinessOut)
def refresh(user: Student, db: DB) -> ReadinessOut:
    rescore_student(user.id)
    db.expire_all()
    return get_readiness(user, db)
