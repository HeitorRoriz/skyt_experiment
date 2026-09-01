"""Load HumanEval+ problems, or the vendored smoke fixtures."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from .manifest import MANIFEST, PACKAGE_DIR, PILOT_TASK_IDS


FIXTURE_PATH = PACKAGE_DIR / "fixtures" / "smoke_problems.json"


def load_smoke_problems() -> List[Dict[str, Any]]:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        problems = json.load(handle)
    if not isinstance(problems, list) or not problems:
        raise ValueError("Smoke fixtures are missing")
    return problems


def load_evalplus_problems() -> Tuple[Dict[str, Dict[str, Any]], str]:
    """Return EvalPlus problems and the dataset MD5.

    Requires the optional ``evalplus`` package. Not used by unit tests.
    """
    try:
        from evalplus.data import get_human_eval_plus, get_human_eval_plus_hash
    except ImportError as exc:
        raise ImportError(
            "evalplus is required to load the official HumanEval+ dataset. "
            "Install the pin in experiment_manifest.json."
        ) from exc
    problems = get_human_eval_plus()
    digest = get_human_eval_plus_hash()
    pinned = (MANIFEST.get("dataset") or {}).get("dataset_md5")
    if not pinned:
        raise ValueError(
            "dataset_md5 is not pinned in experiment_manifest.json"
        )
    if digest != pinned:
        raise ValueError(
            f"HumanEval+ hash {digest} does not match pinned {pinned}"
        )
    if len(problems) != 164:
        raise ValueError(f"Expected 164 HumanEval+ tasks, got {len(problems)}")
    missing = [task_id for task_id in PILOT_TASK_IDS if task_id not in problems]
    if missing:
        raise ValueError(f"Pilot ids missing from dataset: {missing}")
    return problems, digest
