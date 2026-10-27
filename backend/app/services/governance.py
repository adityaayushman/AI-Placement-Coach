"""Consent, audit and event helpers shared by every module."""

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuditLog, Consent, Event

CONSENT_VERSION = "2026-10"
SCOPES = {
    "resume": "Store and analyse my resume.",
    "interview_recording": "Record and analyse my mock-interview audio.",
    "face_analysis": "Read face position and eye contact from my camera during mock interviews. "
    "Video stays in my browser; only summary numbers are sent.",
    "analytics": "Log my in-app activity to personalise recommendations.",
    "coordinator_visibility": "Let placement coordinators see my individual results.",
}


def current_consents(db: Session, user_id: int) -> dict[str, bool]:
    rows = db.scalars(select(Consent).where(Consent.user_id == user_id).order_by(Consent.id)).all()
    state = dict.fromkeys(SCOPES, False)
    for row in rows:
        state[row.scope] = row.granted
    return state


def has_consent(db: Session, user_id: int, scope: str) -> bool:
    return current_consents(db, user_id).get(scope, False)


def require_consent(db: Session, user_id: int, scope: str) -> None:
    if not has_consent(db, user_id, scope):
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"Consent '{scope}' not granted")


def set_consent(db: Session, user_id: int, scope: str, granted: bool) -> None:
    if scope not in SCOPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown scope '{scope}'")
    db.add(Consent(user_id=user_id, scope=scope, granted=granted, version=CONSENT_VERSION))


def audit(db: Session, actor_id: int | None, action: str, target: str = "", **meta: Any) -> None:
    db.add(AuditLog(actor_id=actor_id, action=action, target=target, meta=meta))


def log_event(db: Session, user_id: int, type_: str, **payload: Any) -> bool:
    """Append to the interaction log only when the student allows analytics."""
    if not has_consent(db, user_id, "analytics"):
        return False
    db.add(Event(user_id=user_id, type=type_, payload=payload))
    return True
