import json
from pathlib import Path
from math import sqrt

rows = json.loads(
    Path("outputs/benchmark/humaneval_plus_164_n20_skyt_heldout_oracle_split/oracle_split_config_rows.json").read_text(encoding="utf-8")
)
xs, ys = [], []
for row in rows:
    if row.get("pre_plus_same_at_2") is None or row.get("delta_plus_same_at_2") is None:
        continue
    xs.append(float(row["pre_plus_same_at_2"]))
    ys.append(float(row["delta_plus_same_at_2"]))

def spearman(a, b):
    ra = {v: i for i, v in enumerate(sorted(range(len(a)), key=lambda i: a[i]))}
    rb = {v: i for i, v in enumerate(sorted(range(len(b)), key=lambda i: b[i]))}
    n = len(a)
    d2 = sum((ra[i] - rb[i]) ** 2 for i in range(n))
    return 1 - 6 * d2 / (n * (n * n - 1))

print("n", len(xs), "spearman", round(spearman(xs, ys), 3))
