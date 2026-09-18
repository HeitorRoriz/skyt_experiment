"""HumanEval+ adapter CLI. Default: smoke only, no API calls."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from .analyze import analyze_records
from skyt.humaneval_heldout import HELDOUT_OUT, OVERLAY_SOURCE, heldout_grid
from skyt.humaneval_repair import repair_pilot
from .run import run_config, run_full, run_pilot
from .dataset import load_smoke_problems
from .generate import ApiSpendBlocked, generate_completion
from .manifest import MANIFEST, PILOT_TASK_IDS
from .provenance import attach_oracle, new_generation_record
from .sandbox import SandboxUnavailable, docker_available, evaluate_stitched
from .stitch import stitch_solution


def _canonical_code(problem: Dict[str, Any]) -> str:
    prompt = problem["prompt"]
    if not prompt.endswith("\n"):
        prompt += "\n"
    return prompt + problem["canonical_solution"]


def run_smoke() -> Dict[str, Any]:
    problems = load_smoke_problems()
    add = next(item for item in problems if item["task_id"] == "Smoke/add")
    identity = next(item for item in problems if item["task_id"] == "Smoke/identity")

    good = stitch_solution(add["prompt"], add["canonical_solution"], add["entry_point"])
    body_only = stitch_solution(add["prompt"], "    return a + b\n", add["entry_point"])
    fenced = stitch_solution(
        add["prompt"],
        "```python\ndef add(a: int, b: int) -> int:\n    return a + b\n```",
        add["entry_point"],
    )
    base_only = stitch_solution(
        add["prompt"],
        "    return a + b if a >= 0 else 0\n",
        add["entry_point"],
    )
    bad = stitch_solution(add["prompt"], "    return a - b\n", add["entry_point"])
    boom = stitch_solution(
        identity["prompt"],
        "    while True:\n        pass\n",
        identity["entry_point"],
    )
    garbage = stitch_solution(add["prompt"], "not python (", add["entry_point"])

    stitch_ok = (
        good["parse_ok"]
        and good["has_entry_point"]
        and body_only["parse_ok"]
        and body_only["has_entry_point"]
        and fenced["parse_ok"]
        and fenced["has_entry_point"]
        and not garbage["parse_ok"]
    )

    sandbox: Dict[str, Any] = {"docker": docker_available()}
    if sandbox["docker"]:
        sandbox["canonical"] = evaluate_stitched(good["stitched_code"], add)
        sandbox["base_only"] = evaluate_stitched(base_only["stitched_code"], add)
        sandbox["incorrect"] = evaluate_stitched(bad["stitched_code"], add)
        sandbox["timeout"] = evaluate_stitched(
            boom["stitched_code"], identity, timeout_seconds=3
        )
        sandbox["score_recovery"] = {
            "canonical_certified": sandbox["canonical"]["certified"] is True,
            "base_only_passes_base_fails_plus": (
                sandbox["base_only"]["base_passed"] is True
                and sandbox["base_only"]["plus_passed"] is False
            ),
            "incorrect_fails_base": sandbox["incorrect"]["base_passed"] is False,
            "timeout_status": sandbox["timeout"]["base_status"] == "timeout",
        }
    else:
        sandbox["error"] = "Docker is not running; sandbox half of smoke was skipped"

    records = []
    for index, stitch in enumerate((good, good, base_only, bad)):
        record = new_generation_record(
            task_id=add["task_id"],
            model="smoke-local",
            temperature=0.0,
            run_index=index,
            problem_prompt=add["prompt"],
            raw_response=stitch["extracted_completion"],
            stitch=stitch,
        )
        if sandbox.get("docker"):
            oracle = evaluate_stitched(stitch["stitched_code"], add)
            record = attach_oracle(record, oracle)
        records.append(record)

    analysis = None
    if sandbox.get("docker"):
        analysis = analyze_records(records, cv_splits=6)

    report = {
        "stitch_ok": stitch_ok,
        "pilot_n": len(PILOT_TASK_IDS),
        "manifest_models": MANIFEST["models"],
        "sandbox": sandbox,
        "analysis_keys": sorted(analysis.keys()) if analysis else None,
        "ok": bool(
            stitch_ok
            and sandbox.get("docker")
            and sandbox.get("score_recovery", {}).get("canonical_certified")
            and sandbox.get("score_recovery", {}).get("base_only_passes_base_fails_plus")
            and sandbox.get("score_recovery", {}).get("incorrect_fails_base")
            and sandbox.get("score_recovery", {}).get("timeout_status")
        ),
    }
    return report


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HumanEval+ adapter")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("smoke", help="Stitch + Docker checks. No API calls.")
    gen = sub.add_parser("generate", help="Paid generation (blocked unless --allow-api)")
    gen.add_argument("--allow-api", action="store_true")
    gen.add_argument("--model", default=MANIFEST["models"][0])
    gen.add_argument("--temperature", type=float, default=0.0)
    run = sub.add_parser(
        "run",
        help="Generate + score one config (blocked unless --allow-api)",
    )
    run.add_argument("--allow-api", action="store_true")
    run.add_argument("--task-id", required=True)
    run.add_argument("--model", default=MANIFEST["models"][0])
    run.add_argument("--temperature", type=float, default=0.0)
    run.add_argument("--n", type=int, required=True)
    run.add_argument("--out-dir", required=True)
    run.add_argument("--force", action="store_true")
    pilot = sub.add_parser(
        "pilot",
        help="30-task HumanEval+ grid (blocked unless --allow-api)",
    )
    pilot.add_argument("--allow-api", action="store_true")
    pilot.add_argument("--n", type=int, default=int(MANIFEST["n_pilot"]))
    pilot.add_argument(
        "--out-dir",
        default=str(Path("outputs") / "humaneval_plus" / "pilot"),
    )
    repair = sub.add_parser(
        "repair",
        help="SKYT Certified Consensus replay on stored gens (no API)",
    )
    repair.add_argument(
        "--source-dir",
        default=str(Path("outputs") / "humaneval_plus" / "pilot"),
    )
    repair.add_argument(
        "--out-dir",
        default=str(Path("outputs") / "humaneval_plus" / "pilot_skyt"),
    )
    repair.add_argument("--n", type=int, default=int(MANIFEST["n_pilot"]))
    repair.add_argument("--limit", type=int, default=0)
    repair.add_argument("--force", action="store_true")
    heldout = sub.add_parser(
        "heldout",
        help=(
            "Held-out SKYT rewrite on stored N=20 overlay gens (no API). "
            "Train 10 pick Certified Consensus, repair the other 10, "
            "fingerprint same@2 on the test slice."
        ),
    )
    heldout.add_argument("--source-dir", default=str(OVERLAY_SOURCE))
    heldout.add_argument("--out-dir", default=str(HELDOUT_OUT))
    heldout.add_argument("--n", type=int, default=int(MANIFEST["n_full"]))
    heldout.add_argument("--train-size", type=int, default=10)
    heldout.add_argument("--n-splits", type=int, default=20)
    heldout.add_argument("--seed", type=int, default=20260723)
    heldout.add_argument("--limit", type=int, default=0)
    heldout.add_argument("--force", action="store_true")
    heldout.add_argument("--task-id")
    heldout.add_argument("--model")
    heldout.add_argument("--temperature", type=float)
    full = sub.add_parser(
        "full",
        help="164-task overlay at protocol N=20 (blocked unless --allow-api).",
    )
    full.add_argument("--allow-api", action="store_true")
    full.add_argument(
        "--out-dir",
        default=str(Path("outputs") / "benchmark" / "humaneval_plus_164_n20"),
    )
    full.add_argument("--force", action="store_true")
    full.add_argument(
        "--only-incomplete",
        action="store_true",
        help="Retry configs that lack a complete jsonl+summary. Do not regenerate finished ones.",
    )
    args = parser.parse_args(argv)

    if args.cmd == "smoke":
        report = run_smoke()
        json.dump(report, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0 if report["ok"] else 2

    if args.cmd == "generate":
        try:
            generate_completion(
                model=args.model,
                problem_prompt="def add(a, b):\n",
                temperature=args.temperature,
                max_tokens=int(MANIFEST["generation"]["max_tokens"]),
                allow_api=bool(args.allow_api),
            )
        except ApiSpendBlocked as exc:
            print(exc, file=sys.stderr)
            return 3
        print("Generation entrypoint is wired; use `run` for a scored config.")
        return 0

    if args.cmd == "run":
        if not args.allow_api:
            print(
                "Refusing to call an LLM. Re-run with --allow-api after smoke tests pass.",
                file=sys.stderr,
            )
            return 3
        try:
            summary = run_config(
                task_id=args.task_id,
                model=args.model,
                temperature=args.temperature,
                n=args.n,
                out_dir=Path(args.out_dir),
                allow_api=True,
                force=bool(args.force),
            )
        except ApiSpendBlocked as exc:
            print(exc, file=sys.stderr)
            return 3
        json.dump(summary, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
        return 0

    if args.cmd == "pilot":
        if not args.allow_api:
            print(
                "Refusing to call an LLM. Re-run with --allow-api after smoke tests pass.",
                file=sys.stderr,
            )
            return 3
        try:
            report = run_pilot(
                out_dir=Path(args.out_dir),
                n=args.n,
                allow_api=True,
            )
        except (ApiSpendBlocked, SandboxUnavailable) as exc:
            print(exc, file=sys.stderr)
            return 3
        json.dump(
            {
                "n_configs": report["n_configs"],
                "cost": report["cost"],
            },
            sys.stdout,
            indent=2,
            default=str,
        )
        sys.stdout.write("\n")
        return 0

    if args.cmd == "full":
        if not args.allow_api:
            print(
                "Refusing to call an LLM. Re-run with --allow-api after smoke tests pass.",
                file=sys.stderr,
            )
            return 3
        try:
            report = run_full(
                out_dir=Path(args.out_dir),
                n=int(MANIFEST["n_full"]),
                allow_api=True,
                force=bool(args.force),
                only_incomplete=bool(args.only_incomplete),
            )
        except (ApiSpendBlocked, SandboxUnavailable, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        json.dump(
            {
                "n_configs": report["n_configs"],
                "n_tasks": report["n_tasks"],
                "n": report["n"],
                "cost": report["cost"],
            },
            sys.stdout,
            indent=2,
            default=str,
        )
        sys.stdout.write("\n")
        return 0

    if args.cmd == "repair":
        try:
            report = repair_pilot(
                source_dir=Path(args.source_dir),
                out_dir=Path(args.out_dir),
                n=args.n,
                force=bool(args.force),
                limit=int(args.limit),
            )
        except (SandboxUnavailable, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        json.dump(
            {
                "n_configs": report["n_configs"],
                "n_regressions": report["n_regressions"],
                "n_rescues": report["n_rescues"],
                "n_failed_configs": report["n_failed_configs"],
            },
            sys.stdout,
            indent=2,
            default=str,
        )
        sys.stdout.write("\n")
        return 0 if report["n_failed_configs"] == 0 else 2

    if args.cmd == "heldout":
        try:
            report = heldout_grid(
                source_dir=Path(args.source_dir),
                out_dir=Path(args.out_dir),
                n=int(args.n),
                train_size=int(args.train_size),
                n_splits=int(args.n_splits),
                seed=int(args.seed),
                force=bool(args.force),
                limit=int(args.limit),
                task_id=args.task_id,
                model=args.model,
                temperature=args.temperature,
            )
        except (SandboxUnavailable, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        post = (report.get("post") or {}).get("all") or {}
        json.dump(
            {
                "n_configs": report["n_configs"],
                "n_scored": report["n_scored"],
                "n_failed_configs": report["n_failed_configs"],
                "n_splits": report["n_splits"],
                "post_same_at_2": post.get("same_at_2"),
                "post_same_at_2_given_cert": post.get("same_at_2_given_cert"),
                "post_plus_pass": post.get("plus_pass"),
                "out_dir": report["out_dir"],
            },
            sys.stdout,
            indent=2,
            default=str,
        )
        sys.stdout.write("\n")
        return 0 if report["n_failed_configs"] == 0 else 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
