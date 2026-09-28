# Coordinator handoff (not for annotators)

This file, `PROTOCOL.md`, and `gold.json` stay with the coordinator.
Do **not** include them in annotator zips or email.

## What each annotator receives

Send **one** of these packs (already zipped under `packs/`):

- Annotator A: `packs/annotator_a.zip`
- Annotator B: `packs/annotator_b.zip`

Each zip contains only `INSTRUCTIONS.md`, `README.md`,
`annotation_sheet.csv`, and `programs/`.
If you unpack by hand instead of using the zip:
give `INSTRUCTIONS.md`, one of `annotator_a/` or `annotator_b/`,
and the shared `programs/` folder. Never give `gold.json`.

## Blindness

Annotators must not see model, temperature, SameEval verdict,
fingerprint category, pre/post, or expected answer.
Blind sheets have only `order`, `pair_id`, `human_same`, `notes`.

## After both sheets return

Copy filled CSVs back onto `annotator_a/annotation_sheet.csv`
and `annotator_b/annotation_sheet.csv`, then score:

```
python -m skyt.annotation_score \
  --gold outputs/benchmark/fingerprint_annotation_dual/gold.json \
  --sheet-a outputs/benchmark/fingerprint_annotation_dual/annotator_a/annotation_sheet.csv \
  --sheet-b outputs/benchmark/fingerprint_annotation_dual/annotator_b/annotation_sheet.csv \
  --out outputs/benchmark/fingerprint_annotation_dual/score.json
```

128 pairs; nested prefix of the 240-pair overlay sample
at `outputs/benchmark/fingerprint_annotation_sample/` (seed 20260723).
Leave paper construct wording as unlabeled until both sheets are back.
