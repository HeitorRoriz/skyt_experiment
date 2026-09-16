"""Dataset and sandbox pins. Paid runs refuse on mismatch."""

from __future__ import annotations

import json
import shutil
import subprocess
from typing import Any, Dict, Optional

from benchmarks.humaneval_plus.manifest import MANIFEST
from benchmarks.humaneval_plus.sandbox import docker_available

from .schema import RELATION_VERSION, RELATION_VERSION_NOTE


class PinMismatch(ValueError):
    """Pinned dataset hash or sandbox image digest does not match."""


def _normalize_digest(value: str) -> str:
    text = (value or "").strip()
    if "@" in text:
        text = text.rsplit("@", 1)[-1]
    if text and not text.startswith("sha256:") and len(text) == 64:
        text = f"sha256:{text}"
    return text


def pinned_dataset_md5() -> str:
    digest = (MANIFEST.get("dataset") or {}).get("dataset_md5")
    if not digest:
        raise PinMismatch("dataset_md5 is not pinned in experiment_manifest.json")
    return str(digest)


def pinned_image_digest() -> str:
    digest = (MANIFEST.get("sandbox") or {}).get("image_digest")
    if not digest:
        raise PinMismatch("sandbox.image_digest is not pinned")
    return _normalize_digest(str(digest))


def check_dataset_hash() -> Dict[str, Any]:
    pinned = pinned_dataset_md5()
    payload: Dict[str, Any] = {
        "pinned": pinned,
        "evalplus_version": (MANIFEST.get("dataset") or {}).get("evalplus_version"),
        "humaneval_plus_dataset_version": (MANIFEST.get("dataset") or {}).get(
            "humaneval_plus_dataset_version"
        ),
    }
    try:
        from evalplus.data import get_human_eval_plus_hash
    except ImportError:
        payload["status"] = "unverified"
        payload["reason"] = "evalplus is not installed"
        return payload
    observed = get_human_eval_plus_hash()
    payload["observed"] = observed
    if observed != pinned:
        raise PinMismatch(
            f"HumanEval+ hash {observed} does not match pinned {pinned}"
        )
    payload["status"] = "ok"
    return payload


def inspect_local_image_digest(image: Optional[str] = None) -> Dict[str, Any]:
    image = image or str(MANIFEST["sandbox"]["image"])
    pinned = pinned_image_digest()
    payload: Dict[str, Any] = {
        "image": image,
        "pinned": pinned,
        "network": MANIFEST["sandbox"].get("network"),
    }
    if not docker_available():
        payload["status"] = "unverified"
        payload["reason"] = "Docker is not running"
        return payload
    docker = shutil.which("docker")
    if not docker:
        payload["status"] = "unverified"
        payload["reason"] = "docker executable not found"
        return payload
    try:
        completed = subprocess.run(
            [docker, "image", "inspect", image, "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        payload["status"] = "unverified"
        payload["reason"] = type(exc).__name__
        return payload
    if completed.returncode != 0:
        payload["status"] = "unverified"
        payload["reason"] = (completed.stderr or "image inspect failed").strip()[:300]
        return payload
    try:
        info = json.loads(completed.stdout)
    except json.JSONDecodeError:
        payload["status"] = "unverified"
        payload["reason"] = "docker inspect returned non-JSON"
        return payload
    candidates = []
    for item in info.get("RepoDigests") or []:
        candidates.append(_normalize_digest(str(item)))
    image_id = _normalize_digest(str(info.get("Id") or ""))
    if image_id:
        candidates.append(image_id)
    payload["observed"] = candidates
    if pinned in candidates:
        payload["status"] = "ok"
        return payload
    raise PinMismatch(
        f"Docker image {image} digest {candidates} does not match pinned {pinned}"
    )


def collect_pins() -> Dict[str, Any]:
    dataset = check_dataset_hash()
    sandbox = inspect_local_image_digest()
    return {
        "relation_version": RELATION_VERSION,
        "relation_version_note": RELATION_VERSION_NOTE,
        "dataset": dataset,
        "sandbox": sandbox,
    }


def require_verified_pins() -> Dict[str, Any]:
    pins = collect_pins()
    if pins["dataset"].get("status") != "ok":
        raise PinMismatch(
            "Refusing a paid run until the HumanEval+ dataset hash is verified. "
            f"{pins['dataset']}"
        )
    if pins["sandbox"].get("status") != "ok":
        raise PinMismatch(
            "Refusing a paid run until the pinned sandbox image digest is verified. "
            f"{pins['sandbox']}"
        )
    return pins
