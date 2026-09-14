"""Validity invariants for the structural sameness relation (Step 1).

The settled cases in ``benchmarks.structural_validity.metamorphic`` are asserted
here. All of them pass as of the 2026-09-14 extractor fix, which moved the
naming policy and docstring handling into ``_canonicalize`` so that every
property sees the same canonical tree, and replaced the seven-name α-renamer
allowlist with scope analysis.

Before that fix seven of these failed: identifier renames leaked through
``data_dependency_graph`` and ``function_contracts``, docstring text leaked
through ``ast.dump``, and non-allowlisted builtins such as ``all``/``any``
collapsed onto the same fingerprint at distance 0. Each case below is a
regression guard for one of those.
"""

from __future__ import annotations

import pytest

from benchmarks.structural_validity.metamorphic import ALL_CASES, evaluate


@pytest.fixture(scope="module")
def results():
    return {row["name"]: row for row in evaluate()}


def _case_ids(group: str):
    return [case.name for case in ALL_CASES if case.group == group]


@pytest.mark.parametrize("name", _case_ids("SAME"))
def test_semantics_preserving_edits_are_the_same_form(name, results):
    """Formatting, identifier and docstring edits must not register as churn."""
    row = results[name]
    assert row["relation_says_same"], (
        f"false split: {name} has distance {row['distance']:.4f}; "
        f"differing properties: {row['differing_properties']}"
    )


@pytest.mark.parametrize("name", _case_ids("DIFFERENT"))
def test_distinct_programs_are_not_the_same_form(name, results):
    """Rewrites a reviewer would notice must register as a different form."""
    row = results[name]
    assert not row["relation_says_same"], (
        f"false merge: {name} has distance 0, so the relation calls two "
        "behaviorally different programs the same form"
    )


_UNDECIDED_IDS = _case_ids("UNDECIDED")


@pytest.mark.skipif(not _UNDECIDED_IDS, reason="no undecided metamorphic cases")
@pytest.mark.parametrize("name", _UNDECIDED_IDS or ["_none"])
def test_undecided_edits_are_characterized_not_asserted(name, results):
    """Record today's behavior for edits whose definition is still open.

    No direction is asserted. The test only pins that the relation produces a
    finite verdict, so the definitional call can be made against real output.
    """
    row = results[name]
    assert row["distance"] >= 0.0
    assert row["verdict"] in {"same", "different"}
