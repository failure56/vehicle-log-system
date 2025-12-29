# データフロー図 (Data Flow Diagram)

Vehicle Log System の処理パイプラインの全体像を示します。

## 全体フロー概要

```mermaid
flowchart TB
    Start([生データ]) --> Ingestion
    Ingestion[Ingestion<br/>データ統合処理] --> Merged[merged.parquet<br/>統合時系列データ]
    Merged --> Chunker
    Chunker[Chunker<br/>時間窓分割処理] --> Chunks[chunks/<br/>チャンクデータ群]
    Chunks --> Embedding
    Embedding[Embedding<br/>ベクトル化処理] --> Vectors[embeddings/<br/>ベクトルデータ]
    Vectors --> DB
    DB[(DuckDB<br/>データベース)] --> API
    API[FastAPI<br/>REST API] --> Client([クライアント])
    
    style Ingestion fill:#e1f5ff
    style Chunker fill:#e1f5ff
    style Embedding fill:#e1f5ff
    style DB fill:#ffe1e1
    style API fill:#e1ffe1
    style Merged fill:#fff4e1
    style Chunks fill:#fff4e1
    style Vectors fill:#fff4e1
```

## 各処理ステージの詳細

### 1. Ingestion（データ統合）

**入力:**
- CAN bus ログ（CSV）
- GPS データ（CSV）
- テレメトリデータ（CSV）
- その他の車載センサーデータ

**処理:**
- タイムスタンプの正規化
- データフォーマットの統一
- 異なるソースのデータをマージ
- 欠損値の処理

**出力:**
- `prepared/merged.parquet` - 統合された時系列データ

**ステータス:** 🚧 準備中

---

### 2. Chunking（チャンク化）

**入力:**
- `prepared/merged.parquet`

**処理:**
- 時系列データを固定長の時間窓で分割（デフォルト: 60秒）
- 各チャンクに連番インデックスを付与
- Parquet 形式で保存

**出力:**
- `data/chunks/chunk_0.parquet`
- `data/chunks/chunk_1.parquet`
- `data/chunks/chunk_N.parquet`

**実装:** `chunking/make_chunks.py`

**主要パラメータ:**
- `CHUNK_LEN = 60` (秒)

---

### 3. Embedding（ベクトル化）

**入力:**
- `data/chunks/` 内の各チャンクファイル

**処理:**
- 各チャンクから特徴量を抽出
- 特徴量をベクトル化
- 類似検索用のインデックス構築

**出力:**
- `embeddings/` - ベクトルデータとインデックス

**ステータス:** 🚧 準備中

**将来の拡張:**
- FFT による周波数成分解析
- 統計的特徴量（平均、分散、最大・最小値）
- 運転シーン分類ラベル

---

### 4. Database (DuckDB)

**入力:**
- `embeddings/` - ベクトルデータ

**処理:**
- DuckDB データベースへのデータ投入
- テーブル構造の初期化
- インデックスの構築

**テーブル構造:**

```sql
-- CAN ログテーブル
CREATE TABLE can_log (
    ts TIMESTAMP,
    vehicle_id VARCHAR,
    signal VARCHAR,
    value DOUBLE
);

-- GPS ログテーブル
CREATE TABLE gps_log (
    ts TIMESTAMP,
    vehicle_id VARCHAR,
    lat DOUBLE,
    lon DOUBLE,
    speed DOUBLE,
    heading DOUBLE
);
```

**データベースファイル:**
- `data/db/vehicle_logs.duckdb`

**実装:** `db/run_duckdb.py`

---

### 5. API (FastAPI)

**入力:**
- DuckDB からのクエリ結果
- チャンクファイルの直接読み込み

**処理:**
- REST API エンドポイントの提供
- クエリパラメータの処理
- レスポンスのJSON変換

**主要エンドポイント:**
- `GET /` - ヘルスチェック
- `GET /chunks` - チャンク一覧
- `GET /chunks/{chunk_id}` - 特定チャンクのデータ取得
- その他（将来追加予定）

**実装:** `api/main.py`

**アクセス:**
- `http://localhost:8000`

---

## Docker サービス構成

```mermaid
flowchart LR
    subgraph Docker Compose
        I[ingestion]
        C[chunker]
        E[embedding]
        D[db<br/>vehicle_db]
        A[api]
    end
    
    I --> C
    C --> E
    E --> D
    D --> A
    A --> |port 8000| Client([外部アクセス])
    
    style I fill:#e1f5ff
    style C fill:#e1f5ff
    style E fill:#e1f5ff
    style D fill:#ffe1e1
    style A fill:#e1ffe1
```

### サービス間の依存関係

- **ingestion** → **chunker**: データ統合後にチャンク化
- **chunker** → **embedding**: チャンク生成後にベクトル化
- **embedding** → **db**: ベクトル化後にDB保存
- **db** → **api**: DBからデータ取得してAPI提供

### ボリュームマウント

各サービスは Docker ボリュームを通じてデータを共有:

- `./data` - 永続データストレージ
- `./prepared` - 統合データ
- `./chunks` - チャンクデータ
- `./embeddings` - ベクトルデータ

---

## 実行フロー

### 初回セットアップ

```bash
# 1. サンプルデータのダウンロード
docker compose run chunker python download_sample_data.py

# 2. チャンク化処理
docker compose run chunker python make_chunks.py

# 3. 全サービスの起動
docker compose up
```

### データ処理フロー（将来）

```bash
# 1. データ統合
docker compose run ingestion python prepare_data.py

# 2. チャンク化
docker compose run chunker python make_chunks.py

# 3. ベクトル化
docker compose run embedding python create_embeddings.py

# 4. API起動
docker compose up api db
```

---

## データフォーマット

### Parquet ファイル構造

すべての中間データは Apache Parquet 形式で保存されます:

**利点:**
- 列指向ストレージで効率的な圧縮
- スキーマ情報の保持
- 高速な読み込み性能
- Pandas/PyArrow との互換性

**タイムスタンプ:**
- 内部: int64 (ナノ秒)
- 処理時: 秒単位に変換

---

## トラブルシューティング

### よくある問題

| 問題 | 原因 | 解決方法 |
|------|------|---------|
| チャンクが生成されない | サンプルデータが未ダウンロード | `docker compose run chunker python download_sample_data.py` |
| API が起動しない | DB サービスが起動していない | `docker compose up db` を先に実行 |
| パスが見つからない | ボリュームマウントの問題 | `docker-compose.yml` のボリューム設定を確認 |

---

## 今後の拡張予定

### 機能追加

- [ ] CAN デコーダーの実装
- [ ] GPS 補間処理（Kalman Filter）
- [ ] リアルタイム処理対応
- [ ] Web UI ダッシュボード
- [ ] データエクスポート機能

### 最適化

- [ ] 並列処理の導入
- [ ] キャッシング戦略
- [ ] インデックス最適化
