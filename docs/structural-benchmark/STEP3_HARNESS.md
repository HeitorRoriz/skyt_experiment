# Step 3 — overlay harness (one command)

**Cut 2026-09-14.** The measuring tape is `python -m benchmark`. That scorer
uses **canonical-form fingerprint only**: no Certified Consensus, no CV, no
match-to-human. SKYT repair/Table 2 live under `skyt/`. Frozen runtime remains
`src/` + `agents/`.

```
python -m benchmark pins
python -m benchmark estimate --n-tasks 30 --n 10
python -m benchmark score \
    --source-dir outputs/humaneval_plus/pilot \
    --out-dir outputs/benchmark/pilot_v2
python -m benchmark discriminant \
    --source-dir outputs/humaneval_plus/pilot \
    --out-dir outputs/benchmark/discriminant
python -m benchmark run \
    --task-id HumanEval/23 --model gpt-4o-mini --temperature 0.0 --n 10 \
    --out-dir outputs/benchmark/dryrun \
    --allow-api
python -m benchmark full
python -m benchmark full --from-dir outputs/humaneval_plus/pilot
python -m benchmark full --allow-api --from-dir outputs/humaneval_plus/pilot
```

`run` may use any of the 164 HumanEval+ ids and does **not** write SKYT
summaries (`analyze=False`). The historical HumanEval+ CLI still defaults to
the 30-task pilot lock. Never write into `outputs/humaneval_plus/pilot/` or
`outputs/gate0/`.

Reports are **one slice per model × temperature**, not one mixed headline.

---

## What the command reports

Both numbers, always, with every denominator:

| JSON key | Public name | Meaning |
| --- | --- | --- |
| `same_at_2` | `same@2` | Two independent draws both certify **and** are the same program. Failures stay in the denominator. |
| `same_at_2_given_cert` | `same@2\|cert` | Same program, given that both draws certify. **Undefined** when a config has fewer than two certified draws; those configs are dropped and `n_dropped_same_at_2_given_cert` is reported. |
| `plus_pass` | pass rate | Share of the *N* draws that certify (HumanEval+ plus tests). |

`relation_version` is `2` (canonical-form fingerprint from Step 1). SPEC OPEN 1
(the public names) is still open. OPEN 3 is **settled**: protocol *N*=20,
CV 10/10. `full` locks *N* to 20 and refuses mixed or smaller *N*. It does
**not** rewrite the HumanEval+ 30-task pilot (*N*=10, labeled `pilot_grid`).
`--n` is required on `run` and `estimate`.

Intervals are a task-clustered bootstrap (seed `20260723`), not a binomial
interval over pairs. Schema `structural-repeatability-benchmark-v2` stamps an
`inference` block and `pilot_grid`. Details:
[`STEP5_INFERENCE.md`](STEP5_INFERENCE.md).

Tests (no API):

```
python -m pytest tests/test_structural_repeatability.py tests/test_structural_validity.py tests/test_benchmark_inference.py tests/test_humaneval_plus_adapter.py
```

---

## Pins that refuse

- HumanEval+ dataset MD5 `916d9bfe7b490c2447245ec91595fa4f` (already enforced
  by `benchmarks.humaneval_plus.dataset.load_evalplus_problems`).
- Sandbox image digest from `experiment_manifest.json`. `run` refuses to spend
  until both the dataset hash and the local image digest verify.
- `score`, `run`, and `full` refuse `--out-dir` under `outputs/gate0/` or
  `outputs/humaneval_plus/pilot/`. Reading the pilot for a v2 rescore is fine;
  writing back into it is not.
- `score` refuses jsonl that already has `repair_applied` or a style contract.

Paid generation still requires `--allow-api`. The cost sketch is printed first
(list price as of 2026-09-01, not an invoice).

---

## What this step does not do

- No Certified Consensus picker in the overlay path.
- No SKYT repair.
- No paid 164-task generation until `--allow-api`. The runner exists:
  `python -m benchmark full` writes `outputs/benchmark/humaneval_plus_164_n20`
  (164 × 2 models × 2 temperatures × *N*=20). Frozen trees stay read-only.
- No stamp of `relation_version` onto the frozen generation-record schema in
  `src/` (SPEC OPEN 4). Overlay reports carry the version; existing jsonl does
  not change.
- FSE Table 1/2 still quote pre-fix 56.9% / 67.4%. Scoring the stored pilot
  with this command recomputes under relation v2; that must not silently
  replace the published tables.
