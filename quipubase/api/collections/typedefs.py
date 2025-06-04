"""Data Modelation module"""

import json
import os
import typing as tp
from pathlib import Path
from uuid import uuid4

import typing_extensions as tpe
from pydantic import BaseModel, Field

import orjson
from pydantic import BaseModel, Field, create_model  # pylint: disable=W0611
from rocksdict import Options  # pylint: disable=E0611
from rocksdict import PlainTableFactoryOptions  # pylint: disable=E0611
from rocksdict import Rdict, SliceTransform

from quipubase.lib.utils import encrypt, get_logger, handle


T = tp.TypeVar("T", bound="Collection")

logger = get_logger("[Collections]")


MAPPING: dict[str, tp.Type[tp.Any]] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
    "null": type(None),
}

QuipuActions: tpe.TypeAlias = tp.Literal["create", "read", "update", "delete", "query", "stop"]

class SubResponse(BaseModel, tp.Generic[T]):
    """Event model"""

    event: QuipuActions
    data: T | list[T]


class PubResponse(BaseModel, tp.Generic[T]):
    collection: str
    data: T | list[T]
    event: QuipuActions

class JsonSchema(tpe.TypedDict, total=False):
    """JSON Schema representation"""

    title: tpe.NotRequired[str]
    description: tpe.NotRequired[str]
    type: tpe.Required[str]
    properties: tpe.Required[tp.Dict[str, tp.Any]]
    required: tpe.NotRequired[list[str]]
    
# First define the JsonSchema as a regular Pydantic model (not TypedDict)
class JsonSchemaModel(BaseModel):
    """JSON Schema representation"""

    model_config = {"extra": "allow", "arbitrary_types_allowed": True, "cache_strings": True, "json_schema_extra": {"example": {
        "title": "Task",
        "type": "object",
        "properties": {
            "done": {"type": "boolean"},
            "title": {"type": "string"},
            "description": {"type": "string"}
        },
        "required": ["title", "done"]
    }}}
    title: str = Field(...)
    type: str = Field(default="object")
    properties: tp.Dict[str, tp.Any] = Field(
        ...,
    )
    required: tp.Optional[list[str]] = Field(default=None)
    description: tp.Optional[str] = Field(default=None)

    def _process_type(self, schema: tp.Dict[str, tp.Any] , depth: int = 0) -> tp.Any:
        """Helper method to process types with recursion control"""
        if depth > 10:  # Max nesting depth
            return str

        if "enum" in schema:
            enum_values = schema.get("enum", [])
            if enum_values and all(isinstance(v, type(enum_values[0])) for v in enum_values):
                return tp.Literal[tuple(enum_values)]  # type: ignore
                
        schema_type = schema.get("type", "string")
        
        if schema_type == "object" and "properties" in schema:
            # Create nested model
            nested_attrs:tp.Dict[str, tp.Any]  = {}
            for key, prop_schema in schema["properties"].items():
                is_required = "required" in schema and key in schema["required"]
                field_type = self._process_type(prop_schema, depth + 1)
                
                if is_required:
                    nested_attrs[key] = (field_type, ...)
                else:
                    nested_attrs[key] = (tp.Optional[field_type], None)
                    
            model_name = f"Nested_{self.title}_{depth}_{abs(hash(str(schema)))}"
            return create_model(model_name, **nested_attrs)
            
        elif schema_type == "array" and "items" in schema:
            item_type = self._process_type(schema["items"], depth + 1)
            return tp.List[item_type]
            
        return MAPPING.get(schema_type, str)

    def create_class(self):
        """Create a class based on the schema with recursion control"""
        attributes:tp.Dict[str, tp.Any]  = {}
        for key, prop_schema in self.properties.items():
            is_required = self.required and key in self.required
            field_type = self._process_type(prop_schema)
            
            if is_required:
                attributes[key] = (field_type, ...)
            else:
                attributes[key] = (tp.Optional[field_type], Field(default=None))

        model_name = f"{self.title}::{encrypt(self.model_dump_json(exclude_none=True))}"
        return create_model(model_name, __base__=Collection, **attributes)

    def cast_to_type(self) -> tp.Any:
        """Cast the schema to the corresponding Python type"""
        return self._process_type(self.model_dump())


