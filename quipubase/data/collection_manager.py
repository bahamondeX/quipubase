import json
import os
import shutil
from pathlib import Path
from typing import Generator, Type

from fastapi import HTTPException

from ..models.typedefs import (CollectionMetadataType, CollectionType,
                               DeleteCollectionReturnType, JsonSchema,
                               JsonSchemaModel)
from ..models.utils import get_logger, singleton
from .collection import Collection
from .create_class import create_class

logger = get_logger("[CollectionManager]")


@singleton
class CollectionManager:
    """Singleton for managing collection classes and exchanges"""

    def retrieve_collection(self, collection_id: str) -> Type[Collection]:
        """Get or create a collection class for a given collection ID"""
        for data_dir in Path("/app/data/colllections").iterdir():
            if not data_dir.is_dir():
                continue
            if data_dir.as_posix().split("/")[-1] == collection_id:
                json_schema = self.get_json_schema(collection_id)
                return create_class(schema=json_schema)
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_id}' not found in data directory",
        )

    def get_json_schema(self, collection_id: str) -> JsonSchemaModel:
        """Get the JSON schema for a collection ID"""
        # Check in .data directory
        data_dir = os.path.join("/app/data/colllections")
        if not os.path.exists(data_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Data directory for Quipubase not found at {data_dir}",
            )
        for directory in os.listdir(data_dir):
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

    def list_collections(self) -> Generator[CollectionMetadataType, None, None]:
        """List all collections in the data directory"""
        data_dir = os.path.join("/app/data/colllections")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        for directory in os.listdir(data_dir):
            if os.path.isdir(os.path.join(data_dir, directory)):
                col_id = Path(directory).as_posix().split("/")[-1]
                klass = self.retrieve_collection(col_id)
                yield {"name": klass.__name__, "id": col_id}

    def get_collection(self, *, col_id: str) -> CollectionType:
        """Retrieve a collection class by ID"""
        try:
            klass = self.retrieve_collection(col_id)
            return {
                "name": klass.__name__,
                "id": col_id,
                "schema": JsonSchema(**klass.model_json_schema()),
            }
        except HTTPException as e:
            logger.error(f"Failed to retrieve collection '{col_id}': {str(e)}")
            raise e

    def delete_collection(self, *, col_id: str) -> DeleteCollectionReturnType:
        try:
            path = Path("/app/data/colllections")
            shutil.rmtree(path)
            return {"code": 0}
        except HTTPException as e:
            logger.error(f"Failed to delete collection '{col_id}': {str(e)}")
            return {"code": 500}
        except Exception as e:
            logger.error(f"Failed to delete collection '{col_id}': {str(e)}")
            return {"code": 1}

    def create_collection(self, *, data: JsonSchemaModel) -> CollectionType:
        """Create a new collection"""
        try:
            klass = create_class(schema=data)
            klass.init()
            return {
                "name": klass.__name__,
                "id": klass.col_id(),
                "schema": JsonSchema(**klass.col_json_schema().model_dump()),
            }
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create collection: {str(e)}",
            )
