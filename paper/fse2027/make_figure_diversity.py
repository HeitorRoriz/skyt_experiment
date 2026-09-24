"""Exploratory figure: Extra-failure rate by Base-form diversity bin.

Reads diversity_signal.json. Does not edit make_figure_skyt.py and does not
recompute the bootstrap.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PAPER = Path(__file__).resolve().parent
REPO = PAPER.parents[1]
REPORT = REPO / "outputs" / "benchmark" / "diversity_signal" / "diversity_signal.json"
OUT = PAPER / "figures" / "fig_diversity_signal.pdf"

BIN_ORDER = ("D=0", "T1", "T2", "T3")
BIN_LABELS = ("D = 0", "T1", "T2", "T3")


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
            "legend.fontsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def _pretty(cell: str) -> str:
    return (
        cell.replace("claude-sonnet-4-5-20250929", "Claude 4.5")
        .replace("gpt-4o-mini", "GPT-4o-mini")
        .replace("claude-sonnet-5", "Sonnet 5")
        .replace("claude-haiku-4-5-20251001", "Haiku 4.5")
        .replace("gpt-6-luna", "Luna")
    )


def make_figure(report: dict, out_path: Path) -> None:
    _style()
    cells = list(report["bins"]["cells"])
    colors = ["#4C78A8", "#72B7B2", "#F58518", "#E45756", "#54A24B", "#B279A2"]
    x = np.arange(len(BIN_ORDER))
    width = 0.8 / max(len(cells), 1)
    fig, ax = plt.subplots(figsize=(5.2, 3.2), layout="constrained")
    for index, cell in enumerate(cells):
        by_name = {row["bin"]: row for row in report["bins"]["cells"][cell]}
        heights = []
        lows = []
        highs = []
        for name in BIN_ORDER:
            row = by_name.get(name) or {}
            estimate = row.get("estimate")
            ci = row.get("ci95")
            heights.append(np.nan if estimate is None else 100.0 * estimate)
            if estimate is None or not ci or ci[0] is None:
                lows.append(0.0)
                highs.append(0.0)
            else:
                lows.append(max(0.0, 100.0 * estimate - 100.0 * ci[0]))
                highs.append(max(0.0, 100.0 * ci[1] - 100.0 * estimate))
        offset = (index - (len(cells) - 1) / 2) * width
        ax.bar(
            x + offset,
            heights,
            width=width * 0.92,
            label=_pretty(cell),
            color=colors[index % len(colors)],
            yerr=np.vstack([lows, highs]),
            capsize=2,
            error_kw={"elinewidth": 0.6},
        )
    ax.set_xticks(x)
    ax.set_xticklabels(BIN_LABELS)
    ax.set_ylabel("Extra-failure rate among Base-passers (%)")
    ax.set_xlabel("Form diversity (D = 0, then tertiles of D > 0)")
    ax.legend(frameon=False, ncol=2)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def main() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    make_figure(report, OUT)
    print(OUT)


if __name__ == "__main__":
    main()
