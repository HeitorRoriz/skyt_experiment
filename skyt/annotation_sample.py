"""Stratified fingerprint annotation sample from the frozen overlay. No LLM.

Heitor (and a second annotator if available) labels whether two programs
would be treated as the same implementation for review / verification /
maintenance / change-control. Repaired post-SKYT programs were not persisted,
so this sample is overlay (raw) pairs only.
"""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
import random
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from benchmark.protect import assert_writable
from benchmark.relation import RELATION_VERSION, fingerprint
from benchmark.schema import BOOTSTRAP_SEED
from benchmark.score import _is_certified
from benchmarks.humaneval_plus.provenance import atomic_write_json
from benchmarks.humaneval_plus.run import _load_existing, _safe_name
from skyt.humaneval_heldout import OVERLAY_SOURCE


OUT_DIR = Path("outputs") / "benchmark" / "fingerprint_annotation_sample"
DUAL_OUT = Path("outputs") / "benchmark" / "fingerprint_annotation_dual"
N = 20
PER_STRATUM = 15
DUAL_PER_STRATUM = 8
CELLS = [
    ("gpt-4o-mini", 0.0),
    ("gpt-4o-mini", 0.7),
    ("claude-sonnet-4-5-20250929", 0.7),
    ("claude-sonnet-4-5-20250929", 0.0),
]


def _stratum(fp_same: bool, both_cert: bool) -> str:
    same = "fp_same" if fp_same else "fp_diff"
    cert = "both_cert" if both_cert else "not_both_cert"
    return f"{same}|{cert}"


def _pair_id(
    task_id: str, model: str, temperature: float, i: int, j: int
) -> str:
    raw = f"{task_id}|{model}|{temperature}|{i}|{j}|v{RELATION_VERSION}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def collect_candidates(source_dir: Path) -> Dict[Tuple[str, float, str], List[Dict[str, Any]]]:
    buckets: Dict[Tuple[str, float, str], List[Dict[str, Any]]] = defaultdict(list)
    jsonl_files = sorted(source_dir.glob("*.jsonl"))
    for path in jsonl_files:
        records = sorted(
            _load_existing(path), key=lambda item: int(item.get("run_index", 0))
        )[:N]
        if len(records) < 2:
            continue
        task_id = records[0].get("task_id")
        model = records[0].get("model")
        temperature = float(records[0].get("temperature", 0.0))
        if task_id is None or model is None:
            continue
        prints = [
            fingerprint(record.get("stitched_code") or "", flexible_naming=True)
            for record in records
        ]
        certified = [
            _is_certified(record, fp is not None)
            for record, fp in zip(records, prints)
        ]
        for i, j in itertools.combinations(range(len(records)), 2):
            if prints[i] is None or prints[j] is None:
                continue
            fp_same = prints[i] == prints[j]
            both_cert = bool(certified[i] and certified[j])
            key = (str(model), float(temperature), _stratum(fp_same, both_cert))
            buckets[key].append(
                {
                    "task_id": str(task_id),
                    "model": str(model),
                    "temperature": float(temperature),
                    "run_i": int(records[i]["run_index"]),
                    "run_j": int(records[j]["run_index"]),
                    "fingerprint_same": fp_same,
                    "i_certified": bool(certified[i]),
                    "j_certified": bool(certified[j]),
                    "both_certified": both_cert,
                    "stratum": _stratum(fp_same, both_cert),
                    "source_jsonl": path.name,
                }
            )
    return buckets


def sample_pairs(
    buckets: Dict[Tuple[str, float, str], List[Dict[str, Any]]],
    *,
    per_stratum: int = PER_STRATUM,
    seed: int = BOOTSTRAP_SEED,
) -> List[Dict[str, Any]]:
    rng = random.Random(seed)
    sampled: List[Dict[str, Any]] = []
    for model, temperature in CELLS:
        for fp_same in (True, False):
            for both_cert in (True, False):
                key = (model, float(temperature), _stratum(fp_same, both_cert))
                pool = list(buckets.get(key, []))
                rng.shuffle(pool)
                take = pool[:per_stratum]
                if len(take) < per_stratum:
                    print(
                        f"  short stratum {key}: {len(take)}/{per_stratum}",
                        flush=True,
                    )
                sampled.extend(take)
    rng.shuffle(sampled)
    for index, row in enumerate(sampled, start=1):
        row["pair_id"] = _pair_id(
            row["task_id"],
            row["model"],
            row["temperature"],
            row["run_i"],
            row["run_j"],
        )
        row["order"] = index
        row["human_same"] = ""
        row["annotator"] = ""
        row["notes"] = ""
    return sampled


