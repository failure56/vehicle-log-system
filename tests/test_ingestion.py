"""
ingestion/prepare_data.py のテスト。
CAN/GPS CSV の読み込みと DuckDB へのロード処理を検証する。
"""
import duckdb
import pandas as pd

from ingestion.prepare_data import load_can_csv, load_gps_csv


class TestLoadCanCsv:
    """CAN CSV ロードのテスト。"""

    def test_loads_can_data(self, db_con, sample_can_csv):
        """CAN CSV を正常にロードできること。"""
        count = load_can_csv(db_con, sample_can_csv)
        assert count > 0

    def test_inserts_4_signals(self, db_con, sample_can_csv):
        """steering, throttle, brake, speed の 4 信号がロードされること。"""
        load_can_csv(db_con, sample_can_csv)
        signals = db_con.execute("SELECT DISTINCT signal FROM can_log ORDER BY signal").fetchdf()
        signal_list = sorted(list(signals["signal"]))
        assert signal_list == ["brake", "speed", "steering", "throttle"]

    def test_correct_row_count(self, db_con, sample_can_csv):
        """20 行の CSV × 4 信号 = 80 行がロードされること。"""
        count = load_can_csv(db_con, sample_can_csv)
        assert count == 80  # 20 rows × 4 signals

    def test_vehicle_id_set(self, db_con, sample_can_csv):
        """vehicle_id が正しくセットされること。"""
        load_can_csv(db_con, sample_can_csv)
        ids = db_con.execute("SELECT DISTINCT vehicle_id FROM can_log").fetchdf()
        assert len(ids) == 1
        assert ids["vehicle_id"].iloc[0] == "sample_vehicle_01"

    def test_timestamp_sequential(self, db_con, sample_can_csv):
        """タイムスタンプが昇順であること。"""
        load_can_csv(db_con, sample_can_csv)
        ts_list = db_con.execute(
            "SELECT DISTINCT ts FROM can_log ORDER BY ts"
        ).fetchdf()["ts"].tolist()
        for i in range(1, len(ts_list)):
            assert ts_list[i] >= ts_list[i - 1]

    def test_skip_missing_file(self, db_con):
        """存在しないファイルの場合はスキップして 0 を返すこと。"""
        count = load_can_csv(db_con, "/nonexistent/can.csv")
        assert count == 0

    def test_delete_before_insert(self, db_con, sample_can_csv):
        """2 回ロードしてもデータが重複しないこと（DELETE → INSERT）。"""
        load_can_csv(db_con, sample_can_csv)
        count1 = db_con.execute("SELECT COUNT(*) FROM can_log").fetchone()[0]
        load_can_csv(db_con, sample_can_csv)
        count2 = db_con.execute("SELECT COUNT(*) FROM can_log").fetchone()[0]
        assert count1 == count2


class TestLoadGpsCsv:
    """GPS CSV ロードのテスト。"""

    def test_loads_gps_data(self, db_con, sample_gps_csv):
        """GPS CSV を正常にロードできること。"""
        count = load_gps_csv(db_con, sample_gps_csv)
        assert count > 0

    def test_correct_row_count(self, db_con, sample_gps_csv):
        """20 行の GPS データがロードされること。"""
        count = load_gps_csv(db_con, sample_gps_csv)
        assert count == 20

    def test_lat_lon_range(self, db_con, sample_gps_csv):
        """lat/lon が東京近辺の妥当な範囲内であること。"""
        load_gps_csv(db_con, sample_gps_csv)
        stats = db_con.execute(
            "SELECT MIN(lat), MAX(lat), MIN(lon), MAX(lon) FROM gps_log"
        ).fetchone()
        assert 35.0 < stats[0] < 36.5   # min lat
        assert 35.0 < stats[1] < 36.5   # max lat
        assert 139.0 < stats[2] < 140.5  # min lon
        assert 139.0 < stats[3] < 140.5  # max lon

    def test_speed_non_negative(self, db_con, sample_gps_csv):
        """speed が 0 以上であること。"""
        load_gps_csv(db_con, sample_gps_csv)
        min_speed = db_con.execute("SELECT MIN(speed) FROM gps_log").fetchone()[0]
        assert min_speed >= 0

    def test_skip_missing_file(self, db_con):
        """存在しないファイルの場合はスキップして 0 を返すこと。"""
        count = load_gps_csv(db_con, "/nonexistent/gps.csv")
        assert count == 0

    def test_delete_before_insert(self, db_con, sample_gps_csv):
        """2 回ロードしてもデータが重複しないこと。"""
        load_gps_csv(db_con, sample_gps_csv)
        count1 = db_con.execute("SELECT COUNT(*) FROM gps_log").fetchone()[0]
        load_gps_csv(db_con, sample_gps_csv)
        count2 = db_con.execute("SELECT COUNT(*) FROM gps_log").fetchone()[0]
        assert count1 == count2

    def test_heading_range(self, db_con, sample_gps_csv):
        """heading が 0〜360 の範囲内であること。"""
        load_gps_csv(db_con, sample_gps_csv)
        stats = db_con.execute(
            "SELECT MIN(heading), MAX(heading) FROM gps_log"
        ).fetchone()
        assert stats[0] >= 0
        assert stats[1] <= 360
