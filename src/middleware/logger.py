# src/middleware/logger.py
"""
[TODO logger.py]
Goal: atomic CSV appends with schema validation. No code.

1. Append functions: log_run, log_distance_pre, log_distance_post, log_repair.
2. Validate headers against schema.py. Create file with headers if missing.
3. Atomicity: write tmp file then rename to avoid partial writes.
4. Timestamps: ISO 8601 naive; store timezone string separately if needed.
5. Acceptance: repeated calls never corrupt headers or column order.
"""

import csv
import os
import tempfile
from datetime import datetime
from typing import Union
from .schema import (
    RunSpec, DistanceRecord, RepairRecord,
    RUNS_CSV_HEADERS, DISTANCES_CSV_HEADERS, REPAIRS_CSV_HEADERS,
    RUNS_CSV_PATH, DISTANCES_PRE_CSV_PATH, DISTANCES_POST_CSV_PATH, REPAIRS_CSV_PATH
)

def log_run(run_spec: RunSpec) -> None:
    """
    Log run specification to runs.csv
    
    Args:
        run_spec: RunSpec object containing run metadata
    """
    row_data = {
        "run_id": run_spec.run_id,
        "prompt_id": run_spec.prompt_id,
        "mode": run_spec.mode,
        "timestamp": run_spec.timestamp.isoformat(),
        "model": run_spec.model,
        "temperature": run_spec.temperature,
        "seed": run_spec.seed or "",
        "oracle_version": run_spec.oracle_version,
        "normalization_version": run_spec.normalization_version,
        "contract_id": run_spec.contract_id
    }
    
    _append_csv_row(RUNS_CSV_PATH, RUNS_CSV_HEADERS, row_data)

def log_distance(distance_record: DistanceRecord, csv_path: str) -> None:
    """
    Log distance measurement to distances CSV
    
    Args:
        distance_record: DistanceRecord object
        csv_path: Path to distances CSV (pre or post)
    """
    row_data = {
        "run_id": distance_record.run_id,
        "sample_id": distance_record.sample_id,
        "prompt_id": distance_record.prompt_id,
        "stage": distance_record.stage,
        "signature": distance_record.signature,
        "d": distance_record.d,
        "compliant": distance_record.compliant,
        "normalization_version": distance_record.normalization_version,
        "timestamp": distance_record.timestamp.isoformat()
    }
    
    _append_csv_row(csv_path, DISTANCES_CSV_HEADERS, row_data)

def log_repair(repair_record: RepairRecord) -> None:
    """
    Log repair operation to repairs.csv
    
    Args:
        repair_record: RepairRecord object containing repair details
    """
    row_data = {
        "run_id": repair_record.run_id,
        "sample_id": repair_record.sample_id,
        "before_signature": repair_record.before_signature,
        "after_signature": repair_record.after_signature,
        "d_before": repair_record.d_before,
        "d_after": repair_record.d_after,
        "steps": repair_record.steps,
        "success": repair_record.success,
        "reason": repair_record.reason,
        "timestamp": repair_record.timestamp.isoformat()
    }
    
    _append_csv_row(REPAIRS_CSV_PATH, REPAIRS_CSV_HEADERS, row_data)

def _append_csv_row(csv_path: str, headers: list, row_data: dict) -> None:
    """
    Atomically append a row to CSV file with header validation
    
    Args:
        csv_path: Path to CSV file
        headers: Expected CSV headers
        row_data: Row data dict
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    # Check if file exists and validate headers
    file_exists = os.path.exists(csv_path)
    if file_exists:
        _validate_csv_headers(csv_path, headers)
    
    # Create temporary file in same directory for atomic operation
    temp_dir = os.path.dirname(csv_path)
    with tempfile.NamedTemporaryFile(mode='w', newline='', encoding='utf-8',
                                     dir=temp_dir, delete=False) as temp_file:
        temp_path = temp_file.name
        
        # If original file exists, copy it to temp file first
        if file_exists:
            with open(csv_path, 'r', encoding='utf-8') as orig_file:
                temp_file.write(orig_file.read())
        else:
            # Write headers for new file
            writer = csv.DictWriter(temp_file, fieldnames=headers)
            writer.writeheader()
        
        # Append new row
        writer = csv.DictWriter(temp_file, fieldnames=headers)
        
        # Ensure all header fields are present in row_data
        complete_row = {header: row_data.get(header, "") for header in headers}
        writer.writerow(complete_row)
    
    # Atomic rename
    os.replace(temp_path, csv_path)

def _validate_csv_headers(csv_path: str, expected_headers: list) -> None:
    """
    Validate that CSV file has expected headers
    
    Args:
        csv_path: Path to CSV file
        expected_headers: List of expected header names
    
    Raises:
        ValueError: If headers don't match
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            actual_headers = next(reader, [])
        
        if actual_headers != expected_headers:
            raise ValueError(
                f"CSV header mismatch in {csv_path}. "
                f"Expected: {expected_headers}, "
                f"Actual: {actual_headers}"
            )
    
    except StopIteration:
        # Empty file, headers will be written
        pass

def read_csv_records(csv_path: str) -> list:
    """
    Read all records from CSV file
    
    Args:
        csv_path: Path to CSV file
    
    Returns:
        List of dict records
    """
    if not os.path.exists(csv_path):
        return []
    
    records = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    return records
