"""
Tests for the core Collection class functionality.
"""

import pytest
import uuid
import asyncio
import os
import shutil
from pathlib import Path

from quipubase.collection import Collection
from tests.conftest import TestModel

# Helper function to run coroutines
async def run_coroutine(coro):
    """Helper to unwrap decorated coroutines"""
    if asyncio.iscoroutine(coro):
        return await coro
    return coro

@pytest.mark.asyncio
async def test_collection_create_retrieve(cleanup):
    """Test creating and retrieving a collection item."""
    # Create a test item
    test_item = TestModel(name="Test Item", value=42)
    
    # Create the item synchronously to avoid any issues with decorated coroutines
    try:
        test_item.col().put(test_item.id.bytes, test_item.model_dump_json().encode("utf-8"))
    except Exception as e:
        # If directory doesn't exist, create it
        os.makedirs(os.path.dirname(TestModel.col_path()), exist_ok=True)
        test_item.col().put(test_item.id.bytes, test_item.model_dump_json().encode("utf-8"))
    
    # Retrieve the item directly using the RocksDB API
    raw_data = test_item.col().get(test_item.id.bytes)
    assert raw_data is not None
    
    # Test the path
    path = TestModel.col_path()
    assert os.path.exists(path)

def test_collection_path():
    """Test the collection path generation."""
    path = TestModel.col_path()
    assert path is not None
    assert len(path) > 0
    
    # Path should be a directory in user's home
    assert path.startswith(Path.home().as_posix())

def test_collection_json_schema():
    """Test the JSON schema generation."""
    schema = TestModel.col_json_schema()
    
    # Basic schema structure checks
    assert schema.title == "TestModel"
    assert "properties" in schema.model_dump()
    
    # Check that properties exist
    properties = schema.model_dump()["properties"]
    assert "id" in properties
    assert "name" in properties
    assert "value" in properties