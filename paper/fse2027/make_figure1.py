"""Figure 1 for the FSE 2027 draft.

Hardcoded from Gate 0 CSVs and HumanEval+ table1.json / table2.json
(2026-09-02). Does not read outputs/, call APIs, or touch the runtime.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent

# Cluster-bootstrap 95% CIs (percent). Pairwise in panel (a) is MEASURE 1.
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

# HumanEval+ 30-task overall (task-mean, cluster by task).
HE_PRE = {
    "Plus pass": (80.5, 66.5, 92.8),
    "Pairwise (e2e)": (56.9, 44.6, 68.8),
    "Pairwise (cert.)": (67.4, 57.2, 77.0),
    "Match to human": (9.3, 0.0, 20.4),
}
HE_POST = {
    "Plus pass": (83.3, 70.0, 95.0),
    "Pairwise (e2e)": (75.9, 63.1, 87.4),
    "Pairwise (cert.)": (90.5, 84.3, 95.5),
    "Match to human": (9.3, 0.0, 20.4),
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
    ax.set_ylabel("End-to-end pairwise exact-match (%)")
    ax.set_title("(a) Contracted tasks (MEASURE 1)")
    ax.legend(frameon=False, loc="upper left", ncols=1)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.5, color="#bbbbbb")

    ax = axes[1]
    metrics = list(HE_PRE.keys())
    x = np.arange(len(metrics))
    width = 0.36
    pre_vals = [HE_PRE[m][0] for m in metrics]
    post_vals = [HE_POST[m][0] for m in metrics]
    pre_err = np.array([_yerr(*HE_PRE[m]) for m in metrics]).T
    post_err = np.array([_yerr(*HE_POST[m]) for m in metrics]).T

    ax.bar(
        x - width / 2,
        pre_vals,
        width,
        label="Table 1 (raw)",
        color=PRE,
        edgecolor="black",
        linewidth=0.4,
        yerr=pre_err,
        capsize=2.0,
        error_kw={"elinewidth": 0.7, "capthick": 0.7},
    )
    ax.bar(
        x + width / 2,
        post_vals,
        width,
        label="Table 2 (SKYT)",
        color=POST,
        edgecolor="black",
        linewidth=0.4,
        hatch="xx",
        yerr=post_err,
        capsize=2.0,
        error_kw={"elinewidth": 0.7, "capthick": 0.7},
    )
    ax.set_xticks(x, ["Plus\npass", "Pairwise\n(e2e)", "Pairwise\n(cert.)", "Match to\nhuman"])
    ax.set_ylim(0, 100)
    ax.set_ylabel("Task-mean (%)")
    ax.set_title("(b) HumanEval+ 30-task run")
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
