import asyncio
import typing as tp

from ..collections.typedefs import Collection, SubResponse

from quipubase.lib import db

T = tp.TypeVar("T", bound=Collection)


class PubSub(tp.Generic[T]):
    _model: type[T]

    def __init__(self):
        self._pubsub = db.pubsub()  # type: ignore

    @classmethod
    def __class_getitem__(cls, model: type[T]):
        cls._model = model
        return cls

    async def pub(self, channel: str, event: SubResponse[T]) -> None:
        await db.publish(channel, event.model_dump_json())  # type: ignore

    async def sub(self, channel: str) -> tp.AsyncGenerator[SubResponse[T], None]:
        await self._pubsub.subscribe(channel)  # type: ignore
        try:
            while True:
                msg = await self._pubsub.get_message(  # type: ignore
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if msg and msg["type"] == "message":
                    try:
                        raw = msg["data"]  # type: ignore
                        event = SubResponse[self._model].model_validate_json(raw)  # type: ignore
                        yield event
                    except Exception:
                        continue
                await asyncio.sleep(0.01)
        finally:
            await self.unsub(channel)

    async def unsub(self, channel: str) -> None:
        await self._pubsub.unsubscribe(channel)  # type: ignore
