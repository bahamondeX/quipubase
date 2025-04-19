import json
import threading
import time
import uuid

import pytest
import requests
# Commented out since this module isn't installed
# import sseclient
from fastapi import status


@pytest.mark.skip("SSE client tests require a running server")
def test_sse_connection():
    """Test connecting to an SSE endpoint and receiving events"""
    # This test requires a running server and the sseclient-py package
    # Start the server in a separate thread or subprocess

    # Create a collection via the REST API
    schema = {
        "title": "SSETestCollection",
        "description": "A test collection for SSE",
        "type": "object",
        "properties": {"name": {"type": "string"}, "value": {"type": "integer"}},
    }

    # Use requests instead of test client since we need a real HTTP server
    base_url = "http://localhost:8000"  # Adjust port if needed

    # Create collection
    response = requests.post(f"{base_url}/v1/collections", json=schema)
    assert response.status_code == 200
    collection_id = response.json()["id"]

    # Start SSE client in a separate thread
    events = []

    def sse_client_thread():
        headers = {"Accept": "text/event-stream"}
        response = requests.get(
            f"{base_url}/v1/pubsub/{collection_id}/subscribe?subscription=test-sse",
            stream=True,
            headers=headers,
        )
        client = sseclient.SSEClient(response)
        for event in client.events():
            events.append(event)
            if len(events) >= 1:  # Exit after receiving at least one event
                break

    # Start the SSE client thread
    thread = threading.Thread(target=sse_client_thread)
    thread.daemon = True
    thread.start()

    # Give the SSE connection time to establish
    time.sleep(1)

    # Publish an event via the REST API
    create_payload = {
        "action": "create",
        "value": {"name": "SSE Test Item", "value": 42},
        "sub": "test-sse",
    }
    response = requests.post(
        f"{base_url}/v1/pubsub/{collection_id}/publish", json=create_payload
    )
    assert response.status_code == 200

    # Wait for the event to be received
    time.sleep(2)
    thread.join(timeout=3)

    # Verify events were received
    assert len(events) > 0
    event = events[0]
    assert event.event == "create"
    data = json.loads(event.data)
    assert data["name"] == "SSE Test Item"

    # Close the subscription
    response = requests.post(
        f"{base_url}/v1/pubsub/{collection_id}/close?subscription=test-sse"
    )
    assert response.status_code == 200
