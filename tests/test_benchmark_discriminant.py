"""Discriminant judges. No API. Does not change same()."""

from __future__ import annotations

import pytest

from benchmark.cli import main
from benchmark.discriminant.judges import classify_cell, judge_pair
from benchmark.discriminant.census import run_census
from benchmark.discriminant.ted import _T, ted_and_size, zhang_shasha, ast_to_tree
from benchmark.protect import ProtectedOutputError, REPO_ROOT
from benchmark.validity.metamorphic import BASE
from benchmarks.humaneval_plus.dataset import load_smoke_problems
from benchmarks.humaneval_plus.provenance import (
    attach_oracle,
    dump_jsonl,
    new_generation_record,
)
from benchmarks.humaneval_plus.stitch import stitch_solution
import ast


DOCSTRING = BASE.replace(
    "Return True when n is prime.",
    "Check primality of the integer n and report the result.",
)

RENAMED = '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    for divisor in range(2, int(n ** 0.5) + 1):
        if n % divisor == 0:
            return False
    return True
'''

SPACED = BASE.replace("\n    if n", "\n\n    if n")

WHILE = '''\
def is_prime(n):
    """Return True when n is prime."""
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True
'''


def test_ted_zero_on_identical_trees():
    tree = ast_to_tree(ast.parse(BASE))
    other = ast_to_tree(ast.parse(BASE))
    assert zhang_shasha(tree, tree) == 0
    assert zhang_shasha(tree, other) == 0
    packed = ted_and_size(BASE, BASE)
    assert packed is not None
    assert packed[0] == 0


def test_zhang_shasha_on_tiny_labeled_trees():
    def leaf(name: str) -> _T:
        return _T((name, ""), [])

    assert zhang_shasha(leaf("a"), leaf("a")) == 0
    assert zhang_shasha(leaf("a"), leaf("b")) == 1
    left = _T(("a", ""), [leaf("b"), leaf("c")])
    right = _T(("a", ""), [leaf("b")])
    assert zhang_shasha(left, right) == 1


def test_ted_positive_when_constant_changes():
    other = BASE.replace("return True", "return False", 1)
    packed = ted_and_size(BASE, other)
    assert packed is not None
    assert packed[0] > 0


def test_formatting_is_type1_not_string():
    v = judge_pair(BASE, SPACED)
    assert v["string_eq"] is False
    assert v["parse_unparse_eq"] is True
    assert v["fingerprint_eq"] is True
    assert classify_cell(v) == "formatting"


def test_docstring_splits_type2_not_the_tape():
    v = judge_pair(BASE, DOCSTRING)
    assert v["fingerprint_eq"] is True
    assert v["raw_ast_eq"] is False
    assert v["type2_eq"] is False
    assert classify_cell(v) == "docstring_or_prose"


def test_bound_rename_is_type2_and_tape():
    v = judge_pair(BASE, RENAMED)
    assert v["fingerprint_eq"] is True
    assert v["type2_eq"] is True
    assert v["raw_ast_eq"] is False
    assert classify_cell(v) == "bound_rename"


def test_loop_vs_while_is_not_the_same_program():
    v = judge_pair(BASE, WHILE)
    assert v["fingerprint_eq"] is False
    assert v["string_eq"] is False


def test_census_on_certified_jsonl(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    alt = stitch_solution(add["prompt"], "    return a + b  # x\n", "add")
    source = tmp_path / "source"
    source.mkdir()

    def rec(index, stitch):
        record = new_generation_record(
            task_id="Smoke/add",
            model="smoke-local",
            temperature=0.0,
            run_index=index,
            problem_prompt=add["prompt"],
            raw_response=stitch["extracted_completion"],
            stitch=stitch,
        )
        return attach_oracle(
            record,
            {"base_passed": True, "plus_passed": True, "certified": True},
        )

    dump_jsonl(source / "add.jsonl", [rec(0, good), rec(1, alt), rec(2, good)])
    out = tmp_path / "disc"
    report = run_census(source, out, sample_per_cell=5, seed=20260723)
    assert report["n_pairs"] == 3
    assert report["tape"] == "fingerprint_eq"
    assert "string_eq" in report["vs_fingerprint"]
    cells = report["vs_fingerprint"]["string_eq"]
    assert cells["n_compared"] == 3
    assert (out / "discriminant_report.json").exists()
    assert (
        main(
            [
                "discriminant",
                "--source-dir",
                str(source),
                "--out-dir",
                str(tmp_path / "cli"),
                "--sample-per-cell",
                "2",
            ]
        )
        == 0
    )


def test_discriminant_refuses_frozen_out_dir(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    record = new_generation_record(
        task_id="Smoke/add",
        model="smoke-local",
        temperature=0.0,
        run_index=0,
        problem_prompt=add["prompt"],
        raw_response=good["extracted_completion"],
        stitch=good,
    )
    record = attach_oracle(
        record, {"base_passed": True, "plus_passed": True, "certified": True}
    )
    other = dict(record)
    other["run_index"] = 1
    dump_jsonl(source / "ok.jsonl", [record, other])
    with pytest.raises(ProtectedOutputError):
        run_census(source, REPO_ROOT / "outputs" / "gate0")


def test_discriminant_refuses_repaired_jsonl(tmp_path):
    problems = load_smoke_problems()
    add = problems[0]
    good = stitch_solution(add["prompt"], "    return a + b\n", "add")
    source = tmp_path / "source"
    source.mkdir()
    record = new_generation_record(
        task_id="Smoke/add",
        model="smoke-local",
        temperature=0.0,
        run_index=0,
        problem_prompt=add["prompt"],
        raw_response=good["extracted_completion"],
        stitch=good,
    )
    record = attach_oracle(
        record, {"base_passed": True, "plus_passed": True, "certified": True}
    )
    record["repair_applied"] = True
    dump_jsonl(source / "repaired.jsonl", [record])
    with pytest.raises(ValueError, match="refuses SKYT-repaired"):
        run_census(source, tmp_path / "out")
