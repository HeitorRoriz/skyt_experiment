"""
Security Analyzer - Enhanced security and side effect analysis using bandit

Provides comprehensive security scanning to complement AST-based side effect detection.
Follows Single Responsibility Principle: only analyzes security and side effects.
"""

import tempfile
import subprocess
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Check if bandit is available
try:
    import sys
    result = subprocess.run(
        [sys.executable, '-m', 'bandit', '--version'],
        capture_output=True,
        text=True,
        timeout=1
    )
    BANDIT_AVAILABLE = result.returncode == 0
except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
    BANDIT_AVAILABLE = False


class SecurityAnalyzer:
    """
    Analyzes code security and side effects using bandit.
    
    Provides:
    - Security vulnerability detection
    - I/O operation detection
    - Network call detection
    - Unsafe operation detection (eval, exec, etc.)
    - Comprehensive side effect profiling
    
    Design principles:
    - Single Responsibility: Only security/side effect analysis
    - Fail gracefully: Returns None if bandit unavailable
    - No side effects: Pure function, no state mutation
    """
    
    def __init__(self):
        """Initialize security analyzer and verify bandit availability"""
        self.available = BANDIT_AVAILABLE
        if not self.available:
            logger.warning(
                "bandit not available. Install with: pip install bandit"
            )
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Analyze code security and side effects using bandit.
        
        Args:
            code: Python source code string
            
        Returns:
            Dictionary with security analysis results
            
        Example:
            >>> analyzer = SecurityAnalyzer()
            >>> result = analyzer.analyze("import os; os.system('ls')")
            >>> result['has_unsafe_operations']
            True
        """
        if not self.available:
            return self._unavailable_result()
        
        try:
            return self._scan_security(code)
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return self._error_result(str(e))
    
    def _scan_security(self, code: str) -> Dict[str, Any]:
        """
        Run bandit security scanner.
        
        Detects:
        - File I/O operations
        - Network calls (requests, urllib, socket)
        - System calls (os.system, subprocess)
        - Eval/exec usage
        - Hardcoded secrets
        - SQL injection risks
        - Shell injection risks
        - And more...
        """
        # Write code to temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Run bandit with JSON output
            import sys
            result = subprocess.run(
                [
                    sys.executable, '-m', 'bandit',
                    '-f', 'json',
                    '-ll',  # Only report low severity and above
                    temp_path
                ],
                capture_output=True,
                text=True,
                timeout=5.0
            )
            
            # Parse JSON output
            if result.stdout:
                try:
                    report = json.loads(result.stdout)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse bandit JSON output")
                    return self._empty_result()
            else:
                return self._empty_result()
            
            # Extract and categorize issues
            issues = report.get("results", [])
            
            return {
                **self._categorize_issues(issues),
                **self._compute_metrics(issues),
            }
            
        except subprocess.TimeoutExpired:
            logger.warning("bandit timeout")
            return self._error_result("timeout")
        finally:
            # Clean up temp file
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass
    
    def _categorize_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Categorize security issues by type.
        
        Categories:
        - I/O operations: File, network, system
        - Unsafe operations: eval, exec, compile
        - Security risks: Hardcoded passwords, SQL injection, etc.
        """
        io_operations = []
        network_calls = []
        system_calls = []
        unsafe_operations = []
        security_risks = []
        
        for issue in issues:
            test_id = issue.get("test_id", "")
            issue_text = issue.get("issue_text", "")
            
            # Categorize by test ID
            # File I/O
            if test_id in ["B101", "B102", "B103", "B108", "B110"]:
                io_operations.append({
                    "type": "file_io",
                    "test_id": test_id,
                    "message": issue_text,
                    "line": issue.get("line_number"),
                    "severity": issue.get("issue_severity"),
                })
            
            # Network operations
            elif test_id in ["B310", "B320", "B321"]:
                network_calls.append({
                    "type": "network",
                    "test_id": test_id,
                    "message": issue_text,
                    "line": issue.get("line_number"),
                    "severity": issue.get("issue_severity"),
                })
            
            # System/subprocess calls
            elif test_id in ["B602", "B603", "B604", "B605", "B606", "B607"]:
                system_calls.append({
                    "type": "system_call",
                    "test_id": test_id,
                    "message": issue_text,
                    "line": issue.get("line_number"),
                    "severity": issue.get("issue_severity"),
                })
            
            # Unsafe operations (eval, exec, compile, __import__)
            elif test_id in ["B307", "B102"]:
                unsafe_operations.append({
                    "type": "unsafe_operation",
                    "test_id": test_id,
                    "message": issue_text,
                    "line": issue.get("line_number"),
                    "severity": issue.get("issue_severity"),
                })
            
            # Security risks
            else:
                security_risks.append({
                    "test_id": test_id,
                    "message": issue_text,
                    "line": issue.get("line_number"),
                    "severity": issue.get("issue_severity"),
                    "confidence": issue.get("issue_confidence"),
                })
        
        return {
            "io_operations": io_operations,
            "network_calls": network_calls,
            "system_calls": system_calls,
            "unsafe_operations": unsafe_operations,
            "security_risks": security_risks,
        }
    
    def _compute_metrics(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute aggregate security metrics.
        """
        # Count by severity
        severity_counts = {
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }
        
        for issue in issues:
            severity = issue.get("issue_severity", "LOW")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Determine purity level
        has_side_effects = len(issues) > 0
        
        if not has_side_effects:
            purity_level = "pure"
        elif severity_counts["HIGH"] > 0:
            purity_level = "unsafe"
        elif severity_counts["MEDIUM"] > 0:
            purity_level = "impure"
        else:
            purity_level = "mostly_pure"
        
        return {
            "total_issues": len(issues),
            "high_severity_count": severity_counts["HIGH"],
            "medium_severity_count": severity_counts["MEDIUM"],
            "low_severity_count": severity_counts["LOW"],
            "has_side_effects": has_side_effects,
            "purity_level": purity_level,
            "security_score": self._compute_security_score(severity_counts, len(issues)),
        }
    
    def _compute_security_score(self, severity_counts: Dict[str, int], total: int) -> float:
        """
        Compute security score (0.0 to 1.0).
        
        1.0 = No issues (perfectly secure/pure)
        0.0 = Many high-severity issues
        
        Formula: 1.0 - (weighted_issues / max_possible_weight)
        """
        if total == 0:
            return 1.0
        
        # Weight by severity
        weighted_sum = (
            severity_counts["HIGH"] * 3.0 +
            severity_counts["MEDIUM"] * 2.0 +
            severity_counts["LOW"] * 1.0
        )
        
        # Normalize (assume max 10 high-severity issues as worst case)
        max_weight = 10 * 3.0
        
        score = max(0.0, 1.0 - (weighted_sum / max_weight))
        return round(score, 3)
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return result when no issues found"""
        return {
            "io_operations": [],
            "network_calls": [],
            "system_calls": [],
            "unsafe_operations": [],
            "security_risks": [],
            "total_issues": 0,
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "low_severity_count": 0,
            "has_side_effects": False,
            "purity_level": "pure",
            "security_score": 1.0,
        }
    
    def _unavailable_result(self) -> Dict[str, Any]:
        """Return result when bandit is not available"""
        return {
            "bandit_available": False,
            "io_operations": [],
            "network_calls": [],
            "system_calls": [],
            "unsafe_operations": [],
            "security_risks": [],
            "total_issues": 0,
            "has_side_effects": None,
            "purity_level": None,
            "security_score": None,
        }
    
    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Return result when analysis fails"""
        return {
            "bandit_available": True,
            "analysis_error": error_msg,
            "io_operations": [],
            "network_calls": [],
            "system_calls": [],
            "unsafe_operations": [],
            "security_risks": [],
            "total_issues": 0,
            "has_side_effects": None,
            "purity_level": None,
            "security_score": None,
        }
