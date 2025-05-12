from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional, Type, Union

from pydantic import BaseModel, Field, create_model  # type: ignore

from ..models.const import MAPPING
from ..models.typedefs import JsonSchema, JsonSchemaModel
from .collection import Collection


def sanitize(text: str):
    """
    Sanitize the text by removing the leading and trailing whitespaces.
    """
    if text[:2] == "```":
        text = text[7:]
    if text[-3:] == "```":
        text = text[:-3]
    try:
        jsonified = json.loads(text)
        if "data" in jsonified:
            assert isinstance(jsonified["data"], list)
        else:
            raise ValueError("Invalid JSON format")
    except (Exception, ValueError, IndexError) as e:
        raise Exception(f"{e.__class__.__name__}: {e}") from e  # pylint: disable=W0719
    return jsonified["data"]


def parse_anyof_oneof(
    namespace: str, schema: Dict[str, Any]
) -> Union[Type[BaseModel], None]:
    """
    Parse the 'anyOf' or 'oneOf' schema and return the corresponding Union type.
    """
    for i in ("anyOf", "oneOf", "allOf"):
        if i in schema:
            return Union[
                tuple[type](cast_to_type(namespace, sub_schema) for sub_schema in schema[i])  # type: ignore
            ]
    return None


def cast_to_type(schema: JsonSchema) -> Any:
    """
    Cast the schema to the corresponding Python type.
    """
    if "enum" in schema:
        enum_values = tuple(schema.get("enum") or [])
        if enum_values and all(
            isinstance(value, type(enum_values[0])) for value in enum_values
        ):
            return Literal[enum_values]
    elif schema.get("type") == "object":
        if schema.get("properties"):
            s = JsonSchema(**schema)
            return create_class(schema=JsonSchemaModel.model_validate(s))
    elif schema.get("type") == "array":
        assert "items" in schema, "Missing 'items' in array schema"
        return List[cast_to_type((schema.get("items") or {}))]  # type: ignore
    return MAPPING.get(schema.get("type", "string"), str)


def create_class(*, schema: JsonSchemaModel):
    """
    Create a class based on the schema.
    """
    name = schema.title
    properties = schema.properties
    attributes: dict[str, Any] = {}
    for key, value in properties.items():
        if schema.required and key in schema.required:
            attributes[key] = (cast_to_type(value), ...)
        else:
            attributes[key] = (
                Optional[cast_to_type(value)],
                Field(default=None),
            )
    return create_model(
        f"{name}::{abs(hash(schema.model_dump_json()))}",
        __base__=Collection,
        **attributes,
    )
