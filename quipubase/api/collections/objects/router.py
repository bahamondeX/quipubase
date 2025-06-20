from __future__ import annotations

import asyncio
from typing import AsyncIterator

from fastapi import APIRouter, Request
from sse_starlette import EventSourceResponse

from ....lib.exceptions import QuipubaseException
from ....lib.utils import get_logger, handle
from ..service import CollectionManager
from ..typedefs import PubResponse, QuipubaseRequest, SubResponse
from .service import PubSub

logger = get_logger("[ObjectsRouter]")


def route() -> APIRouter:
    router = APIRouter(tags=["collections"], prefix="/collections")
    col_manager = CollectionManager()

    @handle
    @router.post("/objects/{collection_id}", response_model=PubResponse)
    async def _(collection_id: str, req: QuipubaseRequest):
        klass = await col_manager.retrieve_collection(collection_id)

        pubsub = PubSub[klass]()
        item = None

        # Verificar si la solicitud tiene un ID
        if req.id is not None and req.event in ("update", "delete"):
            item = klass.retrieve(id=req.id)
            assert item.id is not None, "Item retrieved didn't have an id"
            if req.data is not None:
                # Si hay datos, actualizamos el ítem existente
                item.update(id=item.id, **req.data)
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
        if item is None:
            raise QuipubaseException(detail="No data available", status_code=-12500)
        event = SubResponse[klass](event=req.event, data=item)
        await pubsub.pub(collection_id, event)  # type: ignore
        assert item is not None
        return PubResponse[klass](collection=collection_id, data=item, event=req.event)

    @router.get("/objects/{collection_id}", response_class=EventSourceResponse)
    async def _(request: Request, collection_id: str):
        """Subscribe to events for a specific collection"""
        try:
            klass = await col_manager.retrieve_collection(collection_id)
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
            raise QuipubaseException(status_code=500, detail="Subscription failed")

    return router
