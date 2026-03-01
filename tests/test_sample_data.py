"""
chunking/download_sample_data.py のテスト。
合成データ生成の正当性を検証する。
"""
import os
import csv

import pytest

from chunking.download_sample_data import generate_can_csv, generate_gps_csv


class TestGenerateCanCsv:
    """CAN CSV 生成のテスト。"""

    def test_creates_file(self, tmp_path):
        """ファイルが生成されること。"""
        path = str(tmp_path / "can.csv")
        generate_can_csv(path, num_rows=100)
        assert os.path.exists(path)

    def test_correct_row_count(self, tmp_path):
        """指定行数のデータが生成されること。"""
        path = str(tmp_path / "can.csv")
        generate_can_csv(path, num_rows=50)
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 51  # ヘッダ + 50 行

    def test_has_required_columns(self, tmp_path):
        """必須カラムが含まれること。"""
        path = str(tmp_path / "can.csv")
        generate_can_csv(path, num_rows=10)
        with open(path) as f:
            reader = csv.reader(f)
            header = next(reader)
        for col in ["steering", "throttle", "brake", "speed"]:
            assert col in header

    def test_speed_non_negative(self, tmp_path):
        """speed が 0 以上であること。"""
        path = str(tmp_path / "can.csv")
        generate_can_csv(path, num_rows=200)
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert float(row["speed"]) >= 0

    def test_speed_max_120(self, tmp_path):
        """speed が 120 以下であること。"""
        path = str(tmp_path / "can.csv")
        generate_can_csv(path, num_rows=500)
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert float(row["speed"]) <= 120.0

    def test_throttle_non_negative(self, tmp_path):
        """throttle が 0 以上であること。"""
        path = str(tmp_path / "can.csv")
        generate_can_csv(path, num_rows=200)
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert float(row["throttle"]) >= 0

    def test_brake_non_negative(self, tmp_path):
        """brake が 0 以上であること。"""
        path = str(tmp_path / "can.csv")
        generate_can_csv(path, num_rows=200)
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert float(row["brake"]) >= 0


class TestGenerateGpsCsv:
    """GPS CSV 生成のテスト。"""

    def test_creates_file(self, tmp_path):
        """ファイルが生成されること。"""
        path = str(tmp_path / "gps.csv")
        generate_gps_csv(path, num_rows=50)
        assert os.path.exists(path)

    def test_correct_row_count(self, tmp_path):
        """指定行数のデータが生成されること。"""
        path = str(tmp_path / "gps.csv")
        generate_gps_csv(path, num_rows=30)
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 31  # ヘッダ + 30 行

    def test_has_required_columns(self, tmp_path):
        """必須カラムが含まれること。"""
        path = str(tmp_path / "gps.csv")
        generate_gps_csv(path, num_rows=10)
        with open(path) as f:
            reader = csv.reader(f)
            header = next(reader)
        for col in ["latitude", "longitude", "speed", "heading"]:
            assert col in header

    def test_lat_near_tokyo(self, tmp_path):
        """緯度が東京付近（35〜36°）であること。"""
        path = str(tmp_path / "gps.csv")
        generate_gps_csv(path, num_rows=50)
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                lat = float(row["latitude"])
                assert 34.0 < lat < 37.0, f"Unexpected latitude: {lat}"

    def test_speed_non_negative(self, tmp_path):
        """speed が 0 以上であること。"""
        path = str(tmp_path / "gps.csv")
        generate_gps_csv(path, num_rows=100)
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                assert float(row["speed"]) >= 0
