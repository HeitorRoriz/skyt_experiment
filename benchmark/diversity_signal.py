"""Exploratory: form diversity among Base-passers vs Extra-test failure.

Reads existing overlay jsonl. Does not call an API and does not write into
frozen trees. Imports fingerprint, config_repeatability, and the cluster
bootstrap helper; it does not redefine them.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import statistics
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from benchmark.metrics import _percentile, cluster_bootstrap_mean, config_repeatability
from benchmark.protect import ProtectedOutputError, assert_writable, is_protected
from benchmark.relation import RELATION_VERSION, fingerprint
from benchmark.score import _iter_jsonl
from benchmarks.humaneval_plus.provenance import atomic_write_json

REPO_ROOT = Path(__file__).resolve().parents[1]
PREREG_RELATIVE = Path("docs/internal/DIVERSITY_SIGNAL_PREREG_2026-09-24.md")
BOOTSTRAP_SEED = 20260723

ConfigKey = Tuple[str, str, Optional[float]]


class DiversitySignalError(RuntimeError):
    """Raised when a generation or a cross-check violates the protocol."""


def _forbidden_write(out_dir: Path) -> None:
    """Refuse frozen trees and any held-out, oracle-split, or expansion tree."""
    assert_writable(out_dir)
    resolved = out_dir.expanduser().resolve()
    parts = {part.lower() for part in resolved.parts}
    blocked_tokens = ("heldout", "oracle_split", "expansion", "gate0")
    if any(token in part for part in parts for token in blocked_tokens):
        raise ProtectedOutputError(
            f"Refusing to write into a protected analysis tree: {out_dir}"
        )
    if is_protected(resolved):
        raise ProtectedOutputError(f"Refusing to write into {out_dir}")


def _cell_label(model: str, temperature: Optional[float]) -> str:
    if temperature is None:
        return f"{model} default"
    return f"{model} T={temperature:.1f}"


def _form_keys(codes: Sequence[str]) -> List[str]:
    """Hashable canonical key. Unparseable programs are singletons."""
    keys: List[str] = []
    for index, code in enumerate(codes):
        token = fingerprint(code or "")
        keys.append(token if token is not None else f"__unparsed_{index}")
    return keys


def diversity_from_sizes(sizes: Sequence[int], n: int) -> Optional[float]:
    """1 - same@2. None when fewer than two programs."""
    if n < 2:
        return None
    numerator = sum(size * (size - 1) for size in sizes)
    return 1.0 - (numerator / (n * (n - 1)))


def shannon_entropy(sizes: Sequence[int], n: int) -> Optional[float]:
    """Shannon entropy of form shares, bits. None when n = 0."""
    if n <= 0:
        return None
    total = 0.0
    for size in sizes:
        if size <= 0:
            continue
        share = size / n
        total -= share * math.log2(share)
    return total


def loo_roles(keys: Sequence[str]) -> Tuple[List[int], List[int], List[int]]:
    """Return modal, non-modal, and unclassified indexes under LOO mode.

    A program is unclassified when two or more classes tie for largest
    after it is removed. Extra outcomes are not an input.
    """
    counts: Counter[str] = Counter(keys)
    modal: List[int] = []
    nonmodal: List[int] = []
    unclassified: List[int] = []
    for index, key in enumerate(keys):
        reduced = counts.copy()
        reduced[key] -= 1
        if reduced[key] == 0:
            del reduced[key]
        if not reduced:
            unclassified.append(index)
            continue
        largest = max(reduced.values())
        leaders = [name for name, size in reduced.items() if size == largest]
        if len(leaders) != 1:
            unclassified.append(index)
        elif key == leaders[0]:
            modal.append(index)
        else:
            nonmodal.append(index)
    return modal, nonmodal, unclassified


def _ranks(values: Sequence[float]) -> List[float]:
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(values):
        end = cursor
        while (
            end + 1 < len(values)
            and values[order[end + 1]] == values[order[cursor]]
        ):
            end += 1
        average = (cursor + end) / 2.0 + 1.0
        for position in range(cursor, end + 1):
            ranks[order[position]] = average
        cursor = end + 1
    return ranks


def _pearson(left: Sequence[float], right: Sequence[float]) -> Optional[float]:
    n = len(left)
    if n != len(right) or n < 2:
        return None
    mean_left = statistics.mean(left)
    mean_right = statistics.mean(right)
    cov = sum(
        (a - mean_left) * (b - mean_right) for a, b in zip(left, right)
    )
    var_left = math.sqrt(sum((a - mean_left) ** 2 for a in left))
    var_right = math.sqrt(sum((b - mean_right) ** 2 for b in right))
    if var_left == 0.0 or var_right == 0.0:
        return None
    return cov / (var_left * var_right)


def spearman(left: Sequence[float], right: Sequence[float]) -> Optional[float]:
    if len(left) < 2:
        return None
    return _pearson(_ranks(left), _ranks(right))


def _residualize(outcome: Sequence[float], control: Sequence[float]) -> List[float]:
    mean_y = statistics.mean(outcome)
    mean_x = statistics.mean(control)
    var_x = sum((value - mean_x) ** 2 for value in control)
    if var_x == 0.0:
        return [value - mean_y for value in outcome]
    cov = sum(
        (y - mean_y) * (x - mean_x) for y, x in zip(outcome, control)
    )
    slope = cov / var_x
    return [
        y - (mean_y + slope * (x - mean_x)) for y, x in zip(outcome, control)
    ]


def partial_spearman(
    left: Sequence[float],
    right: Sequence[float],
    control: Sequence[float],
) -> Optional[float]:
    """Spearman of rank-residuals after linear control for ``control``."""
    if len(left) < 3:
        return None
    ranked_left = _ranks(left)
    ranked_right = _ranks(right)
    ranked_control = _ranks(control)
    return _pearson(
        _residualize(ranked_left, ranked_control),
        _residualize(ranked_right, ranked_control),
    )


def task_demeaned_spearman(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["task_id"])].append(row)
    left: List[float] = []
    right: List[float] = []
    for group in grouped.values():
        if len(group) < 2:
            continue
        mean_d = statistics.mean(float(row["D_c"]) for row in group)
        mean_f = statistics.mean(float(row["F_c"]) for row in group)
        for row in group:
            left.append(float(row["D_c"]) - mean_d)
            right.append(float(row["F_c"]) - mean_f)
    return spearman(left, right)


def _load_records(source_dir: Path) -> List[Dict[str, Any]]:
    files = sorted(source_dir.glob("*.jsonl"))
    if not files:
        raise DiversitySignalError(f"No *.jsonl files in {source_dir}")
    records: List[Dict[str, Any]] = []
    for path in files:
        for record in _iter_jsonl(path):
            if record.get("repair_applied"):
                raise DiversitySignalError(
                    f"{path.name}: diversity analysis refuses repair_applied records"
                )
            if record.get("style_contract"):
                raise DiversitySignalError(
                    f"{path.name}: diversity analysis refuses style-contract records"
                )
            records.append(record)
    if not records:
        raise DiversitySignalError(f"No generation records in {source_dir}")
    return records


def _oracle_bool(record: Dict[str, Any], name: str) -> bool:
    oracle = record.get("oracle") or {}
    return bool(oracle.get(name))


def config_row(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """One configuration. Forms and the LOO mode use Base pass only."""
    task_id = str(records[0]["task_id"])
    model = str(records[0]["model"])
    raw_temp = records[0].get("temperature", 0.0)
    temperature = None if raw_temp is None else float(raw_temp)
    ordered = sorted(records, key=lambda record: int(record.get("run_index", -1)))
    base_records = [record for record in ordered if _oracle_bool(record, "base_passed")]
    for record in base_records:
        if _oracle_bool(record, "plus_passed") and not _oracle_bool(record, "base_passed"):
            raise DiversitySignalError(
                f"{task_id} {model}: plus_passed without base_passed"
            )
    keys = _form_keys([record.get("stitched_code") or "" for record in base_records])
    sizes = list(Counter(keys).values())
    n_c = len(base_records)
    extra_survived = sum(1 for record in base_records if _oracle_bool(record, "plus_passed"))
    f_c = None if n_c == 0 else 1.0 - (extra_survived / n_c)
    d_c = diversity_from_sizes(sizes, n_c)
    modal, nonmodal, unclassified = loo_roles(keys) if n_c else ([], [], [])
    plus_flags = [_oracle_bool(record, "plus_passed") for record in base_records]

    def _rate(indexes: Sequence[int]) -> Optional[float]:
        if not indexes:
            return None
        return statistics.mean(1.0 if plus_flags[index] else 0.0 for index in indexes)

    s_mod = _rate(modal)
    s_non = _rate(nonmodal)
    return {
        "task_id": task_id,
        "model": model,
        "temperature": temperature,
        "cell": _cell_label(model, temperature),
        "n_c": n_c,
        "n_forms": len(sizes),
        "D_c": d_c,
        "F_c": f_c,
        "entropy": shannon_entropy(sizes, n_c),
        "n_modal": len(modal),
        "n_nonmodal": len(nonmodal),
        "n_unclassified": len(unclassified),
        "s_mod": s_mod,
        "s_non": s_non,
        "delta": None if s_mod is None or s_non is None else s_mod - s_non,
        "a1_eligible": bool(modal) and bool(nonmodal),
        "a2_eligible": n_c >= 2 and d_c is not None and f_c is not None,
        "base_records": base_records,
        "keys": keys,
    }


def _ci_from_draws(draws: Sequence[Optional[float]]) -> Dict[str, Any]:
    finite = [float(value) for value in draws if value is not None and math.isfinite(value)]
    if not finite:
        return {
            "lower": None,
            "upper": None,
            "n_defined": 0,
            "n_undefined": len(draws),
        }
    ordered = sorted(finite)
    return {
        "lower": _percentile(ordered, 0.025),
        "upper": _percentile(ordered, 0.975),
        "n_defined": len(finite),
        "n_undefined": len(draws) - len(finite),
    }


def _mean_ci_matches_helper(
    values: Sequence[float],
    cluster_ids: Sequence[str],
    *,
    n_bootstrap: int,
    seed: int,
) -> Dict[str, float]:
    """Paper helper. Used to lock the pooled-mean interval."""
    result = cluster_bootstrap_mean(
        values,
        cluster_ids,
        n_bootstrap=n_bootstrap,
        seed=seed,
    )
    return {
        "mean": result["mean"],
        "lower": result["lower"],
        "upper": result["upper"],
        "n_clusters": result["n_clusters"],
        "n_observations": result["n_observations"],
    }


def _task_means(rows: Sequence[Dict[str, Any]], field: str) -> Dict[str, float]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        grouped[str(row["task_id"])].append(float(value))
    return {task: statistics.mean(values) for task, values in grouped.items()}


def _point_from_task_means(task_means: Dict[str, float]) -> Optional[float]:
    if not task_means:
        return None
    return statistics.mean(task_means.values())


def _spearman_rows(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if len(rows) < 2:
        return None
    return spearman(
        [float(row["D_c"]) for row in rows],
        [float(row["F_c"]) for row in rows],
    )


def _partial_rows(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    if len(rows) < 3:
        return None
    return partial_spearman(
        [float(row["D_c"]) for row in rows],
        [float(row["F_c"]) for row in rows],
        [float(row["n_c"]) / 20.0 for row in rows],
    )


def _positive_tertile_edges(values: Sequence[float]) -> Tuple[float, float]:
    ordered = sorted(values)
    if len(ordered) < 3:
        raise DiversitySignalError("Need at least three positive D_c values for tertiles")
    return (
        _percentile(ordered, 1.0 / 3.0),
        _percentile(ordered, 2.0 / 3.0),
    )


def _bin_name(d_value: float, low: float, high: float) -> str:
    if d_value == 0.0:
        return "D=0"
    if d_value <= low:
        return "T1"
    if d_value <= high:
        return "T2"
    return "T3"


def _bin_task_means(
    rows: Sequence[Dict[str, Any]],
    low: float,
    high: float,
) -> Dict[str, Dict[str, float]]:
    grouped: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        name = _bin_name(float(row["D_c"]), low, high)
        grouped[name][str(row["task_id"])].append(float(row["F_c"]))
    return {
        name: {task: statistics.mean(values) for task, values in tasks.items()}
        for name, tasks in grouped.items()
    }


def joint_bootstrap(
    a1_rows: Sequence[Dict[str, Any]],
    a2_rows: Sequence[Dict[str, Any]],
    *,
    n_bootstrap: int,
    seed: int,
    edges: Tuple[float, float],
) -> Dict[str, Any]:
    """One task draw per replicate, shared by every cell and every statistic."""
    tasks = sorted({str(row["task_id"]) for row in list(a1_rows) + list(a2_rows)})
    if len(tasks) < 2:
        raise DiversitySignalError("Need at least two tasks to bootstrap")
    cells = sorted({str(row["cell"]) for row in list(a1_rows) + list(a2_rows)})
    a1_by_cell = {
        cell: [row for row in a1_rows if row["cell"] == cell] for cell in cells
    }
    a2_by_cell = {
        cell: [row for row in a2_rows if row["cell"] == cell] for cell in cells
    }
    a1_means = {
        field: _task_means(a1_rows, field) for field in ("s_mod", "s_non", "delta")
    }
    a1_cell_means = {
        cell: {field: _task_means(rows, field) for field in ("s_mod", "s_non", "delta")}
        for cell, rows in a1_by_cell.items()
    }
    a2_by_task: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in a2_rows:
        a2_by_task[str(row["task_id"])].append(row)
    a2_cell_by_task = {
        cell: _group_by_task(rows) for cell, rows in a2_by_cell.items()
    }
    sensitive = [row for row in a2_rows if int(row["n_c"]) >= 10]
    sensitive_by_task = _group_by_task(sensitive)
    low, high = edges
    bin_means = _bin_task_means(a2_rows, low, high)
    bin_cell_means = {
        cell: _bin_task_means(rows, low, high) for cell, rows in a2_by_cell.items()
    }
    bin_names = ("D=0", "T1", "T2", "T3")

    rng = random.Random(seed)
    store: Dict[str, List[Optional[float]]] = defaultdict(list)
    for _ in range(n_bootstrap):
        drawn = rng.choices(tasks, k=len(tasks))
        for field, mapping in a1_means.items():
            store[f"a1.{field}"].append(_resampled_mean(mapping, drawn))
        for cell, fields in a1_cell_means.items():
            for field, mapping in fields.items():
                store[f"a1.{cell}.{field}"].append(_resampled_mean(mapping, drawn))
        drawn_a2 = _expand(a2_by_task, drawn)
        store["a2.rho"].append(_spearman_rows(drawn_a2))
        store["a2.partial"].append(_partial_rows(drawn_a2))
        store["a2.within"].append(task_demeaned_spearman(drawn_a2))
        drawn_sensitive = _expand(sensitive_by_task, drawn)
        store["a2.sensitive_rho"].append(_spearman_rows(drawn_sensitive))
        store["a2.sensitive_partial"].append(_partial_rows(drawn_sensitive))
        for cell, grouped in a2_cell_by_task.items():
            drawn_cell = _expand(grouped, drawn)
            store[f"a2.{cell}.rho"].append(_spearman_rows(drawn_cell))
            store[f"a2.{cell}.partial"].append(_partial_rows(drawn_cell))
            store[f"a2.{cell}.within"].append(task_demeaned_spearman(drawn_cell))
        for name in bin_names:
            store[f"bin.{name}"].append(_resampled_mean(bin_means.get(name, {}), drawn))
            for cell, mapping in bin_cell_means.items():
                store[f"bin.{cell}.{name}"].append(
                    _resampled_mean(mapping.get(name, {}), drawn)
                )
    return {key: _ci_from_draws(values) for key, values in store.items()}


def _group_by_task(rows: Sequence[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["task_id"])].append(row)
    return grouped


def _expand(
    grouped: Dict[str, List[Dict[str, Any]]],
    drawn: Sequence[str],
) -> List[Dict[str, Any]]:
    selected: List[Dict[str, Any]] = []
    for task in drawn:
        selected.extend(grouped.get(task, []))
    return selected


def _resampled_mean(task_means: Dict[str, float], drawn: Sequence[str]) -> Optional[float]:
    values = [task_means[task] for task in drawn if task in task_means]
    if not values:
        return None
    return statistics.mean(values)


def _estimate_block(
    point: Optional[float],
    interval: Dict[str, Any],
    *,
    n_configs: int,
    n_tasks: int,
) -> Dict[str, Any]:
    return {
        "estimate": point,
        "ci95": (
            [interval["lower"], interval["upper"]]
            if point is not None and interval.get("lower") is not None
            else None
        ),
        "n_configs": n_configs,
        "n_tasks": n_tasks,
        "n_bootstrap_defined": interval.get("n_defined"),
        "n_bootstrap_undefined": interval.get("n_undefined"),
    }


def _generation_pooled(rows: Sequence[Dict[str, Any]]) -> Dict[str, Optional[float]]:
    modal_n = sum(int(row["n_modal"]) for row in rows)
    non_n = sum(int(row["n_nonmodal"]) for row in rows)
    modal_surv = sum(float(row["s_mod"]) * int(row["n_modal"]) for row in rows)
    non_surv = sum(float(row["s_non"]) * int(row["n_nonmodal"]) for row in rows)
    return {
        "s_mod": None if modal_n == 0 else modal_surv / modal_n,
        "s_non": None if non_n == 0 else non_surv / non_n,
        "n_modal_programs": modal_n,
        "n_nonmodal_programs": non_n,
    }


def cross_check(rows: Sequence[Dict[str, Any]], *, seed: int, n_configs: int = 5) -> None:
    """A3. Plus certification must match config_repeatability exactly."""
    eligible = [row for row in rows if row["a2_eligible"]]
    if len(eligible) < n_configs:
        raise DiversitySignalError("Not enough configurations for the A3 cross-check")
    rng = random.Random(seed)
    picked = rng.sample(eligible, n_configs)
    for row in picked:
        _cross_check_one(row)


def _certified_diversity(records: Sequence[Dict[str, Any]], flag: str) -> Optional[float]:
    prints = [fingerprint(record.get("stitched_code") or "") for record in records]
    certified = [
        token is not None and _oracle_bool(record, flag)
        for record, token in zip(records, prints)
    ]
    analysis = config_repeatability(prints, certified)
    given = analysis["same_at_2_given_cert"]
    if given is None:
        return None
    keys = _form_keys(
        [
            record.get("stitched_code") or ""
            for record, ok in zip(records, certified)
            if ok
        ]
    )
    n = len(keys)
    ours = diversity_from_sizes(list(Counter(keys).values()), n)
    if ours is None or abs(ours - (1.0 - given)) > 1e-9:
        raise DiversitySignalError(
            "A3 mismatch: diversity disagrees with 1 - same@2|cert "
            f"for {flag} ({ours} vs {None if given is None else 1.0 - given})"
        )
    return ours


def _cross_check_one(row: Dict[str, Any]) -> None:
    records = row["base_records"]
    # Base-certified same@2|cert on the Base-passing set. D_c uses that set.
    prints = [fingerprint(record.get("stitched_code") or "") for record in records]
    certified = [token is not None for token in prints]
    if not all(certified):
        # Unparseable Base-passers are singletons in D_c and are not certified
        # by the scorer. Compare D_c to the scorer on the parseable subset only
        # when every Base-passer parses; otherwise require the parseable
        # Base subset and the full Plus subset to match, and require D_c to
        # match the singleton-aware pair rate.
        _certified_diversity(records, "base_passed")
    else:
        analysis = config_repeatability(prints, certified)
        given = analysis["same_at_2_given_cert"]
        if given is None or row["D_c"] is None or abs(row["D_c"] - (1.0 - given)) > 1e-9:
            raise DiversitySignalError(
                f"A3 Base mismatch on {row['task_id']} {row['cell']}: "
                f"D_c={row['D_c']} vs 1-same@2|cert="
                f"{None if given is None else 1.0 - given}"
            )
    _certified_diversity(records, "plus_passed")
    full_prints = prints
    full_certified = [
        token is not None and _oracle_bool(record, "plus_passed")
        for record, token in zip(records, full_prints)
    ]
    if sum(full_certified) >= 2:
        plus_analysis = config_repeatability(full_prints, full_certified)
        plus_given = plus_analysis["same_at_2_given_cert"]
        plus_keys = [
            token
            for token, ok in zip(full_prints, full_certified)
            if ok
        ]
        plus_d = diversity_from_sizes(list(Counter(plus_keys).values()), len(plus_keys))
        if plus_given is None or plus_d is None or abs(plus_d - (1.0 - plus_given)) > 1e-9:
            raise DiversitySignalError(
                f"A3 Plus mismatch on {row['task_id']} {row['cell']}"
            )


def _git_hash() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def _prereg_hash(path: Path) -> str:
    if not path.is_file():
        raise DiversitySignalError(
            f"Pre-registration note is missing: {path}. Write it before computing."
        )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def analyze(
    source_dirs: Sequence[Path],
    out_dir: Path,
    *,
    n_bootstrap: int = 10000,
    seed: int = BOOTSTRAP_SEED,
    prereg_path: Path = REPO_ROOT / PREREG_RELATIVE,
) -> Dict[str, Any]:
    _forbidden_write(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prereg_digest = _prereg_hash(prereg_path)
    (out_dir / "prereg_hash.txt").write_text(prereg_digest + "\n", encoding="utf-8")

    grouped: Dict[ConfigKey, List[Dict[str, Any]]] = defaultdict(list)
    for source in source_dirs:
        for record in _load_records(source):
            task_id = record.get("task_id")
            model = record.get("model")
            if task_id is None or model is None:
                continue
            raw_temp = record.get("temperature", 0.0)
            temperature = None if raw_temp is None else float(raw_temp)
            if _oracle_bool(record, "plus_passed") and not _oracle_bool(record, "base_passed"):
                raise DiversitySignalError(
                    f"{task_id} {model}: plus_passed without base_passed"
                )
            grouped[(str(task_id), str(model), temperature)].append(record)
    if not grouped:
        raise DiversitySignalError("No configurations loaded")

    rows = [config_row(records) for records in grouped.values()]
    cross_check(rows, seed=seed)

    a1_rows = [row for row in rows if row["a1_eligible"]]
    a2_rows = [row for row in rows if row["a2_eligible"]]
    positive = [float(row["D_c"]) for row in a2_rows if float(row["D_c"]) > 0.0]
    edges = _positive_tertile_edges(positive)
    intervals = joint_bootstrap(
        a1_rows,
        a2_rows,
        n_bootstrap=n_bootstrap,
        seed=seed,
        edges=edges,
    )
    helper_delta = _mean_ci_matches_helper(
        [float(row["delta"]) for row in a1_rows],
        [str(row["task_id"]) for row in a1_rows],
        n_bootstrap=n_bootstrap,
        seed=seed,
    )

    def pack_a1(selected: Sequence[Dict[str, Any]], prefix: str) -> Dict[str, Any]:
        tasks = {str(row["task_id"]) for row in selected}
        block = {}
        for field in ("s_mod", "s_non", "delta"):
            block[field] = _estimate_block(
                _point_from_task_means(_task_means(selected, field)),
                intervals[f"{prefix}{field}"],
                n_configs=len(selected),
                n_tasks=len(tasks),
            )
        block["generation_pooled"] = _generation_pooled(selected)
        return block

    def pack_rho(selected: Sequence[Dict[str, Any]], key: str) -> Dict[str, Any]:
        tasks = {str(row["task_id"]) for row in selected}
        return _estimate_block(
            _spearman_rows(selected),
            intervals[key],
            n_configs=len(selected),
            n_tasks=len(tasks),
        )

    cells = sorted({str(row["cell"]) for row in rows})
    a1_cells = {}
    a2_cells = {}
    for cell in cells:
        selected_a1 = [row for row in a1_rows if row["cell"] == cell]
        selected_a2 = [row for row in a2_rows if row["cell"] == cell]
        if selected_a1:
            a1_cells[cell] = pack_a1(selected_a1, f"a1.{cell}.")
        if selected_a2:
            a2_cells[cell] = {
                "rho": pack_rho(selected_a2, f"a2.{cell}.rho"),
                "partial_rho": _estimate_block(
                    _partial_rows(selected_a2),
                    intervals[f"a2.{cell}.partial"],
                    n_configs=len(selected_a2),
                    n_tasks=len({row["task_id"] for row in selected_a2}),
                ),
                "within_task_rho": _estimate_block(
                    task_demeaned_spearman(selected_a2),
                    intervals[f"a2.{cell}.within"],
                    n_configs=len(selected_a2),
                    n_tasks=len({row["task_id"] for row in selected_a2}),
                ),
            }

    bin_names = ("D=0", "T1", "T2", "T3")
    bin_means = _bin_task_means(a2_rows, edges[0], edges[1])
    bins_pooled = []
    for name in bin_names:
        mapping = bin_means.get(name, {})
        bins_pooled.append(
            {
                "bin": name,
                **_estimate_block(
                    _point_from_task_means(mapping),
                    intervals[f"bin.{name}"],
                    n_configs=sum(
                        1
                        for row in a2_rows
                        if _bin_name(float(row["D_c"]), edges[0], edges[1]) == name
                    ),
                    n_tasks=len(mapping),
                ),
            }
        )
    bins_by_cell = {}
    for cell in cells:
        selected = [row for row in a2_rows if row["cell"] == cell]
        cell_bins = _bin_task_means(selected, edges[0], edges[1])
        bins_by_cell[cell] = []
        for name in bin_names:
            mapping = cell_bins.get(name, {})
            bins_by_cell[cell].append(
                {
                    "bin": name,
                    **_estimate_block(
                        _point_from_task_means(mapping),
                        intervals[f"bin.{cell}.{name}"],
                        n_configs=sum(
                            1
                            for row in selected
                            if _bin_name(float(row["D_c"]), edges[0], edges[1]) == name
                        ),
                        n_tasks=len(mapping),
                    ),
                }
            )

    sensitive = [row for row in a2_rows if int(row["n_c"]) >= 10]
    n_lt2 = sum(1 for row in rows if int(row["n_c"]) < 2)
    n_no_contrast = sum(1 for row in rows if int(row["n_c"]) >= 2 and not row["a1_eligible"])
    n_unclassified_programs = sum(int(row["n_unclassified"]) for row in rows)
    n_unclassified_configs = sum(1 for row in rows if int(row["n_unclassified"]) > 0)

    report = {
        "schema": "sameeval-diversity-signal-v1",
        "exploratory": True,
        "relation_version": RELATION_VERSION,
        "seed": seed,
        "n_bootstrap": n_bootstrap,
        "git_hash": _git_hash(),
        "prereg_sha256": prereg_digest,
        "prereg_path": str(prereg_path),
        "source_dirs": [str(path) for path in source_dirs],
        "n_configs": len(rows),
        "exclusions": {
            "n_c_lt_2": n_lt2,
            "a1_no_within_config_contrast": n_no_contrast,
            "a1_unclassified_programs": n_unclassified_programs,
            "configs_with_unclassified_programs": n_unclassified_configs,
            "a1_eligible_configs": len(a1_rows),
            "a1_eligible_tasks": len({row["task_id"] for row in a1_rows}),
            "a2_eligible_configs": len(a2_rows),
            "a2_eligible_tasks": len({row["task_id"] for row in a2_rows}),
        },
        "a1": {
            "pooled": pack_a1(a1_rows, "a1."),
            "cells": a1_cells,
            "helper_delta_ci": helper_delta,
            "note": (
                "Reported intervals resample tasks jointly. "
                "helper_delta_ci is cluster_bootstrap_mean on pooled delta "
                "and is not the headline interval when cell sets differ."
            ),
        },
        "a2": {
            "rho": pack_rho(a2_rows, "a2.rho"),
            "partial_rho": _estimate_block(
                _partial_rows(a2_rows),
                intervals["a2.partial"],
                n_configs=len(a2_rows),
                n_tasks=len({row["task_id"] for row in a2_rows}),
            ),
            "within_task_rho": _estimate_block(
                task_demeaned_spearman(a2_rows),
                intervals["a2.within"],
                n_configs=len(a2_rows),
                n_tasks=len({row["task_id"] for row in a2_rows}),
            ),
            "cells": a2_cells,
            "sensitivity_n_c_ge_10": {
                "rho": _estimate_block(
                    _spearman_rows(sensitive),
                    intervals["a2.sensitive_rho"],
                    n_configs=len(sensitive),
                    n_tasks=len({row["task_id"] for row in sensitive}),
                ),
                "partial_rho": _estimate_block(
                    _partial_rows(sensitive),
                    intervals["a2.sensitive_partial"],
                    n_configs=len(sensitive),
                    n_tasks=len({row["task_id"] for row in sensitive}),
                ),
            },
        },
        "bins": {
            "rule": "D=0 separate; tertiles of D_c>0 use fixed pooled edges",
            "positive_tertile_edges": [edges[0], edges[1]],
            "pooled": bins_pooled,
            "cells": bins_by_cell,
        },
        "a3": "passed",
    }
    atomic_write_json(out_dir / "diversity_signal.json", report)
    _write_csv(out_dir / "per_config.csv", rows)
    return report


def _write_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "task_id",
        "model",
        "temperature",
        "n_c",
        "n_forms",
        "D_c",
        "F_c",
        "n_modal",
        "n_nonmodal",
        "n_unclassified",
        "s_mod",
        "s_non",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (item["task_id"], item["model"], str(item["temperature"]))):
            writer.writerow({field: row.get(field) for field in fields})


def uniformity_class(f_c: float) -> str:
    """Post hoc label. Extra outcomes are not used to define forms."""
    if f_c == 0.0:
        return "all_pass"
    if f_c == 1.0:
        return "all_fail"
    if 0.0 < f_c < 1.0:
        return "mixed"
    raise DiversitySignalError(f"F_c outside [0, 1]: {f_c}")


def form_extra_uniformity(keys: Sequence[str], plus_flags: Sequence[bool]) -> Tuple[int, int]:
    """Forms with at least two Base-passers, and how many of those are uniform."""
    grouped: Dict[str, List[bool]] = defaultdict(list)
    for key, flag in zip(keys, plus_flags):
        grouped[key].append(bool(flag))
    multi = [flags for flags in grouped.values() if len(flags) >= 2]
    uniform = sum(1 for flags in multi if len(set(flags)) == 1)
    return uniform, len(multi)


def _uniformity_row(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    row = config_row(records)
    plus_flags = [_oracle_bool(record, "plus_passed") for record in row["base_records"]]
    uniform, multi = form_extra_uniformity(row["keys"], plus_flags)
    f_c = row["F_c"]
    label = None if f_c is None else uniformity_class(float(f_c))
    return {
        "task_id": row["task_id"],
        "model": row["model"],
        "temperature": row["temperature"],
        "cell": row["cell"],
        "n_c": row["n_c"],
        "F_c": f_c,
        "uniformity": label,
        "a1_eligible": row["a1_eligible"],
        "a2_eligible": row["a2_eligible"],
        "n_forms_uniform": uniform,
        "n_forms_ge2": multi,
    }


def _share_task_means(rows: Sequence[Dict[str, Any]], label: str) -> Dict[str, float]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row["task_id"])].append(1.0 if row["uniformity"] == label else 0.0)
    return {task: statistics.mean(values) for task, values in grouped.items()}


def _all_fail_given_failure_means(rows: Sequence[Dict[str, Any]]) -> Dict[str, float]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        if row["F_c"] is None or float(row["F_c"]) <= 0.0:
            continue
        grouped[str(row["task_id"])].append(1.0 if row["uniformity"] == "all_fail" else 0.0)
    return {task: statistics.mean(values) for task, values in grouped.items()}


def _form_share(rows: Sequence[Dict[str, Any]]) -> Optional[float]:
    uniform = sum(int(row["n_forms_uniform"]) for row in rows)
    multi = sum(int(row["n_forms_ge2"]) for row in rows)
    if multi == 0:
        return None
    return uniform / multi


def _count_labels(rows: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"all_pass": 0, "all_fail": 0, "mixed": 0}
    for row in rows:
        label = row["uniformity"]
        if label in counts:
            counts[label] += 1
    return counts


def posthoc_uniformity(
    source_dirs: Sequence[Path],
    out_dir: Path,
    *,
    n_bootstrap: int = 10000,
    seed: int = BOOTSTRAP_SEED,
) -> Dict[str, Any]:
    """Post hoc, descriptive. Does not write pre-registered files."""
    _forbidden_write(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    grouped: Dict[ConfigKey, List[Dict[str, Any]]] = defaultdict(list)
    for source in source_dirs:
        for record in _load_records(source):
            task_id = record.get("task_id")
            model = record.get("model")
            if task_id is None or model is None:
                continue
            raw_temp = record.get("temperature", 0.0)
            temperature = None if raw_temp is None else float(raw_temp)
            grouped[(str(task_id), str(model), temperature)].append(record)
    rows = [_uniformity_row(records) for records in grouped.values()]
    a2_rows = [row for row in rows if row["a2_eligible"]]
    tasks = sorted({str(row["task_id"]) for row in a2_rows})
    cells = sorted({str(row["cell"]) for row in a2_rows})
    by_cell = {cell: [row for row in a2_rows if row["cell"] == cell] for cell in cells}
    by_task = _group_by_task(a2_rows)

    def pack(selected: Sequence[Dict[str, Any]], prefix: str, intervals: Dict[str, Any]) -> Dict[str, Any]:
        shares = {}
        for label in ("all_pass", "all_fail", "mixed"):
            means = _share_task_means(selected, label)
            shares[label] = _estimate_block(
                _point_from_task_means(means),
                intervals[f"{prefix}{label}"],
                n_configs=len(selected),
                n_tasks=len({row["task_id"] for row in selected}),
            )
        failing = [row for row in selected if float(row["F_c"]) > 0.0]
        key_means = _all_fail_given_failure_means(selected)
        shares["all_fail_given_any_failure"] = _estimate_block(
            _point_from_task_means(key_means),
            intervals[f"{prefix}all_fail_given_any_failure"],
            n_configs=len(failing),
            n_tasks=len(key_means),
        )
        shares["counts"] = _count_labels(selected)
        shares["n_configs"] = len(selected)
        return shares

    rng = random.Random(seed)
    store: Dict[str, List[Optional[float]]] = defaultdict(list)
    labels = ("all_pass", "all_fail", "mixed")
    pooled_means = {label: _share_task_means(a2_rows, label) for label in labels}
    pooled_key = _all_fail_given_failure_means(a2_rows)
    cell_means = {
        cell: {label: _share_task_means(selected, label) for label in labels}
        for cell, selected in by_cell.items()
    }
    cell_keys = {cell: _all_fail_given_failure_means(selected) for cell, selected in by_cell.items()}
    for _ in range(n_bootstrap):
        drawn = rng.choices(tasks, k=len(tasks))
        for label, mapping in pooled_means.items():
            store[f"pooled.{label}"].append(_resampled_mean(mapping, drawn))
        store["pooled.all_fail_given_any_failure"].append(_resampled_mean(pooled_key, drawn))
        for cell, mapping in cell_means.items():
            for label, values in mapping.items():
                store[f"{cell}.{label}"].append(_resampled_mean(values, drawn))
            store[f"{cell}.all_fail_given_any_failure"].append(
                _resampled_mean(cell_keys[cell], drawn)
            )
        drawn_rows = _expand(by_task, drawn)
        store["b2.form_share"].append(_form_share(drawn_rows))
    intervals = {key: _ci_from_draws(values) for key, values in store.items()}

    claude_cell = "claude-sonnet-4-5-20250929 T=0.7"
    claude_a1 = [
        row for row in rows
        if row["cell"] == claude_cell and row["a1_eligible"]
    ]
    claude_counts = _count_labels(claude_a1)
    claude_mixed = claude_counts["mixed"]
    report = {
        "schema": "sameeval-diversity-uniformity-posthoc-v1",
        "post_hoc": True,
        "descriptive": True,
        "seed": seed,
        "n_bootstrap": n_bootstrap,
        "source_dirs": [str(path) for path in source_dirs],
        "eligibility": "n_c >= 2 (same as A2)",
        "b1": {
            "pooled": pack(a2_rows, "pooled.", intervals),
            "cells": {cell: pack(selected, f"{cell}.", intervals) for cell, selected in by_cell.items()},
        },
        "b2": _estimate_block(
            _form_share(a2_rows),
            intervals["b2.form_share"],
            n_configs=sum(int(row["n_forms_ge2"]) for row in a2_rows),
            n_tasks=len(tasks),
        ),
        "claude_4_5_t07_a1": {
            "n_configs": len(claude_a1),
            "counts": claude_counts,
            "every_config_all_pass_or_all_fail": claude_mixed == 0 and len(claude_a1) > 0,
            "stop_for_investigation": claude_mixed > 0,
        },
    }
    atomic_write_json(out_dir / "posthoc_uniformity.json", report)
    _write_uniformity_csv(out_dir / "posthoc_uniformity_per_config.csv", a2_rows)
    return report


def _write_uniformity_csv(path: Path, rows: Sequence[Dict[str, Any]]) -> None:
    fields = [
        "task_id",
        "model",
        "temperature",
        "n_c",
        "F_c",
        "uniformity",
        "a1_eligible",
        "n_forms_ge2",
        "n_forms_uniform",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (item["task_id"], item["model"], str(item["temperature"]))):
            writer.writerow({field: row.get(field) for field in fields})


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Exploratory diversity-signal analysis")
    parser.add_argument("--trees", nargs="+", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    parser.add_argument("--n-boot", type=int, default=10000)
    parser.add_argument(
        "--posthoc-uniformity",
        action="store_true",
        help="Post hoc descriptive check. Does not rewrite pre-registered outputs.",
    )
    args = parser.parse_args(argv)
    if args.posthoc_uniformity:
        posthoc_uniformity(args.trees, args.out, n_bootstrap=args.n_boot, seed=args.seed)
    else:
        analyze(args.trees, args.out, n_bootstrap=args.n_boot, seed=args.seed)


if __name__ == "__main__":
    main()
