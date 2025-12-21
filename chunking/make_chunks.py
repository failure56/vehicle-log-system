import duckdb, pandas as pd, numpy as np, os

CHUNK_LEN = 60
SUBCHUNK = 5

def load_logs():
    con = duckdb.connect("data/db/vehicle_logs.duckdb")
    can = con.execute("SELECT * FROM can_log ORDER BY ts").df()
    gps = con.execute("SELECT * FROM gps_log ORDER BY ts").df()
    return can, gps

def make_chunks(gps_df):
    # Convert timestamp to seconds (DuckDB returns datetime64[us], so divide by 10**6)
    gps_df["sec"] = gps_df["ts"].values.astype("int64") // 10**6
    sec_min, sec_max = gps_df["sec"].min(), gps_df["sec"].max()

    chunks = []
    t = sec_min
    while t + CHUNK_LEN <= sec_max:
        chunk = gps_df[(gps_df["sec"] >= t) & (gps_df["sec"] < t+CHUNK_LEN)]
        if len(chunk) > 0:
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
    chunks = make_chunks(gps)
    save_parquet(chunks)
    print(f"{len(chunks)} chunks created.")
