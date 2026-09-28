# Annotator B — processing and findings

Coordinator note. Not for annotators.

Superseded for current numbers by [`ANNOTATION_FINDINGS.md`](ANNOTATION_FINDINGS.md) (2026-09-27), which scores both sheets. The figures below are the annotator-B-only pass and are unchanged.

Date: 2026-09-26. Status at time of writing: annotator B only.

Annotator B is an embedded software engineer. Source sheet: `Annotation_solved.csv`.

## What was scored

The 128-pair nested dual sample in this folder (`gold.json`). It is the prefix of the 240-pair overlay sample: 4 model × temperature cells × 4 strata × 8 pairs. Pairs are raw overlay programs, not repaired post-SKYT programs.

The question on the sheet:

> Would these two programs be treated as the same implementation for code review, verification, maintenance, or change-control purposes?

`1` / `YES` = same implementation. `0` / `NO` = different.

Gold `fingerprint_same` is the canonical-tree fingerprint (`benchmark.relation.fingerprint`, flexible naming). The scorer treats the fingerprint as the prediction and `human_same` as the reference.

The 128-pair set is stratified, with 64 fingerprint-same and 64 fingerprint-different pairs by construction. Precision, recall, and F1 below are validation-sample metrics. They are not population prevalence estimates. Sensitivity and specificity are the preferred summary.

## How the sheet was processed

1. Read `Annotation_solved.csv` (UTF-8). Columns: `order`, `pair_id`, `human_same`, `notes`.
2. Checked completeness before scoring:
   - 128 data rows, 128 unique `pair_id`s, no duplicate ids.
   - Every `pair_id` matches `gold.json`. No missing ids, no extra ids.
   - Labels are only `YES` (101) and `NO` (27). No blanks, no other tokens.
   - `notes` is empty on every row.
3. Copied the file onto `annotator_b/annotation_sheet.csv`, replacing the blank protocol sheet. Labels were not rewritten to `1`/`0`. `skyt.annotation_score._as_label` maps `YES`/`NO` to 1/0.
4. Left `gold.json`, `annotator_a/`, and `packs/annotator_b.zip` unchanged. The zip is still the blank pack.
5. Scored with `skyt.annotation_score.score` under the name `B`. Wrote `score_annotator_b.json`. Did not write `score.json`, which the protocol reserves for both sheets.

Confusion counts use fingerprint = prediction, human = reference:

| Cell | Meaning |
|---|---|
| TP | Fingerprint same, annotator same |
| FP | Fingerprint same, annotator different |
| TN | Fingerprint different, annotator different |
| FN | Fingerprint different, annotator same |

Stratum and model breakdowns in this note were computed in the same pass from `gold.json` joined to his labels. They are not a separate schema file.

## Headline

| Metric | Value |
|---|---|
| Labeled | 128 / 128 |
| He said same | 101 / 128 |
| He said different | 27 / 128 |
| Raw agreement | 91 / 128 = 71.1% |
| TP, FP, TN, FN | 64, 0, 27, 37 |
| Sensitivity (recall) | 64 / 101 = 63.4% |
| Specificity | 27 / 27 = 100% |
| Precision | 64 / 64 = 100% |
| F1 | 128 / 165 = 0.776 |
| Cohen's κ | not computed (annotator A absent) |

Every disagreement is an FN. The fingerprint never called a pair the same when he called it different. When he says two programs are different implementations, the fingerprint agrees. When he says they are the same, the fingerprint agrees on 64 of 101 pairs.

|  | He said same | He said different |
|---|---:|---:|
| Fingerprint same | 64 | 0 |
| Fingerprint different | 37 | 27 |

## By stratum

Each stratum has 32 pairs.

| Stratum | Agreement | He said same |
|---|---:|---:|
| Fingerprint same, both certified | 32 / 32 (100%) | 32 |
| Fingerprint same, not both certified | 32 / 32 (100%) | 32 |
| Fingerprint different, both certified | 5 / 32 (15.6%) | 27 |
| Fingerprint different, not both certified | 22 / 32 (68.8%) | 10 |

On fingerprint-same pairs he agrees completely, certified or not. The gap is inside fingerprint-different pairs, and certification splits it. When both programs are certified he treats 27/32 fingerprint-different pairs as the same implementation. When they are not both certified he treats 10/32 that way.

## By model and temperature

Each cell has 32 pairs, balanced 16 fingerprint-same and 16 fingerprint-different. The fingerprint-same half is 16/16 agreement in every cell, so the cell differences below are entirely in the fingerprint-different half.

