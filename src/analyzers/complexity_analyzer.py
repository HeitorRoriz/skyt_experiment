"""
Complexity Analyzer - Enhanced complexity metrics using radon

Provides compiler-grade complexity analysis to complement AST-based heuristics.
Follows Single Responsibility Principle: only analyzes complexity.
"""

from typing import Dict, Any, Optional
import logging

# Lazy import radon to avoid dependency if not needed
try:
    from radon.complexity import cc_visit, average_complexity
    from radon.metrics import mi_visit, h_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False

logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """
    Analyzes code complexity using radon metrics.
    
    Provides:
    - Cyclomatic complexity (McCabe metric, CFG-based)
    - Maintainability index
    - Halstead metrics
    
    Design principles:
    - Single Responsibility: Only complexity analysis
    - Fail gracefully: Returns None if radon unavailable
    - No side effects: Pure function, no state mutation
    """
    
    def __init__(self):
        """Initialize analyzer and check radon availability"""
        self.available = RADON_AVAILABLE
        if not self.available:
            logger.warning(
                "radon not available. Install with: pip install radon"
            )
    
    def analyze(self, code: str) -> Dict[str, Any]:
        """
        Analyze code complexity using radon.
        
        Args:
            code: Python source code string
            
        Returns:
            Dictionary with complexity metrics, or empty dict if radon unavailable
            
        Example:
            >>> analyzer = ComplexityAnalyzer()
            >>> result = analyzer.analyze("def f(n): return n")
            >>> result['cyclomatic_complexity']
            1
        """
        if not self.available:
            return self._unavailable_result()
        
        try:
            return {
                **self._analyze_cyclomatic(code),
                **self._analyze_maintainability(code),
                **self._analyze_halstead(code),
            }
        except Exception as e:
            logger.error(f"Complexity analysis failed: {e}")
            return self._error_result(str(e))
    
    def _analyze_cyclomatic(self, code: str) -> Dict[str, Any]:
        """
        Cyclomatic complexity (McCabe metric).
        
        Based on Control Flow Graph (CFG):
        - M = E - N + 2P
        - E = edges, N = nodes, P = connected components
        
        Interpretation:
        - 1-10: Simple, low risk (Rank A-B)
        - 11-20: Moderate complexity (Rank C)
        - 21-50: Complex, high risk (Rank D-E)
        - 50+: Untestable, very high risk (Rank F)
        """
        results = cc_visit(code)
        
        if not results:
            return {
                "cyclomatic_complexity": 0,
                "complexity_rank": "A",
                "average_complexity": 0.0,
            }
        
        # Get the main function's complexity (first result)
        main_result = results[0]
        complexity_value = main_result.complexity
        
        # Calculate rank from complexity
        # Based on radon's ranking: A (1-5), B (6-10), C (11-20), D (21-50), E (51-100), F (100+)
        if complexity_value <= 5:
            rank = "A"
        elif complexity_value <= 10:
            rank = "B"
        elif complexity_value <= 20:
            rank = "C"
        elif complexity_value <= 50:
            rank = "D"
        elif complexity_value <= 100:
            rank = "E"
        else:
            rank = "F"
        
        return {
            "cyclomatic_complexity": complexity_value,
            "complexity_rank": rank,
            "average_complexity": average_complexity(results),
        }
    
    def _analyze_maintainability(self, code: str) -> Dict[str, Any]:
        """
        Maintainability Index.
        
        Formula (Microsoft variant):
        - MI = 171 - 5.2*ln(HV) - 0.23*CC - 16.2*ln(LOC)
        - HV = Halstead Volume
        - CC = Cyclomatic Complexity
        - LOC = Lines of Code
        
        Interpretation:
        - 0-9: Unmaintainable
        - 10-19: Hard to maintain
        - 20-100: Maintainable
        """
        mi = mi_visit(code, multi=True)
        
        return {
            "maintainability_index": mi if mi else 100.0,
        }
    
    def _analyze_halstead(self, code: str) -> Dict[str, Any]:
        """
        Halstead complexity metrics.
        
        Based on operators and operands:
        - Volume: Information content
        - Difficulty: How hard to understand
        - Effort: Mental effort to understand
        - Bugs: Estimated bugs (Effort / 3000)
        
        Developed by Maurice Halstead (1977).
        """
        h = h_visit(code)
        
        if not h or not h.total:
            return {
                "halstead_difficulty": 0.0,
                "halstead_effort": 0.0,
                "halstead_volume": 0.0,
                "halstead_bugs": 0.0,
            }
        
        return {
            "halstead_difficulty": h.total.difficulty,
            "halstead_effort": h.total.effort,
            "halstead_volume": h.total.volume,
            "halstead_bugs": h.total.bugs,
        }
    
    def _unavailable_result(self) -> Dict[str, Any]:
        """Return result when radon is not available"""
        return {
            "radon_available": False,
            "cyclomatic_complexity": None,
            "complexity_rank": None,
            "maintainability_index": None,
            "halstead_difficulty": None,
            "halstead_effort": None,
            "halstead_volume": None,
            "halstead_bugs": None,
        }
    
    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """Return result when analysis fails"""
        return {
            "radon_available": True,
            "analysis_error": error_msg,
            "cyclomatic_complexity": None,
            "complexity_rank": None,
            "maintainability_index": None,
            "halstead_difficulty": None,
            "halstead_effort": None,
            "halstead_volume": None,
            "halstead_bugs": None,
        }
