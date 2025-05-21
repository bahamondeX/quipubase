# In typedefs.py
from typing import Any, Dict, Literal, Optional, TypeAlias

from pydantic import BaseModel, Field, InstanceOf
from typing_extensions import NotRequired, TypedDict

# Define QuipuActions as a type alias for a set of string literals
QuipuActions: TypeAlias = Literal["create", "read", "update", "delete", "query", "stop"]


# First define the JsonSchema as a regular Pydantic model (not TypedDict)
class JsonSchemaModel(BaseModel):
    """JSON Schema representation"""

    model_config = {"extra": "allow"}
    title: str = Field(...)
    type: str = Field(default="object")
    properties: Dict[str, Any] = Field(...)
   

# Keep TypedDict version if needed elsewhere
class JsonSchema(TypedDict):
    """JSON Schema representation"""

    title: str
    description: NotRequired[str]
    type: str
    properties: Dict[str, Any]
    enum: NotRequired[list[Any]]

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
    id: Optional[str] = Field(default=None)
    data: Optional[Dict[str, Any]] = Field(default=None)
