"""Continuous-improvement loop: any new student data schedules a readiness rescore.

With JOBS_INLINE the job runs in-process (tests, single-box demo); otherwise it is queued on RQ
and picked up by the worker. Failures to enqueue fall back to inline so data is never stale."""

import logging

from app.config import get_settings

log = logging.getLogger(__name__)


def request_rescore(user_id: int) -> None:
    if get_settings().jobs_inline:
        from app.workers.tasks import rescore_student

        rescore_student(user_id)
        return
    try:
        from redis import Redis
        from rq import Queue

        conn = Redis.from_url(get_settings().redis_url, socket_connect_timeout=1)
        Queue("default", connection=conn).enqueue(
            "app.workers.tasks.rescore_student", user_id, job_timeout=120
        )
    except Exception:
        log.warning("enqueue failed; rescoring inline")
        from app.workers.tasks import rescore_student

        rescore_student(user_id)
