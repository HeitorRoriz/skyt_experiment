"""
Extract the headline numbers requested by the SBES Industry Track paper.
All numbers come from outputs/metrics_summary.csv.
Each row is an aggregated cell (contract x model x temperature) with `runs` runs.
"""
import csv
from collections import defaultdict
from statistics import mean

CSV_PATH = "outputs/metrics_summary.csv"

MODEL_DISPLAY = {
    "gpt-4o-mini": "GPT-4o-mini",
    "gpt-4o": "GPT-4o",
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
}
TASK_DISPLAY = {
    "balanced_brackets": "Balanced Brackets",
    "binary_search":     "Binary Search",
    "slugify":           "Slugify",
}
PAPER_TASKS = ["balanced_brackets", "binary_search", "slugify"]
PAPER_MODELS = ["gpt-4o-mini", "gpt-4o", "claude-sonnet-4-5-20250929"]


def load() -> list[dict]:
    rows = []
    with open(CSV_PATH, newline="") as f:
        for r in csv.DictReader(f):
            for k in ("R_raw", "R_anchor_pre", "R_anchor_post", "Delta_rescue"):
                try:
                    r[k] = float(r[k]) if r[k] != "" else None
                except ValueError:
                    r[k] = None
            try:
                r["runs"] = int(r["runs"])
            except (ValueError, KeyError):
                r["runs"] = 20
            try:
                r["decoding_temperature"] = float(r["decoding_temperature"])
            except ValueError:
                pass
            rows.append(r)
    return rows


def filt(rows, contract=None, model=None, temp=None):
    out = rows
    if contract is not None:
        out = [r for r in out if r["contract_id"] == contract]
    if model is not None:
        out = [r for r in out if r["model"] == model]
    if temp is not None:
        out = [r for r in out if r["decoding_temperature"] == temp]
    return out


def latest_per_cell(rows):
    """De-duplicate when a (contract, model, temp) cell has more than one row,
    keeping the most recent timestamp."""
    by_key = {}
    for r in rows:
        key = (r["contract_id"], r["model"], r["decoding_temperature"])
        if key not in by_key or r["timestamp"] > by_key[key]["timestamp"]:
            by_key[key] = r
    return list(by_key.values())


def weighted_mean(values, weights):
    pairs = [(v, w) for v, w in zip(values, weights) if v is not None]
    if not pairs:
        return None
    total_w = sum(w for _, w in pairs)
    return sum(v * w for v, w in pairs) / total_w if total_w else None


