# In typedefs.py
from typing import Any, Dict, Literal, Optional, TypeAlias

from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict, Required

# Define QuipuActions as a type alias for a set of string literals
QuipuActions: TypeAlias = Literal["create", "read", "update", "delete", "query", "stop"]


# First define the JsonSchema as a regular Pydantic model (not TypedDict)
class JsonSchemaModel(BaseModel):
    """JSON Schema representation"""

    model_config = {"extra": "allow"}
    title: str = Field(..., examples=["Task"])
    type: str = Field(default="object",examples=["object"])
    properties: Dict[str, Any] = Field(...,examples=[{"done":{"type":"boolean"},"title":{"type":"string"},"description":{"type":"string"}}])
    required:list[str] = Field(...,examples=[["title","done"]])

# Keep TypedDict version if needed elsewhere
class JsonSchema(TypedDict,total=False):
    """JSON Schema representation"""

    title: NotRequired[str]
    description: NotRequired[str]
    type: Required[str]
    properties: Required[Dict[str, Any]]
    required: NotRequired[list[str]]

class CollectionType(TypedDict):
    id: str
    name: str
    schema: JsonSchema


class CollectionMetadataType(TypedDict):
    id: str
    name: str


class DeleteCollectionReturnType(TypedDict):
    code: int

class QuipubaseRequest(BaseModel):
    event: QuipuActions = Field(default="query")
    id: Optional[str] = Field(default=None)
    data: Optional[Dict[str, Any]] = Field(default=None)
