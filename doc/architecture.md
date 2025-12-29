# システムアーキテクチャ (System Architecture)

Vehicle Log System の技術アーキテクチャとコンポーネント設計について説明します。

## アーキテクチャ概要

### システム構成図

```mermaid
graph TB
    subgraph "データレイヤー"
        RawData[生データ<br/>CSV/CAN/GPS]
        Prepared[prepared/<br/>merged.parquet]
        Chunks[data/chunks/<br/>chunk_*.parquet]
        Embeddings[embeddings/<br/>vectors]
        DB[(DuckDB<br/>vehicle_logs.duckdb)]
    end
    
    subgraph "処理レイヤー"
        Ingestion[Ingestion Service<br/>Python 3.11]
        Chunker[Chunker Service<br/>Python 3.11]
        Embedding[Embedding Service<br/>Python 3.11]
        DBService[DB Service<br/>DuckDB]
    end
    
    subgraph "アプリケーションレイヤー"
        API[FastAPI<br/>REST API Server]
    end
    
    subgraph "クライアントレイヤー"
        Client[HTTP Client<br/>Web/CLI/Python]
    end
    
    RawData --> Ingestion
    Ingestion --> Prepared
    Prepared --> Chunker
    Chunker --> Chunks
    Chunks --> Embedding
    Embedding --> Embeddings
    Embeddings --> DBService
    DBService --> DB
    DB --> API
    API --> Client
    
    style RawData fill:#f9f9f9
    style Prepared fill:#fff4e1
    style Chunks fill:#fff4e1
    style Embeddings fill:#fff4e1
    style DB fill:#ffe1e1
    style Ingestion fill:#e1f5ff
    style Chunker fill:#e1f5ff
    style Embedding fill:#e1f5ff
    style DBService fill:#e1f5ff
    style API fill:#e1ffe1
    style Client fill:#f0f0f0
```

---

## コンポーネント詳細

### 1. Ingestion Service

**目的:** 複数ソースからの生データを統合し、単一の時系列データを生成

**技術スタック:**
- Python 3.11
- Pandas (データ処理)
- PyArrow (Parquet I/O)

**主要機能:**
- CSV ファイルの読み込み
- タイムスタンプの正規化
- データの結合とマージ
- Parquet 形式での出力

**入力:**
- `data/sample/` - 生データファイル群

**出力:**
- `prepared/merged.parquet` - 統合時系列データ

**実行方法:**
```bash
docker compose run ingestion python prepare_data.py
```

**ステータス:** 🚧 準備中

---

### 2. Chunker Service

**目的:** 時系列データを固定長の時間窓で分割

**技術スタック:**
- Python 3.11
- Pandas
- NumPy

**主要機能:**
- 時系列データの読み込み
- タイムスタンプベースの分割（デフォルト: 60秒）
- チャンクへの連番付与
- Parquet 形式での保存

**アルゴリズム:**
```python
# 擬似コード
CHUNK_LEN = 60  # 秒
timestamps = data['ts'] / 1e9  # ナノ秒 → 秒
chunk_indices = (timestamps // CHUNK_LEN).astype(int)

for idx in unique(chunk_indices):
    chunk_data = data[chunk_indices == idx]
    save_to_parquet(f"chunk_{idx}.parquet", chunk_data)
```

**入力:**
- `prepared/merged.parquet`

**出力:**
- `data/chunks/chunk_0.parquet`
- `data/chunks/chunk_1.parquet`
- ...

**実行方法:**
```bash
docker compose run chunker python make_chunks.py
```

**実装ファイル:**
- `chunking/make_chunks.py`
- `chunking/download_sample_data.py`

---

### 3. Embedding Service

**目的:** 各チャンクから特徴量を抽出し、ベクトル化

**技術スタック:**
- Python 3.11
- NumPy (数値計算)
- Scikit-learn (特徴量抽出)
- 将来: TensorFlow/PyTorch (深層学習モデル)

**想定される特徴量:**

