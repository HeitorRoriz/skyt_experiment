"""Dual-annotator scoring. No Docker, no API."""

from skyt.annotation_score import cohen_kappa, confusion, precision_recall_f1, score


def test_kappa_perfect_and_chance():
    assert cohen_kappa([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0
    assert abs(cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0]) or 0.0) < 1e-12


def test_fingerprint_vs_human_counts():
    gold = {
        "p1": {"pair_id": "p1", "fingerprint_same": True},
        "p2": {"pair_id": "p2", "fingerprint_same": True},
        "p3": {"pair_id": "p3", "fingerprint_same": False},
        "p4": {"pair_id": "p4", "fingerprint_same": False},
    }
    sheets = {
        "A": {"p1": 1, "p2": 0, "p3": 0, "p4": 0},
        "B": {"p1": 1, "p2": 0, "p3": 0, "p4": 1},
    }
    payload = score(gold, sheets)
    assert payload["human_human"]["n_both_labeled"] == 4
    counts = payload["fingerprint_vs_human"]["A"]["confusion"]
    assert counts == confusion([1, 1, 0, 0], [1, 0, 0, 0])
    stats = precision_recall_f1(counts)
    assert stats["precision"] == 0.5
    assert stats["recall"] == 1.0
    assert stats["sensitivity"] == 1.0
    assert stats["specificity"] == 2 / 3
