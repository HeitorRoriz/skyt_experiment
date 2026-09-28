# Annotator A

Read `INSTRUCTIONS.md` first.

> Would these two programs be treated as the same implementation for code review, verification, maintenance, or change-control purposes?

For each row of `annotation_sheet.csv`, open
`programs/{order:03d}_{pair_id}/A.py` and `B.py`
(order is zero-padded to three digits, e.g. `001_abc123`).
In the zip pack those folders sit next to this README;
if you were given the kit folders instead, use `../programs/`.
Write `1` (same implementation) or `0` (different) in `human_same`.
Optional comments go in `notes`.
Do not discuss cases with the other annotator.
