"""Overlay harness tests. No paid API calls."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.humaneval_plus.dataset import load_smoke_problems
from benchmarks.humaneval_plus.provenance import (
    attach_oracle,
    dump_jsonl,
    new_generation_record,
)
from benchmarks.humaneval_plus.stitch import stitch_solution
from benchmarks.structural_repeatability.cli import main
from benchmarks.structural_repeatability.estimate import estimate_grid
from benchmarks.structural_repeatability.pins import pinned_dataset_md5, pinned_image_digest
from benchmarks.structural_repeatability.protect import (
    ProtectedOutputError,
    REPO_ROOT,
    assert_writable,
    default_protected,
    is_protected,
)
from benchmarks.structural_repeatability.schema import RELATION_VERSION, SCHEMA
from benchmarks.structural_repeatability.score import score_directory


def _record(task_id, model, temperature, run_index, stitch, certified):
    record = new_generation_record(
        task_id=task_id,
        model=model,
        temperature=temperature,
        run_index=run_index,
        problem_prompt="def add(a, b):\n",
        raw_response=stitch["extracted_completion"],
        stitch=stitch,
    )
    return attach_oracle(
        record,
        {
            "base_passed": True,
            "plus_passed": certified,
            "certified": certified,
        },
    )


def _write_config(path: Path, records) -> None:
    dump_jsonl(path, records)


def test_relation_version_is_canonical_form_fingerprint():
    assert RELATION_VERSION == 2
    assert SCHEMA == "skyt-structural-repeatability-overlay-v1"
    assert pinned_dataset_md5() == "916d9bfe7b490c2447245ec91595fa4f"
    assert pinned_image_digest().startswith("sha256:")


def test_default_protected_trees_include_gate0_and_pilot():
    protected = default_protected()
    assert (REPO_ROOT / "outputs" / "gate0") in protected
    assert (REPO_ROOT / "outputs" / "humaneval_plus" / "pilot") in protected
    assert is_protected(REPO_ROOT / "outputs" / "gate0")
    assert is_protected(REPO_ROOT / "outputs" / "humaneval_plus" / "pilot" / "nested")
    assert not is_protected(REPO_ROOT / "outputs" / "gate0_consensus")
    assert not is_protected(REPO_ROOT / "outputs" / "humaneval_plus" / "pilot_skyt")
    assert not is_protected(REPO_ROOT / "outputs" / "structural_repeatability")


def test_assert_writable_refuses_frozen_out_dir(tmp_path):
    frozen = tmp_path / "pilot"
    frozen.mkdir()
    with pytest.raises(ProtectedOutputError, match="frozen historical tree"):
        assert_writable(frozen, frozen=[frozen])
    with pytest.raises(ProtectedOutputError):
        assert_writable(frozen / "nested", frozen=[frozen])
    other = tmp_path / "overlay"
    assert_writable(other, frozen=[frozen])


def test_score_writes_both_metrics_and_drop_count(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    bad = stitch_solution(add["prompt"], "    return a - b\n", "add")

    source = tmp_path / "source"
    source.mkdir()
    defined = [
        _record("Smoke/add", "smoke-local", 0.0, 0, bad, False),
        _record("Smoke/add", "smoke-local", 0.0, 1, bad, False),
        _record("Smoke/add", "smoke-local", 0.0, 2, good, True),
        _record("Smoke/add", "smoke-local", 0.0, 3, good, True),
    ]
    undefined = [
        _record("Smoke/identity", "smoke-local", 0.7, 0, bad, False),
        _record("Smoke/identity", "smoke-local", 0.7, 1, bad, False),
        _record("Smoke/identity", "smoke-local", 0.7, 2, bad, False),
        _record("Smoke/identity", "smoke-local", 0.7, 3, good, True),
    ]
    _write_config(source / "add.jsonl", defined)
    _write_config(source / "identity.jsonl", undefined)

    out_dir = tmp_path / "overlay"
    report = score_directory(
        source,
        out_dir,
        cv_splits=8,
        n_bootstrap=200,
    )
    headline = report["headline"]
    assert report["relation_version"] == 2
    assert report["no_skyt_repair"] is True
    assert headline["n_configs"] == 2
    assert headline["n_tasks"] == 2
    assert headline["n_dropped_same_at_2_given_cert"] == 1
    assert headline["same_at_2_given_cert_n_defined"] == 1
    assert headline["same_at_2_given_cert_n_missing"] == 1
    assert headline["same_at_2_n_defined"] == 2
    assert headline["same_at_2_n_missing"] == 0
    assert headline["same_at_2"] is not None
    assert 0.0 <= headline["same_at_2"] <= 1.0
    by_task = {row["task_id"]: row for row in report["configs"]}
    assert by_task["Smoke/add"]["same_at_2_given_cert"] == pytest.approx(1.0)
    assert by_task["Smoke/identity"]["same_at_2_given_cert"] is None
    # 1 certified pair out of C(4,2)=6
    assert by_task["Smoke/add"]["same_at_2"] == pytest.approx(1.0 / 6.0)
    written = json.loads((out_dir / "overlay_report.json").read_text(encoding="utf-8"))
    assert written["schema"] == SCHEMA
    assert "same_at_2" in written["headline"]
    assert "same_at_2_given_cert" in written["headline"]


def test_score_refuses_repaired_records_and_protected_out_dir(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    repaired = _record("Smoke/add", "smoke-local", 0.0, 0, good, True)
    repaired["repair_applied"] = True
    other = _record("Smoke/add", "smoke-local", 0.0, 1, good, True)
    _write_config(source / "repaired.jsonl", [repaired, other])
    with pytest.raises(ValueError, match="SKYT-repaired"):
        score_directory(source, tmp_path / "ok", cv_splits=4, n_bootstrap=50)

    clean_source = tmp_path / "clean"
    clean_source.mkdir()
    _write_config(
        clean_source / "ok.jsonl",
        [
            _record("Smoke/add", "smoke-local", 0.0, 0, good, True),
            _record("Smoke/add", "smoke-local", 0.0, 1, good, True),
        ],
    )
    with pytest.raises(ProtectedOutputError):
        score_directory(
            clean_source,
            REPO_ROOT / "outputs" / "humaneval_plus" / "pilot",
            cv_splits=4,
            n_bootstrap=50,
        )


def test_cli_score_and_run_refuse_without_spending(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    _write_config(
        source / "ok.jsonl",
        [
            _record("Smoke/add", "smoke-local", 0.0, 0, good, True),
            _record("Smoke/add", "smoke-local", 0.0, 1, good, True),
        ],
    )
    out_dir = tmp_path / "overlay"
    assert (
        main(
            [
                "score",
                "--source-dir",
                str(source),
                "--out-dir",
                str(out_dir),
                "--cv-splits",
                "8",
                "--n-bootstrap",
                "50",
            ]
        )
        == 0
    )
    assert (out_dir / "overlay_report.json").exists()

    assert (
        main(
            [
                "run",
                "--task-id",
                "HumanEval/23",
                "--model",
                "gpt-4o-mini",
                "--temperature",
                "0.0",
                "--n",
                "2",
                "--out-dir",
                str(tmp_path / "paid"),
            ]
        )
        == 3
    )
    assert (
        main(
            [
                "run",
                "--allow-api",
                "--task-id",
                "HumanEval/23",
                "--model",
                "gpt-4o-mini",
                "--temperature",
                "0.0",
                "--n",
                "2",
                "--out-dir",
                str(REPO_ROOT / "outputs" / "gate0"),
            ]
        )
        == 3
    )
    assert (
        main(
            [
                "score",
                "--source-dir",
                str(source),
                "--out-dir",
                str(REPO_ROOT / "outputs" / "humaneval_plus" / "pilot"),
            ]
        )
        == 3
    )


def test_estimate_prints_usd_without_api():
    payload = estimate_grid(n_tasks=30, n=10)
    assert payload["n_calls"] == 30 * 2 * 2 * 10
    assert payload["usd_estimate"] > 0
    assert payload["no_skyt_repair"] is True
    assert main(["estimate", "--n-tasks", "1", "--n", "10", "--model", "gpt-4o-mini", "--temperature", "0.0"]) == 0
