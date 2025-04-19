from __future__ import annotations
import asyncio
import uuid
import shutil
import typing as tp
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, FastAPI, Request
from fastapi.responses import StreamingResponse
from .collection import Collection
from .utils import handle, logger, get_logger
from .exchange import Exchange, Event
from .classgen import create_class as generate_model_class
from .typedefs import JsonSchema, CollectionType, CollectionRequest, CollectionResponse

T = tp.TypeVar("T", bound=Collection)

logger = get_logger("[API]")


class Router(APIRouter):
    def __init__(self, **kwargs: tp.Any):
        super().__init__(**kwargs)
        self.collections: dict[str, tp.Type[Collection]] = {}
        self.exchanges: dict[str, Exchange[Collection]] = {}

        @self.post("/collections")
        @handle
        async def _(request_data: Dict[str, Any]):
            data = dict(request_data)
            if data["name"] in self.collections:
                raise HTTPException(
                    status_code=400,
                    detail=f"Collection '{data['name']}' already exists",
                )

            return self.create_collection(schema=data["definition"], name=data["name"])

        @self.get("/collections")
        @handle
        async def _(limit: int = 100, offset: int = 0):
            return list(self.list_collections(limit=limit, offset=offset))

        @self.get("/collections/{collection_id}")
        @handle
        async def _(collection_id: str):
            return self.get_collection(col_id=collection_id)

        @self.delete("/collections/{collection_id}")
        @handle
        async def _(collection_id: str):
            success = self.delete_collection(col_id=collection_id)
            return {"success": success}

        @self.post("/collections/{collection_id}/items")
        @handle
        async def _(collection_id: str, item: Dict[str, Any]):
            if collection_id in self.collections:
                model = self.collections[collection_id]
            else:
                # Try to find the collection in subclasses
                collection = self.get_collection(col_id=collection_id)
                model = self.create_klass(schema=collection.definition)
                self.collections[collection_id] = model
                self.exchanges[collection_id] = Exchange[model]()

            item_obj = model.model_validate(item)
            await asyncio.to_thread(item_obj.create)

            # Publish the event if the exchange exists
            if collection_id in self.exchanges:
                exchange = self.exchanges[collection_id]
                # Use list to consume the generator
                async for _ in exchange.pub(
                    sub="public", event="create", value=item_obj
                ):
                    pass

            return item_obj.model_dump()

        @self.get("/collections/{collection_id}/items/{item_id}")
        @handle
        async def _(collection_id: str, item_id: str):
            if collection_id in self.collections:
                model = self.collections[collection_id]
            else:
                # Try to find the collection in subclasses
                collection = self.get_collection(col_id=collection_id)
                model = self.create_klass(schema=collection.definition)
                self.collections[collection_id] = model
                self.exchanges[collection_id] = Exchange[model]()

            # Convert item_id string to UUID
            try:
                uuid_item_id = uuid.UUID(item_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid UUID format")

            item = await asyncio.to_thread(model.retrieve, id=uuid_item_id)

            if item is None:
                raise HTTPException(
                    status_code=404, detail=f"Item with ID '{item_id}' not found"
                )

            return item.model_dump()

        @self.put("/collections/{collection_id}/items/{item_id}")
        @handle
        async def _(collection_id: str, item_id: str, item: Dict[str, Any]):
            if collection_id in self.collections:
                model = self.collections[collection_id]
            else:
                # Try to find the collection in subclasses
                collection = self.get_collection(col_id=collection_id)
                model = self.create_klass(schema=collection.definition)
                self.collections[collection_id] = model
                self.exchanges[collection_id] = Exchange[model]()

            # Convert item_id string to UUID
            try:
                uuid_item_id = uuid.UUID(item_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid UUID format")

            # Remove id from data if present to prevent overwriting
            data = dict(item)
            if "id" in data:
                del data["id"]

            updated_item = await asyncio.to_thread(
                model.update, id=uuid_item_id, **data
            )

            if updated_item is None:
                raise HTTPException(
                    status_code=404, detail=f"Item with ID '{item_id}' not found"
                )

            # Publish the event if the exchange exists
            if collection_id in self.exchanges:
                exchange = self.exchanges[collection_id]
                async for _ in exchange.pub(
                    sub="public", event="update", value=updated_item
                ):
                    pass

            return updated_item.model_dump()

        @self.delete("/collections/{collection_id}/items/{item_id}")
        @handle
        async def _(collection_id: str, item_id: str):
            if collection_id in self.collections:
                model = self.collections[collection_id]
            else:
                # Try to find the collection in subclasses
                collection = self.get_collection(col_id=collection_id)
                model = self.create_klass(schema=collection.definition)
                self.collections[collection_id] = model
                self.exchanges[collection_id] = Exchange[model]()

            # Convert item_id string to UUID
            try:
                uuid_item_id = uuid.UUID(item_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid UUID format")

            # Get the item before deletion for event publishing
            item = await asyncio.to_thread(model.retrieve, id=uuid_item_id)
            if item is None:
                raise HTTPException(
                    status_code=404, detail=f"Item with ID '{item_id}' not found"
                )

            result = await asyncio.to_thread(model.delete, id=uuid_item_id)

            if not result:
                raise HTTPException(
                    status_code=404, detail=f"Item with ID '{item_id}' not found"
                )

            # Publish the event if the exchange exists
            if collection_id in self.exchanges:
                exchange = self.exchanges[collection_id]
                async for _ in exchange.pub(sub="public", event="delete", value=item):
                    pass

            return {"success": True}

        @self.get("/collections/{collection_id}/items")
        @handle
        async def _(
            request: Request, collection_id: str, *, limit: int = 100, offset: int = 0
        ):
            if collection_id in self.collections:
                model = self.collections[collection_id]
            else:
                # Try to find the collection in subclasses
                collection = self.get_collection(col_id=collection_id)
                model = self.create_klass(schema=collection.definition)
                self.collections[collection_id] = model
                self.exchanges[collection_id] = Exchange[model]()

            items_generator = await asyncio.to_thread(
                model.find, limit=limit, offset=offset, **request.query_params
            )

            # Convert generator to list
            result: list[dict[str, tp.Any]] = []
            for item in items_generator:
                result.append(item.model_dump())

                # Publish the query event
                if collection_id in self.exchanges:
                    exchange = self.exchanges[collection_id]
                    async for _ in exchange.pub(
                        sub="public", event="query", value=item
                    ):
                        pass
            return result

        @self.get("/collections/{collection_id}/subscribe")
        @handle
        async def _(collection_id: str, *, limit: int = 100, offset: int = 0):
            if collection_id in self.collections:
                model = self.collections[collection_id]
            else:
                # Try to find the collection in subclasses
                try:
                    collection = self.get_collection(col_id=collection_id)
                    model = self.create_klass(schema=collection.definition)
                    self.collections[collection_id] = model
                    self.exchanges[collection_id] = Exchange[model]()
                except HTTPException:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Collection '{collection_id}' not found",
                    )

            if collection_id not in self.exchanges:
                self.exchanges[collection_id] = Exchange[model]()

            exchange = self.exchanges[collection_id]

            async def event_generator():
                try:
                    async for item in exchange.sub(sub="public"):
                        # Create an event with the item data
                        evt = Event(event="update", data=item)
                        yield evt.to_sse()
                except asyncio.CancelledError:
                    await exchange.close(sub="public")
                except Exception as e:
                    logger.error(f"Subscription error: {e}")
                    await exchange.close(sub="public")

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream",
                },
            )

    def list_collections(
        self, *, limit: int = 100, offset: int = 0
    ) -> tp.Iterator[CollectionType]:
        for col in Collection.__subclasses__():
            if offset:
                offset -= 1
                continue
            if limit:
                limit -= 1
                yield CollectionType(
                    id=col.col_path().split("/")[-1], definition=col.col_json_schema()
                )
                continue
            yield CollectionType(
                id=col.col_path().split("/")[-1], definition=col.col_json_schema()
            )
            break

    def get_collection(self, *, col_id: str) -> CollectionType:
        for col in Collection.__subclasses__():
            if col.col_path().split("/")[-1] == col_id:
                return CollectionType(
                    id=col.col_path().split("/")[-1], definition=col.col_json_schema()
                )
        raise HTTPException(status_code=404, detail="Collection not found")

    def create_klass(self, *, schema: JsonSchema):
        return generate_model_class(schema=schema)

    def create_collection(self, *, schema: JsonSchema, name: str) -> CollectionType:
        col = generate_model_class(schema=schema)
        self.collections[name] = col
        self.exchanges[name] = Exchange[col]()
        return CollectionType(
            id=col.col_path().split("/")[-1], definition=col.col_json_schema()
        )

    def delete_collection(self, *, col_id: str) -> bool:
        if col_id in self.collections:
            model = self.collections[col_id]
            result = model.destroy()
            if result == 0:
                if col_id in self.exchanges:
                    asyncio.create_task(self.exchanges[col_id].close())
                    del self.exchanges[col_id]
                del self.collections[col_id]
                return True

        for col in Collection.__subclasses__():
            if col.col_path().split("/")[-1] == col_id:
                shutil.rmtree(col.col_path())
                return True

        raise HTTPException(status_code=404, detail="Collection not found")


class QuipuBase(FastAPI):
    def __init__(self, *args: tp.Any, **kwargs: tp.Any):
        super().__init__(
            title="QuipuBase",
            description="A document database based on `jsonschema`",
            version="0.0.1",
            **kwargs,
        )
        self.include_router(Router())
