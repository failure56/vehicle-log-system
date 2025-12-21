"""車両ログシステムのFastAPI サーバー。

チャンクファイル（Parquet形式）を提供するREST APIエンドポイントを実装しています。
"""
from fastapi import FastAPI
import pandas as pd
import os

app = FastAPI()

@app.get("/chunks")
def list_chunks():
    """利用可能なチャンクファイルのリストを取得する。
    
    Returns:
        dict: チャンクファイル名のリストを含む辞書
    """
    files = os.listdir("data/chunks")
    return {"chunks": files}

@app.get("/chunk/{cid}")
def get_chunk(cid: int):
    """指定されたIDのチャンクデータを取得する。
    
    Args:
        cid: チャンクID（整数）
        
    Returns:
        dict: チャンクデータ（最初の50行）または エラーメッセージ
    """
    f = f"data/chunks/chunk_{cid}.parquet"
    if not os.path.exists(f):
        return {"error": "not found"}
    df = pd.read_parquet(f)
    # 大きなレスポンスを避けるため、最初の50行のみ返す
    return df.head(50).to_dict()
