# Step 3 — overlay harness (one command)

Date: 2026-09-14. Phase 2 of [`BENCHMARK_PLAN.md`](BENCHMARK_PLAN.md).

This step packages the measuring tape. It does **not** pick a canon and it
does **not** run SKYT repair. Historical trees stay frozen.

```
python -m benchmarks.structural_repeatability pins
python -m benchmarks.structural_repeatability estimate --n-tasks 30 --n 10
python -m benchmarks.structural_repeatability score \
    --source-dir outputs/humaneval_plus/pilot \
    --out-dir outputs/structural_repeatability/pilot_v2
python -m benchmarks.structural_repeatability run \
    --task-id HumanEval/23 --model gpt-4o-mini --temperature 0.0 --n 10 \
    --out-dir outputs/structural_repeatability/dryrun \
    --allow-api
```

Tests (no API):

```
python -m pytest tests/test_structural_repeatability.py
```

---

## What the command reports

Both numbers, always, with every denominator:

| JSON key | Public name | Meaning |
| --- | --- | --- |
| `same_at_2` | `same@2` | Two independent draws both certify **and** are the same program. Failures stay in the denominator. |
| `same_at_2_given_cert` | `same@2\|cert` | Same program, given that both draws certify. **Undefined** when a config has fewer than two certified draws; those configs are dropped and `n_dropped_same_at_2_given_cert` is reported. |
| `plus_pass` | pass rate | Share of the *N* draws that certify (HumanEval+ plus tests). |

`relation_version` is `2` (canonical-form fingerprint from Step 1). SPEC OPEN 1
(the public names) and OPEN 3 (a single *N*) are still open; this harness does
not silently switch the HumanEval+ pilot from N=10 to N=20. `--n` is required
on `run` and `estimate`.

Intervals are a task-clustered bootstrap (seed `20260723`), not a binomial
interval over pairs.

---

## Pins that refuse

- HumanEval+ dataset MD5 `916d9bfe7b490c2447245ec91595fa4f` (already enforced
  by `benchmarks.humaneval_plus.dataset.load_evalplus_problems`).
- Sandbox image digest from `experiment_manifest.json`. `run` refuses to spend
  until both the dataset hash and the local image digest verify.
- `score` and `run` refuse `--out-dir` under `outputs/gate0/` or
  `outputs/humaneval_plus/pilot/`. Reading the pilot for a v2 rescore is fine;
  writing back into it is not.
- `score` refuses jsonl that already has `repair_applied` or a style contract.

Paid generation still requires `--allow-api`. The cost sketch is printed first
(list price as of 2026-09-01, not an invoice).

---

## What this step does not do

- No Certified Consensus picker in the overlay path.
- No SKYT repair.
- No full 164-task run (Phase 3).
- No stamp of `relation_version` onto the frozen generation-record schema in
  `src/` (SPEC OPEN 4). Overlay reports carry the version; existing jsonl does
  not change.
- FSE Table 1/2 still quote pre-fix 56.9% / 67.4%. Scoring the stored pilot
  with this command recomputes under relation v2; that must not silently
  replace the published tables.
