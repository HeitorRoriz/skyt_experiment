# gate0_pairwise_analysis.py
"""
GATE 0 — Anchor-free repeatability analysis (FSE 2027 work plan, Section 2).

Computes, per experiment configuration (contract x model x temperature), from the
per-config JSONs in outputs/ (never metrics_summary.csv, which has known duplicates):

  1. Mean pairwise canon distance across all C(n,2) generation pairs (anchor-free
     dispersion; the headline Gate 0 measure).
  2. Pairwise exact-match rate (fraction of pairs at distance 0 — the anchor-free
     analog of R_anchor).
  3. Modal-form frequency (share of the largest distance-0 equivalence cluster).
  4. Medoid-centered statistics (the six-sigma-style "variance around the canon"
     with a principled, data-derived center instead of the first-compliant anchor).
  5. Anchor-vs-medoid comparison ("unlucky anchor" delta), using the stored
     anchor-relative distances for exact comparability with published numbers.

All computation is local (no API calls). Both pre-repair (raw_outputs) and
post-repair (repaired_outputs) passes are computed.

Scopes are reported separately, never merged (working agreement):
  - SBES scope: 12 base contracts.
  - MSR scope: 15 tasks (12 base + 3 *_strict).

Outputs:
  outputs/gate0/gate0_per_config.csv
  outputs/gate0/gate0_scope_summary.csv
  outputs/gate0/*.png  (comparison plots)
"""

import csv
import glob
import json
import os
import re
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from foundational_properties import FoundationalProperties  # noqa: E402

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
GATE0_DIR = os.path.join(OUTPUTS_DIR, "gate0")
FILENAME_RE = re.compile(r"^(?P<contract>.+)_temp(?P<temp>[\d.]+)_(?P<ts>\d{8}_\d{6})\.json$")
ZERO_TOL = 1e-12


# ---------------------------------------------------------------------------
# Config selection: latest complete (successful_runs == num_runs == 20) file
# per (contract_id, model, temperature).
# ---------------------------------------------------------------------------

def select_configs():
    candidates = {}
    skipped = []
    for path in sorted(glob.glob(os.path.join(OUTPUTS_DIR, "*.json"))):
        fname = os.path.basename(path)
        m = FILENAME_RE.match(fname)
        if not m:
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            skipped.append((fname, f"unreadable: {e}"))
            continue
        if data.get("successful_runs") != 20 or len(data.get("raw_outputs", [])) != 20:
            skipped.append((fname, f"incomplete ({data.get('successful_runs')} runs)"))
            continue
        if not data.get("canon_data"):
            skipped.append((fname, "no canon_data"))
            continue
        if "model" not in data:
            # Pre-schema pilot runs (2026-01-19) lack the model field; every such
            # (contract, temperature) config was verified superseded by a later
            # model-tagged run, so these are safely excluded.
            skipped.append((fname, "pre-schema (no model field), superseded"))
            continue
        key = (data["contract_id"], data["model"], float(data["temperature"]))
        ts = m.group("ts")
        if key not in candidates or ts > candidates[key][0]:
            candidates[key] = (ts, path, data)
    return candidates, skipped


# ---------------------------------------------------------------------------
# Per-config analysis
# ---------------------------------------------------------------------------

def build_distance_matrix(fp, props_list, contract):
    n = len(props_list)
    D = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = fp.calculate_distance(props_list[i], props_list[j], contract)
            D[i][j] = D[j][i] = d
    return D


def modal_cluster_share(D):
    """Largest equivalence cluster under distance == 0 (union-find)."""
    n = len(D)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if D[i][j] <= ZERO_TOL:
                ri, rj = find(i), find(j)
                if ri != rj:
                    parent[ri] = rj
    sizes = defaultdict(int)
    for i in range(n):
        sizes[find(i)] += 1
    return max(sizes.values()) / n


