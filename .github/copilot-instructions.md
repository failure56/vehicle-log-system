# Copilot Instructions for Vehicle Log System

## Repository Overview

This is a modular data pipeline for processing vehicle telemetry data (CAN bus, GPS, and general telemetry). The system performs data ingestion, chunking, feature extraction, embedding, and querying capabilities.

## Technology Stack

- **Language**: Python 3.11
- **Web Framework**: FastAPI with Uvicorn
- **Database**: DuckDB
- **Data Processing**: Pandas, NumPy, PyArrow
- **Containerization**: Docker and Docker Compose
- **Data Format**: Parquet files for efficient storage

## Docker Services

The system uses the following Docker Compose services:
- **ingestion**: Data ingestion service (in preparation)
- **chunker**: Time-series chunking service
- **embedding**: Vector embedding service (in preparation)
- **db**: DuckDB database server (container: `vehicle_db`)
- **api**: FastAPI REST API server

## Project Structure

```
vehicle-log-system/
├── api/                    # FastAPI server for querying data
│   ├── Dockerfile
│   └── main.py
├── chunking/               # Time-series chunking logic
│   ├── Dockerfile
│   ├── make_chunks.py
│   └── download_sample_data.py
├── db/                     # DuckDB initialization
│   ├── Dockerfile
│   └── run_duckdb.py
├── data/                   # Data storage directory
│   ├── chunks/             # Chunked data (Parquet) - created by chunker
│   ├── db/                 # DuckDB database files
│   └── sample/             # Sample input data
├── chunks/                 # Docker volume mount (created at runtime)
├── prepared/               # Docker volume mount (created at runtime)
├── embeddings/             # Docker volume mount (created at runtime)
├── docker-compose.yml      # Multi-service orchestration
└── README.md
```

**Note**: 
- Directories `chunks/`, `prepared/`, `embeddings/` at the root are Docker volume mount points created at runtime
- The `data/` directory contains persistent data storage
- **Known Issue**: The `chunker` service mounts `./chunks:/app/chunks` but the code (`make_chunks.py`) writes to `data/chunks/`. The `ingestion` service has `./data:/app/data` mounted. This configuration mismatch needs to be resolved for proper operation

## Development Workflow

### Building and Running

1. **Download sample data** (first time only):
   ```bash
   docker compose run chunker python download_sample_data.py
   ```

2. **Generate chunks**:
   ```bash
   docker compose run chunker python make_chunks.py
   ```

3. **Start all services**:
   ```bash
   docker compose up
   ```

4. **Access points**:
   - API Server: http://localhost:8000
   - DuckDB: File-based access (no network port exposed)

### Testing

- No formal test suite exists yet
- Manual testing via API endpoints and Docker Compose
- When adding tests, follow Python testing conventions (pytest recommended)

## Code Conventions

### Python Style

- Use Python 3.11+ features
- Import standard libraries first, then third-party, then local modules
- Keep functions focused and single-purpose
- Use type hints where appropriate for clarity

### Data Processing

- **Time units**: Timestamps are stored as nanoseconds (int64) and converted to seconds for chunking
- **Chunk size**: Default is 60 seconds (`CHUNK_LEN = 60`)
- **File format**: Use Parquet for all data storage (efficient compression and columnar format)
- **Naming convention**: Chunks are named `chunk_{idx}.parquet` where idx is sequential

### Database

- **DuckDB tables**:
  - `can_log`: CAN bus data (ts, vehicle_id, signal, value)
  - `gps_log`: GPS data (ts, vehicle_id, lat, lon, speed, heading)
- All tables use `ts TIMESTAMP` for time-series ordering
- Always order queries by `ts` for time-series data

### Docker

- Each service has its own Dockerfile
- Use `python:3.11-slim` as base image for consistency
- Volume mounts connect services to shared data directories
- Services run commands explicitly in docker-compose.yml or via `docker compose run`

### API Design

- Use FastAPI for RESTful endpoints
- Return JSON responses with descriptive keys
- Handle file-not-found gracefully with error messages
- Limit large responses (e.g., `.head(50)` for dataframes)

## Common Tasks

### Adding a New Data Processing Module

1. Create a new directory (e.g., `embedding/`)
2. Add a Dockerfile following existing patterns
3. Create the main Python script with clear entry point
4. Add service to `docker-compose.yml`
5. Update README.md with new module documentation

### Modifying Chunking Logic

- Edit `chunking/make_chunks.py`
- Keep `CHUNK_LEN` configurable
- Ensure output maintains Parquet format
- Test with sample data before deploying

### Adding API Endpoints

- Edit `api/main.py`
- Follow FastAPI decorator patterns (`@app.get()`, etc.)
- Include path and query parameters as needed
- Return dict/JSON-compatible types
- Handle errors gracefully

## Important Notes

- **Language**: Documentation is in Japanese (日本語), code comments in English
- **Data paths**: All data paths are relative to the working directory in containers
- **Volume mounts**: Services share data through Docker volumes
- **Service dependencies**: Check `depends_on` in docker-compose.yml
- **Status**: Some modules (ingestion, embedding) are in preparation (`準備中`)

## Future Enhancements Planned

- CAN raw log ingestion
- High-resolution GPS interpolation (Kalman Filter)
- FFT-based frequency features
- Driving scene classification
- Web UI dashboard

## Security Considerations

- No secrets or credentials should be committed to the repository
- Use environment variables for sensitive configuration
- The `.gitignore` already excludes `.env`, `*.secret`, `*.key`, `*.token`

## When Helping with This Repository

1. **Understand the data flow**: Ingestion → Chunking → Embedding → Database → API
2. **Respect the modular architecture**: Each service is independent
3. **Maintain Docker-first approach**: All development uses Docker Compose
4. **Keep Japanese documentation**: README and user-facing docs use Japanese
5. **Preserve existing patterns**: Follow established naming and structure conventions
6. **Test with Docker**: Always validate changes in Docker containers, not just local Python