1. **統計的特徴量:**
   - 平均値、中央値
   - 標準偏差、分散
   - 最大値、最小値
   - パーセンタイル

2. **周波数特徴量:**
   - FFT (高速フーリエ変換)
   - スペクトログラム
   - 主要周波数成分

3. **時系列特徴量:**
   - 傾き（トレンド）
   - 変化率
   - ピーク検出

**入力:**
- `data/chunks/chunk_*.parquet`

**出力:**
- `embeddings/vectors.npy` - ベクトルデータ
- `embeddings/metadata.json` - メタデータ

**実行方法:**
```bash
docker compose run embedding python create_embeddings.py
```

**ステータス:** 🚧 準備中

---

### 4. Database Service (DuckDB)

**目的:** 構造化データの永続化とクエリ処理

**技術スタック:**
- DuckDB (組み込み分析データベース)
- Python 3.11

**DuckDB の特徴:**
- 軽量で高速な分析処理
- PostgreSQL 互換の SQL
- Parquet ファイルの直接クエリ対応
- OLAP (分析処理) に最適化

**テーブル設計:**

```sql
-- CAN bus ログ
CREATE TABLE can_log (
    ts TIMESTAMP,           -- タイムスタンプ
    vehicle_id VARCHAR,     -- 車両ID
    signal VARCHAR,         -- シグナル名
    value DOUBLE           -- 値
);

-- GPS ログ
CREATE TABLE gps_log (
    ts TIMESTAMP,           -- タイムスタンプ
    vehicle_id VARCHAR,     -- 車両ID
    lat DOUBLE,            -- 緯度
    lon DOUBLE,            -- 経度
    speed DOUBLE,          -- 速度 (km/h)
    heading DOUBLE         -- 方位角 (度)
);

-- インデックス
CREATE INDEX idx_can_ts ON can_log(ts);
CREATE INDEX idx_gps_ts ON gps_log(ts);
```

**入力:**
- `embeddings/` - ベクトルデータ

**データベースファイル:**
- `data/db/vehicle_logs.duckdb`

**実行方法:**
```bash
docker compose up db
```

**実装ファイル:**
- `db/run_duckdb.py`

---

### 5. API Service (FastAPI)

**目的:** REST API による データアクセス層の提供

**技術スタック:**
- FastAPI (高速な非同期Webフレームワーク)
- Uvicorn (ASGI サーバー)
- Pydantic (データバリデーション)

**エンドポイント設計:**

| メソッド | パス | 説明 |
|---------|------|------|
| GET | `/` | ヘルスチェック |
| GET | `/chunks` | チャンク一覧取得 |
| GET | `/chunks/{chunk_id}` | 特定チャンクのデータ取得 |
| GET | `/query` | SQL クエリ実行 (将来) |
| POST | `/search` | ベクトル類似検索 (将来) |

**レスポンス形式:**
```json
{
  "status": "success",
  "data": [...],
  "count": 100,
  "timestamp": "2025-12-29T00:00:00Z"
}
```

**入力:**
- DuckDB クエリ結果
- Parquet ファイル（直接読み込み）

**ポート:**
- `8000` (HTTP)

**実行方法:**
```bash
docker compose up api
```

**アクセス:**
```bash
curl http://localhost:8000/
curl http://localhost:8000/chunks
```

**実装ファイル:**
- `api/main.py`

---

## データフロー詳細

### ファイルフォーマット

すべての中間データは **Apache Parquet** 形式:

**Parquet の利点:**
- 列指向ストレージ → 効率的な圧縮
- スキーマ情報の埋め込み
- 高速な列アクセス
- Pandas/PyArrow との互換性

**タイムスタンプの扱い:**
- 内部表現: `int64` (ナノ秒)
- 処理時: 秒単位に変換 (`ts / 1e9`)
- DuckDB: `TIMESTAMP` 型

---

## Docker 構成

### Dockerfile 設計方針

各サービスは独立した Dockerfile を持つ:

**ベースイメージ:**
```dockerfile
FROM python:3.11-slim
```

**共通パターン:**
1. 作業ディレクトリ設定
2. 依存関係インストール
3. アプリケーションコード配置
4. 実行コマンド指定

**例: Chunker Service**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "make_chunks.py"]
```

### Docker Compose オーケストレーション

**サービス依存関係:**
```yaml
ingestion → chunker → embedding → db → api
```

**ボリュームマウント戦略:**
- ホスト側の `./data` を各コンテナの `/app/data` にマウント
- データの永続化と共有を実現

**ネットワーク:**
- デフォルトブリッジネットワーク
- サービス名で相互通信可能

---

## セキュリティ考慮事項

### 現在の実装

- ローカル開発環境向け
- 認証・認可なし
- ポート 8000 のみ公開

### 本番環境への移行時の推奨事項

1. **認証:**
   - OAuth 2.0 / JWT トークン
   - API キー認証

2. **通信:**
   - HTTPS/TLS 暗号化
   - リバースプロキシ (Nginx)

3. **データベース:**
   - アクセス制御
   - パスワード保護

4. **環境変数:**
   - `.env` ファイルで機密情報管理
   - Docker Secrets の活用

---

## パフォーマンス最適化

### 現在の最適化

- **Parquet 形式**: 圧縮率が高く、読み込みが高速
- **DuckDB**: OLAP クエリに最適化
- **Pandas**: ベクトル化された処理

### 将来の最適化案

1. **並列処理:**
   - マルチプロセス/マルチスレッド
   - Dask/Ray による分散処理

2. **キャッシング:**
   - Redis でクエリ結果をキャッシュ
   - API レベルでの ETag 対応

3. **インデックス:**
   - タイムスタンプインデックスの最適化
   - 複合インデックスの活用

4. **ストリーミング:**
   - Apache Kafka でリアルタイム処理
   - ストリーミングチャンク化

---

## 拡張性

### 水平スケーリング

- **API サーバー**: ロードバランサーで複数インスタンス
- **処理サービス**: Kubernetes での並列実行

### 垂直スケーリング

- DuckDB のメモリ割り当て増加
- コンテナリソース制限の調整

---

## 監視とロギング

### 推奨ツール

- **ログ集約**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **メトリクス**: Prometheus + Grafana
- **トレーシング**: Jaeger/OpenTelemetry

### ログ出力方針

- 構造化ログ (JSON 形式)
- タイムスタンプ付き
- ログレベル: DEBUG, INFO, WARNING, ERROR

---

## テスト戦略

### 現在の状態

- 手動テストのみ
- Docker Compose での統合テスト

### 推奨テスト構成

1. **ユニットテスト:**
   - pytest
   - 各モジュールの関数テスト

2. **統合テスト:**
   - Docker Compose でのエンドツーエンドテスト
   - API エンドポイントテスト

3. **パフォーマンステスト:**
   - 大量データでの処理時間計測
   - メモリ使用量の監視

---

## トラブルシューティング

### デバッグ方法

**ログ確認:**
```bash
docker compose logs -f [service_name]
```

**コンテナ内での確認:**
```bash
docker compose exec [service_name] bash
```

**ボリュームの確認:**
```bash
docker volume ls
docker volume inspect [volume_name]
```

### よくある問題

| 問題 | 原因 | 解決方法 |
|------|------|---------|
| コンテナが起動しない | Dockerfile のビルドエラー | `docker compose build --no-cache` |
| ボリュームが空 | マウントパスの誤り | `docker-compose.yml` を確認 |
| API が応答しない | DB サービスが起動していない | 依存関係を確認 |

---

## 参考資料

### 使用技術のドキュメント

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Apache Parquet Format](https://parquet.apache.org/docs/)

### 関連プロジェクト

- CAN bus デコーディング: `python-can`
- GPS 処理: `gpxpy`, `geopy`
- 時系列分析: `tslearn`, `tsfresh`
