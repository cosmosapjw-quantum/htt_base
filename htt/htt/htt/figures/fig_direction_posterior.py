#!/usr/bin/env python3
"""
fig_direction_posterior.py — Directional posterior on the sky
==============================================================
Mollweide projection showing the (l, b) posterior density from
IS-06 3D catalog sampling, with credible cones and reference
directions (CMB dipole, CatWISE, CF4).

Mode 2 upgrade
--------------
The figure now prefers the document-defined
``fiducial_posterior_bundle_vX.json`` artifact when available and falls
back to the legacy ``IS06_3D_posterior.npz`` fixture otherwise.
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
from scipy.stats import gaussian_kde

_CORE = Path(__file__).resolve().parent.parent / "core"
if _CORE.is_dir() and str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from plot_style import COLS, apply_style, save_fig

__all__ = ["load_direction_posterior", "build_figure", "main"]


# HTT_PIPELINE_OUTDIR overrides the legacy '/mnt/user-data/outputs'
# default so smoke tests can inject the repo-local synthetic fixture
# (bass_py/htt/tests/fixtures/pipeline_outputs/IS06_3D_posterior.npz)
# without depending on the original author mount.
_OUTDIR = Path(os.environ.get("HTT_PIPELINE_OUTDIR", "/mnt/user-data/outputs"))

# Truth (injection)
L_TRUE, B_TRUE = 264.0, 48.0

# Reference directions (Galactic coordinates)
REFS = {
    "CMB dipole": (264.0, 48.3, COLS["red"], "*", 12),
    "CatWISE": (240.5, 41.4, COLS["orange"], "s", 7),
    "CF4 bulk flow": (298.0, -8.0, COLS["green"], "D", 7),
    "Injected truth": (L_TRUE, B_TRUE, COLS["blue"], "o", 8),
}


def _bundle_candidates(outdir: Path) -> list[Path]:
    return sorted(outdir.glob("fiducial_posterior_bundle*.json"))


def _load_from_bundle(bundle_path: Path) -> tuple[np.ndarray, np.ndarray, str]:
    with bundle_path.open(encoding="utf-8") as fh:
        bundle = json.load(fh)
    summary = bundle.get("posterior_summary", bundle)
    lb_post = summary.get("lb_posterior")
    if not isinstance(lb_post, dict):
        raise KeyError(
            f"{bundle_path.name} is missing posterior_summary.lb_posterior"
        )
    if "l_deg" not in lb_post or "b_deg" not in lb_post:
        raise KeyError(
            f"{bundle_path.name} must contain lb_posterior.l_deg and .b_deg"
        )
    return (
        np.asarray(lb_post["l_deg"], dtype=float),
        np.asarray(lb_post["b_deg"], dtype=float),
        "fiducial_bundle",
    )


def _load_from_npz(outdir: Path) -> tuple[np.ndarray, np.ndarray, str]:
    data = np.load(outdir / "IS06_3D_posterior.npz", allow_pickle=True)
    if "l_rad" in data and "b_rad" in data:
        return (
            np.degrees(data["l_rad"]),
            np.degrees(data["b_rad"]),
            "legacy_npz_radians",
        )
    if "l" in data and "b" in data:
        return (
            np.asarray(data["l"], dtype=float),
            np.asarray(data["b"], dtype=float),
            "legacy_npz_degrees",
        )
    raise KeyError(
        "IS06_3D_posterior.npz must contain either (l_rad, b_rad) or (l, b)"
    )


def load_direction_posterior(
    outdir: str | os.PathLike[str] | None = None,
) -> tuple[np.ndarray, np.ndarray, str]:
    """Load the direction posterior from Mode 2 JSON or legacy NPZ."""
    root = Path(outdir) if outdir is not None else _OUTDIR
    for bundle_path in _bundle_candidates(root):
        return _load_from_bundle(bundle_path)
    return _load_from_npz(root)


def gal_to_moll(l_deg: np.ndarray, b_deg: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Convert Galactic (l, b) in degrees to Mollweide (lon, lat) in radians."""
    lon = np.where(l_deg > 180.0, l_deg - 360.0, l_deg)
    return np.radians(lon), np.radians(b_deg)


def ang_sep_deg(l1: np.ndarray, b1: np.ndarray, l2: float, b2: float) -> np.ndarray:
    """Great-circle separation in degrees."""
    l1r, b1r = np.radians(l1), np.radians(b1)
    l2r, b2r = np.radians(l2), np.radians(b2)
    cos_sep = (
        np.sin(b1r) * np.sin(b2r)
        + np.cos(b1r) * np.cos(b2r) * np.cos(l1r - l2r)
    )
    return np.degrees(np.arccos(np.clip(cos_sep, -1.0, 1.0)))


