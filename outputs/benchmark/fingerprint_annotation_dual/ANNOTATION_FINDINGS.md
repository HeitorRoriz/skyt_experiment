# Fingerprint annotation — both sheets

Coordinator note. Not for annotators.

The 2026-09-27 draft of `paper/fse2027/main.tex` now reports the sample
metrics in RQ2. Prevalence-reweighted sensitivity/specificity, the κ
interval, and the implementation-level rates are in `validity_stats.json`
(seed 20260723, 10,000 resamples) and are marked post hoc in the draft.
Task-mean certified structural disagreement on the four annotated cells is
23.4% (20.0–27.0). Implementation-level disagreement is 17.0% (12.2–22.0)
for A and 4.7% (1.3–8.7) for B. Stratified κ interval is 0.25–0.56.
Reweighted sensitivity is 91.5% (A) and 82.8% (B).

The figures below are the unweighted sample. They are unchanged.

Date: 2026-09-27. Both sheets are scored. Machine-readable result: `score.json`.

Annotator A is the first rater. Annotator B is an embedded software engineer. They labeled independently, on blind sheets, and did not discuss cases.

## What this study is

The question on every pair:

> Would these two programs be treated as the same implementation for code review, verification, maintenance, or change-control purposes?

`1` means same implementation. `0` means different.

The gold label is `fingerprint_same`: identical canonical-form fingerprints (`benchmark.relation.fingerprint`, flexible naming). That fingerprint is the SameEval ruler. SameEval uses it to measure whether two regenerations are the same program. SKYT is a separate policy: it picks the most reproduced verified form and repairs other generations toward that form. SameEval then measures the result. This sample does not contain repaired programs. It is 128 raw overlay pairs, a nested prefix of the 240-pair sample (4 model × temperature cells × 4 strata × 8). The set is stratified, 64 fingerprint-same and 64 fingerprint-different by construction, so precision and F1 are sample metrics. Sensitivity, specificity, raw agreement, and Cohen's κ are the numbers to quote.

## How the sheets were processed

Annotator B was processed on 2026-09-26 from `Annotation_solved.csv` (see the note in `ANNOTATOR_B.md`). Labels `YES`/`NO`, 128/128, no notes. Copied onto `annotator_b/annotation_sheet.csv`.

Annotator A arrived 2026-09-27 as `annotator_a/annotation_sheet.csv`.

1. Columns: `order`, `pair_id`, `human_same`, `notes`. 128 rows, labels only `1` (81) and `0` (47), notes empty, no duplicate orders.
2. Excel had rewritten two pair ids that look like numbers:
   - order 3: `02628509120090e4` came back as `2.63E+16`, label `1`
   - order 55: `3603855321645717` came back as `3.60E+15`, label `1`
3. Those two ids were restored from `order` against `gold.json`. The untouched return is kept at `annotator_a/annotation_sheet_as_returned.csv`. The sheet that was scored is `annotator_a/annotation_sheet.csv`.
4. After the repair, all 128 pair ids match gold on both sheets. `gold.json`, the program folders, and the zip packs were not modified.
5. Scored with `skyt.annotation_score.score` as annotators `A` and `B`. Wrote `score.json`.

The scorer treats the fingerprint as the prediction and the human label as the reference.

| Cell | Meaning |
|---|---|
| TP | Fingerprint same, human same |
| FP | Fingerprint same, human different |
| TN | Fingerprint different, human different |
| FN | Fingerprint different, human same |

`majority_agree` keeps only pairs where A and B gave the same label. The 32 disagreements are left out. There is no third vote.

## Headline

| | A | B | Pairs they agree on |
|---|---:|---:|---:|
| Said same | 81 / 128 | 101 / 128 | 75 same, 21 different |
| Agreement with the fingerprint | 109 / 128 (85.2%) | 91 / 128 (71.1%) | 84 / 96 (87.5%) |
| Sensitivity | 63 / 81 (77.8%) | 64 / 101 (63.4%) | 63 / 75 (84.0%) |
| Specificity | 46 / 47 (97.9%) | 27 / 27 (100%) | 21 / 21 (100%) |
| Precision | 63 / 64 (98.4%) | 64 / 64 (100%) | 63 / 63 (100%) |

Human–human: raw agreement 96 / 128 = 75%. Cohen's κ = 0.41.

Confusion, fingerprint by row, human by column:

