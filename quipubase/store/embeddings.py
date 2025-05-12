"""
Embedding Service Implementation
=============================

This module provides the embedding service implementation for generating vector
representations of text data and performing similarity searches. It supports
multiple embedding models and provides efficient vector operations.

Key Features:
- Multiple embedding model support
- Efficient vector operations
- Similarity search with cosine similarity
- Text embedding generation

Dependencies:
- numpy: For numerical operations and array handling
- faiss: For efficient similarity search
- light_embed: For embedding model management
"""

import typing as tp
import faiss  # type: ignore
import numpy as np
import typing_extensions as tpx
from light_embed import TextEmbedding  # type: ignore
from numpy.typing import NDArray

from .typedefs import QueryMatch

Texts: tpx.TypeAlias = tp.Union[str, list[str]]
EmbeddingModel: tpx.TypeAlias = tp.Literal["poly-sage", "deep-pulse", "mini-scope"]
Semantic: tpx.TypeAlias = tp.Union[Texts, NDArray[np.float32]]

MODELS: dict[EmbeddingModel, TextEmbedding] = {
    "poly-sage": TextEmbedding("nomic-ai/nomic-embed-text-v1.5"),
    "deep-pulse": TextEmbedding("sentence-transformers/all-mpnet-base-v2"),
    "mini-scope": TextEmbedding("sentence-transformers/all-MiniLM-L6-v2"),
}


class EmbeddingService(tp.NamedTuple):
    """
    Service for generating vector representations and performing similarity searches.

    Args:
        model (EmbeddingModel): The embedding model to use

    Attributes:
        model (EmbeddingModel): The embedding model instance
    """

    model: EmbeddingModel

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
            return np.array([], dtype=np.float32).reshape(0, 768 if self.model != 'mini-scope' else 386)

        raw_output = MODELS[self.model].encode(data)  # <- aquí está el potencial error
        print(f"[DEBUG] Raw embedding output type: {type(raw_output)}, shape: {getattr(raw_output, 'shape', None)}")
        
        return np.asarray(raw_output, dtype=np.float32)  # fuerza a convertir si no es ndarray

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
        if not isinstance(semantic, np.ndarray):
            raise ValueError(f"Expected numpy array, got {type(semantic)}")
        if semantic.dtype != np.float32:
            semantic = semantic.astype(np.float32)
        if semantic.size == 0:
            return np.array([], dtype=np.float32).reshape(0, 768 if self.model != 'mini-scope' else 384)
        return semantic

    def search(
        self,
        query: list[float],
        corpus: list[list[float]],
        top_k: int = 3,
    ) -> list[QueryMatch]:
        """
        Perform similarity search using cosine similarity.

        Args:
            query (list[float]): Query vector
            corpus (list[list[float]]): List of vectors to search against
            top_k (int): Number of top results to return (default: 3)

        Returns:
            list[QueryMatch]: List of top matches with scores

        Example:
            >>> query = [0.1, 0.2, 0.3]
            >>> corpus = [[0.4, 0.5, 0.6], [0.7, 0.8, 0.9]]
            >>> matches = service.search(query, corpus, top_k=2)
        """
        # Convert to numpy arrays
        corpus_np = np.array(corpus, dtype=np.float32)
        query_np = np.array(query, dtype=np.float32)

        # Calculate cosine similarities
        similarities = corpus_np @ query_np / (
            np.linalg.norm(corpus_np, axis=1) * np.linalg.norm(query_np) + 1e-8
        )
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [
            QueryMatch(
                content=str(i),
                embedding=corpus[i],
                score=float(similarities[i]),
            )
            for i in top_indices
        ]