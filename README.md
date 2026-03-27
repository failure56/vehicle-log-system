# Vehicle Log System  

![Tests](https://github.com/failure56/vehicle-log-system/actions/workflows/test.yml/badge.svg)
![E2E](https://github.com/failure56/vehicle-log-system/actions/workflows/e2e-pipeline.yml/badge.svg)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/failure56/COVERAGE_GIST_ID/raw/vehicle-log-system-coverage.json)

車載データ（CAN / GPS / Telemetry）の前処理・チャンク化・特徴量抽出・埋め込み・検索を行うためのモジュール型データパイプラインです。

---

## 🚗 システム概要

Vehicle Log System は以下の処理を段階的に行います：

1. **Ingestion**  
   生データ（CSV / テレメトリ / CAN / GPS）を DuckDB にロード。



出出出て

2. **Chunking**  
   60秒ごとに時間窓で分割し、  
   GPS + CAN のチャンク単位の特徴量を抽出。

3. **Embedding**  
   各チャンクを sentence-transformers (`all-MiniLM-L6-v2`) でベクトル化して DuckDB に保存。

4. **DuckDB + FastAPI**  
   DuckDB に保存されたデータを FastAPI からクエリ・ベクトル類似検索。

---

## 📁 ディレクトリ構成

```
vehicle-log-system/
├── api/                    # FastAPI サーバー
│   ├── Dockerfile
│   └── main.py
├── chunking/               # チャンク生成処理
│   ├── Dockerfile
│   ├── make_chunks.py
│   └── download_sample_data.py
├── db/                     # DuckDB スキーマ初期化
│   ├── Dockerfile
│   └── run_duckdb.py
├── embedding/              # ベクトル化処理
│   ├── Dockerfile
│   └── embed_chunks.py
├── ingestion/              # CSV → DuckDB ロード
│   ├── Dockerfile
│   └── prepare_data.py
├── prepared/               # (予約: 統合時系列データ)
├── data/
│   ├── chunks/             # チャンク済み Parquet
│   ├── db/                 # DuckDB ファイル
│   │   └── vehicle_logs.duckdb
│   └── sample/             # サンプル CSV
├── scripts/
│   └── rewrite_issue.py    # Issue リライト AI スクリプト
├── .github/
│   ├── copilot-instructions.md
│   ├── copilot/agents/     # Copilot カスタムエージェント
│   │   ├── pipeline.md
│   │   ├── data-engineer.md
│   │   ├── vehicle-api.md
│   │   └── issue-ops.md
│   ├── prompts/
│   └── workflows/
├── docker-compose.yml
└── README.md
```

---

## 🐳 クイックスタート

### 前提条件
- Docker および Docker Compose がインストールされていること

### 実行手順

**1. DB スキーマ初期化**
```bash
docker compose run db
```

**2. サンプルデータのダウンロード（初回のみ）**
```bash
docker compose run chunker python download_sample_data.py
```

**3. CSV を DuckDB にロード**
```bash
docker compose run ingestion python prepare_data.py
```

**4. チャンク化処理**
```bash
docker compose run chunker python make_chunks.py
```

**5. ベクトル化（Embedding）**
```bash
docker compose run embedding python embed_chunks.py
```

**6. API サーバーの起動**
```bash
docker compose up api
```

**7. API へのアクセス**
- **API Server**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **チャンク一覧**: http://localhost:8000/chunks
- **類似検索**: http://localhost:8000/search?q=acceleration&top_k=5

---

## 🔌 API エンドポイント

| Method | Path | 説明 |
|---|---|---|
| GET | `/health` | ヘルスチェック |
| GET | `/chunks` | チャンクファイル一覧 |
| GET | `/chunk/{cid}` | 特定チャンクの先頭50行 |
| GET | `/search?q=...&top_k=5` | ベクトル類似検索 |
| GET | `/logs?table=gps_log&vehicle_id=...` | CAN/GPS ログ直接クエリ |

---

## 🔧 各処理の詳細

### 1. Ingestion（前処理）
- **実装**: `ingestion/prepare_data.py`
- **処理**: `data/sample/` 内の CSV を読み込み、DuckDB の `can_log` / `gps_log` テーブルにロード
- **出力**: DuckDB テーブル

### 2. Chunking（チャンク化）
- **実装**: `chunking/make_chunks.py`
- **処理**: GPS + CAN データを 60秒ウィンドウで分割、特徴量（速度統計・CAN信号統計等）を付与
- **出力**: `data/chunks/chunk_*.parquet`

### 3. Embedding（埋め込み）
- **実装**: `embedding/embed_chunks.py`
- **モデル**: sentence-transformers `all-MiniLM-L6-v2`（384次元）
- **処理**: チャンクの特徴量をテキスト表現に変換 → ベクトル化 → DuckDB `embeddings` テーブルに保存

### 4. データベース & API
- **DB**: DuckDB（`data/db/vehicle_logs.duckdb`）— ファイルベース、全サービスがボリュームマウント経由でアクセス
- **API**: FastAPI サーバー（`api/main.py`）— チャンク確認・ベクトル検索・ログクエリ

---

## 🛠️ トラブルシューティング

| 問題 | 解決方法 |
|------|--------|
| サンプルデータが見つからない | `docker compose run chunker python download_sample_data.py` を実行 |
| DuckDB にテーブルがない | `docker compose run db` でスキーマを初期化 |
| チャンクが空 | `docker compose run ingestion python prepare_data.py` でデータをロード後、チャンク化 |
| API が起動しない | `docker compose logs api` でエラーを確認 |
| 検索で 503 エラー | `docker compose run embedding python embed_chunks.py` でベクトルを生成 |


## 📊 データについて

現在は **Kaggle の「Vehicle Telemetry Dataset」** をサンプルデータとして使用。

### 対応予定のデータタイプ
- **CAN bus**: ID / DLC / payload decoding
- **GPS**: 補間 / smoothing
- **OBD-II PID**: ログデータ
- **IMU / GNSS**: フュージョン処理

---

## 🗺️ ロードマップ（今後の予定）

- [ ] CAN 生ログ ingestion の追加
- [ ] 高解像度 GPS 補間（Kalman Filter）
- [ ] 周波数成分特徴量（FFT）
- [ ] 走行シーン分類モデルへの応用
- [ ] Web UI ダッシュボード

---

## 📝 ライセンス

[ライセンス情報を記載]