def _codes_for_pair(source_dir: Path, row: Dict[str, Any]) -> Tuple[str, str]:
    stem = _safe_name(row["task_id"], row["model"], row["temperature"])
    records = {
        int(item["run_index"]): item
        for item in _load_existing(source_dir / f"{stem}.jsonl")
    }
    left = records[int(row["run_i"])].get("stitched_code") or ""
    right = records[int(row["run_j"])].get("stitched_code") or ""
    return left, right


def write_sample(
    pairs: List[Dict[str, Any]],
    source_dir: Path,
    out_dir: Path,
) -> Path:
    assert_writable(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    programs_dir = out_dir / "programs"
    programs_dir.mkdir(exist_ok=True)
    sheet_path = out_dir / "annotation_sheet.csv"
    manifest = {
        "schema": "sameeval-fingerprint-annotation-v1",
        "relation_version": RELATION_VERSION,
        "source_dir": str(source_dir),
        "n_pairs": len(pairs),
        "per_stratum": PER_STRATUM,
        "seed": BOOTSTRAP_SEED,
        "phase": "overlay_raw",
        "question": (
            "Would these two programs be treated as the same implementation "
            "for code review, verification, maintenance, or change-control?"
        ),
        "labels": {"1": "same", "0": "different", "": "unlabeled"},
        "note": (
            "Post-SKYT repaired programs were not persisted; sample is "
            "overlay (raw) pairs. Fill human_same with 1 or 0."
        ),
        "pairs": pairs,
    }
    atomic_write_json(out_dir / "pairs.json", manifest)
    fieldnames = [
        "order",
        "pair_id",
        "task_id",
        "model",
        "temperature",
        "run_i",
        "run_j",
        "fingerprint_same",
        "both_certified",
        "i_certified",
        "j_certified",
        "stratum",
        "human_same",
        "annotator",
        "notes",
    ]
    with sheet_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in pairs:
            writer.writerow({name: row.get(name) for name in fieldnames})
            left, right = _codes_for_pair(source_dir, row)
            pair_dir = programs_dir / f"{row['order']:03d}_{row['pair_id']}"
            pair_dir.mkdir(exist_ok=True)
            (pair_dir / "A.py").write_text(left, encoding="utf-8")
            (pair_dir / "B.py").write_text(right, encoding="utf-8")
            (pair_dir / "meta.json").write_text(
                json.dumps(
                    {
                        "pair_id": row["pair_id"],
                        "task_id": row["task_id"],
                        "model": row["model"],
                        "temperature": row["temperature"],
                        "fingerprint_same": row["fingerprint_same"],
                        "question": manifest["question"],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
    blind_path = out_dir / "annotation_sheet_blind.csv"
    blind_fields = [
        "order",
        "pair_id",
        "task_id",
        "model",
        "temperature",
        "human_same",
        "annotator",
        "notes",
    ]
    with blind_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=blind_fields)
        writer.writeheader()
        for row in pairs:
            writer.writerow({name: row.get(name) for name in blind_fields})
    readme = out_dir / "README.md"
    readme.write_text(
        "\n".join(
            [
                "# Fingerprint annotation sample",
                "",
                manifest["question"],
                "",
                "Label `human_same` in `annotation_sheet.csv`: `1` = same implementation, `0` = different.",
                "Do not look at `fingerprint_same` while labeling if you want an independent judgment.",
                "",
                f"N pairs: {len(pairs)}. Seed {BOOTSTRAP_SEED}. Overlay raw only.",
                "Programs: `programs/<order>_<pair_id>/A.py` and `B.py`.",
                "Label the blind sheet; score later against `annotation_sheet.csv`.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"wrote {sheet_path} ({len(pairs)} pairs)", flush=True)
    return sheet_path


QUESTION = (
    "Would these two programs be treated as the same implementation "
    "for code review, verification, maintenance, or change-control purposes?"
)

INSTRUCTIONS_MD = f"""# Annotator instructions

You will see pairs of Python programs (`A.py` and `B.py`). For each pair,
answer **one** question:

> {QUESTION}

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

Each pair lives in `programs/{{order:03d}}_{{pair_id}}/` (order is zero-padded
to three digits). Open `A.py` and `B.py` there.
"""

BLIND_SHEET_FIELDS = ["order", "pair_id", "human_same", "notes"]
FORBIDDEN_BLIND_COLUMNS = {
    "model",
    "temperature",
    "fingerprint_same",
    "stratum",
    "sameeval",
    "pre_post",
    "expected",
}


def nested_dual_pairs(
    pairs: Sequence[Dict[str, Any]],
    *,
    per_stratum: int = DUAL_PER_STRATUM,
) -> List[Dict[str, Any]]:
    """Prefix of the 240-pair sample: 4 cells × 4 strata × 8 = 128 pairs."""
    buckets: Dict[Tuple[str, float, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in pairs:
        key = (str(row["model"]), float(row["temperature"]), str(row["stratum"]))
        buckets[key].append(row)
    sampled: List[Dict[str, Any]] = []
    for model, temperature in CELLS:
        for fp_same in (True, False):
            for both_cert in (True, False):
                key = (model, float(temperature), _stratum(fp_same, both_cert))
                pool = sorted(buckets.get(key, []), key=lambda item: str(item["pair_id"]))
                sampled.extend(pool[:per_stratum])
    sampled.sort(key=lambda item: str(item["pair_id"]))
    for index, row in enumerate(sampled, start=1):
        row = dict(row)
        row["order"] = index
        sampled[index - 1] = row
    return sampled


def _copy_programs(
    source_programs: Path,
    dest_programs: Path,
    pairs: Sequence[Dict[str, Any]],
) -> None:
    dest_programs.mkdir(parents=True, exist_ok=True)
    by_id = {}
    if source_programs.exists():
        for folder in source_programs.iterdir():
            if folder.is_dir() and "_" in folder.name:
                by_id[folder.name.split("_", 1)[1]] = folder
    for row in pairs:
        pair_id = str(row["pair_id"])
        src = by_id.get(pair_id)
        dest = dest_programs / f"{int(row['order']):03d}_{pair_id}"
        dest.mkdir(parents=True, exist_ok=True)
        if src is not None:
            (dest / "A.py").write_text(
                (src / "A.py").read_text(encoding="utf-8"), encoding="utf-8"
            )
            (dest / "B.py").write_text(
                (src / "B.py").read_text(encoding="utf-8"), encoding="utf-8"
            )
        (dest / "QUESTION.txt").write_text(QUESTION + "\n", encoding="utf-8")


def _annotator_readme(annotator: str) -> str:
    return "\n".join(
        [
            f"# Annotator {annotator}",
            "",
            "Read `INSTRUCTIONS.md` first.",
            "",
            f"> {QUESTION}",
            "",
            "For each row of `annotation_sheet.csv`, open",
            "`programs/{order:03d}_{pair_id}/A.py` and `B.py`",
            "(order is zero-padded to three digits, e.g. `001_abc123`).",
            "In the zip pack those folders sit next to this README;",
            "if you were given the kit folders instead, use `../programs/`.",
            "Write `1` (same implementation) or `0` (different) in `human_same`.",
            "Optional comments go in `notes`.",
            "Do not discuss cases with the other annotator.",
            "",
        ]
    )


def _coordinator_md(n_pairs: int) -> str:
    return "\n".join(
        [
            "# Coordinator handoff (not for annotators)",
            "",
            "This file, `PROTOCOL.md`, and `gold.json` stay with the coordinator.",
            "Do **not** include them in annotator zips or email.",
            "",
            "## What each annotator receives",
            "",
            "Send **one** of these packs (already zipped under `packs/`):",
            "",
            "- Annotator A: `packs/annotator_a.zip`",
            "- Annotator B: `packs/annotator_b.zip`",
            "",
            "Each zip contains only `INSTRUCTIONS.md`, `README.md`,",
            "`annotation_sheet.csv`, and `programs/`.",
            "If you unpack by hand instead of using the zip:",
            "give `INSTRUCTIONS.md`, one of `annotator_a/` or `annotator_b/`,",
            "and the shared `programs/` folder. Never give `gold.json`.",
            "",
            "## Blindness",
            "",
            "Annotators must not see model, temperature, SameEval verdict,",
            "fingerprint category, pre/post, or expected answer.",
            "Blind sheets have only `order`, `pair_id`, `human_same`, `notes`.",
            "",
            "## After both sheets return",
            "",
            "Copy filled CSVs back onto `annotator_a/annotation_sheet.csv`",
            "and `annotator_b/annotation_sheet.csv`, then score:",
            "",
            "```",
            "python -m skyt.annotation_score \\",
            "  --gold outputs/benchmark/fingerprint_annotation_dual/gold.json \\",
            "  --sheet-a outputs/benchmark/fingerprint_annotation_dual/annotator_a/annotation_sheet.csv \\",
            "  --sheet-b outputs/benchmark/fingerprint_annotation_dual/annotator_b/annotation_sheet.csv \\",
            "  --out outputs/benchmark/fingerprint_annotation_dual/score.json",
            "```",
            "",
            f"{n_pairs} pairs; nested prefix of the 240-pair overlay sample",
            f"at `outputs/benchmark/fingerprint_annotation_sample/` (seed {BOOTSTRAP_SEED}).",
            "Leave paper construct wording as unlabeled until both sheets are back.",
            "",
        ]
    )


def _protocol_md(n_pairs: int) -> str:
    return "\n".join(
        [
            "# Dual-annotator fingerprint protocol",
            "",
            "Coordinator file. Annotators read `INSTRUCTIONS.md`, not this.",
            "",
            f"> {QUESTION}",
            "",
            f"{n_pairs} pairs (4 model×temperature cells × 4 strata × {DUAL_PER_STRATUM}).",
            f"Nested subset of the 240-pair overlay sample (seed {BOOTSTRAP_SEED}).",
            "",
            "Give each person **only** their zip under `packs/`",
            "(`INSTRUCTIONS.md` + their sheet + `programs/`).",
            "Do not give `gold.json`, this protocol, or `COORDINATOR.md`.",
            "",
            "Score after both sheets are filled:",
            "",
            "```",
            "python -m skyt.annotation_score \\",
            "  --gold outputs/benchmark/fingerprint_annotation_dual/gold.json \\",
            "  --sheet-a outputs/benchmark/fingerprint_annotation_dual/annotator_a/annotation_sheet.csv \\",
            "  --sheet-b outputs/benchmark/fingerprint_annotation_dual/annotator_b/annotation_sheet.csv \\",
            "  --out outputs/benchmark/fingerprint_annotation_dual/score.json",
            "```",
            "",
            "Reports Cohen's κ and raw agreement (human–human), plus",
            "sensitivity / specificity / precision / recall / F1 of the",
            "fingerprint against each annotator (human = reference).",
            "The 128-pair set is stratified, so precision and F1 are",
            "validation-sample metrics, not population prevalence estimates.",
            "",
        ]
    )


def _write_blind_sheet(path: Path, pairs: Sequence[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=BLIND_SHEET_FIELDS)
        writer.writeheader()
        for row in pairs:
            writer.writerow(
                {
                    "order": row["order"],
                    "pair_id": row["pair_id"],
                    "human_same": "",
                    "notes": "",
                }
            )
    with path.open(encoding="utf-8", newline="") as handle:
        header = next(csv.reader(handle))
    leaked = [name for name in header if name.lower() in FORBIDDEN_BLIND_COLUMNS]
    if leaked or header != BLIND_SHEET_FIELDS:
        raise ValueError(f"non-blind sheet columns: {header}")


def _zip_annotator_pack(
    zip_path: Path,
    *,
    instructions: str,
    readme: str,
    sheet: Path,
    programs: Path,
) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("INSTRUCTIONS.md", instructions)
        archive.writestr("README.md", readme)
        archive.write(sheet, arcname="annotation_sheet.csv")
        for file_path in sorted(programs.rglob("*")):
            if file_path.is_file():
                archive.write(file_path, arcname=str(Path("programs") / file_path.relative_to(programs)))


def write_dual_pack(
    pairs: Sequence[Dict[str, Any]],
    *,
    source_sample: Path = OUT_DIR,
    out_dir: Path = DUAL_OUT,
) -> Path:
    """Two blind sheets. No model, temperature, or fingerprint on annotator files."""
    assert_writable(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    gold = {
        "schema": "sameeval-fingerprint-annotation-dual-v1",
        "relation_version": RELATION_VERSION,
        "n_pairs": len(pairs),
        "per_stratum": DUAL_PER_STRATUM,
        "seed": BOOTSTRAP_SEED,
        "parent_sample": str(source_sample),
        "question": QUESTION,
        "labels": {"1": "same", "0": "different", "": "unlabeled"},
        "pairs": list(pairs),
    }
    atomic_write_json(out_dir / "gold.json", gold)
    _copy_programs(source_sample / "programs", out_dir / "programs", pairs)
    (out_dir / "INSTRUCTIONS.md").write_text(INSTRUCTIONS_MD, encoding="utf-8")
    (out_dir / "COORDINATOR.md").write_text(_coordinator_md(len(pairs)), encoding="utf-8")
    (out_dir / "PROTOCOL.md").write_text(_protocol_md(len(pairs)), encoding="utf-8")
    for annotator in ("A", "B"):
        folder = out_dir / f"annotator_{annotator.lower()}"
        folder.mkdir(exist_ok=True)
        sheet = folder / "annotation_sheet.csv"
        _write_blind_sheet(sheet, pairs)
        readme = _annotator_readme(annotator)
        (folder / "README.md").write_text(readme, encoding="utf-8")
        (folder / "INSTRUCTIONS.md").write_text(INSTRUCTIONS_MD, encoding="utf-8")
        _zip_annotator_pack(
            out_dir / "packs" / f"annotator_{annotator.lower()}.zip",
            instructions=INSTRUCTIONS_MD,
            readme=readme,
            sheet=sheet,
            programs=out_dir / "programs",
        )
    print(f"wrote dual pack {out_dir} ({len(pairs)} pairs)", flush=True)
    return out_dir


def run(*, source_dir: Path = OVERLAY_SOURCE, out_dir: Path = OUT_DIR) -> List[Dict[str, Any]]:
    print("collecting overlay pairs", flush=True)
    buckets = collect_candidates(source_dir)
    for key, items in sorted(buckets.items(), key=lambda item: (item[0][0], item[0][1], item[0][2])):
        print(f"  {key[0]} T={key[1]} {key[2]}: {len(items)}", flush=True)
    pairs = sample_pairs(buckets)
    write_sample(pairs, source_dir, out_dir)
    return pairs


def run_dual(*, sample_dir: Path = OUT_DIR, out_dir: Path = DUAL_OUT) -> List[Dict[str, Any]]:
    manifest = json.loads((sample_dir / "pairs.json").read_text(encoding="utf-8"))
    pairs = nested_dual_pairs(manifest["pairs"])
    write_dual_pack(pairs, source_sample=sample_dir, out_dir=out_dir)
    return pairs


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fingerprint annotation sample (no LLM).")
    parser.add_argument(
        "--dual",
        action="store_true",
        help="Write the 128-pair two-annotator pack from the existing 240-pair sample.",
    )
    args = parser.parse_args()
    if args.dual:
        run_dual()
    else:
        run()
