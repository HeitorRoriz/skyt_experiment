"""
Deep dive: what's the most impactful rescue figure SKYT can honestly claim?

Looks at the data from multiple angles:
  A. Per-cell peaks at full sample size (n>=20)
  B. Per-(contract, model) aggregates pooled across temperatures
  C. Per-contract aggregates pooled across all models and temperatures
  D. The "rescue at high temperature" story (T>=0.5)
  E. How often does SKYT meaningfully help (Delta >= 0.30)?
"""
import csv
from collections import defaultdict
from statistics import mean

CSV = "outputs/metrics_summary.csv"

def load():
    rows = []
    with open(CSV, newline="") as f:
        for r in csv.DictReader(f):
            for k in ("R_raw", "R_anchor_pre", "R_anchor_post", "Delta_rescue"):
                try: r[k] = float(r[k]) if r[k] != "" else None
                except: r[k] = None
            try: r["runs"] = int(r["runs"])
            except: r["runs"] = 0
            try: r["decoding_temperature"] = float(r["decoding_temperature"])
            except: pass
            rows.append(r)
    return rows


def latest(rows):
    by = {}
    for r in rows:
        k = (r["contract_id"], r["model"], r["decoding_temperature"])
        if k not in by or r["timestamp"] > by[k]["timestamp"]:
            by[k] = r
    return list(by.values())


def wmean(vals, ws):
    pairs = [(v, w) for v, w in zip(vals, ws) if v is not None and w]
    if not pairs:
        return None
    tw = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / tw if tw else None


rows = latest(load())
print(f"Total unique cells: {len(rows)}\n")

# ---------- A. Top 10 cells at full sample size (runs>=20) ----------
print("=" * 86)
print("A. TOP 15 RESCUE CELLS at FULL SAMPLE SIZE (runs >= 20)")
print("=" * 86)
full = [r for r in rows if r["runs"] >= 20]
print(f"   {len(full)} cells have runs >= 20 (out of {len(rows)} total)")
top = sorted(full, key=lambda r: r["Delta_rescue"] or -1, reverse=True)[:15]
print(f"\n{'Contract':<24} {'Model':<28} {'T':>4} {'n':>3} "
      f"{'R_raw':>6} {'R_pre':>6} {'R_post':>7} {'Delta':>7}")
print("-" * 86)
for r in top:
    print(f"{r['contract_id']:<24} {r['model']:<28} {r['decoding_temperature']:>4} "
          f"{r['runs']:>3} {r['R_raw']:>6.2f} {r['R_anchor_pre']:>6.2f} "
          f"{r['R_anchor_post']:>7.2f} {r['Delta_rescue']:>+7.3f}")

# ---------- B. Per (contract, model) aggregates (all temps, n>=20 cells only) ----------
print("\n" + "=" * 86)
print("B. PER (contract, model) AGGREGATE, full-sample cells only")
print("=" * 86)
groups = defaultdict(list)
for r in full:
    groups[(r["contract_id"], r["model"])].append(r)
agg = []
for (c, m), cells in groups.items():
    ws = [c2["runs"] for c2 in cells]
    raw  = wmean([c2["R_raw"] for c2 in cells], ws)
    pre  = wmean([c2["R_anchor_pre"] for c2 in cells], ws)
    post = wmean([c2["R_anchor_post"] for c2 in cells], ws)
    delta= wmean([c2["Delta_rescue"] for c2 in cells], ws)
    n    = sum(ws)
    agg.append((c, m, raw, pre, post, delta, n, len(cells)))
agg.sort(key=lambda x: x[5] or -1, reverse=True)
print(f"\n{'Contract':<24} {'Model':<28} {'Cells':>6} {'n':>4} "
      f"{'R_raw':>6} {'R_pre':>6} {'R_post':>7} {'Delta':>7}")
print("-" * 86)
for c, m, raw, pre, post, delta, n, k in agg[:20]:
    print(f"{c:<24} {m:<28} {k:>6} {n:>4} {raw:>6.2f} {pre:>6.2f} {post:>7.2f} {delta:>+7.3f}")

