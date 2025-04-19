from __future__ import annotations
import typing as tp
from typing_extensions import TypedDict
from pydantic import BaseModel

Property = tp.Dict[str, tp.Any]
QuipuActions = tp.Literal["create", "update", "delete", "read", "query", "stop"]


class CollectionRequest(BaseModel):
    definition: JsonSchema
    name: str


class CollectionResponse(BaseModel):
    id: str
    definition: JsonSchema


class JsonSchema(TypedDict, total=False):
    """JSON Schema representation"""

    title: str
    description: str
    type: tp.Literal[
        "object", "array", "string", "number", "integer", "boolean", "null"
    ]

    properties: Property
    required: list[str]
    enum: list[tp.Union[int, float, str]]
    items: list[tp.Any]  # Avoiding recursive reference to JsonSchema
    additionalProperties: bool
    patternProperties: Property
    definitions: Property
    allOf: list[tp.Any]  # Avoiding recursive reference to JsonSchema
    oneOf: list[tp.Any]  # Avoiding recursive reference to JsonSchema


class CollectionType(BaseModel):
    id: str
    definition: JsonSchema


# The model_rebuild call will be moved to __init__.py to ensure all types are defined first
