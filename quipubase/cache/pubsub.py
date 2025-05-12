import asyncio
import typing as tp

from quipubase.data.collection import Collection
from quipubase.data.event import EventType

from .cache import _db  # type: ignore

T = tp.TypeVar("T", bound=Collection)


class PubSub(tp.Generic[T]):
    _model: type[T]
    _pubsub = _db.pubsub()  # type: ignore

    @classmethod
    def __class_getitem__(cls, model: type[T]):
        cls._model = model
        return cls

    async def pub(self, channel: str, event: EventType[T]) -> None:
        """Publish a strongly typed Event[T]"""
        await _db.publish(channel, event.model_dump_json())  # type: ignore

    async def sub(self, channel: str) -> tp.AsyncGenerator[EventType[T], None]:
        """Subscribe and yield Event[T] instances"""
        await self._pubsub.subscribe(channel)  # type: ignore
        while True:
            msg = await self._pubsub.get_message(  # type: ignore
                ignore_subscribe_messages=True, timeout=1.0
            )
            if msg and msg["type"] == "message":
                try:
                    raw = msg["data"]  # type: ignore
                    event = EventType[self._model].model_validate_json(raw)  # type: ignore
                    yield event
                except Exception:
                    continue
            await asyncio.sleep(0.01)
