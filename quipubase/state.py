import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

from fastapi import HTTPException

from .collection import Collection
from .utils import get_logger, singleton
from .exchange import Exchange
from .classgen import create_class
from .typedefs import JsonSchemaModel

logger = get_logger("[StateManager]")

T = TypeVar("T", bound=Collection)


@singleton
class StateManager:
    """Singleton for managing collection classes and exchanges"""

    collections_cache: Dict[str, Type[Collection]]
    exchanges_cache: Dict[str, Exchange[Any]]

    def __init__(
        self, collections_cache: Optional[Dict[str, Type[Collection]]] = None
    ) -> None:
        self.collections_cache = collections_cache or {}
        self.exchanges_cache = {}

    def get_collection(self, collection_id: str) -> Type[Collection]:
        """Get or create a collection class for a given collection ID"""
        # First check cache
        if collection_id in self.collections_cache:
            return self.collections_cache[collection_id]

        # Try to find from existing Collection subclasses
        for col_class in Collection.__subclasses__():
            col_path = col_class.col_path().split("/")[-1]
            if col_path == collection_id:
                self.collections_cache[collection_id] = col_class
                return col_class

        # Try to load from disk by getting the schema
        try:
            schema = self.get_json_schema(collection_id)
            klass = create_class(schema=schema)
            self.collections_cache[collection_id] = klass
            return klass
        except Exception as e:
            logger.error(f"Failed to get collection {collection_id}: {str(e)}")
            raise HTTPException(
                status_code=404, detail=f"Collection '{collection_id}' not found"
            )

    def get_exchange(self, collection_id: str) -> Exchange[Any]:
        """Get or create an exchange for a given collection ID"""
        if collection_id not in self.exchanges_cache:
            # Get the collection class first
            collection_class = self.get_collection(collection_id)
            # Create a new exchange
            self.exchanges_cache[collection_id] = Exchange[collection_class]()

        return self.exchanges_cache[collection_id]

    def get_json_schema(self, collection_id: str) -> JsonSchemaModel:
        """Get the JSON schema for a collection ID"""
        # First check cache
        for klass in self.collections_cache.values():
            col_path = klass.col_path().split("/")[-1]
            if col_path == collection_id:
                return klass.col_json_schema()

        # Check in .data directory
        data_dir = os.path.join(Path.home(), ".data")
        if not os.path.exists(data_dir):
            raise HTTPException(
                status_code=404, detail=f"Data directory not found at {data_dir}"
            )

        # Try to find a directory matching collection_id
        for directory in os.listdir(data_dir):
            # Check if this is the collection we're looking for
            if directory == collection_id:
                schema_path = Path(os.path.join(data_dir, directory, "schema.json"))
                if not schema_path.exists():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Schema file not found for collection '{collection_id}'",
                    )

                try:
                    schema_data = json.loads(schema_path.read_text())
                    return JsonSchemaModel(**schema_data)
                except Exception as e:
                    logger.error(
                        f"Failed to parse schema for {collection_id}: {str(e)}"
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to parse schema for collection '{collection_id}': {str(e)}",
                    )

        # If we get here, the collection was not found
        raise HTTPException(
            status_code=404, detail=f"Collection '{collection_id}' not found"
        )

    def clear_cache(self, collection_id: Optional[str] = None) -> None:
        """Clear the cache for a specific collection or all collections"""
        if collection_id is not None:
            if collection_id in self.collections_cache:
                del self.collections_cache[collection_id]
            if collection_id in self.exchanges_cache:
                del self.exchanges_cache[collection_id]
        else:
            self.collections_cache.clear()
            self.exchanges_cache.clear()
