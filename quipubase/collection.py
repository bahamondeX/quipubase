from typing import Any, Optional, Type, TypeVar, Iterator
from rocksdict import Rdict, Options, SliceTransform, PlainTableFactoryOptions
import os
import orjson
import json
import shutil
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from pathlib import Path
from .utils import get_logger, encrypt
from .typedefs import JsonSchemaModel

T = TypeVar("T", bound="Collection")

logger = get_logger("[Collections]")

class Collection(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    def __repr__(self):
        return self.model_dump_json(indent=4)

    def __str__(self):
        return self.__repr__()

    @classmethod
    def col(cls) -> Rdict:
        """Get or create a RocksDB instance for this collection."""
        return Rdict(cls.col_path(), cls.options())

    @classmethod
    def col_path(cls):
        home_dir = Path.home().as_posix()
        return os.path.join(
            home_dir, ".data", encrypt(json.dumps(cls.model_json_schema()))
        )

    @classmethod
    def col_json_schema(cls) -> JsonSchemaModel:
        """Create a schema for this collection"""
        data = cls.model_json_schema()
        path = Path(os.path.join(cls.col_path(), "schema.json"))
        if not path.exists():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            path.write_text(json.dumps(data, indent=4))
        return JsonSchemaModel(**data)

    @classmethod
    def cpu_count(cls):
        return os.cpu_count() or 1

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
    def retrieve(cls: Type[T], *, id: UUID) -> Optional[T]:
        """Retrieve a single record by ID."""
        raw_data = cls.col().get(id.bytes)
        if raw_data is None:
            return None
        json_data = orjson.loads(raw_data)
        return cls.model_validate(json_data)

    def create(self) -> None:
        """Save/update the record in the database."""
        self.col().put(self.id.bytes, self.model_dump_json().encode("utf-8"))

    @classmethod
    def delete(cls, *, id: UUID) -> bool:
        """Delete a record by ID."""
        try:
            cls.col().delete(id.bytes)
            return True
        except KeyError:
            return False

    @classmethod
    def find(cls: Type[T], *, limit: int = 100, offset: int = 0, **kwargs: Any) -> Iterator[T]:
        """
        Find records matching the given criteria.

        Args:
            limit: Max records to return
            offset: Records to skip
            **kwargs: Field filters

        Yields:
            Matching model instances
        """
        db = cls.col()
        riter = db.iter()
        riter.seek_to_first()

        # Saltar offset inicial
        while riter.valid() and offset > 0:
            riter.next()
            offset -= 1

        # Iterar hasta cumplir el límite
        while riter.valid() and limit > 0:
            try:
                data = orjson.loads(riter.value())
                if all(data.get(k) == v for k, v in kwargs.items() if k != "id"):
                    yield cls.model_validate(data)
                    limit -= 1
            except Exception as e:
                logger.error(f"Error parsing record: {e}")
            riter.next()  # Asegurar avance siempre

    @classmethod
    def update(cls: Type[T], *, id: UUID, **kwargs: Any) -> Optional[T]:
        """Update specific fields of a record by ID."""
        # Get the current record
        record = cls.retrieve(id=id)
        if record is None:
            return None

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
    def destroy(cls):
        try:
            shutil.rmtree(cls.col_path())
            return 0
        except Exception as e:
            logger.error(e)
            return 1


Collection.model_rebuild()
