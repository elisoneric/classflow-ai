from functools import lru_cache

from redis import Redis
from rq import Queue

from app.core.config import get_settings


@lru_cache
def get_redis_connection() -> Redis:
    return Redis.from_url(get_settings().redis_url)


@lru_cache
def get_queue() -> Queue:
    return Queue("default", connection=get_redis_connection())
