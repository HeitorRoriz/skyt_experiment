"""Shared structural-repeatability measures for SKYT experiments.

The module deliberately separates three concerns:

* structural validity: an output can be represented by the structural ruler;
* certification: an output passes the behavioral oracle and static policy;
* canon policy: a representative is selected from certified outputs.

Pairs share generations and are therefore not independent binomial trials.
This module computes U-statistics; inference across tasks/contracts is handled
with an equal-cluster bootstrap.
"""

from __future__ import annotations

import itertools
import math
import random
import statistics
from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple


ZERO_TOL = 1e-12
Distance = Optional[float]
DistanceMatrix = List[List[Distance]]


def build_distance_matrix(
    items: Sequence[Optional[Any]],
    distance: Callable[[Any, Any], float],
) -> DistanceMatrix:
    """Build an NxN symmetric matrix while preserving invalid outputs.

    ``None`` items remain in the matrix with undefined distances. Keeping the
    original N is essential for end-to-end measures: invalid generations count
    in the denominator rather than disappearing from the experiment.
    """
    n = len(items)
    matrix: DistanceMatrix = [[None] * n for _ in range(n)]
    for i, item in enumerate(items):
        if item is not None:
            matrix[i][i] = 0.0
    for i in range(n):
        if items[i] is None:
            continue
        for j in range(i + 1, n):
            if items[j] is None:
                continue
            value = float(distance(items[i], items[j]))
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid distance at ({i}, {j}): {value!r}")
            matrix[i][j] = matrix[j][i] = value
    return matrix


def _validate_matrix(matrix: Sequence[Sequence[Distance]]) -> None:
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("Distance matrix must be square")
    for i in range(n):
        diagonal = matrix[i][i]
        if diagonal is not None:
            if not math.isfinite(diagonal) or diagonal < 0:
                raise ValueError(f"Invalid distance on matrix diagonal at {i}")
            if abs(diagonal) > ZERO_TOL:
                raise ValueError(f"Distance matrix diagonal is non-zero at {i}")
        for j in range(i + 1, n):
            left, right = matrix[i][j], matrix[j][i]
            if (left is None) != (right is None):
                raise ValueError(f"Distance matrix is asymmetric at ({i}, {j})")
            if left is not None:
                if not math.isfinite(left) or left < 0:
                    raise ValueError(f"Invalid distance at ({i}, {j})")
                if not math.isfinite(right) or right < 0:
                    raise ValueError(f"Invalid distance at ({j}, {i})")
                if abs(left - right) > ZERO_TOL:
                    raise ValueError(
                        f"Distance matrix is asymmetric at ({i}, {j})"
                    )


def _validate_mask(mask: Sequence[bool], n: int, name: str) -> None:
    if len(mask) != n:
        raise ValueError(f"{name} must contain exactly {n} values")


def _validate_valid_submatrix(
    matrix: Sequence[Sequence[Distance]],
    valid_mask: Sequence[bool],
) -> None:
    valid = [i for i, value in enumerate(valid_mask) if value]
    for i in valid:
        if matrix[i][i] is None:
            raise ValueError(f"Valid output {i} has no diagonal distance")
    for i, j in itertools.combinations(valid, 2):
        if matrix[i][j] is None:
            raise ValueError(
                f"Valid outputs {i} and {j} have no defined distance"
            )


def _is_match(matrix: Sequence[Sequence[Distance]], i: int, j: int) -> bool:
    value = matrix[i][j]
    return value is not None and value <= ZERO_TOL


def equivalence_classes(
    matrix: Sequence[Sequence[Distance]],
    indices: Iterable[int],
    *,
    validate_transitivity: bool = True,
    validate_matrix: bool = True,
) -> List[List[int]]:
    """Return distance-zero equivalence classes in deterministic order.

    Modal mass only has a coherent meaning if distance zero is an equivalence
    relation. The explicit transitivity check prevents union-find from silently
    joining a non-transitive chain into a fictitious class.
    """
    if validate_matrix:
        _validate_matrix(matrix)
    selected = sorted(set(indices))
    n = len(matrix)
    if any(i < 0 or i >= n for i in selected):
        raise IndexError("Equivalence-class index is outside the matrix")
    if any(matrix[i][i] is None for i in selected):
        raise ValueError("Equivalence classes require structurally valid items")

    if validate_transitivity:
        for i in selected:
            for j in selected:
                if not _is_match(matrix, i, j):
                    continue
                for k in selected:
                    if _is_match(matrix, j, k) and not _is_match(matrix, i, k):
                        raise ValueError(
                            "Distance-zero relation is not transitive: "
                            f"{i}~{j} and {j}~{k}, but {i}!~{k}"
                        )

    remaining = set(selected)
    classes: List[List[int]] = []
    while remaining:
        representative = min(remaining)
        group = sorted(i for i in remaining if _is_match(matrix, representative, i))
        classes.append(group)
        remaining.difference_update(group)
    return classes


