import asyncio
import json
import time
import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.mark.skip("Schema validation needs to be fixed")
def test_publish_event(client, cleanup):
    """Test publishing an event to a collection subscription"""
    # First create a collection
    schema = {
        "title": "TestPubCollection",
        "description": "A test collection for pub/sub",
        "type": "object",
        "properties": {"name": {"type": "string"}, "value": {"type": "integer"}},
    }
    response = client.post("/v1/collections", json=schema)
    collection_id = response.json()["id"]

    # Create an item in the collection
    create_payload = {"action": "create", "data": {"name": "Test Item", "value": 42}}
    response = client.post(
        f"/v1/collections/{collection_id}/action", json=create_payload
    )
    item_id = response.json()["id"]

    # Publish an update event
    publish_payload = {
        "action": "update",
        "id": item_id,
        "value": {"name": "Updated Item", "value": 99},
        "sub": "test-subscription",
    }
    response = client.post(f"/v1/pubsub/{collection_id}/publish", json=publish_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "message" in data

    # Verify the item was updated
    read_payload = {"action": "read", "id": item_id}
    response = client.post(f"/v1/collections/{collection_id}/action", json=read_payload)
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["name"] == "Updated Item"
    assert item["value"] == 99


@pytest.mark.skip("SSE testing requires special handling")
def test_subscribe_endpoint(client, cleanup):
    """Test subscribing to a collection with SSE"""
    # This test would normally use an SSE client, but we'll simulate it
    # Create a collection
    schema = {
        "title": "TestSubCollection",
        "description": "A test collection for subscription",
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    response = client.post("/v1/collections", json=schema)
    collection_id = response.json()["id"]

    # This would normally be a streaming response
    with client.get(
        f"/v1/pubsub/{collection_id}/subscribe?subscription=test-sub", stream=True
    ) as response:
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["Content-Type"] == "text/event-stream"
        # Further testing would require simulating the SSE client behavior


@pytest.mark.skip("Schema validation needs to be fixed")
def test_close_subscription(client, cleanup):
    """Test closing a subscription"""
    # Create a collection
    schema = {
        "title": "TestCloseSubCollection",
        "description": "A test collection for closing subscription",
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    response = client.post("/v1/collections", json=schema)
    collection_id = response.json()["id"]

    # Close a specific subscription
    response = client.post(f"/v1/pubsub/{collection_id}/close?subscription=test-sub")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "message" in data

    # Close all subscriptions
    response = client.post(f"/v1/pubsub/{collection_id}/close")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "message" in data


@pytest.mark.skip("Schema validation needs to be fixed")
def test_publish_create_event(client, cleanup):
    """Test publishing a create event to a collection subscription"""
    # First create a collection
    schema = {
        "title": "TestCreatePubCollection",
        "description": "A test collection for create pub/sub",
        "type": "object",
        "properties": {"name": {"type": "string"}, "value": {"type": "integer"}},
    }
    response = client.post("/v1/collections", json=schema)
    collection_id = response.json()["id"]

    # Publish a create event
    publish_payload = {
        "action": "create",
        "value": {"name": "New Item", "value": 123},
        "sub": "test-subscription",
    }
    response = client.post(f"/v1/pubsub/{collection_id}/publish", json=publish_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    if data["item"]:
        assert data["item"]["name"] == "New Item"
        assert data["item"]["value"] == 123

    # Verify the item was created by querying the collection
    query_payload = {"action": "query", "data": {"name": "New Item"}}
    response = client.post(
        f"/v1/collections/{collection_id}/action", json=query_payload
    )
    assert response.status_code == status.HTTP_200_OK
    query_result = response.json()
    assert len(query_result["items"]) > 0
    assert query_result["items"][0]["value"] == 123


@pytest.mark.skip("Schema validation needs to be fixed")
def test_publish_delete_event(client, cleanup):
    """Test publishing a delete event to a collection subscription"""
    # First create a collection
    schema = {
        "title": "TestDeletePubCollection",
        "description": "A test collection for delete pub/sub",
        "type": "object",
        "properties": {"name": {"type": "string"}, "value": {"type": "integer"}},
    }
    response = client.post("/v1/collections", json=schema)
    collection_id = response.json()["id"]

    # Create an item in the collection
    create_payload = {
        "action": "create",
        "data": {"name": "Delete Test Item", "value": 42},
    }
    response = client.post(
        f"/v1/collections/{collection_id}/action", json=create_payload
    )
    item_id = response.json()["id"]

    # Publish a delete event
    publish_payload = {"action": "delete", "id": item_id, "sub": "test-subscription"}
    response = client.post(f"/v1/pubsub/{collection_id}/publish", json=publish_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True

    # Verify the item was deleted
    read_payload = {"action": "read", "id": item_id}
    response = client.post(f"/v1/collections/{collection_id}/action", json=read_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
