"""Post-hoc held-out helpers. No Docker, no API."""

from __future__ import annotations

from pathlib import Path

import pytest

from skyt.heldout_posthoc import _identical_copies, _pearson, load_heldout_configs
from skyt.humaneval_heldout import HELDOUT_OUT


def test_identical_certified_copies_are_perfect_repeatability():
    assert _identical_copies(True, True)["same_at_2"] == 1.0
    assert _identical_copies(True, False)["same_at_2"] == 0.0


def test_pearson_negative_when_low_baseline_has_high_lift():
    xs = [0.1, 0.2, 0.8, 0.9]
    ys = [0.7, 0.6, 0.1, 0.0]
    value = _pearson(xs, ys)
    assert value is not None
    assert value < -0.9


@pytest.mark.skipif(
    not (Path(HELDOUT_OUT) / "HumanEval_0_claude_sonnet_4_5_20250929_temp0.0_heldout.json").exists()
    and not HELDOUT_OUT.exists(),
    reason="held-out summaries not on disk",
)
def test_common_support_is_pre_eligible_set():
    if not HELDOUT_OUT.exists():
        pytest.skip("held-out tree missing")
    rows = load_heldout_configs(HELDOUT_OUT)
    if len(rows) != 656:
        pytest.skip(f"incomplete held-out tree ({len(rows)})")
    common = sum(1 for row in rows if row["common_support"])
    pre = sum(1 for row in rows if row["pre_same_at_2_given_cert"] is not None)
    assert common == pre
    assert common == 562
