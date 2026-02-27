"""
Ingestion: サンプル CSV を DuckDB にロードする。

data/sample/can.csv  → can_log テーブル
data/sample/gps.csv  → gps_log テーブル
"""
import duckdb
import pandas as pd
import os
import sys

DB_PATH = "data/db/vehicle_logs.duckdb"
SAMPLE_DIR = "data/sample"

VEHICLE_ID = "sample_vehicle_01"


def load_can_csv(con: duckdb.DuckDBPyConnection, path: str) -> int:
    """
    Udacity self-driving CSV をパースして can_log テーブルに挿入する。
    CSV の形式: timestamp, CAN_ID, signal_name, value (想定)
    実際のデータ構造に合わせてパースロジックを調整。
    """
    if not os.path.exists(path):
        print(f"[SKIP] CAN CSV not found: {path}")
        return 0

    df = pd.read_csv(path, nrows=5)
    print(f"[INFO] CAN CSV columns: {list(df.columns)}")

    df = pd.read_csv(path)

    # Udacity CH2_final.csv は以下のような列を持つ:
    #   center, left, right, steering, throttle, brake, speed
    # これを CAN 信号として扱う
    records = []
    for col in ["steering", "throttle", "brake", "speed"]:
        if col in df.columns:
            for idx, row in df.iterrows():
                records.append({
                    "ts": pd.Timestamp("2024-01-01") + pd.Timedelta(seconds=idx * 0.1),
                    "vehicle_id": VEHICLE_ID,
                    "signal": col,
                    "value": float(row[col]) if pd.notna(row[col]) else 0.0,
                })

    if not records:
        print("[WARN] No CAN signals extracted.")
        return 0

    can_df = pd.DataFrame(records)
    con.execute("DELETE FROM can_log")
    con.register("can_df", can_df)
    con.execute("INSERT INTO can_log SELECT ts, vehicle_id, signal, value FROM can_df")
    con.unregister("can_df")
    count = con.execute("SELECT COUNT(*) FROM can_log").fetchone()[0]
    print(f"[OK] can_log: {count} rows inserted")
    return count


def load_gps_csv(con: duckdb.DuckDBPyConnection, path: str) -> int:
    """
    GPS CSV をパースして gps_log テーブルに挿入する。
    NMEA サンプルデータの形式に合わせてパース。
    """
    if not os.path.exists(path):
        print(f"[SKIP] GPS CSV not found: {path}")
        return 0

    df = pd.read_csv(path, nrows=5)
    print(f"[INFO] GPS CSV columns: {list(df.columns)}")

    df = pd.read_csv(path)

    # NMEA CSV の列構造に合わせてマッピング
    # 列名が想定と異なる場合はフォールバック処理
    records = []
    for idx, row in df.iterrows():
        rec = {
            "vehicle_id": VEHICLE_ID,
            "ts": pd.Timestamp("2024-01-01") + pd.Timedelta(seconds=idx),
        }
        # lat/lon の取得（複数の列名パターンに対応）
        for lat_col in ["lat", "latitude", "Latitude"]:
            if lat_col in df.columns:
                rec["lat"] = float(row[lat_col]) if pd.notna(row[lat_col]) else 0.0
                break
        else:
            rec["lat"] = 0.0

        for lon_col in ["lon", "longitude", "Longitude"]:
            if lon_col in df.columns:
                rec["lon"] = float(row[lon_col]) if pd.notna(row[lon_col]) else 0.0
                break
        else:
            rec["lon"] = 0.0

        for spd_col in ["speed", "Speed", "spd"]:
            if spd_col in df.columns:
                rec["speed"] = float(row[spd_col]) if pd.notna(row[spd_col]) else 0.0
                break
        else:
            rec["speed"] = 0.0

        for hdg_col in ["heading", "Heading", "course", "Course"]:
            if hdg_col in df.columns:
                rec["heading"] = float(row[hdg_col]) if pd.notna(row[hdg_col]) else 0.0
                break
        else:
            rec["heading"] = 0.0

        records.append(rec)

    if not records:
        print("[WARN] No GPS records extracted.")
        return 0

    gps_df = pd.DataFrame(records)
    con.execute("DELETE FROM gps_log")
    con.register("gps_df", gps_df)
    con.execute("INSERT INTO gps_log SELECT ts, vehicle_id, lat, lon, speed, heading FROM gps_df")
    con.unregister("gps_df")
    count = con.execute("SELECT COUNT(*) FROM gps_log").fetchone()[0]
    print(f"[OK] gps_log: {count} rows inserted")
    return count


def main():
    # DB ディレクトリの確保
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # サンプルデータの存在確認
    can_path = os.path.join(SAMPLE_DIR, "can.csv")
    gps_path = os.path.join(SAMPLE_DIR, "gps.csv")

    if not os.path.exists(can_path) and not os.path.exists(gps_path):
        print(f"[ERROR] No sample data found in {SAMPLE_DIR}/")
        print("Run: docker compose run chunker python download_sample_data.py")
        sys.exit(1)

    con = duckdb.connect(DB_PATH)

    # スキーマを確保（db/run_duckdb.py と同じ定義）
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

    total = 0
    total += load_can_csv(con, can_path)
    total += load_gps_csv(con, gps_path)

    con.close()
    print(f"\n=== Ingestion complete: {total} total rows loaded ===")


if __name__ == "__main__":
    main()
