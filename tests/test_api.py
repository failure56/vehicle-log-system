"""Tests for FastAPI endpoints."""
import pytest
import requests
import time


API_BASE_URL = "http://localhost:8000"


def wait_for_api(timeout=30):
    """Wait for API to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f"{API_BASE_URL}/chunks", timeout=1)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            time.sleep(1)
    return False


def test_api_is_running():
    """Test that API server is running."""
    assert wait_for_api(), "API did not start within timeout period"


def test_list_chunks_endpoint():
    """Test GET /chunks endpoint."""
    if not wait_for_api():
        pytest.skip("API not available")
    
    response = requests.get(f"{API_BASE_URL}/chunks")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "chunks" in data, "Response should contain 'chunks' key"
    assert isinstance(data["chunks"], list), "'chunks' should be a list"
    
    print(f"API returned {len(data['chunks'])} chunks")


def test_get_chunk_endpoint_valid():
    """Test GET /chunk/{cid} endpoint with valid chunk."""
    if not wait_for_api():
        pytest.skip("API not available")
    
    # First get list of chunks
    response = requests.get(f"{API_BASE_URL}/chunks")
    data = response.json()
    
    if len(data["chunks"]) == 0:
        pytest.skip("No chunks available for testing")
    
    # Test getting first chunk (chunk_0)
    response = requests.get(f"{API_BASE_URL}/chunk/0")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    chunk_data = response.json()
    assert isinstance(chunk_data, dict), "Chunk data should be a dictionary"
    
    # Check for expected keys (column names from parquet)
    expected_keys = ["ts", "vehicle_id", "sec"]
    for key in expected_keys:
        assert key in chunk_data, f"Expected key '{key}' in chunk data"
    
    print(f"Successfully retrieved chunk 0 with keys: {list(chunk_data.keys())}")


def test_get_chunk_endpoint_invalid():
    """Test GET /chunk/{cid} endpoint with invalid chunk ID."""
    if not wait_for_api():
        pytest.skip("API not available")
    
    # Try to get a chunk that doesn't exist
    response = requests.get(f"{API_BASE_URL}/chunk/99999")
    assert response.status_code == 200, "API should return 200 even for not found"
    
    data = response.json()
    assert "error" in data, "Should return error for non-existent chunk"
    assert data["error"] == "not found", "Error message should be 'not found'"
    
    print("Correctly handled invalid chunk ID")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
