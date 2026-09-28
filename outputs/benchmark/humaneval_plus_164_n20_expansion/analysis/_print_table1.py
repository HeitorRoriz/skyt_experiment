import json
from pathlib import Path

base = Path("outputs/benchmark/humaneval_plus_164_n20_expansion")
for name in ["frozen_rescore", "haiku45_score", "luna_score", "sonnet5_score"]:
    p = base / name / "benchmark_report.json"
    r = json.loads(p.read_text(encoding="utf-8"))
    for s in r["slices"]:
        print(
            s["model"],
            s["temperature"],
            "plus",
            round(s["plus_pass_pct"], 1),
            "same2",
            round(s["same_at_2_pct"], 1),
            "same2c",
            round(s["same_at_2_given_cert_pct"], 1),
            "drop",
            s["n_dropped_same_at_2_given_cert"],
        )

pools = json.loads((base / "analysis" / "table1_pools.json").read_text(encoding="utf-8"))
for p in pools["t3"]:
    pa = p["plus_pass_diff"]["estimate"]
    ca = p["same_at_2_given_cert_diff"]["estimate"]
    print(
        "T3",
        p["temperature"],
        p["model_a"].split("-")[0:3],
        "vs",
        p["model_b"].split("-")[0:3],
        "plus",
        None if pa is None else round(100 * pa, 1),
        "cert",
        None if ca is None else round(100 * ca, 1),
        "rev",
        p["rank_reversal"],
    )
