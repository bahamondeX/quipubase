import typing as tp
import asyncio
from dataclasses import dataclass, field
from uuid import UUID

from .collection import Collection

T = tp.TypeVar("T", bound=Collection)

@dataclass
class Event(tp.Generic[T]):
	event:tp.Literal["create","update","delete", "read", "query","stop"]
	data:tp.Optional[T]


@dataclass
class Exchange(tp.Generic[T]):
	queues:dict[str,asyncio.Queue[Event[T]]] = field(default_factory=lambda:{"public":asyncio.Queue[Event[T]]()})

	async def sub(self, *, sub: str):
		if sub not in self.queues:
			self.queues[sub] = asyncio.Queue[Event[T]]()
		while True:
			q = self.queues[sub]
			item = await q.get()
			if item.event == "stop":
				break
			assert item.data is not None, "No data was found in the listener"
			yield item.data

	async def pub(
		self,
		*,
		sub: str,
		event: tp.Literal["create", "update", "delete", "read", "query", "stop"],
		value: tp.Optional[T],
		id: tp.Optional[UUID]
	):
		if sub not in self.queues:
			self.queues[sub] = asyncio.Queue[Event[T]]()
		q = self.queues[sub]
		if value is None and id is None:
			assert event == "stop", "Cannot create an action event without an `id` or a `value`."
			await q.put(Event[T](event="stop",data=None))
		if value is None:
			assert event in ("read","delete")
			if event == "read":
				item = Event.__annotations__.get("data").get(id) # type: ignore
				yield tp.cast(T, item)

