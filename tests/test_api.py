"""FastAPI エンドポイントのテスト。"""
import pytest
import requests
import time


API_BASE_URL = "http://localhost:8000"


def wait_for_api(timeout=30):
    """APIが起動するまで待機する。
    
    Args:
        timeout: 最大待機時間（秒）
        
    Returns:
        bool: APIが起動した場合True、タイムアウトした場合False
    """
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
    """APIサーバーが起動しているかテストする。"""
    assert wait_for_api(), "API did not start within timeout period"


def test_list_chunks_endpoint():
    """GET /chunks エンドポイントをテストする。"""
    if not wait_for_api():
        pytest.skip("API not available")
    
    response = requests.get(f"{API_BASE_URL}/chunks")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert "chunks" in data, "Response should contain 'chunks' key"
    assert isinstance(data["chunks"], list), "'chunks' should be a list"
    
    print(f"API returned {len(data['chunks'])} chunks")


def test_get_chunk_endpoint_valid():
    """GET /chunk/{cid} エンドポイントを有効なチャンクIDでテストする。"""
    if not wait_for_api():
        pytest.skip("API not available")
    
    # まずチャンクのリストを取得
    response = requests.get(f"{API_BASE_URL}/chunks")
    data = response.json()
    
    if len(data["chunks"]) == 0:
        pytest.skip("No chunks available for testing")
    
    # 最初のチャンク（chunk_0）を取得してテスト
    response = requests.get(f"{API_BASE_URL}/chunk/0")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    chunk_data = response.json()
    assert isinstance(chunk_data, dict), "Chunk data should be a dictionary"
    
    # Parquetファイルから期待されるキー（カラム名）を確認
    expected_keys = ["ts", "vehicle_id", "sec"]
    for key in expected_keys:
        assert key in chunk_data, f"Expected key '{key}' in chunk data"
    
    print(f"Successfully retrieved chunk 0 with keys: {list(chunk_data.keys())}")


def test_get_chunk_endpoint_invalid():
    """GET /chunk/{cid} エンドポイントを無効なチャンクIDでテストする。"""
    if not wait_for_api():
        pytest.skip("API not available")
    
    # 存在しないチャンクを取得しようとする
    response = requests.get(f"{API_BASE_URL}/chunk/99999")
    assert response.status_code == 200, "API should return 200 even for not found"
    
    data = response.json()
    assert "error" in data, "Should return error for non-existent chunk"
    assert data["error"] == "not found", "Error message should be 'not found'"
    
    print("Correctly handled invalid chunk ID")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
