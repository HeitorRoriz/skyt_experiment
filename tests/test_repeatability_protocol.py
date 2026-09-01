"""Tests for the frozen FSE structural-repeatability protocol."""

import json
import hashlib
import os
import subprocess
import sys

import pytest

from src.foundational_properties import FoundationalProperties
from src.repeatability_protocol import (
    analyze_repeatability,
    build_distance_matrix,
    cluster_bootstrap_mean,
    equivalence_classes,
    repeated_balanced_cv,
    select_certified_consensus,
)
from gate0_pairwise_analysis import analyze_pass, derive_certification_mask


def test_dependency_extraction_is_stable_across_hash_seeds():
    script = """
import json
from src.foundational_properties import FoundationalProperties
code = 'def f(a, b, c):\\n    result = a + b + c\\n    return result\\n'
props = FoundationalProperties().extract_all_properties(code)
print(json.dumps(props['data_dependency_graph']['dependencies'], sort_keys=True))
"""
    outputs = []
    for seed in ("1", "987654"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-c", script],
                cwd=os.path.dirname(os.path.dirname(__file__)),
                env=env,
                text=True,
            ).strip()
        )

    assert outputs[0] == outputs[1]
    assert json.loads(outputs[0])["result"] == ["a", "b", "c"]


def test_legacy_dependency_lists_are_normalized_without_mutation():
    legacy = {
        "data_dependency_graph": {
            "dependencies": {"result": ["z", "a", "m"]},
            "assignments": {},
        }
    }
    normalized = FoundationalProperties.normalize_properties(legacy)

    assert normalized["data_dependency_graph"]["dependencies"]["result"] == [
        "a", "m", "z"
    ]
    assert legacy["data_dependency_graph"]["dependencies"]["result"] == [
        "z", "a", "m"
    ]


def test_distance_to_legacy_properties_ignores_serialization_order():
    fp = FoundationalProperties()
    left = fp.extract_all_properties(
        "def f(a, b):\n    result = a + b\n    return result\n"
    )
    right = json.loads(json.dumps(left))
    dependencies = right["data_dependency_graph"]["dependencies"]["result"]
    right["data_dependency_graph"]["dependencies"]["result"] = list(
        reversed(dependencies)
    )

    assert fp.calculate_distance(left, right) == pytest.approx(0.0)


def test_invalid_outputs_remain_in_end_to_end_denominator():
    matrix = [
        [0.0, 0.0, 0.5, None],
        [0.0, 0.0, 0.5, None],
        [0.5, 0.5, 0.0, None],
        [None, None, None, None],
    ]
    result = analyze_repeatability(
        matrix,
        valid_mask=[True, True, True, False],
        certified_mask=[True, True, True, False],
        tie_break_keys=["a", "b", "c", "invalid"],
    )

    assert result["n_total"] == 4
    assert result["n_valid"] == 3
    assert result["n_certified"] == 3
    assert result["pairwise_exact_match_end_to_end"] == pytest.approx(1 / 6)
    assert result["pairwise_exact_match_certified"] == pytest.approx(1 / 3)
    assert result["pairwise_exact_match_valid"] == pytest.approx(1 / 3)
    assert result["certified_modal_mass"] == pytest.approx(2 / 4)
    assert result["certified_modal_share"] == pytest.approx(2 / 3)
    assert result["pairwise_distance_valid_mean"] == pytest.approx(1 / 3)


def test_certification_must_be_subset_of_structural_validity():
    with pytest.raises(ValueError, match="Certified outputs"):
        analyze_repeatability(
            [[0.0, None], [None, None]],
            valid_mask=[True, False],
            certified_mask=[True, True],
            tie_break_keys=["a", "b"],
        )


