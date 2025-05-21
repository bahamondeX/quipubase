from __future__ import annotations

import json
import logging
import typing as tp
import uuid
from dataclasses import dataclass, field

import httpx
import typing_extensions as tpe
from pydantic import BaseModel, Field, InstanceOf

# --- Constants --- #
DEFAULT_BASE_URL = "http://localhost:5454"

# --- Type Aliases --- #
EmbeddingModel: tpe.TypeAlias = tp.Literal["poly-sage", "deep-pulse", "mini-scope"]
QuipuActions: tpe.TypeAlias = tp.Literal[
    "create", "read", "update", "delete", "query", "stop"
]

# --- Generic Type Variable --- #
T = tp.TypeVar("T", bound=BaseModel)

# --- Logging --- #
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Added basic logging configuration


# --- JSON Schema Type --- #
class JsonSchema(tpe.TypedDict):
    """
    Represents a JSON Schema.  This TypedDict provides a structured way to define
    the schema for data validation, particularly for collection creation.
    """

    type: tpe.Required[str]
    title: tpe.NotRequired[str]
    description: tpe.NotRequired[str]
    properties: tpe.NotRequired[tp.Dict[str, JsonSchema]]
    required: tpe.NotRequired[list[str]]
    enum: tpe.NotRequired[list[tp.Any]]
    items: tpe.NotRequired[tp.Dict[str, JsonSchema]]


# --- Data Models --- #
class EmbedText(BaseModel):
    """
    Represents text to be embedded, along with the embedding model to use.
    """

    content: list[str]
    model: EmbeddingModel = Field(
        ...,
        description="The embedding model to use: poly-sage, deep-pulse, or mini-scope.",
    )


class UpsertText(EmbedText):
    """
    Represents text to be upserted into a vector store, including the namespace.
    """

    namespace: str = Field(..., description="The namespace to upsert the text into.")


class QueryText(EmbedText):
    """
    Represents a text query for the vector store, including namespace and top-k.
    """

    namespace: str = Field(..., description="The namespace to query.")
    top_k: int = Field(..., description="The number of nearest neighbors to retrieve.")


class DeleteText(BaseModel):
    """
    Represents a request to delete texts from a vector store by their IDs.
    """

    namespace: str = Field(..., description="The namespace to delete from.")
    ids: list[str] = Field(..., description="A list of IDs to delete.")