def build_figure(
    l_deg: np.ndarray,
    b_deg: np.ndarray,
    *,
    title_suffix: str = "",
):
    """Build the direction-posterior figure without saving it."""
    apply_style()
    l_shift = np.where(l_deg > 180.0, l_deg - 360.0, l_deg)
    b_shift = np.asarray(b_deg, dtype=float)
    med_l = float(np.median(l_shift))
    med_b = float(np.median(b_shift))
    seps = ang_sep_deg(l_shift, b_shift, med_l, med_b)
    cone_68 = float(np.percentile(seps, 68))
    cone_95 = float(np.percentile(seps, 95))

    has_kde = False
    try:
        kde = gaussian_kde(np.vstack([l_shift, b_shift]), bw_method=0.3)
        l_grid = np.linspace(l_shift.min() - 15.0, l_shift.max() + 15.0, 200)
        b_grid = np.linspace(b_shift.min() - 15.0, b_shift.max() + 15.0, 100)
        L_mg, B_mg = np.meshgrid(l_grid, b_grid)
        positions = np.vstack([L_mg.ravel(), B_mg.ravel()])
        Z = kde(positions).reshape(L_mg.shape)
        has_kde = True
    except Exception:
        pass

    fig = plt.figure(figsize=(7.0, 4.5))
    ax = fig.add_subplot(111, projection="mollweide")
    lon_samp, lat_samp = gal_to_moll(l_deg, b_deg)
    ax.scatter(
        lon_samp,
        lat_samp,
        s=0.3,
        alpha=0.15,
        color=COLS["blue"],
        rasterized=True,
        zorder=1,
    )

    if has_kde:
        lon_mg_rad = np.radians(L_mg)
        lat_mg_rad = np.radians(B_mg)
        levels = np.percentile(Z[Z > 0], [10, 40, 70, 90])
        ax.contour(
            lon_mg_rad,
            lat_mg_rad,
            Z,
            levels=levels,
            colors=COLS["blue"],
            linewidths=[0.4, 0.6, 0.8, 1.0],
            alpha=0.7,
            zorder=2,
        )
        ax.contourf(
            lon_mg_rad,
            lat_mg_rad,
            Z,
            levels=[levels[-1], Z.max() * 2.0],
            colors=[COLS["blue"]],
            alpha=0.15,
            zorder=1,
        )

    lon_med, lat_med = gal_to_moll(
        np.array([med_l + (360.0 if med_l < 0.0 else 0.0)]),
        np.array([med_b]),
    )
    ax.plot(lon_med, lat_med, "+", ms=10, mew=1.5, color=COLS["blue"], zorder=8)

    for name, (l_ref, b_ref, color, marker, ms) in REFS.items():
        lon_r, lat_r = gal_to_moll(np.array([l_ref]), np.array([b_ref]))
        ax.plot(
            lon_r,
            lat_r,
            marker=marker,
            ms=ms,
            color=color,
            markeredgecolor="k",
            markeredgewidth=0.4,
            zorder=10,
            label=f"{name} ({l_ref:.0f}°, {b_ref:.0f}°)",
        )

    median_l = med_l + 360.0 if med_l < 0.0 else med_l
    ax.text(
        0.02,
        0.02,
        f"68% cone: {cone_68:.0f}°\n95% cone: {cone_95:.0f}°\n"
        f"Median: ({median_l:.0f}°, {med_b:.0f}°)",
        transform=ax.transAxes,
        fontsize=8,
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor="white",
            edgecolor=COLS["gray"],
            alpha=0.9,
        ),
        va="bottom",
        zorder=15,
    )
    ax.grid(True, alpha=0.3, lw=0.4)
    ax.set_xlabel("Galactic longitude $l$", fontsize=10, labelpad=5)
    ax.set_ylabel("Galactic latitude $b$", fontsize=10)
    title = "Direction posterior"
    if title_suffix:
        title = f"{title} ({title_suffix})"
    ax.set_title(title, fontsize=12)
    ax.legend(
        fontsize=7.5,
        loc="upper right",
        framealpha=0.9,
        markerscale=1.0,
        handletextpad=0.3,
    )
    fig.tight_layout()
    return fig


def main() -> None:
    l_deg, b_deg, source = load_direction_posterior()
    fig = build_figure(l_deg, b_deg, title_suffix=source)
    save_fig(fig, "fig_direction_posterior")
    print("Saved fig_direction_posterior.pdf + .png")


if __name__ == "__main__":
    main()
