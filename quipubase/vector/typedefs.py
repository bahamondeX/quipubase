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

import os
import typing as tp

import numpy as np
import orjson
import typing_extensions as tpe
from numpy.typing import NDArray
from pydantic import BaseModel, WithJsonSchema, field_serializer, field_validator, computed_field
from rocksdict import Rdict

from quipubase.utils.utils import handle, encrypt

DIR: str = "./data"
EMB: str = "/embeddings/"

Texts: tpe.TypeAlias = tp.Union[str, list[str]]
EmbeddingModel: tpe.TypeAlias = tp.Literal["poly-sage", "deep-pulse", "mini-scope"]
Semantic: tpe.TypeAlias = tp.Union[Texts, NDArray[np.float32]]


class Embedding(BaseModel):
    """
    Represents a text embedding with associated metadata.

    Attributes:
        id (str): Unique identifier for the embedding (auto-generated UUID)
        content (str | list[str]): Text content or list of strings
        embedding (NDArray[np.float32]): Vector representation of the content
    """
    model_config = {
        "extra": "allow",
        "arbitrary_types_allowed": True,
        "json_encoders": {
            NDArray: lambda v: v.tolist(),
            np.ndarray: lambda v: v.tolist(),
        },
    }
    content: str
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

    @computed_field(return_type=str)
    @property
    def id(self):
        return encrypt(self.content)
    
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
        os.makedirs(f"{DIR}/", exist_ok=True)
        if not os.path.exists(f"{DIR}{EMB}{namespace}"):
            os.makedirs(f"{DIR}{EMB}{namespace}", exist_ok=True)
        return Rdict(f"{DIR}{EMB}{namespace}")

    @classmethod
    @handle
    def retrieve(cls, *, id: str, namespace: str):
        db = cls.db(namespace=namespace)
        item = db.get(id)
        if item is None:
            return None
        return cls(**orjson.loads(item))

    @handle
    def create(self, *, namespace: str):
        db = self.db(namespace=namespace)
        if db.key_may_exist(self.id):
            data = db.get(self.id)
            if data is None:
                db[self.id] = self.model_dump_json()
        db[self.id] = self.model_dump_json()
        return self

    @classmethod
    @handle
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
    id: str
    score: float
    content: str


class EmbedText(BaseModel):
    """
    Base input for embedding text content.
    Attributes:
        content (list[str]): List of text strings to be embedded
        model (EmbeddingModel): Model type for generating embeddings    
    """
    model_config = {
        "extra": "allow",
        "arbitrary_types_allowed": True,
        "json_encoders": {
            NDArray: lambda v: v.tolist(),
            np.ndarray: lambda v: v.tolist(),
        },
        "json_schema_extra": {
            "description": "Base model for text embeddings",
            "examples": [
                {
                    "content": ["I love Quipubase!", "I love myself!", "I love my family!", "I love my friends!", "I love my country!", "I love my job!"],
                    "model": "poly-sage"
                }
            ]
        }
    }
  
    content: list[str]
    model: EmbeddingModel

class QueryText(EmbedText):
    model_config = {
        "json_schema_extra": {
            "description": "Model for querying text embeddings",
            "examples": [
                {
                    "content": ["I love you!"],
                    "model": "poly-sage",
                    "namespace": "quipubase",
                    "top_k": 5
                }
            ]
        }
    }
    top_k: int


class DeleteText(BaseModel):
    ids: list[str]


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
        count (int): Number of items processed
    """

    data: list[SemanticContent]
    count: int
    ellapsed: float


class QueryResponse(tpe.TypedDict):
    """
    Response type for similarity search queries.

    Fields:
        matches (list[QueryMatch]): List of matching items
        count (int): Total number of items considered
    """

    data: list[QueryMatch]
    count: int
    ellapsed:float


class DeleteResponse(tpe.TypedDict):
    """
    Response type for delete operations.

    Fields:
        embeddings (list[str]): List of deleted item IDs
        count (int): Number of items deleted
        ellapsed (float): Seconds taken to perform the action
    """

    data: list[str]
    count: int
    ellapsed: float


class EmbedResponse(tpe.TypedDict):
    data: list[Embedding]
    count: int
    ellapsed: float