def test_non_transitive_zero_relation_is_rejected():
    matrix = [
        [0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
    ]
    with pytest.raises(ValueError, match="not transitive"):
        equivalence_classes(matrix, [0, 1, 2])


@pytest.mark.parametrize("bad_value", [-0.1, float("nan")])
def test_invalid_distance_values_are_rejected(bad_value):
    matrix = [[0.0, bad_value], [bad_value, 0.0]]
    with pytest.raises(ValueError, match="Invalid distance"):
        analyze_repeatability(
            matrix,
            valid_mask=[True, True],
            certified_mask=[True, True],
            tie_break_keys=["a", "b"],
        )


def test_missing_distance_between_valid_outputs_is_rejected():
    with pytest.raises(ValueError, match="no defined distance"):
        analyze_repeatability(
            [[0.0, None], [None, 0.0]],
            valid_mask=[True, True],
            certified_mask=[True, True],
            tie_break_keys=["a", "b"],
        )


def test_consensus_uses_medoid_across_tied_modal_classes():
    matrix = [
        [0.0, 0.0, 0.8, 0.8, 0.1],
        [0.0, 0.0, 0.8, 0.8, 0.1],
        [0.8, 0.8, 0.0, 0.0, 0.9],
        [0.8, 0.8, 0.0, 0.0, 0.9],
        [0.1, 0.1, 0.9, 0.9, 0.0],
    ]
    selected = select_certified_consensus(
        matrix, range(5), ["a0", "a1", "b0", "b1", "c"]
    )

    assert selected["class_indices"] == [0, 1]
    assert selected["index"] == 0


def test_consensus_final_tie_break_is_lexical():
    matrix = [
        [0.0, 0.0, 0.5, 0.5],
        [0.0, 0.0, 0.5, 0.5],
        [0.5, 0.5, 0.0, 0.0],
        [0.5, 0.5, 0.0, 0.0],
    ]
    selected = select_certified_consensus(
        matrix, range(4), ["z0", "z1", "a0", "a1"]
    )

    assert selected["class_indices"] == [2, 3]
    assert selected["index"] == 2


def test_repeated_balanced_cv_is_reproducible():
    labels = ["a", "a", "a", "b", "b", "b"]
    matrix = build_distance_matrix(
        labels, lambda left, right: 0.0 if left == right else 1.0
    )
    kwargs = {
        "matrix": matrix,
        "valid_mask": [True] * 6,
        "certified_mask": [True] * 6,
        "tie_break_keys": [f"{label}{i}" for i, label in enumerate(labels)],
        "train_size": 3,
        "n_splits": 10,
        "seed": 42,
    }

    first = repeated_balanced_cv(**kwargs)
    second = repeated_balanced_cv(**kwargs)

    assert first == second
    assert first["cv_n_splits"] == 10
    assert 0.0 <= first["cv_heldout_match_end_to_end"] <= 1.0
    assert 0.0 <= first["cv_canon_stability"] <= 1.0


def test_cluster_bootstrap_gives_equal_weight_to_each_task():
    result = cluster_bootstrap_mean(
        values=[0.0, 0.0, 1.0],
        cluster_ids=["task-a", "task-a", "task-b"],
        n_bootstrap=500,
        seed=7,
    )
    repeated = cluster_bootstrap_mean(
        values=[0.0, 0.0, 1.0],
        cluster_ids=["task-a", "task-a", "task-b"],
        n_bootstrap=500,
        seed=7,
    )

    assert result == repeated
    assert result["mean"] == pytest.approx(0.5)
    assert result["n_clusters"] == 2


def test_gate0_adapter_reports_legacy_and_frozen_fields():
    outputs = [
        "def f(x):\n    return x + 1\n",
        "def f(x):\n    return x + 1\n",
        "def f(x):\n    if x:\n        return x + 1\n    return 1\n",
        "not valid python (",
    ]
    fp = FoundationalProperties()
    canon = fp.extract_all_properties(outputs[0])
    data = {
        "contract": {"constraints": {"variable_naming": {"naming_policy": "flexible"}}},
        "canon_data": {"foundational_properties": canon},
    }
    result = analyze_pass(
        data,
        outputs,
        stored_distances=[0.0, 0.0, 0.5, 1.0],
        stored_r_anchor=0.5,
        certified_mask=[True, True, True, False],
        cv_splits=6,
    )

    assert result["n_total"] == 4
    assert result["n"] == 3
    assert result["n_excluded"] == 1
    assert result["pairwise_exact_match_end_to_end"] == pytest.approx(1 / 6)
    assert result["certified_modal_mass"] == pytest.approx(0.5)
    assert result["analysis_canon_policy"] == "certified_consensus"
    assert result["medoid_index_local"] == result["consensus_index"]
    assert result["R_medoid_split"] is not None
    assert result["cv_n_splits"] == 6
    assert result["anchor_mean_recomputed"] is not None


def test_gate0_does_not_inherit_raw_oracles_for_post_repair():
    data = {
        "metrics": {
            "behavioral_stats": {
                "oracle_results": [{"passed": True}, {"passed": True}]
            }
        },
        "contract": {},
    }
    outputs = [
        "def f(x):\n    return x\n",
        "def f(x):\n    return x + 1\n",
    ]

    mask, source, oracle_mask = derive_certification_mask(
        data, outputs, "post"
    )
    assert mask is None
    assert oracle_mask is None
    assert source == "unavailable_no_post_oracle"
    result = analyze_pass(
        data,
        outputs,
        stored_distances=[0.0, 1.0],
        stored_r_anchor=0.5,
        certified_mask=None,
        cv_splits=2,
    )

    assert result["certification_available"] is False
    assert result["pairwise_exact_match_end_to_end"] is None
    assert result["certified_modal_mass"] is None
    assert result["cv_heldout_match_end_to_end"] is None
    assert result["analysis_canon_policy"] == "none"
    assert result["medoid_index_local"] is None
    assert result["R_medoid"] is None
    assert result["plain_medoid_index"] is not None


def test_gate0_analysis_canon_is_certified_consensus_not_plain_medoid():
    """Majority of valid outputs can sit on an uncertified form.

    The analysis canon must still be the certified mode, not the geometric
    medoid of every structurally valid generation. Runtime first-valid is
    unused here.
    """
    uncertified_majority = "def f(x):\n    return x\n"
    certified_mode = "def f(x):\n    return x + 1\n"
    outputs = [uncertified_majority] * 5 + [certified_mode] * 2
    fp = FoundationalProperties()
    data = {
        "contract": {"constraints": {"variable_naming": {"naming_policy": "flexible"}}},
        "canon_data": {
            "foundational_properties": fp.extract_all_properties(
                uncertified_majority
            )
        },
    }
    result = analyze_pass(
        data,
        outputs,
        stored_distances=[0.0] * 5 + [1.0, 1.0],
        stored_r_anchor=5 / 7,
        certified_mask=[False] * 5 + [True, True],
        cv_splits=4,
    )

    assert result["plain_medoid_index"] in {0, 1, 2, 3, 4}
    assert result["consensus_index"] in {5, 6}
    assert result["medoid_index_local"] == result["consensus_index"]
    assert result["analysis_canon_policy"] == "certified_consensus"
    assert result["anchor_medoid_distance"] > 0
    assert result["anchor_plain_medoid_distance"] == pytest.approx(0.0)


def test_gate0_accepts_only_hash_bound_post_oracle_cache():
    outputs = [
        "def f(x):\n    return x\n",
        "def f(x):\n    return x + 1\n",
    ]
    contract = {}
    cache = {
        "contract_sha256": hashlib.sha256(
            json.dumps(
                contract, sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest(),
        "oracle_results": [
            {
                "output_sha256": hashlib.sha256(code.encode()).hexdigest(),
                "result": {"passed": passed},
            }
            for code, passed in zip(outputs, [True, False])
        ]
    }
    mask, source, oracle_mask = derive_certification_mask(
        {"contract": contract, "metrics": {}},
        outputs,
        "post",
        cache,
    )

    assert mask == [True, False]
    assert oracle_mask == [True, False]
    assert source == "sandbox_post_oracle_cache"

    cache["oracle_results"][0]["output_sha256"] = "wrong"
    with pytest.raises(ValueError, match="hash does not match"):
        derive_certification_mask(
            {"contract": contract, "metrics": {}},
            outputs,
            "post",
            cache,
        )
