"""Inference lock: task-cluster CIs, never binomial on pairs."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from benchmark.metrics import cluster_bootstrap_mean, cluster_jackknife_mean
from benchmark.report import build_report, is_pilot_grid
from benchmark.schema import (
    FROZEN_PROTOCOL_N,
    INFERENCE_VERSION,
    PILOT_TASK_WARN_BELOW,
    REQUIRED_SLICE_KEYS,
    SCHEMA,
)


def _wilson(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wrong interval, used only to prove we did not adopt it."""
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = (
        z
        * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n)
        / denom
    )
    return center - half, center + half


def test_schema_v2_inference_version():
    assert SCHEMA == "structural-repeatability-benchmark-v2"
    assert INFERENCE_VERSION == 1
    assert FROZEN_PROTOCOL_N == 20
    assert PILOT_TASK_WARN_BELOW == 30


def test_cluster_ci_is_wider_than_wilson_on_pairs():
    values = [0.1, 0.3, 0.5, 0.7, 0.9]
    ids = [f"task-{index}" for index in range(len(values))]
    boot = cluster_bootstrap_mean(
        values, ids, n_bootstrap=3000, seed=20260723
    )
    width_boot = boot["upper"] - boot["lower"]
    p = sum(values) / len(values)
    n_pairs = len(values) * 45  # fake C(10,2) per task
    lo, hi = _wilson(p, n_pairs)
    width_wilson = hi - lo
    assert width_boot > 2.0 * width_wilson
    assert boot["n_clusters"] == 5


def test_equal_task_weight_not_pair_weight():
    result = cluster_bootstrap_mean(
        values=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
        cluster_ids=["busy"] * 9 + ["quiet"],
        n_bootstrap=500,
        seed=7,
    )
    assert result["mean"] == pytest.approx(0.5)
    assert result["n_clusters"] == 2
    jack = cluster_jackknife_mean(
        values=[0.0, 1.0, 0.5],
        cluster_ids=["a", "b", "c"],
    )
    assert jack["skipped"] is None
    assert jack["se"] is not None
    assert jack["lower"] is not None


def test_jackknife_skipped_below_three_tasks():
    jack = cluster_jackknife_mean([0.0, 1.0], ["a", "b"])
    assert jack["skipped"] == "need_at_least_3_tasks"
    assert jack["lower"] is None


def test_mixed_n_refused():
    with pytest.raises(ValueError, match="cannot mix sample sizes"):
        build_report(
            [
                {
                    "task_id": "T1",
                    "model": "m",
                    "temperature": 0.0,
                    "n": 10,
                    "same_at_2": 0.5,
                    "same_at_2_given_cert": 0.5,
                    "plus_pass": 0.8,
                },
                {
                    "task_id": "T2",
                    "model": "m",
                    "temperature": 0.0,
                    "n": 20,
                    "same_at_2": 0.4,
                    "same_at_2_given_cert": 0.4,
                    "plus_pass": 0.7,
                },
            ],
            n_bootstrap=50,
        )


def test_missing_metric_refused():
    with pytest.raises(ValueError, match="missing required metric"):
        build_report(
            [
                {
                    "task_id": "T1",
                    "model": "m",
                    "temperature": 0.0,
                    "n": 10,
                    "same_at_2": 0.5,
                    "same_at_2_given_cert": 0.5,
                }
            ],
            n_bootstrap=20,
        )


def test_slice_has_all_three_metrics_and_drop_count():
    report = build_report(
        [
            {
                "task_id": "T1",
                "model": "m",
                "temperature": 0.0,
                "n": 10,
                "same_at_2": 0.2,
                "same_at_2_given_cert": 1.0,
                "plus_pass": 0.5,
            },
            {
                "task_id": "T2",
                "model": "m",
                "temperature": 0.0,
                "n": 10,
                "same_at_2": 0.0,
                "same_at_2_given_cert": None,
                "plus_pass": 0.1,
            },
            {
                "task_id": "T3",
                "model": "m",
                "temperature": 0.0,
                "n": 10,
                "same_at_2": 0.4,
                "same_at_2_given_cert": 0.8,
                "plus_pass": 0.6,
            },
        ],
        n_bootstrap=200,
    )
    slice_row = report["slices"][0]
    for key in REQUIRED_SLICE_KEYS:
        assert key in slice_row
    assert slice_row["n_dropped_same_at_2_given_cert"] == 1
    assert slice_row["same_at_2"] is not None
    assert slice_row["plus_pass"] is not None
    assert slice_row["same_at_2_given_cert"] is not None
    assert slice_row["same_at_2_given_cert_n_missing"] == 1
    assert slice_row["same_at_2_jackknife_skipped"] is None
    assert report["pilot_grid"] is True
    assert is_pilot_grid(n_tasks=30, n=10) is True
    assert is_pilot_grid(n_tasks=164, n=20) is False


def test_benchmark_package_does_not_call_wilson():
    root = Path(__file__).resolve().parents[1] / "benchmark"
    offenders = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "wilson_confidence_interval" in text or "from src.enhanced_stats" in text:
            offenders.append(str(path.relative_to(root)))
    assert offenders == []
