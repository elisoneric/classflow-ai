"""RQ worker entrypoint. Run with: python worker.py (see docker-compose.yml)."""

from rq import Worker

from app.core.logging import configure_logging
from app.infrastructure.jobs.queue import get_queue, get_redis_connection

if __name__ == "__main__":
    configure_logging()
    worker = Worker([get_queue()], connection=get_redis_connection())
    worker.work()
