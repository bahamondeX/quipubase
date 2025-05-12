import asyncio
import json
import typing as tp
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from httpx import AsyncClient, Response
from pydantic import BaseModel

# Define type variable for generic
T = tp.TypeVar("T", bound="Collection")


class Collection(BaseModel):
    """Base class for all collection models"""

    pass


class Event(BaseModel):
    """Event model for pub/sub"""

    id: UUID
    collection_id: str
    event: str
    data: tp.Optional[tp.Dict[str, tp.Any]] = None
    timestamp: datetime = None


@dataclass
class QuipuBaseClient(tp.Generic[T]):
    """
    Client for interacting with the QuipuBase API.

    Provides methods for managing collections and performing CRUD operations.
    """

    base_url: str = field(default="https://quipubase.online")
    _client: tp.Optional[AsyncClient] = None
    _model: tp.ClassVar[tp.Type[T]] = None

    def __post_init__(self):
        self._client = AsyncClient(base_url=self.base_url)

    @classmethod
    def for_model(cls, model_cls: tp.Type[T]) -> "QuipuBaseClient[T]":
        """Create a client for a specific model type"""
        instance = cls()
        instance._model = model_cls
        return instance

    async def _request(
        self,
        endpoint: str,
        method: str,
        json_data: tp.Optional[tp.Any] = None,
        params: tp.Optional[dict] = None,
        headers: tp.Optional[dict] = None,
        debug: bool = False,
    ) -> Response:
        """Generic request method"""
        default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        all_headers = {**default_headers, **(headers or {})}

        # Prepare the data
        if isinstance(json_data, BaseModel):
            data = json_data.model_dump(exclude_none=True)
        else:
            data = json_data

        try:
            if debug:
                print(f"Sending {method} request to {endpoint}")
                print(f"Request payload: {json.dumps(data, default=str)}")

            response = await self._client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params,
                headers=all_headers,
            )

            if debug and response.status_code >= 400:
                print(f"Error response ({response.status_code}): {response.text}")

            response.raise_for_status()
            return response

        except Exception as e:
            if debug:
                print(f"Request failed: {method} {endpoint}")
                print(f"Request data: {json.dumps(data, default=str)}")
                print(f"Error: {str(e)}")
            raise Exception(f"API request error: {str(e)}")

    async def create_collection(self, schema: dict) -> dict:
        """Create a new collection with the given schema"""
        response = await self._request("/v1/collections", "POST", json_data=schema)
        return response.json()

    async def list_collections(self) -> list[dict]:
        """List all collections"""
        response = await self._request("/v1/collections", "GET")
        return response.json()

    async def get_collection(self, collection_id: str) -> dict:
        """Get a specific collection by ID"""
        response = await self._request(f"/v1/collections/{collection_id}", "GET")
        return response.json()

    async def delete_collection(self, collection_id: str) -> dict:
        """Delete a collection by ID"""
        response = await self._request(f"/v1/collections/{collection_id}", "DELETE")
        return response.json()

    async def create_document(self, collection_id: str, data: T) -> T:
        """Create a document in a collection"""
        # According to OpenAPI spec from paste.txt:
        # The PUT endpoint expects an ActionRequest with event, id (optional), and data
        data_dict = (
            data.model_dump(exclude_none=True) if isinstance(data, BaseModel) else data
        )

        action_request = {"event": "create", "data": data_dict}

        # Send the request with debug info
        response = await self._request(
            f"/v1/collections/{collection_id}",
            "PUT",
            json_data=action_request,
            debug=True,
        )

        return self._model.model_validate(response.json())

    async def get_document(self, collection_id: str, doc_id: str) -> T:
        """Get a document from a collection"""
        action_request = {"event": "read", "id": doc_id}
        response = await self._request(
            f"/v1/collections/{collection_id}", "PUT", json_data=action_request
        )
        return self._model.model_validate(response.json())

    async def update_document(self, collection_id: str, doc_id: str, data: T) -> T:
        """Update a document in a collection"""
        data_dict = (
            data.model_dump(exclude_none=True) if isinstance(data, BaseModel) else data
        )

        action_request = {"event": "update", "id": doc_id, "data": data_dict}
        response = await self._request(
            f"/v1/collections/{collection_id}", "PUT", json_data=action_request
        )
        return self._model.model_validate(response.json())

    async def delete_document(self, collection_id: str, doc_id: str) -> dict:
        """Delete a document from a collection"""
        action_request = {"event": "delete", "id": doc_id}
        response = await self._request(
            f"/v1/collections/{collection_id}", "PUT", json_data=action_request
        )
        return response.json()

    async def query_collection(self, collection_id: str, query: dict = None) -> list[T]:
        """Query documents in a collection"""
        action_request = {"event": "query", "data": query or {}}
        response = await self._request(
            f"/v1/collections/{collection_id}", "PUT", json_data=action_request
        )
        results = response.json()
        if isinstance(results, list):
            return [self._model.model_validate(item) for item in results]
        return []

    async def publish_event(
        self, collection_id: str, event_type: str, data: tp.Any
    ) -> dict:
        """Publish an event to a collection"""
        action_request = {
            "event": event_type,
            "data": (
                data.model_dump(exclude_none=True)
                if isinstance(data, BaseModel)
                else data
            ),
        }
        response = await self._request(
            f"/v1/events/{collection_id}", "POST", json_data=action_request
        )
        return response.json()

    async def subscribe(self, collection_id: str) -> tp.AsyncIterator[Event]:
        """Subscribe to events from a collection"""
        async with self._client.stream(
            "GET", f"/v1/events/{collection_id}", headers={"Accept": "application/json"}
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        event_data = json.loads(line)
                        yield Event(**event_data)
                    except json.JSONDecodeError as e:
                        print(f"Error decoding event: {e}")
                        continue


# Example usage
async def example():
    # Define a model for your collection
    class User(Collection):
        name: str
        email: str
        age: int

    # Create schema for the collection
    user_schema = {
        "title": "Users",
        "description": "Collection of users",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "email": {"type": "string", "format": "email"},
            "age": {"type": "integer", "minimum": 0},
        },
        "required": ["name", "email"],
    }

    # Initialize client
    client = QuipuBaseClient.for_model(User)

    try:
        # Create collection
        print("Creating collection...")
        collection = await client.create_collection(user_schema)
        collection_id = collection["id"]
        print(f"Collection created with ID: {collection_id}")

        # Create document
        print("Creating document...")
        user = User(name="John Doe", email="john@example.com", age=30)
        created_user = await client.create_document(collection_id, user)
        print(f"User created: {created_user}")

        # Query collection
        print("Querying collection...")
        users = await client.query_collection(collection_id)
        print(f"Found {len(users)} users")

        # Subscribe to events (with timeout)
        print("Subscribing to events (5s timeout)...")
        try:
            subscription = client.subscribe(collection_id)
            done = False
            start_time = asyncio.get_event_loop().time()
            timeout = 5  # 5 seconds

            while not done:
                try:
                    # Set timeout for getting next event
                    event = await asyncio.wait_for(
                        anext(subscription.__aiter__()), timeout=1.0
                    )
                    print(f"Event received: {event.event}")

                    # Check overall timeout
                    if asyncio.get_event_loop().time() - start_time >= timeout:
                        print("Subscription timeout reached")
                        done = True

                except asyncio.TimeoutError:
                    # Check if overall timeout reached
                    if asyncio.get_event_loop().time() - start_time >= timeout:
                        print("Subscription timeout reached")
                        done = True
                except StopAsyncIteration:
                    print("Subscription ended")
                    done = True
        except Exception as e:
            print(f"Subscription error: {e}")

    except Exception as e:
        print(f"Error in example: {str(e)}")


# For direct execution
if __name__ == "__main__":
    asyncio.run(example())
