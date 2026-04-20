#!/usr/bin/env python3
"""
fig_retention_fraction_vs_posterior.py — ZoA retention vs fiducial drift
========================================================================
Figure F102 from ``BASS_PY_HTT_TSC_RESEARCH_PLAN.md``.

Loads ``retention_vs_posterior_vX.json`` and plots how the Mode 0 ladder
direction drifts away from the Mode 2 fiducial posterior as retained sky
fraction changes.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_CORE = Path(__file__).resolve().parent.parent / "core"
if _CORE.is_dir() and str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from plot_style import COLS, apply_style, save_fig

__all__ = ["load_retention_vs_posterior_artifact", "build_figure", "main"]

_OUTDIR = Path(os.environ.get("HTT_PIPELINE_OUTDIR", "/mnt/user-data/outputs"))


def load_retention_vs_posterior_artifact(
    outdir: str | os.PathLike[str] | None = None,
) -> dict:
    """Load the newest ``retention_vs_posterior*.json`` artifact."""
    root = Path(outdir) if outdir is not None else _OUTDIR
    candidates = sorted(root.glob("retention_vs_posterior*.json"))
    if not candidates:
        raise FileNotFoundError(
            f"no retention_vs_posterior*.json found under {root}"
        )
    with candidates[-1].open(encoding="utf-8") as fh:
        return json.load(fh)


def build_figure(artifact: dict):
    """Build the retention-vs-posterior figure without saving it."""
    apply_style()
    retention = np.asarray(artifact["retention_fraction"], dtype=float)
    shift = np.asarray(artifact["posterior_shift_deg"], dtype=float)
    bcut = np.asarray(artifact["bcut_deg"], dtype=float)
    cone_68 = float(artifact["credible_cone_68_deg"])
    cone_95 = float(artifact["credible_cone_95_deg"])

    valid = np.isfinite(retention) & np.isfinite(shift)
    fig, ax = plt.subplots(figsize=(7.0, 4.8))
    if np.any(valid):
        order = np.argsort(retention[valid])
        ax.plot(
            retention[valid][order],
            shift[valid][order],
            color=COLS["blue"],
            lw=1.3,
            alpha=0.7,
            zorder=1,
        )
        sc = ax.scatter(
            retention[valid],
            shift[valid],
            c=bcut[valid],
            cmap="viridis",
            s=44,
            edgecolors="white",
            linewidths=0.5,
            zorder=3,
        )
        cbar = fig.colorbar(sc, ax=ax, pad=0.02)
        cbar.set_label(r"$b_{\rm cut}$ [deg]")

    ax.axhline(
        cone_68,
        color=COLS["orange"],
        ls="--",
        lw=1.2,
        label="68% cone",
    )
    ax.axhline(
        cone_95,
        color=COLS["red"],
        ls=":",
        lw=1.2,
        label="95% cone",
    )
    ax.set_xlabel("Retention fraction")
    ax.set_ylabel("Shift from fiducial axis [deg]")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=9)

    corr = artifact.get("correlation_retention_vs_shift")
    title = "Retention vs fiducial posterior drift"
    if corr is not None:
        title += f"  |  corr={corr:.2f}"
    ax.set_title(title, fontsize=12)
    fig.tight_layout()
    return fig


def main() -> None:
    artifact = load_retention_vs_posterior_artifact()
    fig = build_figure(artifact)
    save_fig(fig, "fig_retention_fraction_vs_posterior")
    print("Saved fig_retention_fraction_vs_posterior.pdf + .png")


if __name__ == "__main__":
    main()
