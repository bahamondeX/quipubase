import typing as tp
from dataclasses import dataclass
from functools import cached_property

import numpy as np
import typing_extensions as tpx
from numpy.typing import NDArray
from rocksdict import Rdict

from .embeddings import EmbeddingModel, EmbeddingService
from .typedefs import (Embedding, EmbeddingUpsertResponse, MetaData,
                       QueryResponse)


@dataclass
class IndexStats:
    """Statistics about the index."""

    dimension: int
    namespaces: tp.Dict[str, tp.Dict[str, int]]
    total_vector_count: int


class Filter(object):
    """
    Represents a MongoDB-like filter for metadata queries.

    Supports operators: $eq, $ne, $in, $nin, $gt, $gte, $lt, $lte
    """

    def __init__(self, query: tp.Union[dict[str, tp.Any], tuple[str, tp.Any]]) -> None:
        if isinstance(query, tuple):
            query = dict([query])
        self.query = query

    @staticmethod
    def eq(field: str, value: tp.Any) -> "Filter":
        """Create filter for exact match."""
        return Filter({field: value})

    @staticmethod
    def ne(field: str, value: tp.Any) -> "Filter":
        """Create filter for not equal."""
        return Filter({field: {"$ne": value}})

    @staticmethod
    def in_(field: str, values: tp.List[tp.Any]) -> "Filter":
        """Create filter for value in list."""
        return Filter({field: {"$in": values}})

    @staticmethod
    def nin(field: str, values: tp.List[tp.Any]) -> "Filter":
        """Create filter for value not in list."""
        return Filter({field: {"$nin": values}})

    @staticmethod
    def gt(field: str, value: tp.Union[int, float]) -> "Filter":
        """Create filter for greater than."""
        return Filter({field: {"$gt": value}})

    @staticmethod
    def gte(field: str, value: tp.Union[int, float]) -> "Filter":
        """Create filter for greater than or equal."""
        return Filter({field: {"$gte": value}})

    @staticmethod
    def lt(field: str, value: tp.Union[int, float]) -> "Filter":
        """Create filter for less than."""
        return Filter({field: {"$lt": value}})

    @staticmethod
    def lte(field: str, value: tp.Union[int, float]) -> "Filter":
        """Create filter for less than or equal."""
        return Filter({field: {"$lte": value}})

    def __and__(self, other: "Filter") -> "Filter":
        """Combine filters with AND."""
        return Filter({"$and": [self.query, other.query]})

    def __or__(self, other: "Filter") -> "Filter":
        """Combine filters with OR."""
        return Filter({"$or": [self.query, other.query]})


