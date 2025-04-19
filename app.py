import asyncio
import os
import random
import typing as tp
from functools import wraps

import orjson
from aioredis import Redis
from dotenv import load_dotenv

from quipubase.collection import Collection

load_dotenv()

# Redis connection
_db: Redis = Redis.from_url(
    os.environ["REDIS_URL"],
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
            cached = await _db.get(key)
            if cached is not None:
                return orjson.loads(cached)

            result = (
                await func(*args, **kwargs)
                if asyncio.iscoroutinefunction(func)
                else func(*args, **kwargs)
            )
            await _db.set(key, orjson.dumps(result), ex=ttl)
            return result

        return wrapper

    return decorator


# PubSub infrastructure
C = tp.TypeVar("C", bound=Collection)


class PubSub(tp.Generic[C]):
    _model: tp.Type[C]
    _pubsub = _db.pubsub()

    @classmethod
    def __class_getitem__(cls, collection: tp.Type[C]):
        cls._model = collection
        return cls

    async def pub(self, channel: str, data: C) -> None:
        await _db.publish(channel, data.model_dump_json())

    async def sub(self, channel: str) -> tp.AsyncGenerator[C, None]:
        await self._pubsub.subscribe(channel)
        while True:
            msg = await self._pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if msg and msg["type"] == "message":
                try:
                    yield self._model.model_validate_json(msg["data"])
                except Exception:
                    continue
            await asyncio.sleep(0.01)


# Example Collection
class Point(Collection):
    x: int
    y: int


def create_point() -> Point:
    return Point(x=random.randint(0, 100), y=random.randint(0, 100))


# Typed PubSub instance
class PointPubSub(PubSub[Point]):
    pass


# Demo test
async def main():
    ps = PointPubSub()
    channel = "points"

    async def publisher():
        for _ in range(1000):
            await asyncio.sleep(1)
            point = create_point()
            await ps.pub(channel, point)
            print("[PUBLISH]", point.model_dump())

    async def subscriber():
        async for point in ps.sub(channel):
            print("[SUBSCRIBE]", point.model_dump())

    await asyncio.gather(
        publisher(),
        subscriber(),
    )


if __name__ == "__main__":
    asyncio.run(main())
