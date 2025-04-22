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
        return manager.delete_collection(col_id=collection_id)

    return router
