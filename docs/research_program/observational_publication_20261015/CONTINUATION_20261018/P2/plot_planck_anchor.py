"""Render exact computed finite geometry, never a probability interval."""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

root = Path(__file__).resolve().parent
result = json.loads((root / "results/PLANCK_ANCHOR_GEOMETRY_20261018.json").read_text())
groups = result["groups"]
all_block = result["all_refined_using_orthogonal_E_B_blocks"]
labels = ["All (E/B constrained)", "E", "B"]
records = [all_block, groups["E"], groups["B"]]
colors = ["#1d3557", "#287f8e", "#a23b58"]
fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.3), layout="constrained")
for y, row, color in zip(range(3), records, colors):
    lo, hi = row["matched_reconstructed_angle_degrees_interval"]
    axes[0].plot([lo, hi], [y, y], color=color, linewidth=5, solid_capstyle="butt")
    axes[0].scatter([lo, hi], [y, y], color=color, s=25)
    axes[0].text(hi+1, y, f"{lo:.2f}–{hi:.2f}°", va="center", fontsize=9)
    lower = 100*row["best_nonnegative_scalar_residual_fraction_lower"]
    axes[1].barh(y, lower, color=color, height=.45)
    axes[1].text(lower+1, y, f"≥ {lower:.2f}%", va="center", fontsize=9)
for ax in axes:
    ax.set_yticks(range(3), labels)
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", alpha=.15)
    ax.set_axisbelow(True)
axes[0].set_xlim(0, 105)
axes[0].set_xlabel("Matched vs. original L128 coefficient angle")
axes[1].set_xlim(0, 105)
axes[1].set_xlabel("Best scalar-fit residual / matched norm (%)")
fig.suptitle("Planck SMICA: finite estimator geometry", fontsize=14)
fig.supxlabel("Conditional geometric bounds from committed real-data summaries; not confidence intervals", fontsize=9)
for extension in ("png", "svg"):
    fig.savefig(root / "results" / ("PLANCK_ANCHOR_GEOMETRY_20261018."+extension), dpi=180)
