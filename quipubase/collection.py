from typing import Any, Optional, Type, TypeVar, Iterator
from rocksdict import Rdict, Options, SliceTransform, PlainTableFactoryOptions
import os
import orjson
import json
import shutil
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from pathlib import Path
from .utils import get_logger, handle, encrypt

T = TypeVar("T", bound="Collection")

logger = get_logger("[Collections]")

class Collection(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    @classmethod
    def col(cls) -> Rdict:
        """Get or create a RocksDB instance for this collection."""
        return Rdict(cls.col_path(), cls.options())

    @classmethod
    def col_path(cls):
        home_dir = Path.home().as_posix()
        return os.path.join(home_dir, ".data", encrypt(cls.__name__))

    @classmethod
    def col_json_schema(cls):
        """Create a schema for this collection"""
        data = cls.model_json_schema()
        path = Path(os.path.join(cls.col_path(), "schema.json"))
        if not path.exists():
            path.write_text(json.dumps(data, indent=4))
        return data

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
    @handle
    def retrieve(cls: Type[T], *, id: UUID) -> Optional[T]:
        """Retrieve a single record by ID."""
        raw_data = cls.col().get(id.bytes)
        if raw_data is None:
            return None
        json_data = orjson.loads(raw_data)
        return cls.model_validate(json_data)

    @handle
    def create(self) -> None:
        """Save/update the record in the database."""
        self.col().put(self.id.bytes, self.model_dump_json().encode("utf-8"))

    @classmethod
    @handle
    def delete(cls, *, id: UUID) -> bool:
        """Delete a record by ID."""
        try:
            cls.col().delete(id.bytes)
            return True
        except KeyError:
            return False

    @classmethod
    @handle
    def find(cls: Type[T], *, limit: int = 100, offset: int = 0, **kwargs: Any) -> Iterator[T]:
        """
		Find records matching the given criteria.
		
		Yields:
			Model instances matching the criteria
		
		Args:
			limit: Maximum number of records to return
			offset: Number of matching records to skip
			**kwargs: Field equality filters
		"""
        # Simplify implementation to use dictionary items directly
        db = cls.col()
        riter = db.iter()
        riter.seek_to_first()
        while riter.valid() and offset:
            offset -= 1
            riter.next()
        while riter.valid() and limit:
            key = riter.key()
            value = riter.value()
            try:
                data = orjson.loads(value)
                # Check if the item matches all criteria
                matches = True
                for k, v in kwargs.items():
                    if k not in data or data[k] != v:
                        matches = False
                        break
                if matches:
                    # Convert UUID bytes back to UUID object for the id field
                    if isinstance(key, bytes) and len(key) == 16:
                        id_obj = UUID(bytes=key)
                    else:
                        id_obj = key
                    # Create model instance including the id
                    instance = cls.model_validate({"id": id_obj, **data})
                    yield instance
                    limit -= 1
                riter.next()
            except Exception as e:
                # Skip invalid entries
                logger.error(e)
                continue	# Skip invalid entries
        return None

    @classmethod
    @handle
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