class CollectionType(tpe.TypedDict):
    id: str
    name: str
    schema: JsonSchema


class CollectionMetadataType(tpe.TypedDict):
    id: str
    name: str


class DeleteCollectionReturnType(tpe.TypedDict):
    code: int



class QuipubaseRequest(BaseModel):
    """
    Quipubase Request
    A model representing a request to the Quipubase API. This model includes fields for the action type, record ID, and any additional data required for the request.
    Attributes:
        event (QuipuActions): The action to be performed (create, read, update, delete, query).
        id (Optional[str]): The unique identifier for the record. If None, a new record will be created.
        data (Optional[Dict[str, Any]]): Additional data required for the request. This can include fields to update or query parameters.
    """
    model_config = {
        "extra": "ignore",
        "arbitrary_types_allowed": True,
        "json_schema_extra": {
            "example": {
                "event": "create",
                "id": None,
                "data": {
                    "title": "Example Record",
                    "description": "This is an example record for testing purposes.",
                    "done": False,
                }
            }
        }
    }
    event: QuipuActions = Field(default="query")
    id: tp.Optional[str] = Field(default=None)
    data: tp.Optional[tp.Dict[str, tp.Any]] = Field(default=None)


class Collection(BaseModel):
    """
    Collection

    A base model class for managing a RocksDB-backed collection of records. This class provides methods for creating, retrieving, updating, deleting, and querying records, as well as managing the underlying database schema and configuration.

    Attributes:
        id (Optional[UUID]): The unique identifier for the record, autogenerated by default.

    Methods:
        col() -> Rdict:
            Get or create a RocksDB instance for this collection.

        col_path() -> str:
            Get the absolute path to the collection directory.

        col_json_schema() -> JsonSchemaModel:
            Create and persist a JSON schema for this collection.

        cpu_count() -> int:
            Get the number of CPU cores available.

        tool_definition() -> dict[str, Any]:
            Generate tool parameters for `OpenAI` function calling.

        tool_param() -> dict:
            Generate tool parameters for `Anthropic` function calling.

        options() -> Options:
            Configure RocksDB options for optimal performance.

        retrieve(cls, *, id: UUID) -> Optional[T]:
            Retrieve a single record by its ID.

        create(self) -> None:
            Save or update the current record in the database.

        delete(cls, *, id: UUID) -> bool:
            Delete a record by its ID.

        find(cls, *, limit: int = 100, offset: int = 0, **kwargs: Any) -> Iterator[T]:

        update(cls, *, id: UUID, **kwargs: Any) -> Optional[T]:
            Update specific fields of a record by its ID.

        destroy(cls) -> int:
            Delete the entire collection and its data.

        init(cls) -> None:
            Initialize the collection by creating necessary directories and files.
    """

    id: tp.Optional[str] = Field(default_factory=lambda: str(uuid4()))
    model_config = {
        "extra": "allow",
        "arbitrary_types_allowed": True
    }
    def __init__(self, **kwargs: tp.Any):
        super().__init__(**kwargs)
        if self.id is None:
            self.id = str(uuid4())

    def __repr__(self):
        return self.model_dump_json(indent=4)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def db(cls) -> Rdict:
        """Get or create a RocksDB instance for this collection."""
        return Rdict(cls.col_path(), cls.options())

    @classmethod
    def col_path(cls):
        """The absolute path to the collection directory."""
        base_dir = Path("./data/collections").as_posix()
        if not os.path.exists(os.path.join(base_dir, cls.col_id())):
            os.makedirs(os.path.join(base_dir, cls.col_id()), exist_ok=True)
        return os.path.join(base_dir, cls.col_id())

    @classmethod
    def col_id(cls):
        return encrypt(json.dumps(cls.model_json_schema(), sort_keys=True))

    @classmethod
    def col_json_schema(cls) -> JsonSchemaModel:
        """Create a schema for this collection"""
        return JsonSchemaModel(**cls.model_json_schema())

    @classmethod
    def cpu_count(cls):
        """Get the number of CPU cores available."""
        return os.cpu_count() or 1

    @classmethod
    def tool_openai(cls) -> dict[str, tp.Any]:
        """Generate tool parameters for `OpenAI` function calling."""
        return {
            "type": "function",
            "function": {
                "name": cls.__name__,
                "description": cls.__doc__ or "",
                "parameters": cls.model_json_schema().get("properties", {}),
            },
        }

    @classmethod
    def tool_anthropic(cls) -> dict[str, tp.Any]:
        """Generate tool parameters for `Anthropic` function calling."""
        return {
            "input_schema": cls.model_json_schema(),
            "name": cls.__name__,
            "description": cls.__doc__ or "",
            "cache_control": {"type": "ephemeral"},
        }

    @classmethod
    def options(cls) -> Options:
        """Configure RocksDB options for optimal performance."""
        opt = Options()
        opt.create_if_missing(True)
        opt.set_max_background_jobs(cls.cpu_count())
        opt.set_write_buffer_size(0x10000000)
        opt.set_level_zero_file_num_compaction_trigger(4)
        opt.set_max_bytes_for_level_base(0x40000000)
        opt.set_target_file_size_base(0x10000000)
        opt.set_max_bytes_for_level_multiplier(4.0)
        opt.set_prefix_extractor(SliceTransform.create_max_len_prefix(8))
        opt.set_plain_table_factory(PlainTableFactoryOptions())
        return opt

    @classmethod
    @handle
    def retrieve(cls: tp.Type[T], *, id: str) -> T:  # pylint: disable=W0622
        """Retrieve a single record by ID."""
        raw_data = cls.db().get(id)
        if raw_data is None:
            raise KeyError(f"Record {id} not found")
        json_data = orjson.loads(raw_data)  # pylint: disable=E1101
        return cls.model_validate(json_data)
    @handle
    def create(self) -> None:
        """Save/update the record in the database."""
        if self.id is None:
            self.id = str(uuid4())
        data = self.model_dump_json(exclude_none=True).encode("utf-8")
        self.db().put(self.id, data)  # pylint: disable=E1101
        assert (
            self.db().get(self.id) == data  # pylint: disable=E1101
        ), f"Failed to persist record {self.id}"

    @classmethod
    @handle
    def delete(cls, *, id: str) -> bool:  # pylint: disable=W0622
        """Delete a record by ID."""
        try:
            cls.db().delete(id)
            return True
        except KeyError:
            return False

    @classmethod
    def find(
        cls: tp.Type[T], *, limit: int = 100, offset: int = 0, **kwargs: tp.Any
    ) -> tp.Iterator[T]:
        """
        Find records matching the given criteria.

        Args:
            limit: Max records to return
            offset: Records to skip
            **kwargs: Field filters

        Yields:
            Matching model instances
        """
        riter = cls.db().iter()
        riter.seek_to_first()

        # Saltar offset inicial
        while riter.valid() and offset > 0:
            riter.next()
            offset -= 1

        # Iterar hasta cumplir el límite
        while riter.valid() and limit > 0:
            try:
                data = orjson.loads(riter.value())  # pylint: disable=E1101
                if all(data.get(k) == v for k, v in kwargs.items() if k != "id"):
                    yield cls.model_validate(data)
                    limit -= 1
            except Exception as e:  # pylint: disable=W0718
                logger.error("Error parsing record: %s", e)
            riter.next()

    @classmethod
    @handle
    def update(
        cls: tp.Type[T], *, id: str, **kwargs: tp.Any
    ) -> tp.Optional[T]:  # pylint: disable=W0622
        """Update specific fields of a record by ID."""
        # Get the current record
        record = cls.retrieve(id=id)
        # Update the fields
        record_dict = record.model_dump()
        for field_name, new_value in kwargs.items():
            if field_name in record_dict and field_name != "id":
                record_dict[field_name] = new_value

        # Create updated instance
        updated_record = cls.model_validate(record_dict)
        updated_record.create()

        return updated_record

    @classmethod
    def init(cls):
        data = cls.model_json_schema()
        if not os.path.exists(cls.col_path()):
            os.makedirs(cls.col_path(), exist_ok=True)
        schema_json_path = Path(cls.col_path()) / "schema.json"
        schema_json_path.write_text(json.dumps(data, sort_keys=True))


Collection.model_rebuild()
QuipubaseRequest.model_rebuild()