import typing as tp
import time
from typing import AsyncGenerator, Optional, Type
import asyncio
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .collection import Collection
from .utils import handle
from .typedefs import QuipuActions

T = tp.TypeVar("T", bound=Collection)


@dataclass
class Event(tp.Generic[T]):
    ref: UUID = field(default_factory=uuid4)
    ts: float = field(default_factory=time.time)
    event: QuipuActions = field(default="stop")
    data: tp.Optional[T] = field(default=None)

    def to_sse(self) -> str:
        """Formato para Server-Sent Events"""
        if self.data is None:
            return (
                f"event: {self.event}\nid: {self.ref}\ndata: null\ntime: {self.ts}\n\n"
            )
        data_str = self.data.model_dump_json()
        return f"event: {self.event}\nid: {self.ref}\ndata: {data_str}\ntime: {self.ts}\n\n"


@dataclass
class Exchange(tp.Generic[T]):
    @classmethod
    def __class_getitem__(cls, item: Type[T]) -> "Type[Exchange[T]]":
        cls._model = item
        return cls

    queues: dict[str, asyncio.Queue[Event[T]]] = field(
        default_factory=lambda: {"public": asyncio.Queue()}
    )

    @handle
    async def sub(self, *, sub: str) -> AsyncGenerator[T, None]:
        """Subscribe to a queue and yield events"""
        if sub not in self.queues:
            self.queues[sub] = asyncio.Queue[Event[T]]()
        while True:
            q = self.queues[sub]
            item = await q.get()
            if item.event == "stop":
                break
            assert item.data is not None, "No data was found in the listener"
            print(item.data)
            yield item.data

    @handle
    async def pub(
        self,
        *,
        sub: str,
        event: QuipuActions,
        value: tp.Optional[T] = None,
        id: tp.Optional[UUID] = None,
        **kwargs: tp.Any,
    ) -> AsyncGenerator[T, None]:
        """Publish an event to a queue"""
        if sub not in self.queues:
            self.queues[sub] = asyncio.Queue[Event[T]]()
        q = self.queues[sub]

        # Crear objeto evento
        evt = Event[T](event=event, data=value)

        # Handle stop event
        if value is None and id is None:
            assert (
                event == "stop"
            ), "Cannot create an action event without an `id` or a `value`."
            await q.put(evt)
            return

        # Handle value-based events (create, update)
        if value is not None:
            await q.put(evt)
            if event != "stop":
                yield value
            return

        # Handle ID-based events (read, delete, query)
        assert id is not None, "Either value or id must be provided"

        if event == "read":
            # Retrieve the item from the collection
            item = await asyncio.to_thread(self._model.retrieve, id=id)
            if item is not None:
                evt.data = item
                await q.put(evt)
                yield item

        elif event == "delete":
            # Get the item before deleting it
            item = await asyncio.to_thread(self._model.retrieve, id=id)
            if item is not None:
                success = await asyncio.to_thread(self._model.delete, id=id)
                if success:
                    evt.data = item
                    await q.put(evt)
                    yield item

        elif event == "query":
            # For query events with an ID, just notify about the ID
            items = await asyncio.to_thread(self._model.find, **kwargs)
            for item in items:
                evt = Event[T](event=event, data=item)
                await q.put(evt)
                yield item

    @handle
    async def close(self, *, sub: Optional[str] = None) -> None:
        """Close a specific subscription or all subscriptions"""
        if sub is not None:
            if sub in self.queues:
                await self.queues[sub].put(Event[T](event="stop", data=None))
                del self.queues[sub]
        else:
            # Close all subscriptions
            for queue_name in list(self.queues.keys()):
                await self.queues[queue_name].put(Event[T](event="stop", data=None))
                del self.queues[queue_name]
