"""Assessments (quiz engine), mastery and recommendations: Phases 3 and 6."""

from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.db.base import utcnow
from app.db.models import (
    Assessment,
    AssessmentAttempt,
    LearningResource,
    QuestionBank,
    Recommendation,
    SkillMastery,
)
from app.deps import DB, CurrentUser, Student
from app.schemas.common import ORM
from app.services.governance import log_event
from app.services.knowledge import nudge, observe, refresh_recommendations
from app.services.rescoring import request_rescore

router = APIRouter(tags=["learning"])


class QuestionOut(ORM):
    id: int
    skill: str
    difficulty: int
    prompt: str
    options: list[str]


class AssessmentOut(ORM):
    id: int
    title: str
    skill: str


class AssessmentDetail(AssessmentOut):
    questions: list[QuestionOut]


class AttemptIn(BaseModel):
    answers: dict[int, int]  # question_id -> chosen option index


class AttemptOut(ORM):
    id: int
    assessment_id: int
    score: float
    correct: dict[str, bool]


class MasteryOut(ORM):
    skill: str
    p_known: float
    n_obs: int


class ResourceOut(ORM):
    id: int
    title: str
    url: str
    kind: str
    minutes: int


class RecommendationOut(ORM):
    id: int
    skill: str
    reason: str
    priority: float
    status: str
    resource: ResourceOut | None = None


class RecStatusIn(BaseModel):
    status: Literal["accepted", "ignored", "completed"]


@router.get("/assessments", response_model=list[AssessmentOut])
def list_assessments(db: DB, _: CurrentUser) -> list[Assessment]:
    return list(db.scalars(select(Assessment).order_by(Assessment.id)))


@router.get("/assessments/{aid}", response_model=AssessmentDetail)
def get_assessment(aid: int, db: DB, _: CurrentUser) -> AssessmentDetail:
    a = db.get(Assessment, aid)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    qs = db.scalars(select(QuestionBank).where(QuestionBank.id.in_(a.question_ids))).all()
    return AssessmentDetail(
        id=a.id,
        title=a.title,
        skill=a.skill,
        questions=[QuestionOut.model_validate(q) for q in qs],
    )


@router.post("/assessments/{aid}/attempts", response_model=AttemptOut, status_code=201)
def submit_attempt(aid: int, body: AttemptIn, user: Student, db: DB) -> AssessmentAttempt:
    a = db.get(Assessment, aid)
    if a is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    qs = db.scalars(select(QuestionBank).where(QuestionBank.id.in_(a.question_ids))).all()
    correct: dict[str, bool] = {}
    for q in qs:
        ok = body.answers.get(q.id) == q.answer_index
        correct[str(q.id)] = ok
        observe(db, user.id, q.skill or a.skill, ok)
    score = round(100 * sum(correct.values()) / len(qs), 1) if qs else 0.0
    attempt = AssessmentAttempt(
        user_id=user.id,
        assessment_id=aid,
        answers={str(k): v for k, v in body.answers.items()},
        correct=correct,
        score=score,
    )
    db.add(attempt)
    log_event(db, user.id, "assessment_attempted", assessment_id=aid, skill=a.skill, score=score)
    refresh_recommendations(db, user.id)
    db.commit()
    request_rescore(user.id)
    return attempt


@router.get("/me/attempts", response_model=list[AttemptOut])
def my_attempts(user: Student, db: DB) -> list[AssessmentAttempt]:
    return list(
        db.scalars(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.user_id == user.id)
            .order_by(AssessmentAttempt.id.desc())
        )
    )


@router.get("/me/mastery", response_model=list[MasteryOut])
def my_mastery(user: Student, db: DB) -> list[SkillMastery]:
    return list(
        db.scalars(
            select(SkillMastery).where(SkillMastery.user_id == user.id).order_by(SkillMastery.skill)
        )
    )


def _with_resource(db: DB, rec: Recommendation) -> RecommendationOut:
    out = RecommendationOut.model_validate(rec)
    if rec.resource_id:
        res = db.get(LearningResource, rec.resource_id)
        out.resource = ResourceOut.model_validate(res) if res else None
    return out


@router.get("/me/recommendations", response_model=list[RecommendationOut])
def my_recommendations(user: Student, db: DB) -> list[RecommendationOut]:
    recs = list(
        db.scalars(
            select(Recommendation)
            .where(
                Recommendation.user_id == user.id, Recommendation.status.in_(["open", "accepted"])
            )
            .order_by(Recommendation.priority.desc())
        )
    )
    if not recs:
        recs = refresh_recommendations(db, user.id)
        db.commit()
    return [_with_resource(db, r) for r in recs]


@router.patch("/me/recommendations/{rid}", response_model=RecommendationOut)
def update_recommendation(rid: int, body: RecStatusIn, user: Student, db: DB) -> RecommendationOut:
    rec = db.get(Recommendation, rid)
    if rec is None or rec.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    rec.status = body.status
    rec.updated_at = utcnow()
    log_event(db, user.id, f"recommendation_{body.status}", skill=rec.skill, rec_id=rec.id)
    if body.status == "completed":
        nudge(db, user.id, rec.skill)
    if body.status in ("completed", "ignored"):
        db.flush()
        refresh_recommendations(db, user.id)
    db.commit()
    return _with_resource(db, rec)
