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
- **データ処理**: Pandas, NumPy, PyArrow
- **API**: FastAPI + Uvicorn
- **Embedding**: sentence-transformers `all-MiniLM-L6-v2`（384次元）
- **コンテナ**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **テスト**: pytest + pytest-cov

## プロジェクト構成

```
vehicle-log-system/
├── api/                    # FastAPI サーバー
│   ├── Dockerfile
│   ├── __init__.py
│   └── main.py
├── chunking/               # 時系列チャンク分割
│   ├── Dockerfile
│   ├── __init__.py
│   ├── make_chunks.py
│   └── download_sample_data.py
├── db/                     # DuckDB 初期化
│   ├── Dockerfile
│   ├── __init__.py
│   └── run_duckdb.py
├── embedding/              # ベクトル化
│   ├── Dockerfile
│   ├── __init__.py
│   └── embed_chunks.py
├── ingestion/              # データ取り込み
│   ├── Dockerfile
│   ├── __init__.py
│   └── prepare_data.py
├── tests/                  # pytest テストスイート
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_chunking.py
│   ├── test_db.py
│   ├── test_embedding.py
│   ├── test_ingestion.py
│   └── test_sample_data.py
├── data/                   # データストレージ
│   ├── chunks/             # チャンク済み Parquet
│   ├── db/                 # DuckDB ファイル
│   └── sample/             # サンプル入力データ
├── .github/workflows/      # CI/CD
│   ├── test.yml            # テスト + ビルド検証
│   └── e2e-pipeline.yml    # E2E パイプライン
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

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
- インポート順序: 標準ライブラリ → サードパーティ → ローカルモジュール

## 開発ワークフロー

### ビルド・実行

```bash
# サンプルデータの生成（初回のみ）
docker compose run --rm chunker python download_sample_data.py

# 全パイプライン実行
docker compose run --rm db
docker compose run --rm ingestion
docker compose run --rm chunker
docker compose run --rm embedding
docker compose up -d api
```

### テスト

```bash
# ローカルテスト実行
pip install -e ".[dev]"
pytest -m "not slow"

# Docker ビルド確認
docker compose build
```

- テストアーティファクトは `work/` に出力（`.gitignore` 済み）
- アクセスポイント: http://localhost:8000

## よくある作業

### 新しいデータ処理モジュールの追加

1. 新しいディレクトリを作成（例: `embedding/`）
2. 既存パターンに従って Dockerfile を追加
3. エントリーポイントとなる Python スクリプトを作成
4. `docker-compose.yml` にサービスを追加
5. `README.md` を更新

### API エンドポイントの追加

- `api/main.py` を編集
- FastAPI デコレータパターンに従う（`@app.get()` 等）
- dict/JSON 互換型を返す
- エラーを適切にハンドリング

## レビュー時の追加観点

コードレビューを依頼された場合は、以下も確認すること:

- SQL インジェクションのリスクがないか（パラメータバインド使用）
- 深刻度を 🔴 Critical / 🟡 Warning / 🔵 Info で表示
- DuckDB 接続の `read_only` 設定が適切か
- Docker ボリュームマウントのパス整合性

## セキュリティ

- シークレットや認証情報をリポジトリにコミットしない
- 機密設定には環境変数を使用
- `.gitignore` で `.env`, `*.secret`, `*.key`, `*.token` を除外済み

## 今後の拡張予定

- CAN raw log ingestion
- 高精度 GPS 補間（Kalman Filter）
- FFT ベースの周波数特徴量
- 走行シーン分類
- Web UI ダッシュボード
