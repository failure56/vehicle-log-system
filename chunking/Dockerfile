FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential && rm -rf /var/lib/apt/lists/*

RUN pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org duckdb pandas numpy pyarrow

WORKDIR /app
COPY make_chunks.py /app/
COPY download_sample_data.py /app/
