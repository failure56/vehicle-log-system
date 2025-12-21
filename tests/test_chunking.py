"""Tests for chunking functionality."""
import pandas as pd
import os
import pytest
import sys

# Add chunking directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'chunking'))


def test_chunk_creation():
    """Test that chunks are created correctly."""
    chunks_dir = "data/chunks"
    
    # Check that chunks directory exists
    assert os.path.exists(chunks_dir), f"Chunks directory not found at {chunks_dir}"
    
    # Get list of chunk files
    chunk_files = [f for f in os.listdir(chunks_dir) if f.startswith("chunk_") and f.endswith(".parquet")]
    
    # At least one chunk should be created
    assert len(chunk_files) > 0, "No chunks were created"
    
    print(f"Found {len(chunk_files)} chunk files")


def test_chunk_format():
    """Test that chunk files have correct format."""
    chunks_dir = "data/chunks"
    chunk_files = [f for f in os.listdir(chunks_dir) if f.startswith("chunk_") and f.endswith(".parquet")]
    
    if len(chunk_files) == 0:
        pytest.skip("No chunks available for testing")
    
    # Test first chunk
    first_chunk = os.path.join(chunks_dir, chunk_files[0])
    df = pd.read_parquet(first_chunk)
    
    # Check that dataframe is not empty
    assert len(df) > 0, "Chunk dataframe should not be empty"
    
    # Check required columns exist
    required_columns = ['ts', 'vehicle_id', 'sec']
    for col in required_columns:
        assert col in df.columns, f"Column '{col}' missing from chunk"
    
    print(f"Chunk has {len(df)} rows and columns: {df.columns.tolist()}")


def test_chunk_time_range():
    """Test that chunks have correct time range (60 seconds)."""
    chunks_dir = "data/chunks"
    chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.startswith("chunk_") and f.endswith(".parquet")])
    
    if len(chunk_files) == 0:
        pytest.skip("No chunks available for testing")
    
    # Test first chunk
    first_chunk = os.path.join(chunks_dir, chunk_files[0])
    df = pd.read_parquet(first_chunk)
    
    if len(df) > 1:
        # Check time range
        sec_range = df['sec'].max() - df['sec'].min()
        # Should be approximately 60 seconds (or less for last chunk)
        assert sec_range <= 60, f"Chunk time range exceeds 60 seconds: {sec_range}"
        print(f"Chunk time range: {sec_range} seconds")


def test_chunk_naming_convention():
    """Test that chunk files follow naming convention."""
    chunks_dir = "data/chunks"
    chunk_files = [f for f in os.listdir(chunks_dir) if f.startswith("chunk_") and f.endswith(".parquet")]
    
    # Check naming pattern
    import re
    pattern = re.compile(r'^chunk_\d+\.parquet$')
    
    for chunk_file in chunk_files:
        assert pattern.match(chunk_file), f"Chunk file {chunk_file} doesn't match naming convention"
    
    print(f"All {len(chunk_files)} chunk files follow naming convention")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
