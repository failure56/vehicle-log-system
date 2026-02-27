"""
embedding/embed_chunks.py のテスト。
チャンクのテキスト変換処理を検証する（モデル推論はマーク付き）。
"""
import pandas as pd
import numpy as np
import pytest

from embedding.embed_chunks import chunk_to_text, init_embedding_table


class TestChunkToText:
    """chunk_to_text のテスト。"""

    def _make_df(self) -> pd.DataFrame:
        """テスト用チャンク DataFrame。"""
        n = 10
        return pd.DataFrame({
            "ts": pd.date_range("2024-01-01", periods=n, freq="1s"),
            "vehicle_id": "test_vehicle",
            "lat": np.linspace(35.68, 35.69, n),
            "lon": np.linspace(139.76, 139.77, n),
            "speed": np.random.default_rng(0).uniform(20, 60, n),
            "heading": np.random.default_rng(0).uniform(0, 360, n),
            "can_steering_mean": [5.0] * n,
            "can_throttle_mean": [0.4] * n,
        })

    def test_returns_string(self):
        """文字列を返すこと。"""
        text = chunk_to_text(self._make_df(), "chunk_0.parquet")
        assert isinstance(text, str)

    def test_contains_filename(self):
        """テキストにファイル名が含まれること。"""
        text = chunk_to_text(self._make_df(), "chunk_0.parquet")
        assert "chunk_0.parquet" in text

    def test_contains_speed_info(self):
        """テキストに speed 統計情報が含まれること。"""
        text = chunk_to_text(self._make_df(), "chunk_0.parquet")
        assert "Speed" in text
        assert "mean=" in text

    def test_contains_gps_range(self):
        """テキストに GPS 範囲情報が含まれること。"""
        text = chunk_to_text(self._make_df(), "chunk_0.parquet")
        assert "GPS range" in text
        assert "lat=" in text

    def test_contains_can_signals(self):
        """テキストに CAN 信号情報が含まれること。"""
        text = chunk_to_text(self._make_df(), "chunk_0.parquet")
        assert "CAN" in text

    def test_contains_data_points(self):
        """テキストにデータポイント数が含まれること。"""
        text = chunk_to_text(self._make_df(), "chunk_0.parquet")
        assert "10 data points" in text

    def test_no_crash_without_optional_columns(self):
        """speed, lat, lon がないデータフレームでもクラッシュしないこと。"""
        df = pd.DataFrame({"ts": pd.date_range("2024-01-01", periods=5, freq="1s")})
        text = chunk_to_text(df, "chunk_empty.parquet")
        assert isinstance(text, str)
        assert "chunk_empty.parquet" in text

    def test_heading_info(self):
        """テキストに heading 情報が含まれること。"""
        text = chunk_to_text(self._make_df(), "chunk_0.parquet")
        assert "Heading" in text


class TestInitEmbeddingTable:
    """init_embedding_table のテスト。"""

    def test_creates_embedding_table(self, db_con):
        """embeddings テーブルが作成されること（フィクスチャで既にあるが冪等確認）。"""
        init_embedding_table(db_con)
        tables = [t[0] for t in db_con.execute("SHOW TABLES").fetchall()]
        assert "embeddings" in tables

    def test_idempotent(self, db_con):
        """2 回呼んでもエラーにならないこと。"""
        init_embedding_table(db_con)
        init_embedding_table(db_con)
        count = db_con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
        assert count == 0


class TestEmbedding:
    """ベクトル化の統合テスト（モデルロードが必要）。"""

    @pytest.mark.slow
    def test_model_encode(self):
        """sentence-transformers モデルが 384 次元のベクトルを返すこと。"""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            pytest.skip("sentence-transformers not installed")

        model = SentenceTransformer("all-MiniLM-L6-v2")
        vec = model.encode("test query")
        assert vec.shape == (384,)

    @pytest.mark.slow
    def test_batch_encode(self):
        """複数テキストのバッチエンコードが正しく動作すること。"""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            pytest.skip("sentence-transformers not installed")

        model = SentenceTransformer("all-MiniLM-L6-v2")
        texts = ["high speed driving", "slow city driving", "stopped"]
        vecs = model.encode(texts)
        assert vecs.shape == (3, 384)