class Embedding(BaseModel):
    """
    Represents an embedding vector associated with a content ID.
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique ID of the embedding.",
    )
    content: str | list[str] = Field(
        ..., description="The original text or list of texts."
    )
    embedding: list[float] = Field(..., description="The embedding vector.")


class QueryMatch(BaseModel):
    """
    Represents a single query match result.
    """

    score: float = Field(..., description="The similarity score of the match.")
    content: str = Field(..., description="The content of the matched text.")


class SemanticContent(tpe.TypedDict):
    """
    Represents semantic content with an ID and content string.
    """

    id: str
    content: str


# --- Response Types --- #
class UpsertResponse(tpe.TypedDict):
    """
    Represents the response from an upsert operation.
    """

    contents: list[SemanticContent]
    upsertedCount: int


class QueryResponse(tpe.TypedDict):
    """
    Represents the response from a query operation.
    """

    matches: list[QueryMatch]
    readCount: int


class DeleteResponse(tpe.TypedDict):
    """
    Represents the response from a delete operation.
    """

    embeddings: list[str]
    deletedCount: int


class EmbedResponse(tpe.TypedDict):
    """
    Represents the response from an embedding operation.
    """

    data: list[Embedding]
    created: float
    embedCount: int


class CollectionType(tpe.TypedDict):
    """
    Represents the schema and metadata of a collection.
    """

    id: str
    name: str
    schema: JsonSchema


class CollectionMetadataType(tpe.TypedDict):
    """
    Represents metadata about a collection (ID and name).
    """

    id: str
    name: str


class DeleteCollectionReturnType(tpe.TypedDict):
    """
    Represents the return type when deleting a collection.
    """

    code: int


# --- PubSub Types --- #
class PubReturnType(tpe.TypedDict):
    """
    Represents the return type for publishing an event.
    """

    collection: str
    data: InstanceOf[BaseModel] | dict[str, tp.Any]
    event: QuipuActions


class QuipubaseRequest(BaseModel):
    """
    Represents a request to publish an event.
    """

    event: QuipuActions = Field(
        default="query", description="The event type (e.g., create, read, update)."
    )
    id: tp.Optional[uuid.UUID] = Field(
        default=None, description="Optional unique ID for the request."
    )
    data: tp.Optional[InstanceOf[BaseModel]] = Field(
        default=None, description="The data associated with the event."
    )

    model_config = {
        "arbitrary_types_allowed": True,  # Allows BaseModel instances for 'data'
    }


class Collection(BaseModel):
    """
    Represents a collection with an optional ID.
    """

    id: tp.Optional[uuid.UUID] = Field(
        default_factory=uuid.uuid4, description="Unique ID of the collection."
    )


class QuipubaseEvent(tpe.TypedDict):
    """
    Represents an event published to a collection.
    """

    event: QuipuActions
    data: InstanceOf[BaseModel]


# --- Async Client Class --- #
@dataclass
class AsyncQuipuBase(tp.Generic[T]):
    """
    Asynchronous client for interacting with the QuipuBase API.

    Provides methods for managing collections and performing CRUD operations.  This client
    uses `httpx.AsyncClient` for asynchronous communication.

    Type Parameter:
        T (Type[BaseModel]): The expected data model for certain operations.  This
            allows the client to automatically deserialize responses into the
            specified Pydantic model.
    """

    base_url: str = field(default=DEFAULT_BASE_URL)
    _client: tp.Optional[httpx.AsyncClient] = field(
        default=None, init=False, repr=False
    )
    _model: tp.Type[T] | None = field(default=None, init=False, repr=False)

    @classmethod
    def __cls_getitem__(cls, item: tp.Type[T]):
        """
        Generic class method to set the expected data model `T`.  This enables
        using the class with a specific model, like `AsyncQuipuBase[MyModel]`.

        Args:
            item (Type[BaseModel]): The Pydantic model class.

        Returns:
            Type[AsyncQuipuBase[T]]: The class itself, with the model type set.
        """
        cls._model = item
        return cls

    def __post_init__(self):
        """
        Initializes the `httpx.AsyncClient` when the class is instantiated.
        """
        self._client = httpx.AsyncClient(base_url=self.base_url)

    async def _request(
        self,
        endpoint: str,
        method: str,
        json_data: tp.Optional[tp.Any] = None,
        params: tp.Optional[dict[str, str]] = None,
        headers: tp.Optional[dict[str, str]] = None,
        debug: bool = False,
    ) -> httpx.Response:
        """
        Sends an HTTP request to the specified endpoint.

        This is a generic method used by other methods to interact with the API.

        Args:
            endpoint (str): The API endpoint to send the request to.
            method (str): The HTTP method (e.g., "GET", "POST", "DELETE").
            json_data (Optional[Any]): The data to send in the request body as JSON.
            params (Optional[dict[str, str]]): Query parameters for the request.
            headers (Optional[dict[str, str]]): Custom headers for the request.
            debug (bool):  If True, logs the request and response details.

        Returns:
            httpx.Response: The HTTP response object.

        Raises:
            httpx.HTTPStatusError: If the HTTP status code indicates an error.
            httpx.RequestError: If there is an error with the HTTP request itself.
            Exception: For other unexpected errors.
        """
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        all_headers = {**default_headers, **(headers or {})}

        # Prepare the data.  Handles both BaseModel and dict.
        data = (
            json_data.model_dump(exclude_none=True)
            if isinstance(json_data, BaseModel)
            else json_data
        )

        if debug:
            logger.info(f"Sending {method} request to {endpoint}")
            logger.info(f"Request payload: {json.dumps(data, default=str)}")

        assert self._client is not None  # Ensure the client is initialized
        response = await self._client.request(
            method=method,
            url=endpoint,
            json=data,
            params=params,
            headers=all_headers,
        )

        if debug and response.status_code >= 400:
            logger.info(f"Error response ({response.status_code}): {response.text}")
        response.raise_for_status()  # Raise for status *after* logging
        return response

    async def create_collection(
        self, schema: JsonSchema | tp.Dict[str, tp.Any]
    ) -> CollectionType:
        """
        Creates a new collection with the given schema.

        Args:
            schema (JsonSchema | dict[str, Any]): The schema for the collection.
                This defines the structure of the data that can be stored in the
                collection.  It can be either a JsonSchema TypedDict or a
                plain Python dictionary.

        Returns:
            CollectionType: The created collection's metadata.
        """
        response = await self._request("/v1/collections", "POST", json_data=schema)
        return response.json()

    async def list_collections(self) -> list[CollectionMetadataType]:
        """
        Lists all collections.

        Returns:
            list[CollectionMetadataType]: A list of metadata for all collections.
        """
        response = await self._request("/v1/collections", "GET")
        return response.json()

    async def get_collection(self, collection_id: str) -> CollectionType:
        """
        Gets a specific collection by its ID.

        Args:
            collection_id (str): The ID of the collection to retrieve.

        Returns:
            CollectionType: The collection's metadata and schema.
        """
        response = await self._request(f"/v1/collections/{collection_id}", "GET")
        return response.json()

    async def delete_collection(self, collection_id: str) -> DeleteCollectionReturnType:
        """
        Deletes a collection by its ID.

        Args:
            collection_id (str): The ID of the collection to delete.

        Returns:
            DeleteCollectionReturnType:  Indicates the result of the deletion.
        """
        response = await self._request(f"/v1/collections/{collection_id}", "DELETE")
        return response.json()

    async def publish_event(
        self, collection_id: str, data: QuipubaseRequest
    ) -> PubReturnType:
        """
        Publishes an event to a collection.

        Args:
            collection_id (str): The ID of the collection to publish the event to.
            data (QuipubaseRequest): The event data, including the event type and payload.

        Returns:
            PubReturnType: The result of publishing the event.
        """
        action_request: dict[str, tp.Any] = {
            "event": data.event,
            "data": (
                data.data.model_dump(exclude_none=True)
                if isinstance(data.data, BaseModel)
                else data.data
            ),
        }
        response = await self._request(
            f"/v1/events/{collection_id}", "POST", json_data=action_request
        )
        return response.json()

    async def subscribe(self, collection_id: str) -> tp.AsyncIterator[QuipubaseEvent]:
        """
        Subscribes to events from a collection.  This returns an *asynchronous*
        iterator, which must be used in an `async for` loop.

        Args:
            collection_id (str): The ID of the collection to subscribe to.

        Yields:
            QuipubaseEvent:  Each event as it is received.
        """
        assert self._client is not None
        async with self._client.stream(
            "GET", f"/v1/events/{collection_id}", headers={"Event": "Text-Stream"}
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        event_data = json.loads(line[7:])
                        yield QuipubaseEvent(**event_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding event: {e}, line: {line}")
                        continue  # Important: Continue to the next line

    async def upsert_vectors(
        self, namespace: str, texts: list[str], model: EmbeddingModel
    ) -> UpsertResponse:
        """
        Upserts texts into the vector store.

        Args:
            namespace (str): The namespace to upsert the texts into.
            texts (list[str]): The list of texts to upsert.
            model (EmbeddingModel): The embedding model to use.

        Returns:
            UpsertResponse: The result of the upsert operation.
        """
        payload = UpsertText(namespace=namespace, content=texts, model=model)
        response = await self._request("/v1/vector/upsert", "POST", json_data=payload)
        return response.json()

    async def query_vectors(
        self, namespace: str, query: str, top_k: int, model: EmbeddingModel
    ) -> QueryResponse:
        """
        Queries the vector store for similar texts.

        Args:
            namespace (str): The namespace to query.
            query (str): The query text.
            top_k (int): The number of nearest neighbors to retrieve.
            model (EmbeddingModel): The embedding model to use.

        Returns:
            QueryResponse: The result of the query operation.
        """
        payload = QueryText(
            namespace=namespace, content=[query], model=model, top_k=top_k
        )
        response = await self._request("/v1/vector/query", "POST", json_data=payload)
        return response.json()

    async def delete_vectors(self, namespace: str, ids: list[str]) -> DeleteResponse:
        """
        Deletes vectors from the vector store.

        Args:
            namespace (str): The namespace to delete from.
            ids (list[str]): The IDs of the vectors to delete.

        Returns:
            DeleteResponse: The result of the delete operation.
        """
        payload = DeleteText(namespace=namespace, ids=ids)
        response = await self._request("/v1/vector/delete", "DELETE", json_data=payload)
        return response.json()

    async def embed_texts(
        self, content: list[str], model: EmbeddingModel
    ) -> EmbedResponse:
        """
        Embeds texts using the specified model.

        Args:
            content (list[str]): The list of texts to embed.
            model (EmbeddingModel): The embedding model to use.

        Returns:
            EmbedResponse: The embedding vectors.
        """
        payload = EmbedText(content=content, model=model)
        response = await self._request("/v1/vector/embed", "POST", json_data=payload)
        return response.json()


# --- Synchronous Client Class --- #
@dataclass
class QuipuBase(tp.Generic[T]):
    """
    Synchronous client for interacting with the QuipuBase API.

    Provides methods for managing collections and performing CRUD operations. This client
    uses `httpx.Client` for synchronous communication.

    Type Parameter:
        T (Type[BaseModel]): The expected data model for certain operations.
            This allows the client to automatically deserialize responses
            into the specified Pydantic model.
    """

    base_url: str = field(default=DEFAULT_BASE_URL)
    _client: tp.Optional[httpx.Client] = field(default=None, init=False, repr=False)
    _model: tp.Type[T] | None = field(default=None, init=False, repr=False)

    @classmethod
    def __cls_getitem__(cls, item: tp.Type[T]):
        """
        Generic class method to set the expected data model `T`.
        This enables using the class with a specific model, like `QuipuBase[MyModel]`.

        Args:
            item (Type[BaseModel]): The Pydantic model class.

        Returns:
            Type[QuipuBase[T]]: The class itself, with the model type set.
        """
        cls._model = item
        return cls

    def __post_init__(self):
        """
        Initializes the `httpx.Client` when the class is instantiated.
        """
        self._client = httpx.Client(base_url=self.base_url)

    def _request(
        self,
        endpoint: str,
        method: str,
        json_data: tp.Optional[tp.Any] = None,
        params: tp.Optional[dict[str, str]] = None,
        headers: tp.Optional[dict[str, str]] = None,
        debug: bool = False,
    ) -> httpx.Response:
        """
        Sends an HTTP request to the specified endpoint (synchronous version).

        This is a generic method used by other methods to interact with the API.

        Args:
            endpoint (str): The API endpoint to send the request to.
            method (str): The HTTP method (e.g., "GET", "POST", "DELETE").
            json_data (Optional[Any]): The data to send in the request body as JSON.
            params (Optional[dict[str, str]]): Query parameters for the request.
            headers (Optional[dict[str, str]]): Custom headers for the request.
            debug (bool): If True, logs the request and response details

        Returns:
            httpx.Response: The HTTP response object.

        Raises:
            httpx.HTTPStatusError: If the HTTP status code indicates an error.
            httpx.RequestError: If there is an error with the HTTP request itself.
            Exception: For other unexpected errors.
        """
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        all_headers = {**default_headers, **(headers or {})}

        # Prepare the data
        data = (
            json_data.model_dump(exclude_none=True)
            if isinstance(json_data, BaseModel)
            else json_data
        )
        if debug:
            logger.info(f"Sending {method} request to {endpoint}")
            logger.info(f"Request payload: {json.dumps(data, default=str)}")

        assert self._client is not None  # Ensure client is initialized.
        response = self._client.request(
            method=method,
            url=endpoint,
            json=data,
            params=params,
            headers=all_headers,
        )
        if debug and response.status_code >= 400:
            logger.info(f"Error response ({response.status_code}): {response.text}")

        response.raise_for_status()  # Raise for status *after* logging
        return response

    def create_collection(
        self, schema: JsonSchema | tp.Dict[str, tp.Any]
    ) -> CollectionType:
        """
        Creates a new collection with the given schema (synchronous version).

        Args:
            schema (JsonSchema | dict[str, Any]): The schema for the collection.

        Returns:
            CollectionType: The created collection's metadata.
        """
        response = self._request("/v1/collections", "POST", json_data=schema)
        return response.json()

    def list_collections(self) -> list[CollectionMetadataType]:
        """
        Lists all collections (synchronous version).

        Returns:
            list[CollectionMetadataType]: A list of metadata for all collections.
        """
        response = self._request("/v1/collections", "GET")
        return response.json()

    def get_collection(self, collection_id: str) -> CollectionType:
        """
        Gets a specific collection by its ID (synchronous version).

        Args:
            collection_id (str): The ID of the collection to retrieve.

        Returns:
            CollectionType: The collection's metadata and schema.
        """
        response = self._request(f"/v1/collections/{collection_id}", "GET")
        return response.json()

    def delete_collection(self, collection_id: str) -> DeleteCollectionReturnType:
        """
        Deletes a collection by its ID (synchronous version).

        Args:
            collection_id (str): The ID of the collection to delete.

        Returns:
            DeleteCollectionReturnType: Indicates the result of the deletion
        """
        response = self._request(f"/v1/collections/{collection_id}", "DELETE")
        return response.json()

    def publish_event(
        self, collection_id: str, data: QuipubaseRequest
    ) -> PubReturnType:
        """
        Publishesan event to a collection (synchronous version).

        Args:
            collection_id (str): The ID of the collection to publish the event to.
            data (QuipubaseRequest): The event data.

        Returns:
            PubReturnType: The result of publishing the event.
        """
        action_request: dict[str, tp.Any] = {
            "event": data.event,
            "data": (
                data.data.model_dump(exclude_none=True)
                if isinstance(data.data, BaseModel)
                else data.data
            ),
        }
        response = self._request(
            f"/v1/events/{collection_id}", "POST", json_data=action_request
        )
        return response.json()

    def subscribe(self, collection_id: str) -> tp.Iterator[QuipubaseEvent]:
        """
        Subscribes to events from a collection (synchronous version).  This returns
        a standard Python iterator.

        Args:
            collection_id (str): The ID of the collection to subscribe to.

        Yields:
            QuipubaseEvent: Each event as it is received.
        """
        assert self._client is not None
        with self._client.stream(
            "GET", f"/v1/events/{collection_id}", headers={"Event": "Text-Stream"}
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.strip():
                    try:
                        event_data = json.loads(line[7:])
                        yield QuipubaseEvent(**event_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error decoding event: {e}, line: {line}")
                        continue  # Important: Continue to the next line

    # --- Vector API (Synchronous) --- #
    def upsert_vectors(
        self, namespace: str, texts: list[str], model: EmbeddingModel
    ) -> UpsertResponse:
        """
        Upserts texts into the vector store (synchronous version).

        Args:
            namespace (str): The namespace to upsert the texts into.
            texts (list[str]): The list of texts to upsert.
            model (EmbeddingModel): The embedding model to use.

        Returns:
            UpsertResponse: The result of the upsert operation.
        """
        payload = UpsertText(namespace=namespace, content=texts, model=model)
        response = self._request("/v1/vector/upsert", "POST", json_data=payload)
        return response.json()

    def query_vectors(
        self, namespace: str, query: str, top_k: int, model: EmbeddingModel
    ) -> QueryResponse:
        """
        Queries the vector store for similar texts (synchronous version).

        Args:
            namespace (str): The namespace to query.
            query (str): The query text.
            top_k (int): The number of nearest neighbors to retrieve.
            model (EmbeddingModel): The embedding model to use.

        Returns:
            QueryResponse: The result of the query operation.
        """
        payload = QueryText(
            namespace=namespace, content=[query], model=model, top_k=top_k
        )
        response = self._request("/v1/vector/query", "POST", json_data=payload)
        return response.json()

    def delete_vectors(self, namespace: str, ids: list[str]) -> DeleteResponse:
        """
        Deletes vectors from the vector store (synchronous version).

        Args:
            namespace (str): The namespace to delete from.
            ids (list[str]): The IDs of the vectors to delete.

        Returns:
            DeleteResponse: The result of the delete operation.
        """
        payload = DeleteText(namespace=namespace, ids=ids)
        response = self._request("/v1/vector/delete", "DELETE", json_data=payload)
        return response.json()

    def embed_texts(self, content: list[str], model: EmbeddingModel) -> EmbedResponse:
        """
        Embeds texts using the specified model (synchronous version).

        Args:
            content (list[str]): The list of texts to embed.
            model (EmbeddingModel): The embedding model to use.

        Returns:
            EmbedResponse: The embedding vectors.
        """
        payload = EmbedText(content=content, model=model)
        response = self._request("/v1/vector/embed", "POST", json_data=payload)
        return response.json()
