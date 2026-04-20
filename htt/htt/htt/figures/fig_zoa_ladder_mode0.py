#!/usr/bin/env python3
"""
fig_zoa_ladder_mode0.py — Mode 0 ZoA ladder diagnostics
=======================================================
Figure F44 from ``BASS_PY_HTT_TSC_RESEARCH_PLAN.md``.

Plots the diagnostic ladder over Galactic plane cuts:
retention fraction, recovered bulk-flow amplitude, and axis instability
relative to the lowest-cut reference direction.
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

__all__ = ["load_zoa_ladder_artifact", "build_figure", "main"]

_OUTDIR = Path(os.environ.get("HTT_PIPELINE_OUTDIR", "/mnt/user-data/outputs"))


def load_zoa_ladder_artifact(
    outdir: str | os.PathLike[str] | None = None,
) -> dict:
    """Load the newest ``diag_zoa_ladder*.json`` artifact from a directory."""
    root = Path(outdir) if outdir is not None else _OUTDIR
    candidates = sorted(root.glob("diag_zoa_ladder*.json"))
    if not candidates:
        raise FileNotFoundError(f"no diag_zoa_ladder*.json found under {root}")
    with candidates[-1].open(encoding="utf-8") as fh:
        return json.load(fh)


def build_figure(artifact: dict):
    """Build the Mode 0 ZoA ladder figure without saving it."""
    apply_style()
    bcut = np.asarray(artifact["bcut_deg"], dtype=float)
    retention = np.asarray(artifact["retention_fraction"], dtype=float)
    amplitude = np.asarray(artifact["V_magnitude_kmps"], dtype=float)
    instability = np.asarray(artifact["axis_instability_deg"], dtype=float)
    threshold = artifact.get("stability_threshold_deg")

    fig, (ax_top, ax_bottom) = plt.subplots(
        2,
        1,
        figsize=(7.2, 5.8),
        sharex=True,
        height_ratios=(1.4, 1.0),
    )

    ax_top.plot(
        bcut,
        amplitude,
        marker="o",
        color=COLS["blue"],
        lw=1.6,
        label="|V_hat|",
    )
    ax_top.set_ylabel(r"$|\hat V|$ [km/s]")
    ax_top.grid(True, alpha=0.25)

    ax_ret = ax_top.twinx()
    ax_ret.plot(
        bcut,
        retention,
        marker="s",
        color=COLS["orange"],
        lw=1.2,
        label="retention",
    )
    ax_ret.set_ylabel("Retention fraction")
    ax_ret.set_ylim(0.0, 1.05)

    lines = ax_top.get_lines() + ax_ret.get_lines()
    labels = [line.get_label() for line in lines]
    ax_top.legend(lines, labels, loc="best", fontsize=9)

    ax_bottom.plot(
        bcut,
        instability,
        marker="D",
        color=COLS["green"],
        lw=1.4,
        label="axis instability",
    )
    if threshold is not None:
        ax_bottom.axhline(
            float(threshold),
            color=COLS["red"],
            ls="--",
            lw=1.0,
            label="stability threshold",
        )
    ax_bottom.set_xlabel(r"ZoA half-angle $b_{\rm cut}$ [deg]")
    ax_bottom.set_ylabel("Axis instability [deg]")
    ax_bottom.grid(True, alpha=0.25)
    ax_bottom.legend(loc="best", fontsize=9)

    stable = artifact.get("zoa_ladder_stable")
    max_instability = artifact.get("max_axis_instability_deg")
    title = "Mode 0 ZoA ladder"
    if stable is not None:
        title += f"  |  stable={stable}"
    if max_instability is not None:
        title += f", max drift={max_instability:.1f}°"
    fig.suptitle(title, fontsize=13)
    fig.tight_layout()
    return fig


def main() -> None:
    artifact = load_zoa_ladder_artifact()
    fig = build_figure(artifact)
    save_fig(fig, "fig_zoa_ladder_mode0")
    print("Saved fig_zoa_ladder_mode0.pdf + .png")


if __name__ == "__main__":
    main()
