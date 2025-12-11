import os
import urllib.request

DATA_DIR = "/app/data/sample"

FILES = {
    "can.csv": "https://raw.githubusercontent.com/udacity/self-driving-car/master/datasets/CH2_final.csv",
    "gps.csv": "https://raw.githubusercontent.com/kazi11/nmea-sample-data/master/GPSLOG03.csv"
}

def download_file(url, path):
    print(f"Downloading {url}  -> {path}")
    urllib.request.urlretrieve(url, path)

def ensure_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory {path}")

def main():
    ensure_directory(DATA_DIR)

    for filename, url in FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            download_file(url, filepath)
        else:
            print(f"{filepath} already exists, skipping.")

    print("Download complete.")

if __name__ == "__main__":
    main()
