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
  4. Analysis-canon statistics around Certified Consensus
     (certified mode → medoid on tied modes → lexical key). Historical
     outputs/*.json used a first-valid repair anchor; consensus replay
     artifacts used the form picked from the certified generations.
  5. Anchor-vs-consensus comparison ("unlucky first-valid" delta), using the
     stored first-valid distances for comparability with published R_anchor.
     A plain geometric medoid of all structurally valid outputs is kept only
     as a sensitivity column. Even/odd split-half remains sensitivity only.

All computation is local (no API calls). Both pre-repair (raw_outputs) and
post-repair (repaired_outputs) passes are computed.

Scopes are reported separately, never merged (working agreement):
  - SBES scope: 12 base contracts.
  - MSR scope: 15 tasks (12 base + 3 *_strict).

Outputs (defaults; override with --out-dir):
  outputs/gate0/gate0_per_config.csv          historical first-valid repair
  outputs/gate0_consensus/                     Certified Consensus repair replay
  *.png  (comparison plots under the chosen --out-dir)
"""

import argparse
import csv
import glob
import hashlib
import itertools
import json
import os
import re
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from contract_compliance import check_contract_compliance  # noqa: E402
from foundational_properties import FoundationalProperties  # noqa: E402
from repeatability_protocol import (  # noqa: E402
    ZERO_TOL,
    analyze_repeatability,
    build_distance_matrix as protocol_distance_matrix,
    cluster_bootstrap_mean,
    modal_share,
    repeated_balanced_cv,
)

OUTPUTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
GATE0_DIR = os.path.join(OUTPUTS_DIR, "gate0")
POST_ORACLE_CACHE = os.path.join(GATE0_DIR, "post_oracle_cache.json")
FILENAME_RE = re.compile(r"^(?P<contract>.+)_temp(?P<temp>[\d.]+)_(?P<ts>\d{8}_\d{6})\.json$")
CV_SPLITS = 2000
CV_SEED = 20260723


# ---------------------------------------------------------------------------
# Config selection: latest complete (successful_runs == num_runs == 20) file
# per (contract_id, model, temperature).
# ---------------------------------------------------------------------------

def select_configs(outputs_dir=None):
    outputs_dir = outputs_dir or OUTPUTS_DIR
    candidates = {}
    skipped = []
    for path in sorted(glob.glob(os.path.join(outputs_dir, "*.json"))):
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
        # Consensus replay stores canon_data=None when nothing certifies
        # (e.g. binary_search_strict). Pairwise analysis still applies.
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

def normalize_props(props):
    """Compatibility wrapper for legacy persisted property dictionaries."""
    return FoundationalProperties.normalize_properties(props)


def build_distance_matrix(fp, props_list, contract):
    """Backward-compatible full matrix for a list of valid properties."""
    return protocol_distance_matrix(
        props_list,
        lambda left, right: fp.calculate_distance(left, right, contract),
    )


def modal_cluster_share(D):
    """Largest distance-zero equivalence class among all matrix entries."""
    return modal_share(D, range(len(D))) if D else 0.0


def _legacy_split_half(D, valid_indices):
    """Keep the historical even/odd medoid estimate as sensitivity only."""
    half_a = valid_indices[0::2]
    half_b = valid_indices[1::2]
    if len(half_a) < 2 or not half_b:
        return None, None
    medoid = min(
        half_a,
        key=lambda i: statistics.mean(D[i][j] for j in half_a if j != i),
    )
    distances = [D[medoid][j] for j in half_b]
    return (
        sum(1 for value in distances if value <= ZERO_TOL) / len(distances),
        statistics.mean(distances),
    )


def _abs_norm(path):
    return os.path.normcase(os.path.normpath(os.path.abspath(path)))


def load_post_oracle_cache(gate0_dir=None):
    """Load a post-oracle cache from *this* analysis out-dir only.

    Replay files reuse original basenames. Never fall back to
    outputs/gate0/post_oracle_cache.json when writing a different out-dir:
    that cache is first-valid post oracles. Consensus replay JSONs carry
    stored behavioral_stats_post instead.
    """
    gate0_dir = gate0_dir or GATE0_DIR
    cache_path = os.path.join(gate0_dir, "post_oracle_cache.json")
    if not os.path.exists(cache_path):
        return {}
    with open(cache_path, "r", encoding="utf-8") as handle:
        cache = json.load(handle)
    if cache.get("schema") != "skyt-post-oracle-cache-v2":
        raise ValueError("Unsupported post-oracle cache schema")
    oracle_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "src",
        "oracle_system.py",
    )
    with open(oracle_path, "rb") as oracle_file:
        oracle_digest = hashlib.sha256(oracle_file.read()).hexdigest()
    if cache.get("oracle_source_sha256") != oracle_digest:
        raise ValueError(
            "Post-oracle cache was produced by a different oracle source"
        )
    return cache.get("entries") or {}


def derive_certification_mask(
    data, outputs, pass_name, post_cache_entry=None
):
    """Oracle-pass plus the repository's static compliance checker.

    Historical post results come only from the hash-bound sandbox cache. New
    runs persist ``behavioral_stats_post`` directly. Raw oracle results are
    never inherited by changed repaired outputs.
    """
    metrics = data.get("metrics") or {}
    if pass_name == "pre":
        oracle_results = (
            (metrics.get("behavioral_stats") or {}).get("oracle_results") or []
        )
        source = "stored_raw_oracle"
    elif (metrics.get("behavioral_stats_post") or {}).get("oracle_results"):
        oracle_results = (
            metrics["behavioral_stats_post"].get("oracle_results") or []
        )
        source = "stored_post_oracle"
    elif post_cache_entry:
        contract_serialized = json.dumps(
            data.get("contract") or {},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        contract_digest = hashlib.sha256(
            contract_serialized.encode("utf-8")
        ).hexdigest()
        if post_cache_entry.get("contract_sha256") != contract_digest:
            raise ValueError("Post-oracle cache contract hash does not match")
        cached_results = post_cache_entry.get("oracle_results") or []
        if len(cached_results) != len(outputs):
            raise ValueError("Post-oracle cache output count does not match data")
        for code, cached in zip(outputs, cached_results):
            digest = hashlib.sha256((code or "").encode("utf-8")).hexdigest()
            if cached.get("output_sha256") != digest:
                raise ValueError("Post-oracle cache hash does not match output")
        oracle_results = [
            cached.get("result") or {} for cached in cached_results
        ]
        source = "sandbox_post_oracle_cache"
    else:
        return None, "unavailable_no_post_oracle", None

    mask = []
    oracle_pass_mask = []
    for index, code in enumerate(outputs):
        oracle_passed = (
            bool(oracle_results[index].get("passed"))
            if index < len(oracle_results) else False
        )
        oracle_pass_mask.append(oracle_passed)
        compliant, _ = check_contract_compliance(
            code or "", data.get("contract") or {}
        )
        mask.append(oracle_passed and compliant)
    return mask, source, oracle_pass_mask


def analyze_pass(
    data,
    outputs,
    stored_distances,
    stored_r_anchor,
    certified_mask=None,
    cv_splits=CV_SPLITS,
):
    """Compute all Gate 0 measures for one pass (pre or post) of one config."""
    contract = data.get("contract") or {}
    fp = FoundationalProperties(contract)

    if len(outputs) < 2:
        return None

    extracted = [
        normalize_props(fp.extract_all_properties(code or ""))
        for code in outputs
    ]
    props_all = [
        props if any(value is not None for value in props.values()) else None
        for props in extracted
    ]
    valid_mask = [props is not None for props in props_all]
    valid_indices = [i for i, valid in enumerate(valid_mask) if valid]
    n_valid = len(valid_indices)
    certification_available = certified_mask is not None
    if certified_mask is None:
        certified_mask = [False] * len(outputs)
    if len(certified_mask) != len(outputs):
        raise ValueError("certified_mask must align with outputs")
    certified_mask = [
        bool(certified_mask[i] and valid_mask[i])
        for i in range(len(outputs))
    ]

    D = protocol_distance_matrix(
        props_all,
        lambda left, right: fp.calculate_distance(left, right, contract),
    )
    frozen = analyze_repeatability(
        D, valid_mask, certified_mask, [code or "" for code in outputs]
    )
    if certification_available:
        cv = repeated_balanced_cv(
            D,
            valid_mask,
            certified_mask,
            [code or "" for code in outputs],
            train_size=min(10, len(outputs) // 2),
            n_splits=cv_splits,
            seed=CV_SEED,
        )
    else:
        cv = {
            "cv_train_size": min(10, len(outputs) // 2),
            "cv_n_splits": 0,
            "cv_seed": CV_SEED,
            "cv_selection_rate": None,
            "cv_heldout_match_end_to_end": None,
            "cv_heldout_match_certified": None,
            "cv_heldout_distance_valid": None,
            "cv_canon_stability": None,
            "cv_n_conditional_splits": 0,
            "cv_n_stability_splits": 0,
        }

    pair_dists = [
        D[i][j]
        for i, j in itertools.combinations(valid_indices, 2)
    ]

    # Sensitivity only: geometric medoid of every structurally valid output,
    # certified or not. This is not the frozen analysis canon.
    plain_medoid_index = None
    plain_medoid_dists = []
    r_plain_medoid = None
    mean_dist_plain_medoid = None
    if n_valid >= 2:
        plain_medoid_index = min(
            valid_indices,
            key=lambda i: statistics.mean(
                D[i][j] for j in valid_indices if j != i
            ),
        )
        plain_medoid_dists = [
            D[plain_medoid_index][j]
            for j in valid_indices if j != plain_medoid_index
        ]
        r_plain_medoid = (
            1 + sum(1 for value in plain_medoid_dists if value <= ZERO_TOL)
        ) / n_valid
        mean_dist_plain_medoid = statistics.mean(plain_medoid_dists)
    r_medoid_split, mean_dist_medoid_split = _legacy_split_half(
        D, valid_indices
    )

    # Analysis canon: Certified Consensus. This block only scores the
    # already-run outputs (historical first-valid or consensus replay).
    consensus_index = frozen.get("consensus_index")
    analysis_canon_policy = (
        "certified_consensus"
        if certification_available and consensus_index is not None
        else "none"
    )
    analysis_canon_index = (
        consensus_index if analysis_canon_policy == "certified_consensus"
        else None
    )
    analysis_canon_dists = []
    r_medoid = None
    mean_dist_medoid = None
    if analysis_canon_index is not None and n_valid:
        analysis_canon_dists = [
            D[analysis_canon_index][j]
            for j in valid_indices if j != analysis_canon_index
        ]
        matching_valid = sum(
            1 for j in valid_indices
            if D[analysis_canon_index][j] is not None
            and D[analysis_canon_index][j] <= ZERO_TOL
        )
        r_medoid = matching_valid / n_valid
        mean_dist_medoid = (
            statistics.mean(analysis_canon_dists)
            if analysis_canon_dists else 0.0
        )

    # Normalize stored first-valid properties before cross-process comparison.
    canon_props = normalize_props(
        (data.get("canon_data") or {}).get("foundational_properties")
    )
    anchor_dists_recomputed = (
        [fp.calculate_distance(canon_props, props_all[i], contract)
         for i in valid_indices]
        if canon_props else []
    )
    analysis_center_props = (
        props_all[analysis_canon_index]
        if analysis_canon_index is not None else None
    )
    anchor_medoid_distance = (
        fp.calculate_distance(canon_props, analysis_center_props, contract)
        if canon_props and analysis_center_props is not None else None
    )
    anchor_plain_medoid_distance = (
        fp.calculate_distance(
            canon_props, props_all[plain_medoid_index], contract
        )
        if canon_props and plain_medoid_index is not None else None
    )
    anchor_mean = statistics.mean(stored_distances) if stored_distances else None
    anchor_mean_recomputed = (
        statistics.mean(anchor_dists_recomputed)
        if anchor_dists_recomputed else None
    )
    unlucky_delta = (
        anchor_mean - mean_dist_medoid
        if anchor_mean is not None and mean_dist_medoid is not None else None
    )
    unlucky_delta_recomputed = (
        anchor_mean_recomputed - mean_dist_medoid
        if anchor_mean_recomputed is not None and mean_dist_medoid is not None
        else None
    )

    result = {
        "n": n_valid,
        "n_total": len(outputs),
        "n_excluded": len(outputs) - n_valid,
        "mean_pairwise": frozen["pairwise_distance_valid_mean"],
        "std_pairwise": frozen["pairwise_distance_valid_std"],
        "exact_match_rate": frozen["pairwise_exact_match_valid"],
        "modal_share": frozen["valid_modal_share"],
        "analysis_canon_policy": analysis_canon_policy,
        "medoid_index_local": analysis_canon_index,
        "mean_dist_medoid": mean_dist_medoid,
        "std_dist_medoid": (
            statistics.pstdev(analysis_canon_dists)
            if analysis_canon_dists else None
        ),
        "max_dist_medoid": (
            max(analysis_canon_dists) if analysis_canon_dists else None
        ),
        "R_medoid": r_medoid,
        "plain_medoid_index": plain_medoid_index,
        "mean_dist_plain_medoid": mean_dist_plain_medoid,
        "R_plain_medoid": r_plain_medoid,
        "anchor_plain_medoid_distance": anchor_plain_medoid_distance,
        "R_medoid_split": r_medoid_split,
        "mean_dist_medoid_split": mean_dist_medoid_split,
        "anchor_medoid_distance": anchor_medoid_distance,
        "anchor_mean_stored": anchor_mean,
        "anchor_mean_recomputed": anchor_mean_recomputed,
        "R_anchor_stored": stored_r_anchor,
        "unlucky_anchor_delta": unlucky_delta,
        "unlucky_anchor_delta_recomputed": unlucky_delta_recomputed,
        "_pair_dists": pair_dists,
        "_medoid_dists": analysis_canon_dists,
        "_plain_medoid_dists": plain_medoid_dists,
        "_anchor_dists": list(stored_distances) if stored_distances else [],
    }
    result.update(frozen)
    result.update(cv)
    result["certification_available"] = certification_available
    if not certification_available:
        for field in (
            "n_certified",
            "certification_rate",
            "pairwise_exact_match_end_to_end",
            "pairwise_exact_match_certified",
            "certified_modal_mass",
            "certified_modal_share",
            "consensus_index",
            "consensus_modal_size",
        ):
            result[field] = None
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(outputs_dir=None, gate0_dir=None):
    outputs_dir = outputs_dir or OUTPUTS_DIR
    gate0_dir = gate0_dir or GATE0_DIR
    if (
        _abs_norm(gate0_dir) == _abs_norm(GATE0_DIR)
        and _abs_norm(outputs_dir) != _abs_norm(OUTPUTS_DIR)
    ):
        raise SystemExit(
            "Refusing to overwrite historical outputs/gate0 from a "
            "non-historical --source-dir. Pass --out-dir "
            "(e.g. outputs/gate0_consensus)."
        )
    os.makedirs(gate0_dir, exist_ok=True)
    configs, skipped = select_configs(outputs_dir)
    post_oracle_cache = load_post_oracle_cache(gate0_dir)
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
        cache_entry = post_oracle_cache.get(os.path.basename(path))
        certification = {
            pass_name: derive_certification_mask(
                data, outputs, pass_name, cache_entry
            )
            for pass_name, (outputs, _, _) in passes.items()
        }
        raw_oracle_mask = certification["pre"][2]
        post_oracle_mask = certification["post"][2]
        paired_regressions = paired_rescues = None
        if (
            raw_oracle_mask is not None
            and post_oracle_mask is not None
            and len(raw_oracle_mask) == len(post_oracle_mask)
        ):
            paired_regressions = sum(
                raw_passed and not post_passed
                for raw_passed, post_passed
                in zip(raw_oracle_mask, post_oracle_mask)
            )
            paired_rescues = sum(
                not raw_passed and post_passed
                for raw_passed, post_passed
                in zip(raw_oracle_mask, post_oracle_mask)
            )

        for pass_name, (outputs, stored_d, stored_r) in passes.items():
            if len(outputs) < 2:
                continue
            certified_mask, certification_source, oracle_pass_mask = (
                certification[pass_name]
            )
            res = analyze_pass(
                data, outputs, stored_d, stored_r, certified_mask
            )
            if res is None:
                continue
            is_strict = contract_id.endswith("_strict")
            metrics_behavioral = metrics.get("behavioral_stats") or {}
            row = {
                "contract_id": contract_id,
                "model": model,
                "temperature": temp,
                "is_strict": is_strict,
                "pass": pass_name,
                "source_file": os.path.basename(path),
                "certification_oracle_source": certification_source,
                "R_behavioral_stored": metrics.get("R_behavioral"),
                "behavioral_pass_rate_stored": metrics_behavioral.get("pass_rate"),
                "behavioral_pass_rate_actual": (
                    statistics.mean(oracle_pass_mask)
                    if oracle_pass_mask is not None else None
                ),
                "paired_oracle_regressions": (
                    paired_regressions if pass_name == "post" else None
                ),
                "paired_oracle_rescues": (
                    paired_rescues if pass_name == "post" else None
                ),
            }
            row.update({k: v for k, v in res.items() if not k.startswith("_")})
            rows.append(row)

            # SBES scope = base contracts only; MSR scope = base + strict.
            scopes = ["msr"] if is_strict else ["sbes", "msr"]
            for scope in scopes:
                pooled[(scope, pass_name, "pairwise")].extend(res["_pair_dists"])
                pooled[(scope, pass_name, "medoid")].extend(res["_medoid_dists"])
                pooled[(scope, pass_name, "plain_medoid")].extend(
                    res["_plain_medoid_dists"]
                )
                pooled[(scope, pass_name, "anchor")].extend(res["_anchor_dists"])
        print(f"  done: {contract_id} / {model} / T={temp}")

    # ------------------------------------------------------------------ CSV
    per_config_csv = os.path.join(gate0_dir, "gate0_per_config.csv")
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

    def mean_field(selected, field):
        values = [r[field] for r in selected if r.get(field) is not None]
        return statistics.mean(values) if values else None

    def clustered(selected, field):
        usable = [r for r in selected if r.get(field) is not None]
        if not usable:
            return None
        return cluster_bootstrap_mean(
            [r[field] for r in usable],
            [r["contract_id"] for r in usable],
            n_bootstrap=10000,
            seed=CV_SEED,
        )

    def ci_text(result):
        return (
            f"{result['lower']:.3f}..{result['upper']:.3f}"
            if result else None
        )

    summary_rows = []
    for scope in ("sbes", "msr"):
        for pass_name in ("pre", "post"):
            sel = [r for r in scope_rows(scope) if r["pass"] == pass_name]
            if not sel:
                continue
            valid_deltas = [r["unlucky_anchor_delta"] for r in sel
                            if r["unlucky_anchor_delta"] is not None]
            modal_cluster = clustered(sel, "modal_share")
            split_cluster = clustered(sel, "R_medoid_split")
            frozen_pair_cluster = clustered(
                sel, "pairwise_exact_match_end_to_end"
            )
            conditional_pair_cluster = clustered(
                sel, "pairwise_exact_match_certified"
            )
            frozen_modal_cluster = clustered(sel, "certified_modal_mass")
            certification_cluster = clustered(sel, "certification_rate")
            cv_match_cluster = clustered(
                sel, "cv_heldout_match_end_to_end"
            )
            cv_stability_cluster = clustered(sel, "cv_canon_stability")

            cells_by_contract = defaultdict(int)
            for selected_row in sel:
                cells_by_contract[selected_row["contract_id"]] += 1
            expected_cells = max(cells_by_contract.values())
            incomplete_contracts = sorted(
                contract_id
                for contract_id, count in cells_by_contract.items()
                if count != expected_cells
            )
            complete_sel = [
                selected_row for selected_row in sel
                if selected_row["contract_id"] not in incomplete_contracts
            ]
            complete_pair_cluster = clustered(
                complete_sel, "pairwise_exact_match_end_to_end"
            )
            complete_modal_cluster = clustered(
                complete_sel, "certified_modal_mass"
            )
            summary_rows.append({
                "scope": scope.upper(),
                "pass": pass_name,
                "n_configs": len(sel),
                "n_contracts": len(cells_by_contract),
                "expected_cells_per_contract": expected_cells,
                "incomplete_grid_contracts": ";".join(incomplete_contracts),
                # Historical descriptive fields (configuration-weighted).
                "mean_pairwise": mean_field(sel, "mean_pairwise"),
                "mean_exact_match_rate": mean_field(sel, "exact_match_rate"),
                "mean_modal_share": mean_field(sel, "modal_share"),
                "modal_share_ci95_cluster": ci_text(modal_cluster),
                "mean_dist_medoid": mean_field(sel, "mean_dist_medoid"),
                "mean_R_medoid": mean_field(sel, "R_medoid"),
                "mean_dist_plain_medoid": mean_field(
                    sel, "mean_dist_plain_medoid"
                ),
                "mean_R_plain_medoid": mean_field(sel, "R_plain_medoid"),
                "mean_R_medoid_split": mean_field(sel, "R_medoid_split"),
                "R_medoid_split_ci95_cluster": ci_text(split_cluster),
                "mean_dist_medoid_split": mean_field(
                    sel, "mean_dist_medoid_split"
                ),
                "mean_R_behavioral_stored": mean_field(
                    sel, "R_behavioral_stored"
                ),
                "mean_behavioral_pass_rate_stored": mean_field(
                    sel, "behavioral_pass_rate_stored"
                ),
                "mean_behavioral_pass_rate_actual": mean_field(
                    sel, "behavioral_pass_rate_actual"
                ),
                "total_paired_oracle_regressions": sum(
                    r.get("paired_oracle_regressions") or 0 for r in sel
                ),
                "total_paired_oracle_rescues": sum(
                    r.get("paired_oracle_rescues") or 0 for r in sel
                ),
                "mean_R_anchor_stored": mean_field(sel, "R_anchor_stored"),
                "mean_anchor_dist_stored": mean_field(
                    sel, "anchor_mean_stored"
                ),
                "mean_anchor_dist_recomputed": mean_field(
                    sel, "anchor_mean_recomputed"
                ),
                "mean_unlucky_anchor_delta": statistics.mean(valid_deltas) if valid_deltas else None,
                "mean_unlucky_anchor_delta_recomputed": mean_field(
                    sel, "unlucky_anchor_delta_recomputed"
                ),
                "pct_configs_anchor_is_medoid": statistics.mean(
                    1.0 if (r["anchor_medoid_distance"] is not None
                            and r["anchor_medoid_distance"] <= ZERO_TOL) else 0.0
                    for r in sel
                    if r.get("analysis_canon_policy") == "certified_consensus"
                ) if any(
                    r.get("analysis_canon_policy") == "certified_consensus"
                    for r in sel
                ) else None,
                "pct_configs_anchor_is_plain_medoid": statistics.mean(
                    1.0 if (
                        r["anchor_plain_medoid_distance"] is not None
                        and r["anchor_plain_medoid_distance"] <= ZERO_TOL
                    ) else 0.0
                    for r in sel
                    if r.get("anchor_plain_medoid_distance") is not None
                ) if any(
                    r.get("anchor_plain_medoid_distance") is not None
                    for r in sel
                ) else None,
                # Frozen FSE measures and policy evaluation. Point estimates
                # give equal weight to each contract; intervals resample them.
                "contract_mean_pairwise_exact_match_end_to_end": (
                    frozen_pair_cluster["mean"]
                    if frozen_pair_cluster else None
                ),
                "pairwise_exact_match_end_to_end_ci95_cluster": ci_text(
                    frozen_pair_cluster
                ),
                "contract_mean_pairwise_exact_match_certified": (
                    conditional_pair_cluster["mean"]
                    if conditional_pair_cluster else None
                ),
                "pairwise_exact_match_certified_n_configs": (
                    conditional_pair_cluster["n_observations"]
                    if conditional_pair_cluster else 0
                ),
                "pairwise_exact_match_certified_n_contracts": (
                    conditional_pair_cluster["n_clusters"]
                    if conditional_pair_cluster else 0
                ),
                "contract_mean_certified_modal_mass": (
                    frozen_modal_cluster["mean"]
                    if frozen_modal_cluster else None
                ),
                "certified_modal_mass_ci95_cluster": ci_text(
                    frozen_modal_cluster
                ),
                "contract_mean_certification_rate": (
                    certification_cluster["mean"]
                    if certification_cluster else None
                ),
                "contract_mean_cv_heldout_match_end_to_end": (
                    cv_match_cluster["mean"] if cv_match_cluster else None
                ),
                "cv_heldout_match_end_to_end_ci95_cluster": ci_text(
                    cv_match_cluster
                ),
                "contract_mean_cv_canon_stability": (
                    cv_stability_cluster["mean"]
                    if cv_stability_cluster else None
                ),
                "cv_canon_stability_n_configs": (
                    cv_stability_cluster["n_observations"]
                    if cv_stability_cluster else 0
                ),
                "cv_canon_stability_n_contracts": (
                    cv_stability_cluster["n_clusters"]
                    if cv_stability_cluster else 0
                ),
                "cv_canon_stability_ci95_cluster": ci_text(
                    cv_stability_cluster
                ),
                # Sensitivity for the incomplete is_prime_strict model cell.
                "complete_grid_n_contracts": (
                    len(cells_by_contract) - len(incomplete_contracts)
                ),
                "complete_grid_contract_mean_pairwise_exact_match_end_to_end": (
                    complete_pair_cluster["mean"]
                    if complete_pair_cluster else None
                ),
                "complete_grid_pairwise_exact_match_end_to_end_ci95_cluster": (
                    ci_text(complete_pair_cluster)
                ),
                "complete_grid_contract_mean_certified_modal_mass": (
                    complete_modal_cluster["mean"]
                    if complete_modal_cluster else None
                ),
                "complete_grid_certified_modal_mass_ci95_cluster": ci_text(
                    complete_modal_cluster
                ),
            })
    summary_csv = os.path.join(gate0_dir, "gate0_scope_summary.csv")
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
    make_plots(rows, pooled, gate0_dir)

    print(f"\nGate 0 analysis complete. Outputs in {gate0_dir}")


def make_plots(rows, pooled, gate0_dir):
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
            ax.hist(medoid, bins=bins, alpha=0.55,
                    label="Certified Consensus (analysis canon)",
                    density=True)
            ax.set_title(f"{scope.upper()} — {pass_name}-repair")
            ax.set_xlabel("canon distance")
            ax.legend()
        axes[0].set_ylabel("density")
        fig.suptitle(
            "Variance around the canon: first-valid runtime anchor vs Certified Consensus"
        )
        fig.tight_layout()
        fig.savefig(os.path.join(gate0_dir, f"anchor_vs_medoid_{scope}.png"), dpi=150)
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
    fig.savefig(os.path.join(gate0_dir, "unlucky_anchor_scatter.png"), dpi=150)
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
    ax.set_ylabel("anchor mean dist − Certified Consensus mean dist")
    ax.set_title(
        "Unlucky first-valid delta by model (pre-repair)\n"
        "> 0 means the stored first-valid overstates dispersion"
    )
    fig.tight_layout()
    fig.savefig(os.path.join(gate0_dir, "unlucky_delta_by_model.png"), dpi=150)
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
    fig.savefig(os.path.join(gate0_dir, "pre_vs_post_pairwise.png"), dpi=150)
    plt.close(fig)

    print(f"Wrote 5 plots to {gate0_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Gate 0 pairwise analysis. Historical outputs/gate0 = first-valid "
            "repair baseline. Use --source-dir outputs/consensus_repair "
            "--out-dir outputs/gate0_consensus for Certified Consensus replay."
        )
    )
    parser.add_argument(
        "--source-dir",
        default=OUTPUTS_DIR,
        help="Per-config JSON directory (default: historical outputs/)",
    )
    parser.add_argument(
        "--out-dir",
        default=GATE0_DIR,
        help="Write CSVs and plots here (default: outputs/gate0)",
    )
    args = parser.parse_args()
    main(outputs_dir=args.source_dir, gate0_dir=args.out_dir)
