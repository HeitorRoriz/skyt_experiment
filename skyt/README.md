# SKYT (the tool)

This directory is the **tool**: pick a Certified Consensus form, repair toward
it, score pre/post. The frozen pipeline modules remain in `src/` and `agents/`
so the Option C runtime is not rewritten in this cut.

| Path | Role |
| --- | --- |
| `src/`, `agents/` | Frozen SKYT runtime (canon, transformer, contracts) |
| `skyt/humaneval_repair.py` | HumanEval+ Certified Consensus replay (no API) |
| `skyt/table2.py` | Table 2 builder on repaired summaries |
| `benchmark/` | Measuring tape: fingerprint `same()`, `same@2` |

Do not overwrite `outputs/gate0/` or `outputs/humaneval_plus/pilot/`.
