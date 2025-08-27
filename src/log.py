import csv, hashlib, os
FIELDS = ["ts","prompt_id","run_id","model","temperature","raw_hash","canon_signature","oracle_pass","structural_ok","canonicalization_ok","contract_pass","notes","metrics_version"]
def sha256(s: str) -> str: 
    import hashlib; return hashlib.sha256(s.encode("utf-8")).hexdigest()
def ensure_csv(path: str):
    new = not os.path.exists(path)
    f = open(path,"a",newline="",encoding="utf-8")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new: w.writeheader()
    return f,w
def log_row(path, row):
    f,w = ensure_csv(path); w.writerow(row); f.close()
