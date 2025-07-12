import os
import pytest
from fastapi.testclient import TestClient
import glob
from pathlib import Path

# Setup test data directory paths
DATA_DIR = Path(__file__).parent.parent / "data"


@pytest.fixture
def test_data_dir():
    """Fixture to provide the test data directory path."""
    return DATA_DIR


@pytest.fixture
def witsml_files():
    """Fixture to provide a list of WITSML files in the data directory."""
    witsml_files = glob.glob(str(DATA_DIR / "*.xml"))
    return witsml_files


@pytest.fixture
def test_client():
    """Fixture to provide a FastAPI test client."""
    from tests.test_server.app import app

    return TestClient(app)
