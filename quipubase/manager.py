import json
import os
from pathlib import Path
from typing import Dict, Type

from fastapi import HTTPException

from .classgen import create_class
from .collection import Collection
from .typedefs import JsonSchemaModel
from .utils import get_logger, singleton

logger = get_logger("[StateManager]")


@singleton
class StateManager:
    """Singleton for managing collection classes and exchanges"""

    def _get_collection(self, collection_id: str) -> Type[Collection]:
        """Get or create a collection class for a given collection ID"""
        for data_dir in Path(os.path.join(Path.home(), ".data")).iterdir():
            if not data_dir.is_dir():
                continue
            if data_dir.as_posix().split("/")[-1] == collection_id:
                json_schema = self._get_json_schema(collection_id)
                return create_class(schema=json_schema)
        raise HTTPException(
            status_code=404,
            detail=f"Collection '{collection_id}' not found in data directory",
        )

    def _get_json_schema(self, collection_id: str) -> JsonSchemaModel:
        """Get the JSON schema for a collection ID"""
        # Check in .data directory
        data_dir = os.path.join(Path.home(), ".data")
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
                    schema_data = json.loads(schema_path.read_text(), encoding="utf-8")
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

    def list_collections(self):
        """List all collections in the data directory"""
        data_dir = os.path.join(Path.home(), ".data")
        if not os.path.exists(data_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Data directory for Quipubase not found at {data_dir}",
            )
        for directory in os.listdir(data_dir):
            if os.path.isdir(os.path.join(data_dir, directory)):
                col_id = Path(directory).as_posix().split("/")[-1]
                klass = self._get_collection(col_id)
                yield {"name":klass.__name__, "id":col_id}
                
    def retrieve_collection(self, *, col_id:str):
        """Retrieve a collection class by ID"""
        try:
            klass = self._get_collection(col_id)
            return {"name":klass.__name__, "id":col_id, "schema":klass.model_json_schema()}
        except HTTPException as e:
            logger.error(f"Failed to retrieve collection '{col_id}': {str(e)}")
            raise e