def modal_share(
    matrix: Sequence[Sequence[Distance]],
    indices: Iterable[int],
    *,
    denominator: Optional[int] = None,
) -> float:
    """Return largest distance-zero class divided by the requested denominator."""
    selected = sorted(set(indices))
    if not selected:
        return 0.0
    classes = equivalence_classes(matrix, selected)
    denom = len(selected) if denominator is None else denominator
    if denom <= 0:
        raise ValueError("Modal-share denominator must be positive")
    return max(len(group) for group in classes) / denom


def select_certified_consensus(
    matrix: Sequence[Sequence[Distance]],
    certified_indices: Iterable[int],
    tie_break_keys: Sequence[str],
    *,
    validate_transitivity: bool = True,
) -> Optional[Dict[str, Any]]:
    """Select certified mode, medoid across tied modes, then lexical key.

    The returned ``index`` is an observed generation, not a synthetic program.
    """
    certified = sorted(set(certified_indices))
    if not certified:
        return None
    if len(tie_break_keys) != len(matrix):
        raise ValueError("One deterministic tie-break key is required per output")

    classes = equivalence_classes(
        matrix,
        certified,
        validate_transitivity=validate_transitivity,
        validate_matrix=validate_transitivity,
    )
    modal_size = max(len(group) for group in classes)
    tied_classes = [group for group in classes if len(group) == modal_size]

    candidates = [i for group in tied_classes for i in group]

    def mean_distance(candidate: int) -> float:
        others = [i for i in certified if i != candidate]
        if not others:
            return 0.0
        distances = [matrix[candidate][i] for i in others]
        if any(value is None for value in distances):
            raise ValueError("Certified outputs must have defined pairwise distances")
        return statistics.mean(float(value) for value in distances)

    index = min(
        candidates,
        key=lambda i: (mean_distance(i), tie_break_keys[i], i),
    )
    selected_class = next(group for group in tied_classes if index in group)
    return {
        "index": index,
        "class_indices": selected_class,
        "modal_size": modal_size,
        "medoid_mean_distance": mean_distance(index),
        "tie_break_key": tie_break_keys[index],
    }


def analyze_repeatability(
    matrix: Sequence[Sequence[Distance]],
    valid_mask: Sequence[bool],
    certified_mask: Sequence[bool],
    tie_break_keys: Sequence[str],
) -> Dict[str, Any]:
    """Compute frozen per-configuration repeatability measures."""
    _validate_matrix(matrix)
    n = len(matrix)
    _validate_mask(valid_mask, n, "valid_mask")
    _validate_mask(certified_mask, n, "certified_mask")
    _validate_valid_submatrix(matrix, valid_mask)
    if len(tie_break_keys) != n:
        raise ValueError("One deterministic tie-break key is required per output")
    if any(certified_mask[i] and not valid_mask[i] for i in range(n)):
        raise ValueError("Certified outputs must also be structurally valid")

    valid = [i for i, is_valid in enumerate(valid_mask) if is_valid]
    certified = [i for i, is_certified in enumerate(certified_mask) if is_certified]
    all_pairs = list(itertools.combinations(range(n), 2))
    valid_pairs = list(itertools.combinations(valid, 2))
    certified_pairs = list(itertools.combinations(certified, 2))

    matching_valid_pairs = sum(_is_match(matrix, i, j) for i, j in valid_pairs)
    matching_certified_pairs = sum(
        _is_match(matrix, i, j) for i, j in certified_pairs
    )
    valid_distances = [
        float(matrix[i][j])
        for i, j in valid_pairs
        if matrix[i][j] is not None
    ]

    consensus = select_certified_consensus(matrix, certified, tie_break_keys)
    modal_size = consensus["modal_size"] if consensus else 0

    return {
        "n_total": n,
        "n_valid": len(valid),
        "n_certified": len(certified),
        "certification_rate": len(certified) / n if n else 0.0,
        "n_pairs_total": len(all_pairs),
        "n_pairs_valid": len(valid_pairs),
        "n_pairs_certified": len(certified_pairs),
        # Population probability that two independent draws both certify and
        # have the same structural form.
        "pairwise_exact_match_end_to_end": (
            matching_certified_pairs / len(all_pairs) if all_pairs else None
        ),
        # Conditional probability of structural agreement given two certified
        # draws. Undefined when fewer than two outputs certify.
        "pairwise_exact_match_certified": (
            matching_certified_pairs / len(certified_pairs)
            if certified_pairs
            else None
        ),
        # Historical anchor-free measure among all structurally valid outputs.
        "pairwise_exact_match_valid": (
            matching_valid_pairs / len(valid_pairs) if valid_pairs else None
        ),
        "certified_modal_mass": modal_size / n if n else 0.0,
        "certified_modal_share": (
            modal_size / len(certified) if certified else None
        ),
        "valid_modal_mass": (
            modal_share(matrix, valid, denominator=n) if valid else 0.0
        ),
        "valid_modal_share": modal_share(matrix, valid) if valid else None,
        "pairwise_distance_valid_mean": (
            statistics.mean(valid_distances) if valid_distances else None
        ),
        "pairwise_distance_valid_std": (
            statistics.pstdev(valid_distances) if valid_distances else None
        ),
        "consensus_index": consensus["index"] if consensus else None,
        "consensus_modal_size": modal_size,
    }


