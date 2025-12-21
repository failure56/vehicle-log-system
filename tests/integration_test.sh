#!/bin/bash
# Integration test script for vehicle log system

set -e  # Exit on any error

echo "=========================================="
echo "Vehicle Log System Integration Test"
echo "=========================================="

# Clean up any previous test data
echo ""
echo "Step 1: Cleaning up previous test data..."
rm -rf data/db data/chunks
mkdir -p data/db data/chunks

# Build all services
echo ""
echo "Step 2: Building Docker services..."
docker compose build

# Initialize database
echo ""
echo "Step 3: Initializing database..."
docker compose run --rm db python run_duckdb.py

# Download sample data (if not exists)
echo ""
echo "Step 4: Checking sample data..."
if [ ! -f "data/sample/gps.csv" ] && [ ! -f "data/sample/can.csv" ]; then
    echo "Downloading sample data..."
    docker compose run --rm chunker python download_sample_data.py
else
    echo "Sample data already exists, skipping download."
fi

# Create mock data for testing (since actual download might fail)
echo ""
echo "Step 5: Creating test data..."
docker compose run --rm -e PYTEST_RUNNING=1 chunker python -c "
import pandas as pd
import numpy as np
import os
import duckdb

# Create test GPS data
np.random.seed(42)
n_points = 1000
timestamps = np.arange(n_points) * 1e9  # nanoseconds

gps_data = pd.DataFrame({
    'ts': pd.to_datetime(timestamps, unit='ns'),
    'vehicle_id': ['vehicle_001'] * n_points,
    'lat': 35.6762 + np.random.randn(n_points) * 0.01,  # Tokyo area
    'lon': 139.6503 + np.random.randn(n_points) * 0.01,
    'speed': np.abs(np.random.randn(n_points) * 20 + 50),
    'heading': np.random.rand(n_points) * 360
})

# Create test CAN data
can_data = pd.DataFrame({
    'ts': pd.to_datetime(timestamps[:500], unit='ns'),
    'vehicle_id': ['vehicle_001'] * 500,
    'signal': ['engine_rpm', 'vehicle_speed'] * 250,
    'value': np.random.rand(500) * 100
})

# Insert into DuckDB
con = duckdb.connect('data/db/vehicle_logs.duckdb')
con.execute('INSERT INTO gps_log SELECT * FROM gps_data')
con.execute('INSERT INTO can_log SELECT * FROM can_data')
con.close()

print('Test data created successfully')
"

# Run chunking
echo ""
echo "Step 6: Creating chunks..."
docker compose run --rm chunker python make_chunks.py

# Verify chunks were created
echo ""
echo "Step 7: Verifying chunks..."
CHUNK_COUNT=$(ls -1 data/chunks/chunk_*.parquet 2>/dev/null | wc -l)
if [ "$CHUNK_COUNT" -eq 0 ]; then
    echo "ERROR: No chunks were created!"
    exit 1
fi
echo "✓ Created $CHUNK_COUNT chunks"

# Start API service in background
echo ""
echo "Step 8: Starting API service..."
docker compose up -d api

# Wait for API to be ready
echo "Waiting for API to be ready..."
sleep 5

# Check API health
echo ""
echo "Step 9: Testing API endpoints..."
API_RESPONSE=$(curl -s http://localhost:8000/chunks)
if [[ $API_RESPONSE == *"chunks"* ]]; then
    echo "✓ API is responding correctly"
else
    echo "ERROR: API is not responding correctly"
    docker compose logs api
    docker compose down
    exit 1
fi

# Stop services
echo ""
echo "Step 10: Stopping services..."
docker compose down

echo ""
echo "=========================================="
echo "✓ All integration tests passed!"
echo "=========================================="
