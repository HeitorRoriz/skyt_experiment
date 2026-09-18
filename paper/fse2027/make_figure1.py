"""Figure 1 for the FSE 2027 draft.

Hardcoded from HumanEval+ 164-task benchmark_report.json (2026-09-18).
Does not read outputs/, call APIs, or touch the runtime.
No SBES/MSR numbers.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent

# Per-cell task-mean with cluster-bootstrap 95% CIs (percent).
CELLS = [
    ("GPT-4o-mini\nT=0.0", {
        "Plus pass": (79.3, 73.0, 85.2),
        "same@2": (74.3, 67.9, 80.3),
        "same@2|cert": (93.7, 90.9, 96.1),
    }),
    ("GPT-4o-mini\nT=0.7", {
        "Plus pass": (79.7, 73.8, 85.2),
        "same@2": (48.9, 42.9, 54.8),
        "same@2|cert": (60.0, 54.4, 65.6),
    }),
    ("Claude 4.5\nT=0.0", {
        "Plus pass": (87.4, 82.3, 92.1),
        "same@2": (77.3, 71.8, 82.5),
        "same@2|cert": (88.4, 85.0, 91.5),
    }),
    ("Claude 4.5\nT=0.7", {
        "Plus pass": (86.8, 81.6, 91.7),
        "same@2": (63.2, 57.4, 68.9),
        "same@2|cert": (72.2, 67.0, 77.1),
    }),
]

PASS = "#4C78A8"
SAME = "#F58518"
CERT = "#54A24B"


def _yerr(point: float, lo: float, hi: float) -> tuple[float, float]:
    return (point - lo, hi - point)


def main() -> None:
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

    fig, ax = plt.subplots(figsize=(7.15, 3.05), layout="constrained")
    labels = [name for name, _ in CELLS]
    x = np.arange(len(labels))
    width = 0.24
    metrics = (
        ("Plus pass", PASS, ""),
        ("same@2|cert", CERT, "xx"),
        ("same@2", SAME, "//"),
    )
    offsets = (-width, 0.0, width)

    for offset, (metric, color, hatch) in zip(offsets, metrics):
        vals = [cell[metric][0] for _, cell in CELLS]
        err = np.array([_yerr(*cell[metric]) for _, cell in CELLS]).T
        ax.bar(
            x + offset,
            vals,
            width,
            label=metric,
            color=color,
            edgecolor="black",
            linewidth=0.4,
            hatch=hatch,
            yerr=err,
            capsize=2.0,
            error_kw={"elinewidth": 0.7, "capthick": 0.7},
        )

    ax.set_xticks(x, labels)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Task-mean (%)")
    ax.set_title("SameEval on HumanEval+ (164 tasks, N=20)")
    ax.legend(frameon=False, loc="lower left")
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, color="#bbbbbb")

    pdf = OUT / "fig1.pdf"
    png = OUT / "fig1.png"
    fig.savefig(pdf, bbox_inches="tight")
    fig.savefig(png, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {pdf}")
    print(f"wrote {png}")


if __name__ == "__main__":
    main()
