"""Property ablation for the structural sameness relation (Step 1A).

Read-only. Reads stored HumanEval+ generations, recomputes per-property
distances for every certified pair, and derives each ablation variant
analytically from that vector.

Distance zero under the full relation means *every* property agreed, so a pair
matches under a variant exactly when the variant's properties are all zero:

* full 14           -> nonzero set is empty
* AST fingerprint   -> 'normalized_ast_structure' is not in the nonzero set
* drop property X   -> nonzero set is a subset of {X}

A pair is **binding** when the AST fingerprint agrees but the full relation
still says "different". Binding pairs are the only evidence that the other 13
properties constrain the headline at all.

Usage:
    python -m benchmarks.structural_validity.ablation
    python -m benchmarks.structural_validity.ablation --source-dir <dir> --out-dir <dir>

No API calls. No writes outside --out-dir.
"""

from __future__ import annotations

import argparse
import json
import itertools
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.foundational_properties import FoundationalProperties

# Same contract the stored HumanEval+ analysis uses: flexible naming, so the
# α-renamed fingerprint is the one compared.
HE_CONTRACT = {"constraints": {"variable_naming": {"naming_policy": "flexible"}}}

AST_PROP = "normalized_ast_structure"

DEFAULT_SOURCE = Path("outputs/humaneval_plus/pilot")
DEFAULT_OUT = Path("outputs/validity")


def load_records(path: Path) -> List[Dict[str, Any]]:
    """Read one config jsonl, skipping a truncated trailing line."""
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # Power-loss during the pilot produced truncated last lines.
                continue
    return records


def config_identity(path: Path) -> Dict[str, str]:
    """Recover task/model/temperature from the stored filename."""
    stem = path.stem
    task = stem.split("_")[0] + "/" + stem.split("_")[1]
    temp = stem.rsplit("temp", 1)[-1] if "temp" in stem else "?"
    middle = stem.split("_", 2)[2] if stem.count("_") >= 2 else ""
    model = middle.rsplit("_temp", 1)[0] if "_temp" in middle else middle
    return {"task_id": task, "model": model, "temperature": temp}


def certified_flag(record: Dict[str, Any]) -> bool:
    oracle = record.get("oracle") or {}
    if oracle.get("plus_passed") is not None:
        return bool(oracle.get("certified"))
    return bool(oracle.get("base_passed"))


def analyze_config(
    path: Path,
    extractor: FoundationalProperties,
    properties: Sequence[str],
) -> Optional[Dict[str, Any]]:
    """Per-property distances for every certified pair in one config."""
    records = load_records(path)
    n = len(records)
    if n < 2:
        return None

    props: List[Optional[Dict[str, Any]]] = []
    for record in records:
        code = record.get("stitched_code") or ""
        extracted = extractor.extract_all_properties(code)
        if any(value is not None for value in extracted.values()):
            props.append(FoundationalProperties.normalize_properties(extracted))
        else:
            props.append(None)

    certified = [
        certified_flag(record) and props[index] is not None
        for index, record in enumerate(records)
    ]
    certified_indices = [i for i, ok in enumerate(certified) if ok]

    # Nonzero property set per certified pair.
    pair_nonzero: Dict[Tuple[int, int], frozenset] = {}
    for i, j in itertools.combinations(certified_indices, 2):
        nonzero = set()
        for name in properties:
            left = props[i].get(name) if props[i] else None
            right = props[j].get(name) if props[j] else None
            distance = extractor._calculate_property_distance(
                left, right, name, HE_CONTRACT
            )
            if distance > 1e-12:
                nonzero.add(name)
        pair_nonzero[(i, j)] = frozenset(nonzero)

    return {
        **config_identity(path),
        "file": path.name,
        "n": n,
        "n_certified": len(certified_indices),
        "n_pairs_total": n * (n - 1) // 2,
        "n_pairs_certified": len(pair_nonzero),
        "pair_nonzero": pair_nonzero,
    }


def variant_match(nonzero: frozenset, variant: str) -> bool:
    """Does this pair match under the named variant?"""
    if variant == "all14":
        return not nonzero
    if variant == "ast_only":
        return AST_PROP not in nonzero
    if variant.startswith("drop_"):
        dropped = variant[len("drop_") :]
        return nonzero.issubset({dropped})
    raise ValueError(f"Unknown variant: {variant}")


