import json
from typing import Type

from fastapi import HTTPException, status
from prisma.models import CollectionModel as collection

from prisma import Json
from quipubase.lib.exceptions import QuipubaseException
from quipubase.lib.utils import encrypt, get_logger, singleton

from .typedefs import (Collection, CollectionType, DeleteCollectionReturnType,
                       JsonSchema, JsonSchemaModel)

logger = get_logger("[CollectionManager]")


@singleton
class CollectionManager:
    """Singleton for managing collection classes and exchanges"""

    def __init__(self):
        try:
            self.db = collection.prisma()
        except Exception as e:
            logger.error(f"Failed to initialize CollectionManager: {str(e)}")
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize CollectionManager: {str(e)}",
            )

    async def retrieve_collection(self, collection_id: str) -> Type[Collection]:
        """Get or create a collection class for a given collection ID"""
        try:
            data = await self.db.find_unique(where={"id": collection_id})
            if not data:
                raise QuipubaseException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{collection_id}' not found",
                )

            json_schema = json.loads(data.json_schema)
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

    async def get_json_schema(self, collection_id: str) -> JsonSchemaModel:
        """Get the JSON schema for a collection ID"""
        try:
            data = await self.db.find_unique(where={"id": collection_id})
            if not data:
                raise QuipubaseException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection '{collection_id}' not found",
                )

            json_schema = json.loads(data.json_schema)
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

    async def list_collections(self):
        """List all collections in the database"""
        try:
            for col in await self.db.find_many(take=100):
                yield {"sha": col.sha, "id": col.id}
        except Exception as e:
            logger.error(f"Failed to list collections: {str(e)}")
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to list collections",
            )

    async def get_collection(self, *, col_id: str) -> CollectionType:
        """Retrieve a collection class by ID"""
        try:
            klass = await self.retrieve_collection(col_id)
            sha = klass.col_id()
            col = await self.db.find_unique_or_raise(where={"sha": sha})
            return {
                "id": col.id,
                "sha": col.sha,
                "schema": JsonSchema(**json.loads(col.json_schema)),
            }
        except QuipubaseException as e:
            logger.error(f"Failed to get collection '{col_id}': {str(e)}")
            raise e

    async def delete_collection(self, *, col_id: str) -> DeleteCollectionReturnType:
        """Delete a collection by ID"""
        try:
            # Remove from database
            if not await self.db.find_unique(where={"id": col_id}):
                return {"code": 1}
            await self.db.delete(where={"id": col_id})
            return {"code": 0}
        except HTTPException as e:
            logger.error(f"Failed to delete collection '{col_id}': {str(e)}")
            return {"code": 500}
        except Exception as e:
            logger.error(f"Unexpected error deleting collection '{col_id}': {str(e)}")
            return {"code": 1}

    async def create_collection(self, *, data: JsonSchemaModel) -> CollectionType:
        """Create a new collection"""
        sha = encrypt(json.dumps(JsonSchema(**data.model_dump())))
        col = await self.db.find_unique(where={"sha": sha})
        if col is not None:
            klass = await self.retrieve_collection(col.id)
            return {
                "sha": col.sha,
                "id": col.id,
                "schema": JsonSchema(**klass.model_json_schema()),
            }
        try:
            # Create collection class
            klass = data.create_class()
            sha = klass.col_id()
            import uuid
            from datetime import datetime, timezone

            col = await self.db.create(
                data={
                    "id": str(uuid.uuid4()),
                    "sha": sha,
                    "json_schema": Json(json.dumps(klass.model_json_schema())),
                    "updated_at": datetime.now(timezone.utc),
                }
            )
            logger.info(f"Successfully created collection '{col.model_dump_json()}'")
        except Exception as e:
            # Cleanup if database operation fails
            raise QuipubaseException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store collection schema: {str(e)}",
            )

        return {
            "sha": col.sha,
            "id": col.id,
            "schema": JsonSchema(**klass.model_json_schema()),
        }
