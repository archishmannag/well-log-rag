import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(test_client):
    """Test the root endpoint."""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"


def test_list_files(test_client):
    """Test listing files."""
    response = test_client.get("/files")
    assert response.status_code == 200
    assert "files" in response.json()
    assert "count" in response.json()

    # If we have files, check their structure
    if response.json()["count"] > 0:
        file = response.json()["files"][0]
        assert "id" in file
        assert "well_name" in file
        assert "file_type" in file


def test_get_file(test_client):
    """Test getting a specific file."""
    # First get the list of files
    response = test_client.get("/files")
    assert response.status_code == 200

    # If we have files, try to get the first one
    if response.json()["count"] > 0:
        file_id = response.json()["files"][0]["id"]

        # Get the specific file
        response = test_client.get(f"/files/{file_id}")
        assert response.status_code == 200
        assert "info" in response.json()
        assert "content" in response.json()

        # Check content structure
        content = response.json()["content"]
        assert "header" in content
        assert "data" in content
    else:
        pytest.skip("No files available for testing")


def test_nonexistent_file(test_client):
    """Test requesting a non-existent file."""
    response = test_client.get("/files/nonexistent-id")
    assert response.status_code == 404
