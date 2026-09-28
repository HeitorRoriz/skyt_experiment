"""Human-study intervals for the FSE draft. No LLM, no fingerprint changes.

Population stratum weights are the census of both-parse pairs on the four
annotated cells (GPT-4o-mini and Claude Sonnet 4.5, T in {0.0, 0.7}).
"""

from __future__ import annotations

import itertools
import json
import random
import statistics
from collections import defaultdict
from pathlib import Path

from benchmark.relation import fingerprint
from benchmark.score import _is_certified
from benchmarks.humaneval_plus.provenance import atomic_write_json
from benchmarks.humaneval_plus.run import _load_existing
from skyt.annotation_sample import CELLS, N, _stratum
from skyt.annotation_score import cohen_kappa, load_gold, load_sheet
from skyt.humaneval_heldout import OVERLAY_SOURCE

SEED = 20260723
N_BOOT = 10000
ROOT = Path("outputs/benchmark/fingerprint_annotation_dual")
CELLS_SET = {(model, float(temperature)) for model, temperature in CELLS}


def _percentile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = position - lower
    return sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight


def _ci(samples):
    ordered = sorted(samples)
    return {
        "mean": statistics.mean(samples),
        "lower": _percentile(ordered, 0.025),
        "upper": _percentile(ordered, 0.975),
    }


def census():
    """Per-config stratum counts and certified-disagreement rate."""
    configs = []
    for path in sorted(OVERLAY_SOURCE.glob("*.jsonl")):
        records = sorted(
            _load_existing(path), key=lambda item: int(item.get("run_index", 0))
        )[:N]
        if len(records) < 2:
            continue
        model = records[0].get("model")
        temperature = float(records[0].get("temperature", 0.0))
        task_id = records[0].get("task_id")
        if (str(model), temperature) not in CELLS_SET or task_id is None:
            continue
        prints = [
            fingerprint(record.get("stitched_code") or "", flexible_naming=True)
            for record in records
        ]
        certified = [
            _is_certified(record, fp is not None)
            for record, fp in zip(records, prints)
        ]
        counts = defaultdict(int)
        both_cert_pairs = 0
        both_cert_diff = 0
        parsed_pairs = 0
        for i, j in itertools.combinations(range(len(records)), 2):
            if prints[i] is None or prints[j] is None:
                continue
            parsed_pairs += 1
            fp_same = prints[i] == prints[j]
            both_cert = bool(certified[i] and certified[j])
            counts[_stratum(fp_same, both_cert)] += 1
            if both_cert:
                both_cert_pairs += 1
                if not fp_same:
                    both_cert_diff += 1
        configs.append(
            {
                "task_id": str(task_id),
                "model": str(model),
                "temperature": temperature,
                "parsed_pairs": parsed_pairs,
                "strata": dict(counts),
                "both_cert_pairs": both_cert_pairs,
                "both_cert_diff": both_cert_diff,
                "certified_disagreement": (
                    both_cert_diff / both_cert_pairs if both_cert_pairs else None
                ),
            }
        )
    return configs


def _human_rates(gold, labels):
    """Per cell, P(label different | stratum) on the 8-pair samples."""
    buckets = defaultdict(list)
    for row in gold.values():
        key = (
            str(row["model"]),
            float(row["temperature"]),
            str(row["stratum"]),
        )
        buckets[key].append(int(labels[row["pair_id"]]))
    rates = {}
    for key, values in buckets.items():
        rates[key] = {
            "n": len(values),
            "p_same": sum(values) / len(values),
            "p_different": 1.0 - sum(values) / len(values),
            "labels": values,
        }
    return rates


