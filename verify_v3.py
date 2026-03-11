import math
import pandas as pd

def wilson(p, n, z=1.96):
    d = 1 + z**2/n
    c = p + z**2/(2*n)
    m = z * math.sqrt(p*(1-p)/n + z**2/(4*n**2))
    return round((c-m)/d, 2), round((c+m)/d, 2)

# Verify Wilson CIs from the paper table
cases = [
    ("BS/4omini R_raw",   .39, 100, (.30, .49)),
    ("BS/4omini R_pre",   .10, 100, (.06, .17)),
    ("BS/4omini R_post",  .40, 100, (.31, .50)),
    ("BB/4omini R_raw",   .30, 100, (.22, .40)),
    ("BB/4omini R_pre",   .36, 100, (.27, .46)),
    ("BB/4omini R_post",  .82, 100, (.73, .88)),
    ("SL/4omini R_raw",   .56, 100, (.46, .65)),
    ("SL/4o R_raw",       .32, 100, (.24, .42)),
    ("BS/Claude R_raw",   .82, 100, (.73, .88)),
    ("SL/Claude R_raw",   .65, 100, (.55, .74)),
    ("BS/4o R_raw",       .61, 100, (.51, .70)),
    ("BS/4o R_pre",       .34, 100, (.25, .44)),
    ("BS/4o R_post",      .51, 100, (.41, .61)),
    ("BB/4o R_raw",       .27, 100, (.19, .36)),
    ("SL/4o R_pre",       .02, 100, (.01, .07)),
    ("SL/4o R_post",      .09, 100, (.05, .16)),
    ("SL/4omini R_pre",   .54, 100, (.44, .63)),
    ("SL/4omini R_post",  .76, 100, (.67, .83)),
    # Zero proportions
    ("BS/Claude R_pre",   .00, 100, (.00, .04)),
    ("BB/4o R_pre",       .00, 100, (.00, .04)),
    ("BB/Claude R_pre",   .00, 100, (.00, .04)),
    ("SL/Claude R_pre",   .00, 100, (.00, .04)),
]

print("=== Wilson CI Verification ===")
all_ok = True
for name, p, n, expected in cases:
    got = wilson(p, n)
    ok = got == expected
    if not ok:
        all_ok = False
    status = "OK" if ok else "MISMATCH"
    print(f"  {status}: {name}: p={p} N={n} -> computed={got} paper={expected}")

print()
if all_ok:
    print("ALL Wilson CIs match the paper.")
else:
    print("SOME Wilson CIs DO NOT match the paper.")

# Verify strict variant max Delta_rescue
print()
print("=== Strict variant max Delta_rescue ===")
df = pd.read_csv("outputs/metrics_summary.csv")
df = df[df["runs"] == 20]
strict = df[df["contract_id"].str.contains("strict")]
max_row = strict.loc[strict["Delta_rescue"].idxmax()]
print(f"  Max Delta_rescue = {max_row['Delta_rescue']} ({max_row['contract_id']}, {max_row['model']}, T={max_row['decoding_temperature']})")

# Verify base task max Delta_rescue
base = df[~df["contract_id"].str.contains("strict")]
max_base = base.loc[base["Delta_rescue"].idxmax()]
print(f"  Max base Delta_rescue = {max_base['Delta_rescue']} ({max_base['contract_id']}, {max_base['model']}, T={max_base['decoding_temperature']})")

# Check model name in paper vs CSV
print()
print("=== Model names in CSV ===")
print(f"  {df['model'].unique()}")
print("  Paper says: GPT-4o-mini, GPT-4o, Claude Sonnet 4.5")
print(f"  CSV Claude model: claude-sonnet-4-5-20250929 (paper should say 4.5, not 4)")
