# src/log.py
"""
CSV logger with fixed schema for SKYT experiment results
Writes one row per run with all relevant metrics and metadata
"""

import csv
import os
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

from .metrics import MetricsResult
from .contract_checker import ContractResult


@dataclass
class RunLog:
    """Single run log entry"""
    timestamp: str
    prompt_id: str
    run_id: int
    model: str
    temperature: float
    raw_code: str
    canonical_code: Optional[str]
    canonical_signature: Optional[str]
    structural_ok: bool
    canonicalization_ok: bool
    oracle_passed: Optional[bool]
    contract_passed: bool
    error_message: Optional[str]


class ExperimentLogger:
    """CSV logger for experiment results"""
    
    # Fixed CSV schema
    FIELDNAMES = [
        'timestamp',
        'prompt_id', 
        'run_id',
        'model',
        'temperature',
        'raw_code',
        'canonical_code',
        'canonical_signature',
        'structural_ok',
        'canonicalization_ok',
        'oracle_passed',
        'contract_passed',
        'error_message'
    ]
    
    def __init__(self, log_file: str):
        """
        Initialize logger
        
        Args:
            log_file: Path to CSV log file
        """
        self.log_file = log_file
        self._ensure_log_file()
    
    def _ensure_log_file(self):
        """Ensure log file exists with proper headers"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Create file with headers if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
                writer.writeheader()
    
    def log_run(self, 
                prompt_id: str,
                run_id: int,
                model: str,
                temperature: float,
                raw_code: str,
                contract_result: ContractResult):
        """
        Log a single run
        
        Args:
            prompt_id: Identifier for the prompt used
            run_id: Run number within the prompt
            model: LLM model used
            temperature: Temperature setting
            raw_code: Raw LLM output
            contract_result: Result from contract checking
        """
        log_entry = RunLog(
            timestamp=datetime.now().isoformat(),
            prompt_id=prompt_id,
            run_id=run_id,
            model=model,
            temperature=temperature,
            raw_code=raw_code,
            canonical_code=contract_result.canonical_code,
            canonical_signature=contract_result.canonical_signature,
            structural_ok=contract_result.structural_ok,
            canonicalization_ok=contract_result.canonicalization_ok,
            oracle_passed=contract_result.oracle_result,
            contract_passed=contract_result.contract_pass,
            error_message=contract_result.error_message
        )
        
        # Write to CSV
        with open(self.log_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELDNAMES)
            writer.writerow({
                'timestamp': log_entry.timestamp,
                'prompt_id': log_entry.prompt_id,
                'run_id': log_entry.run_id,
                'model': log_entry.model,
                'temperature': log_entry.temperature,
                'raw_code': log_entry.raw_code.replace('\n', '\\n'),  # Escape newlines
                'canonical_code': log_entry.canonical_code.replace('\n', '\\n') if log_entry.canonical_code else None,
                'canonical_signature': log_entry.canonical_signature,
                'structural_ok': log_entry.structural_ok,
                'canonicalization_ok': log_entry.canonicalization_ok,
                'oracle_passed': log_entry.oracle_passed,
                'contract_passed': log_entry.contract_passed,
                'error_message': log_entry.error_message
            })
    
    def log_summary(self, 
                    prompt_id: str,
                    metrics: MetricsResult,
                    model: str,
                    temperature: float):
        """
        Log summary metrics for a prompt (optional - for summary analysis)
        
        Args:
            prompt_id: Identifier for the prompt
            metrics: Calculated metrics
            model: LLM model used
            temperature: Temperature setting
        """
        # This could be logged to a separate summary file if needed
        # For now, metrics are calculated from the run logs
        pass
    
    def read_logs(self, prompt_id: Optional[str] = None) -> List[RunLog]:
        """
        Read logs from CSV file
        
        Args:
            prompt_id: Optional filter by prompt ID
            
        Returns:
            List of RunLog entries
        """
        logs = []
        
        if not os.path.exists(self.log_file):
            return logs
        
        with open(self.log_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if prompt_id is None or row['prompt_id'] == prompt_id:
                    logs.append(RunLog(
                        timestamp=row['timestamp'],
                        prompt_id=row['prompt_id'],
                        run_id=int(row['run_id']),
                        model=row['model'],
                        temperature=float(row['temperature']),
                        raw_code=row['raw_code'].replace('\\n', '\n'),  # Unescape newlines
                        canonical_code=row['canonical_code'].replace('\\n', '\n') if row['canonical_code'] else None,
                        canonical_signature=row['canonical_signature'],
                        structural_ok=row['structural_ok'].lower() == 'true',
                        canonicalization_ok=row['canonicalization_ok'].lower() == 'true',
                        oracle_passed=None if row['oracle_passed'] == 'None' else row['oracle_passed'].lower() == 'true',
                        contract_passed=row['contract_passed'].lower() == 'true',
                        error_message=row['error_message'] if row['error_message'] else None
                    ))
        
        return logs
