from collections import Counter
def r_raw(rows): 
    if not rows: return 0.0
    from collections import Counter
    c = Counter(r["raw_hash"] for r in rows)
    return max(c.values())/len(rows)
def r_canon(rows):
    ok = [r for r in rows if r.get("contract_pass")]
    if not ok: return 0.0
    c = Counter(r["canon_signature"] for r in ok)
    return max(c.values())/len(ok)
def canon_coverage(rows):
    if not rows: return 0.0
    return sum(1 for r in rows if r.get("contract_pass"))/len(rows)
def rescue_delta(rows):
    return r_canon(rows) - r_raw(rows)
