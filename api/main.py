from fastapi import FastAPI
import pandas as pd
import os

app = FastAPI()

@app.get("/chunks")
def list_chunks():
    files = os.listdir("data/chunks")
    return {"chunks": files}

@app.get("/chunk/{cid}")
def get_chunk(cid: int):
    f = f"data/chunks/chunk_{cid}.parquet"
    if not os.path.exists(f):
        return {"error": "not found"}
    df = pd.read_parquet(f)
    return df.head(50).to_dict()