def _task_means(configs, rate_of):
    """Equal weight per task. Within a task, defined configs are averaged.

    rate_of maps (model, T, stratum) -> P(human says different). None keeps
    the structural certified-disagreement rate.
    """
    grouped = defaultdict(list)
    for row in configs:
        if row["certified_disagreement"] is None:
            continue
        d = row["certified_disagreement"]
        if rate_of is None:
            value = d
        else:
            cell = (row["model"], row["temperature"])
            r_diff = rate_of[(*cell, "fp_diff|both_cert")]
            r_same = rate_of[(*cell, "fp_same|both_cert")]
            value = d * r_diff + (1.0 - d) * r_same
        grouped[row["task_id"]].append(value)
    return {task: statistics.mean(values) for task, values in grouped.items()}


def _mean_tasks(task_means, tasks):
    values = [task_means[task] for task in tasks if task in task_means]
    if not values:
        return None
    return statistics.mean(values)


def _reweighted(pairs, weights, design_n):
    """Stratum share split across that stratum's design count, not per draw size.

    design_n is the number of sampled pairs in the stratum (32). Disagreements
    omitted from ``pairs`` therefore reduce that stratum's weight.
    """
    sens_n = sens_d = spec_n = spec_d = 0.0
    for stratum, fp_same, human in pairs:
        w = weights[stratum] / design_n[stratum]
        if human == 1:
            sens_d += w
            if fp_same == 1:
                sens_n += w
        else:
            spec_d += w
            if fp_same == 0:
                spec_n += w
    return {
        "sensitivity": sens_n / sens_d if sens_d else None,
        "specificity": spec_n / spec_d if spec_d else None,
    }


