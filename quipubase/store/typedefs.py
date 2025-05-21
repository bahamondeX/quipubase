"""
Vector Store Type Definitions
===========================

This module contains type definitions and Pydantic models used in the vector store
implementation. It provides the core data structures for managing embeddings and
vector similarity search operations.

Key Features:
- Embedding model for storing text content and vector representations
- QueryMatch for similarity search results
- Response types for upsert, query, and delete operations
- JSON serialization support for complex types

Dependencies:
- numpy: For numerical operations and array handling
- pydantic: For data validation and serialization
- rocksdict: For persistent storage
"""

import typing as tp
from pathlib import Path
from uuid import uuid4

import numpy as np
import orjson
import typing_extensions as tpe
from numpy.typing import NDArray
from pydantic import (BaseModel, Field, WithJsonSchema, field_serializer,
                      field_validator)
from rocksdict import Rdict


class Embedding(BaseModel):
    """
    Represents a text embedding with associated metadata.

    Attributes:
        id (str): Unique identifier for the embedding (auto-generated UUID)
        content (str | list[str]): Text content or list of strings
        embedding (NDArray[np.float32]): Vector representation of the content
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str | list[str]
    embedding: tp.Annotated[
        NDArray[np.float32],
        WithJsonSchema({"type": "array", "items": {"type": "number"}}),
    ]

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            NDArray: lambda v: v.tolist(),
            np.ndarray: lambda v: v.tolist(),
        },
    }

    @field_serializer("embedding")
    @classmethod
    def serialize_embedding(cls, v: tp.Any):
        if isinstance(v, np.ndarray):
            return v.tolist()

    @field_validator("embedding", mode="before")
    @classmethod
    def validate_embedding(cls, v: tp.Any):  # type: ignore
        if isinstance(v, list):
            return np.array(v, dtype=np.float32)
        elif isinstance(v, np.ndarray):
            return v  # type: ignore
        raise ValueError(f"Expected list or numpy array, got {type(v)}")

    @classmethod
    def db(cls, *, namespace: str):
        return Rdict(str(Path.home() / ".vector" / namespace))

    @classmethod
    def retrieve(cls, *, id: str, namespace: str):
        db = cls.db(namespace=namespace)
        item = db.get(id)
        if item is None:
            return None
        return cls(**orjson.loads(item))

    def create(self, *, namespace: str):
        db = self.db(namespace=namespace)
        db[self.id] = self.model_dump_json()
        return self

    @classmethod
    def delete(cls, *, id: str, namespace: str):
        db = cls.db(namespace=namespace)
        if db.key_may_exist(id):
            del db[id]

    @classmethod
    def scan(cls, *, namespace: str):
        db = cls.db(namespace=namespace)
        iterable = db.iter()
        iterable.seek_to_first()
        while iterable.valid():
            try:
                value = iterable.value()
                yield cls(**orjson.loads(value))
                iterable.next()
            except:
                iterable.next()
                continue


class QueryMatch(BaseModel):
    """
    Represents a similarity search result.

    Attributes:
        score (float): Similarity score between 0 and 1
        content (str): Text content of the matched item
        embedding (NDArray[np.float32]): Vector representation of the matched item
    """

    model_config = {
        "arbitrary_types_allowed": True,
        "json_encoders": {
            NDArray: lambda v: v.tolist(),
            np.ndarray: lambda v: v.tolist(),
        },
    }

    score: float
    content: str


class SemanticContent(tpe.TypedDict):
    """
    Typed dictionary for storing semantic content information.

    Fields:
        id (str): Unique identifier
        content (str): Text content
    """

    id: str
    content: str


class UpsertResponse(tpe.TypedDict):
    """
    Response type for upsert operations.

    Fields:
        contents (list[SemanticContent]): List of inserted/updated items
        upsertedCount (int): Number of items processed
    """

    contents: list[SemanticContent]
    upsertedCount: int


class QueryResponse(tpe.TypedDict):
    """
    Response type for similarity search queries.

    Fields:
        matches (list[QueryMatch]): List of matching items
        readCount (int): Total number of items considered
    """

    matches: list[QueryMatch]
    readCount: int


class DeleteResponse(tpe.TypedDict):
    """
    Response type for delete operations.

    Fields:
        embeddings (list[str]): List of deleted item IDs
        deletedCount (int): Number of items deleted
    """

    embeddings: list[str]
    deletedCount: int


class EmbedResponse(tpe.TypedDict):
    data: list[Embedding]
    created: float
    embedCount: int
