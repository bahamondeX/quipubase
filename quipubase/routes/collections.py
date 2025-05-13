from __future__ import annotations

from fastapi import APIRouter

from ..data.collection_manager import CollectionManager
from ..models.typedefs import (CollectionMetadataType, CollectionType,
                               DeleteCollectionReturnType, JsonSchemaModel)
from ..models.utils import get_logger

logger = get_logger("[CollectionRouter]")
manager = CollectionManager()


def collections_router() -> APIRouter:
    """Factory function to create a collection management router"""

    router = APIRouter(prefix="/collections", tags=["collections"])

    @router.post("", response_model=CollectionType)
    async def _(
        data: JsonSchemaModel,
    ):
        """Create a new collection"""
        return manager.create_collection(data=data)

    @router.get("", response_model=list[CollectionMetadataType])
    async def _():
        """List all collections"""
        return list(manager.list_collections())

    @router.get("/{collection_id}", response_model=CollectionType)
    async def _(collection_id: str):
        """Get a specific collection by ID"""
        return manager.get_collection(col_id=collection_id)

    @router.delete("/{collection_id}", response_model=DeleteCollectionReturnType)
    async def _(collection_id: str) -> DeleteCollectionReturnType:
        """Delete a collection by ID"""
        return manager.delete_collection(col_id=collection_id)

    return router
