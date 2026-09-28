# Annotator instructions

You will see pairs of Python programs (`A.py` and `B.py`). For each pair,
answer **one** question:

> Would these two programs be treated as the same implementation for code review, verification, maintenance, or change-control purposes?

Write `1` (same) or `0` (different) in `human_same` on your sheet.

## Same implementation

Differences that would **not** normally trigger separate reasoning about
program behavior or structure. Typical examples: names, whitespace,
comments, equivalent local rearrangements that a reviewer would treat as
the same solution.

## Different implementation

Differences substantial enough to require **independent**
review/verification reasoning. Typical examples: a different algorithm,
different control-flow shape, different boundary handling, or a change
you would want to re-read as a new patch.

## Rules

- Do not discuss the task with the other annotator until both sheets are
  complete.
- Do not try to reverse-engineer any automatic metric.
- If you are unsure, still pick 0 or 1 using the criterion above; do not
  leave the cell blank.

You should have only your sheet and the `programs/` folder. You should
**not** see model, temperature, pre/post status, automatic labels, or
expected answers.

Each pair lives in `programs/{order:03d}_{pair_id}/` (order is zero-padded
to three digits). Open `A.py` and `B.py` there.
