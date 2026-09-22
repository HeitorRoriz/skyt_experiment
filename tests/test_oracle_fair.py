"""Oracle-split Extra-survival and Base-cache helpers. No Docker, no API."""

from skyt.oracle_fair import raw_split_metrics, replay_cached_record
from skyt.oracle_split_posthoc import extra_survival_rate
from src.code_transformer import CodeTransformer


def test_extra_survival_skips_splits_with_no_base_passer():
    splits = [
        {"pre_n_base_certified": 10, "pre_n_plus_certified": 8},
        {"pre_n_base_certified": 0, "pre_n_plus_certified": 0},
        {"pre_n_base_certified": 5, "pre_n_plus_certified": 5},
    ]
    assert extra_survival_rate(splits, "pre") == (0.8 + 1.0) / 2


def test_replay_cached_base_passer_that_fails_extra():
    record = {
        "stitched_code": "def add(a, b):\n    return a + b\n",
        "oracle": {"base_passed": True, "plus_passed": False},
    }
    metrics = replay_cached_record(record)
    assert metrics["base_pass"] == 1.0
    assert metrics["plus_pass"] == 0.0
    assert metrics["extra_survival"] == 0.0
    assert metrics["plus_same_at_2"] == 0.0
    assert metrics["base_pass_extra_fail"] == 1.0


def test_raw_split_extra_survival_from_counts():
    split = {
        "pre_n_base_certified": 10,
        "pre_n_plus_certified": 7,
        "pre_base_pass": 1.0,
        "pre_plus_pass": 0.7,
        "pre_plus_same_at_2": 0.4,
        "pre_same_at_2": 0.5,
    }
    metrics = raw_split_metrics(split)
    assert metrics["extra_survival"] == 0.7
    assert metrics["hit"] is False


def test_live_transformer_default_max_level_is_three():
    class _Canon:
        pass

    transformer = CodeTransformer(_Canon())
    assert transformer.max_transformation_level == 3


def test_l1_is_raw_and_l2_needs_docker():
    from skyt.level_ablation import run_level

    try:
        run_level(1)
        raise AssertionError("L1 should exit")
    except SystemExit as exc:
        assert "Raw" in str(exc)
    try:
        run_level(2)
        raise AssertionError("L2 should exit")
    except SystemExit as exc:
        assert "Docker" in str(exc)