| Cell | Agreement | He said same | Of 16 fingerprint-different, he said same |
|---|---:|---:|---:|
| Claude Sonnet 4.5, T=0.0 | 21 / 32 (65.6%) | 27 / 32 | 11 / 16 |
| Claude Sonnet 4.5, T=0.7 | 22 / 32 (68.8%) | 26 / 32 | 10 / 16 |
| gpt-4o-mini, T=0.0 | 24 / 32 (75.0%) | 24 / 32 | 8 / 16 |
| gpt-4o-mini, T=0.7 | 24 / 32 (75.0%) | 24 / 32 | 8 / 16 |

Temperature does not move his labels inside a model. Claude fingerprint-different pairs are called the same more often than gpt-4o-mini pairs (21/32 vs 16/32).

## What three opened pairs look like

Only three pairs were opened. Do not treat them as a classification of all 37 disagreements.

- **Order 2** (`HumanEval/89`, Claude T=0.0, both certified). He said same; fingerprint different. One program appends the shifted character after the if/else; the other appends inside both branches. Same behavior, different tree.
- **Order 6** (`HumanEval/113`, Claude T=0.0, not both certified). He said same; fingerprint different. One program reassigns `output`; the other introduces a second temporary and assigns `output` from that. Same replace, different binding structure. Flexible naming does not erase that.
- **Order 47** (`HumanEval/46`, gpt-4o-mini T=0.7, both certified). He said different; fingerprint different. One program allocates the Fibonacci prefix by index assignment; the other builds it by concatenation.

The five fingerprint-different, both-certified pairs he marked different are orders 47 (`HumanEval/46`), 61 (`HumanEval/24`), 91 (`HumanEval/156`), 111 (`HumanEval/117`), and 117 (`HumanEval/156`).

## The 37 fingerprint-different pairs he called same

This list shows the fingerprint label. Keep it out of annotator A's view until that sheet is finished.

| Order | Task | Model | T | Both certified |
|---:|---|---|---:|---|
| 2 | HumanEval/89 | Claude | 0.0 | yes |
| 4 | HumanEval/86 | Claude | 0.0 | yes |
| 6 | HumanEval/113 | Claude | 0.0 | no |
| 10 | HumanEval/113 | Claude | 0.7 | no |
| 14 | HumanEval/158 | gpt-4o-mini | 0.0 | yes |
| 19 | HumanEval/65 | Claude | 0.7 | yes |
| 20 | HumanEval/105 | gpt-4o-mini | 0.0 | no |
| 24 | HumanEval/96 | gpt-4o-mini | 0.7 | yes |
| 25 | HumanEval/113 | Claude | 0.0 | no |
| 26 | HumanEval/149 | Claude | 0.0 | yes |
| 27 | HumanEval/113 | Claude | 0.7 | no |
| 28 | HumanEval/68 | gpt-4o-mini | 0.0 | yes |
| 30 | HumanEval/39 | Claude | 0.0 | no |
| 31 | HumanEval/69 | Claude | 0.0 | yes |
| 37 | HumanEval/5 | gpt-4o-mini | 0.0 | yes |
| 39 | HumanEval/129 | gpt-4o-mini | 0.7 | no |
| 41 | HumanEval/109 | Claude | 0.0 | yes |
| 45 | HumanEval/92 | gpt-4o-mini | 0.7 | yes |
| 49 | HumanEval/90 | gpt-4o-mini | 0.7 | yes |
| 51 | HumanEval/139 | gpt-4o-mini | 0.0 | yes |
| 54 | HumanEval/145 | Claude | 0.0 | no |
| 55 | HumanEval/6 | gpt-4o-mini | 0.0 | yes |
| 56 | HumanEval/6 | gpt-4o-mini | 0.0 | yes |
| 63 | HumanEval/105 | gpt-4o-mini | 0.7 | no |
| 64 | HumanEval/3 | gpt-4o-mini | 0.0 | yes |
| 65 | HumanEval/123 | Claude | 0.7 | yes |
| 67 | HumanEval/158 | Claude | 0.7 | yes |
| 70 | HumanEval/125 | Claude | 0.7 | yes |
| 74 | HumanEval/73 | Claude | 0.7 | yes |
| 79 | HumanEval/64 | Claude | 0.0 | yes |
| 80 | HumanEval/133 | Claude | 0.0 | yes |
| 81 | HumanEval/124 | gpt-4o-mini | 0.7 | no |
| 84 | HumanEval/128 | Claude | 0.7 | yes |
| 85 | HumanEval/106 | Claude | 0.7 | yes |
| 99 | HumanEval/94 | gpt-4o-mini | 0.7 | yes |
| 100 | HumanEval/104 | Claude | 0.7 | yes |
| 121 | HumanEval/130 | gpt-4o-mini | 0.7 | yes |

`HumanEval/113` accounts for 4 of the 37. No other task accounts for more than 2.

## Not done

- Annotator A's sheet was not read and not scored.
- No adjudication, no Cohen's κ, no majority label.
- The 37 disagreements were not classified beyond the three pairs opened above.
- No paper text was updated. These numbers stay out of the papers until both sheets are back.
