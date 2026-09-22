"""Held-out SKYT figures for the FSE 2027 draft.

Reads posthoc_report.json. No API, no runtime change, no overlay overwrite.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PAPER = Path(__file__).resolve().parent
REPO = PAPER.parents[1]
ORACLE_POSTHOC = (
    REPO
    / "outputs"
    / "benchmark"
    / "humaneval_plus_164_n20_skyt_heldout_oracle_split"
    / "oracle_split_posthoc.json"
)
ROWS = (
    REPO
    / "outputs"
    / "benchmark"
    / "humaneval_plus_164_n20_skyt_heldout_oracle_split"
    / "oracle_split_config_rows.json"
)

CELL_LABELS = {
    "gpt-4o-mini T=0.0": "GPT-4o-mini T=0.0",
    "gpt-4o-mini T=0.7": "GPT-4o-mini T=0.7",
    "claude-sonnet-4-5-20250929 T=0.0": "Claude 4.5 T=0.0",
    "claude-sonnet-4-5-20250929 T=0.7": "Claude 4.5 T=0.7",
}

COLORS = {
    "gpt-4o-mini T=0.0": "#4C78A8",
    "gpt-4o-mini T=0.7": "#72B7B2",
    "claude-sonnet-4-5-20250929 T=0.0": "#F58518",
    "claude-sonnet-4-5-20250929 T=0.7": "#E45756",
}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.size": 8.5,
            "axes.labelsize": 8.5,
            "axes.titlesize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _slice_by_label(report: dict, label: str) -> dict:
    for row in report["slices"]:
        if row["label"] == label:
            return row
    raise KeyError(label)


def make_arrows(report: dict, out_stem: Path) -> None:
    _style()
    fig, ax = plt.subplots(figsize=(4.8, 4.4), layout="constrained")
    for label, pretty in CELL_LABELS.items():
        row = _slice_by_label(report, label)
        x0 = row["plus_pass_pre"]["pct"]
        y0 = (row.get("plus_same_at_2_pre") or row["same_at_2_pre"])["pct"]
        x1 = row["plus_pass_post"]["pct"]
        y1 = (row.get("plus_same_at_2_post") or row["same_at_2_post"])["pct"]
        color = COLORS[label]
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops={
                "arrowstyle": "-|>",
                "color": color,
                "lw": 1.6,
                "mutation_scale": 10,
            },
        )
        ax.scatter([x0], [y0], s=28, color=color, zorder=3, label=pretty)
        ax.scatter([x1], [y1], s=36, color=color, marker="s", zorder=3)
    ax.set_xlabel("Held-out Plus pass (%)")
    ax.set_ylabel("same@2 (%)")
    ax.set_xlim(72, 96)
    ax.set_ylim(40, 96)
    ax.set_title("SKYT primarily improves repeatability")
    ax.legend(frameon=False, loc="lower right")
    ax.set_axisbelow(True)
    ax.grid(True, linestyle=":", linewidth=0.5, color="#bbbbbb")
    fig.savefig(out_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(out_stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_stem.with_suffix('.pdf')}")


def _disagreement_pre(row: dict) -> float:
    block = row.get("plus_disagreement_pre_common") or row["disagreement_pre_common"]
    return block["pct"]


def _disagreement_post(row: dict) -> float:
    block = row.get("plus_disagreement_post_common") or row["disagreement_post_common"]
    return block["pct"]


def make_disagreement(report: dict, out_stem: Path) -> None:
    _style()
    overall = _slice_by_label(report, "all")
    labels = ["Overall"] + list(CELL_LABELS.values())
    keys = ["all"] + list(CELL_LABELS)
    pre = [_disagreement_pre(_slice_by_label(report, key)) for key in keys]
    post = [_disagreement_post(_slice_by_label(report, key)) for key in keys]
    fig, ax = plt.subplots(figsize=(7.15, 3.05), layout="constrained")
    x = np.arange(len(labels))
    width = 0.36
    ax.bar(
        x - width / 2,
        pre,
        width,
        label="RAW",
        color="#4C78A8",
        edgecolor="black",
        linewidth=0.4,
    )
    ax.bar(
        x + width / 2,
        post,
        width,
        label="SKYT",
        color="#54A24B",
        edgecolor="black",
        linewidth=0.4,
        hatch="//",
    )
    ax.set_xticks(x, labels, rotation=15, ha="right")
    ax.set_ylabel("Certified disagreement (%)")
    ax.set_ylim(0, max(pre) * 1.25)
    rel = overall.get("plus_disagreement_relative_reduction_common_pct")
    if rel is None:
        rel = overall.get("disagreement_relative_reduction_common_pct")
    ax.set_title(
        f"Certified disagreement  "
        f"{_disagreement_pre(overall)}% → "
        f"{_disagreement_post(overall)}% "
        f"(relative reduction {rel}%)"
    )
    ax.legend(frameon=False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, color="#bbbbbb")
    fig.savefig(out_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(out_stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_stem.with_suffix('.pdf')}")


def make_lift_scatter(out_stem: Path) -> None:
    rows = json.loads(ROWS.read_text(encoding="utf-8"))
    _style()
    fig, ax = plt.subplots(figsize=(4.8, 4.4), layout="constrained")
    for label, pretty in CELL_LABELS.items():
        model, _, temp = label.partition(" T=")
        xs = []
        ys = []
        for row in rows:
            if row["model"] != model or float(row["temperature"]) != float(temp):
                continue
            if row.get("pre_plus_same_at_2") is not None:
                xs.append(100.0 * float(row["pre_plus_same_at_2"]))
                ys.append(100.0 * float(row["delta_plus_same_at_2"]))
            elif row.get("pre_same_at_2") is not None and row.get("delta_same_at_2") is not None:
                xs.append(100.0 * float(row["pre_same_at_2"]))
                ys.append(100.0 * float(row["delta_same_at_2"]))
            else:
                continue
        ax.scatter(xs, ys, s=12, alpha=0.55, color=COLORS[label], label=pretty, edgecolors="none")
    ax.axhline(0.0, color="#888888", linewidth=0.6)
    ax.set_xlabel("Baseline same@2 (%)")
    ax.set_ylabel("SKYT lift (pp)")
    ax.set_title("Larger lift where baseline repeatability is lower")
    ax.legend(frameon=False, loc="upper right", markerscale=1.4)
    ax.set_axisbelow(True)
    ax.grid(True, linestyle=":", linewidth=0.5, color="#bbbbbb")
    fig.savefig(out_stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(out_stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out_stem.with_suffix('.pdf')}")


def main() -> None:
    oracle = json.loads(ORACLE_POSTHOC.read_text(encoding="utf-8"))
    make_arrows(oracle, PAPER / "fig_arrows")
    make_disagreement(oracle, PAPER / "fig_disagreement")
    make_lift_scatter(PAPER / "fig_lift")


if __name__ == "__main__":
    main()
