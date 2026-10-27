"""Background jobs (run by RQ, or inline when JOBS_INLINE is set)."""

import logging

from app.db.models import User
from app.db.session import get_sessionmaker

log = logging.getLogger(__name__)


def rescore_student(user_id: int) -> float | None:
    from app.services.aggregator import compute

    with get_sessionmaker()() as db:
        user = db.get(User, user_id)
        if user is None or user.role != "student":
            return None
        row = compute(db, user_id)
        db.commit()
        log.info("rescored user=%s score=%s model=%s", user_id, row.score, row.model_version)
        return row.score


def retrain_readiness(csv_path: str | None = None) -> str:
    from app.services.training import train_and_register

    return train_and_register(csv_path)
