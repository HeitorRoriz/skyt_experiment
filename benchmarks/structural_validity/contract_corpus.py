"""Step 1 validity pass over the MSR/SBES contract corpus.

Read-only. Mirrors ``ablation.py`` and ``audit.py`` but reads the per-config
JSONs in ``outputs/`` and honours **each contract's own naming policy**, which
is the reason this corpus needs a separate pass.

Why the policy matters. ``_should_use_alpha_renaming`` returns ``False`` under a
*strict* policy, so ``normalized_ast_structure`` compares the raw ``ast_hash``.
``data_dependency_graph`` and ``function_contracts`` also key on raw names. Under
strict naming those two are therefore *consistent* with the declared policy, and
the identifier leak that affects the HumanEval+ arm cannot arise. Under flexible
naming it can. This script reports which policy each contract actually declares
rather than assuming.

Certification follows Gate 0: stored raw oracle pass **and** the repository's
static contract-compliance checker. Only the pre-repair pass is scored, since
that is the population measure.

Usage:
    python -m benchmarks.structural_validity.contract_corpus
    python -m benchmarks.structural_validity.contract_corpus --source-dir outputs/consensus_repair
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.foundational_properties import FoundationalProperties

from benchmarks.structural_validity.ablation import AST_PROP, variant_match
from benchmarks.structural_validity.audit import LEAK_PROPS, alpha_reextract, free_name_sequence

import gate0_pairwise_analysis as gate0

DEFAULT_SOURCE = Path("outputs")
DEFAULT_OUT = Path("outputs/validity")


def naming_policy(contract: Dict[str, Any]) -> str:
    constraints = contract.get("constraints") or {}
    var_naming = constraints.get("variable_naming") or {}
    return var_naming.get("naming_policy", "flexible")


def analyze_config(
    contract_id: str,
    model: str,
    temperature: float,
    data: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    contract = data.get("contract") or {}
    outputs = data.get("raw_outputs") or []
    if len(outputs) < 2:
        return None

    extractor = FoundationalProperties(contract)
    properties = list(extractor.properties)

    props: List[Optional[Dict[str, Any]]] = []
    for code in outputs:
        extracted = extractor.extract_all_properties(code or "")
        props.append(
            FoundationalProperties.normalize_properties(extracted)
            if any(value is not None for value in extracted.values())
            else None
        )

    certified_mask, source, _ = gate0.derive_certification_mask(data, outputs, "pre")
    if certified_mask is None:
        return None
    indices = [
        i
        for i, ok in enumerate(certified_mask)
        if ok and props[i] is not None
    ]

    pair_nonzero: Dict[Tuple[int, int], frozenset] = {}
    for i, j in itertools.combinations(indices, 2):
        nonzero = set()
        for name in properties:
            distance = extractor._calculate_property_distance(
                props[i].get(name), props[j].get(name), name, contract
            )
            if distance > 1e-12:
                nonzero.add(name)
        pair_nonzero[(i, j)] = frozenset(nonzero)

    zero_pairs = [pair for pair, nonzero in pair_nonzero.items() if not nonzero]

    # False merges: distance-0 pairs that call different free names.
    free_names = {i: free_name_sequence(outputs[i] or "") for i in indices}
    merges = 0
    for i, j in zero_pairs:
        left, right = free_names[i], free_names[j]
        if left is not None and right is not None and left != right:
            merges += 1

    # Identifier-leak bridge, only meaningful where the policy is flexible.
    policy = naming_policy(contract)
    leak_naming_only = 0
    leak_survives = 0
    if policy != "strict":
        alpha_cache: Dict[int, Optional[Dict[str, Any]]] = {}
        for (i, j), nonzero in pair_nonzero.items():
            if AST_PROP in nonzero or not nonzero:
                continue
            for index in (i, j):
                if index not in alpha_cache:
                    alpha_cache[index] = alpha_reextract(extractor, outputs[index] or "")
            left, right = alpha_cache[i], alpha_cache[j]
            if left is None or right is None:
                continue
            still = {name for name in nonzero if name not in LEAK_PROPS}
            for name in nonzero & set(LEAK_PROPS):
                if (
                    extractor._calculate_property_distance(
                        left[name], right[name], name, contract
                    )
                    > 1e-12
                ):
                    still.add(name)
            if still:
                leak_survives += 1
            else:
                leak_naming_only += 1

    # Transitivity of distance-0 among certified generations.
    zero_set = {frozenset(pair) for pair in zero_pairs}

    def is_zero(a: int, b: int) -> bool:
        return a == b or frozenset((a, b)) in zero_set

    violations = 0
    for a, b, c in itertools.combinations(indices, 3):
        for x, y, z in ((a, b, c), (b, a, c), (a, c, b)):
            if is_zero(x, y) and is_zero(y, z) and not is_zero(x, z):
                violations += 1
                break

    return {
        "contract_id": contract_id,
        "model": model,
        "temperature": temperature,
        "is_strict_task": contract_id.endswith("_strict"),
        "naming_policy": policy,
        "certification_source": source,
        "n": len(outputs),
        "n_certified": len(indices),
        "n_pairs_total": len(outputs) * (len(outputs) - 1) // 2,
        "n_pairs_certified": len(pair_nonzero),
        "n_zero_pairs": len(zero_pairs),
        "false_merge_pairs": merges,
        "leak_naming_only": leak_naming_only,
        "leak_survives": leak_survives,
        "transitivity_violations": violations,
        "pair_nonzero": pair_nonzero,
        "properties": properties,
    }


def summarize(configs: List[Dict[str, Any]], scope: str) -> Dict[str, Any]:
    """Contract-mean rates for one scope. SBES excludes the strict tasks."""
    selected = (
        configs if scope == "msr" else [c for c in configs if not c["is_strict_task"]]
    )
    if not selected:
        return {}

    properties = selected[0]["properties"]
    variants = ["all14", "ast_only"] + [f"drop_{name}" for name in properties]

    out: Dict[str, Any] = {}
    for variant in variants:
        by_contract_e2e: Dict[str, List[float]] = defaultdict(list)
        by_contract_cert: Dict[str, List[float]] = defaultdict(list)
        for config in selected:
            pairs = config["pair_nonzero"]
            matched = sum(1 for nz in pairs.values() if variant_match(nz, variant))
            by_contract_e2e[config["contract_id"]].append(matched / config["n_pairs_total"])
            if pairs:
                by_contract_cert[config["contract_id"]].append(matched / len(pairs))

        def contract_mean(buckets: Dict[str, List[float]]) -> Optional[float]:
            scores = [sum(v) / len(v) for v in buckets.values() if v]
            return sum(scores) / len(scores) if scores else None

        out[variant] = {
            "pairwise_end_to_end": contract_mean(by_contract_e2e),
            "pairwise_certified": contract_mean(by_contract_cert),
        }

    binding = Counter()
    ast_agree = 0
    binding_pairs = 0
    for config in selected:
        for nonzero in config["pair_nonzero"].values():
            if AST_PROP in nonzero:
                continue
            ast_agree += 1
            if nonzero:
                binding_pairs += 1
                binding.update(nonzero)

    return {
        "scope": scope.upper(),
        "n_configs": len(selected),
        "n_contracts": len({c["contract_id"] for c in selected}),
        "n_certified_pairs": sum(len(c["pair_nonzero"]) for c in selected),
        "variants": out,
        "binding": {
            "n_pairs_ast_agrees": ast_agree,
            "n_binding_pairs": binding_pairs,
            "splitting_properties": dict(binding.most_common()),
        },
        "false_merge_pairs": sum(c["false_merge_pairs"] for c in selected),
        "n_zero_pairs": sum(c["n_zero_pairs"] for c in selected),
        "transitivity_violations": sum(c["transitivity_violations"] for c in selected),
        "leak_naming_only": sum(c["leak_naming_only"] for c in selected),
        "leak_survives": sum(c["leak_survives"] for c in selected),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    selected, skipped = gate0.select_configs(str(args.source_dir))
    print(f"selected {len(selected)} configs ({len(skipped)} skipped)")

    configs = []
    for (contract_id, model, temperature), (_ts, _path, data) in sorted(selected.items()):
        result = analyze_config(contract_id, model, temperature, data)
        if result:
            configs.append(result)

    policies = Counter(c["naming_policy"] for c in configs)
    print(f"declared naming policies: {dict(policies)}")
    print()

    summaries = {scope: summarize(configs, scope) for scope in ("sbes", "msr")}

    for scope, summary in summaries.items():
        if not summary:
            continue
        base = summary["variants"]["all14"]
        print(f"=== {summary['scope']}  "
              f"{summary['n_contracts']} contracts, {summary['n_configs']} configs, "
              f"{summary['n_certified_pairs']} certified pairs ===")
        inert = []
        for variant, scores in summary["variants"].items():
            if variant.startswith("drop_") and scores["pairwise_end_to_end"] is not None:
                if abs(scores["pairwise_end_to_end"] - base["pairwise_end_to_end"]) < 1e-9:
                    inert.append(variant[len("drop_"):])
                    continue
            e2e = scores["pairwise_end_to_end"]
            cert = scores["pairwise_certified"]
            e2e_text = f"{e2e * 100:6.2f}" if e2e is not None else "    na"
            cert_text = f"{cert * 100:6.2f}" if cert is not None else "    na"
            print(f"   {variant:<34} e2e={e2e_text}  cert={cert_text}")
        print(f"   inert properties ({len(inert)}): {', '.join(inert) or 'none'}")
        b = summary["binding"]
        print(f"   binding pairs {b['n_binding_pairs']} of {b['n_pairs_ast_agrees']} "
              f"ast-agreeing; splitters {b['splitting_properties'] or 'none'}")
        print(f"   false merges {summary['false_merge_pairs']} of "
              f"{summary['n_zero_pairs']} distance-0 pairs")
        print(f"   transitivity violations {summary['transitivity_violations']}")
        print(f"   identifier leak: naming-only {summary['leak_naming_only']}, "
              f"survives {summary['leak_survives']} "
              f"(not applicable where policy is strict)")
        print()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "contract_corpus.json"
    payload = {
        "source_dir": str(args.source_dir),
        "declared_naming_policies": dict(policies),
        "scopes": summaries,
        "configs": [
            {k: v for k, v in c.items() if k != "pair_nonzero"} for c in configs
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
