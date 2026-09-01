"""Certified Consensus pick for the SKYT runtime canon.

Certified = oracle pass + contract compliance. The selected program is an
observed generation (certified mode, medoid on ties, lexical key). This module
does not invent a canon via make_compliant.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .contract_compliance import check_contract_compliance
from .foundational_properties import FoundationalProperties
from .repeatability_protocol import (
    build_distance_matrix,
    select_certified_consensus,
)


def certification_mask(
    codes: Sequence[str],
    contract: Dict[str, Any],
    oracle_results: Sequence[Dict[str, Any]],
) -> List[bool]:
    if len(codes) != len(oracle_results):
        raise ValueError("oracle_results must align with codes")
    mask = []
    for code, oracle in zip(codes, oracle_results):
        oracle_passed = bool((oracle or {}).get("passed"))
        compliant, _ = check_contract_compliance(code or "", contract or {})
        mask.append(oracle_passed and compliant)
    return mask


def select_certified_consensus_canon(
    codes: Sequence[str],
    contract: Dict[str, Any],
    oracle_results: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """Return the Certified Consensus generation, or None if none certify."""
    n = len(codes)
    if n == 0:
        return None
    certified = certification_mask(codes, contract, oracle_results)
    extractor = FoundationalProperties(contract)
    extracted = [
        extractor.extract_all_properties(code or "") for code in codes
    ]
    props: List[Optional[Dict[str, Any]]] = []
    valid_mask = []
    for item in extracted:
        is_valid = any(value is not None for value in item.values())
        valid_mask.append(is_valid)
        props.append(item if is_valid else None)

    certified_and_valid = [
        bool(certified[i] and valid_mask[i]) for i in range(n)
    ]
    if not any(certified_and_valid):
        return None

    matrix = build_distance_matrix(
        props,
        lambda left, right: extractor.calculate_distance(left, right, contract),
    )
    selected = select_certified_consensus(
        matrix,
        [i for i, ok in enumerate(certified_and_valid) if ok],
        [code or "" for code in codes],
    )
    if selected is None:
        return None
    index = int(selected["index"])
    return {
        "index": index,
        "code": codes[index],
        "oracle_result": oracle_results[index],
        "selection": selected,
        "n_certified": sum(certified_and_valid),
        "canon_policy": "certified_consensus",
    }
