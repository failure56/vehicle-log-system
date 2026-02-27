# Vehicle Log System — Copilot Instructions

## プロジェクト概要

車載データ（CAN / GPS / Telemetry）の前処理・チャンク化・ベクトル化・検索を行うモジュール型データパイプライン。

## アーキテクチャ

```
Raw CSV → [Ingestion] → DuckDB tables → [Chunking] → Parquet chunks → [Embedding] → DuckDB vectors → [FastAPI]
```

### コンポーネント

| サービス | ディレクトリ | 説明 |
|---|---|---|
| ingestion | `ingestion/` | CSV → DuckDB テーブルへのデータロード |
| chunker | `chunking/` | 60秒時間窓でのチャンク分割 + 特徴量抽出 |
| embedding | `embedding/` | sentence-transformers でチャンクをベクトル化 |
| db | `db/` | DuckDB スキーマ初期化 |
| api | `api/` | FastAPI サーバー（検索・クエリ） |

## 技術スタック

- **言語**: Python 3.11
- **データベース**: DuckDB（ファイルベース `data/db/vehicle_logs.duckdb`）
- **データ形式**: Parquet（チャンク）、CSV（入力）
- **API**: FastAPI + Uvicorn
- **Embedding**: sentence-transformers `all-MiniLM-L6-v2`（384次元）
- **コンテナ**: Docker + Docker Compose
- **CI/CD**: GitHub Actions

## DuckDB テーブル

- `can_log`: ts, vehicle_id, signal, value
- `gps_log`: ts, vehicle_id, lat, lon, speed, heading
- `embeddings`: chunk_id, chunk_file, text_repr, vector FLOAT[384], speed_mean, speed_std, lat_range, lon_range, num_rows, start_ts, end_ts

## 命名規則

- Python ファイル: snake_case（例: `make_chunks.py`）
- Docker サービス名: kebab-case または単語（例: `chunker`, `api`）
- チャンクファイル: `chunk_{index}.parquet`
- ブランチ名: `feature/`, `bugfix/`, `hotfix/` プレフィックス

## コーディングルール

- 型ヒントを適度に使用
- docstring は日本語可（コード内コメントは日英混在OK）
- DuckDB 接続は `read_only=True` で開き、書き込みが必要な場合のみ通常接続
- Parquet I/O には `pandas.to_parquet()` / `pd.read_parquet()` を使用
- FastAPI エンドポイントでは適切な HTTP ステータスコードを返す
- SQL は文字列結合ではなくパラメータバインド（`?`）を使用する
- DuckDB 接続は関数内で適切にクローズする（`with` 文 or `try/finally`）

## レビュー時の追加観点

コードレビューを依頼された場合は、以下も確認すること:

- SQL インジェクションのリスクがないか（パラメータバインド使用）
- 深刻度を 🔴 Critical / 🟡 Warning / 🔵 Info で表示
- DuckDB 接続の `read_only` 設定が適切か
- Docker ボリュームマウントのパス整合性
