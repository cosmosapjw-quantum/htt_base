"""Plot stored conditional tensor intervals; never rerun an upstream fit."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
d = json.loads((HERE / "RESULT.json").read_text())
scenarios = list(d["scenarios"])
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
palette = {"B_optical_STF": "#1b6ca8", "C_union": "#c05a32"}
for j, name in enumerate(palette):
    point = [d["scenarios"][s]["models"][name]["point_norm_sigma_eff_over_H"] for s in scenarios]
    top = [d["scenarios"][s]["models"][name]["reference_region"]["norm_sigma_eff_over_H_interval"][1] for s in scenarios]
    xx = np.arange(4) + (j-.5)*.14
    ax[0].errorbar(xx, point, yerr=[point, np.subtract(top, point)], fmt="o", capsize=3,
                   color=palette[name], label=name.replace("_", " "))
    radii = d["scenario_remainder_radii_L2_h2_over_H"]
    for s in scenarios:
        rows = d["scenarios"][s]["models"][name]["remainder_sensitivity"]
        ax[1].plot(radii, [r["conditional_sigma2_upper"] for r in rows],
                   color=palette[name], alpha=.5, lw=1.5)
ax[0].set_xticks(range(4), [s.replace("a_", "a=").replace("_b_", "\nb=") for s in scenarios])
ax[0].set_ylabel(r"$\|\sigma_{\rm eff}/H\|_F$ scenario")
ax[0].set_title("Five-coordinate tensor image\nzero belongs to every reference ellipsoid")
ax[0].legend(fontsize=8)
ax[0].grid(alpha=.2)
ax[1].set_xlabel(r"Declared remainder radius $r$ in full-sky $L^2(h_2/H)$")
ax[1].set_ylabel(r"Upper scenario bound for $\Sigma_{\rm eff}^2$")
ax[1].set_title("All lower bounds are zero\ncurves: four covariance scenarios per model")
ax[1].grid(alpha=.2)
fig.suptitle("Conditional optical STF analysis · fixed-law plug-in reference; no physical G shear or 95% coverage", fontsize=11)
fig.savefig(HERE / "OPTICAL_SHEAR.png", dpi=180)
fig.savefig(HERE / "OPTICAL_SHEAR.pdf")
