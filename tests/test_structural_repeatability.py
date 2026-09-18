"""Benchmark tape tests. No paid API calls. No SKYT protocol."""

from __future__ import annotations

import json

import pytest

from benchmark.cli import main
from benchmark.estimate import estimate_grid
from benchmark.pins import pinned_dataset_md5, pinned_image_digest
from benchmark.protect import (
    ProtectedOutputError,
    REPO_ROOT,
    assert_writable,
    default_protected,
    is_protected,
)
from benchmark.relation import RELATION_VERSION, same
from benchmark.schema import SCHEMA
from benchmark.score import score_directory
from benchmark.validity.metamorphic import BASE
from benchmarks.humaneval_plus.dataset import load_smoke_problems
from benchmarks.humaneval_plus.provenance import (
    attach_oracle,
    dump_jsonl,
    new_generation_record,
)
from benchmarks.humaneval_plus.stitch import stitch_solution


_PLUS_DEFAULT = object()


def _record(task_id, model, temperature, run_index, stitch, certified, plus_passed=_PLUS_DEFAULT):
    record = new_generation_record(
        task_id=task_id,
        model=model,
        temperature=temperature,
        run_index=run_index,
        problem_prompt="def add(a, b):\n",
        raw_response=stitch["extracted_completion"],
        stitch=stitch,
    )
    if plus_passed is _PLUS_DEFAULT:
        plus_passed = certified
    payload = {
        "base_passed": True,
        "plus_passed": plus_passed,
        "certified": certified,
    }
    return attach_oracle(record, payload)


def test_fingerprint_ignores_docstring():
    reworded = BASE.replace(
        "Return True when n is prime.",
        "Check primality of the integer n.",
    )
    assert same(BASE, reworded)


def test_pins_and_schema():
    assert RELATION_VERSION == 2
    assert SCHEMA == "structural-repeatability-benchmark-v2"
    assert pinned_dataset_md5() == "916d9bfe7b490c2447245ec91595fa4f"
    assert pinned_image_digest().startswith("sha256:")


def test_protected_trees():
    assert is_protected(REPO_ROOT / "outputs" / "gate0")
    assert is_protected(REPO_ROOT / "outputs" / "humaneval_plus" / "pilot" / "nested")
    assert not is_protected(REPO_ROOT / "outputs" / "gate0_consensus")
    assert not is_protected(REPO_ROOT / "outputs" / "benchmark")


