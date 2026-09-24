"""Synthetic checks for the exploratory diversity-signal analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import hashlib

from benchmark.diversity_signal import (
    DiversitySignalError,
    analyze,
    config_row,
    diversity_from_sizes,
    joint_bootstrap,
    loo_roles,
    main,
    uniformity_class,
)
from benchmark.metrics import cluster_bootstrap_mean


def _record(task, model, temperature, run_index, code, base, plus, repair=False):
    return {
        "task_id": task,
        "model": model,
        "temperature": temperature,
        "run_index": run_index,
        "stitched_code": code,
        "repair_applied": repair,
        "style_contract": None,
        "oracle": {"base_passed": base, "plus_passed": plus},
    }


def _fn(name, body):
    return f"def {name}(x):\n    {body}\n"


def test_loo_tie_is_unclassified():
    keys = ["a", "a", "b", "b", "c"]
    modal, nonmodal, unclassified = loo_roles(keys)
    assert unclassified == [4]
    assert 4 not in modal
    assert 4 not in nonmodal


def test_single_form_excluded_from_a1_and_diversity_zero():
    code = _fn("f", "return x")
    records = [
        _record("HumanEval/0", "m", 0.0, i, code, True, True) for i in range(4)
    ]
    row = config_row(records)
    assert row["D_c"] == 0.0
    assert row["a1_eligible"] is False
    assert row["a2_eligible"] is True


def test_n_c_below_two_excluded():
    records = [
        _record("HumanEval/0", "m", 0.0, 0, _fn("f", "return x"), True, True),
        _record("HumanEval/0", "m", 0.0, 1, _fn("f", "return x"), False, False),
    ]
    row = config_row(records)
    assert row["n_c"] == 1
    assert row["a1_eligible"] is False
    assert row["a2_eligible"] is False


def test_diversity_matches_hand_computed_same_at_2():
    # Class sizes 3 and 1. same@2 = 3*2 / (4*3) = 0.5. D = 0.5.
    assert diversity_from_sizes([3, 1], 4) == pytest.approx(0.5)
    assert diversity_from_sizes([4], 4) == pytest.approx(0.0)


def test_same_seed_identical_bootstrap():
    rows = []
    for task in ("t1", "t2", "t3", "t4"):
        for cell, d_value, f_value in (
            ("m T=0.0", 0.2, 0.1),
            ("m T=0.7", 0.8, 0.4),
        ):
            rows.append(
                {
                    "task_id": task,
                    "cell": cell,
                    "D_c": d_value,
                    "F_c": f_value,
                    "n_c": 10,
                    "s_mod": 0.9,
                    "s_non": 0.4,
                    "delta": 0.5,
                }
            )
    first = joint_bootstrap(rows, rows, n_bootstrap=20, seed=20260723, edges=(0.3, 0.6))
    second = joint_bootstrap(rows, rows, n_bootstrap=20, seed=20260723, edges=(0.3, 0.6))
    assert first == second


def test_repair_applied_raises(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    record = _record("HumanEval/0", "m", 0.0, 0, _fn("f", "return x"), True, True, repair=True)
    (source / "one.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    prereg = tmp_path / "prereg.md"
    prereg.write_text("prereg\n", encoding="utf-8")
    with pytest.raises(DiversitySignalError, match="repair_applied"):
        analyze([source], tmp_path / "out", n_bootstrap=10, seed=1, prereg_path=prereg)


def test_uniformity_classes():
    assert uniformity_class(0.0) == "all_pass"
    assert uniformity_class(1.0) == "all_fail"
    assert uniformity_class(0.25) == "mixed"
    assert uniformity_class(0.25) != "all_fail"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_posthoc_uniformity_does_not_touch_preregistered_files(tmp_path: Path):
    source = tmp_path / "src"
    source.mkdir()
    records = []
    for task_index in range(5):
        plus = task_index % 2 == 0
        for index in range(4):
            body = f"return x + {task_index}" if index < 3 else f"return x + {task_index + 10}"
            records.append(
                _record(
                    f"HumanEval/{task_index}",
                    "m",
                    0.0,
                    index,
                    _fn("f", body),
                    True,
                    plus,
                )
            )
    (source / "one.jsonl").write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )
    prereg = tmp_path / "prereg.md"
    prereg.write_text("prereg\n", encoding="utf-8")
    out = tmp_path / "out"
    analyze([source], out, n_bootstrap=8, seed=1, prereg_path=prereg)
    frozen = [
        out / "diversity_signal.json",
        out / "per_config.csv",
        out / "prereg_hash.txt",
    ]
    before = {path.name: _sha256(path) for path in frozen}
    main(
        [
            "--trees",
            str(source),
            "--out",
            str(out),
            "--seed",
            "1",
            "--n-boot",
            "8",
            "--posthoc-uniformity",
        ]
    )
    after = {path.name: _sha256(path) for path in frozen}
    assert before == after
    assert (out / "posthoc_uniformity.json").is_file()
    assert (out / "posthoc_uniformity_per_config.csv").is_file()


def test_pooled_mean_interval_matches_helper():
    values = [0.1, 0.2, 0.4, 0.5]
    ids = ["t1", "t1", "t2", "t2"]
    helper = cluster_bootstrap_mean(values, ids, n_bootstrap=30, seed=20260723)
    rows = [
        {"task_id": "t1", "cell": "c", "D_c": 0.1, "F_c": 0.0, "n_c": 10, "s_mod": 0.1, "s_non": 0.0, "delta": 0.1},
        {"task_id": "t1", "cell": "c", "D_c": 0.2, "F_c": 0.0, "n_c": 10, "s_mod": 0.2, "s_non": 0.0, "delta": 0.2},
        {"task_id": "t2", "cell": "c", "D_c": 0.4, "F_c": 0.0, "n_c": 10, "s_mod": 0.4, "s_non": 0.0, "delta": 0.4},
        {"task_id": "t2", "cell": "c", "D_c": 0.5, "F_c": 0.0, "n_c": 10, "s_mod": 0.5, "s_non": 0.0, "delta": 0.5},
    ]
    # Two cells would change the draw. One cell: joint mean of task means
    # matches the helper when the resampled unit is the task mean.
    got = joint_bootstrap(rows, rows, n_bootstrap=30, seed=20260723, edges=(0.2, 0.4))
    assert got["a1.delta"]["lower"] == pytest.approx(helper["lower"])
    assert got["a1.delta"]["upper"] == pytest.approx(helper["upper"])
