"""HumanEval+ adapter tests. No paid API calls."""

from __future__ import annotations

import json
import random

import pytest

from benchmarks.humaneval_plus.analyze import analyze_records
from benchmarks.humaneval_plus.cli import main, run_smoke
from benchmarks.humaneval_plus.dataset import load_smoke_problems
from benchmarks.humaneval_plus.generate import ApiSpendBlocked, generate_completion
from benchmarks.humaneval_plus.manifest import MANIFEST, PILOT_SEED, PILOT_TASK_IDS
from benchmarks.humaneval_plus.prompts import prompt_bundle_hash, render_user_prompt
from benchmarks.humaneval_plus.provenance import attach_oracle, new_generation_record
from benchmarks.humaneval_plus.sandbox import docker_available, evaluate_stitched, plus_cases_for_problem
from benchmarks.humaneval_plus.stitch import extract_completion, stitch_solution


def test_pilot_ids_are_preregistered_and_reproducible():
    rng = random.Random(PILOT_SEED)
    universe = [f"HumanEval/{i}" for i in range(164)]
    expected = sorted(rng.sample(universe, 30))
    assert PILOT_TASK_IDS == expected
    assert len(set(PILOT_TASK_IDS)) == 30
    assert "HumanEval/32" in PILOT_TASK_IDS


def test_manifest_forbids_repair_and_style_contracts():
    assert MANIFEST["analysis"]["no_skyt_repair"] is True
    assert MANIFEST["analysis"]["no_style_contracts"] is True
    assert MANIFEST["models"] == ["gpt-4o-mini", "claude-sonnet-4-5-20250929"]
    assert MANIFEST["temperatures"] == [0.0, 0.7]
    assert MANIFEST["n_pilot"] == 10
    assert MANIFEST["n_full"] == 20


def test_evalplus_dataset_md5_is_pinned():
    digest = MANIFEST["dataset"]["dataset_md5"]
    assert digest == "916d9bfe7b490c2447245ec91595fa4f"
    assert MANIFEST["dataset"]["evalplus_version"] == "0.3.1"
    assert MANIFEST["dataset"]["humaneval_plus_dataset_version"] == "v0.1.10"


def test_extract_and_stitch_body_fence_and_garbage():
    problems = load_smoke_problems()
    add = problems[0]
    body = stitch_solution(add["prompt"], "    return a + b\n", "add")
    assert body["parse_ok"]
    assert body["has_entry_point"]
    assert body["stitch_mode"] == "prompt_plus_body"
    assert "def add" in body["stitched_code"]

    fenced = stitch_solution(
        add["prompt"],
        "```python\ndef add(a: int, b: int) -> int:\n    return a + b\n```",
        "add",
    )
    assert fenced["stitch_mode"] == "standalone"
    assert fenced["parse_ok"]
    assert extract_completion("```\nreturn 1\n```") == "return 1"

    garbage = stitch_solution(add["prompt"], "not python (", "add")
    assert garbage["parse_ok"] is False
    assert plus_cases_for_problem(add)[0]["expected"] == 0


def test_generate_refuses_without_allow_api():
    with pytest.raises(ApiSpendBlocked):
        generate_completion(
            model="gpt-4o-mini",
            problem_prompt="def add(a, b):\n",
            temperature=0.0,
            max_tokens=16,
            allow_api=False,
        )
    assert main(["generate"]) == 3
    assert main(["run", "--task-id", "HumanEval/23", "--n", "2", "--out-dir", "outputs/humaneval_plus/dryrun"]) == 3


def test_provenance_record_has_hashes_and_no_repair():
    problems = load_smoke_problems()
    add = problems[0]
    stitch = stitch_solution(add["prompt"], add["canonical_solution"], "add")
    record = new_generation_record(
        task_id=add["task_id"],
        model="smoke-local",
        temperature=0.0,
        run_index=0,
        problem_prompt=add["prompt"],
        raw_response="    return a + b",
        stitch=stitch,
    )
    assert record["repair_applied"] is False
    assert record["style_contract"] is None
    assert record["prompt"]["prompt_bundle_sha256"] == prompt_bundle_hash()
    assert add["prompt"].strip() in render_user_prompt(add["prompt"])
    record = attach_oracle(
        record,
        {
            "base_status": "pass",
            "base_passed": True,
            "plus_status": "pass",
            "plus_passed": True,
            "certified": True,
        },
    )
    assert record["oracle"]["certified"] is True


def test_analyze_uses_plus_certification_not_uncertified_majority():
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    bad = stitch_solution(add["prompt"], "    return abs(a) + abs(b)\n", "add")
    records = []
    for index, (stitch, certified) in enumerate(
        [(bad, False), (bad, False), (bad, False), (good, True), (good, True)]
    ):
        record = new_generation_record(
            task_id="Smoke/add",
            model="smoke-local",
            temperature=0.0,
            run_index=index,
            problem_prompt=add["prompt"],
            raw_response=stitch["extracted_completion"],
            stitch=stitch,
        )
        record = attach_oracle(
            record,
            {
                "base_passed": True,
                "plus_passed": certified,
                "certified": certified,
            },
        )
        records.append(record)
    result = analyze_records(records, cv_splits=8)
    assert result["n_plus_certified"] == 2
    assert result["consensus_index"] in {3, 4}
    assert result["no_skyt_repair"] is True
    assert result["no_style_contracts"] is True


@pytest.mark.skipif(not docker_available(), reason="Docker is not running")
def test_docker_sandbox_recovers_base_plus_and_timeout():
    problems = load_smoke_problems()
    add = next(item for item in problems if item["task_id"] == "Smoke/add")
    identity = next(item for item in problems if item["task_id"] == "Smoke/identity")
    good = stitch_solution(add["prompt"], add["canonical_solution"], "add")
    base_only = stitch_solution(add["prompt"], "    return a + b if a >= 0 else 0\n", "add")
    wrong = stitch_solution(add["prompt"], "    return a - b\n", "add")
    hang = stitch_solution(
        identity["prompt"], "    while True:\n        pass\n", "identity"
    )

    canonical = evaluate_stitched(good["stitched_code"], add)
    assert canonical["certified"] is True
    assert canonical["base_passed"] is True
    assert canonical["plus_passed"] is True

    split = evaluate_stitched(base_only["stitched_code"], add)
    assert split["base_passed"] is True
    assert split["plus_passed"] is False

    failed = evaluate_stitched(wrong["stitched_code"], add)
    assert failed["base_passed"] is False

    timed = evaluate_stitched(hang["stitched_code"], identity, timeout_seconds=3)
    assert timed["base_status"] == "timeout"


def test_smoke_report_stitch_always_runs():
    report = run_smoke()
    assert report["stitch_ok"] is True
    assert report["pilot_n"] == 30
    if docker_available():
        assert report["ok"] is True
        recovery = report["sandbox"]["score_recovery"]
        assert recovery["canonical_certified"] is True
        assert recovery["base_only_passes_base_fails_plus"] is True
        assert recovery["incorrect_fails_base"] is True
        assert recovery["timeout_status"] is True
    else:
        assert report["ok"] is False
        assert "Docker" in report["sandbox"]["error"]
