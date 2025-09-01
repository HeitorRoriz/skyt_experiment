# src/matrix.py
"""
Experiment matrix management for SKYT pipeline
Handles experiment scheduling and status tracking
"""

import json
import os
from typing import Dict, Any, List, Optional
from .config import MODEL, TEMPERATURE, TARGET_RUNS_PER_PROMPT


class ExperimentMatrix:
    """Manages experiment matrix with status tracking"""
    
    def __init__(self, matrix_path: str = "outputs/experiment_matrix.json"):
        self.matrix_path = matrix_path
        self.experiments = self._load_matrix()
    
    def _load_matrix(self) -> List[Dict[str, Any]]:
        """Load experiment matrix from file or create default"""
        if os.path.exists(self.matrix_path):
            with open(self.matrix_path, 'r') as f:
                return json.load(f)
        else:
            return self._create_default_matrix()
    
    def _create_default_matrix(self) -> List[Dict[str, Any]]:
        """Create default experiment matrix"""
        # Load prompt templates
        templates_path = "contracts/templates.json"
        if os.path.exists(templates_path):
            with open(templates_path, 'r') as f:
                templates = json.load(f)
        else:
            templates = [{"id": "default", "prompt": "Generate fibonacci function"}]
        
        experiments = []
        temperatures = [0.0, 0.2]
        modes = ["with_contract", "no_contract"]
        
        for template in templates:
            for temp in temperatures:
                for mode in modes:
                    exp = {
                        "prompt_id": template["id"],
                        "temperature": temp,
                        "mode": mode,
                        "model": MODEL,
                        "status": "pending",
                        "attempts": 0,
                        "last_error": None,
                        "completed_runs": 0,
                        "target_runs": TARGET_RUNS_PER_PROMPT
                    }
                    experiments.append(exp)
        
        return experiments
    
    def save_matrix(self):
        """Save experiment matrix to file"""
        os.makedirs(os.path.dirname(self.matrix_path), exist_ok=True)
        with open(self.matrix_path, 'w') as f:
            json.dump(self.experiments, f, indent=2)
    
    def get_next_experiment(self) -> Optional[Dict[str, Any]]:
        """Get next pending experiment"""
        for exp in self.experiments:
            if exp["status"] == "pending" or (exp["status"] == "running" and exp["completed_runs"] < exp["target_runs"]):
                return exp
        return None
    
    def mark_experiment_running(self, prompt_id: str, temperature: float, mode: str):
        """Mark experiment as running"""
        exp = self._find_experiment(prompt_id, temperature, mode)
        if exp:
            exp["status"] = "running"
            self.save_matrix()
    
    def mark_experiment_completed(self, prompt_id: str, temperature: float, mode: str):
        """Mark experiment as completed"""
        exp = self._find_experiment(prompt_id, temperature, mode)
        if exp:
            exp["completed_runs"] += 1
            if exp["completed_runs"] >= exp["target_runs"]:
                exp["status"] = "completed"
            self.save_matrix()
    
    def mark_experiment_failed(self, prompt_id: str, temperature: float, mode: str, error: str):
        """Mark experiment as failed"""
        exp = self._find_experiment(prompt_id, temperature, mode)
        if exp:
            exp["status"] = "failed"
            exp["last_error"] = error
            exp["attempts"] += 1
            self.save_matrix()
    
    def _find_experiment(self, prompt_id: str, temperature: float, mode: str) -> Optional[Dict[str, Any]]:
        """Find experiment by parameters"""
        for exp in self.experiments:
            if (exp["prompt_id"] == prompt_id and 
                exp["temperature"] == temperature and 
                exp["mode"] == mode):
                return exp
        return None
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get summary of experiment statuses"""
        summary = {"pending": 0, "running": 0, "completed": 0, "failed": 0}
        for exp in self.experiments:
            summary[exp["status"]] += 1
        return summary
