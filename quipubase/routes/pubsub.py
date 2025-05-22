from __future__ import annotations

import asyncio
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Request
from sse_starlette import EventSourceResponse

from ..cache import PubSub
from ..data.collection_manager import CollectionManager
from ..data.responses import EventType, PubType
from ..models.typedefs import QuipubaseRequest
from ..models.utils import get_logger

logger = get_logger("[PubSubRouter]")


def pubsub_router() -> APIRouter:
    router = APIRouter(tags=["events"])
    col_manager = CollectionManager()

    @router.post("/events/{collection_id}", response_model=PubType)
    async def _(collection_id: str, req: QuipubaseRequest):
        klass = col_manager.retrieve_collection(collection_id)
        try:
            pubsub = PubSub[klass]()
            item = None

            # Verificar si la solicitud tiene un ID
            if req.id is not None and req.event in ("update","delete"):
                item = klass.retrieve(id=req.id)
                assert item.id is not None, "Item retrieved didn't have an id"
                if req.data is not None:
                    # Si hay datos, actualizamos el ítem existente
                    item.update(id=item.id,**req.data)
                else:
                    # Si no hay datos, eliminamos el ítem
                    item.delete(id=req.id)
            elif req.data is not None and req.event in ("create", "update"):
                # Si no hay ID, creamos un nuevo ítem si los datos están presentes
                item = klass.model_validate(req.data)
                if item.id is not None and req.event == "update":
                    # Si el ítem tiene un ID, actualizamos
                    klass.update(id=item.id, **req.data)
                else:
                    # Si no tiene ID, lo creamos
                    item.create()
            elif req.event == "query":
                item = list(klass.find(**req.data if req.data else {}))
            elif req.event == "read":
                assert req.id is not None, "Not id provided for `read` request"
                item = klass.retrieve(id=req.id)
            else:
                assert req.event == "stop"
            event = EventType[klass](event=req.event, data=item)
            await pubsub.pub(collection_id, event)
            assert item is not None
            return PubType[klass](collection=collection_id, data=item, event=req.event)
        except Exception as e:
            logger.error(f"Publish error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/events/{collection_id}", response_class=EventSourceResponse)
    async def _(request: Request, collection_id: str):
        """Subscribe to events for a specific collection"""
        try:
            klass = col_manager.retrieve_collection(collection_id)
            pubsub = PubSub[klass]()

            async def event_generator() -> AsyncIterator[str]:
                try:
                    async for event in pubsub.sub(channel=collection_id):
                        if await request.is_disconnected() or event.event == "stop":
                            break
                        yield event.model_dump_json()
                except asyncio.CancelledError:
                    logger.info(f"Client disconnected from collection: {collection_id}")
                    # Opcional: publicar un evento `stop` u otra limpieza
                finally:
                    await pubsub.unsub(channel=collection_id)

            return EventSourceResponse(event_generator())

        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise HTTPException(status_code=500, detail="Subscription failed")

    return router