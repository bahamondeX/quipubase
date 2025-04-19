"""
Test suite for quipubase.

This package contains tests for all components of the quipubase library:
- Collection/document database operations
- Schema definition and class generation
- Event exchange and PubSub
- State management
- FastAPI handlers and endpoints
- Utility functions
"""

import asyncio
import os
import uuid

import pytest
from fastapi.testclient import TestClient

from quipubase import create_app


@pytest.fixture
def client():
    """Create a test client for the app"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def cleanup():
    """Cleanup temporary test collections and files"""
    yield
    # This code runs after each test
    # Clean up any test collections/data
    test_dir = os.path.join(os.path.expanduser("~"), ".data", "test_collections")
    if os.path.exists(test_dir):
        import shutil

        shutil.rmtree(test_dir)