def summarize(configs: Sequence[Dict[str, Any]], properties: Sequence[str]) -> Dict[str, Any]:
    variants = ["all14", "ast_only"] + [f"drop_{name}" for name in properties]

    # Per-config rates, then task-mean, matching the published aggregation.
    per_variant: Dict[str, Dict[str, Any]] = {}
    for variant in variants:
        by_task_e2e: Dict[str, List[float]] = defaultdict(list)
        by_task_cert: Dict[str, List[float]] = defaultdict(list)
        for config in configs:
            pairs = config["pair_nonzero"]
            matched = sum(1 for nonzero in pairs.values() if variant_match(nonzero, variant))
            by_task_e2e[config["task_id"]].append(matched / config["n_pairs_total"])
            if pairs:
                by_task_cert[config["task_id"]].append(matched / len(pairs))

        def task_mean(buckets: Dict[str, List[float]]) -> Optional[float]:
            task_scores = [sum(v) / len(v) for v in buckets.values() if v]
            return sum(task_scores) / len(task_scores) if task_scores else None

        per_variant[variant] = {
            "pairwise_end_to_end": task_mean(by_task_e2e),
            "pairwise_certified": task_mean(by_task_cert),
            "n_tasks_certified_defined": len(by_task_cert),
        }

    # Binding pairs: AST fingerprint agrees, full relation still says different.
    binding_total = 0
    ast_match_total = 0
    binding_attribution: Counter = Counter()
    binding_by_config: List[Dict[str, Any]] = []
    for config in configs:
        binding_here = 0
        for nonzero in config["pair_nonzero"].values():
            if AST_PROP in nonzero:
                continue
            ast_match_total += 1
            if nonzero:
                binding_total += 1
                binding_here += 1
                binding_attribution.update(nonzero)
        if binding_here:
            binding_by_config.append(
                {
                    "file": config["file"],
                    "task_id": config["task_id"],
                    "model": config["model"],
                    "temperature": config["temperature"],
                    "binding_pairs": binding_here,
                }
            )

    return {
        "n_configs": len(configs),
        "n_tasks": len({c["task_id"] for c in configs}),
        "n_certified_pairs": sum(len(c["pair_nonzero"]) for c in configs),
        "variants": per_variant,
        "binding": {
            "n_pairs_ast_fingerprint_agrees": ast_match_total,
            "n_binding_pairs": binding_total,
            "share_of_ast_agreeing_pairs_split_by_others": (
                binding_total / ast_match_total if ast_match_total else None
            ),
            "splitting_properties": dict(binding_attribution.most_common()),
            "configs_with_binding_pairs": binding_by_config,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    extractor = FoundationalProperties(HE_CONTRACT)
    properties = list(extractor.properties)

    files = sorted(p for p in args.source_dir.glob("*.jsonl"))
    if not files:
        raise SystemExit(f"No .jsonl configs under {args.source_dir}")

    configs = []
    for path in files:
        result = analyze_config(path, extractor, properties)
        if result:
            configs.append(result)

    summary = summarize(configs, properties)
    summary["source_dir"] = str(args.source_dir)
    summary["properties"] = properties

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "ablation.json"
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    full = summary["variants"]["all14"]
    ast = summary["variants"]["ast_only"]
    binding = summary["binding"]

    print(f"configs {summary['n_configs']}  tasks {summary['n_tasks']}  "
          f"certified pairs {summary['n_certified_pairs']}")
    print()
    print("variant                              e2e pairwise   certified pairwise")
    for variant, scores in summary["variants"].items():
        e2e = scores["pairwise_end_to_end"]
        cert = scores["pairwise_certified"]
        flag = ""
        if variant.startswith("drop_") and e2e is not None:
            if full["pairwise_end_to_end"] is not None and abs(e2e - full["pairwise_end_to_end"]) < 1e-9:
                flag = "  (no effect)"
        print(f"  {variant:<34} {e2e:>8.4f}       {cert:>8.4f}{flag}")
    print()
    print(f"AST fingerprint agrees on {binding['n_pairs_ast_fingerprint_agrees']} certified pairs")
    print(f"of those, {binding['n_binding_pairs']} are split by other properties")
    if binding["splitting_properties"]:
        print("splitting properties:")
        for name, count in binding["splitting_properties"].items():
            print(f"  {name}: {count}")
    else:
        print("no property other than the AST fingerprint ever binds")
    print()
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
