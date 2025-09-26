# tests_mw/test_metrics.py
"""
[TODO test_metrics.py]
Goal: metrics from synthetic logs. No code.

1. Build small synthetic pre/post CSVs to yield known R_raw, R_anchor, mu, P_tau, deltas.
2. Verify metrics_summary.csv numeric equality.
"""

import unittest
import tempfile
import os
import csv
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.middleware.metrics import compute_metrics, write_metrics_summary, _compute_prompt_metrics
from src.middleware.schema import (
    DISTANCES_PRE_CSV_PATH, DISTANCES_POST_CSV_PATH, REPAIRS_CSV_PATH,
    DISTANCES_CSV_HEADERS, REPAIRS_CSV_HEADERS, DEFAULT_TAU
)

class TestMetricsComputation(unittest.TestCase):
    """Test metrics computation from synthetic data"""
    
    def setUp(self):
        """Set up test environment with temporary files"""
        self.test_dir = tempfile.mkdtemp()
        
        # Override CSV paths to use test directory
        self.original_pre_path = DISTANCES_PRE_CSV_PATH
        self.original_post_path = DISTANCES_POST_CSV_PATH
        self.original_repairs_path = REPAIRS_CSV_PATH
        
        # Create test CSV paths
        self.test_pre_path = os.path.join(self.test_dir, "distances_pre.csv")
        self.test_post_path = os.path.join(self.test_dir, "distances_post.csv")
        self.test_repairs_path = os.path.join(self.test_dir, "repairs.csv")
        
        # Patch the paths in the module
        import src.middleware.metrics as metrics_module
        metrics_module.DISTANCES_PRE_CSV_PATH = self.test_pre_path
        metrics_module.DISTANCES_POST_CSV_PATH = self.test_post_path
        metrics_module.REPAIRS_CSV_PATH = self.test_repairs_path
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir)
        
        # Restore original paths
        import src.middleware.metrics as metrics_module
        metrics_module.DISTANCES_PRE_CSV_PATH = self.original_pre_path
        metrics_module.DISTANCES_POST_CSV_PATH = self.original_post_path
        metrics_module.REPAIRS_CSV_PATH = self.original_repairs_path
    
    def test_perfect_repeatability_scenario(self):
        """Test metrics for perfect repeatability scenario"""
        # Create synthetic data: all samples identical
        pre_data = [
            {"run_id": "run1", "sample_id": "s1", "prompt_id": "test", "stage": "pre", 
             "signature": "sig1", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "prompt_id": "test", "stage": "pre", 
             "signature": "sig1", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run3", "sample_id": "s3", "prompt_id": "test", "stage": "pre", 
             "signature": "sig1", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
        ]
        
        post_data = [
            {"run_id": "run1", "sample_id": "s1", "prompt_id": "test", "stage": "post", 
             "signature": "sig1", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "prompt_id": "test", "stage": "post", 
             "signature": "sig1", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run3", "sample_id": "s3", "prompt_id": "test", "stage": "post", 
             "signature": "sig1", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
        ]
        
        repairs_data = [
            {"run_id": "run1", "sample_id": "s1", "before_signature": "sig1", 
             "after_signature": "sig1", "d_before": "0.0", "d_after": "0.0", 
             "steps": "0", "success": "True", "reason": "no_repair_needed", 
             "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "before_signature": "sig1", 
             "after_signature": "sig1", "d_before": "0.0", "d_after": "0.0", 
             "steps": "0", "success": "True", "reason": "no_repair_needed", 
             "timestamp": datetime.now().isoformat()},
            {"run_id": "run3", "sample_id": "s3", "before_signature": "sig1", 
             "after_signature": "sig1", "d_before": "0.0", "d_after": "0.0", 
             "steps": "0", "success": "True", "reason": "no_repair_needed", 
             "timestamp": datetime.now().isoformat()},
        ]
        
        # Write synthetic data
        self._write_csv_data(self.test_pre_path, DISTANCES_CSV_HEADERS, pre_data)
        self._write_csv_data(self.test_post_path, DISTANCES_CSV_HEADERS, post_data)
        self._write_csv_data(self.test_repairs_path, REPAIRS_CSV_HEADERS, repairs_data)
        
        # Compute metrics
        metrics = compute_metrics("test", DEFAULT_TAU)
        
        # Verify perfect repeatability
        self.assertIn("test", metrics)
        record = metrics["test"]
        
        self.assertEqual(record.N, 3)
        self.assertEqual(record.R_raw, 1.0)  # All signatures identical
        self.assertEqual(record.R_anchor, 1.0)  # All distances = 0
        self.assertEqual(record.mu_pre, 0.0)  # Mean distance = 0
        self.assertEqual(record.mu_post, 0.0)  # Mean distance = 0
        self.assertEqual(record.P_tau_pre, 1.0)  # All ≤ tau
        self.assertEqual(record.P_tau_post, 1.0)  # All ≤ tau
        self.assertEqual(record.rescue_rate, 0.0)  # No rescues needed
    
    def test_mixed_repeatability_scenario(self):
        """Test metrics for mixed repeatability scenario"""
        # Create synthetic data: some identical, some different
        pre_data = [
            {"run_id": "run1", "sample_id": "s1", "prompt_id": "test", "stage": "pre", 
             "signature": "sig1", "d": "0.5", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "prompt_id": "test", "stage": "pre", 
             "signature": "sig1", "d": "0.5", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run3", "sample_id": "s3", "prompt_id": "test", "stage": "pre", 
             "signature": "sig2", "d": "0.8", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run4", "sample_id": "s4", "prompt_id": "test", "stage": "pre", 
             "signature": "sig3", "d": "0.2", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
        ]
        
        post_data = [
            {"run_id": "run1", "sample_id": "s1", "prompt_id": "test", "stage": "post", 
             "signature": "canon_sig", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "prompt_id": "test", "stage": "post", 
             "signature": "canon_sig", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run3", "sample_id": "s3", "prompt_id": "test", "stage": "post", 
             "signature": "sig2", "d": "0.3", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run4", "sample_id": "s4", "prompt_id": "test", "stage": "post", 
             "signature": "canon_sig", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
        ]
        
        repairs_data = [
            {"run_id": "run1", "sample_id": "s1", "before_signature": "sig1", 
             "after_signature": "canon_sig", "d_before": "0.5", "d_after": "0.0", 
             "steps": "2", "success": "True", "reason": "repair_success", 
             "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "before_signature": "sig1", 
             "after_signature": "canon_sig", "d_before": "0.5", "d_after": "0.0", 
             "steps": "2", "success": "True", "reason": "repair_success", 
             "timestamp": datetime.now().isoformat()},
            {"run_id": "run3", "sample_id": "s3", "before_signature": "sig2", 
             "after_signature": "sig2", "d_before": "0.8", "d_after": "0.3", 
             "steps": "3", "success": "False", "reason": "repair_incomplete", 
             "timestamp": datetime.now().isoformat()},
            {"run_id": "run4", "sample_id": "s4", "before_signature": "sig3", 
             "after_signature": "canon_sig", "d_before": "0.2", "d_after": "0.0", 
             "steps": "1", "success": "True", "reason": "repair_success", 
             "timestamp": datetime.now().isoformat()},
        ]
        
        # Write synthetic data
        self._write_csv_data(self.test_pre_path, DISTANCES_CSV_HEADERS, pre_data)
        self._write_csv_data(self.test_post_path, DISTANCES_CSV_HEADERS, post_data)
        self._write_csv_data(self.test_repairs_path, REPAIRS_CSV_HEADERS, repairs_data)
        
        # Compute metrics
        metrics = compute_metrics("test", DEFAULT_TAU)
        
        # Verify computed metrics
        self.assertIn("test", metrics)
        record = metrics["test"]
        
        self.assertEqual(record.N, 4)
        self.assertEqual(record.R_raw, 0.5)  # 2/4 have sig1
        self.assertEqual(record.R_anchor, 0.75)  # 3/4 have d=0 post-repair
        self.assertAlmostEqual(record.mu_pre, 0.5, places=2)  # (0.5+0.5+0.8+0.2)/4
        self.assertAlmostEqual(record.mu_post, 0.075, places=2)  # (0+0+0.3+0)/4
        self.assertEqual(record.rescue_rate, 0.75)  # 3/4 went from d>0 to d=0
    
    def test_no_rescue_scenario(self):
        """Test metrics when no repairs are successful"""
        # Create synthetic data: repairs fail
        pre_data = [
            {"run_id": "run1", "sample_id": "s1", "prompt_id": "test", "stage": "pre", 
             "signature": "sig1", "d": "0.8", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "prompt_id": "test", "stage": "pre", 
             "signature": "sig2", "d": "0.9", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
        ]
        
        post_data = [
            {"run_id": "run1", "sample_id": "s1", "prompt_id": "test", "stage": "post", 
             "signature": "sig1", "d": "0.7", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "prompt_id": "test", "stage": "post", 
             "signature": "sig2", "d": "0.8", "compliant": "False", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
        ]
        
        repairs_data = [
            {"run_id": "run1", "sample_id": "s1", "before_signature": "sig1", 
             "after_signature": "sig1", "d_before": "0.8", "d_after": "0.7", 
             "steps": "3", "success": "False", "reason": "repair_incomplete", 
             "timestamp": datetime.now().isoformat()},
            {"run_id": "run2", "sample_id": "s2", "before_signature": "sig2", 
             "after_signature": "sig2", "d_before": "0.9", "d_after": "0.8", 
             "steps": "3", "success": "False", "reason": "repair_incomplete", 
             "timestamp": datetime.now().isoformat()},
        ]
        
        # Write synthetic data
        self._write_csv_data(self.test_pre_path, DISTANCES_CSV_HEADERS, pre_data)
        self._write_csv_data(self.test_post_path, DISTANCES_CSV_HEADERS, post_data)
        self._write_csv_data(self.test_repairs_path, REPAIRS_CSV_HEADERS, repairs_data)
        
        # Compute metrics
        metrics = compute_metrics("test", DEFAULT_TAU)
        
        # Verify metrics
        record = metrics["test"]
        
        self.assertEqual(record.N, 2)
        self.assertEqual(record.R_raw, 0.5)  # Each signature appears once
        self.assertEqual(record.R_anchor, 0.0)  # No d=0 post-repair
        self.assertEqual(record.rescue_rate, 0.0)  # No successful rescues
        self.assertLess(record.mu_post, record.mu_pre)  # Some improvement in mean distance
    
    def test_metrics_csv_output(self):
        """Test that metrics are correctly written to CSV"""
        # Create minimal synthetic data
        pre_data = [
            {"run_id": "run1", "sample_id": "s1", "prompt_id": "test", "stage": "pre", 
             "signature": "sig1", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
        ]
        
        post_data = [
            {"run_id": "run1", "sample_id": "s1", "prompt_id": "test", "stage": "post", 
             "signature": "sig1", "d": "0.0", "compliant": "True", 
             "normalization_version": "1.0", "timestamp": datetime.now().isoformat()},
        ]
        
        repairs_data = [
            {"run_id": "run1", "sample_id": "s1", "before_signature": "sig1", 
             "after_signature": "sig1", "d_before": "0.0", "d_after": "0.0", 
             "steps": "0", "success": "True", "reason": "no_repair_needed", 
             "timestamp": datetime.now().isoformat()},
        ]
        
        # Write synthetic data
        self._write_csv_data(self.test_pre_path, DISTANCES_CSV_HEADERS, pre_data)
        self._write_csv_data(self.test_post_path, DISTANCES_CSV_HEADERS, post_data)
        self._write_csv_data(self.test_repairs_path, REPAIRS_CSV_HEADERS, repairs_data)
        
        # Compute and write metrics
        metrics = compute_metrics("test", DEFAULT_TAU)
        
        # Override metrics CSV path for test
        test_metrics_path = os.path.join(self.test_dir, "metrics_summary.csv")
        import src.middleware.metrics as metrics_module
        original_metrics_path = metrics_module.METRICS_CSV_PATH
        metrics_module.METRICS_CSV_PATH = test_metrics_path
        
        try:
            write_metrics_summary(metrics)
            
            # Verify CSV was written correctly
            self.assertTrue(os.path.exists(test_metrics_path))
            
            # Read and verify content
            with open(test_metrics_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            self.assertEqual(len(rows), 1)
            row = rows[0]
            
            self.assertEqual(row["prompt_id"], "test")
            self.assertEqual(row["N"], "1")
            self.assertEqual(row["R_raw"], "1.0")
            self.assertEqual(row["R_anchor"], "1.0")
        
        finally:
            # Restore original path
            metrics_module.METRICS_CSV_PATH = original_metrics_path
    
    def _write_csv_data(self, path: str, headers: list, data: list):
        """Helper to write CSV data"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in data:
                # Ensure all headers are present
                complete_row = {header: row.get(header, "") for header in headers}
                writer.writerow(complete_row)

if __name__ == '__main__':
    unittest.main()
