"""Held-out split nesting and robustness helpers. No Docker, no API."""

from skyt.humaneval_heldout import balanced_splits_ordered, heldout_splits
from skyt.heldout_robust import b_robustness_table, post_fingerprint_from_persist

SEED = 20260723


def test_ordered_prefix_matches_heldout_split_set():
    for b in (20, 50, 100):
        paper = set(heldout_splits(20, 10, b, SEED))
        ordered = set(balanced_splits_ordered(20, 10, b, SEED))
        assert paper == ordered


def test_larger_b_is_superset():
    small = set(balanced_splits_ordered(20, 10, 20, SEED))
    large = set(balanced_splits_ordered(20, 10, 50, SEED))
    assert small.issubset(large)
    assert len(large) == 50


def test_b_table_uses_nested_prefix():
    rows = [
        {
            "task_id": "HumanEval/0",
            "splits": [
                {"pre_same_at_2": 0.4, "post_same_at_2": 0.8},
                {"pre_same_at_2": 0.5, "post_same_at_2": 0.9},
            ],
        }
    ]
    table = b_robustness_table(rows, targets=(1, 2, 5))
    assert table[0]["B"] == 1
    assert table[0]["n_configs"] == 1
    assert table[1]["n_configs"] == 1
    assert table[2]["n_configs"] == 0
    assert table[0]["delta_same_at_2"]["mean"] == 0.4


def test_post_fingerprint_from_persisted_codes():
    rows = [
        {
            "task_id": "HumanEval/0",
            "model": "gpt-4o-mini",
            "temperature": 0.0,
            "splits": [
                {
                    "test_codes": [
                        "def add(a, b):\n    return a + b\n",
                        "def add(a, b):\n    return a + b\n",
                    ],
                    "test_plus": [True, True],
                }
            ],
        }
    ]
    payload = post_fingerprint_from_persist(rows)
    assert payload["n_configs_with_persisted_programs"] == 1
    sameeval = payload["slices"]["sameeval_v2"]["all"]
    assert sameeval["mean"] == 1.0
