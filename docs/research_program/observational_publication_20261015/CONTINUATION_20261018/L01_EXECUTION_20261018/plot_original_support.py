"""Original selected-support response and retained finite-band magnitudes."""
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
    result = json.loads(args.result.read_text())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    singular = result["high_response"]["singular_values"]
    axes[0].plot(np.arange(1, len(singular)+1), singular, color="#172f51")
    axes[0].set(xlabel="Singular-value index", ylabel="Finite coefficient gain",
                title="Original 30,021-pixel support: ell6..8 → ell2..5")
    products = ("full", "hm1", "hm2", "oe1", "oe2")
    for j, (band, label, color) in enumerate((("low", "ell2..5", "#172f51"),
            ("mid", "ell6..8", "#c96823"), ("tail", "ell9..128", "#3b8b81"))):
        vals = [result["saved_L128_projections_on_original_selected_support"][p]["component_norms_K_CMB"][band]*1e9 for p in products]
        axes[1].bar(np.arange(5)+(j-1)*.25, vals, width=.24, color=color, label=label)
    total = [result["saved_L128_projections_on_original_selected_support"][p]["component_norms_K_CMB"]["total"]*1e9 for p in products]
    axes[1].plot(np.arange(5), total, "ko", ms=4, label="total norm")
    axes[1].set_xticks(np.arange(5), products)
    axes[1].set(ylabel="Selected-support coefficient norm [nK_CMB]",
                title="Saved L128 reconstructions; no new forward SHT")
    axes[1].legend(frameon=False, fontsize=9)
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.15)
    fig.suptitle("Finite processing response only: component norms do not add; ell>128 remains unbounded", fontsize=11)
    fig.tight_layout()
    for suffix in ("png", "pdf"):
        path = args.result.parent/("ORIGINAL_SELECTED_SUPPORT_RESPONSE."+suffix)
        if path.exists(): raise FileExistsError(path)
        fig.savefig(path, dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__": main()
