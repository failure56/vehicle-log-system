import duckdb, os
os.makedirs("data/db", exist_ok=True)
con = duckdb.connect("data/db/vehicle_logs.duckdb")

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

print("DuckDB initialized.")
