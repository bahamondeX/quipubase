from __future__ import annotations
from typing import TypeVar, Dict, Optional, Any, AsyncIterator
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..collection import Collection
from ..utils import get_logger
from ..state import StateManager
from ..exchange import Event
from ..typedefs import PubRequest

logger = get_logger("[PubSubRouter]")

T = TypeVar("T", bound=Collection)


class PubActionResponse(BaseModel):
    """Response model for publish actions"""

    success: bool
    message: str
    item: Optional[Dict[str, Any]] = None


def pubsub_router() -> APIRouter:
    """Factory function to create a pubsub router"""

    router = APIRouter(prefix="/pubsub", tags=["pubsub"])
    state_manager = StateManager()

    @router.post("/{collection_id}/publish", response_model=PubActionResponse)
    async def _(collection_id: str, req: PubRequest) -> PubActionResponse:
        """Publish an event to a collection subscription"""
        try:
            exchange = state_manager.get_exchange(collection_id)

            async for item in exchange.pub(
                sub=req.sub,
                event=req.action,
                value=req.value,
                id=req.id,
            ):
                # Return the first (and only) item
                return PubActionResponse(
                    success=True,
                    message=f"Event {req.action} published successfully to {req.sub}",
                    item=item.model_dump() if item else None,
                )

            # If no items were yielded but no errors occurred
            return PubActionResponse(
                success=True,
                message=f"Event {req.action} published successfully to {req.sub}",
                item=None,
            )

        except Exception as e:
            logger.error(f"Error publishing event: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error publishing event: {str(e)}"
            )

    @router.get("/{collection_id}/subscribe")
    async def _(
        collection_id: str,
        subscription: str = Query(default="public"),
    ):
        """Subscribe to a collection using Server-Sent Events (SSE)"""
        try:
            exchange = state_manager.get_exchange(collection_id)

            async def event_generator() -> AsyncIterator[str]:
                try:
                    async for item in exchange.sub(sub=subscription):
                        # Create an event
                        event = Event(
                            event="update" if item.id else "create", data=item
                        )
                        yield event.to_sse()
                except Exception as e:
                    logger.error(f"Error in SSE stream: {str(e)}")
                    # Send error event
                    yield f"event: error\ndata: {str(e)}\n\n"
                finally:
                    # Ensure subscription is closed when done
                    await exchange.close(sub=subscription)

            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache"},
            )

        except Exception as e:
            logger.error(f"Error setting up SSE subscription: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error setting up SSE subscription: {str(e)}"
            )

    @router.post("/{collection_id}/close")
    async def _(collection_id: str, subscription: Optional[str] = None):
        """Close a specific subscription or all subscriptions for a collection"""
        try:
            exchange = state_manager.get_exchange(collection_id)
            await exchange.close(sub=subscription)
            return {
                "success": True,
                "message": f"Closed {'all subscriptions' if subscription is None else f'subscription {subscription}'} for collection {collection_id}",
            }
        except Exception as e:
            logger.error(f"Error closing subscription: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error closing subscription: {str(e)}"
            )

    return router
