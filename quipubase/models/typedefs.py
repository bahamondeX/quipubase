# In typedefs.py
import uuid
from typing import Any, Dict, Literal, Optional, TypeAlias

from pydantic import BaseModel, Field, InstanceOf
from typing_extensions import NotRequired, TypedDict

# Define QuipuActions as a type alias for a set of string literals
QuipuActions: TypeAlias = Literal["create", "read", "update", "delete", "query", "stop"]

JsonSchemaType: TypeAlias = Literal[
    "object", "array", "string", "number", "integer", "boolean", "null"
]


# First define the JsonSchema as a regular Pydantic model (not TypedDict)
class JsonSchemaModel(BaseModel):
    """JSON Schema representation"""

    title: str = Field(...)
    description: Optional[str] = Field(default=None)
    type: JsonSchemaType = Field(default="object")
    properties: Dict[str, Any] = Field(..., alias="properties")
    required: Optional[list[str]] = Field(default=None, alias="required")
    enum: Optional[list[Any]] = Field(default=None, alias="enum")
    items: Optional[Any] = Field(default=None, alias="items")


# Keep TypedDict version if needed elsewhere
class JsonSchema(TypedDict):
    """JSON Schema representation"""

    title: str
    description: NotRequired[str]
    type: JsonSchemaType
    properties: Dict[str, Any]
    enum: NotRequired[list[Any]]
    items: NotRequired[Any]


class CollectionType(TypedDict):
    id: str
    name: str
    schema: JsonSchema


class CollectionMetadataType(TypedDict):
    id: str
    name: str


class DeleteCollectionReturnType(TypedDict):
    code: int


class PubReturnType(TypedDict):
    collection: str
    data: InstanceOf[BaseModel]
    event: QuipuActions


class QuipubaseRequest(BaseModel):
    event: QuipuActions = Field(default="query")
    id: Optional[uuid.UUID] = Field(default=None)
    data: Optional[Dict[str, Any]] = Field(default=None)
