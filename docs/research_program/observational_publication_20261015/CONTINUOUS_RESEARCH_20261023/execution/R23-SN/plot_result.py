"""Render the stored R23-SN result; no model construction or refitting."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
RESULT = HERE / "RESULT.json"
OLD_CONFIG = HERE.parents[2] / "ADVERSARIAL_AUDIT_20261022/continuation/sn010010/CONFIG.json"


def inputs():
    result = json.loads(RESULT.read_text())
    config = json.loads(OLD_CONFIG.read_text())
    digest = hashlib.sha256(OLD_CONFIG.read_bytes()).hexdigest()
    if digest != result["input_sha256"]["old_config"]:
        raise ValueError("frozen parity-bound config identity changed")
    if result["task_id"] != "R23-SN" or result["claim_tier"] != "C0_PUBLIC_MODEL_CONDITIONAL_RESPONSE":
        raise ValueError("unexpected result identity or claim tier")
    if result["original_baseline"]["adequacy"] != "BASELINE_ADEQUACY_HOLD":
        raise ValueError("original failed baseline missing")
    if result["public_modelcov_fit"]["published_parity"] != "NOT_REPRODUCED":
        raise ValueError("published parity state changed")
    return result, config


def make_figure():
    result, config = inputs()
    old = result["original_baseline"]
    public = result["public_modelcov_fit"]
    defects = public["published_defects"]
    bounds = config["published_parity_tolerances"]
    keys = ("x0_relative", "x1", "c", "t0_day")
    ratios = np.array([defects[k] / bounds[k] for k in keys])
    if not np.isfinite(ratios).all() or any(abs(v) <= 1 for v in ratios):
        raise ValueError("stored four-way parity failure not reproduced")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(12.5, 7.4),
                                   gridspec_kw={"height_ratios": [1, 1.35]})
    fig.subplots_adjust(left=.24, right=.96, top=.83, bottom=.15, hspace=.46)
    fig.suptitle("SN010010: retained baseline and public model-covariance diagnostic",
                 fontsize=15, weight="bold", y=.97)
    fig.text(.5, .915, "HTT  |  C0 conditional public MODEL000  |  NOT nominal producer FITRES",
             ha="center", fontsize=10, color="#374151")

    values = [old["reduced_chi2"], public["reduced_chi2"]]
    names = ["Original measurement-only\nBASELINE_ADEQUACY_HOLD",
             "Public MODEL000 covariance\nIRLS fixed point (conditional)"]
    ax0.barh([1, 0], values, height=.5, color=["#b44443", "#198789"])
    ax0.set_yticks([1, 0], names)
    ax0.axvline(config["working_fit_quality_max_reduced_chi2"],
                color="#1f2937", linestyle="--", linewidth=1.5,
                label="Frozen adequacy threshold = 3")
    for i, value in enumerate(values):
        ax0.text(value + .08, 1 - i, f"{value:.4f}", va="center", weight="bold")
    ax0.set_xlim(0, 3.9)
    ax0.set_xlabel(r"Fit $\chi^2/19$ (same 23 frozen photometry rows)")
    ax0.legend(loc="lower right", frameon=False, fontsize=9)
    ax0.grid(axis="x", alpha=.2)
    ax0.set_axisbelow(True)

    labels = [r"$\Delta x_0/x_{0,\mathrm{pub}}$  (bound 0.1%)",
              r"$\Delta x_1$  (bound 0.001)",
              r"$\Delta c$  (bound 0.001)",
              r"$\Delta t_0$  (bound 0.01 d)"]
    positions = np.arange(4)[::-1]
    ax1.axvspan(-1, 1, color="#dbeedc", alpha=.95, label="Frozen parity band")
    ax1.axvline(-1, color="#64748b", linewidth=1)
    ax1.axvline(1, color="#64748b", linewidth=1)
    ax1.axvline(0, color="#475569", linewidth=.8)
    ax1.barh(positions, ratios, height=.55, color="#b44443")
    ax1.set_yticks(positions, labels)
    ax1.set_xlim(-22.5, 22.5)
    ax1.set_xticks([-20, -15, -10, -5, -1, 0, 1, 5, 10, 15, 20])
    ax1.set_xlabel("Signed parameter difference / frozen absolute parity bound")
    ax1.grid(axis="x", alpha=.17)
    ax1.set_axisbelow(True)
    ax1.legend(loc="upper right", frameon=False, fontsize=9)
    for y, ratio in zip(positions, ratios):
        if ratio < -15:
            x, align, color = ratio + .55, "left", "white"
        elif ratio < 0:
            x, align, color = ratio - .4, "right", "black"
        else:
            x, align, color = ratio + .4, "left", "black"
        ax1.text(x, y, f"{ratio:+.2f} × bound", va="center", ha=align,
                 fontsize=9, weight="bold", color=color)

    fig.text(.5, .075,
             "PARITY_NOT_REPRODUCED / scientific HOLD. Public IRLS is not a normalized "
             "parameter-dependent Gaussian MLE.",
             ha="center", color="#9b292b", fontsize=10, weight="bold")
    fig.text(.5, .045,
             "Source: stored R23-SN/RESULT.json and frozen CONFIG.json; no refit. "
             "Missing nominal PS1.nml, trained model binding and observed FITRES.",
             ha="center", color="#475569", fontsize=8.5)

    for ext in ("png", "pdf"):
        metadata = {"Title": "R23-SN conditional public model-covariance diagnostic",
                    "Author": "HTT research program"}
        if ext == "pdf":
            metadata["CreationDate"] = datetime(2026, 10, 23, tzinfo=timezone.utc)
            metadata["ModDate"] = datetime(2026, 10, 23, tzinfo=timezone.utc)
        fig.savefig(HERE / f"BASELINE_PARITY.{ext}", dpi=180,
                    facecolor="white", metadata=metadata)
    plt.close(fig)


if __name__ == "__main__":
    make_figure()
