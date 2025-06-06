import asyncio
import os
import typing as tp
from functools import wraps

import orjson
from aioredis import Redis

from .utils import ttl_cache


# Caching decorator
T = tp.TypeVar("T")
P = tp.ParamSpec("P")

@ttl_cache
def load_cache():
    db: Redis = Redis.from_url(  # type: ignore
        os.environ["REDIS_URL"],
        max_connections=250,
        encoding="utf-8",
        decode_responses=False,  # for orjson
    )
    return db

def cache(ttl: int = 60 * 60 * 24 * 7):
    def decorator(func: tp.Callable[P, tp.Awaitable[T] | T]):
        db = load_cache()
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            key = f"{func.__module__}.{func.__qualname__}:{orjson.dumps({'args': args, 'kwargs': kwargs}).hex()}"
            cached = await db.get(key)  # type: ignore
            if cached is not None:
                return orjson.loads(cached)  # type: ignore

            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )
            await db.set(key, orjson.dumps(result), ex=ttl)  # type: ignore
            return result  # type: ignore
        return wrapper
    return decorator
