from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import AuditLog, LearningResource, ModelVersion, QuestionBank, User
from app.deps import DB, Admin, Staff
from app.schemas.common import ORM, StaffCreateIn, UserOut
from app.services.governance import audit

router = APIRouter(prefix="/admin", tags=["admin"])


class AuditOut(ORM):
    id: int
    actor_id: int | None
    action: str
    target: str
    meta: dict[str, Any]
    created_at: Any


class ModelVersionOut(ORM):
    version: str
    metrics: dict[str, Any]
    data_hash: str
    is_active: bool
    created_at: Any


class QuestionIn(BaseModel):
    kind: str
    skill: str = ""
    category: str = "technical"
    difficulty: int = 1
    company_type: str = "any"
    prompt: str
    options: list[str] = []
    answer_index: int | None = None
    key_points: list[str] = []
    reference_answer: str = ""


class ResourceIn(BaseModel):
    skill: str
    title: str
    url: str
    kind: str = "article"
    minutes: int = 30


@router.post("/users", response_model=UserOut, status_code=201)
def create_staff(body: StaffCreateIn, actor: Admin, db: DB) -> User:
    if db.scalar(select(User).where(User.email == body.email.lower())):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")
    user = User(
        email=body.email.lower(),
        full_name=body.full_name,
        role=body.role,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    db.flush()
    audit(db, actor.id, "create_staff", f"user:{user.id}", role=body.role)
    db.commit()
    return user


@router.get("/audit", response_model=list[AuditOut])
def audit_log(actor: Admin, db: DB, limit: int = 200) -> list[AuditLog]:
    rows = list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 1000))))
    audit(db, actor.id, "read_audit_log")
    db.commit()
    return rows


@router.get("/models", response_model=list[ModelVersionOut])
def model_versions(_: Staff, db: DB) -> list[ModelVersion]:
    return list(db.scalars(select(ModelVersion).order_by(ModelVersion.id.desc())))


@router.post("/models/retrain", status_code=202)
def retrain(actor: Admin, db: DB) -> dict[str, str]:
    from app.workers.tasks import retrain_readiness

    audit(db, actor.id, "retrain_readiness")
    db.commit()
    return {"version": retrain_readiness()}


@router.post("/questions", status_code=201)
def add_question(body: QuestionIn, actor: Admin, db: DB) -> dict[str, int]:
    q = QuestionBank(**body.model_dump())
    db.add(q)
    db.flush()
    audit(db, actor.id, "add_question", f"question:{q.id}")
    db.commit()
    return {"id": q.id}


@router.post("/resources", status_code=201)
def add_resource(body: ResourceIn, actor: Admin, db: DB) -> dict[str, int]:
    r = LearningResource(**body.model_dump())
    db.add(r)
    db.flush()
    audit(db, actor.id, "add_resource", f"resource:{r.id}")
    db.commit()
    return {"id": r.id}
