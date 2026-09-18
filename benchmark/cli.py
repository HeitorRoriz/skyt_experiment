"""Structural repeatability benchmark CLI. Measuring tape only."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .estimate import estimate_grid
from .pins import PinMismatch, collect_pins, require_verified_pins
from .protect import ProtectedOutputError, assert_writable
from .relation import RELATION_VERSION
from .schema import FROZEN_PROTOCOL_N, PILOT_TASK_WARN_BELOW, SCHEMA
from .score import score_directory


def _print_json(payload: object) -> None:
    json.dump(payload, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def _warn_pilot_grid(report: dict) -> None:
    if not report.get("pilot_grid"):
        return
    print(
        "WARNING: pilot_grid=true. At least one slice has n_tasks < "
        f"{PILOT_TASK_WARN_BELOW} or N < {FROZEN_PROTOCOL_N}. "
        "Do not paste this as the frozen N=20 / full-task protocol.",
        file=sys.stderr,
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Structural repeatability benchmark: same@2 / same@2|cert. "
            "Canonical-form fingerprint only. No SKYT canon or repair."
        )
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pins", help="Print dataset/sandbox/relation pins. No API.")

    estimate = sub.add_parser("estimate", help="List-price USD sketch. No API.")
    estimate.add_argument("--n-tasks", type=int, required=True)
    estimate.add_argument("--n", type=int, required=True)
    estimate.add_argument("--model", action="append", dest="models")
    estimate.add_argument(
        "--temperature", action="append", dest="temperatures", type=float
    )
    estimate.add_argument("--from-dir")

    score = sub.add_parser("score", help="Score stored jsonl. No API.")
    score.add_argument("--source-dir", required=True)
    score.add_argument("--out-dir", required=True)
    score.add_argument("--n-bootstrap", type=int, default=10000)

    disc = sub.add_parser(
        "discriminant",
        help="Disagreement census vs string/AST/TED/clone-like judges. No API.",
    )
    disc.add_argument("--source-dir", required=True)
    disc.add_argument("--out-dir", required=True)
    disc.add_argument("--sample-per-cell", type=int, default=20)
    disc.add_argument("--limit-pairs", type=int, default=0)

    run = sub.add_parser(
        "run",
        help="Generate + score one config (blocked unless --allow-api).",
    )
    run.add_argument("--allow-api", action="store_true")
    run.add_argument("--task-id", required=True)
    run.add_argument("--model", required=True)
    run.add_argument("--temperature", type=float, required=True)
    run.add_argument("--n", type=int, required=True)
    run.add_argument("--out-dir", required=True)
    run.add_argument("--force", action="store_true")
    run.add_argument("--from-dir")

    full = sub.add_parser(
        "full",
        help="164 HumanEval+ tasks at protocol N=20 (blocked unless --allow-api).",
    )
    full.add_argument("--allow-api", action="store_true")
    full.add_argument(
        "--out-dir",
        default=str(Path("outputs") / "benchmark" / "humaneval_plus_164_n20"),
    )
    full.add_argument("--from-dir")
    full.add_argument("--force", action="store_true")
    full.add_argument(
        "--only-incomplete",
        action="store_true",
        help="Retry configs that lack a complete jsonl+summary. Do not regenerate finished ones.",
    )
    full.add_argument("--n-bootstrap", type=int, default=10000)

    args = parser.parse_args(argv)

    if args.cmd == "pins":
        try:
            payload = collect_pins()
        except PinMismatch as exc:
            print(exc, file=sys.stderr)
            return 2
        _print_json(payload)
        return 0

    if args.cmd == "estimate":
        _print_json(
            estimate_grid(
                n_tasks=args.n_tasks,
                n=args.n,
                models=args.models,
                temperatures=args.temperatures,
                from_dir=Path(args.from_dir) if args.from_dir else None,
            )
        )
        return 0

    if args.cmd == "score":
        try:
            report = score_directory(
                Path(args.source_dir),
                Path(args.out_dir),
                n_bootstrap=args.n_bootstrap,
            )
        except (ProtectedOutputError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        _warn_pilot_grid(report)
        _print_json(
            {
                "schema": report["schema"],
                "relation_version": report["relation_version"],
                "inference_version": report.get("inference_version"),
                "inference": report.get("inference"),
                "pilot_grid": report.get("pilot_grid"),
                "slices": report["slices"],
                "report_path": report.get("report_path"),
            }
        )
        return 0

    if args.cmd == "discriminant":
        from .discriminant.census import run_census

        try:
            report = run_census(
                Path(args.source_dir),
                Path(args.out_dir),
                sample_per_cell=args.sample_per_cell,
                limit_pairs=args.limit_pairs,
            )
        except (ProtectedOutputError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        _print_json(
            {
                "schema": report["schema"],
                "n_pairs": report["n_pairs"],
                "vs_fingerprint": report["vs_fingerprint"],
                "report_path": report.get("report_path"),
            }
        )
        return 0

    if args.cmd == "run":
        out_dir = Path(args.out_dir)
        try:
            assert_writable(out_dir)
        except ProtectedOutputError as exc:
            print(exc, file=sys.stderr)
            return 3
        sketch = estimate_grid(
            n_tasks=1,
            n=args.n,
            models=[args.model],
            temperatures=[args.temperature],
            from_dir=Path(args.from_dir) if args.from_dir else None,
        )
        print(
            "Cost sketch (list price, not an invoice): "
            f"USD {sketch['usd_estimate']} for {sketch['n_calls']} calls "
            f"(N={args.n}, relation_version={RELATION_VERSION}).",
            file=sys.stderr,
        )
        json.dump(sketch, sys.stderr, indent=2, default=str)
        sys.stderr.write("\n")
        if not args.allow_api:
            print(
                "Refusing to call an LLM. Re-run with --allow-api after pins pass.",
                file=sys.stderr,
            )
            return 3
        try:
            pins = require_verified_pins()
        except PinMismatch as exc:
            print(exc, file=sys.stderr)
            return 2
        from benchmarks.humaneval_plus.generate import ApiSpendBlocked
        from benchmarks.humaneval_plus.run import run_config
        from benchmarks.humaneval_plus.sandbox import SandboxUnavailable

        try:
            run_config(
                task_id=args.task_id,
                model=args.model,
                temperature=args.temperature,
                n=args.n,
                out_dir=out_dir,
                allow_api=True,
                force=bool(args.force),
                restrict_to_pilot=False,
                analyze=False,
            )
        except (ApiSpendBlocked, SandboxUnavailable, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        try:
            report = score_directory(out_dir, out_dir, n_bootstrap=200)
        except (ProtectedOutputError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        report["pins"] = pins
        report["cost_sketch"] = sketch
        path = out_dir / "benchmark_report.json"
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        _warn_pilot_grid(report)
        _print_json(
            {
                "schema": SCHEMA,
                "relation_version": RELATION_VERSION,
                "inference_version": report.get("inference_version"),
                "pilot_grid": report.get("pilot_grid"),
                "slices": report["slices"],
                "report_path": str(path),
            }
        )
        return 0

    if args.cmd == "full":
        out_dir = Path(args.out_dir)
        try:
            assert_writable(out_dir)
        except ProtectedOutputError as exc:
            print(exc, file=sys.stderr)
            return 3
        sketch = estimate_grid(
            n_tasks=164,
            n=FROZEN_PROTOCOL_N,
            from_dir=Path(args.from_dir) if args.from_dir else None,
        )
        print(
            "Cost sketch (list price, not an invoice): "
            f"USD {sketch['usd_estimate']} for {sketch['n_calls']} calls "
            f"(164 tasks, N={FROZEN_PROTOCOL_N}, relation_version={RELATION_VERSION}).",
            file=sys.stderr,
        )
        json.dump(sketch, sys.stderr, indent=2, default=str)
        sys.stderr.write("\n")
        if not args.allow_api:
            print(
                "Refusing to call an LLM. Re-run with --allow-api after pins pass.",
                file=sys.stderr,
            )
            return 3
        try:
            pins = require_verified_pins()
        except PinMismatch as exc:
            print(exc, file=sys.stderr)
            return 2
        from benchmarks.humaneval_plus.generate import ApiSpendBlocked
        from benchmarks.humaneval_plus.run import run_full
        from benchmarks.humaneval_plus.sandbox import SandboxUnavailable

        try:
            grid = run_full(
                out_dir=out_dir,
                n=FROZEN_PROTOCOL_N,
                allow_api=True,
                force=bool(args.force),
                only_incomplete=bool(args.only_incomplete),
            )
        except (ApiSpendBlocked, SandboxUnavailable, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        try:
            report = score_directory(
                out_dir, out_dir, n_bootstrap=args.n_bootstrap
            )
        except (ProtectedOutputError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        report["pins"] = pins
        report["cost_sketch"] = sketch
        report["grid"] = {
            "n_configs": grid["n_configs"],
            "n_tasks": grid["n_tasks"],
            "n": grid["n"],
        }
        path = out_dir / "benchmark_report.json"
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        _warn_pilot_grid(report)
        _print_json(
            {
                "schema": SCHEMA,
                "relation_version": RELATION_VERSION,
                "inference_version": report.get("inference_version"),
                "pilot_grid": report.get("pilot_grid"),
                "n_tasks": grid["n_tasks"],
                "n": grid["n"],
                "slices": report["slices"],
                "report_path": str(path),
            }
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