|  | A same | A different | B same | B different |
|---|---:|---:|---:|---:|
| Fingerprint same | 63 | 1 | 64 | 0 |
| Fingerprint different | 18 | 46 | 37 | 27 |

On the 96 pairs where the humans agree:

|  | Both said same | Both said different |
|---|---:|---:|
| Fingerprint same | 63 | 0 |
| Fingerprint different | 12 | 21 |

The single "fingerprint same, A different" pair is order 29, `HumanEval/38`. The two files are byte-identical. B marked them same. No pair exists where the fingerprint says same and both humans say different.

## Where the humans agree with each other

| Stratum | They agree | Of those, both said same | Fingerprint agreement on that consensus |
|---|---:|---:|---:|
| Fingerprint same, both certified | 32 / 32 | 32 | 32 / 32 |
| Fingerprint same, not both certified | 31 / 32 | 31 | 31 / 31 |
| Fingerprint different, both certified | 14 / 32 | 10 | 4 / 14 |
| Fingerprint different, not both certified | 19 / 32 | 2 | 17 / 19 |

They agree with each other on fingerprint-same pairs (63/64). On fingerprint-different pairs they agree on 33/64. Almost all of the shared "this is still the same implementation" calls (10 of 12) are pairs where both programs passed the tests.

Of the 32 human disagreements, 26 are A different and B same, and 6 are A same and B different. 18 of the 32 sit in "fingerprint different, both certified."

## By model, annotator A against the fingerprint

Each cell is 32 pairs. B's cell numbers are unchanged from `ANNOTATOR_B.md`.

| Cell | A agreement | A said same | Human–human agreement |
|---|---:|---:|---:|
| Claude Sonnet 4.5, T=0.0 | 26 / 32 (81.3%) | 20 / 32 | 21 / 32 |
| Claude Sonnet 4.5, T=0.7 | 28 / 32 (87.5%) | 20 / 32 | 22 / 32 |
| gpt-4o-mini, T=0.0 | 26 / 32 (81.3%) | 22 / 32 | 28 / 32 |
| gpt-4o-mini, T=0.7 | 29 / 32 (90.6%) | 19 / 32 | 25 / 32 |

A's only fingerprint-same rejection is in the Claude T=0.0 cell (order 29).

## Two opened pairs

- **Order 29** (`HumanEval/38`, fingerprint same, not both certified). A said different, B said same. `A.py` and `B.py` are the same 473 bytes.
- **Order 14** (`HumanEval/158`, fingerprint different, both certified). Both humans said same. The programs differ by the order of two assignments, `max_unique_count = unique_count` and `max_word = word`.

## The 12 pairs both called same while the fingerprint says different

| Order | Task | Model | T | Both certified |
|---:|---|---|---:|---|
| 6 | HumanEval/113 | Claude | 0.0 | no |
| 14 | HumanEval/158 | gpt-4o-mini | 0.0 | yes |
| 25 | HumanEval/113 | Claude | 0.0 | no |
| 28 | HumanEval/68 | gpt-4o-mini | 0.0 | yes |
| 45 | HumanEval/92 | gpt-4o-mini | 0.7 | yes |
| 55 | HumanEval/6 | gpt-4o-mini | 0.0 | yes |
| 56 | HumanEval/6 | gpt-4o-mini | 0.0 | yes |
| 64 | HumanEval/3 | gpt-4o-mini | 0.0 | yes |
| 70 | HumanEval/125 | Claude | 0.7 | yes |
| 74 | HumanEval/73 | Claude | 0.7 | yes |
| 80 | HumanEval/133 | Claude | 0.0 | yes |
| 121 | HumanEval/130 | gpt-4o-mini | 0.7 | yes |

## The 32 pairs the humans did not agree on

