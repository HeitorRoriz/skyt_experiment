from typing import Dict, Any, Optional, Tuple, List
from .determinism_lint import check_determinism_rules
from .canonicalizer import canonicalize_python

_EXPECTED_FIB20 = [0,1,1,2,3,5,8,13,21,34,55,89,144,233,377,610,987,1597,2584,4181]

def _safe_exec(py_source: str, ns: Dict[str, Any]) -> None:
    ns["__builtins__"] = {
        "range": range, "len": len, "print": print, "list": list, "dict": dict,
        "tuple": tuple, "set": set, "abs": abs, "min": min, "max": max, "sum": sum, "ord": ord, "chr": chr
    }
    exec(py_source, ns, ns)

def _oracle_fibonacci20(py_source: str, fn_name: str) -> Tuple[bool,str]:
    ns: Dict[str, Any] = {}
    try:
        _safe_exec(py_source, ns)
        if fn_name not in ns or not callable(ns[fn_name]): return False, "Missing required function"
        out = ns[fn_name]()
        ok = (out == _EXPECTED_FIB20)
        return ok, ("ok" if ok else f"Unexpected output: {out}")
    except Exception as e:
        return False, f"Runtime error: {e}"

def _oracle_slugify_basic(py_source: str, fn_name: str) -> Tuple[bool,str]:
    tests = ["São  Paulo", "  SkYt  Project ", "a_b  c"]
    expected = ["sao-paulo","skyt-project","a-b-c"]
    ns: Dict[str, Any] = {}
    try:
        _safe_exec(py_source, ns)
        if fn_name not in ns: return False, "Missing required function"
        out = ns[fn_name](tests)
        return (out == expected), ("ok" if out == expected else f"Unexpected: {out}")
    except Exception as e:
        return False, f"Runtime error: {e}"

def _oracle_csv_to_json_basic(py_source: str, fn_name: str) -> Tuple[bool,str]:
    csv_text = "name,age\nAda,36\nTuring,41\n"
    expected = [{"age":"36","name":"Ada"},{"age":"41","name":"Turing"}]
    ns: Dict[str, Any] = {}
    try:
        _safe_exec(py_source, ns)
        if fn_name not in ns: return False, "Missing required function"
        out = ns[fn_name](csv_text)
        # compare as sorted-by-keys strings for stability
        def norm(d): return {k:str(d[k]) for k in sorted(d.keys())}
        ok = [norm(x) for x in out] == [norm(x) for x in expected]
        return ok, ("ok" if ok else f"Unexpected: {out}")
    except Exception as e:
        return False, f"Runtime error: {e}"

def _oracle_balanced_brackets_basic(py_source: str, fn_name: str) -> Tuple[bool,str]:
    cases = ["([]){}", "([)]", "{[()()]}", "((("]
    expected = [True, False, True, False]
    ns: Dict[str, Any] = {}
    try:
        _safe_exec(py_source, ns)
        if fn_name not in ns: return False, "Missing required function"
        out = [ns[fn_name](s) for s in cases]
        return (out == expected), ("ok" if out == expected else f"Unexpected: {out}")
    except Exception as e:
        return False, f"Runtime error: {e}"

def _run_oracle(py_source: str, fn_name: str, oracle: Optional[str]) -> Tuple[bool, str]:
    if oracle is None:
        return True, "no_oracle"
    table = {
        "fibonacci20": _oracle_fibonacci20,
        "slugify_basic": _oracle_slugify_basic,
        "csv_to_json_basic": _oracle_csv_to_json_basic,
        "balanced_brackets_basic": _oracle_balanced_brackets_basic,
    }
    if oracle not in table:
        return False, f"Unknown oracle: {oracle}"
    return table[oracle](py_source, fn_name)

def check_contract(py_source: str, enforce_function_name: Optional[str] = None, oracle: Optional[str] = None) -> Dict[str, Any]:
    structural_errors = check_determinism_rules(py_source)
    structural_ok = len(structural_errors) == 0
    canon_code, canon_signature, canonicalization_ok = canonicalize_python(py_source, enforce_function_name=enforce_function_name)
    if structural_ok and canonicalization_ok:
        oracle_pass, oracle_msg = _run_oracle(py_source, enforce_function_name or "", oracle)
    else:
        oracle_pass, oracle_msg = False, "skipped_oracle_due_to_structure_or_canon_failure"
    if oracle is None and structural_ok and canonicalization_ok:
        oracle_pass, oracle_msg = True, "no_oracle"
    contract_pass = structural_ok and canonicalization_ok and (oracle is None or oracle_pass)
    return {
        "structural_ok": structural_ok,
        "structural_errors": structural_errors,
        "canonicalization_ok": canonicalization_ok,
        "oracle_pass": oracle_pass,
        "oracle_msg": oracle_msg,
        "canon_code": canon_code,
        "canon_signature": canon_signature,
        "contract_pass": contract_pass,
    }