# ---------- C. Per-contract aggregates (all models, all temps, n>=20 cells) ----------
print("\n" + "=" * 86)
print("C. PER-CONTRACT AGGREGATE (pooled across all models & temps, n>=20)")
print("=" * 86)
by_c = defaultdict(list)
for r in full:
    by_c[r["contract_id"]].append(r)
contract_aggs = []
for c, cells in by_c.items():
    ws = [r["runs"] for r in cells]
    delta = wmean([r["Delta_rescue"] for r in cells], ws)
    raw   = wmean([r["R_raw"] for r in cells], ws)
    post  = wmean([r["R_anchor_post"] for r in cells], ws)
    contract_aggs.append((c, raw, post, delta, sum(ws), len(cells)))
contract_aggs.sort(key=lambda x: x[3] or -1, reverse=True)
print(f"\n{'Contract':<24} {'Cells':>6} {'n':>4} {'R_raw':>7} {'R_post':>7} {'Delta':>7}")
print("-" * 60)
for c, raw, post, delta, n, k in contract_aggs:
    print(f"{c:<24} {k:>6} {n:>4} {raw:>7.2f} {post:>7.2f} {delta:>+7.3f}")

# ---------- D. The "rescue at HIGH temperature" story ----------
print("\n" + "=" * 86)
print("D. HIGH-TEMPERATURE STORY (T >= 0.5, full samples)")
print("=" * 86)
hi = [r for r in full if r["decoding_temperature"] >= 0.5]
print(f"   {len(hi)} cells at T>=0.5 with n>=20")
top_hi = sorted(hi, key=lambda r: r["Delta_rescue"] or -1, reverse=True)[:10]
print(f"\n{'Contract':<24} {'Model':<28} {'T':>4} {'n':>3} "
      f"{'R_raw':>6} {'R_post':>7} {'Delta':>7}")
print("-" * 80)
for r in top_hi:
    print(f"{r['contract_id']:<24} {r['model']:<28} {r['decoding_temperature']:>4} "
          f"{r['runs']:>3} {r['R_raw']:>6.2f} "
          f"{r['R_anchor_post']:>7.2f} {r['Delta_rescue']:>+7.3f}")

# ---------- E. How often does SKYT meaningfully help? ----------
print("\n" + "=" * 86)
print("E. DISTRIBUTION OF Delta_rescue (full-sample cells only)")
print("=" * 86)
deltas = [r["Delta_rescue"] for r in full if r["Delta_rescue"] is not None]
total = len(deltas)
buckets = [
    (">= 0.50", sum(1 for d in deltas if d >= 0.50)),
    (">= 0.30", sum(1 for d in deltas if d >= 0.30)),
    (">= 0.10", sum(1 for d in deltas if d >= 0.10)),
    ("> 0",     sum(1 for d in deltas if d > 0)),
    ("= 0",     sum(1 for d in deltas if d == 0)),
    ("< 0",     sum(1 for d in deltas if d < 0)),
]
print(f"   total cells: {total}")
for label, n in buckets:
    print(f"   Delta {label:<8}: {n:>3} cells ({100.0*n/total:>5.1f}%)")
print(f"   median Delta: {sorted(deltas)[total//2]:+.3f}")
print(f"   mean   Delta: {mean(deltas):+.3f}")

# ---------- F. Subset where SKYT is "intended": GPT-4o-mini cells ----------
print("\n" + "=" * 86)
print("F. GPT-4o-mini ONLY (the model the paper highlights)")
print("=" * 86)
gpt4om = [r for r in full if r["model"] == "gpt-4o-mini"]
print(f"   {len(gpt4om)} GPT-4o-mini cells with n>=20")
deltas_g = [r["Delta_rescue"] for r in gpt4om if r["Delta_rescue"] is not None]
print(f"   mean Delta:   {mean(deltas_g):+.3f}")
print(f"   median Delta: {sorted(deltas_g)[len(deltas_g)//2]:+.3f}")
print(f"   max Delta:    {max(deltas_g):+.3f}")
print(f"   cells with Delta >= 0.30: {sum(1 for d in deltas_g if d >= 0.30)}/{len(deltas_g)}")
print(f"   cells with Delta >= 0.50: {sum(1 for d in deltas_g if d >= 0.50)}/{len(deltas_g)}")
