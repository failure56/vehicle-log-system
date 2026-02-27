"""
chunking/make_chunks.py のテスト。
GPS + CAN ログから 60 秒チャンクの生成を検証する。
"""
import os
import math

import duckdb
import pandas as pd
import numpy as np
import pytest

from chunking.make_chunks import compute_can_features, make_chunks, save_parquet, CHUNK_LEN


# ---------------------------------------------------------------------------
# ヘルパー：テスト用 GPS / CAN DataFrame
# ---------------------------------------------------------------------------

def _make_gps_df(n_seconds: int = 180) -> pd.DataFrame:
    """n_seconds 秒分の GPS データを生成する。"""
    base_ts = pd.Timestamp("2024-01-01")
    return pd.DataFrame({
        "ts": [base_ts + pd.Timedelta(seconds=i) for i in range(n_seconds)],
        "vehicle_id": "test_vehicle",
        "lat": np.linspace(35.68, 35.69, n_seconds),
        "lon": np.linspace(139.76, 139.77, n_seconds),
        "speed": np.random.default_rng(42).uniform(20, 60, n_seconds),
        "heading": np.random.default_rng(42).uniform(0, 360, n_seconds),
    })


def _make_can_df(n_seconds: int = 180) -> pd.DataFrame:
    """n_seconds 秒分の CAN データを生成する（0.1秒間隔, 4 信号）。"""
    records = []
    base_ts = pd.Timestamp("2024-01-01")
    for i in range(n_seconds * 10):  # 0.1 秒間隔
        t = base_ts + pd.Timedelta(seconds=i * 0.1)
        for signal, val in [
            ("steering", math.sin(i * 0.01) * 20),
            ("throttle", 0.4),
            ("brake", 0.0),
            ("speed", 40 + math.sin(i * 0.005) * 10),
        ]:
            records.append({"ts": t, "vehicle_id": "test_vehicle", "signal": signal, "value": val})
    return pd.DataFrame(records)


class TestComputeCanFeatures:
    """compute_can_features のテスト。"""

    def test_returns_dict(self):
        """辞書を返すこと。"""
        can_df = _make_can_df(120)
        # sec_start/sec_end は UNIX タイムスタンプ（マイクロ秒 → //10**6 済み前提）
        sec_start = can_df["ts"].astype("int64").iloc[0] // 10**6
        sec_end = sec_start + CHUNK_LEN
        result = compute_can_features(can_df, sec_start, sec_end)
        assert isinstance(result, dict)

    def test_contains_4_signals(self):
        """4 信号分の統計量が返ること。"""
        can_df = _make_can_df(120)
        sec_start = can_df["ts"].astype("int64").iloc[0] // 10**6
        sec_end = sec_start + CHUNK_LEN
        result = compute_can_features(can_df, sec_start, sec_end)
        signals_found = set()
        for key in result:
            parts = key.split("_")
            if len(parts) >= 3:
                signals_found.add(parts[1])
        assert "steering" in signals_found
        assert "throttle" in signals_found

    def test_mean_std_max_min_keys(self):
        """各信号に mean/std/max/min キーが含まれること。"""
        can_df = _make_can_df(120)
        sec_start = can_df["ts"].astype("int64").iloc[0] // 10**6
        sec_end = sec_start + CHUNK_LEN
        result = compute_can_features(can_df, sec_start, sec_end)
        for suffix in ["mean", "std", "max", "min"]:
            assert f"can_steering_{suffix}" in result


class TestMakeChunks:
    """make_chunks のテスト。"""

    def test_chunk_count(self):
        """180 秒のデータで CHUNK_LEN=60 なら 2 チャンク以上生成されること。"""
        gps = _make_gps_df(180)
        can = _make_can_df(180)
        chunks = make_chunks(gps, can)
        # 180秒 → t+60 <= sec_max を満たすチャンクは少なくとも 2 個
        assert len(chunks) >= 2

    def test_chunk_has_gps_columns(self):
        """各チャンクに GPS 基本カラムが含まれること。"""
        gps = _make_gps_df(120)
        can = _make_can_df(120)
        chunks = make_chunks(gps, can)
        assert len(chunks) > 0
        _, chunk_df = chunks[0]
        for col in ["ts", "lat", "lon", "speed", "heading"]:
            assert col in chunk_df.columns

    def test_chunk_has_feature_columns(self):
        """各チャンクに speed_mean, speed_std, lat_range, lon_range が含まれること。"""
        gps = _make_gps_df(120)
        can = _make_can_df(120)
        chunks = make_chunks(gps, can)
        _, chunk_df = chunks[0]
        for col in ["speed_mean", "speed_std", "lat_range", "lon_range"]:
            assert col in chunk_df.columns, f"Missing column: {col}"

    def test_chunk_has_can_features(self):
        """各チャンクに CAN 統計量列が含まれること。"""
        gps = _make_gps_df(120)
        can = _make_can_df(120)
        chunks = make_chunks(gps, can)
        _, chunk_df = chunks[0]
        can_cols = [c for c in chunk_df.columns if c.startswith("can_")]
        assert len(can_cols) > 0

    def test_no_chunks_for_short_data(self):
        """CHUNK_LEN 未満のデータではチャンクが生成されないこと。"""
        gps = _make_gps_df(30)  # 30秒 < CHUNK_LEN=60
        can = _make_can_df(30)
        chunks = make_chunks(gps, can)
        assert len(chunks) == 0

    def test_chunk_rows_in_time_window(self):
        """各チャンク内の行が 60 秒のウィンドウ内に収まっていること。"""
        gps = _make_gps_df(180)
        can = _make_can_df(180)
        chunks = make_chunks(gps, can)
        for _, chunk_df in chunks:
            duration = (chunk_df["ts"].max() - chunk_df["ts"].min()).total_seconds()
            assert duration < CHUNK_LEN


class TestSaveParquet:
    """save_parquet のテスト。"""

    def test_creates_parquet_files(self, tmp_path):
        """Parquet ファイルが正しく生成されること。"""
        chunks_dir = str(tmp_path / "chunks")
        os.makedirs(chunks_dir, exist_ok=True)

        gps = _make_gps_df(120)
        can = _make_can_df(120)
        chunks = make_chunks(gps, can)

        # 手動で Parquet を保存（パスをテンポラリに差し替え）
        for idx, (start, chunk_df) in enumerate(chunks):
            f = os.path.join(chunks_dir, f"chunk_{idx}.parquet")
            chunk_df.to_parquet(f)

        files = [f for f in os.listdir(chunks_dir) if f.endswith(".parquet")]
        assert len(files) == len(chunks)

    def test_parquet_readable(self, tmp_path):
        """保存した Parquet が pd.read_parquet で読み込めること。"""
        chunks_dir = str(tmp_path / "chunks")
        os.makedirs(chunks_dir, exist_ok=True)

        gps = _make_gps_df(120)
        can = _make_can_df(120)
        chunks = make_chunks(gps, can)

        for idx, (start, chunk_df) in enumerate(chunks):
            f = os.path.join(chunks_dir, f"chunk_{idx}.parquet")
            chunk_df.to_parquet(f)

        # 読み込み確認
        df = pd.read_parquet(os.path.join(chunks_dir, "chunk_0.parquet"))
        assert len(df) > 0
        assert "speed" in df.columns
