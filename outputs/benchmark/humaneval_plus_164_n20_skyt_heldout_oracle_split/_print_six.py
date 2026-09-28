import json
from pathlib import Path

post = json.loads(
    Path("outputs/benchmark/humaneval_plus_164_n20_skyt_heldout_oracle_split/oracle_split_posthoc.json").read_text(encoding="utf-8")
)
cache = json.loads(
    Path("outputs/benchmark/humaneval_plus_164_n20_skyt_heldout_oracle_split/oracle_fair_cache.json").read_text(encoding="utf-8")
)

all_row = post["slices"][0]
print("PLUS |cert common", all_row["n_plus_common_support"])
print("same@2|cert", all_row["plus_same_at_2_given_cert_pre_common"]["pct"], "->", all_row["plus_same_at_2_given_cert_post_common"]["pct"], "d", all_row["delta_plus_same_at_2_given_cert_common"]["pct"], all_row["delta_plus_same_at_2_given_cert_common"]["ci95_pct"])
print("disag", all_row["plus_disagreement_pre_common"]["pct"], all_row["plus_disagreement_pre_common"]["ci95_pct"], "->", all_row["plus_disagreement_post_common"]["pct"], all_row["plus_disagreement_post_common"]["ci95_pct"], "d", all_row["delta_plus_disagreement_common"]["pct"], all_row["delta_plus_disagreement_common"]["ci95_pct"], "rel", all_row["plus_disagreement_relative_reduction_common_pct"])
print("extra", all_row["extra_survival_pre"]["pct"], all_row["extra_survival_pre"]["ci95_pct"], "->", all_row["extra_survival_post"]["pct"], all_row["extra_survival_post"]["ci95_pct"], "d", all_row["delta_extra_survival"]["pct"], all_row["delta_extra_survival"]["ci95_pct"])
print("interaction", post["temperature_interaction_plus_same_at_2"]["pooled_models"])
print("per model")
for k, v in post["temperature_interaction_plus_same_at_2"]["per_model"].items():
    print(" ", k, v["pct"], v["ci95_pct"])

print("\ncells disag")
for row in post["slices"][1:]:
    print(row["label"], row["plus_disagreement_pre_common"]["pct"], "->", row["plus_disagreement_post_common"]["pct"], "rel", row.get("plus_disagreement_relative_reduction_common_pct"), "n", row["n_plus_common_support"])

print("\nCACHE all")
c = cache["slices"][0]
for name in ("raw", "first_base_cache", "consensus_base_cache", "skyt"):
    cell = c[name]
    print(name)
    for k in ("plus_same_at_2", "plus_pass", "base_pass", "extra_survival", "coverage", "base_pass_extra_fail"):
        item = cell.get(k) or {}
        print(" ", k, item.get("pct"), item.get("ci95_pct"))
print("skyt-first", c["skyt_minus_first_cache_plus_same_at_2"]["pct"], c["skyt_minus_first_cache_plus_same_at_2"]["ci95_pct"])
print("skyt-cons", c["skyt_minus_consensus_cache_plus_same_at_2"]["pct"], c["skyt_minus_consensus_cache_plus_same_at_2"]["ci95_pct"])
