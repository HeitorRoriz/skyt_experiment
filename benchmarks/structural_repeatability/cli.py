"""Structural repeatability overlay CLI.

Measuring tape only. No canon picker, no SKYT repair, no writes into
``outputs/gate0/`` or ``outputs/humaneval_plus/pilot/``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .estimate import estimate_grid
from .pins import PinMismatch, collect_pins, require_verified_pins
from .protect import ProtectedOutputError, assert_writable
from .report import build_overlay_report, overlay_row_from_analysis
from .schema import RELATION_VERSION, SCHEMA
from .score import score_directory


DEFAULT_OUT = Path("outputs") / "structural_repeatability"


def _print_json(payload: object) -> None:
    json.dump(payload, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Structural repeatability overlay: same@2 / same@2|cert over an "
            "existing task set. Measuring tape only."
        )
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("pins", help="Print dataset/sandbox/relation pins. No API.")

    estimate = sub.add_parser(
        "estimate",
        help="Print a list-price USD sketch. No API.",
    )
    estimate.add_argument("--n-tasks", type=int, required=True)
    estimate.add_argument("--n", type=int, required=True)
    estimate.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Repeatable. Default: both HumanEval+ adapter models.",
    )
    estimate.add_argument(
        "--temperature",
        action="append",
        dest="temperatures",
        type=float,
        help="Repeatable. Default: 0.0 and 0.7.",
    )
    estimate.add_argument(
        "--from-dir",
        help="Optional jsonl directory whose billed usage sets USD/call.",
    )

    score = sub.add_parser(
        "score",
        help="Recompute overlay metrics from stored jsonl. No API.",
    )
    score.add_argument("--source-dir", required=True)
    score.add_argument("--out-dir", required=True)
    score.add_argument("--cv-splits", type=int, default=2000)
    score.add_argument("--n-bootstrap", type=int, default=10000)

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
    run.add_argument(
        "--from-dir",
        help="Optional billed-usage directory for a tighter USD sketch.",
    )

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
        payload = estimate_grid(
            n_tasks=args.n_tasks,
            n=args.n,
            models=args.models,
            temperatures=args.temperatures,
            from_dir=Path(args.from_dir) if args.from_dir else None,
        )
        _print_json(payload)
        return 0

    if args.cmd == "score":
        try:
            report = score_directory(
                Path(args.source_dir),
                Path(args.out_dir),
                cv_splits=args.cv_splits,
                n_bootstrap=args.n_bootstrap,
            )
        except (ProtectedOutputError, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        _print_json(
            {
                "schema": report["schema"],
                "relation_version": report["relation_version"],
                "headline": report["headline"],
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
            summary = run_config(
                task_id=args.task_id,
                model=args.model,
                temperature=args.temperature,
                n=args.n,
                out_dir=out_dir,
                allow_api=True,
                force=bool(args.force),
            )
        except (ApiSpendBlocked, SandboxUnavailable, ValueError) as exc:
            print(exc, file=sys.stderr)
            return 3
        row = overlay_row_from_analysis(
            task_id=summary["task_id"],
            model=summary["model"],
            temperature=float(summary["temperature"]),
            n=int(summary["n"]),
            analysis=summary.get("analysis") or {},
        )
        report = build_overlay_report(
            [row],
            n_bootstrap=200,
            source_dir=str(out_dir.resolve()),
        )
        report["pins"] = pins
        report["cost_sketch"] = sketch
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / "overlay_report.json"
        path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        _print_json(
            {
                "schema": SCHEMA,
                "relation_version": RELATION_VERSION,
                "headline": report["headline"],
                "report_path": str(path),
                "no_skyt_repair": True,
            }
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
