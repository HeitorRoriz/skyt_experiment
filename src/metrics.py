from collections import Counter
def _is_true(v) -> bool:
    """Normalize various truthy encodings from CSV or memory.
    Accepts 1/0, "1"/"0", "true"/"false" (case-insensitive), True/False.
    """
    if isinstance(v, bool):
        return v
    try:
        if isinstance(v, (int, float)):
            return v != 0
    except Exception:
        pass
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("1", "true", "yes", "y"): return True
        if s in ("0", "false", "no", "n", ""): return False
    return bool(v)

def r_raw(rows): 
    if not rows: return 0.0
    from collections import Counter
    c = Counter(r["raw_hash"] for r in rows)
    return max(c.values())/len(rows)

def r_canon(rows):
    ok = [r for r in rows if _is_true(r.get("contract_pass"))]
    if not ok: return 0.0
    c = Counter(r["canon_signature"] for r in ok)
    return max(c.values())/len(ok)

def canon_coverage(rows):
    if not rows: return 0.0
    return sum(1 for r in rows if _is_true(r.get("contract_pass")))/len(rows)

def rescue_delta(rows):
    return r_canon(rows) - r_raw(rows)
