FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install duckdb pandas pyarrow

WORKDIR /app
COPY prepare_data.py /app/
