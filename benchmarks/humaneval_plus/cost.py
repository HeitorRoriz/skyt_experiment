"""Token → USD estimates from billed usage fields.

Rates are list prices pinned 2026-09-01. This is not a provider invoice.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


PRICING_AS_OF = "2026-09-01"
USD_PER_MILLION = {
    "gpt-4o-mini": {
        "input": 0.15,
        "output": 0.60,
        "source": "OpenAI list price (standard, not batch/cache)",
    },
    "claude-sonnet-4-5-20250929": {
        "input": 3.00,
        "output": 15.00,
        "source": "Anthropic list price Sonnet 4.5 ≤200K context",
    },
}

FULL_TASKS = 164
PILOT_TASKS = 30


def input_output_tokens(usage: Optional[Dict[str, Any]]) -> Tuple[int, int]:
    usage = usage or {}
    inp = usage.get("input_tokens")
    if inp is None:
        inp = usage.get("prompt_tokens")
    out = usage.get("output_tokens")
    if out is None:
        out = usage.get("completion_tokens")
    return int(inp or 0), int(out or 0)


def usd_for_usage(model: str, usage: Optional[Dict[str, Any]]) -> Optional[float]:
    rates = USD_PER_MILLION.get(model)
    if not rates:
        return None
    inp, out = input_output_tokens(usage)
    if inp == 0 and out == 0:
        return 0.0
    return (inp * rates["input"] + out * rates["output"]) / 1_000_000.0


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def collect_cost(out_dir: Path) -> Dict[str, Any]:
    by_model: Dict[str, Dict[str, Any]] = {}
    n_records = 0
    n_with_tokens = 0
    n_failed = 0
    usd_total = 0.0

    for jsonl in sorted(out_dir.glob("*.jsonl")):
        for record in _iter_jsonl(jsonl):
            n_records += 1
            model = record.get("model") or "unknown"
            bucket = by_model.setdefault(
                model,
                {
                    "n_records": 0,
                    "n_with_tokens": 0,
                    "n_failed": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "usd_estimate": 0.0,
                },
            )
            bucket["n_records"] += 1
            if record.get("error"):
                n_failed += 1
                bucket["n_failed"] += 1
            inp, out = input_output_tokens(record.get("usage"))
            if inp or out:
                n_with_tokens += 1
                bucket["n_with_tokens"] += 1
                bucket["input_tokens"] += inp
                bucket["output_tokens"] += out
                usd = usd_for_usage(model, record.get("usage")) or 0.0
                bucket["usd_estimate"] += usd
                usd_total += usd

    scale_n10 = FULL_TASKS / float(PILOT_TASKS)
    mean_usd = (usd_total / n_with_tokens) if n_with_tokens else 0.0
    temps = 2
    n_per_config = 10
    models_in_grid = 2
    pilot_calls = PILOT_TASKS * models_in_grid * temps * n_per_config
    full_n10_calls = FULL_TASKS * models_in_grid * temps * n_per_config
    full_n20_calls = FULL_TASKS * models_in_grid * temps * 20

    by_model_out = {}
    projected_pilot = 0.0
    projected_full_n10 = 0.0
    projected_full_n20 = 0.0
    for name, values in by_model.items():
        billed = values["n_with_tokens"]
        mean = (values["usd_estimate"] / billed) if billed else 0.0
        by_model_out[name] = {
            **values,
            "usd_estimate": round(values["usd_estimate"], 6),
            "usd_per_call": round(mean, 8),
            "projected_pilot_usd": round(mean * PILOT_TASKS * temps * n_per_config, 4),
            "projected_full_n10_usd": round(mean * FULL_TASKS * temps * n_per_config, 4),
            "projected_full_n20_usd": round(mean * FULL_TASKS * temps * 20, 4),
        }
        projected_pilot += mean * PILOT_TASKS * temps * n_per_config
        projected_full_n10 += mean * FULL_TASKS * temps * n_per_config
        projected_full_n20 += mean * FULL_TASKS * temps * 20

    models_seen = set(by_model)
    models_pending = [
        name for name in ("claude-sonnet-4-5-20250929", "gpt-4o-mini") if name not in models_seen
    ]

    return {
        "schema": "skyt-humaneval-plus-cost-v1",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pricing_as_of": PRICING_AS_OF,
        "pricing_usd_per_million": USD_PER_MILLION,
        "note": (
            "USD is list-price × billed tokens on stored responses. "
            "Retries that never returned usage are not billed here. "
            "Provider invoices can differ (cache, tax, tier)."
        ),
        "n_records": n_records,
        "n_with_tokens": n_with_tokens,
        "n_failed": n_failed,
        "usd_spent_so_far": round(usd_total, 6),
        "usd_spent_estimate": round(usd_total, 6),
        "usd_per_billed_call": round(mean_usd, 8),
        "by_model": by_model_out,
        "forecast": {
            "pilot_tasks": PILOT_TASKS,
            "full_tasks": FULL_TASKS,
            "pilot_target_calls": pilot_calls,
            "full_n10_target_calls": full_n10_calls,
            "full_n20_target_calls": full_n20_calls,
            "models_pending": models_pending,
            "projected_pilot_from_models_seen_usd": round(projected_pilot, 4),
            "projected_full_n10_from_models_seen_usd": round(projected_full_n10, 4),
            "projected_full_n20_from_models_seen_usd": round(projected_full_n20, 4),
            "same_grid_n10_full_usd": round(projected_full_n10, 4),
            "same_grid_n20_full_usd": round(projected_full_n20, 4),
            "assumption": (
                "Per-model mean USD/call × remaining grid. "
                "Until both models have billed calls, OpenAI is omitted "
                "(it is much cheaper than Claude). N=20 is 2× N=10. "
                "Harder leftover tasks can cost more than the mean so far."
            ),
        },
    }


def write_cost_ledger(out_dir: Path) -> Dict[str, Any]:
    payload = collect_cost(out_dir)
    path = out_dir / "cost_ledger.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["ledger_path"] = str(path)
    return payload
