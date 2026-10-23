"""Marker and cell plots of the conditional functional images; no interpolated chords."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
data = json.loads((HERE/"RESULT.json").read_text())
labels = data["functional_labels"]
mu = np.asarray(data["linear_image"]["mean_36"]).reshape(12, 3)
norm = np.linalg.norm(mu, axis=1)
outer = np.asarray(data["nonlinear_image"]["norm_outer_5x12x2"])

fig, ax = plt.subplots(figsize=(12, 5), layout="constrained")
for k in range(12):
    color = "#155e75" if k % 2 == 0 else "#a43e4c"
    ax.plot(k, norm[k], marker="o", color=color)
    ax.vlines(k, outer[1, k, 0], outer[1, k, 1], color=color, lw=2)
    ax.hlines([outer[1, k, 0], outer[1, k, 1]], k-.12, k+.12, color=color, lw=1.5)
ax.set_xticks(range(12), labels, rotation=55, ha="right")
ax.set_ylabel("vector norm (µas/year)")
ax.set_title("Reported-bin and contrast norm images · ρ=1 conservative outer intervals")
ax.text(.01, .99, "markers: fitted scenario points; bars: common full24 region\n"
        "true depth, calibrated law, physical MES: unavailable", transform=ax.transAxes,
        va="top", fontsize=9, bbox={"facecolor": "white", "alpha": .85, "edgecolor": "none"})
fig.savefig(HERE/"NORM_IMAGES.png", dpi=170)
plt.close(fig)

pi = np.asarray(data["nonlinear_image"]["empirical_strict_norm_Pi_12x6"])
ratios = [r["spectral_scale_ratio_full_to_zero"] for r in data["cross_depth_discriminator"]]
fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(14, 5), layout="constrained")
im = ax0.imshow(pi, vmin=0, vmax=1, aspect="auto", cmap="viridis", interpolation="nearest")
ax0.set_yticks(range(12), labels)
ax0.set_xticks(range(6), data["nonlinear_image"]["empirical_norm_thresholds_uasyr"])
ax0.set_xlabel("strict norm threshold (µas/year)")
ax0.set_title("Retained 4096-row law: empirical strict Pi")
fig.colorbar(im, ax=ax0, label="fraction of retained rows > threshold")
ax1.bar(range(6), ratios, color=["#155e75" if k % 2 == 0 else "#a43e4c" for k in range(6)])
ax1.axhline(1, color="black", lw=.8, ls="--")
ax1.set_xticks(range(6), [r["contrast"] for r in data["cross_depth_discriminator"]], rotation=55, ha="right")
ax1.set_ylabel("full / zero-cross spectral σ")
ax1.set_title("Cross-depth covariance matters (zero-cross is invalid)")
fig.text(.5, .005, "Computational scenario only · physical law, true depth and calibrated coverage unavailable",
         ha="center", fontsize=9)
fig.savefig(HERE/"EMPIRICAL_PI_AND_COVARIANCE.png", dpi=170)
plt.close(fig)
