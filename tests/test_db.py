"""Tests for database initialization and operations."""
import duckdb
import os
import pytest


def test_database_tables_exist():
    """Test that DuckDB tables are created correctly."""
    db_path = "data/db/vehicle_logs.duckdb"
    
    # Ensure database exists
    assert os.path.exists(db_path), f"Database file not found at {db_path}"
    
    # Connect and check tables
    con = duckdb.connect(db_path, read_only=True)
    
    # Check can_log table
    result = con.execute(
        "SELECT * FROM information_schema.tables WHERE table_name = 'can_log'"
    ).fetchall()
    assert len(result) == 1, "can_log table should exist"
    
    # Check gps_log table
    result = con.execute(
        "SELECT * FROM information_schema.tables WHERE table_name = 'gps_log'"
    ).fetchall()
    assert len(result) == 1, "gps_log table should exist"
    
    con.close()


def test_database_schema():
    """Test that database schema is correct."""
    db_path = "data/db/vehicle_logs.duckdb"
    con = duckdb.connect(db_path, read_only=True)
    
    # Check can_log schema
    columns = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = 'can_log' ORDER BY ordinal_position"
    ).fetchall()
    
    expected_can_columns = [
        ('ts', 'TIMESTAMP'),
        ('vehicle_id', 'VARCHAR'),
        ('signal', 'VARCHAR'),
        ('value', 'DOUBLE')
    ]
    assert columns == expected_can_columns, f"can_log schema mismatch: {columns}"
    
    # Check gps_log schema
    columns = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name = 'gps_log' ORDER BY ordinal_position"
    ).fetchall()
    
    expected_gps_columns = [
        ('ts', 'TIMESTAMP'),
        ('vehicle_id', 'VARCHAR'),
        ('lat', 'DOUBLE'),
        ('lon', 'DOUBLE'),
        ('speed', 'DOUBLE'),
        ('heading', 'DOUBLE')
    ]
    assert columns == expected_gps_columns, f"gps_log schema mismatch: {columns}"
    
    con.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
