"""
Configuration file for pytest fixtures.

This file contains shared fixtures that can be used across multiple test files.
"""

import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from quipubase import create_app
from quipubase.collection import Collection


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

