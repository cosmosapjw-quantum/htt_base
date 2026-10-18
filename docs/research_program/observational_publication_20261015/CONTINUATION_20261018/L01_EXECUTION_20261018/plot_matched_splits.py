"""Plot finite same-estimator contrasts and the measured processing angle."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--result", type=Path, required=True)
    args = ap.parse_args()
    data = json.loads(args.result.read_text())
    subjects = ("full", "HM_half_sum", "HM_half_difference", "OE_half_sum", "OE_half_difference",
                "full_minus_HM_mean", "full_minus_OE_mean")
    labels = ("Full", "HM mean", "HM diff / 2", "OE mean", "OE diff / 2", "Full − HM mean", "Full − OE mean")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={"width_ratios": [1.65, 1]})
    for j, (name, color) in enumerate((("all", "#172f51"), ("E", "#c96823"), ("B", "#3b8b81"))):
        values = data["matched_contrast"][name]["norms_nK_CMB"]
        axes[0].bar(np.arange(len(subjects))+(j-1)*.25, [values[s] for s in subjects],
                    width=.24, label=name, color=color)
        row = data["full_comparison"][name]
        low, high = row["previous_conditional_angle_interval_degrees"]
        actual = row["matched_vs_native_L128"]["angle_degrees"]
        axes[1].plot([low, high], [j, j], lw=7, alpha=.23, color=color)
        axes[1].plot(actual, j, "o", color=color, ms=8)
    axes[0].set_xticks(np.arange(len(subjects)), labels, rotation=28, ha="right")
    axes[0].set_ylabel("Matched inner − common contrast norm [nK_CMB]")
    axes[0].set_title("Same support, five delivered Planck products")
    axes[0].legend(frameon=False)
    axes[1].set_yticks([0, 1, 2], ["all", "E", "B"])
    axes[1].set_xlabel("Matched raw vs native L128 angle [degrees]")
    axes[1].set_title("Actual vectors (dots), prior bounds (bars)")
    axes[1].set_ylim(-.5, 2.5)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.15)
    fig.suptitle("Diagnostic only: one sky, correlated splits, finite coefficient geometry", fontsize=12)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        target = args.result.parent/("MATCHED_SPLIT_DIAGNOSTICS."+suffix)
        if target.exists(): raise FileExistsError(target)
        fig.savefig(target, dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__": main()
