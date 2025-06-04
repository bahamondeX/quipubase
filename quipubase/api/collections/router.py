from __future__ import annotations

from fastapi import APIRouter

from quipubase.lib.utils import encrypt, get_logger

from .service import CollectionManager
from .typedefs import (CollectionMetadataType, CollectionType,
                       DeleteCollectionReturnType, JsonSchemaModel)

logger = get_logger("[CollectionRouter]")
manager = CollectionManager()


def route() -> APIRouter:
    """Factory function to create a collection management router"""

    router = APIRouter(prefix="/collections", tags=["collections"])

    @router.post("", response_model=CollectionType)
    def _(
        data: JsonSchemaModel,
    ):
        """Create a new collection"""
        try:
            collection_id = encrypt(data.model_dump_json())
            return manager.get_collection(col_id=collection_id)
        except:
            return manager.create_collection(data=data)

    @router.get("", response_model=list[CollectionMetadataType])
    def _():
        """List all collections"""
        return list(manager.list_collections())

    @router.get("/{collection_id}", response_model=CollectionType)
    def _(collection_id: str):
        """Get a specific collection by ID"""
        return manager.get_collection(col_id=collection_id)

    @router.delete("/{collection_id}", response_model=DeleteCollectionReturnType)
    def _(collection_id: str) -> DeleteCollectionReturnType:
        """Delete a collection by ID"""
        return manager.delete_collection(col_id=collection_id)

    return router
