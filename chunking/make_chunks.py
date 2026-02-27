"""
Chunking: DuckDB から CAN/GPS ログを読み込み、
60秒ごとの時間窓でチャンク化して Parquet に保存する。
"""
import duckdb, pandas as pd, numpy as np, os

CHUNK_LEN = 60  # seconds


def load_logs():
    con = duckdb.connect("data/db/vehicle_logs.duckdb", read_only=True)
    can = con.execute("SELECT * FROM can_log ORDER BY ts").df()
    gps = con.execute("SELECT * FROM gps_log ORDER BY ts").df()
    con.close()
    return can, gps


def compute_can_features(can_df: pd.DataFrame, sec_start: int, sec_end: int) -> dict:
    """CAN 信号の統計量（平均・標準偏差・最大・最小）を計算する。"""
    can_df["sec"] = can_df["ts"].astype("int64") // 10**6
    window = can_df[(can_df["sec"] >= sec_start) & (can_df["sec"] < sec_end)]

    features = {}
    for signal in window["signal"].unique():
        vals = window[window["signal"] == signal]["value"]
        features[f"can_{signal}_mean"] = vals.mean()
        features[f"can_{signal}_std"] = vals.std()
        features[f"can_{signal}_max"] = vals.max()
        features[f"can_{signal}_min"] = vals.min()
    return features


def make_chunks(gps_df: pd.DataFrame, can_df: pd.DataFrame):
    gps_df["sec"] = gps_df["ts"].astype("int64") // 10**6
    sec_min, sec_max = gps_df["sec"].min(), gps_df["sec"].max()

    chunks = []
    t = sec_min
    while t + CHUNK_LEN <= sec_max:
        chunk = gps_df[(gps_df["sec"] >= t) & (gps_df["sec"] < t + CHUNK_LEN)].copy()
        if len(chunk) > 0:
            # GPS チャンクの基本特徴量
            chunk["speed_mean"] = chunk["speed"].mean()
            chunk["speed_std"] = chunk["speed"].std()
            chunk["lat_range"] = chunk["lat"].max() - chunk["lat"].min()
            chunk["lon_range"] = chunk["lon"].max() - chunk["lon"].min()

            # CAN 信号の統計量をチャンクに追加
            can_features = compute_can_features(can_df, t, t + CHUNK_LEN)
            for k, v in can_features.items():
                chunk[k] = v

            chunks.append((t, chunk))
        t += CHUNK_LEN
    return chunks


def save_parquet(chunks):
    os.makedirs("data/chunks", exist_ok=True)
    for idx, (start, chunk_df) in enumerate(chunks):
        f = f"data/chunks/chunk_{idx}.parquet"
        chunk_df.to_parquet(f)


if __name__ == "__main__":
    can, gps = load_logs()
    chunks = make_chunks(gps, can)
    save_parquet(chunks)
    print(f"{len(chunks)} chunks created.")
