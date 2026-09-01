"""Replay SKYT repair toward Certified Consensus on stored raw generations.

Does not overwrite historical outputs/*.json. Does not call LLM APIs.
Writes outputs/consensus_repair/<original_filename>.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.abspath(__file__))
if REPO not in sys.path:
    sys.path.insert(0, REPO)

from src.contract import Contract  # noqa: E402
from src.canon_selection import select_certified_consensus_canon  # noqa: E402
from src.canon_system import CanonSystem  # noqa: E402
from src.metrics import ComprehensiveMetrics  # noqa: E402
from src.oracle_system import OracleSystem  # noqa: E402

from gate0_pairwise_analysis import select_configs  # noqa: E402

try:
    from agents.enhanced_transformer import EnhancedCodeTransformer
except ImportError:
    EnhancedCodeTransformer = None

DEFAULT_OUT = os.path.join(REPO, "outputs", "consensus_repair")


def _oracle_results_for_raw(data):
    codes = data.get("raw_outputs") or []
    metrics = data.get("metrics") or {}
    stored = (metrics.get("behavioral_stats") or {}).get("oracle_results") or []
    if len(stored) == len(codes):
        return stored, "stored_raw_oracle"
    oracle = OracleSystem()
    contract = data.get("contract") or {}
    return [oracle.run_oracle_tests(code, contract) for code in codes], "rerun_raw_oracle"


def replay_one(data, source_name, out_dir, *, force=False):
    dest = os.path.join(out_dir, source_name)
    if os.path.exists(dest) and not force:
        return {"status": "skipped_exists", "path": dest}

    codes = list(data.get("raw_outputs") or [])
    contract_dict = data.get("contract") or {}
    contract_id = data.get("contract_id") or contract_dict.get("id")
    if len(codes) < 2 or not contract_id:
        return {"status": "skipped_incomplete"}

    oracle_results, oracle_source = _oracle_results_for_raw(data)
    selected = select_certified_consensus_canon(codes, contract_dict, oracle_results)

    payload = deepcopy(data)
    payload["replay_of"] = source_name
    payload["repair_policy"] = "certified_consensus"
    payload["replayed_at"] = datetime.now(timezone.utc).isoformat()
    payload["raw_oracle_source"] = oracle_source
    payload["agents_enabled"] = False

    contract = Contract(contract_dict)
    canon_system = CanonSystem(os.path.join(out_dir, "canon"))
    oracle_system = OracleSystem()

    if selected is None:
        payload["canon_created"] = False
        payload["canon_data"] = None
        payload["canon_policy"] = None
        payload["repaired_outputs"] = list(codes)
        payload["transformation_results"] = [
            {
                "run_id": i + 1,
                "original_code": code,
                "transformed_code": code,
                "transformation_needed": False,
                "skipped_reason": "no_certified_consensus_canon",
            }
            for i, code in enumerate(codes)
        ]
        metrics = ComprehensiveMetrics(canon_system)
        payload["metrics"] = metrics.calculate_comprehensive_metrics(
            codes, codes, contract_dict, contract_id
        )
        os.makedirs(out_dir, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
        return {"status": "no_canon", "path": dest}

    canon_data = canon_system.create_canon(
        contract,
        selected["code"],
        oracle_result=selected["oracle_result"],
        require_oracle_pass=True,
    )
    canon_data["canon_policy"] = "certified_consensus"
    canon_data["consensus_index"] = selected["index"]
    canon_data["consensus_modal_size"] = selected["selection"]["modal_size"]
    canon_data["n_certified"] = selected["n_certified"]
    payload["canon_data"] = canon_data
    payload["canon_created"] = True
    payload["canon_policy"] = "certified_consensus"

    if EnhancedCodeTransformer is None:
        raise RuntimeError(
            "Enhanced transformer required for rollback during replay "
            "(import failed; repo root and src must be on sys.path)"
        )
    transformer = EnhancedCodeTransformer(canon_system, enable_agents=False)
    if getattr(transformer, "enable_agents", True):
        transformer.enable_agents = False

    repaired = []
    transform_rows = []
    for index, code in enumerate(codes):
        comparison = canon_system.compare_to_canon(contract_id, code)
        if comparison.get("is_identical"):
            repaired.append(code)
            transform_rows.append({
                "run_id": index + 1,
                "original_code": code,
                "transformed_code": code,
                "transformation_needed": False,
                "final_distance": comparison.get("distance"),
            })
            continue
        result = transformer.transform_to_canon(
            code, contract_id, contract=contract_dict, oracle_system=oracle_system
        )
        repaired.append(result.get("transformed_code", code))
        transform_rows.append({
            "run_id": index + 1,
            "original_code": code,
            "transformed_code": result.get("transformed_code", code),
            "transformation_needed": True,
            "transformation_success": result.get("success"),
            "final_distance": result.get("final_distance"),
            "transformations_applied": result.get("transformations_applied"),
            "strategy_used": result.get("strategy_used"),
            "rolled_back": result.get("rolled_back"),
            "oracle_validation_performed": result.get("oracle_validation_performed"),
            "post_oracle_result": result.get("post_oracle_result"),
        })

    payload["repaired_outputs"] = repaired
    payload["transformation_results"] = transform_rows
    metrics = ComprehensiveMetrics(canon_system)
    payload["metrics"] = metrics.calculate_comprehensive_metrics(
        codes, repaired, contract_dict, contract_id
    )
    os.makedirs(out_dir, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)
    return {
        "status": "wrote",
        "path": dest,
        "consensus_index": selected["index"],
        "n_certified": selected["n_certified"],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Replay repair toward Certified Consensus (no LLM calls)"
    )
    parser.add_argument("--out-dir", default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)

    configs, skipped = select_configs()
    print(f"Selected {len(configs)} configs ({len(skipped)} skipped)")
    print("Enhanced transformer: enable_agents=False (no planner)")
    os.makedirs(args.out_dir, exist_ok=True)
    counts = {"wrote": 0, "skipped_exists": 0, "no_canon": 0, "failed": 0, "other": 0}
    done = 0
    failures = []
    for (contract_id, model, temp), (_ts, path, data) in sorted(configs.items()):
        source_name = os.path.basename(path)
        try:
            result = replay_one(data, source_name, args.out_dir, force=args.force)
        except Exception as exc:
            result = {"status": "failed", "error": str(exc)}
            failures.append((source_name, contract_id, model, temp, str(exc)))
        status = result.get("status") or "other"
        if status in counts:
            counts[status] += 1
        else:
            counts["other"] += 1
        extra = f" ({result.get('error')})" if result.get("error") else ""
        print(f"  {status}: {contract_id} / {model} / T={temp}{extra}")
        done += 1
        if args.limit and done >= args.limit:
            break
    print(
        f"Replay complete ({done} configs) -> {args.out_dir} "
        f"wrote={counts['wrote']} skipped={counts['skipped_exists']} "
        f"no_canon={counts['no_canon']} failed={counts['failed']}"
    )
    if failures:
        print("Failures:")
        for row in failures:
            print(f"  {row}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
