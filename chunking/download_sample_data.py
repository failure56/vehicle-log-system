"""
サンプルデータ生成スクリプト。
外部ダウンロードに依存せず、ローカルで模擬的な CAN / GPS データを生成する。
"""
import os
import csv
import math
import random

DATA_DIR = "/app/data/sample"

random.seed(42)


def generate_can_csv(path: str, num_rows: int = 5000):
    """模擬 CAN データ（steering, throttle, brake, speed）を生成。"""
    print(f"Generating CAN sample data -> {path} ({num_rows} rows)")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["center", "left", "right", "steering", "throttle", "brake", "speed"])
        speed = 0.0
        for i in range(num_rows):
            steering = math.sin(i * 0.01) * 25.0 + random.gauss(0, 2)
            throttle = max(0, 0.3 + 0.2 * math.sin(i * 0.005) + random.gauss(0, 0.05))
            brake = max(0, random.gauss(0, 0.1)) if random.random() < 0.1 else 0.0
            speed = max(0, speed + (throttle - brake) * 0.5 + random.gauss(0, 0.3))
            speed = min(speed, 120.0)
            writer.writerow([
                f"img_{i:06d}.jpg", f"img_{i:06d}_l.jpg", f"img_{i:06d}_r.jpg",
                f"{steering:.4f}", f"{throttle:.4f}", f"{brake:.4f}", f"{speed:.2f}"
            ])
    print(f"  -> {num_rows} rows written")


def generate_gps_csv(path: str, num_rows: int = 600):
    """模擬 GPS データ（lat, lon, speed, heading）を生成。約10分間のドライブを模擬。"""
    print(f"Generating GPS sample data -> {path} ({num_rows} rows)")
    lat, lon = 35.6812, 139.7671  # 東京駅付近
    heading = 0.0
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["latitude", "longitude", "speed", "heading"])
        for i in range(num_rows):
            speed = 30.0 + 20.0 * math.sin(i * 0.02) + random.gauss(0, 3)
            speed = max(0, speed)
            heading += random.gauss(0, 5)
            heading = heading % 360
            # 移動量（大まかな概算）
            dlat = math.cos(math.radians(heading)) * speed * 0.001 / 111000
            dlon = math.sin(math.radians(heading)) * speed * 0.001 / (111000 * math.cos(math.radians(lat)))
            lat += dlat
            lon += dlon
            writer.writerow([f"{lat:.6f}", f"{lon:.6f}", f"{speed:.2f}", f"{heading:.1f}"])
    print(f"  -> {num_rows} rows written")


def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory {path}")


def main():
    ensure_directory(DATA_DIR)

    can_path = os.path.join(DATA_DIR, "can.csv")
    gps_path = os.path.join(DATA_DIR, "gps.csv")

    if not os.path.exists(can_path):
        generate_can_csv(can_path)
    else:
        print(f"{can_path} already exists, skipping.")

    if not os.path.exists(gps_path):
        generate_gps_csv(gps_path)
    else:
        print(f"{gps_path} already exists, skipping.")

    print("Sample data generation complete.")


if __name__ == "__main__":
    main()
