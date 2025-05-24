"""
Vector Store Implementation
=========================

This module implements the vector store functionality for managing embeddings and
performing similarity searches. It provides a high-level interface for storing,
retrieving, and searching vector data.

Key Features:
- Persistent storage using RocksDB
- Vector similarity search
- Embedding generation using configurable models
- Batch operations for efficient data management

Dependencies:
- numpy: For numerical operations and array handling
- rocksdb: For persistent storage
- pydantic: For data validation and serialization
"""

import typing as tp
from dataclasses import dataclass
from functools import cached_property

import numpy as np
from numpy.typing import NDArray

from ..typedefs import (
    DeleteResponse,
    Embedding,
    QueryResponse,
    SemanticContent,
    UpsertResponse,
)
from .embeddings import EmbeddingModel, EmbeddingService


@dataclass
class VectorStoreService(tp.Hashable):
    """
    Vector store implementation for managing embeddings and similarity searches.

    Args:
        namespace (str): The namespace for this store instance
        model (EmbeddingModel): The embedding model to use for text encoding

    Attributes:
        namespace (str): The namespace for this store instance
        model (EmbeddingModel): The embedding model used for text encoding
        service (EmbeddingService): Cached embedding service instance
    """

    namespace: str
    model: EmbeddingModel

    @cached_property
    def client(self) -> EmbeddingService:
        """
        Get the cached embedding service instance.

        Returns:
            EmbeddingService: Service instance for generating embeddings
        """
        return EmbeddingService(self.model)

    def upsert(self, vectors: list[Embedding]) -> UpsertResponse:
        """
        Insert or update embeddings in the store.

        Args:
            vectors (list[Embedding]): List of embeddings to insert/update

        Returns:
            UpsertResponse: Response containing inserted IDs and count

        Example:
            >>> store.upsert([
            ...     Embedding(content="Hello world", embedding=[0.1, 0.2, 0.3])
            ... ])
        """
        embeddings: list[Embedding] = []
        for vector in vectors:
            embeddings.append(
                Embedding(content=vector.content, embedding=vector.embedding)
            )
        for embedding in embeddings:
            embedding.create(namespace=self.namespace)
        return UpsertResponse(
            contents=[
                SemanticContent(
                    id=embedding.id,
                    content=(
                        embedding.content
                        if isinstance(embedding.content, str)
                        else ", ".join(embedding.content)
                    ),
                )
                for embedding in embeddings
            ],
            upsertedCount=len(embeddings),
        )

    def get(self, id: str) -> tp.Optional[Embedding]:
        """
        Retrieve an embedding by its ID.

        Args:
            id (str): ID of the embedding to retrieve

        Returns:
            tp.Optional[Embedding]: Retrieved embedding or None if not found
        """
        return Embedding.retrieve(id=id, namespace=self.namespace)

    def scan(self) -> tp.List[Embedding]:
        return list(Embedding.scan(namespace=self.namespace))

    def delete(self, ids: list[str]) -> DeleteResponse:
        """
        Delete embeddings by IDs.

        Args:
            ids (list[str] | None): List of IDs to delete, or None to delete all

        Returns:
            DeleteResponse: Response containing deleted IDs and count

        Example:
            >>> response = store.delete(["id1", "id2"])
        """
        for id in ids:
            Embedding.delete(id=id, namespace=self.namespace)
        return DeleteResponse(embeddings=ids, deletedCount=len(ids))

    def embed(self, text: tp.Union[str, list[str]]) -> NDArray[np.float32]:
        """
        Generate embeddings for the given text.

        Args:
            text (tp.Union[str, list[str]]): Text to generate embeddings for

        Returns:
            NDArray[np.float32]: Generated embeddings
        """
        if isinstance(text, str):
            text = [text]
        return self.client.encode(text)

    def query(self, query_vector: list[float], top_k: int = 3):
        """
        Perform a similarity search using cosine similarity.

        Args:
            query_vector (list[float] | NDArray[np.float32]): Query vector
            top_k (int): Number of top results to return (default: 3)

        Returns:
            QueryResponse: Response containing matches and read count

        Example:
            >>> query_vector = store.embed("Find similar content")
            >>> response = store.query(query_vector, top_k=5)
        """
        corpus = list(Embedding.scan(namespace=self.namespace))
        matches = self.client.search(query_vector, corpus, top_k)
        return QueryResponse(matches=matches, readCount=len(matches))
