import pytest
import uuid
import json
import asyncio
from pydantic import BaseModel, Field
from quipubase.collection import Collection
from quipubase.exchange import Exchange, Event
from quipubase.typedefs import JsonSchemaModel

class TestItem(Collection):
    name: str
    value: int = 0

@pytest.mark.skip("Coroutine handling in tests needs to be fixed")
@pytest.mark.asyncio
async def test_collection_operations(cleanup):
    """Test basic collection CRUD operations"""
    # Create a test item
    item = TestItem(name="Test Item", value=42)
    await item.create()
    item_id = item.id
    
    # Retrieve the item
    retrieved = await TestItem.retrieve(id=item_id)
    assert retrieved is not None
    assert retrieved.name == "Test Item"
    assert retrieved.value == 42
    
    # Update the item
    updated = await TestItem.update(id=item_id, value=99)
    assert updated is not None
    assert updated.name == "Test Item"  # Unchanged
    assert updated.value == 99  # Updated
    
    # Find items by query
    results = [item async for item in await TestItem.find(name="Test Item")]
    assert len(results) == 1
    assert results[0].value == 99
    
    # Delete the item
    deleted = await TestItem.delete(id=item_id)
    assert deleted is True
    
    # Verify it's gone
    not_found = await TestItem.retrieve(id=item_id)
    assert not_found is None

@pytest.mark.skip("Schema validation needs to be fixed")
def test_collection_schema(cleanup):
    """Test collection schema generation"""
    schema = TestItem.col_json_schema()
    assert isinstance(schema, JsonSchemaModel)
    assert schema.title == "TestItem"
    assert "name" in schema.properties
    assert "value" in schema.properties
    
    # Verify schema is saved
    schema_path = TestItem.col_path() + "/schema.json"
    import os
    assert os.path.exists(schema_path)

@pytest.mark.skip("Coroutine handling in tests needs to be fixed")
@pytest.mark.asyncio
async def test_exchange_operations(cleanup):
    """Test exchange publish and subscribe operations"""
    exchange = Exchange[TestItem]()
    
    # Create a test item
    item = TestItem(name="Exchange Test", value=42)
    
    # Setup a subscription
    subscription_name = "test-sub"
    results = []
    
    # Create a task to collect items from subscription
    async def collect_items():
        try:
            async for received_item in exchange.sub(sub=subscription_name):
                results.append(received_item)
                if len(results) >= 2:  # Collect 2 items then exit
                    break
        except Exception as e:
            print(f"Error in subscription: {str(e)}")
    
    # Start collecting in background
    collect_task = asyncio.create_task(collect_items())
    
    # Wait a bit for subscription to be ready
    await asyncio.sleep(0.1)
    
    # Publish two items
    item1 = TestItem(name="Item 1", value=1)
    await exchange.pub(sub=subscription_name, event="create", value=item1)
    
    item2 = TestItem(name="Item 2", value=2)
    await exchange.pub(sub=subscription_name, event="create", value=item2)
    
    # Wait for collection to finish
    await asyncio.wait_for(collect_task, timeout=1)
    
    # Close subscription
    await exchange.close(sub=subscription_name)
    
    # Verify results
    assert len(results) == 2
    assert results[0].name == "Item 1"
    assert results[1].name == "Item 2"

@pytest.mark.skip("Coroutine handling in tests needs to be fixed")
@pytest.mark.asyncio
async def test_sse_event_format(cleanup):
    """Test SSE event formatting"""
    # Create a test item
    item = TestItem(name="SSE Test", value=123)
    
    # Create an event
    event = Event[TestItem](event="create", data=item)
    
    # Format as SSE
    sse_text = event.to_sse()
    
    # Verify format
    assert "event: create" in sse_text
    assert f"id: {event.ref}" in sse_text
    assert "data:" in sse_text
    assert "time:" in sse_text
    
    # Verify data content (item JSON is in the data field)
    assert "SSE Test" in sse_text
    assert "123" in sse_text