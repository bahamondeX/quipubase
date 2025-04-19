"""
Configuration file for pytest fixtures.

This file contains shared fixtures that can be used across multiple test files.
"""

import pytest
import shutil
import asyncio
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient

from quipubase import create_app
from quipubase.collection import Collection
from quipubase.state import StateManager
from quipubase.exchange import Exchange


@pytest.fixture
def client():
    """Create a FastAPI TestClient for testing API endpoints"""
    app = create_app()
    with TestClient(app) as client:
        yield client


class TestModel(Collection):
    """A simple model for testing"""

    name: str
    value: int = 0


@pytest.fixture
def test_collection():
    """Return a TestModel class for testing"""
    return TestModel


@pytest.fixture
def test_uuid():
    """Return a UUID for testing"""
    return uuid4()


@pytest.fixture
def state_manager():
    """Return a StateManager instance"""
    return StateManager()


@pytest.fixture
def exchange():
    """Return an Exchange instance for TestModel"""
    exchange = Exchange[TestModel]()
    yield exchange
    # Close all queues
    asyncio.run(exchange.close())


@pytest.fixture
def cleanup():
    """Cleanup fixture to remove test data after tests"""
    # Setup - can create any test data directories needed
    yield
    # Teardown - clean up test data
    test_data_path = Path.home() / ".data"
    if test_data_path.exists():
        # Only clean up collections created during tests
        try:
            # Clean up TestModel data
            TestModel.destroy()
        except Exception:
            pass

        # Clean up any test_ prefixed collections
        for item in test_data_path.iterdir():
            if item.name.startswith("test_"):
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
