# Step 4 — discriminant suite

Date: 2026-09-14. Phase 4 of [`BENCHMARK_PLAN.md`](BENCHMARK_PLAN.md).

This is a **comparison**, not a new `same()`. The tape stays canonical-form
fingerprint. On plus-certified pairs from one config, several older judges
cast a bit; we count where they disagree with the tape.

```
python -m benchmark discriminant \
    --source-dir outputs/humaneval_plus/pilot \
    --out-dir outputs/benchmark/discriminant
```

No API. Refuses writes into `outputs/gate0/` and `outputs/humaneval_plus/pilot/`.
Refuses SKYT-repaired jsonl (same as `score`).

Tests:

```
python -m pytest tests/test_benchmark_discriminant.py
```

## Judges (pinned)

| JSON key | Meaning |
| --- | --- |
| `string_eq` | Exact source. |
| `parse_unparse_eq` | `ast.unparse(ast.parse)` — Type-1-ish. |
| `raw_ast_eq` | MD5 of `ast.dump` with **no** canonicalize. |
| `type2_eq` | α-rename bound names, **keep** docstrings. |
| `ted_zero` | Zhang–Shasha distance 0 on labeled Python ASTs. GumTree-*style* labels, not the Java GumTree matcher. |
| `type3_near` | TED / max(tree size) < **0.30**. Documented, not fitted to headlines. |
| `fingerprint_eq` | Benchmark `same()`. |

`type3_ted_ratio` is `0.30`. Changing it increments `judge_version`. Do not
tune it so the off-diagonals disappear.

## Output

`discriminant_report.json`:

- `vs_fingerprint[judge]`: `both_same`, `both_different`,
  `tape_same_judge_different`, `tape_different_judge_same`, counts.
- `sample`: up to 20 pairs per off-diagonal cell, seed `20260723`, with source
  for the appendix.

Wanted pattern, if the spec is right: string ⊂ parse/unparse ⊂ type-2 ⊂
fingerprint on the *ignore* side, and Type-3 coarser than the tape on
control-flow near-misses.

Human labels are still Phase 5.

## Census on the stored HumanEval+ pilot (2026-09-14)

No API. 4,279 plus-certified pairs. Report:
`outputs/benchmark/discriminant/discriminant_report.json`.

| Judge | both same | both different | tape same, judge different | tape different, judge same |
| --- | ---: | ---: | ---: | ---: |
| exact string | 2853 | 921 | 505 | 0 |
| parse-unparse / raw AST / TED=0 | 3036 | 921 | 322 | 0 |
| Type-2 (α-rename, keep docs) | 3283 | 921 | 75 | 0 |
| Type-3 (`TED/size < 0.30`) | 3358 | 406 | 0 | 515 |

Wanted pattern, and it is what we got:

- On the *ignore* side, string ⊂ parse-unparse ⊂ Type-2 ⊂ fingerprint. A
  stricter judge never called two programs the same when the tape called
  them different (`tape_different_judge_same` = 0 except Type-3).
- The 75 Type-2 disagreements are docstring/prose (sampled 20/20
  `docstring_or_prose`). That is the settled “docs are not form” call.
- Type-3 is coarser: 515 pairs the tape splits and a 30% TED ratio still
  calls near-clones. Sampled 20/20 `type3_near_miss`. That is the
  for-vs-while style gap, not a bug in `same()`.
- parse-unparse, raw AST hash, and TED=0 coincide on this data (same 322
  off-diagonal). They are not independent baselines here.

Do not retune 0.30 so the 515 disappear. They are the discriminant.

