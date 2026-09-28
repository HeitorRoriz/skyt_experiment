import pytest
from skyt.fse_final_posthoc import (
    changed_lines, cohen_kappa, paired_temperature_deltas, reweighted, stratified_bootstrap,
)


def _row(task, t, plus, same):
    return {"model": "gpt-4o-mini", "task_id": task, "temperature": t, "plus_pass": plus, "same_at_2": same}


def test_paired_delta_is_task_level_and_drops_unpaired():
    rows = [_row("a", 0.0, 1.0, 0.9), _row("a", 0.7, 1.0, 0.5),
            _row("b", 0.0, 0.8, 0.6), _row("b", 0.7, 0.8, 0.4),
            _row("c", 0.0, 0.5, 0.5)]  # c has no T=0.7 cell
    out = paired_temperature_deltas(rows, models=("gpt-4o-mini",))["gpt-4o-mini"]
    assert out["plus_pass"]["n_tasks"] == 2
    assert out["plus_pass"]["delta_pts"] == 0.0
    assert out["same_at_2"]["delta_pts"] == pytest.approx(-30.0)


def test_duplicate_cell_rejected():
    with pytest.raises(ValueError):
        paired_temperature_deltas([_row("a", 0.0, 1, 1), _row("a", 0.0, 1, 1)], models=("gpt-4o-mini",))


def test_reweighting_recovers_population_rates():
    # population: 100 fp_same pairs (90 human-same), 900 fp_diff pairs (180 human-same)
    # truth: sens = 90/270, spec = 720/730
    S, D = ("m", 0.0, "fp_same|both_cert"), ("m", 0.0, "fp_diff|both_cert")
    labeled = {S: [1] * 9 + [0], D: [1] * 2 + [0] * 8}  # equal n per stratum, exact rates
    r = reweighted(labeled, {S: 100, D: 900})
    assert r["sensitivity"] == pytest.approx(90 / 270)
    assert r["specificity"] == pytest.approx(720 / 730)
    assert r["ppv"] == pytest.approx(0.9)
    assert r["human_disagreement_cert"] == pytest.approx(730 / 1000)
    assert r["fp_disagreement_cert"] == pytest.approx(0.9)
    # the unweighted sample would say sens = 9/11 -- the bias this corrects
    assert r["sensitivity"] < 9 / 11


def test_kappa_and_bootstrap_shape():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    st = {("s",): [(1, 1), (0, 0), (1, 0), (0, 1), (1, 1), (0, 0)]}
    out = stratified_bootstrap(st, lambda s: {"k": cohen_kappa([p[0] for v in s.values() for p in v],
                                                              [p[1] for v in s.values() for p in v])},
                               n_boot=500)
    lo, hi = out["k"]["ci95"]
    assert lo <= out["k"]["estimate"] <= hi


def test_changed_lines():
    assert changed_lines("a\nb\n", "a\nb\n") == (0, 0.0)
    n, share = changed_lines("a\nb\nc", "a\nx\nc")
    assert n == 2 and share == pytest.approx(2 / 6)
