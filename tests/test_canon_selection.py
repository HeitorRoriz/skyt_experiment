"""Certified Consensus is the runtime canon pick."""

from src.canon_selection import select_certified_consensus_canon
from src.canon_system import CanonSystem
from src.contract import Contract


def _contract():
    return {
        "id": "smoke_add",
        "task_intent": "add",
        "prompt": "def add(a, b):\n",
        "language": "python",
        "contract_version": "2.0",
        "created_timestamp": "2026-09-01",
        "constraints": {"forbidden_patterns": ["eval("]},
    }


def test_consensus_is_certified_mode_not_first_passer():
    first = "def add(a, b):\n    return a - b\n"
    typical = "def add(a, b):\n    return a + b\n"
    other = "def add(a, b):\n    x = a + b\n    return x\n"
    codes = [first, typical, typical, typical, other]
    oracles = [
        {"passed": False},
        {"passed": True},
        {"passed": True},
        {"passed": True},
        {"passed": True},
    ]
    selected = select_certified_consensus_canon(codes, _contract(), oracles)
    assert selected is not None
    assert selected["index"] in {1, 2, 3}
    assert selected["code"] == typical
    assert selected["canon_policy"] == "certified_consensus"


def test_uncertified_majority_is_not_elected():
    junk = "def add(a, b):\n    return 0\n"
    good = "def add(a, b):\n    return a + b\n"
    codes = [junk, junk, junk, junk, good, good]
    oracles = [{"passed": False}] * 4 + [{"passed": True}, {"passed": True}]
    selected = select_certified_consensus_canon(codes, _contract(), oracles)
    assert selected["index"] in {4, 5}
    assert selected["n_certified"] == 2


def test_zero_certified_returns_none():
    codes = ["def add(a, b):\n    return a + b\n"] * 4
    oracles = [{"passed": False}] * 4
    assert select_certified_consensus_canon(codes, _contract(), oracles) is None


def test_forbidden_pattern_is_not_certified():
    codes = [
        "def add(a, b):\n    eval('1')\n    return a + b\n",
        "def add(a, b):\n    return a + b\n",
    ]
    oracles = [{"passed": True}, {"passed": True}]
    selected = select_certified_consensus_canon(codes, _contract(), oracles)
    assert selected["index"] == 1


def test_canon_system_does_not_reuse_disk_first_valid(tmp_path):
    contract = Contract(_contract())
    system = CanonSystem(str(tmp_path))
    oracle = {"passed": True, "pass_rate": 1.0}
    created = system.create_canon(
        contract, "def add(a, b):\n    return a + b\n", oracle_result=oracle
    )
    assert created["canon_policy"] == "certified_consensus"
    assert system.load_canon("smoke_add")["canonical_code"] == created["canonical_code"]
    other = CanonSystem(str(tmp_path))
    assert other.load_canon("smoke_add") is None
