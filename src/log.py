# src/log.py
"""
Logging and data model for SKYT pipeline
Handles ExecutionRecord writing to CSV and XLSX formats
"""

import csv
import os
import time
from typing import Dict, Any
from .config import METRICS_VERSION, LOG_TO_CSV

# ExecutionRecord fields
EXECUTION_FIELDS = [
    "ts", "prompt_id", "run_id", "model", "temperature", 
    "raw_output", "code", "canon_code", "raw_hash", "canon_signature",
    "structural_ok", "canonicalization_ok", "contract_pass", "oracle_pass",
    "notes", "attempts", "last_error", "status", "metrics_version", "contract_id",
    "anchor_hit", "distance", "foundational_signature", "rescued", "rescue_steps",
    "env_signature", "env_ok", "env_enforcement", "env_mismatches"
]


def write_execution_record(record: Dict[str, Any], output_path: str = "outputs/results.csv"):
    """
    Write execution record to CSV file
    
    Args:
        record: ExecutionRecord dict
        output_path: Path to output CSV file
    """
    # Add timestamp and metadata
    record["ts"] = time.time()
    record["run_id"] = record.get("run_id", f"{record['prompt_id']}_{int(time.time())}")
    record["metrics_version"] = METRICS_VERSION
    record["status"] = record.get("status", "completed")
    
    if LOG_TO_CSV:
        _write_csv_record(record, output_path)
    
    # TODO: Add XLSX export if needed


def _write_csv_record(record: Dict[str, Any], path: str):
    """Write single record to CSV file"""
    # Ensure output directory exists
    dirname = os.path.dirname(path)
    if dirname:  # Only create directory if path has a directory component
        os.makedirs(dirname, exist_ok=True)
    
    # Check if file exists to determine if header is needed
    file_exists = os.path.exists(path)
    
    with open(path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=EXECUTION_FIELDS)
        
        if not file_exists:
            writer.writeheader()
        
        # Filter record to only include defined fields
        filtered_record = {k: record.get(k, "") for k in EXECUTION_FIELDS}
        writer.writerow(filtered_record)


def read_execution_records(path: str = "outputs/results.csv") -> list:
    """
    Read execution records from CSV file
    
    Args:
        path: Path to CSV file
    
    Returns:
        List of execution record dicts
    """
    if not os.path.exists(path):
        return []
    
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    
    return records
