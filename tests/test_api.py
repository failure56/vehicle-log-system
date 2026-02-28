"""
api/main.py のテスト。
FastAPI エンドポイントを TestClient で検証する。
"""
import os
import json

import duckdb
import pandas as pd
import numpy as np
import pytest

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# フィクスチャ: テスト用 DB/チャンクを準備し、api/main.py のパスを差し替え
# ---------------------------------------------------------------------------

@pytest.fixture()
def api_client(tmp_data_dir, db_con, sample_chunk_dir, monkeypatch):
    """
    テスト用 DB とチャンクで api/main.py をロードする TestClient。
    """
    db_path = str(tmp_data_dir / "db" / "vehicle_logs.duckdb")

    # GPS ログをテスト用 DB に挿入
    gps_records = []
    base_ts = pd.Timestamp("2024-01-01")
    for i in range(20):
        gps_records.append({
            "ts": base_ts + pd.Timedelta(seconds=i),
            "vehicle_id": "test_vehicle",
            "lat": 35.68 + i * 0.001,
            "lon": 139.76 + i * 0.001,
            "speed": 30.0 + i,
            "heading": float(i * 18 % 360),
        })
    gps_df = pd.DataFrame(gps_records)
    db_con.register("gps_df", gps_df)
    db_con.execute("INSERT INTO gps_log SELECT * FROM gps_df")
    db_con.unregister("gps_df")

    # CAN ログをテスト用 DB に挿入
    can_records = []
    for i in range(20):
        for sig in ["steering", "throttle", "brake", "speed"]:
            can_records.append({
                "ts": base_ts + pd.Timedelta(seconds=i),
                "vehicle_id": "test_vehicle",
                "signal": sig,
                "value": float(i),
            })
    can_df = pd.DataFrame(can_records)
    db_con.register("can_df", can_df)
    db_con.execute("INSERT INTO can_log SELECT * FROM can_df")
    db_con.unregister("can_df")

    db_con.close()  # TestClient は read_only で再接続するため閉じる

    # main モジュールのパス定数を差し替え
    import api.main as api_main
    monkeypatch.setattr(api_main, "DB_PATH", db_path)
    monkeypatch.setattr(api_main, "CHUNKS_DIR", sample_chunk_dir)

    # モデルを None にリセット（テスト間の汚染防止）
    monkeypatch.setattr(api_main, "_model", None)

    client = TestClient(api_main.app)
    yield client


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

class TestHealth:
    def test_health_ok(self, api_client):
        """GET /health が {"status": "ok"} を返すこと。"""
        resp = api_client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# / (root)
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_returns_200(self, api_client):
        """GET / が 200 を返すこと。"""
        resp = api_client.get("/")
        assert resp.status_code == 200

    def test_root_contains_service_info(self, api_client):
        """GET / がサービス名とバージョンを含むこと。"""
        data = api_client.get("/").json()
        assert data["service"] == "Vehicle Log System API"
        assert "version" in data

    def test_root_contains_endpoints(self, api_client):
        """GET / がエンドポイント一覧を含むこと。"""
        data = api_client.get("/").json()
        assert "endpoints" in data
        endpoints = data["endpoints"]
        # 主要エンドポイントが列挙されていること
        assert "/health" in endpoints
        assert "/chunks" in endpoints
        assert "/search?q=...&top_k=5" in endpoints


# ---------------------------------------------------------------------------
# /chunks
# ---------------------------------------------------------------------------

class TestListChunks:
    def test_list_chunks(self, api_client):
        """GET /chunks がチャンク一覧を返すこと。"""
        resp = api_client.get("/chunks")
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert "chunks" in data
        assert data["count"] == 2  # sample_chunk_dir には 2 チャンク

    def test_chunks_filenames(self, api_client):
        """チャンクファイル名が chunk_*.parquet 形式であること。"""
        resp = api_client.get("/chunks")
        for fname in resp.json()["chunks"]:
            assert fname.startswith("chunk_")
            assert fname.endswith(".parquet")


# ---------------------------------------------------------------------------
# /chunk/{cid}
# ---------------------------------------------------------------------------

