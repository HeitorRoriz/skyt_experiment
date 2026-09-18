"""Figure 1 for the FSE 2027 draft.

Hardcoded from Gate 0 CSVs and HumanEval+ 164-task benchmark_report.json
(2026-09-18). Does not read outputs/, call APIs, or touch the runtime.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent

# Cluster-bootstrap 95% CIs (percent). Panel (a) is same@2.
MSR_E2E = {
    "raw": (61.0, 46.3, 74.6),
    "first_valid": (67.4, 56.2, 78.5),
    "consensus": (77.2, 60.7, 90.4),
}
SBES_E2E = {
    "raw": (67.5, 53.8, 81.0),
    "first_valid": (73.2, 61.4, 84.4),
    "consensus": (85.2, 73.2, 93.3),
}

# HumanEval+ 164-task overlay overall (task-mean, cluster by task, N=20).
HE_164 = {
    "Plus pass": (83.3, 78.3, 88.0),
    "same@2": (65.9, 61.0, 70.6),
    "same@2|cert": (76.6, 73.0, 80.0),
}

RAW = "#4C78A8"
FIRST = "#F58518"
CONS = "#54A24B"
PRE = "#4C78A8"
POST = "#54A24B"


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

    fig, axes = plt.subplots(1, 2, figsize=(7.15, 3.05), layout="constrained")

    ax = axes[0]
    policies = ("raw", "first_valid", "consensus")
    labels = ("Raw", "First-valid", "Consensus")
    colors = (RAW, FIRST, CONS)
    hatches = ("", "//", "xx")
    x = np.arange(2)
    width = 0.24
    offsets = (-width, 0.0, width)
    group_names = ("MSR (15 tasks)", "SBES (12 contracts)")
    series = (MSR_E2E, SBES_E2E)

    for i, (key, lab, color, hatch) in enumerate(zip(policies, labels, colors, hatches)):
        vals = [series[g][key][0] for g in range(2)]
        err = np.array([_yerr(*series[g][key]) for g in range(2)]).T
        ax.bar(
            x + offsets[i],
            vals,
            width,
            label=lab,
            color=color,
            edgecolor="black",
            linewidth=0.4,
            hatch=hatch,
            yerr=err,
            capsize=2.0,
            error_kw={"elinewidth": 0.7, "capthick": 0.7},
        )

    ax.set_xticks(x, group_names)
    ax.set_ylim(0, 100)
    ax.set_ylabel("same@2 (%)")
    ax.set_title("(a) Contracted tasks")
    ax.legend(frameon=False, loc="upper left", ncols=1)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, color="#bbbbbb")

    ax = axes[1]
    metrics = list(HE_164.keys())
    x = np.arange(len(metrics))
    width = 0.55
    vals = [HE_164[m][0] for m in metrics]
    err = np.array([_yerr(*HE_164[m]) for m in metrics]).T

    ax.bar(
        x,
        vals,
        width,
        label="overlay",
        color=PRE,
        edgecolor="black",
        linewidth=0.4,
        yerr=err,
        capsize=2.0,
        error_kw={"elinewidth": 0.7, "capthick": 0.7},
    )
    ax.set_xticks(x, ["Plus\npass", "same@2", "same@2\n|cert"])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Task-mean (%)")
    ax.set_title("(b) SameEval on HumanEval+ (164 tasks, N=20)")
    ax.legend(frameon=False, loc="upper left")
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
