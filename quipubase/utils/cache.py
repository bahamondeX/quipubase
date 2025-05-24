import os
import asyncio
import typing as tp
from functools import wraps

import orjson
from aioredis import Redis


# Redis connection
db: Redis = Redis.from_url(  # type: ignore
    os.getenv("REDIS_URL") or "redis://localhost:6379",
    max_connections=250,
    encoding="utf-8",
    decode_responses=False,  # for orjson
)

# Caching decorator
T = tp.TypeVar("T")
P = tp.ParamSpec("P")


def cache(ttl: int = 60 * 60 * 24 * 7):
    def decorator(func: tp.Callable[P, tp.Awaitable[T] | T]):
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
