#!/usr/bin/env python3
"""
LLM Diversity Analyzer
Analyzes the diversity of LLM outputs to detect artificial uniformity
"""

import json
import sys
from typing import List, Dict, Any
from collections import Counter


class LLMDiversityAnalyzer:
    """Analyzes diversity patterns in LLM outputs"""
    
    def __init__(self, results_file: str):
        with open(results_file, 'r') as f:
            self.data = json.load(f)
        
        self.raw_outputs = self.data.get("raw_outputs", [])
        self.temperature = self.data.get("temperature", 0.0)
        
    def analyze_structural_diversity(self) -> Dict[str, Any]:
        """Analyze structural diversity patterns"""
        
        print(f"🔍 ANALYZING STRUCTURAL DIVERSITY (Temperature: {self.temperature})")
        print("=" * 60)
        
        # Extract structural patterns
        patterns = {
            "error_handling": [],
            "boundary_conditions": [],
            "variable_names": [],
            "loop_patterns": [],
            "whitespace_patterns": []
        }
        
        for i, output in enumerate(self.raw_outputs):
            print(f"\n--- Run {i+1} ---")
            print(f"Code: {repr(output[:100])}...")
            
            # Error handling patterns
            if "raise ValueError" in output or "raise Exception" in output:
                patterns["error_handling"].append("raise")
            elif "if n < 0:" in output:
                patterns["error_handling"].append("negative_check")
            else:
                patterns["error_handling"].append("no_error_handling")
            
            # Boundary conditions
            if "if n <= 0:" in output:
                patterns["boundary_conditions"].append("n_lte_0")
            elif "if n < 0:" in output:
                patterns["boundary_conditions"].append("n_lt_0")
            elif "if n < 1:" in output:
                patterns["boundary_conditions"].append("n_lt_1")
            else:
                patterns["boundary_conditions"].append("other")
            
            # Variable names
            if "fib1, fib2" in output or "fib_1, fib_2" in output:
                patterns["variable_names"].append("fib_vars")
            elif "first, second" in output:
                patterns["variable_names"].append("first_second")
            elif "a, b" in output:
                patterns["variable_names"].append("a_b")
            else:
                patterns["variable_names"].append("other")
            
            # Loop patterns
            if "for _ in range" in output:
                patterns["loop_patterns"].append("underscore_range")
            elif "for i in range" in output:
                patterns["loop_patterns"].append("i_range")
            elif "for iteration in range" in output:
                patterns["loop_patterns"].append("iteration_range")
            else:
                patterns["loop_patterns"].append("other")
            
            # Whitespace patterns (count newlines)
            newline_count = output.count('\n')
            if newline_count <= 8:
                patterns["whitespace_patterns"].append("compact")
            elif newline_count <= 12:
                patterns["whitespace_patterns"].append("normal")
            else:
                patterns["whitespace_patterns"].append("verbose")
        
        return patterns
    
    def calculate_diversity_metrics(self, patterns: Dict[str, List[str]]) -> Dict[str, float]:
        """Calculate diversity metrics for each pattern type"""
        
        metrics = {}
        
        for pattern_type, values in patterns.items():
            counter = Counter(values)
            total = len(values)
            
            # Calculate entropy (diversity measure)
            entropy = 0.0
            for count in counter.values():
                if count > 0:
                    p = count / total
                    entropy -= p * (p.bit_length() - 1) if p > 0 else 0
            
            # Normalize entropy (0 = no diversity, 1 = maximum diversity)
            max_entropy = (len(counter).bit_length() - 1) if len(counter) > 1 else 0
            normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
            
            # Calculate uniqueness ratio
            unique_ratio = len(counter) / total
            
            metrics[pattern_type] = {
                "entropy": entropy,
                "normalized_entropy": normalized_entropy,
                "unique_ratio": unique_ratio,
                "unique_count": len(counter),
                "total_count": total,
                "distribution": dict(counter)
            }
        
        return metrics
    
    def detect_suspicious_patterns(self, metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """Detect patterns that suggest artificial uniformity"""
        
        suspicious = []
        
        for pattern_type, metric in metrics.items():
            normalized_entropy = metric["normalized_entropy"]
            unique_ratio = metric["unique_ratio"]
            
            # For high temperature (>1.0), we expect high diversity
            if self.temperature > 1.0:
                if normalized_entropy < 0.3:
                    suspicious.append(f"{pattern_type}: Very low entropy ({normalized_entropy:.2f}) for temp {self.temperature}")
                
                if unique_ratio < 0.4:
                    suspicious.append(f"{pattern_type}: Very low uniqueness ({unique_ratio:.2f}) for temp {self.temperature}")
            
            # Check for extreme uniformity (red flag regardless of temperature)
            if unique_ratio < 0.2:
                suspicious.append(f"{pattern_type}: Extreme uniformity - only {metric['unique_count']}/{metric['total_count']} unique patterns")
        
        return suspicious
    
    def compare_with_expected_diversity(self, temperature: float) -> Dict[str, str]:
        """Compare observed diversity with expected diversity for given temperature"""
        
        expected_ranges = {
            0.0: {"entropy": (0.0, 0.2), "uniqueness": (0.1, 0.3)},
            0.5: {"entropy": (0.2, 0.5), "uniqueness": (0.3, 0.6)},
            1.0: {"entropy": (0.4, 0.7), "uniqueness": (0.5, 0.8)},
            1.5: {"entropy": (0.6, 0.9), "uniqueness": (0.7, 1.0)},
            2.0: {"entropy": (0.7, 1.0), "uniqueness": (0.8, 1.0)}
        }
        
        # Find closest temperature range
        closest_temp = min(expected_ranges.keys(), key=lambda x: abs(x - temperature))
        expected = expected_ranges[closest_temp]
        
        return {
            "expected_entropy_range": expected["entropy"],
            "expected_uniqueness_range": expected["uniqueness"],
            "temperature_reference": closest_temp
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive diversity analysis report"""
        
        print(f"\n📊 LLM DIVERSITY ANALYSIS REPORT")
        print(f"Temperature: {self.temperature}")
        print(f"Total Outputs: {len(self.raw_outputs)}")
        print("=" * 60)
        
        # Analyze patterns
        patterns = self.analyze_structural_diversity()
        metrics = self.calculate_diversity_metrics(patterns)
        suspicious = self.detect_suspicious_patterns(metrics)
        expected = self.compare_with_expected_diversity(self.temperature)
        
        # Print detailed metrics
        print(f"\n📈 DIVERSITY METRICS:")
        for pattern_type, metric in metrics.items():
            print(f"\n{pattern_type.upper()}:")
            print(f"  Entropy: {metric['entropy']:.3f} (normalized: {metric['normalized_entropy']:.3f})")
            print(f"  Uniqueness: {metric['unique_ratio']:.3f} ({metric['unique_count']}/{metric['total_count']})")
            print(f"  Distribution: {metric['distribution']}")
        
        # Print expected vs actual
        print(f"\n🎯 EXPECTED VS ACTUAL (for temp {expected['temperature_reference']}):")
        avg_entropy = sum(m["normalized_entropy"] for m in metrics.values()) / len(metrics)
        avg_uniqueness = sum(m["unique_ratio"] for m in metrics.values()) / len(metrics)
        
        print(f"  Expected Entropy: {expected['expected_entropy_range']}")
        print(f"  Actual Entropy: {avg_entropy:.3f}")
        print(f"  Expected Uniqueness: {expected['expected_uniqueness_range']}")
        print(f"  Actual Uniqueness: {avg_uniqueness:.3f}")
        
        # Print suspicious patterns
        if suspicious:
            print(f"\n🚨 SUSPICIOUS PATTERNS DETECTED:")
            for issue in suspicious:
                print(f"  ⚠️ {issue}")
        else:
            print(f"\n✅ No suspicious uniformity patterns detected")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if len(suspicious) >= 3:
            print("❌ HIGHLY SUSPICIOUS - Artificial uniformity likely")
        elif len(suspicious) >= 1:
            print("⚠️ MODERATELY SUSPICIOUS - Some uniformity concerns")
        else:
            print("✅ DIVERSITY APPEARS NORMAL")
        
        return {
            "temperature": self.temperature,
            "total_outputs": len(self.raw_outputs),
            "patterns": patterns,
            "metrics": metrics,
            "suspicious_patterns": suspicious,
            "expected_ranges": expected,
            "avg_entropy": avg_entropy,
            "avg_uniqueness": avg_uniqueness,
            "assessment": "suspicious" if len(suspicious) >= 1 else "normal"
        }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python llm_diversity_analyzer.py <results_file.json>")
        sys.exit(1)
    
    analyzer = LLMDiversityAnalyzer(sys.argv[1])
    report = analyzer.generate_report()
    
    # Save report
    output_file = "diversity_analysis_report.json"
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {output_file}")