def test_score_is_fingerprint_only_and_sliced(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    bad = stitch_solution(add["prompt"], "    return a - b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    dump_jsonl(
        source / "add.jsonl",
        [
            _record("Smoke/add", "smoke-local", 0.0, 0, bad, False),
            _record("Smoke/add", "smoke-local", 0.0, 1, bad, False),
            _record("Smoke/add", "smoke-local", 0.0, 2, good, True),
            _record("Smoke/add", "smoke-local", 0.0, 3, good, True),
        ],
    )
    dump_jsonl(
        source / "identity.jsonl",
        [
            _record("Smoke/identity", "smoke-local", 0.7, 0, bad, False),
            _record("Smoke/identity", "smoke-local", 0.7, 1, bad, False),
            _record("Smoke/identity", "smoke-local", 0.7, 2, bad, False),
            _record("Smoke/identity", "smoke-local", 0.7, 3, good, True),
        ],
    )
    out_dir = tmp_path / "overlay"
    report = score_directory(source, out_dir, n_bootstrap=200)
    assert "headline" not in report
    assert "consensus_index" not in report
    assert report["relation_version"] == 2
    slices = {(s["model"], s["temperature"]): s for s in report["slices"]}
    assert slices[("smoke-local", 0.0)]["n_dropped_same_at_2_given_cert"] == 0
    assert slices[("smoke-local", 0.7)]["n_dropped_same_at_2_given_cert"] == 1
    by_task = {row["task_id"]: row for row in report["configs"]}
    assert by_task["Smoke/add"]["same_at_2"] == pytest.approx(1.0 / 6.0)
    assert by_task["Smoke/add"]["same_at_2_given_cert"] == pytest.approx(1.0)
    assert by_task["Smoke/identity"]["same_at_2_given_cert"] is None
    written = json.loads((out_dir / "benchmark_report.json").read_text(encoding="utf-8"))
    assert written["schema"] == SCHEMA
    assert "slices" in written
    assert written["inference"]["not"].startswith("binomial")
    assert written["pilot_grid"] is True
    assert "n_pairs_total" not in by_task["Smoke/add"]
    assert by_task["Smoke/add"]["u_statistic_pair_count"] == 6
    add_slice = slices[("smoke-local", 0.0)]
    assert add_slice["same_at_2_n_clusters"] == 1
    assert add_slice["inference_version"] == 1


def test_missing_plus_oracle_does_not_fall_back_to_base(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    dump_jsonl(
        source / "ok.jsonl",
        [
            _record("Smoke/add", "smoke-local", 0.0, 0, good, True, plus_passed=None),
            _record("Smoke/add", "smoke-local", 0.0, 1, good, True, plus_passed=None),
        ],
    )
    report = score_directory(source, tmp_path / "out", n_bootstrap=50)
    row = report["configs"][0]
    assert row["n_certified"] == 0
    assert row["same_at_2"] == 0.0
    assert row["same_at_2_given_cert"] is None


def test_score_refuses_repair_and_frozen_out_dir(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    repaired = _record("Smoke/add", "smoke-local", 0.0, 0, good, True)
    repaired["repair_applied"] = True
    dump_jsonl(
        source / "repaired.jsonl",
        [repaired, _record("Smoke/add", "smoke-local", 0.0, 1, good, True)],
    )
    with pytest.raises(ValueError, match="SKYT-repaired"):
        score_directory(source, tmp_path / "ok", n_bootstrap=50)
    clean = tmp_path / "clean"
    clean.mkdir()
    dump_jsonl(
        clean / "ok.jsonl",
        [
            _record("Smoke/add", "smoke-local", 0.0, 0, good, True),
            _record("Smoke/add", "smoke-local", 0.0, 1, good, True),
        ],
    )
    with pytest.raises(ProtectedOutputError):
        score_directory(
            clean,
            REPO_ROOT / "outputs" / "humaneval_plus" / "pilot",
            n_bootstrap=50,
        )


def test_cli_refuses_api_and_frozen_dirs(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    dump_jsonl(
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
                "--n-bootstrap",
                "50",
            ]
        )
        == 0
    )
    assert (out_dir / "benchmark_report.json").exists()
    assert (
        main(
            [
                "run",
                "--task-id",
                "HumanEval/0",
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
                "HumanEval/0",
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
    assert main(["full"]) == 3
    assert (
        main(
            [
                "full",
                "--allow-api",
                "--out-dir",
                str(REPO_ROOT / "outputs" / "gate0"),
            ]
        )
        == 3
    )


def test_estimate_and_writable_helper(tmp_path):
    payload = estimate_grid(n_tasks=30, n=10)
    assert payload["n_calls"] == 30 * 2 * 2 * 10
    full = estimate_grid(n_tasks=164, n=20)
    assert full["n_calls"] == 164 * 2 * 2 * 20
    assert "Protocol N is 20" in full["note"]
    frozen = tmp_path / "pilot"
    frozen.mkdir()
    with pytest.raises(ProtectedOutputError):
        assert_writable(frozen, frozen=[frozen])
    assert default_protected()
    assert (
        main(
            [
                "estimate",
                "--n-tasks",
                "1",
                "--n",
                "10",
                "--model",
                "gpt-4o-mini",
                "--temperature",
                "0.0",
            ]
        )
        == 0
    )


def test_dump_jsonl_replaces_atomically(tmp_path):
    path = tmp_path / "cell.jsonl"
    dump_jsonl(path, [{"run_index": 0, "ok": True}])
    dump_jsonl(path, [{"run_index": 0, "ok": True}, {"run_index": 1, "ok": True}])
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [row["run_index"] for row in lines] == [0, 1]
    assert not list(tmp_path.glob("*.tmp"))


def test_score_skips_incomplete_when_asked(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    dump_jsonl(
        source / "complete.jsonl",
        [
            _record("Smoke/add", "smoke-local", 0.0, 0, good, True),
            _record("Smoke/add", "smoke-local", 0.0, 1, good, True),
        ],
    )
    dump_jsonl(
        source / "partial.jsonl",
        [_record("Smoke/id", "smoke-local", 0.7, 0, good, True)],
    )
    report = score_directory(
        source,
        tmp_path / "out",
        n_bootstrap=50,
        skip_incomplete=True,
        require_n=2,
        report_filename="sameeval_checkpoint.json",
    )
    assert report["n_complete_configs"] == 1
    assert report["n_skipped_incomplete"] == 1
    assert (tmp_path / "out" / "sameeval_checkpoint.json").exists()
