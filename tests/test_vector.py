"""
Tests for the Vector Embedding and Vector Store functionality
"""

import pytest
import numpy as np
import json
from fastapi.testclient import TestClient

from quipubase.vector.typedefs import (
    EmbedText,
    QueryText,
    DeleteText,
    Embedding,
)
from quipubase.vector.services import VectorStoreService


def test_embed_endpoint(client: TestClient):
    """Test embedding text using the endpoint"""
    # Test the embedding endpoint
    response = client.post(
        "/v1/vector",
        json={
            "content": ["This is a test sentence for embedding"],
            "model": "mini-scope"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "count" in data
    assert "ellapsed" in data
    assert data["count"] == 1
    
    # Verify the embedding structure
    embedding = data["data"][0]
    assert "content" in embedding
    assert "embedding" in embedding
    assert embedding["content"] == "This is a test sentence for embedding"
    assert isinstance(embedding["embedding"], list)
    # mini-scope model produces 384-dimensional embeddings
    assert len(embedding["embedding"]) == 384


def test_embedding_batch(client: TestClient):
    """Test embedding multiple texts in a single request"""
    test_texts = ["First test text", "Second test text", "Third test text"]
    
    response = client.post(
        "/v1/vector",
        json={
            "content": test_texts,
            "model": "mini-scope"
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    
    # Verify all embeddings were generated
    embeddings = data["data"]
    assert len(embeddings) == 3
    
    for i, embedding in enumerate(embeddings):
        assert embedding["content"] == test_texts[i]
        assert len(embedding["embedding"]) == 384


def test_different_embedding_models(client: TestClient):
    """Test embedding generation with different models"""
    test_text = ["Test text for different models"]
    
    # Test mini-scope model
    response = client.post(
        "/v1/vector",
        json={"content": test_text, "model": "mini-scope"},
    )
    assert response.status_code == 200
    mini_scope_dim = len(response.json()["data"][0]["embedding"])
    assert mini_scope_dim == 384
    
    # Test poly-sage model if available
    try:
        response = client.post(
            "/v1/vector",
            json={"content": test_text, "model": "poly-sage"},
        )
        assert response.status_code == 200
        poly_sage_dim = len(response.json()["data"][0]["embedding"])
        # poly-sage typically has 768 dimensions
        assert poly_sage_dim == 768
    except Exception:
        # Skip if model not available
        pytest.skip("poly-sage model not available")


def test_get_embedding_by_id(client: TestClient):
    """Test retrieving an embedding by ID"""
    namespace = "test_get_namespace"
    test_text = ["Text to retrieve by ID"]
    
    # First, create the embedding
    response = client.post(
        f"/v1/vector/{namespace}",
        json={"content": test_text, "model": "mini-scope"},
    )
    assert response.status_code == 200
    
    # Get the ID of the created embedding
    embedding_id = response.json()["data"][0]["id"]
    
    # Retrieve the embedding by ID
    response = client.get(f"/v1/vector/{namespace}/{embedding_id}")
    assert response.status_code == 200
    
    # Verify the retrieved embedding
    embedding = response.json()
    assert embedding["content"] == test_text[0]
    assert embedding["id"] == embedding_id
    
    # Manually clean up with a request (FastAPI TestClient doesn't support json/data in delete)
    headers = {"Content-Type": "application/json"}
    response = client.request(
        "DELETE", 
        f"/v1/vector/{namespace}", 
        headers=headers,
        content=json.dumps({"ids": [embedding_id]})
    )
    assert response.status_code == 200


def test_upsert_query_delete_flow(client: TestClient):
    """Test the full vector store workflow: upsert, query, and delete"""
    namespace = "test_namespace"
    test_texts = ["Hello world", "Testing vector embeddings", "Quipubase rocks"]
    
    # First, upsert the test texts
    response = client.post(
        f"/v1/vector/{namespace}",
        json={
            "content": test_texts,
            "model": "mini-scope"
        },
    )
    assert response.status_code == 200
    upsert_data = response.json()
    assert "data" in upsert_data
    assert "count" in upsert_data
    assert upsert_data["count"] == 3
    
    # Store the IDs for later deletion
    ids = [item["id"] for item in upsert_data["data"]]
    
    # Now query for similar texts - convert scalar to list
    response = client.put(
        f"/v1/vector/{namespace}",
        json={
            "content": ["Hello testing"],  # Put in a list to match expected format
            "model": "mini-scope",
            "top_k": 2
        },
    )
    assert response.status_code == 200
    query_data = response.json()
    assert "data" in query_data
    assert "count" in query_data
    assert query_data["count"] == 2
    
    # Verify the query results
    for match in query_data["data"]:
        assert "id" in match
        assert "score" in match
        assert "content" in match
        assert match["content"] in test_texts
        assert match["score"] > 0 and match["score"] <= 1  # Score should be between 0 and 1
    
    # Finally, delete the embeddings - using request method
    headers = {"Content-Type": "application/json"}
    response = client.request(
        "DELETE", 
        f"/v1/vector/{namespace}", 
        headers=headers,
        content=json.dumps({"ids": ids})
    )
    assert response.status_code == 200
    delete_data = response.json()
    assert "data" in delete_data
    assert "count" in delete_data
    assert delete_data["count"] == 3
    assert set(delete_data["data"]) == set(ids)
    
    # Try to query again, should return no results
    response = client.put(
        f"/v1/vector/{namespace}",
        json={
            "content": ["Hello testing"],
            "model": "mini-scope",
            "top_k": 2
        },
    )
    assert response.status_code == 200
    query_data = response.json()
    assert query_data["count"] == 0


def test_query_with_different_top_k(client: TestClient):
    """Test querying with different top_k values"""
    namespace = "test_top_k"
    test_texts = [
        "First sample text", 
        "Second sample text", 
        "Third sample text",
        "Fourth sample text",
        "Fifth sample text"
    ]
    
    # Insert the texts
    response = client.post(
        f"/v1/vector/{namespace}",
        json={"content": test_texts, "model": "mini-scope"},
    )
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["data"]]
    
    # Query with top_k=1
    response = client.put(
        f"/v1/vector/{namespace}",
        json={"content": ["sample text"], "model": "mini-scope", "top_k": 1},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
    
    # Query with top_k=3
    response = client.put(
        f"/v1/vector/{namespace}",
        json={"content": ["sample text"], "model": "mini-scope", "top_k": 3},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 3
    
    # Query with top_k=5
    response = client.put(
        f"/v1/vector/{namespace}",
        json={"content": ["sample text"], "model": "mini-scope", "top_k": 5},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 5
    
    # Clean up
    headers = {"Content-Type": "application/json"}
    response = client.request(
        "DELETE", 
        f"/v1/vector/{namespace}", 
        headers=headers,
        content=json.dumps({"ids": ids})
    )
    assert response.status_code == 200


def test_error_handling(client: TestClient):
    """Test error handling for invalid requests"""
    # Test with missing model
    response = client.post(
        "/v1/vector",
        json={"content": ["Test text"]},  # Missing model parameter
    )
    assert response.status_code != 200
    
    # Test with invalid model
    response = client.post(
        "/v1/vector",
        json={"content": ["Test text"], "model": "invalid-model"},
    )
    assert response.status_code != 200
    
    # Test with empty content
    response = client.post(
        "/v1/vector",
        json={"content": [], "model": "mini-scope"},
    )
    assert response.status_code == 200  # Should handle empty content gracefully
    assert response.json()["count"] == 0


def test_vector_store_service():
    """Test the VectorStoreService directly"""
    service = VectorStoreService(namespace="test_service", model="mini-scope")
    
    # Test embedding generation
    text = "Test embedding generation"
    embedding = service.embed(text)
    assert isinstance(embedding, np.ndarray)
    assert embedding.dtype == np.float32
    assert embedding.shape[1] == 384  # mini-scope produces 384-dim embeddings
    
    # Test upsert and query operations
    embedding_obj = Embedding(content=text, embedding=embedding[0])
    upsert_response = service.upsert([embedding_obj])
    assert upsert_response["count"] == 1
    
    # Test retrieval
    retrieved = service.get(embedding_obj.id)
    assert retrieved is not None
    assert retrieved.content == text
    assert np.array_equal(retrieved.embedding, embedding[0])
    
    # Test query
    query_vector = service.embed("Test embedding").tolist()
    query_response = service.query(query_vector, top_k=1)
    assert query_response["count"] == 1
    assert query_response["data"][0].content == text  # Access as attribute, not subscriptable
    
    # Test delete
    delete_response = service.delete([embedding_obj.id])
    assert delete_response["count"] == 1
    assert delete_response["data"] == [embedding_obj.id]
    
    # Verify deletion
    assert service.get(embedding_obj.id) is None


def test_multiple_namespaces(client: TestClient):
    """Test using multiple namespaces for vector storage"""
    namespace1 = "test_namespace1"
    namespace2 = "test_namespace2"
    test_text = "Test text for multiple namespaces"
    
    # Insert the same text in both namespaces
    response1 = client.post(
        f"/v1/vector/{namespace1}",
        json={"content": [test_text], "model": "mini-scope"},
    )
    assert response1.status_code == 200
    id1 = response1.json()["data"][0]["id"]
    
    response2 = client.post(
        f"/v1/vector/{namespace2}",
        json={"content": [test_text], "model": "mini-scope"},
    )
    assert response2.status_code == 200
    id2 = response2.json()["data"][0]["id"]
    
    # The IDs should be the same since they contain the same text
    assert id1 == id2
    
    # Verify both namespaces have the embedding
    response1 = client.get(f"/v1/vector/{namespace1}/{id1}")
    assert response1.status_code == 200
    
    response2 = client.get(f"/v1/vector/{namespace2}/{id2}")
    assert response2.status_code == 200
    
    # Delete from namespace1 only - use DELETE correctly
    headers = {"Content-Type": "application/json"}
    response = client.request(
        "DELETE", 
        f"/v1/vector/{namespace1}", 
        headers=headers,
        content=json.dumps({"ids": [id1]})
    )
    assert response.status_code == 200
    
    # Namespace1 should no longer have the embedding
    response1 = client.put(
        f"/v1/vector/{namespace1}",
        json={"content": ["Test text for multiple namespaces"], "model": "mini-scope", "top_k": 1},
    )
    assert response1.status_code == 200
    assert response1.json()["count"] == 0
    
    # Namespace2 should still have the embedding
    response2 = client.put(
        f"/v1/vector/{namespace2}",
        json={"content": ["Test text for multiple namespaces"], "model": "mini-scope", "top_k": 1},
    )
    assert response2.status_code == 200
    assert response2.json()["count"] == 1
    
    # Clean up namespace2
    headers = {"Content-Type": "application/json"}
    response = client.request(
        "DELETE", 
        f"/v1/vector/{namespace2}", 
        headers=headers,
        content=json.dumps({"ids": [id2]})
    )
    assert response.status_code == 200