class TestGetChunk:
    def test_get_chunk_0(self, api_client):
        """GET /chunk/0 が正常にデータを返すこと。"""
        resp = api_client.get("/chunk/0")
        assert resp.status_code == 200
        data = resp.json()
        assert data["chunk_id"] == 0
        assert data["total_rows"] == 10  # sample_chunk_dir の chunk は 10 行
        assert "data" in data

    def test_get_chunk_not_found(self, api_client):
        """存在しないチャンク ID で 404 が返ること。"""
        resp = api_client.get("/chunk/999")
        assert resp.status_code == 404

    def test_chunk_columns(self, api_client):
        """チャンクにカラム情報が含まれること。"""
        resp = api_client.get("/chunk/0")
        data = resp.json()
        assert "columns" in data
        assert "lat" in data["columns"]
        assert "lon" in data["columns"]


# ---------------------------------------------------------------------------
# /logs
# ---------------------------------------------------------------------------

class TestLogs:
    def test_query_gps_log(self, api_client):
        """GET /logs?table=gps_log がデータを返すこと。"""
        resp = api_client.get("/logs", params={"table": "gps_log", "limit": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert data["table"] == "gps_log"
        assert data["count"] == 5

    def test_query_can_log(self, api_client):
        """GET /logs?table=can_log がデータを返すこと。"""
        resp = api_client.get("/logs", params={"table": "can_log", "limit": 10})
        assert resp.status_code == 200
        data = resp.json()
        assert data["table"] == "can_log"
        assert data["count"] == 10

    def test_invalid_table(self, api_client):
        """不正なテーブル名で 400 が返ること。"""
        resp = api_client.get("/logs", params={"table": "invalid_table"})
        assert resp.status_code == 400

    def test_default_limit(self, api_client):
        """limit を省略した場合デフォルト 100 が使われること。"""
        resp = api_client.get("/logs", params={"table": "gps_log"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] <= 100

    def test_filter_by_vehicle_id(self, api_client):
        """vehicle_id フィルタが機能すること。"""
        resp = api_client.get(
            "/logs",
            params={"table": "gps_log", "vehicle_id": "test_vehicle", "limit": 5},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0
        for row in data["data"]:
            assert row["vehicle_id"] == "test_vehicle"

    def test_filter_nonexistent_vehicle(self, api_client):
        """存在しない vehicle_id で空結果が返ること。"""
        resp = api_client.get(
            "/logs",
            params={"table": "gps_log", "vehicle_id": "nonexistent"},
        )
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_sql_injection_prevented(self, api_client):
        """SQL インジェクション文字列で不正な結果にならないこと。"""
        resp = api_client.get(
            "/logs",
            params={"table": "gps_log", "vehicle_id": "'; DROP TABLE gps_log; --"},
        )
        # 400 or 200(空) のいずれかで、テーブルが破壊されないこと
        assert resp.status_code in (200, 400)
        # テーブルが存在し続けることを確認
        resp2 = api_client.get("/logs", params={"table": "gps_log", "limit": 1})
        assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# /search (モデルロードが必要 → slow マーク)
# ---------------------------------------------------------------------------

class TestSearch:
    @pytest.mark.slow
    def test_search_returns_results(self, api_client, tmp_data_dir):
        """GET /search がベクトル類似検索結果を返すこと。"""
        # まず embeddings テーブルにダミーデータを挿入
        db_path = str(tmp_data_dir / "db" / "vehicle_logs.duckdb")
        con = duckdb.connect(db_path)

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            con.close()
            pytest.skip("sentence-transformers not installed")

        model = SentenceTransformer("all-MiniLM-L6-v2")
        text = "High speed driving on highway"
        vec = model.encode(text).tolist()

        con.execute("""
            INSERT INTO embeddings
            (chunk_id, chunk_file, text_repr, vector, speed_mean, speed_std,
             lat_range, lon_range, num_rows, start_ts, end_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [0, "chunk_0.parquet", text, vec, 80.0, 10.0, 0.01, 0.01, 10, None, None])
        con.close()

        resp = api_client.get("/search", params={"q": "fast driving", "top_k": 1})
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "fast driving"
        assert len(data["results"]) == 1
        assert "similarity" in data["results"][0]

    def test_search_missing_query(self, api_client):
        """クエリパラメータなしで 422 が返ること。"""
        resp = api_client.get("/search")
        assert resp.status_code == 422
