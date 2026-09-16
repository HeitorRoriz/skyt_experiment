"""same@2 and same@2|cert. No canon pick, no CV, no human match."""

from __future__ import annotations

import itertools
import math
import random
import statistics
from collections import defaultdict
from typing import Dict, List, Optional, Sequence

from .schema import BOOTSTRAP_SEED


# Two-sided 0.95 normal quantile. Jackknife intervals are only pinned at 95%.
_Z95 = 1.959963984540054


def config_repeatability(
    fingerprints: Sequence[Optional[str]],
    certified: Sequence[bool],
) -> Dict[str, Optional[float]]:
    """Pairwise rates for one task × model × temperature.

    ``certified[i]`` must already be False when ``fingerprints[i]`` is None.
    Pair counts are the U-statistic size, never the *n* of a confidence interval.
    """
    n = len(fingerprints)
    if n != len(certified):
        raise ValueError("fingerprints and certified must be aligned")
    if n < 2:
        raise ValueError("Need at least two generations")
    if any(ok and fingerprints[i] is None for i, ok in enumerate(certified)):
        raise ValueError("Certified generations must have a fingerprint")

    all_pairs = list(itertools.combinations(range(n), 2))
    matching_certified = 0
    certified_pairs = 0
    for i, j in all_pairs:
        if certified[i] and certified[j]:
            certified_pairs += 1
            if fingerprints[i] == fingerprints[j]:
                matching_certified += 1

    n_certified = sum(1 for ok in certified if ok)
    return {
        "n": n,
        "n_certified": n_certified,
        "plus_pass": n_certified / n,
        "same_at_2": matching_certified / len(all_pairs),
        "same_at_2_given_cert": (
            matching_certified / certified_pairs if certified_pairs else None
        ),
        "u_statistic_pair_count": len(all_pairs),
        "u_statistic_certified_pair_count": certified_pairs,
    }


def _cluster_means(
    values: Sequence[float],
    cluster_ids: Sequence[str],
) -> List[float]:
    if len(values) != len(cluster_ids) or not values:
        raise ValueError("values and cluster_ids must be non-empty and aligned")
    grouped: Dict[str, List[float]] = defaultdict(list)
    for value, cluster_id in zip(values, cluster_ids):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"Non-finite cluster value: {value!r}")
        grouped[str(cluster_id)].append(numeric)
    return [statistics.mean(grouped[key]) for key in sorted(grouped)]


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("Cannot take a percentile of no values")
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return (
        sorted_values[lower] * (1 - weight)
        + sorted_values[upper] * weight
    )


def cluster_bootstrap_mean(
    values: Sequence[float],
    cluster_ids: Sequence[str],
    *,
    confidence: float = 0.95,
    n_bootstrap: int = 10000,
    seed: int = BOOTSTRAP_SEED,
) -> Dict[str, float]:
    """Equal-cluster mean. One weight per task_id, not per pair."""
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")
    cluster_means = _cluster_means(values, cluster_ids)
    point = statistics.mean(cluster_means)
    rng = random.Random(seed)
    boot = sorted(
        statistics.mean(rng.choices(cluster_means, k=len(cluster_means)))
        for _ in range(n_bootstrap)
    )
    alpha = (1.0 - confidence) / 2.0
    return {
        "mean": point,
        "lower": _percentile(boot, alpha),
        "upper": _percentile(boot, 1.0 - alpha),
        "n_clusters": len(cluster_means),
        "n_observations": len(values),
    }


def cluster_jackknife_mean(
    values: Sequence[float],
    cluster_ids: Sequence[str],
    *,
    confidence: float = 0.95,
) -> Dict[str, Optional[float]]:
    """Leave-one-task-out SE. Sensitivity next to the bootstrap, not a pair CI.

    Skipped when there are fewer than three tasks.
    """
    cluster_means = _cluster_means(values, cluster_ids)
    point = statistics.mean(cluster_means)
    n_clusters = len(cluster_means)
    base = {
        "mean": point,
        "se": None,
        "lower": None,
        "upper": None,
        "n_clusters": n_clusters,
        "n_observations": len(values),
        "skipped": None,
    }
    if n_clusters < 3:
        base["skipped"] = "need_at_least_3_tasks"
        return base
    if abs(confidence - 0.95) > 1e-12:
        raise ValueError("cluster_jackknife_mean only pins z for confidence=0.95")
    leave = [
        statistics.mean(cluster_means[:index] + cluster_means[index + 1 :])
        for index in range(n_clusters)
    ]
    theta_dot = statistics.mean(leave)
    ss = sum((item - theta_dot) ** 2 for item in leave)
    se = math.sqrt(((n_clusters - 1) / n_clusters) * ss)
    half = _Z95 * se
    base["se"] = se
    base["lower"] = point - half
    base["upper"] = point + half
    return base
