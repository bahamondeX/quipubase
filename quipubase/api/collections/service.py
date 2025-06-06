import json
import shutil
from pathlib import Path
from typing import Generator, Type

from fastapi import HTTPException, status
from rocksdict import Rdict

from quipubase.lib.exceptions import QuipubaseException
from quipubase.lib.utils import get_logger, handle, singleton

from .typedefs import (Collection, CollectionMetadataType, CollectionType,
                       DeleteCollectionReturnType, JsonSchema, JsonSchemaModel)

logger = get_logger("[CollectionManager]")


@singleton
class CollectionManager:
    """Singleton for managing collection classes and exchanges"""

    def __init__(self):
        try:
            self.db_path = Path("./data/meta")
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.db = Rdict(str(self.db_path))
            logger.info(
                f"Initialized CollectionManager with database at {self.db_path}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize CollectionManager: {str(e)}")
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize CollectionManager: {str(e)}",
            )

    def _validate_collection_id(self, collection_id: str) -> None:
        """Validate collection ID format"""
        if not collection_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection ID cannot be empty",
            )
        if len(collection_id) > 255:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Collection ID cannot exceed 255 characters",
            )

    @handle
    def retrieve_collection(self, collection_id: str) -> Type[Collection]:
        """Get or create a collection class for a given collection ID"""
        self._validate_collection_id(collection_id)

        try:
            data = self.db.get(collection_id)
            if not data:
                raise QuipubaseException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{collection_id}' not found",
                )

            json_schema = json.loads(data)
            klass = JsonSchemaModel(**json_schema).create_class()
            logger.info(f"Successfully retrieved collection '{collection_id}'")
            return klass

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode JSON for collection '{collection_id}': {str(e)}"
            )
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid JSON data for collection '{collection_id}'",
            )
        except Exception as e:
            logger.error(f"Failed to retrieve collection '{collection_id}': {str(e)}")
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve collection '{collection_id}'",
            )

    @handle
    def get_json_schema(self, collection_id: str) -> JsonSchemaModel:
        """Get the JSON schema for a collection ID"""
        self._validate_collection_id(collection_id)

        try:
            data = self.db.get(collection_id)
            if not data:
                raise QuipubaseException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{collection_id}' not found",
                )

            json_schema = json.loads(data)
            schema_model = JsonSchemaModel(**json_schema)
            logger.info(
                f"Successfully retrieved schema for collection '{collection_id}'"
            )
            return schema_model

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to decode JSON schema for collection '{collection_id}': {str(e)}"
            )
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Invalid JSON schema for collection '{collection_id}'",
            )
        except Exception as e:
            logger.error(
                f"Failed to get schema for collection '{collection_id}': {str(e)}"
            )
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get schema for collection '{collection_id}'",
            )

    def list_collections(self) -> Generator[CollectionMetadataType, None, None]:
        """List all collections in the database"""
        try:
            for col_id in self.db.keys():
                try:
                    json_schema = json.loads(self.db[col_id])
                    klass = JsonSchemaModel(**json_schema).create_class()
                    yield {"name": klass.__name__, "id": col_id}
                except Exception as e:
                    logger.error(f"Failed to process collection '{col_id}': {str(e)}")
                    continue
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list collections",
            )

    @handle
    def get_collection(self, *, col_id: str) -> CollectionType:
        """Retrieve a collection class by ID"""
        try:
            klass = self.retrieve_collection(col_id)
            return {
                "name": klass.__name__,
                "id": col_id,
                "schema": JsonSchema(**klass.model_json_schema()),
            }
        except QuipubaseException as e:
            logger.error(f"Failed to get collection '{col_id}': {str(e)}")
            raise e

    @handle
    def delete_collection(self, *, col_id: str) -> DeleteCollectionReturnType:
        """Delete a collection by ID"""
        self._validate_collection_id(col_id)

        try:
            # Remove from database
            if not self.db.get(col_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{col_id}' not found",
                )

            # Remove collection directory
            collection_path = Path(f"./data/collections/{col_id}")
            if collection_path.exists():
                if not collection_path.is_dir():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Path '{collection_path}' exists but is not a directory",
                    )

                try:
                    shutil.rmtree(collection_path)
                    logger.info(
                        f"Successfully deleted collection '{col_id}' at {collection_path}"
                    )
                except OSError as e:
                    logger.error(
                        f"Failed to delete collection directory '{collection_path}': {str(e)}"
                    )
                    raise QuipubaseException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to delete collection directory '{collection_path}'",
                    )
            del self.db[col_id]
            return {"code": 0}

        except HTTPException as e:
            logger.error(f"Failed to delete collection '{col_id}': {str(e)}")
            return {"code": 500}
        except Exception as e:
            logger.error(f"Unexpected error deleting collection '{col_id}': {str(e)}")
            return {"code": 1}

    @handle
    def create_collection(self, *, data: JsonSchemaModel) -> CollectionType:
        """Create a new collection"""
        try:
            # Create collection class
            klass = data.create_class()
            klass.init()
            col_id = klass.col_id()

            # Check if collection already exists
            col = self.db.get(col_id)
            if col:
                return self.get_collection(col_id=col_id)

            # Initialize collection

            # Store in database
            try:
                self.db[col_id] = json.dumps(klass.model_json_schema()).encode("utf-8")
                logger.info(f"Successfully created collection '{col_id}'")
            except Exception as e:
                # Cleanup if database operation fails
                raise QuipubaseException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to store collection schema: {str(e)}",
                )

            return {
                "name": klass.__name__,
                "id": col_id,
                "schema": JsonSchema(**klass.model_json_schema()),
            }

        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create collection: {str(e)}",
            )
