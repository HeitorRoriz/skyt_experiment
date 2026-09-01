"""Regression tests for final-output oracle validation."""

from agents.enhanced_transformer import EnhancedCodeTransformer
from src.metrics import ComprehensiveMetrics


class FakeOracle:
    def __init__(self, passing_code):
        self.passing_code = passing_code
        self.calls = []

    def run_oracle_tests(self, code, contract):
        self.calls.append((code, contract))
        return {
            "passed": code == self.passing_code,
            "test_results": [],
        }


def transformer_without_initialization():
    return EnhancedCodeTransformer.__new__(EnhancedCodeTransformer)


def test_behavior_breaking_transformation_is_rolled_back():
    original = "def f(x):\n    return x\n"
    changed = "def f(x):\n    return x + 1\n"
    oracle = FakeOracle(original)
    result = transformer_without_initialization()._validate_final_output(
        {
            "success": True,
            "transformed_code": changed,
            "transformations_applied": ["change-return"],
            "final_distance": 0.0,
        },
        original,
        {"algorithm_family": "test"},
        oracle,
    )

    assert result["success"] is False
    assert result["rolled_back"] is True
    assert result["transformed_code"] == original
    assert result["attempted_transformed_code"] == changed
    assert result["attempted_post_oracle_result"]["passed"] is False
    assert result["post_oracle_result"]["passed"] is True


def test_passing_transformation_is_persisted_with_oracle_evidence():
    original = "def f(x):\n    return x\n"
    changed = "def f(x):\n    return int(x)\n"
    oracle = FakeOracle(changed)
    result = transformer_without_initialization()._validate_final_output(
        {
            "success": True,
            "transformed_code": changed,
            "transformations_applied": ["normalize"],
            "final_distance": 0.0,
        },
        original,
        {"algorithm_family": "test"},
        oracle,
    )

    assert result["success"] is True
    assert result["rolled_back"] is False
    assert result["transformed_code"] == changed
    assert result["post_oracle_result"]["passed"] is True
    assert result["oracle_validation_performed"] is True


class MarkerOracle:
    def run_oracle_tests(self, code, contract):
        passed = "return True" in code
        return {
            "passed": passed,
            "test_results": [{"passed": passed}],
        }


def test_metrics_persist_separate_pre_and_post_oracle_results():
    metrics = ComprehensiveMetrics(canon_system=None)
    metrics.oracle_system = MarkerOracle()
    raw = [
        "def f():\n    return True\n",
        "def f():\n    return False\n",
    ]
    repaired = [
        "def f():\n    return True\n",
        "def f():\n    return True\n",
    ]

    result = metrics.calculate_comprehensive_metrics(
        raw, repaired, {"algorithm_family": "test"}, "test"
    )

    assert result["behavioral_stats"]["pass_rate"] == 0.5
    assert result["behavioral_stats_post"]["pass_rate"] == 1.0
    assert result["R_behavioral_post"] == 1.0
    assert len(result["behavioral_stats_post"]["oracle_results"]) == 2
