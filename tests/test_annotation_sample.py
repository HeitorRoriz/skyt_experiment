"""Dual-pack subsample of the 240-pair overlay sample. No Docker, no API."""

import csv
import json
import zipfile
from collections import Counter

from skyt.annotation_sample import QUESTION, nested_dual_pairs, write_dual_pack


def test_nested_dual_is_128_and_balanced():
    pairs = []
    for model, temp in (
        ("gpt-4o-mini", 0.0),
        ("gpt-4o-mini", 0.7),
        ("claude-sonnet-4-5-20250929", 0.0),
        ("claude-sonnet-4-5-20250929", 0.7),
    ):
        for fp_same in (True, False):
            for both_cert in (True, False):
                stratum = (
                    f"{'fp_same' if fp_same else 'fp_diff'}|"
                    f"{'both_cert' if both_cert else 'not_both_cert'}"
                )
                for i in range(15):
                    pairs.append(
                        {
                            "model": model,
                            "temperature": temp,
                            "stratum": stratum,
                            "pair_id": f"{model}-{temp}-{stratum}-{i:02d}",
                            "fingerprint_same": fp_same,
                        }
                    )
    dual = nested_dual_pairs(pairs)
    assert len(dual) == 128
    assert [row["order"] for row in dual] == list(range(1, 129))
    counts = Counter((row["model"], row["temperature"], row["stratum"]) for row in dual)
    assert len(counts) == 16
    assert set(counts.values()) == {8}


def test_dual_pack_is_blind_and_complete(tmp_path):
    source = tmp_path / "sample"
    pair_id = "abc123def456"
    src_prog = source / "programs" / f"001_{pair_id}"
    src_prog.mkdir(parents=True)
    (src_prog / "A.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (src_prog / "B.py").write_text("def f():\n    return 2\n", encoding="utf-8")
    pairs = [
        {
            "task_id": "HumanEval/0",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "fingerprint_same": True,
            "stratum": "fp_same|both_cert",
            "pair_id": pair_id,
            "order": 1,
        }
    ]
    out = tmp_path / "dual"
    write_dual_pack(pairs, source_sample=source, out_dir=out)
    sheet_text = (out / "annotator_a" / "annotation_sheet.csv").read_text(encoding="utf-8")
    header = next(csv.reader(sheet_text.splitlines()))
    assert header == ["order", "pair_id", "human_same", "notes"]
    assert "gpt" not in sheet_text.lower()
    assert "fingerprint" not in sheet_text.lower()
    assert "0.7" not in sheet_text
    a_readme = (out / "annotator_a" / "README.md").read_text(encoding="utf-8").lower()
    assert "gold" not in a_readme
    instructions = (out / "INSTRUCTIONS.md").read_text(encoding="utf-8")
    assert QUESTION in instructions
    assert "purposes?" in instructions
    gold = json.loads((out / "gold.json").read_text(encoding="utf-8"))
    assert gold["pairs"][0]["fingerprint_same"] is True
    assert (out / "programs" / f"001_{pair_id}" / "A.py").exists()
    with zipfile.ZipFile(out / "packs" / "annotator_a.zip") as archive:
        names = archive.namelist()
    assert "gold.json" not in names
    assert "PROTOCOL.md" not in names
    assert "annotation_sheet.csv" in names
    assert "INSTRUCTIONS.md" in names
    assert any(name.endswith("A.py") for name in names)
