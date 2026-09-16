"""Benchmark output schema. Measuring tape only."""

from __future__ import annotations

from .relation import RELATION_VERSION, RELATION_VERSION_NOTE

SCHEMA = "structural-repeatability-benchmark-v2"
INFERENCE_VERSION = 1
BOOTSTRAP_SEED = 20260723
DEFAULT_N_BOOTSTRAP = 10000
FROZEN_PROTOCOL_N = 20
PILOT_TASK_WARN_BELOW = 30

INFERENCE = {
    "version": INFERENCE_VERSION,
    "unit": "task",
    "estimator": "U-statistic order 2, then equal-cluster mean",
    "interval": "percentile cluster bootstrap over task_id",
    "n_bootstrap": DEFAULT_N_BOOTSTRAP,
    "seed": BOOTSTRAP_SEED,
    "not": "binomial or Wilson on C(N,2) pairs",
    "secondary": "leave-one-task-out jackknife (skipped if n_tasks < 3)",
}

METRIC_HELP = {
    "same_at_2": (
        "Pr[both draws certify and are the same program]. "
        "All C(N,2) pairs; non-certifying draws stay in the denominator. "
        "Published CI is a task-cluster bootstrap, not a binomial on those pairs."
    ),
    "same_at_2_given_cert": (
        "Pr[same program | both draws certify]. Undefined when a config "
        "has fewer than two certified draws; those configs are dropped."
    ),
    "plus_pass": "Share of the N draws that certify (task-set oracle).",
}

REQUIRED_SLICE_KEYS = (
    "model",
    "temperature",
    "n",
    "n_tasks",
    "n_configs",
    "n_dropped_same_at_2_given_cert",
    "same_at_2",
    "same_at_2_given_cert",
    "plus_pass",
    "same_at_2_ci95",
    "same_at_2_given_cert_ci95",
    "plus_pass_ci95",
    "same_at_2_n_clusters",
    "plus_pass_n_clusters",
    "pilot_grid",
    "inference_version",
)

SLICE_METRICS = ("same_at_2", "same_at_2_given_cert", "plus_pass")

__all__ = [
    "BOOTSTRAP_SEED",
    "DEFAULT_N_BOOTSTRAP",
    "FROZEN_PROTOCOL_N",
    "INFERENCE",
    "INFERENCE_VERSION",
    "METRIC_HELP",
    "PILOT_TASK_WARN_BELOW",
    "RELATION_VERSION",
    "RELATION_VERSION_NOTE",
    "REQUIRED_SLICE_KEYS",
    "SCHEMA",
    "SLICE_METRICS",
]
