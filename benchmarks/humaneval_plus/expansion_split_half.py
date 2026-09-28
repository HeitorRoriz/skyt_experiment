"""Split-half reliability of same@2. No API. Does not rescore oracles."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from benchmark.relation import fingerprint
from benchmark.schema import BOOTSTRAP_SEED

ROOT = Path("outputs/benchmark/humaneval_plus_164_n20_expansion/analysis")
TREES = (
    Path("outputs/benchmark/humaneval_plus_164_n20"),
    Path("outputs/benchmark/humaneval_plus_164_n20_expansion/haiku45"),
    Path("outputs/benchmark/humaneval_plus_164_n20_expansion/luna"),
    Path("outputs/benchmark/humaneval_plus_164_n20_expansion/sonnet5"),
)
N_SPLITS = 200
N_BOOT = 10000
SEED = BOOTSTRAP_SEED


def _same2(fps: Sequence[Optional[str]], certified: Sequence[bool], idx: Sequence[int]) -> float:
    hit = 0
    pairs = 0
    for a in range(len(idx)):
        for b in range(a + 1, len(idx)):
            i, j = idx[a], idx[b]
            pairs += 1
            if certified[i] and certified[j] and fps[i] is not None and fps[i] == fps[j]:
                hit += 1
    return hit / pairs


def _load_cell_records() -> Dict[Tuple[str, Optional[float]], List[dict]]:
    grouped: Dict[Tuple[str, Optional[float]], Dict[str, List[dict]]] = {}
    for tree in TREES:
        for path in sorted(tree.glob("*.jsonl")):
            rows = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
            if len(rows) < 20:
                continue
            rows = sorted(rows, key=lambda item: int(item["run_index"]))[:20]
            model = str(rows[0]["model"])
            raw_temp = rows[0].get("temperature")
            temperature = None if raw_temp is None else float(raw_temp)
            task = str(rows[0]["task_id"])
            bucket = grouped.setdefault((model, temperature), {})
            bucket[task] = rows
    return {key: [bucket[task] for task in sorted(bucket)] for key, bucket in grouped.items()}


def _prepare(rows: List[dict]) -> Tuple[List[str], np.ndarray, np.ndarray]:
    tasks = []
    halves_a = []
    halves_b = []
    for records in rows:
        task = str(records[0]["task_id"])
        tasks.append(task)
        fps = []
        certified = []
        for record in records:
            code = record.get("stitched_code") or ""
            fp = fingerprint(code) if record.get("parse_ok") else None
            ok = bool((record.get("oracle") or {}).get("plus_passed")) and fp is not None
            fps.append(fp)
            certified.append(ok)
        rng = random.Random(f"{SEED}:{task}:{records[0]['model']}:{records[0].get('temperature')}")
        a_row = []
        b_row = []
        for _ in range(N_SPLITS):
            order = list(range(20))
            rng.shuffle(order)
            a_row.append(_same2(fps, certified, order[:10]))
            b_row.append(_same2(fps, certified, order[10:]))
        halves_a.append(a_row)
        halves_b.append(b_row)
    return tasks, np.asarray(halves_a, dtype=float), np.asarray(halves_b, dtype=float)


def _corr_pair(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    if np.std(x) == 0 or np.std(y) == 0:
        return float("nan"), float("nan")
    pearson = float(np.corrcoef(x, y)[0, 1])
    rx = np.argsort(np.argsort(x)).astype(float)
    ry = np.argsort(np.argsort(y)).astype(float)
    spearman = float(np.corrcoef(rx, ry)[0, 1])
    return pearson, spearman


def _mean_defined(values: np.ndarray) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return float("nan")
    return float(finite.mean())


def _row_corr(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Pearson of paired rows. x and y are (draws, n)."""
    xc = x - x.mean(axis=1, keepdims=True)
    yc = y - y.mean(axis=1, keepdims=True)
    num = (xc * yc).sum(axis=1)
    den = np.sqrt((xc * xc).sum(axis=1) * (yc * yc).sum(axis=1))
    out = np.full(x.shape[0], np.nan)
    np.divide(num, den, out=out, where=den > 0)
    return out


def _rank_rows(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, axis=1)
    ranks = np.empty_like(order, dtype=float)
    rows = np.arange(values.shape[0])[:, None]
    ranks[rows, order] = np.arange(values.shape[1])
    return ranks


def _bootstrap(a: np.ndarray, b: np.ndarray, seed: int) -> dict:
    n, n_splits = a.shape
    rng = np.random.default_rng(seed)
    pearson = np.empty(n_splits)
    spearman = np.empty(n_splits)
    for split in range(n_splits):
        pearson[split], spearman[split] = _corr_pair(a[:, split], b[:, split])
    point_p = _mean_defined(pearson)
    point_s = _mean_defined(spearman)
    point_abs = float(np.mean(np.abs(a - b)))
    idx = rng.integers(0, n, size=(N_BOOT, n))
    boot_p = np.empty((N_BOOT, n_splits))
    boot_s = np.empty((N_BOOT, n_splits))
    boot_abs = np.empty(N_BOOT)
    abs_diff = np.abs(a - b).mean(axis=1)
    boot_abs = abs_diff[idx].mean(axis=1)
    for split in range(n_splits):
        xs = a[:, split][idx]
        ys = b[:, split][idx]
        boot_p[:, split] = _row_corr(xs, ys)
        boot_s[:, split] = _row_corr(_rank_rows(xs), _rank_rows(ys))
    boot_p_mean = np.nanmean(boot_p, axis=1)
    boot_s_mean = np.nanmean(boot_s, axis=1)

    def pack(point: float, draws: np.ndarray) -> dict:
        finite = draws[np.isfinite(draws)]
        low, high = np.percentile(finite, [2.5, 97.5])
        return {
            "estimate": point,
            "ci95": [float(low), float(high)],
            "n_bootstrap_defined": int(finite.size),
        }

    r10 = pack(point_p, boot_p_mean)
    r20_point = (2 * point_p) / (1 + point_p)
    r20_draws = (2 * boot_p_mean) / (1 + boot_p_mean)
    return {
        "r10_pearson": r10,
        "r10_spearman": pack(point_s, boot_s_mean),
        "r20_spearman_brown": pack(r20_point, r20_draws),
        "mean_abs_diff": pack(point_abs, boot_abs),
        "n_tasks": n,
        "n_splits": n_splits,
    }


def main() -> None:
    cells = _load_cell_records()
    payload = {
        "schema": "sameeval-t6-split-half-v1",
        "seed": SEED,
        "n_splits": N_SPLITS,
        "n_bootstrap": N_BOOT,
        "note": "Disjoint 10/10 halves. r10 is the mean over splits of the cross-config correlation. r20 is the Spearman-Brown prophecy from the Pearson r10.",
        "cells": {},
    }
    for (model, temperature), rows in sorted(cells.items(), key=lambda item: (item[0][0], item[0][1] is None, -1 if item[0][1] is None else item[0][1])):
        label = f"{model}|{temperature}"
        print(label, len(rows), flush=True)
        _tasks, a, b = _prepare(rows)
        payload["cells"][label] = _bootstrap(a, b, SEED)
        print(" ", payload["cells"][label]["r10_pearson"]["estimate"], flush=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / "t6_split_half.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("WROTE", path, flush=True)


if __name__ == "__main__":
    main()
