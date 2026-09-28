# Dual-annotator fingerprint protocol

Coordinator file. Annotators read `INSTRUCTIONS.md`, not this.

> Would these two programs be treated as the same implementation for code review, verification, maintenance, or change-control purposes?

128 pairs (4 model×temperature cells × 4 strata × 8).
Nested subset of the 240-pair overlay sample (seed 20260723).

Give each person **only** their zip under `packs/`
(`INSTRUCTIONS.md` + their sheet + `programs/`).
Do not give `gold.json`, this protocol, or `COORDINATOR.md`.

Score after both sheets are filled:

```
python -m skyt.annotation_score \
  --gold outputs/benchmark/fingerprint_annotation_dual/gold.json \
  --sheet-a outputs/benchmark/fingerprint_annotation_dual/annotator_a/annotation_sheet.csv \
  --sheet-b outputs/benchmark/fingerprint_annotation_dual/annotator_b/annotation_sheet.csv \
  --out outputs/benchmark/fingerprint_annotation_dual/score.json
```

Reports Cohen's κ and raw agreement (human–human), plus
sensitivity / specificity / precision / recall / F1 of the
fingerprint against each annotator (human = reference).
The 128-pair set is stratified, so precision and F1 are
validation-sample metrics, not population prevalence estimates.
