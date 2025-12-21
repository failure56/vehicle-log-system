"""DuckDB データベースの初期化スクリプト。

車両ログシステムで使用するDuckDBデータベースを初期化し、
CANログとGPSログ用のテーブルを作成します。
"""
import duckdb, os

# データベース格納ディレクトリを作成
os.makedirs("data/db", exist_ok=True)

# DuckDBに接続（ファイルが存在しない場合は新規作成）
con = duckdb.connect("data/db/vehicle_logs.duckdb")

# CANログテーブルを作成
# ts: タイムスタンプ
# vehicle_id: 車両ID
# signal: 信号名（例: engine_rpm, vehicle_speed）
# value: 信号の値
con.execute("""
CREATE TABLE IF NOT EXISTS can_log (
    ts TIMESTAMP,
    vehicle_id VARCHAR,
    signal VARCHAR,
    value DOUBLE
);
""")

# GPSログテーブルを作成
# ts: タイムスタンプ
# vehicle_id: 車両ID
# lat: 緯度
# lon: 経度
# speed: 速度
# heading: 進行方向（度）
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

print("DuckDB initialized.")
