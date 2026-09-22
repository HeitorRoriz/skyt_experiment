"""Score dual-annotator fingerprint labels. No LLM.

Gold is fingerprint_same. Human sheets must not include that column.
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _as_label(value: Any) -> Optional[int]:
    text = str(value).strip().lower()
    if text in {"", "na", "n/a", "none"}:
        return None
    if text in {"1", "same", "yes", "true"}:
        return 1
    if text in {"0", "different", "diff", "no", "false"}:
        return 0
    raise ValueError(f"unrecognized label {value!r}")


def load_sheet(path: Path) -> Dict[str, Optional[int]]:
    labels: Dict[str, Optional[int]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            pair_id = str(row["pair_id"]).strip()
            labels[pair_id] = _as_label(row.get("human_same"))
    return labels


def load_gold(path: Path) -> Dict[str, Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pairs = payload.get("pairs") or payload
    return {str(row["pair_id"]): row for row in pairs}


def cohen_kappa(left: Sequence[int], right: Sequence[int]) -> Optional[float]:
    if len(left) != len(right) or not left:
        return None
    n = float(len(left))
    agree = sum(1 for a, b in zip(left, right) if a == b) / n
    p_left = sum(left) / n
    p_right = sum(right) / n
    chance = p_left * p_right + (1.0 - p_left) * (1.0 - p_right)
    if math.isclose(chance, 1.0):
        return 1.0 if math.isclose(agree, 1.0) else 0.0
    return (agree - chance) / (1.0 - chance)


def confusion(pred: Sequence[int], gold: Sequence[int]) -> Dict[str, int]:
    tp = fp = tn = fn = 0
    for p, g in zip(pred, gold):
        if p == 1 and g == 1:
            tp += 1
        elif p == 1 and g == 0:
            fp += 1
        elif p == 0 and g == 0:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def precision_recall_f1(counts: Dict[str, int]) -> Dict[str, Optional[float]]:
    tp, fp, tn, fn = counts["tp"], counts["fp"], counts["tn"], counts["fn"]
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    specificity = tn / (tn + fp) if (tn + fp) else None
    if precision is None or recall is None or (precision + recall) == 0:
        f1 = None
    else:
        f1 = 2.0 * precision * recall / (precision + recall)
    return {
        "precision": precision,
        "recall": recall,
        "sensitivity": recall,
        "specificity": specificity,
        "f1": f1,
    }


def _paired(
    left: Dict[str, Optional[int]],
    right: Dict[str, Optional[int]],
) -> Tuple[List[int], List[int], List[str]]:
    ids = sorted(set(left) & set(right))
    a: List[int] = []
    b: List[int] = []
    kept: List[str] = []
    for pair_id in ids:
        if left[pair_id] is None or right[pair_id] is None:
            continue
        a.append(int(left[pair_id]))
        b.append(int(right[pair_id]))
        kept.append(pair_id)
    return a, b, kept


def score(
    gold: Dict[str, Dict[str, Any]],
    sheets: Dict[str, Dict[str, Optional[int]]],
) -> Dict[str, Any]:
    annotators = sorted(sheets)
    human_human = None
    if len(annotators) >= 2:
        a, b, ids = _paired(sheets[annotators[0]], sheets[annotators[1]])
        human_human = {
            "annotators": annotators[:2],
            "n_both_labeled": len(ids),
            "kappa": cohen_kappa(a, b),
            "raw_agreement": (sum(x == y for x, y in zip(a, b)) / len(a)) if a else None,
        }

    vs_fingerprint = {}
    for name, labels in sheets.items():
        pred: List[int] = []
        human: List[int] = []
        for pair_id, row in gold.items():
            if labels.get(pair_id) is None:
                continue
            pred.append(1 if row.get("fingerprint_same") else 0)
            human.append(int(labels[pair_id]))
        counts = confusion(pred, human) if human else {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        vs_fingerprint[name] = {
            "n_labeled": len(human),
            "n_unlabeled": sum(1 for pair_id in gold if labels.get(pair_id) is None),
            "confusion": counts,
            **precision_recall_f1(counts),
        }

    majority: Dict[str, Optional[int]] = {}
    if len(annotators) >= 2:
        for pair_id in gold:
            values = [
                sheets[name].get(pair_id)
                for name in annotators
                if sheets[name].get(pair_id) is not None
            ]
            if len(values) < 2:
                majority[pair_id] = None
            elif len(set(values)) == 1:
                majority[pair_id] = int(values[0])
            else:
                majority[pair_id] = None
        pred = []
        human = []
        for pair_id, row in gold.items():
            if majority.get(pair_id) is None:
                continue
            pred.append(1 if row.get("fingerprint_same") else 0)
            human.append(int(majority[pair_id]))
        counts = confusion(pred, human) if human else {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        vs_fingerprint["majority_agree"] = {
            "n_labeled": len(human),
            "confusion": counts,
            **precision_recall_f1(counts),
        }

    return {
        "schema": "sameeval-annotation-score-v1",
        "n_gold": len(gold),
        "human_human": human_human,
        "fingerprint_vs_human": vs_fingerprint,
        "note": (
            "Precision/recall/F1 treat fingerprint_same as the prediction and "
            "human_same as the reference. The 128-pair set is stratified, so "
            "precision and F1 are validation-sample metrics, not population "
            "prevalence estimates. Prefer kappa, raw agreement, sensitivity, "
            "and specificity."
        ),
    }


def run(
    *,
    gold_path: Path,
    sheets: Dict[str, Path],
) -> Dict[str, Any]:
    gold = load_gold(gold_path)
    loaded = {name: load_sheet(path) for name, path in sheets.items()}
    return score(gold, loaded)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Score dual fingerprint annotation.")
    parser.add_argument("--gold", required=True)
    parser.add_argument("--sheet-a")
    parser.add_argument("--sheet-b")
    parser.add_argument("--out")
    args = parser.parse_args()
    sheet_map = {}
    if args.sheet_a:
        sheet_map["A"] = Path(args.sheet_a)
    if args.sheet_b:
        sheet_map["B"] = Path(args.sheet_b)
    if not sheet_map:
        raise SystemExit("pass --sheet-a and/or --sheet-b")
    payload = run(gold_path=Path(args.gold), sheets=sheet_map)
    text = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
