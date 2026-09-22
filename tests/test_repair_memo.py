"""Repair-memo inherit oracle. No Docker, no API."""

from skyt.humaneval_repair import humaneval_repair_contract
from skyt.repair_memo import InheritPlusOracle, entry_function_dump, preindex_level3
from src.transformations.convert_to_simple_algorithm import convert_to_simple_algorithm

FORM_A = "def add(a, b):\n    return a + b\n"
FORM_B = "def add(a, b):\n    total = a + b\n    return total\n"


def _problem():
    return {"entry_point": "add", "task_id": "HumanEval/0"}


def _payload(ok=True):
    return {
        "passed": ok,
        "pass_rate": 1.0 if ok else 0.0,
        "base_passed": ok,
        "plus_passed": ok,
        "certified": ok,
    }


def test_entry_dump_ignores_helpers_name_match():
    dump_a = entry_function_dump(FORM_A, "add")
    dump_b = entry_function_dump(FORM_B, "add")
    assert dump_a
    assert dump_a != dump_b


def test_inherit_hash_hit():
    oracle = InheritPlusOracle(_problem(), allow_docker=False)
    oracle.index_payload(FORM_A, _payload(True))
    result = oracle.run_oracle_tests(FORM_A)
    assert result["passed"] is True
    assert oracle.n_hits == 1


def test_level3_output_inherits_canon_after_preindex():
    oracle = InheritPlusOracle(_problem(), allow_docker=False)
    payload = _payload(True)
    oracle.bind_canon(FORM_A, payload)
    records = [{"stitched_code": FORM_B}]
    contract = humaneval_repair_contract(
        task_id="HumanEval/0",
        model="gpt-4o-mini",
        temperature=0.0,
        prompt="def add(a, b):\n",
        entry_point="add",
    )
    n = preindex_level3(oracle, records, FORM_A, contract, payload)
    assert n == 1
    transformed = convert_to_simple_algorithm(FORM_B, FORM_A, contract)["transformed_code"]
    result = oracle.run_oracle_tests(transformed)
    assert result["passed"] is True
    assert result["plus_passed"] is True


def test_unknown_code_fails_closed_without_docker():
    oracle = InheritPlusOracle(_problem(), allow_docker=False)
    result = oracle.run_oracle_tests("def add(a, b):\n    return a * b\n")
    assert result["passed"] is False
    assert oracle.n_unresolved == 1
