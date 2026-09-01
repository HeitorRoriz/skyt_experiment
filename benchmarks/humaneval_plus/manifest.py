"""Tracked experiment pins for HumanEval+. Do not silently edit after the pilot freeze."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


PACKAGE_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = PACKAGE_DIR / "experiment_manifest.json"
PILOT_TASK_IDS_PATH = PACKAGE_DIR / "pilot_task_ids.json"
PILOT_SEED = 20260826


def load_manifest() -> Dict[str, Any]:
    with MANIFEST_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_pilot_task_ids() -> List[str]:
    with PILOT_TASK_IDS_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    ids = list(payload["task_ids"])
    if len(ids) != 30:
        raise ValueError("Pilot must contain exactly 30 preregistered task ids")
    if ids != sorted(ids):
        raise ValueError("Pilot task ids must be stored in sorted order")
    if payload.get("seed") != PILOT_SEED:
        raise ValueError("Pilot seed does not match the locked seed")
    return ids


MANIFEST = load_manifest()
PILOT_TASK_IDS = load_pilot_task_ids()