class Index:
    """
    Pinecone-compatible Index implementation backed by VectorStore.
    """

    def __init__(self, name: str, dimension: int, model: EmbeddingModel):
        self.name = name
        self.dimension = dimension
        self._stores = {}  # namespace -> VectorStore
        self.model = model
        self._default_store = self._get_or_create_store("default")

    def _get_or_create_store(self, namespace: str) -> "VectorStore":
        """Get or create a VectorStore for a namespace."""
        if namespace not in self._stores:
            self._stores[namespace] = VectorStore(
                self.model, f"{self.name}_{namespace}"
            )
        return self._stores[namespace]

    def upsert(
        self, vectors: tp.List[tp.Dict[str, tp.Any]], namespace: str = ""
    ) -> EmbeddingUpsertResponse:
        """
        Upsert vectors into the index.

        Args:
                vectors: List of vector dictionaries with id, values, metadata
                namespace: Optional namespace (defaults to "")

        Returns:
                Dictionary with upsertedCount
        """
        store = self._get_or_create_store(namespace)
        formatted_vectors = []

        for vector in vectors:
            vector_id = vector["id"]
            # Handle both 'values' (Pinecone) and 'embedding' (internal format)
            embedding = np.array(
                vector.get("values", vector.get("embedding")), dtype=np.float32
            )
            metadata = vector.get("metadata", {})
            formatted_vectors.append((vector_id, embedding, metadata))

        return store.upsert(formatted_vectors)

    def query(
        self,
        vector: tp.List[float] = None,
        queries: tp.List[tp.Dict[str, tp.Any]] = None,
        top_k: int = 10,
        namespace: str = "",
        filter: tp.Optional[tp.Dict[str, tp.Any]] = None,
        include_metadata: bool = True,
        include_values: bool = False,
    ) -> QueryResponse:
        """
        Query vectors from the index.

        Args:
                vector: Query vector values
                queries: List of queries (alternative to vector)
                top_k: Number of results to return
                namespace: Optional namespace
                filter: Metadata filter
                include_metadata: Whether to include metadata in results
                include_values: Whether to include vector values in results

        Returns:
                Dictionary with matches
        """
        store = self._get_or_create_store(namespace)

        # Handle filter
        filter_obj = None
        if filter:
            filter_obj = Filter(filter)

        # Handle vector input
        if vector is not None:
            vector_array = np.array(vector, dtype=np.float32)
            result = store.query(
                vector=vector_array,
                filter=filter_obj,
                top_k=top_k,
                include_metadata=include_metadata,
            )

            # Add vector values if requested
            if include_values:
                for match in result["matches"]:
                    if "id" in match:
                        vector_data = store.get(match["id"])
                        if vector_data:
                            match["values"] = vector_data["embedding"].tolist()

            return result

        # Handle multiple queries
        elif queries is not None:
            results = []
            for query in queries:
                q_vector = np.array(query.get("values", []), dtype=np.float32)
                q_filter = (
                    Filter(query.get("filter", {}))
                    if query.get("filter")
                    else filter_obj
                )
                q_top_k = query.get("top_k", top_k)

                result = store.query(
                    vector=q_vector,
                    filter=q_filter,
                    top_k=q_top_k,
                    include_metadata=include_metadata,
                )

                # Add vector values if requested
                if include_values:
                    for match in result["matches"]:
                        if "id" in match:
                            vector_data = store.get(match["id"])
                            if vector_data:
                                match["values"] = vector_data["embedding"].tolist()

                results.append(result)

            return {"results": results}

        raise ValueError("Either 'vector' or 'queries' parameter must be provided")

    def fetch(
        self, ids: tp.List[str], namespace: str = ""
    ) -> tp.Dict[str, tp.List[tp.Dict[str, tp.Any]]]:
        """
        Fetch vectors by ID.

        Args:
                ids: List of vector IDs to fetch
                namespace: Optional namespace

        Returns:
                Dictionary with vectors
        """
        store = self._get_or_create_store(namespace)
        vectors = []

        for vector_id in ids:
            data = store.get(vector_id)
            if data:
                vector = {
                    "id": vector_id,
                    "metadata": data.get("metadata", {}),
                    "values": data.get("embedding", []).tolist(),
                }
                vectors.append(vector)

        return {"vectors": vectors}

    def delete(
        self,
        ids: tp.List[str] = None,
        delete_all: bool = False,
        namespace: str = "",
        filter: tp.Optional[tp.Dict[str, tp.Any]] = None,
    ) -> DeleteResponse:
        """
        Delete vectors from the index.

        Args:
                ids: List of vector IDs to delete
                delete_all: Whether to delete all vectors
                namespace: Optional namespace
                filter: Metadata filter for vectors to delete

        Returns:
                Dictionary with deletedCount
        """
        store = self._get_or_create_store(namespace)

        if delete_all:
            return store.delete(delete_all=True)

        if ids:
            return store.delete(ids=ids)

        if filter:
            filter_obj = Filter(filter)
            # Find vectors matching the filter
            matched_ids = []
            for key in store.store.keys():
                data = store.store[key]
                metadata = data.get("metadata", {})
                if store._matches_filter(metadata, filter_obj.query):
                    matched_ids.append(key)

            return store.delete(ids=matched_ids)

        return {"deletedCount": 0}

    def describe_index_stats(self) -> IndexStats:
        """
        Get statistics about the index.

        Returns:
                IndexStats object
        """
        namespace_stats = {}
        total_count = 0

        for namespace, store in self._stores.items():
            count = len(store.store)
            namespace_stats[namespace] = {"vectorCount": count}
            total_count += count

        return IndexStats(
            dimension=self.dimension,
            namespaces=namespace_stats,
            total_vector_count=total_count,
        )