def _balanced_splits(
    n: int,
    train_size: int,
    n_splits: int,
    seed: int,
) -> List[Tuple[int, ...]]:
    if not 1 <= train_size < n:
        raise ValueError("train_size must be between 1 and n-1")
    if n_splits <= 0:
        raise ValueError("n_splits must be positive")

    total = math.comb(n, train_size)
    if total <= n_splits:
        return list(itertools.combinations(range(n), train_size))

    rng = random.Random(seed)
    chosen = set()
    while len(chosen) < n_splits:
        chosen.add(tuple(sorted(rng.sample(range(n), train_size))))
    return sorted(chosen)


def repeated_balanced_cv(
    matrix: Sequence[Sequence[Distance]],
    valid_mask: Sequence[bool],
    certified_mask: Sequence[bool],
    tie_break_keys: Sequence[str],
    *,
    train_size: int = 10,
    n_splits: int = 2000,
    seed: int = 20260723,
) -> Dict[str, Any]:
    """Evaluate consensus-canon policy on repeated held-out splits."""
    _validate_matrix(matrix)
    n = len(matrix)
    _validate_mask(valid_mask, n, "valid_mask")
    _validate_mask(certified_mask, n, "certified_mask")
    _validate_valid_submatrix(matrix, valid_mask)
    if any(certified_mask[i] and not valid_mask[i] for i in range(n)):
        raise ValueError("Certified outputs must also be structurally valid")
    equivalence_classes(
        matrix,
        [i for i, value in enumerate(certified_mask) if value],
        validate_transitivity=True,
        validate_matrix=False,
    )

    splits = _balanced_splits(n, train_size, n_splits, seed)
    end_to_end_matches: List[float] = []
    conditional_matches: List[float] = []
    heldout_distances: List[float] = []
    stabilities: List[float] = []
    selected = 0

    universe = set(range(n))
    for train_tuple in splits:
        train = set(train_tuple)
        test = sorted(universe - train)
        train_certified = [i for i in train_tuple if certified_mask[i]]
        consensus = select_certified_consensus(
            matrix,
            train_certified,
            tie_break_keys,
            validate_transitivity=False,
        )
        if consensus is None:
            end_to_end_matches.append(0.0)
            continue

        selected += 1
        canon_index = consensus["index"]
        matching = [
            i for i in test
            if certified_mask[i] and _is_match(matrix, canon_index, i)
        ]
        end_to_end_matches.append(len(matching) / len(test))

        test_certified = [i for i in test if certified_mask[i]]
        if test_certified:
            conditional_matches.append(len(matching) / len(test_certified))

        test_valid = [i for i in test if valid_mask[i]]
        distances = [
            float(matrix[canon_index][i])
            for i in test_valid
            if matrix[canon_index][i] is not None
        ]
        if distances:
            heldout_distances.append(statistics.mean(distances))

        test_consensus = select_certified_consensus(
            matrix,
            test_certified,
            tie_break_keys,
            validate_transitivity=False,
        )
        if test_consensus is not None:
            stabilities.append(
                1.0 if _is_match(
                    matrix, canon_index, test_consensus["index"]
                ) else 0.0
            )

    return {
        "cv_train_size": train_size,
        "cv_n_splits": len(splits),
        "cv_seed": seed,
        "cv_selection_rate": selected / len(splits),
        "cv_heldout_match_end_to_end": statistics.mean(end_to_end_matches),
        "cv_heldout_match_certified": (
            statistics.mean(conditional_matches)
            if conditional_matches else None
        ),
        "cv_heldout_distance_valid": (
            statistics.mean(heldout_distances) if heldout_distances else None
        ),
        "cv_canon_stability": (
            statistics.mean(stabilities) if stabilities else None
        ),
        "cv_n_conditional_splits": len(conditional_matches),
        "cv_n_stability_splits": len(stabilities),
    }


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("Cannot take a percentile of no values")
    if not 0 <= probability <= 1:
        raise ValueError("Percentile probability must be in [0, 1]")
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
    seed: int = 20260723,
) -> Dict[str, float]:
    """Equal-cluster mean and percentile bootstrap interval.

    Every contract/task receives equal weight regardless of how many model or
    temperature configurations it contributes.
    """
    if len(values) != len(cluster_ids) or not values:
        raise ValueError("values and cluster_ids must be non-empty and aligned")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be in (0, 1)")
    if n_bootstrap <= 0:
        raise ValueError("n_bootstrap must be positive")

    grouped: Dict[str, List[float]] = defaultdict(list)
    for value, cluster_id in zip(values, cluster_ids):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"Non-finite cluster value: {value!r}")
        grouped[str(cluster_id)].append(numeric)

    cluster_means = [
        statistics.mean(grouped[cluster_id])
        for cluster_id in sorted(grouped)
    ]
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