def main():
    rows = latest_per_cell(load())
    print(f"# Loaded {len(rows)} unique (contract, model, temp) cells\n")

    # ---------- Step 2.1: peak Delta_rescue ----------
    print("=" * 72)
    print("Step 2.1 — Peak Delta_rescue across all configurations")
    print("=" * 72)
    peak = max(rows, key=lambda r: r["Delta_rescue"] or -1)
    print(f"  Contract:    {peak['contract_id']}")
    print(f"  Model:       {peak['model']}")
    print(f"  Temperature: {peak['decoding_temperature']}")
    print(f"  R_raw:       {peak['R_raw']:.3f}")
    print(f"  R_anchor_pre:  {peak['R_anchor_pre']:.3f}")
    print(f"  R_anchor_post: {peak['R_anchor_post']:.3f}")
    print(f"  Delta_rescue: {peak['Delta_rescue']:+.3f}")
    print(f"  Runs:        {peak['runs']}\n")

    # ---------- Step 2.2: binary_search, gpt-4o-mini, T=0.5 ----------
    print("=" * 72)
    print("Step 2.2 — Binary Search + GPT-4o-mini + T=0.5")
    print("=" * 72)
    cell = filt(rows, "binary_search", "gpt-4o-mini", 0.5)
    if cell:
        r = cell[0]
        print(f"  R_raw:        {r['R_raw']:.3f}")
        print(f"  R_anchor_pre: {r['R_anchor_pre']:.3f}")
        print(f"  R_anchor_post:{r['R_anchor_post']:.3f}")
        print(f"  Delta_rescue: {r['Delta_rescue']:+.3f}")
        print(f"  Runs:         {r['runs']}")
    else:
        print("  NOT FOUND")
    print()

    # ---------- Step 2.3: balanced_brackets, gpt-4o-mini, T=0.7 ----------
    print("=" * 72)
    print("Step 2.3 — Balanced Brackets + GPT-4o-mini + T=0.7")
    print("=" * 72)
    cell = filt(rows, "balanced_brackets", "gpt-4o-mini", 0.7)
    if cell:
        r = cell[0]
        print(f"  R_raw:        {r['R_raw']:.3f}")
        print(f"  R_anchor_pre: {r['R_anchor_pre']:.3f}")
        print(f"  R_anchor_post:{r['R_anchor_post']:.3f}")
        print(f"  Delta_rescue: {r['Delta_rescue']:+.3f}")
        print(f"  Runs:         {r['runs']}")
    else:
        print("  NOT FOUND")
    print()

    # ---------- Step 2.4: cross-model summary, pooled across temperatures ----------
    print("=" * 72)
    print("Step 2.4 — Cross-model summary (pooled across 5 temperatures)")
    print("=" * 72)
    print(f"{'Task':<20} {'Model':<22} {'R_raw':>7} {'R_pre':>7} {'R_post':>7} {'Delta':>7} {'N':>4}")
    print("-" * 78)
    summary = []
    for task in PAPER_TASKS:
        for model in PAPER_MODELS:
            cells = filt(rows, task, model)
            if not cells:
                summary.append((task, model, None, None, None, None, 0))
                print(f"{TASK_DISPLAY[task]:<20} {MODEL_DISPLAY[model]:<22} {'NA':>7} {'NA':>7} {'NA':>7} {'NA':>7} {0:>4}")
                continue
            n = sum(c["runs"] for c in cells)
            weights = [c["runs"] for c in cells]
            r_raw  = weighted_mean([c["R_raw"]         for c in cells], weights)
            r_pre  = weighted_mean([c["R_anchor_pre"]  for c in cells], weights)
            r_post = weighted_mean([c["R_anchor_post"] for c in cells], weights)
            delta  = weighted_mean([c["Delta_rescue"]  for c in cells], weights)
            summary.append((task, model, r_raw, r_pre, r_post, delta, n))
            print(f"{TASK_DISPLAY[task]:<20} {MODEL_DISPLAY[model]:<22} {r_raw:>7.3f} {r_pre:>7.3f} {r_post:>7.3f} {delta:>+7.3f} {n:>4}")
    print()

    # ---------- Step 2.5: strict vs standard contracts ----------
    print("=" * 72)
    print("Step 2.5 — Strict (MISRA-C/Power-of-10) vs Standard contracts")
    print("=" * 72)
    pairs = [
        ("binary_search", "binary_search_strict"),
        ("is_prime",      "is_prime_strict"),
        ("lru_cache",     "lru_cache_strict"),
    ]
    print(f"{'Pair':<28} {'std R_pre':>10} {'strict R_pre':>13} {'abs gain':>10} {'rel %':>8}")
    print("-" * 72)
    std_means, strict_means, rel_pct = [], [], []
    for std, strict in pairs:
        std_cells    = filt(rows, std)
        strict_cells = filt(rows, strict)
        if not std_cells or not strict_cells:
            print(f"{std} -> {strict}: missing")
            continue
        std_w = [c["runs"] for c in std_cells]
        str_w = [c["runs"] for c in strict_cells]
        std_pre    = weighted_mean([c["R_anchor_pre"] for c in std_cells],    std_w)
        strict_pre = weighted_mean([c["R_anchor_pre"] for c in strict_cells], str_w)
        gain = strict_pre - std_pre
        rel  = (gain / std_pre * 100.0) if std_pre and std_pre > 0 else float("inf")
        std_means.append(std_pre)
        strict_means.append(strict_pre)
        rel_pct.append(rel)
        rel_str = f"{rel:>7.1f}%" if rel != float("inf") else "  inf"
        print(f"{std:<14} -> {strict:<14} {std_pre:>10.3f} {strict_pre:>13.3f} {gain:>+10.3f} {rel_str:>8}")
    if std_means:
        print()
        print(f"  Mean R_pre standard: {mean(std_means):.3f}")
        print(f"  Mean R_pre strict:   {mean(strict_means):.3f}")
        agg_abs = mean(strict_means) - mean(std_means)
        agg_rel = agg_abs / mean(std_means) * 100.0 if mean(std_means) > 0 else float("inf")
        print(f"  Aggregate absolute gain: {agg_abs:+.3f} pp")
        print(f"  Aggregate relative gain: {agg_rel:+.1f}%")
    print()

    # ---------- Bonus: any configuration with a more impactful number? ----------
    print("=" * 72)
    print("BONUS — Top 5 Delta_rescue, plus zero-rescue Claude rows for context")
    print("=" * 72)
    top5 = sorted(rows, key=lambda r: r["Delta_rescue"] or -1, reverse=True)[:5]
    for r in top5:
        print(f"  {r['contract_id']:<22} {r['model']:<25} T={r['decoding_temperature']:<3} "
              f"R_raw={r['R_raw']:.2f} R_pre={r['R_anchor_pre']:.2f} "
              f"R_post={r['R_anchor_post']:.2f} Delta={r['Delta_rescue']:+.3f}")


if __name__ == "__main__":
    main()
