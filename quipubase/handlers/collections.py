from __future__ import annotations

import asyncio
from typing import Dict

from fastapi import APIRouter, HTTPException

from ..collection import Collection
from ..typedefs import ActionRequest, JsonSchemaModel
from ..utils import get_logger
from ..manager import StateManager


logger = get_logger("[CollectionRouter]")
manager = StateManager()

def collections_router() -> APIRouter:
    """Factory function to create a collection management router"""

    router = APIRouter(prefix="/collections", tags=["collections"])

    @router.post("")
    async def _(
        data: JsonSchemaModel,
    ):
        """Create a new collection"""
        return manager.create_collection(
            data=data)
    @router.get("")
    async def _():
        """List all collections"""
        return list(manager.list_collections())

    @router.get("/{collection_id}")
    async def _(collection_id: str):
        """Get a specific collection by ID"""
        return manager.get_collection(col_id=collection_id)
        
    @router.delete("/{collection_id}")
    async def _(collection_id: str) -> Dict[str, bool]:
        """Delete a collection by ID"""
        for col in Collection.__subclasses__():
            if col.col_path().split("/")[-1] == collection_id:
                col.destroy()
                return {"success": True}
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_id}' not found"
        )

    @router.put("/{collection_id}")
    async def _(collection_id: str, action_request: ActionRequest):
        """Unified endpoint for collection actions (create, read, update, delete, query)"""
        # Get the collection class
        if action_request.data is None and action_request.id is None:
            raise HTTPException(status_code=400, detail="Data or ID required")
        for col_class in Collection.__subclasses__():
            col_path = col_class.col_path().split("/")[-1]
            print(f"col_path: {col_path}, collection_id: {collection_id}")
            if col_path == collection_id:
                action = action_request.event
                if action == "create":
                    if not action_request.data:
                        raise HTTPException(
                            status_code=400, detail="Data required for create action"
                        )
                    item_obj = col_class(**action_request.data)
                    await asyncio.to_thread(item_obj.create)
                    return item_obj
                elif action == "read":
                    if not action_request.id:
                        raise HTTPException(
                            status_code=400, detail="ID required for read action"
                        )
                    item = await asyncio.to_thread(
                        col_class.retrieve, id=action_request.id
                    )
                    if item is None:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Item with ID '{action_request.id}' not found",
                        )
                    return item
                elif action == "update":
                    if not action_request.id or not action_request.data:
                        raise HTTPException(
                            status_code=400,
                            detail="ID and data required for update action",
                        )
                    data = dict(action_request.data)
                    if "id" in data:
                        del data["id"]
                    updated_item = await asyncio.to_thread(
                        col_class.update, id=action_request.id, **data
                    )

                    if updated_item is None:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Item with ID '{action_request.id}' not found",
                        )
                    return updated_item

                elif action == "delete":
                    if not action_request.id:
                        raise HTTPException(
                            status_code=400, detail="ID required for delete action"
                        )

                    # Get item before deletion for return value
                    item = await asyncio.to_thread(
                        col_class.retrieve, id=action_request.id
                    )

                    if item is None:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Item with ID '{action_request.id}' not found",
                        )
                    await asyncio.to_thread(col_class.delete, id=action_request.id)
                    return item
                elif action == "query":
                    # Convert query filters from action_request.data
                    query_filters = {}
                    if action_request.data:
                        query_filters = action_request.data
                    items_generator = await asyncio.to_thread(
                        col_class.find, **query_filters
                    )
                    result: list[Collection] = []
                    for item in items_generator:
                        result.append(item)
                    return result
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid or unsupported action: {action}",
                    )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Collection with ID '{collection_id}' not found",
            )

    return router
