import csv, collections, argparse, os
import matplotlib.pyplot as plt
def load(p): 
    with open(p, newline="", encoding="utf-8") as f: return list(csv.DictReader(f))
def hist(rows, key, title, out_png):
    c = collections.Counter(r[key] for r in rows)
    xs, ys = list(c.keys()), list(c.values())
    plt.figure(); plt.bar(range(len(xs)), ys)
    plt.xticks(range(len(xs)), [x[:8] for x in xs], rotation=45, ha="right")
    plt.title(title); plt.tight_layout();
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    plt.savefig(out_png, dpi=180); plt.close()
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--csv", required=True); ap.add_argument("--tag", required=True); a = ap.parse_args()
    rows = load(a.csv)
    hist(rows, "raw_hash", f"Raw outputs ({a.tag})", f"outputs/hist_raw_{a.tag}.png")
    canon_rows = [r for r in rows if r["contract_pass"] == "1"]
    if canon_rows: hist(canon_rows, "canon_signature", f"Canonical outputs ({a.tag})", f"outputs/hist_canon_{a.tag}.png")
