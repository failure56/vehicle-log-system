"""
Embedding: チャンク Parquet を読み込み、特徴量テキストを生成し、
sentence-transformers でベクトル化して DuckDB に保存する。

使用モデル: all-MiniLM-L6-v2 (384次元, ローカル推論)
"""
import duckdb
import pandas as pd
import numpy as np
import os
import glob

DB_PATH = "data/db/vehicle_logs.duckdb"
CHUNKS_DIR = "data/chunks"
MODEL_NAME = "all-MiniLM-L6-v2"


def init_embedding_table(con: duckdb.DuckDBPyConnection):
    """embedding テーブルを作成する（存在しない場合のみ）。"""
    con.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            chunk_id INTEGER,
            chunk_file VARCHAR,
            text_repr VARCHAR,
            vector FLOAT[384],
            speed_mean DOUBLE,
            speed_std DOUBLE,
            lat_range DOUBLE,
            lon_range DOUBLE,
            num_rows INTEGER,
            start_ts TIMESTAMP,
            end_ts TIMESTAMP
        )
    """)


def chunk_to_text(df: pd.DataFrame, chunk_file: str) -> str:
    """チャンクの特徴量をテキスト表現に変換する（embedding 入力用）。"""
    parts = [f"Vehicle driving segment from file {chunk_file}."]

    if "speed" in df.columns:
        parts.append(f"Speed: mean={df['speed'].mean():.2f}, std={df['speed'].std():.2f}, "
                      f"max={df['speed'].max():.2f}, min={df['speed'].min():.2f}.")

    if "lat" in df.columns and "lon" in df.columns:
        parts.append(f"GPS range: lat=[{df['lat'].min():.6f}, {df['lat'].max():.6f}], "
                      f"lon=[{df['lon'].min():.6f}, {df['lon'].max():.6f}].")

    # CAN 信号の特徴量があれば追加
    can_cols = [c for c in df.columns if c.startswith("can_")]
    if can_cols:
        # ユニークな信号ごとにまとめる
        signals = set(c.split("_")[1] for c in can_cols if len(c.split("_")) >= 3)
        for sig in signals:
            mean_col = f"can_{sig}_mean"
            if mean_col in df.columns:
                parts.append(f"CAN {sig}: mean={df[mean_col].iloc[0]:.2f}.")

    if "heading" in df.columns:
        parts.append(f"Heading: mean={df['heading'].mean():.1f}.")

    duration_rows = len(df)
    parts.append(f"Segment contains {duration_rows} data points.")

    return " ".join(parts)


def main():
    # チャンクファイルの一覧を取得
    chunk_files = sorted(glob.glob(os.path.join(CHUNKS_DIR, "chunk_*.parquet")))
    if not chunk_files:
        print(f"[ERROR] No chunk files found in {CHUNKS_DIR}/")
        print("Run: docker compose run chunker python make_chunks.py")
        return

    print(f"[INFO] Found {len(chunk_files)} chunk files")

    # sentence-transformers モデルの読み込み
    print(f"[INFO] Loading model: {MODEL_NAME}")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(MODEL_NAME)

    # テキスト表現を生成
    texts = []
    metadata = []
    for chunk_file in chunk_files:
        fname = os.path.basename(chunk_file)
        chunk_id = int(fname.replace("chunk_", "").replace(".parquet", ""))
        df = pd.read_parquet(chunk_file)

        text = chunk_to_text(df, fname)
        texts.append(text)

        meta = {
            "chunk_id": chunk_id,
            "chunk_file": fname,
            "text_repr": text,
            "speed_mean": float(df["speed"].mean()) if "speed" in df.columns else 0.0,
            "speed_std": float(df["speed"].std()) if "speed" in df.columns else 0.0,
            "lat_range": float(df["lat"].max() - df["lat"].min()) if "lat" in df.columns else 0.0,
            "lon_range": float(df["lon"].max() - df["lon"].min()) if "lon" in df.columns else 0.0,
            "num_rows": len(df),
            "start_ts": df["ts"].min() if "ts" in df.columns else None,
            "end_ts": df["ts"].max() if "ts" in df.columns else None,
        }
        metadata.append(meta)

    # バッチでベクトル化
    print(f"[INFO] Encoding {len(texts)} chunks...")
    vectors = model.encode(texts, show_progress_bar=True, batch_size=32)

    # DuckDB に保存
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = duckdb.connect(DB_PATH)
    init_embedding_table(con)

    # 既存データをクリアして再挿入
    con.execute("DELETE FROM embeddings")

    for i, (meta, vec) in enumerate(zip(metadata, vectors)):
        con.execute("""
            INSERT INTO embeddings
            (chunk_id, chunk_file, text_repr, vector, speed_mean, speed_std,
             lat_range, lon_range, num_rows, start_ts, end_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            meta["chunk_id"],
            meta["chunk_file"],
            meta["text_repr"],
            vec.tolist(),
            meta["speed_mean"],
            meta["speed_std"],
            meta["lat_range"],
            meta["lon_range"],
            meta["num_rows"],
            meta["start_ts"],
            meta["end_ts"],
        ])

    count = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    con.close()
    print(f"\n=== Embedding complete: {count} vectors stored in DuckDB ===")


if __name__ == "__main__":
    main()
