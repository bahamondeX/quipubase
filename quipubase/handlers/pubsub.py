from __future__ import annotations

from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from ..cache import PubSub
from ..event import Event
from ..state import StateManager
from ..typedefs import ActionRequest, QuipuActions
from ..utils import get_logger

logger = get_logger("[PubSubRouter]")


def pubsub_router() -> APIRouter:
    router = APIRouter(tags=["pubsub"])
    state_manager = StateManager()

    @router.post("/events/{collection_id}")
    async def _(collection_id: str, req: ActionRequest) -> Dict[str, Any]:
        klass = state_manager.get_collection(collection_id)
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
                raise ValueError("Both id and data are missing")

            assert item is not None
            event = Event[klass](event=action, data=item)
            await pubsub.pub(collection_id, event)
            return {
                "collection": klass.col_path().split("/")[-1],
                "id": item.id if item else None,
            }
        except Exception as e:
            logger.error(f"Publish error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/events/{collection_id}")
    async def _(collection_id: str):
        try:
            klass = state_manager.get_collection(collection_id)
            pubsub = PubSub[klass]()

            async def event_generator() -> AsyncIterator[str]:
                async for event in pubsub.sub(channel=collection_id):
                    yield f"data: {event.model_dump_json()}\n\n"

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Transfer-Encoding": "chunked",
                },
            )

        except Exception as e:
            logger.error(f"SSE error: {e}")
            raise HTTPException(status_code=500, detail=f"SSE error: {e}")

    return router