class VectorStore:
    """
    Backend store for vector data.
    """

    def __init__(self, model: EmbeddingModel, namespace: str):
        self.model = model
        self.namespace = namespace
        self.store = Rdict(namespace)
        self.service = EmbeddingService(model)

    def upsert(
        self, vectors: list[tuple[str, NDArray[np.float32], MetaData]]
    ) -> UpsertResponse:
        """
        Upsert vectors into the store.

        Args:
                vectors: List of tuples containing (id, embedding, metadata)

        Returns:
                Dictionary with upsert status
        """
        for vector_id, embedding, metadata in vectors:
            self.store[vector_id] = {
                "id": vector_id,
                "embedding": embedding,
                "metadata": metadata,
            }
        return {"upsertedCount": len(vectors)}

    def get(self, vector_id: str) -> tp.Optional[tp.Dict[str, tp.Any]]:
        """
        Get a vector by ID.

        Args:
                vector_id: Vector ID

        Returns:
                Vector data or None if not found
        """
        if vector_id in self.store:
            return self.store[vector_id]
        return None

    def delete(self, ids: list[str] = None, delete_all: bool = False) -> DeleteResponse:
        """
        Delete vectors from the store.

        Args:
                ids: List of IDs to delete
                delete_all: If True, deletes all vectors

        Returns:
                Dictionary with delete status
        """
        if delete_all:
            count = len(self.store)
            self.store.clear()
            return {"deletedCount": count}

        if ids:
            deleted_count = 0
            for vector_id in ids:
                if vector_id in self.store:
                    del self.store[vector_id]
                    deleted_count += 1
            return {"deletedCount": deleted_count}

        return {"deletedCount": 0}

    def query(
        self,
        vector: NDArray[np.float32] | None = None,
        filter: Filter | None = None,
        top_k: int = 10,
        include_metadata: bool = True,
    ) -> QueryResponse:
        """
        Query the vector store with optional filter and metadata.

        Args:
                vector: Query vector
                filter: Optional filter for metadata
                top_k: Number of results to return
                include_metadata: Whether to include metadata in results

        Returns:
                QueryResponse containing matches
        """
        if vector is None:
            raise ValueError("vector parameter is required")

        # Get embeddings from store
        embeddings = []
        ids = []
        metadatas = []

        # Filter embeddings based on metadata if filter is provided
        for key in self.store.keys():
            data = self.store[key]
            if not data:
                continue
            embedding = data.get("embedding", [])
            metadata = data.get("metadata", {})

            # Apply metadata filter if provided
            if filter and not self._matches_filter(metadata, filter.query):
                continue

            embeddings.append(embedding)
            ids.append(key)
            metadatas.append(metadata)

        if not embeddings:
            return {"matches": []}

        embeddings_array = np.array(embeddings)

        # Reshape vector for search
        vector = vector.reshape(1, -1)
        results = self.service.search(vector, embeddings_array, top_k)

        # Map results back to original IDs and create QueryResponse
        matches = []
        for i, score in results:
            match = {"id": ids[i], "score": float(score)}
            if include_metadata:
                match["metadata"] = metadatas[i]
            matches.append(match)

        return {"matches": matches}

    def _matches_filter(
        self, metadata: MetaData, filter_dict: dict[str, tp.Any]
    ) -> bool:
        """Check if metadata matches the filter criteria."""
        if "$and" in filter_dict:
            return all(
                self._matches_filter(metadata, subfilter)
                for subfilter in filter_dict["$and"]
            )

        if "$or" in filter_dict:
            return any(
                self._matches_filter(metadata, subfilter)
                for subfilter in filter_dict["$or"]
            )

        for field, value in filter_dict.items():
            if field in ["$and", "$or"]:
                continue

            if isinstance(value, dict):  # Handle operators like $in, $eq, etc.
                for op, op_value in value.items():
                    if op == "$eq":
                        if metadata.get(field) != op_value:
                            return False
                    elif op == "$ne":
                        if metadata.get(field) == op_value:
                            return False
                    elif op == "$in":
                        if metadata.get(field) not in op_value:
                            return False
                    elif op == "$nin":
                        if metadata.get(field) in op_value:
                            return False
                    elif op == "$gt":
                        if metadata.get(field) <= op_value:
                            return False
                    elif op == "$gte":
                        if metadata.get(field) < op_value:
                            return False
                    elif op == "$lt":
                        if metadata.get(field) >= op_value:
                            return False
                    elif op == "$lte":
                        if metadata.get(field) > op_value:
                            return False
            else:  # Handle direct equality
                if metadata.get(field) != value:
                    return False
        return True