def main():
    print("census", flush=True)
    configs = census()
    print(f"configs {len(configs)}", flush=True)
    gold = load_gold(ROOT / "gold.json")
    sheets = {
        "A": load_sheet(ROOT / "annotator_a" / "annotation_sheet.csv"),
        "B": load_sheet(ROOT / "annotator_b" / "annotation_sheet.csv"),
    }
    strata_names = [
        "fp_same|both_cert",
        "fp_same|not_both_cert",
        "fp_diff|both_cert",
        "fp_diff|not_both_cert",
    ]
    pop = defaultdict(int)
    for row in configs:
        for name, count in row["strata"].items():
            pop[name] += count
    total_pairs = sum(pop.values())
    weights = {name: pop[name] / total_pairs for name in strata_names}

    defined = [row for row in configs if row["certified_disagreement"] is not None]
    config_mean_disagreement = statistics.mean(
        row["certified_disagreement"] for row in defined
    )
    tasks = sorted({row["task_id"] for row in configs})

    # cell-level structural means
    by_cell = defaultdict(list)
    for row in defined:
        by_cell[(row["model"], row["temperature"])].append(row["certified_disagreement"])
    cell_structural = {
        f"{model}|{temperature}": statistics.mean(values)
        for (model, temperature), values in by_cell.items()
    }

    label_lists = {}
    for name, labels in sheets.items():
        label_lists[name] = _human_rates(gold, labels)

    def cell_rates(name):
        out = {}
        for key, payload in label_lists[name].items():
            out[key] = payload["p_different"]
        return out

    # annotation rows aligned for kappa / reweight
    ann_rows = []
    for row in gold.values():
        ann_rows.append(
            {
                "task_id": str(row["task_id"]),
                "stratum": str(row["stratum"]),
                "model": str(row["model"]),
                "temperature": float(row["temperature"]),
                "fp": 1 if row.get("fingerprint_same") else 0,
                "A": int(sheets["A"][row["pair_id"]]),
                "B": int(sheets["B"][row["pair_id"]]),
            }
        )

    def kappa_of(rows):
        return cohen_kappa([r["A"] for r in rows], [r["B"] for r in rows])

    kappa_point = kappa_of(ann_rows)

    def sens_spec(rows, who):
        tp = fp = tn = fn = 0
        for row in rows:
            pred, human = row["fp"], row[who]
            if pred == 1 and human == 1:
                tp += 1
            elif pred == 1 and human == 0:
                fp += 1
            elif pred == 0 and human == 0:
                tn += 1
            else:
                fn += 1
        sens = tp / (tp + fn) if (tp + fn) else None
        spec = tn / (tn + fp) if (tn + fp) else None
        agree = (tp + tn) / len(rows) if rows else None
        return {"sensitivity": sens, "specificity": spec, "agreement": agree, "n": len(rows)}

    sample_metrics = {who: sens_spec(ann_rows, who) for who in ("A", "B")}
    agreed = [row for row in ann_rows if row["A"] == row["B"]]
    for row in agreed:
        row["C"] = row["A"]
    sample_metrics["consensus"] = sens_spec(agreed, "C")

    design_n = {name: 32 for name in strata_names}
    reweighted = {}
    for who in ("A", "B"):
        reweighted[who] = _reweighted(
            [(r["stratum"], r["fp"], r[who]) for r in ann_rows],
            weights,
            design_n,
        )
    reweighted["consensus"] = _reweighted(
        [(r["stratum"], r["fp"], r["C"]) for r in agreed],
        weights,
        design_n,
    )

    structural_by_task = _task_means(configs, None)
    structural_point = statistics.mean(structural_by_task.values())
    impl_by_task = {}
    impl_point = {}
    for who in ("A", "B"):
        impl_by_task[who] = _task_means(configs, cell_rates(who))
        impl_point[who] = statistics.mean(impl_by_task[who].values())

    rng = random.Random(SEED)
    by_stratum = defaultdict(list)
    by_task = defaultdict(list)
    for index, row in enumerate(ann_rows):
        by_stratum[row["stratum"]].append(index)
        by_task[row["task_id"]].append(index)

    kappa_strat = []
    kappa_task = []
    re_boot = {who: {"sensitivity": [], "specificity": []} for who in ("A", "B", "consensus")}
    impl_boot = {who: [] for who in ("A", "B")}
    struct_boot = []

    # Pre-index labels by cell stratum for resampling humans inside _impl
    # _impl expects a rate (float) per key, so each draw builds a rate dict.
    base_lists = {
        who: {
            key: payload["labels"][:]
            for key, payload in label_lists[who].items()
        }
        for who in ("A", "B")
    }

    for _ in range(N_BOOT):
        # stratified pair resample
        drawn = []
        for name in strata_names:
            idxs = by_stratum[name]
            drawn.extend(ann_rows[i] for i in rng.choices(idxs, k=len(idxs)))
        kappa_strat.append(kappa_of(drawn))
        agreed_b = []
        for row in drawn:
            if row["A"] == row["B"]:
                copied = dict(row)
                copied["C"] = row["A"]
                agreed_b.append(copied)
        for who in ("A", "B"):
            stats = _reweighted(
                [(r["stratum"], r["fp"], r[who]) for r in drawn],
                weights,
                design_n,
            )
            re_boot[who]["sensitivity"].append(stats["sensitivity"])
            re_boot[who]["specificity"].append(stats["specificity"])
        if agreed_b:
            stats = _reweighted(
                [(r["stratum"], r["fp"], r["C"]) for r in agreed_b],
                weights,
                design_n,
            )
            re_boot["consensus"]["sensitivity"].append(stats["sensitivity"])
            re_boot["consensus"]["specificity"].append(stats["specificity"])

        # task-cluster resample of annotation pairs
        task_draw = rng.choices(list(by_task), k=len(by_task))
        clustered = []
        for task_id in task_draw:
            clustered.extend(ann_rows[i] for i in by_task[task_id])
        if clustered:
            kappa_task.append(kappa_of(clustered))

        # structural + implementation: resample tasks, equal task weight
        task_draw = rng.choices(tasks, k=len(tasks))
        struct_boot.append(_mean_tasks(structural_by_task, task_draw))
        for who in ("A", "B"):
            rates = {}
            for key, values in base_lists[who].items():
                sample = rng.choices(values, k=len(values))
                rates[key] = 1.0 - (sum(sample) / len(sample))
            draw_means = _task_means(configs, rates)
            impl_boot[who].append(_mean_tasks(draw_means, task_draw))

    per_cell_human = {}
    for who in ("A", "B"):
        per_cell_human[who] = {
            f"{model}|{temp}|{stratum}": {
                "n": payload["n"],
                "p_different": payload["p_different"],
                "p_same": payload["p_same"],
            }
            for (model, temp, stratum), payload in label_lists[who].items()
        }

    # per-cell implementation point (no bootstrap): cell structural * cell human
    per_cell_impl = {}
    for who in ("A", "B"):
        per_cell_impl[who] = {}
        for (model, temperature), d_values in by_cell.items():
            d = statistics.mean(d_values)
            r_diff = label_lists[who][(model, temperature, "fp_diff|both_cert")][
                "p_different"
            ]
            r_same = label_lists[who][(model, temperature, "fp_same|both_cert")][
                "p_different"
            ]
            per_cell_impl[who][f"{model}|{temperature}"] = {
                "structural_disagreement": d,
                "p_human_different_given_fp_diff": r_diff,
                "p_human_different_given_fp_same": r_same,
                "implementation_disagreement": d * r_diff + (1.0 - d) * r_same,
                "n_configs": len(d_values),
            }

    payload = {
        "seed": SEED,
        "n_bootstrap": N_BOOT,
        "n_configs": len(configs),
        "n_configs_certified_defined": len(defined),
        "parsed_pairs": total_pairs,
        "population_stratum_share": weights,
        "population_stratum_count": dict(pop),
        "structural_certified_disagreement": {
            "point_task_mean": structural_point,
            "point_config_mean": config_mean_disagreement,
            "task_cluster_bootstrap": _ci([v for v in struct_boot if v is not None]),
            "cell": cell_structural,
            "note": (
                "Config-mean of (fingerprint-different both-certified pairs) "
                "/ (both-certified pairs), on the four annotated cells. "
                "This is 1 - same@2|cert under the paper's config mean."
            ),
        },
        "kappa": {
            "point": kappa_point,
            "stratified_bootstrap": _ci(kappa_strat),
            "task_cluster_bootstrap": _ci(kappa_task),
            "n_annotation_tasks": len(by_task),
            "primary": "stratified_bootstrap",
            "primary_reason": (
                "The 128 pairs are a stratified sample. The stratified "
                "resample matches that design. The task-cluster interval "
                "is the dependence check."
            ),
        },
        "sample_metrics": sample_metrics,
        "prevalence_reweighted": {
            who: {
                "point": reweighted[who],
                "stratified_bootstrap": {
                    "sensitivity": _ci(re_boot[who]["sensitivity"]),
                    "specificity": _ci(re_boot[who]["specificity"]),
                },
            }
            for who in ("A", "B", "consensus")
        },
        "implementation_disagreement": {
            who: {
                "point": impl_point[who],
                "bootstrap": _ci([v for v in impl_boot[who] if v is not None]),
                "per_cell": per_cell_impl[who],
            }
            for who in ("A", "B")
        },
        "per_cell_human": per_cell_human,
        "label": "post hoc descriptive for implementation_disagreement; fingerprint unchanged",
    }
    atomic_write_json(ROOT / "validity_stats.json", payload)
    print(json.dumps({
        "structural_task_mean": payload["structural_certified_disagreement"]["point_task_mean"],
        "structural_config_mean": payload["structural_certified_disagreement"]["point_config_mean"],
        "structural_ci": payload["structural_certified_disagreement"]["task_cluster_bootstrap"],
        "kappa": payload["kappa"],
        "reweighted": {k: v["point"] for k, v in payload["prevalence_reweighted"].items()},
        "impl": {k: {"point": v["point"], "ci": v["bootstrap"]} for k, v in payload["implementation_disagreement"].items()},
        "weights": weights,
    }, indent=2))


if __name__ == "__main__":
    main()
