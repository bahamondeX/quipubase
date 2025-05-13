from __future__ import annotations

from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from sse_starlette import EventSourceResponse

from ..cache import PubSub
from ..data.collection_manager import CollectionManager
from ..data.event import EventType
from ..models.typedefs import PubReturnType, QuipuActions, QuipubaseRequest
from ..models.utils import get_logger

logger = get_logger("[PubSubRouter]")


def pubsub_router() -> APIRouter:
    router = APIRouter(tags=["events"])
    col_manager = CollectionManager()

    @router.post("/events/{collection_id}", response_model=PubReturnType)
    async def _(collection_id: str, req: QuipubaseRequest):
        klass = col_manager.retrieve_collection(collection_id)
        try:
            pubsub = PubSub[klass]()
            item = None
            action: QuipuActions

            # Verificar si la solicitud tiene un ID
            if req.id is not None:
                item = klass.retrieve(id=req.id)
                if item is None:
                    raise ValueError(f"Item with id {req.id} not found")

                if req.data is not None:
                    # Si hay datos, actualizamos el ítem existente
                    item.update(**req.data)
                    action = "update"
                else:
                    # Si no hay datos, eliminamos el ítem
                    item.delete(id=req.id)
                    action = "delete"

            elif req.data is not None and req.event in ("create", "update"):
                # Si no hay ID, creamos un nuevo ítem si los datos están presentes
                item = klass.model_validate(req.data)
                if item.id is not None and req.event == "update":
                    # Si el ítem tiene un ID, actualizamos
                    klass.update(id=item.id, **req.data)
                    action = "update"
                else:
                    # Si no tiene ID, lo creamos
                    item.create()
                    action = "create"
            else:
                assert req.event == "stop"
                action = "stop"
            event = EventType[klass](event=action, data=item)
            await pubsub.pub(collection_id, event)
            assert item is not None
            return PubReturnType(collection=collection_id, data=item, event=action)
        except Exception as e:
            logger.error(f"Publish error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/events/{collection_id}", response_class=EventSourceResponse)
    async def _(request: Request, collection_id: str):
        """Subscribe to events for a specific collection"""
        try:
            klass = col_manager.retrieve_collection(collection_id)
            pubsub = PubSub[klass]()

            async def event_generator() -> AsyncIterator[dict[str, object]]:
                async for event in pubsub.sub(channel=collection_id):
                    if await request.is_disconnected() or event.event == "stop":
                        break
                    yield event.model_dump()

            return EventSourceResponse(content=event_generator(), ping=10)
        except Exception as e:
            logger.error(f"SSE error: {e}")
            raise HTTPException(status_code=500, detail=f"SSE error: {e}")

    return router
