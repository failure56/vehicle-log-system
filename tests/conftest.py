"""
共通テストフィクスチャ。
各テストで使う一時 DuckDB, サンプル CSV, チャンク Parquet を提供する。
"""
import os
import csv
import math
import random
import tempfile
import shutil

import duckdb
import pandas as pd
import numpy as np
import pytest


# ---------------------------------------------------------------------------
# 一時ディレクトリ
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_data_dir(tmp_path):
    """data/ と同じ構造を tmp_path に作る。"""
    (tmp_path / "db").mkdir()
    (tmp_path / "sample").mkdir()
    (tmp_path / "chunks").mkdir()
    return tmp_path


# ---------------------------------------------------------------------------
# DuckDB
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_path(tmp_data_dir):
    return str(tmp_data_dir / "db" / "vehicle_logs.duckdb")


@pytest.fixture()
def db_con(db_path):
    """スキーマ初期化済みの DuckDB 接続を返す。テスト後に閉じる。"""
    con = duckdb.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS can_log (
            ts TIMESTAMP, vehicle_id VARCHAR, signal VARCHAR, value DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS gps_log (
            ts TIMESTAMP, vehicle_id VARCHAR, lat DOUBLE, lon DOUBLE, speed DOUBLE, heading DOUBLE
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            chunk_id INTEGER, chunk_file VARCHAR, text_repr VARCHAR,
            vector FLOAT[384],
            speed_mean DOUBLE, speed_std DOUBLE, lat_range DOUBLE, lon_range DOUBLE,
            num_rows INTEGER, start_ts TIMESTAMP, end_ts TIMESTAMP
        )
    """)
    yield con
    con.close()


# ---------------------------------------------------------------------------
# サンプル CSV
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_can_csv(tmp_data_dir):
    """5 行の CAN CSV を生成して返す。"""
    path = str(tmp_data_dir / "sample" / "can.csv")
    random.seed(0)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["center", "left", "right", "steering", "throttle", "brake", "speed"])
        speed = 10.0
        for i in range(20):
            steering = math.sin(i * 0.5) * 10
            throttle = 0.4
            brake = 0.0
            speed = max(0, speed + (throttle - brake) * 0.5 + random.gauss(0, 0.1))
            w.writerow([
                f"img_{i:06d}.jpg", f"img_{i:06d}_l.jpg", f"img_{i:06d}_r.jpg",
                f"{steering:.4f}", f"{throttle:.4f}", f"{brake:.4f}", f"{speed:.2f}",
            ])
    return path


@pytest.fixture()
def sample_gps_csv(tmp_data_dir):
    """20 行の GPS CSV を生成して返す。"""
    path = str(tmp_data_dir / "sample" / "gps.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["latitude", "longitude", "speed", "heading"])
        lat, lon = 35.6812, 139.7671
        for i in range(20):
            speed = 30.0 + 10.0 * math.sin(i * 0.3)
            heading = (i * 15) % 360
            lat += 0.0001
            lon += 0.0001
            w.writerow([f"{lat:.6f}", f"{lon:.6f}", f"{speed:.2f}", f"{heading:.1f}"])
    return path


# ---------------------------------------------------------------------------
# Parquet チャンク（小さなもの）
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_chunk_dir(tmp_data_dir):
    """2 個の小さなチャンク Parquet を生成して返す（ディレクトリパス）。"""
    chunks_dir = str(tmp_data_dir / "chunks")
    for idx in range(2):
        n = 10
        df = pd.DataFrame({
            "ts": pd.date_range("2024-01-01", periods=n, freq="1s"),
            "vehicle_id": "test_vehicle",
            "lat": np.linspace(35.68, 35.69, n),
            "lon": np.linspace(139.76, 139.77, n),
            "speed": np.random.default_rng(idx).uniform(20, 60, n),
            "heading": np.random.default_rng(idx).uniform(0, 360, n),
            "speed_mean": [40.0] * n,
            "speed_std": [10.0] * n,
            "lat_range": [0.01] * n,
            "lon_range": [0.01] * n,
            "sec": np.arange(n),
        })
        df.to_parquet(os.path.join(chunks_dir, f"chunk_{idx}.parquet"))
    return chunks_dir
