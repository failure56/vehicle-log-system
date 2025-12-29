# Vehicle Log System  
車載データ（CAN / GPS / Telemetry）の前処理・チャンク化・特徴量抽出・埋め込み・検索を行うためのモジュール型データパイプラインです。

---

## 🚗 システム概要

Vehicle Log System は以下の処理を段階的に行います：

1. **Ingestion**  
   生データ（CSV / テレメトリ / CAN / GPS）を統合し、  
   単一の時系列データ `merged.parquet` を生成。

2. **Chunking**  
   例：60秒ごとに時間窓で分割し、  
   チャンク単位の特徴量を抽出。

3. **Embedding**  
   各チャンクをベクトル化して保存（類似検索などに利用）。

4. **DuckDB + FastAPI**  
   生成データを DuckDB に保存し、  
   API から検索やクエリを実行可能。

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
├── db/                     # DuckDB サーバー
│   ├── Dockerfile
│   └── run_duckdb.py
├── doc/                    # ドキュメント
│   ├── README.md
│   ├── data-flow.md
│   └── architecture.md
├── embedding/              # ベクトル化処理（準備中）
├── ingestion/              # 前処理（準備中）
├── prepared/               # 統合された時系列データ
├── data/
│   ├── chunks/             # チャンク済みデータ
│   ├── db/                 # DuckDB ファイル
│   │   └── vehicle_logs.duckdb
│   └── sample/             # サンプルデータ
├── docker-compose.yml
└── README.md
```


---

## 📖 ドキュメント

詳細なシステム設計とデータフローについては、以下のドキュメントを参照してください：

- **[データフロー図](./doc/data-flow.md)** - システム全体の処理フローと各ステージの詳細
- **[システムアーキテクチャ](./doc/architecture.md)** - 技術スタック、コンポーネント設計、セキュリティ考慮事項
- **[ドキュメント目次](./doc/README.md)** - 全ドキュメントの一覧

---

## 🐳 クイックスタート

### 前提条件
- Docker および Docker Compose がインストールされていること
- サンプルデータが `data/sample/` に配置されていること

### 実行手順

**1. サンプルデータのダウンロード（初回のみ）**
```bash
docker compose run chunking python download_sample_data.py
```

**2. チャンク化処理**
```bash
docker compose run chunking python make_chunks.py
```

**3. 全サービスの起動**
```bash
docker compose up
```

**4. API へのアクセス**
- **API Server**: http://localhost:8000
- **DuckDB**: ポート 5432 で接続可能

---

## 🔧 各処理の詳細

### 1. Ingestion（前処理）
- **ステータス**: 準備中（`ingestion/`）
- **目的**: 生データ（CSV / テレメトリ）を統合
- **出力**: `prepared/merged.parquet`

### 2. Chunking（チャンク化）
- **実装**: `chunking/make_chunks.py`
- **処理**: 時系列データを 60秒ごとに分割
- **出力**: `data/chunks/` にチャンクデータを保存

### 3. Embedding（埋め込み）
- **ステータス**: 準備中（`embedding/`）
- **目的**: 各チャンクをベクトル化
- **用途**: 類似検索、シーン分類など

### 4. データベース & API
- **DB**: DuckDB（`data/db/vehicle_logs.duckdb`）
- **API**: FastAPI サーバー（`api/main.py`）

---

## 🛠️ トラブルシューティング

| 問題 | 解決方法 |
|------|--------|
| サンプルデータが見つからない | `docker compose run chunking python download_sample_data.py` を実行 |
| DuckDB に接続できない | `docker compose logs db` でログを確認 |
| API が起動しない | `docker compose logs api` でエラーを確認 |


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