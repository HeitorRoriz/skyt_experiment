"""Held-out SKYT rewrite tests. No paid API calls."""

from __future__ import annotations

import pytest

from benchmark.protect import ProtectedOutputError, REPO_ROOT
from benchmarks.humaneval_plus.cli import main
from skyt.humaneval_heldout import (
    fingerprint_repeatability,
    heldout_config,
    heldout_grid,
    heldout_splits,
    balanced_splits_ordered,
    select_train_canon,
)
from skyt.humaneval_repair import (
    apply_certified_consensus_repair,
    humaneval_repair_contract,
    select_certified_consensus_canon,
)


def _record(index: int, code: str, plus: bool) -> dict:
    return {
        "run_index": index,
        "task_id": "HumanEval/0",
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "stitched_code": code,
        "oracle": {
            "base_passed": plus,
            "plus_passed": plus,
            "certified": plus,
        },
    }


def _contract() -> dict:
    return humaneval_repair_contract(
        task_id="HumanEval/0",
        model="gpt-4o-mini",
        temperature=0.0,
        prompt="def add(a, b):\n",
        entry_point="add",
    )


FORM_A = "def add(a, b):\n    return a + b\n"
FORM_B = "def add(a, b):\n    total = a + b\n    return total\n"
FORM_FAIL = "def add(a, b):\n    return a - b\n"


def test_heldout_splits_are_balanced_and_reproducible():
    first = heldout_splits(20, 10, 20, 20260723)
    second = heldout_splits(20, 10, 20, 20260723)
    assert first == second
    assert len(first) == 20
    for train in first:
        assert len(train) == 10
        assert len(set(train)) == 10
        test = set(range(20)) - set(train)
        assert len(test) == 10
        assert not set(train) & test


def test_ordered_splits_share_set_with_sorted_heldout_splits():
    assert set(heldout_splits(20, 10, 20, 20260723)) == set(
        balanced_splits_ordered(20, 10, 20, 20260723)
    )


def test_train_only_canon_ignores_heldout_majority():
    records = []
    for index in range(20):
        if index < 3:
            records.append(_record(index, FORM_A, True))
        elif index < 10:
            records.append(_record(index, FORM_FAIL, False))
        else:
            records.append(_record(index, FORM_B, True))
    contract = _contract()
    train_pick = select_train_canon(records, contract, list(range(10)))
    assert train_pick is not None
    assert train_pick["index"] < 10
    assert records[train_pick["index"]]["stitched_code"] == FORM_A

    full_pick = select_certified_consensus_canon(
        [item["stitched_code"] for item in records],
        contract,
        [
            {
                "passed": bool((item["oracle"] or {}).get("certified")),
                "plus_passed": item["oracle"]["plus_passed"],
                "certified": item["oracle"]["certified"],
            }
            for item in records
        ],
    )
    assert full_pick is not None
    assert full_pick["index"] >= 10
    assert records[full_pick["index"]]["stitched_code"] == FORM_B


def test_fingerprint_same_at_2_keeps_failures_in_denominator():
    records = [
        _record(0, FORM_A, True),
        _record(1, FORM_A, True),
        _record(2, FORM_FAIL, False),
    ]
    analysis = fingerprint_repeatability(records)
    assert analysis["u_statistic_pair_count"] == 3
    assert analysis["same_at_2"] == pytest.approx(1.0 / 3.0)
    assert analysis["same_at_2_given_cert"] == pytest.approx(1.0)


def test_apply_repair_skips_when_train_has_no_canon():
    records = [_record(i, FORM_FAIL, False) for i in range(3)]
    repaired, rows, n_transformed, n_rolled_back = apply_certified_consensus_repair(
        records=records,
        selected=None,
        contract_dict=_contract(),
        oracle=None,
        canon_store=REPO_ROOT / "outputs" / "benchmark" / "unused_canon",
    )
    assert n_transformed == 0
    assert n_rolled_back == 0
    assert all(not item["repair_applied"] for item in repaired)
    assert all(row["skipped_reason"] == "no_certified_consensus_canon" for row in rows)


def test_heldout_config_refuses_wrong_n_and_source_overwrite(tmp_path):
    shared = tmp_path / "overlay"
    shared.mkdir()
    with pytest.raises(ValueError, match="Refusing to overwrite"):
        heldout_config(
            source_dir=shared,
            out_dir=shared,
            task_id="HumanEval/0",
            model="gpt-4o-mini",
            temperature=0.0,
            n=20,
        )
    with pytest.raises(ValueError, match="protocol N=20"):
        heldout_config(
            source_dir=shared,
            out_dir=tmp_path / "heldout",
            task_id="HumanEval/0",
            model="gpt-4o-mini",
            temperature=0.0,
            n=10,
        )


def test_heldout_grid_refuses_frozen_overlay(tmp_path):
    with pytest.raises(ProtectedOutputError):
        heldout_grid(
            source_dir=tmp_path,
            out_dir=REPO_ROOT / "outputs" / "benchmark" / "humaneval_plus_164_n20",
        )


def test_heldout_cli_does_not_require_allow_api():
    with pytest.raises(SystemExit) as exc:
        main(["heldout", "--help"])
    assert exc.value.code == 0


def test_operational_canon_uses_base_when_plus_fails():
    from skyt.humaneval_oracle_split import _base_operational_payload, dual_repeatability

    records = []
    for index in range(10):
        plus_ok = False
        base_ok = index < 3
        records.append(
            {
                "run_index": index,
                "task_id": "HumanEval/0",
                "model": "gpt-4o-mini",
                "temperature": 0.0,
                "stitched_code": FORM_A if base_ok else FORM_FAIL,
                "oracle": {
                    "base_passed": base_ok,
                    "plus_passed": plus_ok,
                    "certified": plus_ok,
                },
            }
        )
    contract = _contract()
    plus_pick = select_train_canon(records, contract, list(range(10)))
    base_pick = select_train_canon(
        records, contract, list(range(10)), payload_fn=_base_operational_payload
    )
    assert plus_pick is None
    assert base_pick is not None
    assert records[base_pick["index"]]["stitched_code"] == FORM_A
    analysis = dual_repeatability(records)
    assert analysis["base_pass"] == pytest.approx(0.3)
    assert analysis["plus_pass"] == pytest.approx(0.0)
