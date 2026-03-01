 テスト生成指示

## ルール

- テストフレームワーク: pytest
- DuckDB はインメモリ (`:memory:`) で接続してテスト
- テスト関数名: `test_{対象関数名}_{条件}` の形式
- Parquet ファイルのテストは `tmp_path` fixture を使用
- docstring にテスト意図を日本語で記述
- 正常系・異常系・境界値の3パターンを最低限カバー

## テストパターン例

### DuckDB 関連

```python
def test_prepare_data_loads_gps_log(tmp_path):
    """GPS CSV を DuckDB にロードし、gps_log テーブルにデータが格納されることを確認する。"""
    db_path = str(tmp_path / "test.duckdb")
    con = duckdb.connect(db_path)
    # ... テストロジック
    con.close()
```

### Parquet 関連

```python
def test_make_chunks_creates_parquet(tmp_path):
    """チャンク分割によって Parquet ファイルが生成されることを確認する。"""
    chunk_dir = tmp_path / "chunks"
    chunk_dir.mkdir()
    # ... テストロジック
```

### FastAPI 関連

```python
from fastapi.testclient import TestClient

def test_health_endpoint():
    """ヘルスチェックエンドポイントが 200 を返すことを確認する。"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
```
