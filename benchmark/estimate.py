"""List-price USD sketch. Not an invoice."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from benchmarks.humaneval_plus.cost import (
    PRICING_AS_OF,
    USD_PER_MILLION,
    collect_cost,
    usd_for_usage,
)
from benchmarks.humaneval_plus.manifest import MANIFEST


SKETCH_USAGE = {"input_tokens": 600, "output_tokens": 250}


def _models(models: Optional[Sequence[str]]) -> List[str]:
    return list(models) if models else list(MANIFEST["models"])


def _temperatures(temperatures: Optional[Sequence[float]]) -> List[float]:
    if temperatures is not None:
        return [float(item) for item in temperatures]
    return [float(item) for item in MANIFEST["temperatures"]]


def estimate_grid(
    *,
    n_tasks: int,
    n: int,
    models: Optional[Sequence[str]] = None,
    temperatures: Optional[Sequence[float]] = None,
    from_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    if n_tasks < 1 or n < 2:
        raise ValueError("n_tasks must be >= 1 and n must be >= 2")
    model_ids = _models(models)
    temps = _temperatures(temperatures)
    n_calls_per_model = n_tasks * len(temps) * n
    n_calls = n_calls_per_model * len(model_ids)

    observed: Dict[str, float] = {}
    if from_dir is not None and Path(from_dir).exists():
        ledger = collect_cost(Path(from_dir))
        for name, bucket in (ledger.get("by_model") or {}).items():
            usd_per = bucket.get("usd_per_call")
            if usd_per:
                observed[name] = float(usd_per)

    by_model = []
    usd_total = 0.0
    for model in model_ids:
        if model in observed:
            usd_per_call = observed[model]
            source = "mean billed USD/call from --from-dir"
        else:
            usd_per_call = usd_for_usage(model, SKETCH_USAGE)
            source = (
                f"sketch {SKETCH_USAGE['input_tokens']} in / "
                f"{SKETCH_USAGE['output_tokens']} out tokens × list price"
            )
        if usd_per_call is None:
            by_model.append(
                {
                    "model": model,
                    "n_calls": n_calls_per_model,
                    "usd_per_call": None,
                    "usd": None,
                    "source": "no list price pinned for this model",
                }
            )
            continue
        usd = round(usd_per_call * n_calls_per_model, 4)
        usd_total += usd
        by_model.append(
            {
                "model": model,
                "n_calls": n_calls_per_model,
                "usd_per_call": round(usd_per_call, 8),
                "usd": usd,
                "source": source,
            }
        )

    return {
        "pricing_as_of": PRICING_AS_OF,
        "pricing_usd_per_million": USD_PER_MILLION,
        "n_tasks": n_tasks,
        "n": n,
        "models": model_ids,
        "temperatures": temps,
        "n_calls": n_calls,
        "usd_estimate": round(usd_total, 4),
        "by_model": by_model,
        "note": (
            "List-price sketch, not an invoice. SPEC OPEN 3 is still open: "
            "this command does not silently switch N from 10 to 20."
        ),
    }
