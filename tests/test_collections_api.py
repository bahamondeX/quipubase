import json
import uuid

import pytest
from fastapi import status


@pytest.mark.skip("Schema validation needs to be fixed")
def test_create_collection(client, cleanup):
    """Test creating a new collection"""
    schema = {
        "title": "TestCollection",
        "description": "A test collection",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "active": {"type": "boolean"},
        },
        "required": ["name"],
    }

    response = client.post("/v1/collections", json=schema)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "id" in data
    assert data["definition"]["title"] == "TestCollection"


@pytest.mark.skip("Schema validation needs to be fixed")
def test_list_collections(client, cleanup):
    """Test listing all collections"""
    # First create a collection
    schema = {
        "title": "TestListCollection",
        "description": "A test collection for listing",
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    client.post("/v1/collections", json=schema)

    # Now list collections
    response = client.get("/v1/collections")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert any(col["definition"]["title"] == "TestListCollection" for col in data)


@pytest.mark.skip("Schema validation needs to be fixed")
def test_get_collection(client, cleanup):
    """Test getting a specific collection by ID"""
    # First create a collection
    schema = {
        "title": "TestGetCollection",
        "description": "A test collection for getting",
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    response = client.post("/v1/collections", json=schema)
    collection_id = response.json()["id"]

    # Now get the collection
    response = client.get(f"/v1/collections/{collection_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == collection_id
    assert data["definition"]["title"] == "TestGetCollection"


@pytest.mark.skip("Schema validation needs to be fixed")
def test_delete_collection(client, cleanup):
    """Test deleting a collection"""
    # First create a collection
    schema = {
        "title": "TestDeleteCollection",
        "description": "A test collection for deleting",
        "type": "object",
        "properties": {"name": {"type": "string"}},
    }
    response = client.post("/v1/collections", json=schema)
    collection_id = response.json()["id"]

    # Now delete the collection
    response = client.delete(f"/v1/collections/{collection_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True

    # Verify it's gone
    response = client.get(f"/v1/collections/{collection_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.skip("Schema validation needs to be fixed")
def test_collection_actions(client, cleanup):
    """Test the unified action endpoint for CRUD operations"""
    # First create a collection
    schema = {
        "title": "TestActionCollection",
        "description": "A test collection for actions",
        "type": "object",
        "properties": {"name": {"type": "string"}, "value": {"type": "integer"}},
    }
    response = client.post("/v1/collections", json=schema)
    collection_id = response.json()["id"]

    # Test create action
    create_payload = {"action": "create", "data": {"name": "Test Item", "value": 42}}
    response = client.post(
        f"/v1/collections/{collection_id}/action", json=create_payload
    )
    assert response.status_code == status.HTTP_200_OK
    item = response.json()
    assert item["name"] == "Test Item"
    assert item["value"] == 42
    item_id = item["id"]

    # Test read action
    read_payload = {"action": "read", "id": item_id}
    response = client.post(f"/v1/collections/{collection_id}/action", json=read_payload)
    assert response.status_code == status.HTTP_200_OK
    read_item = response.json()
    assert read_item["name"] == "Test Item"
    assert read_item["value"] == 42

    # Test update action
    update_payload = {"action": "update", "id": item_id, "data": {"value": 99}}
    response = client.post(
        f"/v1/collections/{collection_id}/action", json=update_payload
    )
    assert response.status_code == status.HTTP_200_OK
    updated_item = response.json()
    assert updated_item["name"] == "Test Item"  # Unchanged
    assert updated_item["value"] == 99  # Updated

    # Test query action
    query_payload = {"action": "query", "data": {"name": "Test Item"}}
    response = client.post(
        f"/v1/collections/{collection_id}/action", json=query_payload
    )
    assert response.status_code == status.HTTP_200_OK
    query_result = response.json()
    assert "items" in query_result
    assert len(query_result["items"]) == 1
    assert query_result["items"][0]["value"] == 99

    # Test delete action
    delete_payload = {"action": "delete", "id": item_id}
    response = client.post(
        f"/v1/collections/{collection_id}/action", json=delete_payload
    )
    assert response.status_code == status.HTTP_200_OK
    delete_result = response.json()
    assert delete_result["success"] is True
    assert delete_result["deleted_item"]["name"] == "Test Item"

    # Verify the item is deleted by trying to read it again
    response = client.post(f"/v1/collections/{collection_id}/action", json=read_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
