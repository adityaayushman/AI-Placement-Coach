"""RQ worker entrypoint. No tasks are registered yet (first ones arrive in Phase 2)."""

from redis import Redis
from rq import Queue, Worker

from app.config import get_settings


def main() -> None:
    conn = Redis.from_url(get_settings().redis_url)
    Worker([Queue("default", connection=conn)], connection=conn).work()


if __name__ == "__main__":
    main()
