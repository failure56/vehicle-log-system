FROM python:3.11-slim

WORKDIR /app
COPY main.py /app/

RUN pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install fastapi uvicorn duckdb pandas numpy pyarrow sentence-transformers

# Start the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

