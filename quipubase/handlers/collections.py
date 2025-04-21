from __future__ import annotations

import asyncio
from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query

from ..classgen import create_class
from ..collection import Collection
from ..typedefs import ActionRequest, CollectionType, JsonSchemaModel
from ..utils import get_logger

logger = get_logger("[CollectionRouter]")


def collections_router() -> APIRouter:
    """Factory function to create a collection management router"""

    router = APIRouter(prefix="/collections", tags=["collections"])

    @router.post("")
    async def _(
        data: JsonSchemaModel,
    ) -> CollectionType:  # Use JsonSchemaModel instead of JsonSchema
        """Create a new collection"""
        col_class = create_class(schema=data)
        return CollectionType(
            id=col_class.col_path().split("/")[-1],
            definition=col_class.col_json_schema(),
        )

    @router.get("")
    async def _(
        limit: int = Query(default=100, ge=0), offset: int = Query(default=0, ge=0)
    ) -> List[str]:
        """List all collections"""

        def generator():
            nonlocal offset, limit
            for col in Collection.__subclasses__():
                if offset:
                    offset -= 1
                    continue
                if limit:
                    limit -= 1
                    yield col.col_path().split("/")[-1]
                continue

        return list(generator())

    @router.get("/{collection_id}")
    async def _(collection_id: str) -> CollectionType:
        """Get a specific collection by ID"""
        for col in Collection.__subclasses__():
            col_path = col.col_path().split("/")[-1]
            logger.info(f"col_path: {col_path}, collection_id: {collection_id}")
            if col_path == collection_id:
                return CollectionType(
                    id=collection_id, definition=col.col_json_schema()
                )
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_id}' not found"
        )

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
