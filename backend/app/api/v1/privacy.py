"""Consent management and the student's data rights: view, export, delete everything."""

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Response
from sqlalchemy import delete, select

from app.db.models import USER_OWNED, InterviewAnswer, InterviewSession, Resume, User
from app.deps import DB, CurrentUser, Student
from app.schemas.common import ConsentIn, ConsentState
from app.services.governance import SCOPES, audit, current_consents, set_consent
from app.services.storage import get_storage

router = APIRouter(tags=["privacy"])


@router.get("/consents", response_model=list[ConsentState])
def list_consents(user: CurrentUser, db: DB) -> list[ConsentState]:
    state = current_consents(db, user.id)
    return [ConsentState(scope=s, description=d, granted=state[s]) for s, d in SCOPES.items()]


@router.put("/consents", response_model=list[ConsentState])
def update_consents(body: list[ConsentIn], user: Student, db: DB) -> list[ConsentState]:
    for item in body:
        set_consent(db, user.id, item.scope, item.granted)
    db.commit()
    return list_consents(user, db)


def _row_dict(row: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in row.__table__.columns:
        value = getattr(row, col.name)
        out[col.name] = value.isoformat() if hasattr(value, "isoformat") else value
    return out


def collect_user_data(db: DB, user: User) -> dict[str, list[dict[str, Any]]]:
    data: dict[str, list[dict[str, Any]]] = {
        "user": [{"id": user.id, "email": user.email, "full_name": user.full_name}]
    }
    for model in USER_OWNED:
        rows = db.scalars(select(model).where(model.user_id == user.id)).all()  # type: ignore[attr-defined]
        data[model.__tablename__] = [_row_dict(r) for r in rows]
    session_ids = [s["id"] for s in data["interview_sessions"]]
    answers = db.scalars(
        select(InterviewAnswer).where(InterviewAnswer.session_id.in_(session_ids))
    ).all()
    data["interview_answers"] = [_row_dict(a) for a in answers]
    return data


@router.get("/me/export")
def export_my_data(user: Student, db: DB, format: str = "json") -> Response:
    data = collect_user_data(db, user)
    audit(db, user.id, "data_export", f"user:{user.id}", format=format)
    db.commit()
    if format == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["table", "field", "value", "row"])
        for table, rows in data.items():
            for i, row in enumerate(rows):
                for field, value in row.items():
                    writer.writerow([table, field, value, i])
        return Response(
            buf.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=my-data.csv"},
        )
    return Response(
        json.dumps(data, default=str, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=my-data.json"},
    )


@router.delete("/me", status_code=204)
def delete_my_data(user: Student, db: DB) -> None:
    """Hard delete: every row keyed to the student, uploaded files, then the account."""
    storage = get_storage()
    paths = list(db.scalars(select(Resume.storage_path).where(Resume.user_id == user.id)))
    session_ids = list(
        db.scalars(select(InterviewSession.id).where(InterviewSession.user_id == user.id))
    )
    paths += [
        p
        for p in db.scalars(
            select(InterviewAnswer.audio_path).where(InterviewAnswer.session_id.in_(session_ids))
        )
        if p
    ]
    db.execute(delete(InterviewAnswer).where(InterviewAnswer.session_id.in_(session_ids)))
    for model in USER_OWNED:
        db.execute(delete(model).where(model.user_id == user.id))  # type: ignore[attr-defined]
    audit(db, None, "student_deleted_all_data", f"user:{user.id}", files=len(paths))
    db.delete(user)
    db.commit()
    for path in paths:
        storage.delete(path)
