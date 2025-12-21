import duckdb, pandas as pd, numpy as np, os

# チャンクの長さ（秒単位）
CHUNK_LEN = 60
SUBCHUNK = 5

def load_logs():
    """DuckDBからCAN/GPSログを読み込む。"""
    con = duckdb.connect("data/db/vehicle_logs.duckdb")
    can = con.execute("SELECT * FROM can_log ORDER BY ts").df()
    gps = con.execute("SELECT * FROM gps_log ORDER BY ts").df()
    return can, gps

def make_chunks(gps_df):
    """GPSデータを時系列チャンクに分割する。
    
    Args:
        gps_df: GPSデータのDataFrame
        
    Returns:
        list: (開始時刻, チャンクDataFrame) のタプルのリスト
    """
    # 空のDataFrameの場合は空リストを返す
    if len(gps_df) == 0:
        return []
    
    # タイムスタンプを秒単位に変換
    # DuckDBはdatetime64[us]（エポックからのマイクロ秒）を返すので、10**6で割って秒に変換
    gps_df["sec"] = gps_df["ts"].values.astype("int64") // 10**6
    sec_min, sec_max = gps_df["sec"].min(), gps_df["sec"].max()

    chunks = []
    t = sec_min
    # 開始時刻から終了時刻まで、CHUNK_LEN秒ごとにチャンクを作成
    while t + CHUNK_LEN <= sec_max:
        # 現在の時間窓に含まれるデータを抽出
        chunk = gps_df[(gps_df["sec"] >= t) & (gps_df["sec"] < t+CHUNK_LEN)]
        if len(chunk) > 0:
            chunks.append((t, chunk))
        t += CHUNK_LEN
    return chunks

def save_parquet(chunks):
    """チャンクをParquet形式で保存する。
    
    Args:
        chunks: (開始時刻, チャンクDataFrame) のタプルのリスト
    """
    os.makedirs("data/chunks", exist_ok=True)
    for idx, (start, chunk_df) in enumerate(chunks):
        f = f"data/chunks/chunk_{idx}.parquet"
        chunk_df.to_parquet(f)

if __name__ == "__main__":
    can, gps = load_logs()
    chunks = make_chunks(gps)
    save_parquet(chunks)
    print(f"{len(chunks)} chunks created.")