def analyze_pass(data, outputs, stored_distances, stored_r_anchor):
    """Compute all Gate 0 measures for one pass (pre or post) of one config."""
    contract = data.get("contract") or {}
    fp = FoundationalProperties(contract)

    props_all = [fp.extract_all_properties(code or "") for code in outputs]
    # extract_all_properties returns all-None properties for unparseable code;
    # two such outputs would spuriously compare as distance 0, so exclude them.
    parseable_idx = [i for i, p in enumerate(props_all)
                     if any(v is not None for v in p.values())]
    n_excluded = len(outputs) - len(parseable_idx)
    props = [props_all[i] for i in parseable_idx]
    n = len(props)
    if n < 2:
        return None

    D = build_distance_matrix(fp, props, contract)
    pair_dists = [D[i][j] for i in range(n) for j in range(i + 1, n)]

    mean_pairwise = statistics.mean(pair_dists)
    std_pairwise = statistics.pstdev(pair_dists)
    exact_match_rate = sum(1 for d in pair_dists if d <= ZERO_TOL) / len(pair_dists)
    modal_share = modal_cluster_share(D)

    # Medoid: generation with minimal mean distance to all others.
    row_means = [sum(D[i]) / (n - 1) for i in range(n)]
    m_idx = min(range(n), key=lambda i: row_means[i])
    medoid_dists = [D[m_idx][j] for j in range(n) if j != m_idx]
    r_medoid = (1 + sum(1 for d in medoid_dists if d <= ZERO_TOL)) / n

    # Anchor comparison. The canon may come from a different run/model (it is
    # created once per contract and reused), so compare its stored properties
    # against the medoid's freshly extracted ones — same asymmetry the runtime
    # pipeline has in compare_to_canon, hence comparable with stored numbers.
    canon_props = (data.get("canon_data") or {}).get("foundational_properties")
    anchor_medoid_distance = (
        fp.calculate_distance(canon_props, props[m_idx], contract)
        if canon_props else None
    )
    anchor_mean = statistics.mean(stored_distances) if stored_distances else None
    mean_dist_medoid = statistics.mean(medoid_dists)
    unlucky_delta = (anchor_mean - mean_dist_medoid) if anchor_mean is not None else None

    return {
        "n": n,
        "n_excluded": n_excluded,
        "mean_pairwise": mean_pairwise,
        "std_pairwise": std_pairwise,
        "exact_match_rate": exact_match_rate,
        "modal_share": modal_share,
        "medoid_index_local": m_idx,
        "mean_dist_medoid": mean_dist_medoid,
        "std_dist_medoid": statistics.pstdev(medoid_dists),
        "max_dist_medoid": max(medoid_dists),
        "R_medoid": r_medoid,
        "anchor_medoid_distance": anchor_medoid_distance,
        "anchor_mean_stored": anchor_mean,
        "R_anchor_stored": stored_r_anchor,
        "unlucky_anchor_delta": unlucky_delta,
        "_pair_dists": pair_dists,
        "_medoid_dists": medoid_dists,
        "_anchor_dists": list(stored_distances) if stored_distances else [],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(GATE0_DIR, exist_ok=True)
    configs, skipped = select_configs()
    print(f"Selected {len(configs)} configs "
          f"({len(skipped)} files skipped as incomplete/duplicate-superseded)")

    rows = []
    pooled = defaultdict(list)  # (scope, pass, kind) -> distances
    for (contract_id, model, temp), (ts, path, data) in sorted(configs.items()):
        metrics = data.get("metrics", {})
        passes = {
            "pre": (data["raw_outputs"], metrics.get("distances_pre"),
                    metrics.get("R_anchor_pre")),
            "post": (data.get("repaired_outputs", []), metrics.get("distances_post"),
                     metrics.get("R_anchor_post")),
        }
        for pass_name, (outputs, stored_d, stored_r) in passes.items():
            if len(outputs) < 2:
                continue
            res = analyze_pass(data, outputs, stored_d, stored_r)
            if res is None:
                continue
            is_strict = contract_id.endswith("_strict")
            row = {
                "contract_id": contract_id,
                "model": model,
                "temperature": temp,
                "is_strict": is_strict,
                "pass": pass_name,
                "source_file": os.path.basename(path),
            }
            row.update({k: v for k, v in res.items() if not k.startswith("_")})
            rows.append(row)

            # SBES scope = base contracts only; MSR scope = base + strict.
            scopes = ["msr"] if is_strict else ["sbes", "msr"]
            for scope in scopes:
                pooled[(scope, pass_name, "pairwise")].extend(res["_pair_dists"])
                pooled[(scope, pass_name, "medoid")].extend(res["_medoid_dists"])
                pooled[(scope, pass_name, "anchor")].extend(res["_anchor_dists"])
        print(f"  done: {contract_id} / {model} / T={temp}")

    # ------------------------------------------------------------------ CSV
    per_config_csv = os.path.join(GATE0_DIR, "gate0_per_config.csv")
    fieldnames = list(rows[0].keys())
    with open(per_config_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {per_config_csv} ({len(rows)} rows)")

    # -------------------------------------------------------- scope summary
    def scope_rows(scope):
        if scope == "sbes":
            return [r for r in rows if not r["is_strict"]]
        return rows

    summary_rows = []
    for scope in ("sbes", "msr"):
        for pass_name in ("pre", "post"):
            sel = [r for r in scope_rows(scope) if r["pass"] == pass_name]
            if not sel:
                continue
            valid_deltas = [r["unlucky_anchor_delta"] for r in sel
                            if r["unlucky_anchor_delta"] is not None]
            summary_rows.append({
                "scope": scope.upper(),
                "pass": pass_name,
                "n_configs": len(sel),
                "mean_pairwise": statistics.mean(r["mean_pairwise"] for r in sel),
                "mean_exact_match_rate": statistics.mean(r["exact_match_rate"] for r in sel),
                "mean_modal_share": statistics.mean(r["modal_share"] for r in sel),
                "mean_dist_medoid": statistics.mean(r["mean_dist_medoid"] for r in sel),
                "mean_R_medoid": statistics.mean(r["R_medoid"] for r in sel),
                "mean_R_anchor_stored": statistics.mean(
                    r["R_anchor_stored"] for r in sel if r["R_anchor_stored"] is not None),
                "mean_anchor_dist_stored": statistics.mean(
                    r["anchor_mean_stored"] for r in sel if r["anchor_mean_stored"] is not None),
                "mean_unlucky_anchor_delta": statistics.mean(valid_deltas) if valid_deltas else None,
                "pct_configs_anchor_is_medoid": statistics.mean(
                    1.0 if (r["anchor_medoid_distance"] is not None
                            and r["anchor_medoid_distance"] <= ZERO_TOL) else 0.0
                    for r in sel),
            })
    summary_csv = os.path.join(GATE0_DIR, "gate0_scope_summary.csv")
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
    print(f"Wrote {summary_csv}")

    for s in summary_rows:
        print("  " + " | ".join(
            f"{k}={v:.3f}" if isinstance(v, float) else f"{k}={v}"
            for k, v in s.items()))

    # ------------------------------------------------------------------ plots
    make_plots(rows, pooled)

    print("\nGate 0 analysis complete. Outputs in outputs/gate0/")


def make_plots(rows, pooled):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # 1. Anchor-centered vs medoid-centered distance distributions (the
    #    six-sigma overlay): if the anchor curve is wider, the unlucky-anchor
    #    confound is visible directly.
    for scope in ("sbes", "msr"):
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharey=True)
        for ax, pass_name in zip(axes, ("pre", "post")):
            anchor = pooled[(scope, pass_name, "anchor")]
            medoid = pooled[(scope, pass_name, "medoid")]
            bins = [x / 50 for x in range(51)]
            ax.hist(anchor, bins=bins, alpha=0.55, label="anchor-centered (stored)",
                    density=True)
            ax.hist(medoid, bins=bins, alpha=0.55, label="medoid-centered (Gate 0)",
                    density=True)
            ax.set_title(f"{scope.upper()} — {pass_name}-repair")
            ax.set_xlabel("canon distance")
            ax.legend()
        axes[0].set_ylabel("density")
        fig.suptitle("Variance around the canon: arbitrary anchor vs empirical medoid")
        fig.tight_layout()
        fig.savefig(os.path.join(GATE0_DIR, f"anchor_vs_medoid_{scope}.png"), dpi=150)
        plt.close(fig)

    # 2. Scatter: stored anchor-mean distance vs anchor-free pairwise mean, per
    #    config (pre-repair). Points far above the diagonal = unlucky anchors.
    pre_rows = [r for r in rows if r["pass"] == "pre" and r["anchor_mean_stored"] is not None]
    models = sorted({r["model"] for r in pre_rows})
    fig, ax = plt.subplots(figsize=(7, 6))
    for model in models:
        sel = [r for r in pre_rows if r["model"] == model]
        ax.scatter([r["mean_pairwise"] for r in sel],
                   [r["anchor_mean_stored"] for r in sel],
                   alpha=0.65, label=model, s=28)
    lim = max([r["mean_pairwise"] for r in pre_rows]
              + [r["anchor_mean_stored"] for r in pre_rows]) * 1.05
    ax.plot([0, lim], [0, lim], "k--", linewidth=1, label="y = x")
    ax.set_xlabel("mean pairwise distance (anchor-free)")
    ax.set_ylabel("mean distance to stored anchor")
    ax.set_title("Unlucky-anchor test (pre-repair, all configs)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(GATE0_DIR, "unlucky_anchor_scatter.png"), dpi=150)
    plt.close(fig)

    # 3. Unlucky-anchor delta by model (Claude-paradox check).
    fig, ax = plt.subplots(figsize=(7, 5))
    deltas_by_model = [
        [r["unlucky_anchor_delta"] for r in pre_rows
         if r["model"] == m and r["unlucky_anchor_delta"] is not None]
        for m in models
    ]
    ax.boxplot(deltas_by_model, tick_labels=models)
    ax.axhline(0.0, color="k", linewidth=1, linestyle="--")
    ax.set_ylabel("anchor mean dist − medoid mean dist")
    ax.set_title("Unlucky-anchor delta by model (pre-repair)\n> 0 means the anchor overstates dispersion")
    fig.tight_layout()
    fig.savefig(os.path.join(GATE0_DIR, "unlucky_delta_by_model.png"), dpi=150)
    plt.close(fig)

    # 4. Pre vs post pairwise dispersion (does repair tighten pairwise, not
    #    just anchor distance? — early check on contribution #4).
    fig, ax = plt.subplots(figsize=(7, 5))
    for pass_name, marker in (("pre", "o"), ("post", "s")):
        sel = [r for r in rows if r["pass"] == pass_name]
        by_model = {m: [r["mean_pairwise"] for r in sel if r["model"] == m]
                    for m in models}
        ax.plot(models, [statistics.mean(by_model[m]) for m in models],
                marker=marker, label=f"{pass_name}-repair")
    ax.set_ylabel("mean pairwise distance")
    ax.set_title("Does SKYT repair tighten pairwise dispersion?")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(GATE0_DIR, "pre_vs_post_pairwise.png"), dpi=150)
    plt.close(fig)

    print("Wrote 5 plots to outputs/gate0/")


if __name__ == "__main__":
    main()
