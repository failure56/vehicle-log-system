# Plan: Vehicle Log System パイプライン修復 & Copilot Agent 定義

## TL;DR

プロジェクトは設計は明確だが、実装は初期段階。**docker-compose.yml のDockerfile参照ミス**（全サービスビルド不可）、**ingestion / embedding が未実装**、**データロードの断絶**が主要な問題。まず全CRITICALバグを修正し、パイプライン全体を動作可能にした上で、各コンポーネントに特化した Copilot カスタムエージェントを `.github/copilot/agents/` に定義する。

---

## 現状サマリー

| コンポーネント | 状態 | 主な問題 |
|---|---|---|
| **Ingestion** | 未実装 (空) | ディレクトリ空、Dockerfile なし |
| **Chunking** | 部分実装 | Dockerfile名不一致、CAN データ未使用、DuckDBへのCSVロードが欠落 |
| **Embedding** | 未実装 (空) | ディレクトリ空、compose は `./embeddings` を参照（typo） |
| **DB** | 部分実装 | スキーマ作成のみ、永続サービスとして動作しない |
| **API** | 部分実装 | パスマウント不一致、エラーハンドリング不足、検索エンドポイントなし |
| **docker-compose.yml** | 壊れている | 全4サービスの `dockerfile:` 参照が実ファイルと不一致 |
| **scripts** | ファイル名バグ | `rewrite)issue.py` → ワークフローは `rewrite_issue.py` を期待 |

---

## Steps

### Phase 0: CRITICAL バグ修正

1. **docker-compose.yml の Dockerfile 参照を修正** — docker-compose.yml の各サービスで `dockerfile: Dockerfile.xxx` を `dockerfile: Dockerfile` に変更。`embedding` サービスの `context: ./embeddings` を `context: ./embedding` に修正
2. **スクリプトのファイル名修正** — `scripts/rewrite)issue.py` を `scripts/rewrite_issue.py` にリネーム

### Phase 1: Ingestion コンポーネント実装

3. `ingestion/Dockerfile` を新規作成 — Python 3.11-slim ベース、`duckdb pandas pyarrow` をインストール
4. `ingestion/prepare_data.py` を新規作成 — `data/sample/` 内の CSV（CAN/GPS）を読み込み、DuckDB の `can_log` / `gps_log` テーブルにロードするスクリプト。これが現在のパイプラインの断絶部分（ダウンロード → DuckDB）を埋める
5. docker-compose.yml の `ingestion` サービスのボリュームマウントに `./data/db:/app/data/db` を追加（DuckDB ファイルへのアクセス用）

### Phase 2: Chunking 修正

6. `chunking/make_chunks.py` を修正 — `can` データの活用ロジック追加（CAN 信号の統計量をチャンクに含める）、未使用の `SUBCHUNK` 定数を削除または活用
7. docker-compose.yml の `chunker` サービスのボリュームを修正 — `./data/chunks:/app/data/chunks` と `./data/db:/app/data/db` を正しくマウント

### Phase 3: Embedding コンポーネント実装

8. `embedding/Dockerfile` を新規作成 — Python 3.11-slim ベース、`sentence-transformers torch duckdb pandas pyarrow` をインストール（ローカル推論をデフォルトとしつつ、OpenAI API もオプションで対応）
9. `embedding/embed_chunks.py` を新規作成 — `data/chunks/` の Parquet チャンクを読み込み、`sentence-transformers` (`all-MiniLM-L6-v2`) でベクトル化して DuckDB の `embeddings` テーブルに保存
10. docker-compose.yml の `embedding` サービスのボリュームを修正

### Phase 4: DB サービス改善

11. `db/run_duckdb.py` を拡張 — `embeddings` テーブルのスキーマ追加（`chunk_id`, `vector FLOAT[]`, `metadata`）。スクリプトをスキーマ初期化後に正常終了する形に整理

### Phase 5: API 拡張

12. `api/main.py` を拡張:
    - `GET /search?q=...&top_k=5` — テキストクエリからベクトル類似検索
    - `GET /logs?vehicle_id=...&start=...&end=...` — DuckDB への直接クエリ
    - 適切な HTTP ステータスコード（404 等）の導入
    - DuckDB への読み取り接続を追加
13. docker-compose.yml の `api` サービスボリュームに `./data/db:/app/data/db` を追加

### Phase 6: GitHub Copilot カスタムエージェント定義

14. `.github/copilot-instructions.md` を新規作成 — プロジェクト全体の Copilot 向けコンテキスト（アーキテクチャ、命名規則、技術スタック）
15. 以下のカスタムエージェント定義を `.github/copilot/agents/` に作成:

| エージェント | ファイル | 用途 |
|---|---|---|
| **@pipeline** | `pipeline.md` | パイプライン全体の設計・デバッグ。データフロー（ingestion→chunking→embedding→db→api）の知識を持ち、docker-compose やボリュームマウントの整合性を検証 |
| **@data-engineer** | `data-engineer.md` | DuckDB スキーマ設計、Parquet 操作、データ変換ロジック。CAN/GPS データの前処理パターンに特化 |
| **@vehicle-api** | `vehicle-api.md` | FastAPI エンドポイントの設計・実装。OpenAPI スキーマ、エラーハンドリング、類似検索APIに特化 |
| **@issue-ops** | `issue-ops.md` | GitHub Actions ワークフローとIssueリライト自動化。OpenAI API連携、ワークフロー構文に特化 |

### Phase 7: ドキュメント更新

16. README.md を更新 — クイックスタートの手順を実際の docker-compose サービス名と一致させる、ポート情報の修正、Embedding セクションのステータス更新

---

## Verification

- `docker compose config` でYAMLの構文・参照エラーがないことを確認
- `docker compose build` で全5サービスのビルドが成功することを確認
- パイプライン全体の E2E テスト:
  1. `docker compose run chunking python download_sample_data.py` → `data/sample/` にCSV生成
  2. `docker compose run ingestion python prepare_data.py` → DuckDB にデータロード
  3. `docker compose run chunker python make_chunks.py` → `data/chunks/` にParquet生成
  4. `docker compose run embedding python embed_chunks.py` → DuckDB に embedding 保存
  5. `docker compose up api` → `http://localhost:8000/chunks` と `/search?q=acceleration` が動作
- GitHub Actions: `rewrite_issue.py` のパスが一致していることを確認

---

## Decisions

- **Embedding モデル**: デフォルトは `sentence-transformers/all-MiniLM-L6-v2`（ローカル、無料、Docker内で完結）。OpenAI Embeddings はオプション対応とする
- **DuckDB 運用方式**: 永続サーバーではなくファイルベース。各サービスがボリュームマウント経由で同一 `.duckdb` ファイルにアクセス（同時書き込みは排他制御で対応）
- **Copilot エージェント**: GitHub Copilot の `.github/copilot/agents/*.md` 形式で定義。VS Code Chat で `@pipeline` のように呼び出し可能にする
