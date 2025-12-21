"""Tests for database initialization and operations."""
import duckdb
import os
import pytest


def test_database_tables_exist():
    """DuckDBのテーブルが正しく作成されているかテストする。"""
    db_path = "data/db/vehicle_logs.duckdb"
    
    # データベースファイルの存在確認
    assert os.path.exists(db_path), f"Database file not found at {db_path}"
    
    # データベースに接続してテーブルを確認
    # コンテキストマネージャーを使用して確実にコネクションをクローズする
    with duckdb.connect(db_path, read_only=True) as con:
        # can_logテーブルの存在確認
        result = con.execute(
            "SELECT * FROM information_schema.tables WHERE table_name = 'can_log'"
        ).fetchall()
        assert len(result) == 1, "can_log table should exist"
        
        # gps_logテーブルの存在確認
        result = con.execute(
            "SELECT * FROM information_schema.tables WHERE table_name = 'gps_log'"
        ).fetchall()
        assert len(result) == 1, "gps_log table should exist"


def test_database_schema():
    """データベーススキーマが正しいかテストする。"""
    db_path = "data/db/vehicle_logs.duckdb"
    
    # コンテキストマネージャーを使用して確実にコネクションをクローズする
    with duckdb.connect(db_path, read_only=True) as con:
        # can_logテーブルのスキーマ確認
        columns = con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'can_log' ORDER BY ordinal_position"
        ).fetchall()
        
        # 期待されるcan_logテーブルのカラム構成
        expected_can_columns = [
            ('ts', 'TIMESTAMP'),
            ('vehicle_id', 'VARCHAR'),
            ('signal', 'VARCHAR'),
            ('value', 'DOUBLE')
        ]
        assert columns == expected_can_columns, f"can_log schema mismatch: {columns}"
        
        # gps_logテーブルのスキーマ確認
        columns = con.execute(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = 'gps_log' ORDER BY ordinal_position"
        ).fetchall()
        
        # 期待されるgps_logテーブルのカラム構成
        expected_gps_columns = [
            ('ts', 'TIMESTAMP'),
            ('vehicle_id', 'VARCHAR'),
            ('lat', 'DOUBLE'),
            ('lon', 'DOUBLE'),
            ('speed', 'DOUBLE'),
            ('heading', 'DOUBLE')
        ]
        assert columns == expected_gps_columns, f"gps_log schema mismatch: {columns}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
