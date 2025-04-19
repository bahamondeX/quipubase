from __future__ import annotations

from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..cache import PubSub
from ..collection import Collection
from ..event import Event
from ..state import StateManager
from ..typedefs import ActionRequest, QuipuActions
from ..utils import get_logger

logger = get_logger("[PubSubRouter]")


def pubsub_router() -> APIRouter:
    router = APIRouter(prefix="/pubsub", tags=["pubsub"])
    state_manager = StateManager()

    @router.post("/events/{collection_id}")
    async def _(collection_id: str, req: ActionRequest) -> Dict[str, Any]:
        klass = state_manager.get_collection(collection_id)
        try:
            pubsub = PubSub[klass]()

            if not isinstance(klass, Collection):
                raise ValueError(f"Expected Collection, got {type(klass)}")

            item = None
            action: QuipuActions

            if req.id is not None:
                item = klass.retrieve(id=req.id)
                if item is None:
                    raise ValueError(f"Item with id {req.id} not found")

                if req.data is not None:
                    item.update(**req.data)
                    action = "update"
                else:
                    item.delete(id=req.id)
                    action = "delete"

            elif req.data is not None:
                item = klass.model_validate(req.data)
                if item.id is not None:
                    klass.update(id=item.id, **req.data)
                    action = "update"
                else:
                    item.create()
                    action = "create"
            else:
                raise ValueError("Both id and data are missing")
            assert item is not None
            event = Event[klass](event=action, item=item)
            await pubsub.pub(collection_id, event)
            return {
                "collection": klass.col_path().split("/")[-1],
                "id": item.id if item else None,
            }

        except Exception as e:
            logger.error(f"Publish error: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/events/{collection_id}")
    async def _(collection_id: str, sub: str = Query(default="public")):
        try:
            klass = state_manager.get_collection(collection_id)
            pubsub = PubSub[klass]()

            async def event_generator() -> AsyncIterator[str]:
                async for event in pubsub.sub(channel=sub):
                    yield f"data: {event.model_dump_json()}\n\n"

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache"},
            )

        except Exception as e:
            logger.error(f"SSE error: {e}")
            raise HTTPException(status_code=500, detail=f"SSE error: {e}")

    return router
