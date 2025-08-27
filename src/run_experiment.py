import argparse, json, time
from .log import log_row, sha256
from .contract_checker import check_contract
from .metrics import r_raw, r_canon, canon_coverage, rescue_delta
def run_suite(templates, runs, model, temperature, out_csv):
    rows = []
    for tpl in templates:
        pid, ptxt = tpl["id"], tpl["prompt"]
        enforce = tpl.get("enforce_function_name")
        oracle = tpl.get("oracle")
        for run_id in range(1, runs+1):
            from .experiment import call_model
            code = call_model(ptxt, model=model, temperature=temperature)
            chk = check_contract(code, enforce_function_name=enforce, oracle=oracle)
            row = {
                "ts": int(time.time()),
                "prompt_id": pid,
                "run_id": run_id,
                "model": model,
                "temperature": temperature,
                "raw_hash": sha256(code),
                "canon_signature": chk["canon_signature"],
                "oracle_pass": int(bool(chk["oracle_pass"])),
                "structural_ok": int(bool(chk["structural_ok"])),
                "canonicalization_ok": int(bool(chk["canonicalization_ok"])),
                "contract_pass": int(bool(chk["contract_pass"])),
                "notes": ";".join(chk["structural_errors"][:3]),
                "metrics_version": "2025-08-26"
            }
            rows.append(row); log_row(out_csv, row)
    return rows
def summarize(rows):
    return {"R_raw": r_raw(rows), "R_canon": r_canon(rows), "Canon_coverage": canon_coverage(rows), "Rescue_delta": rescue_delta(rows)}
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--templates", required=True)
    ap.add_argument("--runs", type=int, default=50)
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--out_csv", default="outputs/results.csv")
    a = ap.parse_args()
    templates = json.load(open(a.templates, "r", encoding="utf-8"))
    rows = run_suite(templates, a.runs, a.model, a.temperature, a.out_csv)
    print("[SUMMARY]", summarize(rows))
