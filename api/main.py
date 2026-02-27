"""
Vehicle Log System API

エンドポイント:
  GET  /chunks                 チャンクファイル一覧
  GET  /chunk/{cid}            特定チャンクの内容（先頭50行）
  GET  /search?q=...&top_k=5   テキストクエリからベクトル類似検索
  GET  /logs                   CAN/GPS ログの直接クエリ
  GET  /health                 ヘルスチェック
"""
from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
import duckdb
import pandas as pd
import numpy as np
import os

DB_PATH = "data/db/vehicle_logs.duckdb"
CHUNKS_DIR = "data/chunks"

# --- sentence-transformers の遅延ロード ---
_model = None


def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            raise HTTPException(
                status_code=503,
                detail="sentence-transformers is not installed. Search is unavailable.",
            )
    return _model


def get_db() -> duckdb.DuckDBPyConnection:
    """DuckDB への読み取り専用接続を返す。"""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=503, detail=f"Database not found: {DB_PATH}")
    return duckdb.connect(DB_PATH, read_only=True)


app = FastAPI(
    title="Vehicle Log System API",
    description="車載データパイプラインの検索・クエリ API",
    version="0.2.0",
)


@app.get("/health")
def health():
    """ヘルスチェック"""
    return {"status": "ok"}


@app.get("/chunks")
def list_chunks():
    """チャンクファイルの一覧を返す。"""
    if not os.path.isdir(CHUNKS_DIR):
        raise HTTPException(status_code=404, detail=f"Chunks directory not found: {CHUNKS_DIR}")
    files = sorted([f for f in os.listdir(CHUNKS_DIR) if f.endswith(".parquet")])
    return {"count": len(files), "chunks": files}


@app.get("/chunk/{cid}")
def get_chunk(cid: int):
    """特定チャンクの内容（先頭50行）を返す。"""
    f = os.path.join(CHUNKS_DIR, f"chunk_{cid}.parquet")
    if not os.path.exists(f):
        raise HTTPException(status_code=404, detail=f"Chunk {cid} not found")
    df = pd.read_parquet(f)
    return {
        "chunk_id": cid,
        "total_rows": len(df),
        "columns": list(df.columns),
        "data": df.head(50).to_dict(orient="records"),
    }


@app.get("/search")
def search(
    q: str = Query(..., description="検索クエリテキスト"),
    top_k: int = Query(5, ge=1, le=50, description="返却する類似チャンク数"),
):
    """
    テキストクエリからベクトル類似検索を実行する。
    embedding テーブルに保存されたベクトルとコサイン類似度で比較。
    """
    model = get_model()
    query_vec = model.encode(q).tolist()

    con = get_db()

    # embeddings テーブルの存在確認
    tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
    if "embeddings" not in tables:
        con.close()
        raise HTTPException(status_code=503, detail="Embeddings table not found. Run embedding pipeline first.")

    count = con.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    if count == 0:
        con.close()
        raise HTTPException(status_code=404, detail="No embeddings stored yet.")

    # コサイン類似度計算
    # DuckDB の list_cosine_similarity 関数を使用
    results = con.execute("""
        SELECT
            chunk_id,
            chunk_file,
            text_repr,
            speed_mean,
            speed_std,
            num_rows,
            start_ts,
            end_ts,
            list_cosine_similarity(vector, ?::FLOAT[384]) AS similarity
        FROM embeddings
        ORDER BY similarity DESC
        LIMIT ?
    """, [query_vec, top_k]).fetchdf()

    con.close()

    return {
        "query": q,
        "top_k": top_k,
        "results": results.to_dict(orient="records"),
    }


@app.get("/logs")
def query_logs(
    table: str = Query("gps_log", description="テーブル名 (gps_log or can_log)"),
    vehicle_id: str = Query(None, description="車両ID でフィルタ"),
    start: str = Query(None, description="開始タイムスタンプ (ISO 8601)"),
    end: str = Query(None, description="終了タイムスタンプ (ISO 8601)"),
    limit: int = Query(100, ge=1, le=10000, description="最大行数"),
):
    """CAN/GPS ログテーブルを直接クエリする。"""
    if table not in ("can_log", "gps_log"):
        raise HTTPException(status_code=400, detail="table must be 'can_log' or 'gps_log'")

    con = get_db()

    conditions = []
    params = []

    if vehicle_id:
        conditions.append("vehicle_id = ?")
        params.append(vehicle_id)
    if start:
        conditions.append("ts >= ?::TIMESTAMP")
        params.append(start)
    if end:
        conditions.append("ts <= ?::TIMESTAMP")
        params.append(end)

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    query = f"SELECT * FROM {table} {where} ORDER BY ts LIMIT ?"
    params.append(limit)

    df = con.execute(query, params).fetchdf()
    con.close()

    return {
        "table": table,
        "count": len(df),
        "data": df.to_dict(orient="records"),
    }
