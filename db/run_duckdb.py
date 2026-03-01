"""
DuckDB スキーマ初期化スクリプト。
全テーブル（can_log, gps_log, embeddings）を CREATE IF NOT EXISTS で作成する。
"""
import duckdb, os

DB_PATH = "data/db/vehicle_logs.duckdb"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
con = duckdb.connect(DB_PATH)

con.execute("""
CREATE TABLE IF NOT EXISTS can_log (
    ts TIMESTAMP,
    vehicle_id VARCHAR,
    signal VARCHAR,
    value DOUBLE
);
""")

con.execute("""
CREATE TABLE IF NOT EXISTS gps_log (
    ts TIMESTAMP,
    vehicle_id VARCHAR,
    lat DOUBLE,
    lon DOUBLE,
    speed DOUBLE,
    heading DOUBLE
);
""")

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
);
""")

# テーブル一覧と行数を表示
tables = con.execute("SHOW TABLES").fetchall()
for (table_name,) in tables:
    count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"  {table_name}: {count} rows")

con.close()
print("DuckDB initialized.")
