"""
Embedding Service Implementation
=============================

This module provides the embedding service implementation for generating vector
representations of text data and performing similarity searches. It supports
multiple embedding models and provides efficient vector operations.

Key Features:
- Multiple embedding model support
- Efficient vector operations
- Similarity search using FAISS
- Text embedding generation

Dependencies:
- numpy: For numerical operations and array handling
- faiss: For efficient similarity search
- light_embed: For embedding model management
"""

import functools as ft
import typing as tp
from dataclasses import dataclass

import faiss  # type: ignore
import numpy as np
import typing_extensions as tpx
from light_embed import TextEmbedding  # type: ignore
from numpy.typing import NDArray

from ..typedefs import Embedding, EmbeddingModel, QueryMatch, Semantic

Texts: tpx.TypeAlias = tp.Union[str, list[str]]


MODELS: dict[EmbeddingModel, str] = {
    "poly-sage": "nomic-ai/nomic-embed-text-v1.5",
    "deep-pulse": "sentence-transformers/all-mpnet-base-v2",
    "mini-scope": "sentence-transformers/all-MiniLM-L6-v2",
}


@dataclass
class EmbeddingService(tp.Hashable):
    """
    Service for generating vector representations and performing similarity searches.

    Args:
            model (EmbeddingModel): The embedding model to use

    Attributes:
            model (EmbeddingModel): The embedding model instance
    """

    model: EmbeddingModel

    @ft.cached_property
    def client(self) -> TextEmbedding:
        """
        Get the embedding model client.

        Returns:
                TextEmbedding: The embedding model client instance
        """
        return TextEmbedding(
            MODELS[self.model],  # type: ignore
        )

    def encode(self, data: Texts) -> NDArray[np.float32]:
        """
        Generate embeddings for text.

        Args:
                data (str | list[str]): Text or list of texts to embed

        Returns:
                NDArray[np.float32]: Generated embeddings

        Example:
                >>> service = EmbeddingService(...)
                >>> embeddings = service.encode("Hello world")
                >>> embeddings = service.encode(["Hello", "world"])
        """
        if isinstance(data, str):
            data = [data]
        if not data:
            return np.array([], dtype=np.float32).reshape(
                0, 768 if self.model != "mini-scope" else 384
            )

        raw_output = self.client.encode(data)  # type: ignore
        return np.asarray(
            raw_output, dtype=np.float32
        )  # force conversion if not ndarray

    def semantic_to_numpy(self, semantic: Semantic) -> NDArray[np.float32]:
        """
        Convert semantic input to numpy array.

        Args:
                semantic (Semantic): Input data (text, list, or numpy array)

        Returns:
                NDArray[np.float32]: Numpy array representation

        Raises:
                ValueError: If input type is not supported

        Example:
                >>> service.semantic_to_numpy("Hello")
                >>> service.semantic_to_numpy(["Hello", "world"])
        """
        if isinstance(semantic, (list, str)):
            return self.encode(semantic)
        if semantic.dtype != np.float32:
            semantic = semantic.astype(np.float32)
        if semantic.size == 0:
            return np.array([], dtype=np.float32).reshape(
                0, 768 if self.model != "mini-scope" else 384
            )
        return semantic

    def search(
        self,
        query: list[float],
        corpus: list[Embedding],
        top_k: int = 3,
    ) -> list[QueryMatch]:
        if not corpus:
            return []

        corpus_embeddings = np.array([c.embedding for c in corpus], dtype=np.float32)
        corpus_embeddings = corpus_embeddings.reshape(len(corpus), -1)
        query_embedding = np.array(query, dtype=np.float32).reshape(1, -1)
        dimension = corpus_embeddings.shape[1]

        # Normalize the query and corpus embeddings
        def normalize(vectors: tp.Any):
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)  # type: ignore
            return vectors / norms  # type: ignore

        normalized_query = normalize(query_embedding)
        normalized_corpus = normalize(corpus_embeddings)

        # Build the Faiss index for inner product search
        index = faiss.IndexFlatIP(dimension)
        index.add(normalized_corpus)  # type: ignore

        # Perform the search for top_k results
        distances, indices = index.search(normalized_query, min(top_k, len(corpus)))  # type: ignore

        # Prepare the results as a list of dictionaries
        results: list[QueryMatch] = []
        for i in range(len(distances[0])):  # type: ignore
            result_dict = QueryMatch(
                score=distances[0][i],  # type: ignore
                content=corpus[indices[0][i]].content,  # type: ignore
            )
            results.append(result_dict)

        return results
