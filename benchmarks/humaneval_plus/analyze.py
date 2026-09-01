"""Score a HumanEval+ config with the frozen repeatability protocol.

Certified = HumanEval+ (plus) pass. Original HumanEval (base) is stored
alongside and never mixed into SKYT contract-compliance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from src.foundational_properties import FoundationalProperties
from src.repeatability_protocol import (
    analyze_repeatability,
    build_distance_matrix,
    repeated_balanced_cv,
    select_certified_consensus,
)

# Flexible naming only. This arm does not author style contracts.
_HE_CONTRACT = {"constraints": {"variable_naming": {"naming_policy": "flexible"}}}


def analyze_records(
    records: Sequence[Dict[str, Any]],
    *,
    cv_splits: int = 2000,
    cv_seed: int = 20260723,
) -> Dict[str, Any]:
    n = len(records)
    if n < 2:
        raise ValueError("Need at least two generations")

    extractor = FoundationalProperties(_HE_CONTRACT)
    codes = [record.get("stitched_code") or "" for record in records]
    props: List[Optional[Dict[str, Any]]] = []
    valid_mask = []
    for code in codes:
        extracted = extractor.extract_all_properties(code)
        is_valid = any(value is not None for value in extracted.values())
        props.append(extracted if is_valid else None)
        valid_mask.append(is_valid)

    certified_mask = []
    base_mask = []
    for record, is_valid in zip(records, valid_mask):
        oracle = record.get("oracle") or {}
        base_ok = bool(oracle.get("base_passed"))
        plus_ok = oracle.get("plus_passed")
        certified = bool(oracle.get("certified")) if plus_ok is not None else base_ok
        base_mask.append(base_ok and is_valid)
        certified_mask.append(certified and is_valid)

    matrix = build_distance_matrix(
        props,
        lambda left, right: extractor.calculate_distance(left, right, _HE_CONTRACT),
    )
    frozen = analyze_repeatability(matrix, valid_mask, certified_mask, codes)
    train_size = min(10, n // 2)
    cv = repeated_balanced_cv(
        matrix,
        valid_mask,
        certified_mask,
        codes,
        train_size=train_size,
        n_splits=cv_splits,
        seed=cv_seed,
    )
    human_code = None
    # Optional: first record may carry the human reference for a baseline.
    human_match = None
    if records and records[0].get("human_reference_code"):
        human_code = records[0]["human_reference_code"]
        human_props = extractor.extract_all_properties(human_code)
        matches = 0
        compared = 0
        for index, is_certified in enumerate(certified_mask):
            if not is_certified or props[index] is None:
                continue
            compared += 1
            if extractor.calculate_distance(human_props, props[index], _HE_CONTRACT) <= 1e-12:
                matches += 1
        human_match = {
            "n_certified": sum(certified_mask),
            "n_structurally_equal_to_human": matches,
        }

    consensus = select_certified_consensus(matrix, [i for i, ok in enumerate(certified_mask) if ok], codes)
    return {
        **frozen,
        **cv,
        "n_base_passed": sum(base_mask),
        "n_plus_certified": sum(certified_mask),
        "consensus_index": consensus["index"] if consensus else None,
        "human_reference": human_match,
        "no_skyt_repair": True,
        "no_style_contracts": True,
    }