| Order | Task | Stratum | Fingerprint | A | B |
|---:|---|---|---:|---:|---:|
| 2 | HumanEval/89 | fp different, both certified | 0 | 0 | 1 |
| 4 | HumanEval/86 | fp different, both certified | 0 | 0 | 1 |
| 7 | HumanEval/100 | fp different, not both certified | 0 | 1 | 0 |
| 10 | HumanEval/113 | fp different, not both certified | 0 | 0 | 1 |
| 19 | HumanEval/65 | fp different, both certified | 0 | 0 | 1 |
| 20 | HumanEval/105 | fp different, not both certified | 0 | 0 | 1 |
| 24 | HumanEval/96 | fp different, both certified | 0 | 0 | 1 |
| 26 | HumanEval/149 | fp different, both certified | 0 | 0 | 1 |
| 27 | HumanEval/113 | fp different, not both certified | 0 | 0 | 1 |
| 29 | HumanEval/38 | fp same, not both certified | 1 | 0 | 1 |
| 30 | HumanEval/39 | fp different, not both certified | 0 | 0 | 1 |
| 31 | HumanEval/69 | fp different, both certified | 0 | 0 | 1 |
| 32 | HumanEval/32 | fp different, not both certified | 0 | 1 | 0 |
| 37 | HumanEval/5 | fp different, both certified | 0 | 0 | 1 |
| 39 | HumanEval/129 | fp different, not both certified | 0 | 0 | 1 |
| 41 | HumanEval/109 | fp different, both certified | 0 | 0 | 1 |
| 49 | HumanEval/90 | fp different, both certified | 0 | 0 | 1 |
| 51 | HumanEval/139 | fp different, both certified | 0 | 0 | 1 |
| 54 | HumanEval/145 | fp different, not both certified | 0 | 0 | 1 |
| 58 | HumanEval/151 | fp different, not both certified | 0 | 1 | 0 |
| 60 | HumanEval/8 | fp different, not both certified | 0 | 1 | 0 |
| 61 | HumanEval/24 | fp different, both certified | 0 | 1 | 0 |
| 63 | HumanEval/105 | fp different, not both certified | 0 | 0 | 1 |
| 65 | HumanEval/123 | fp different, both certified | 0 | 0 | 1 |
| 67 | HumanEval/158 | fp different, both certified | 0 | 0 | 1 |
| 79 | HumanEval/64 | fp different, both certified | 0 | 0 | 1 |
| 81 | HumanEval/124 | fp different, not both certified | 0 | 0 | 1 |
| 84 | HumanEval/128 | fp different, both certified | 0 | 0 | 1 |
| 85 | HumanEval/106 | fp different, both certified | 0 | 0 | 1 |
| 99 | HumanEval/94 | fp different, both certified | 0 | 0 | 1 |
| 100 | HumanEval/104 | fp different, both certified | 0 | 0 | 1 |
| 104 | HumanEval/132 | fp different, not both certified | 0 | 1 | 0 |

## What this says about SameEval

SameEval's claim is narrow: two regenerations are the same program when their canonical fingerprints match. On this sample, that positive call matches both labelers. Across 64 fingerprint-same pairs, the humans jointly said same on 63, and the remaining pair is identical source that A marked different.

The negative call is stricter than either person, and the two people do not share one line for it. A treats 46 of 64 fingerprint-different pairs as different implementations (agreement with the fingerprint 85%). B treats 27 of 64 that way (agreement 71%). They only agree with each other on 33 of those 64. The shared exceptions, 12 pairs both still call the same implementation, are mostly two passing programs whose trees differ by a small rearrangement (order 14 swaps two assignments).

So SameEval is a conservative detector of "same form." It is a partial detector of "same implementation" in the sense the instructions gave the labelers. The gap is widest when both programs pass. That matches the paper's existing boundary: fingerprint identity is the operational definition of same form, and it is not observational equivalence or algorithm identity. Human data now supports the positive side of that boundary and shows the negative side is where labelers diverge.

## What this says about SKYT

SKYT does not define sameness. It chooses the most reproduced verified form and repairs other generations toward it. SameEval is how that repair is scored.

This labeling cannot say whether those repairs are good or bad. Repaired programs were not in the pack.

What it says about the ruler SKYT is graded with:

- A SameEval "same" that both humans accept is the ceiling SKYT is aiming at. The study gives no example of both humans rejecting a fingerprint merge.
- A SameEval "different" sometimes means an edit a reviewer would ignore, especially between two programs that already pass. Some of the scatter SameEval reports, and some of the distance SKYT closes, sits below the line the embedded engineer used for "a different implementation." A draws that line closer to the fingerprint than B does.
- Because the two humans only moderately agree (κ 0.41), there is not yet one human standard a repair policy could be said to have matched.

## Not done

- No third annotator, so the 32 disagreements stay unresolved.
- The 12 consensus exceptions were not all inspected. Only orders 14 and 29 were opened for this note.
- No paper text was updated.
