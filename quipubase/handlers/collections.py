from __future__ import annotations
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Type
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..collection import Collection
from ..utils import get_logger
from ..classgen import create_class
from ..typedefs import JsonSchemaModel, CollectionType, QuipuActions

logger = get_logger("[CollectionRouter]")


class ActionRequest(BaseModel):
    action: QuipuActions
    id: Optional[uuid.UUID] = None
    data: Optional[Dict[str, Any]] = None
    collection_id: Optional[str] = None


def collections_router() -> APIRouter:
    """Factory function to create a collection management router"""

    router = APIRouter(prefix="/collections", tags=["collections"])
    collections_cache: Dict[str, Type[Collection]] = {}

    @router.post("")
    async def _(
        data: JsonSchemaModel,
    ) -> CollectionType:  # Use JsonSchemaModel instead of JsonSchema
        """Create a new collection"""
        collection_name = data.title  # Access as attribute now

        if collection_name in collections_cache:
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{collection_name}' already exists",
            )
        col_class = create_class(schema=data)
        collections_cache[collection_name] = col_class

        return CollectionType(
            id=col_class.col_path().split("/")[-1],
            definition=col_class.col_json_schema(),
        )

    @router.get("")
    async def _(
        limit: int = Query(default=100, ge=0), offset: int = Query(default=0, ge=0)
    ) -> List[CollectionType]:
        """List all collections"""
        result: List[CollectionType] = []

        current_offset = offset
        current_limit = limit

        for _, col in collections_cache.items():
            if current_offset > 0:
                current_offset -= 1
                continue

            if current_limit > 0:
                current_limit -= 1
                result.append(
                    CollectionType(
                        id=col.col_path().split("/")[-1],
                        definition=col.col_json_schema(),
                    )
                )

            if current_limit <= 0:
                break

        if current_limit > 0:
            for col in Collection.__subclasses__():
                col_id = col.col_path().split("/")[-1]

                if any(r.id == col_id for r in result):
                    continue

                if current_offset > 0:
                    current_offset -= 1
                    continue

                if current_limit > 0:
                    current_limit -= 1
                    result.append(
                        CollectionType(id=col_id, definition=col.col_json_schema())
                    )

                if current_limit <= 0:
                    break

        return result

    @router.get("/{collection_id}")
    async def get_collection(collection_id: str) -> CollectionType:
        """Get a specific collection by ID"""
        for _, col in collections_cache.items():
            if col.col_path().split("/")[-1] == collection_id:
                return CollectionType(
                    id=collection_id, definition=col.col_json_schema()
                )

        for col in Collection.__subclasses__():
            if col.col_path().split("/")[-1] == collection_id:
                collections_cache[collection_id] = col
                return CollectionType(
                    id=collection_id, definition=col.col_json_schema()
                )

        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_id}' not found"
        )

    @router.delete("/{collection_id}")
    async def _(collection_id: str) -> Dict[str, bool]:
        """Delete a collection by ID"""
        if collection_id in collections_cache:
            model = collections_cache[collection_id]
            result = model.destroy()

            if result == 0:
                del collections_cache[collection_id]
                return {"success": True}
            else:
                return {"success": False}

        for col in Collection.__subclasses__():
            if col.col_path().split("/")[-1] == collection_id:
                result = col.destroy()
                return {"success": result == 0}

        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_id}' not found"
        )

    @router.post("/{collection_id}/action")
    async def _(collection_id: str, action_request: ActionRequest) -> Dict[str, Any]:
        """Unified endpoint for collection actions (create, read, update, delete, query)"""
        # Get the collection class
        col_class = None

        if collection_id in collections_cache:
            col_class = collections_cache[collection_id]
        else:
            # Try to find from Collection subclasses
            for col in Collection.__subclasses__():
                if col.col_path().split("/")[-1] == collection_id:
                    col_class = col
                    collections_cache[collection_id] = col
                    break

            if col_class is None:
                # Try to get collection and create class
                try:
                    # We need to first check if the collection exists
                    # by looking at its path
                    collection = await get_collection(collection_id)
                    col_class = create_class(schema=collection.definition)
                    collections_cache[collection_id] = col_class
                except HTTPException:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Collection '{collection_id}' not found",
                    )

        # Process based on action type
        action = action_request.action

        if action == "create":
            if not action_request.data:
                raise HTTPException(
                    status_code=400, detail="Data required for create action"
                )

            item_obj = col_class.model_validate(action_request.data)
            await asyncio.to_thread(item_obj.create)
            return item_obj.model_dump()

        elif action == "read":
            if not action_request.id:
                raise HTTPException(
                    status_code=400, detail="ID required for read action"
                )

            item = await asyncio.to_thread(col_class.retrieve, id=action_request.id)

            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Item with ID '{action_request.id}' not found",
                )

            return item.model_dump()

        elif action == "update":
            if not action_request.id or not action_request.data:
                raise HTTPException(
                    status_code=400, detail="ID and data required for update action"
                )

            # Remove id from data if present
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

            return updated_item.model_dump()

        elif action == "delete":
            if not action_request.id:
                raise HTTPException(
                    status_code=400, detail="ID required for delete action"
                )

            # Get item before deletion for return value
            item = await asyncio.to_thread(col_class.retrieve, id=action_request.id)

            if item is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Item with ID '{action_request.id}' not found",
                )
            await asyncio.to_thread(col_class.delete, id=action_request.id)
            return {"success": True, "deleted_item": item.model_dump()}

        elif action == "query":
            # Convert query filters from action_request.data
            query_filters = {}
            if action_request.data:
                query_filters = action_request.data

            items_generator = await asyncio.to_thread(col_class.find, **query_filters)

            # Convert generator to list
            result: list[Dict[str, Any]] = []
            for item in items_generator:
                result.append(item.model_dump())

            return {"items": result, "count": len(result)}

        else:  # action == "stop" or invalid action
            raise HTTPException(
                status_code=400, detail=f"Invalid or unsupported action: {action}"
            )

    return router
