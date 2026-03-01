FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install sentence-transformers duckdb pandas pyarrow

WORKDIR /app
COPY embed_chunks.py /app/
