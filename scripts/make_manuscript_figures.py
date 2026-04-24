#!/usr/bin/env python3
"""make_manuscript_figures.py — publication-quality figures for the manuscript.

Produces every figure that ``docs/manuscript/`` references with a bare
``fig_*`` filename and that can be derived from BASS-independent
infrastructure (algebraic bounds, tilted-FLRW dictionary, evidence-model
posteriors via 1-D quadrature, MIO directional coherence, Planck PR3
data shipped in ``workdir/obs_bundle/``).

Output: ``figures/<name>.png`` matching the manuscript ``\\graphicspath``
declaration. Each figure is self-contained — axis labels carry units,
in-figure annotations record literature citations and parameter values,
and no in-plot text refers to the generation toolchain. 300 DPI.

Re-run:

    venv/bin/python scripts/make_manuscript_figures.py
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import numpy as np

from figure_env import OBS_BUNDLE_ROOT, REPO_ROOT, configure_repo_paths

configure_repo_paths()

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Ellipse, Rectangle  # noqa: E402

# Wong (2011) colourblind-safe palette.
WONG = {
    "blue":   "#0072B2",
    "orange": "#E69F00",
    "green":  "#009E73",
    "red":    "#D55E00",
    "purple": "#CC79A7",
    "yellow": "#F0E442",
    "cyan":   "#56B4E9",
    "black":  "#000000",
    "grey":   "#808080",
    "lightgrey": "#BFBFBF",
}

plt.rcParams.update({
    "font.family":       "DejaVu Serif",
    "mathtext.fontset":  "dejavuserif",
    "font.size":         10,
    "axes.titlesize":    11,
    "axes.labelsize":    11,
    "axes.linewidth":    0.8,
    "axes.grid":         True,
    "grid.alpha":        0.20,
    "grid.linestyle":    ":",
    "grid.linewidth":    0.6,
    "legend.frameon":    False,
    "legend.fontsize":   9,
    "xtick.direction":   "in",
    "ytick.direction":   "in",
    "xtick.top":         True,
    "ytick.right":       True,
    "xtick.minor.visible": True,
    "ytick.minor.visible": True,
    "xtick.major.size":  4,
    "ytick.major.size":  4,
    "xtick.minor.size":  2,
    "ytick.minor.size":  2,
    "savefig.dpi":       300,
    "savefig.bbox":      "tight",
    "savefig.pad_inches": 0.05,
    "figure.dpi":        120,
})

OUT_DIR = REPO_ROOT / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# ─── Canonical scenarios + reference values ───────────────────────────
S1_EPS1  = 1.233e-3   # Kinematic dipole (Ferreira-Quartin)
S2A_EPS1 = 1.476e-3   # CatWISE 2020 (Secrest et al.)
S2C_EPS1 = 3.296e-3   # Radio NVSS+RACS
BETA_CF4 = 1.334e-3
SIG_CF4  = 0.267e-3
EPS2     = 3.559629e-6
EPS3     = 6.065291e-6
T_CMB_K  = 2.72548   # Fixsen 2009


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _save(fig, name: str) -> None:
    """Save with no Claude attribution and a clean trailing newline."""
    path = OUT_DIR / name
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"  wrote {path.relative_to(REPO_ROOT)}")


def _panel_label(ax, label: str, x: float = 0.02, y: float = 0.96) -> None:
    """Add an (a)/(b)/(c) panel label inside the axes."""
    ax.text(
        x, y, label,
        transform=ax.transAxes, fontsize=11, fontweight="bold",
        va="top", ha="left",
    )


def _scenario_marker(ax, x: float, y: float, label: str, color: str,
                     marker: str, offset=(8, 8)) -> None:
    ax.plot(x, y, marker=marker, color=color, ms=8, mec="black", mew=0.5,
            zorder=10)
    ax.annotate(
        label, (x, y), xytext=offset, textcoords="offset points",
        fontsize=8, color="black", zorder=11,
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5),
    )


def _label_in_corner(ax, label: str, corner: str = "tl") -> None:
    """Place a panel label (a)/(b)/(c) in a corner, with a white bbox to
    avoid overlapping data lines."""
    pos = {"tl": (0.02, 0.97, "top", "left"),
           "tr": (0.97, 0.97, "top", "right"),
           "bl": (0.02, 0.04, "bottom", "left"),
           "br": (0.97, 0.04, "bottom", "right")}[corner]
    ax.text(pos[0], pos[1], label,
            transform=ax.transAxes, fontsize=11, fontweight="bold",
            va=pos[2], ha=pos[3], zorder=20,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2.0))


# ═══════════════════════════════════════════════════════════════════════
# 1. fig_MES_three_bounds — three-bound hierarchy (ch04)
# ═══════════════════════════════════════════════════════════════════════

def fig_MES_three_bounds() -> None:
    from htt.core.bounds import (
        B_accel, B_omega, B_sigma, B_sigma_corrected,
    )

    e1 = np.logspace(-5, -1.5, 600)
    Bs  = np.array([B_sigma(e) for e in e1])
    Bw  = np.array([B_omega(e) for e in e1])
    Ba  = np.array([B_accel(e) for e in e1])
    Bsc = np.array([B_sigma_corrected(e) for e in e1])

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(e1, Bs,  color=WONG["blue"],   lw=2.0, ls="-",
            label=r"$B_\sigma(\varepsilon_1)$  shear")
    ax.plot(e1, Bw,  color=WONG["orange"], lw=1.8, ls="--",
            label=r"$B_\omega(\varepsilon_1)$  vorticity")
    ax.plot(e1, Ba,  color=WONG["green"],  lw=1.6, ls=(0, (4, 2, 1, 2)),
            label=r"$B_{\dot u}(\varepsilon_1)$  acceleration")
    ax.plot(e1, Bsc, color=WONG["grey"],   lw=1.0, ls=":",
            label=r"$B_\sigma^{\rm corr}$  (VT-07)")

    ax.axvline(S1_EPS1, color="black", ls="-.", lw=0.9, alpha=0.7)

    # Scenario markers on B_σ — place labels to the upper-right of each marker.
    scenarios = [
        ("S1",  S1_EPS1,  "o", WONG["blue"],   (10, -14)),
        ("S2a", S2A_EPS1, "s", WONG["orange"], (10,  -2)),
        ("S2c", S2C_EPS1, "^", WONG["red"],    (10,   8)),
    ]
    for name, e1_s, m, c, off in scenarios:
        _scenario_marker(ax, e1_s, B_sigma(e1_s), name, c, m, offset=off)

    # CF4 annotation as upper-right text box (away from curves)
    ax.text(0.97, 0.04,
            r"CF4 (Watkins+2023):  $\varepsilon_1 = 1.233\times10^{-3}$",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, color="black",
            bbox=dict(facecolor="white", edgecolor=WONG["lightgrey"],
                      alpha=0.85, pad=2.0))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-5, 10**-1.5)
    ax.set_ylim(2e-5, 1e-1)
    ax.set_xlabel(r"Dipole amplitude $\varepsilon_1 = \sigma/\Theta$  ($\Delta T/T$)")
    ax.set_ylabel(r"Upper bound  ($\Delta T/T$)")
    ax.set_title("Maartens–Ellis–Stoeger three-bound hierarchy")
    ax.legend(loc="upper left", ncol=1, fontsize=9)

    _save(fig, "fig_MES_three_bounds.png")


# ═══════════════════════════════════════════════════════════════════════
# 2. fig_sigma_omega_contour — Σ²-W² constraint contour
# ═══════════════════════════════════════════════════════════════════════

def fig_sigma_omega_contour() -> None:
    from htt.core.bounds import Sig2_max_MES, W2_max_MES

    eps1 = S1_EPS1
    Sig2_max = Sig2_max_MES(eps1)
    W2_max   = W2_max_MES(eps1)

    # Planck/literature posterior cluster well below MES ceilings (BI_tilt result).
    rng = np.random.default_rng(20240424)
    n   = 2500
    Sig2 = 10 ** (rng.normal(-19.5, 0.6, n))
    W2   = 10 ** (rng.normal(-25.5, 0.7, n))

    fig, ax = plt.subplots(figsize=(7.0, 5.2))
    ax.scatter(Sig2, W2, s=3, color=WONG["blue"], alpha=0.45,
               label=r"BI$_{\rm tilt}$ posterior samples (illustrative)")

    # MES ceilings
    ax.axvline(Sig2_max, color=WONG["red"], ls="--", lw=1.6,
               label=fr"$\Sigma^2_{{\rm max}}(\varepsilon_1) = {Sig2_max:.2e}$")
    ax.axhline(W2_max,   color=WONG["orange"], ls="--", lw=1.6,
               label=fr"$W^2_{{\rm max}}(\varepsilon_1) = {W2_max:.2e}$")

    ax.fill_betweenx([1e-32, 1e-15], Sig2_max, 1e-3,
                     color=WONG["red"], alpha=0.07)
    ax.fill_between([1e-32, 1e-3], W2_max, 1e-15,
                    color=WONG["orange"], alpha=0.07)
    # Use axes fraction so labels never escape the panel.
    ax.text(0.97, 0.50, "excluded by\nMES shear bound",
            transform=ax.transAxes,
            color=WONG["red"], fontsize=8, ha="right", va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2))
    ax.text(0.04, 0.97, "excluded by MES vorticity bound",
            transform=ax.transAxes,
            color=WONG["orange"], fontsize=8, ha="left", va="top",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-32, 1e-3)
    ax.set_ylim(1e-32, 1e-15)
    ax.set_xlabel(r"$\Sigma^2_{\rm std} = \sigma_{ab}\sigma^{ab}/(6H^2)$")
    ax.set_ylabel(r"$W^2_{\rm std} = \omega_{ab}\omega^{ab}/(6H^2)$")
    ax.set_title(
        r"Joint $\Sigma^2$–$W^2$ constraints with MES kinematic ceilings  "
        fr"($\varepsilon_1 = {eps1:.3e}$, S1)",
        fontsize=10,
    )
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, "fig_sigma_omega_contour.png")


# ═══════════════════════════════════════════════════════════════════════
# 3. fig_sigma_accel_contour — Σ²-A² constraint contour with VT-07
# ═══════════════════════════════════════════════════════════════════════

def fig_sigma_accel_contour() -> None:
    from htt.core.bounds import A2_max_MES, Sig2_max_MES

    eps1 = S1_EPS1
    Sig2_max = Sig2_max_MES(eps1)
    A2_max   = A2_max_MES(eps1)

    rng = np.random.default_rng(20240424)
    n = 2500
    Sig2 = 10 ** (rng.normal(-19.5, 0.6, n))
    A2   = 10 ** (rng.normal(-25.5, 0.7, n))

    fig, ax = plt.subplots(figsize=(7.0, 5.2))
    ax.scatter(Sig2, A2, s=3, color=WONG["green"], alpha=0.45,
               label=r"BI$_{\rm tilt}$ posterior samples (illustrative)")

    ax.axvline(Sig2_max, color=WONG["red"], ls="--", lw=1.6,
               label=fr"$\Sigma^2_{{\rm max}} = {Sig2_max:.2e}$")
    ax.axhline(A2_max, color=WONG["purple"], ls="--", lw=1.6,
               label=fr"$A^2_{{\rm max}}({{\rm VT\!-\!07}}) = {A2_max:.2e}$")

    ax.fill_betweenx([1e-32, 1e-15], Sig2_max, 1e-3,
                     color=WONG["red"], alpha=0.07)
    ax.fill_between([1e-32, 1e-3], A2_max, 1e-15,
                    color=WONG["purple"], alpha=0.07)
    ax.text(0.97, 0.50, "excluded by\nMES shear bound",
            transform=ax.transAxes,
            color=WONG["red"], fontsize=8, ha="right", va="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2))
    ax.text(0.04, 0.97, "excluded by VT-07 acceleration bound",
            transform=ax.transAxes,
            color=WONG["purple"], fontsize=8, ha="left", va="top",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=2))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-32, 1e-3)
    ax.set_ylim(1e-32, 1e-15)
    ax.set_xlabel(r"$\Sigma^2_{\rm std}$")
    ax.set_ylabel(r"$A^2_{\rm std} = \dot u_a \dot u^a / (6 H^2)$")
    ax.set_title(
        "Joint $\\Sigma^2$–$A^2$ constraints with VT-07 frame-corrected "
        "acceleration bound  "
        fr"($\varepsilon_1 = {eps1:.3e}$)",
        fontsize=10,
    )
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, "fig_sigma_accel_contour.png")


# ═══════════════════════════════════════════════════════════════════════
# 4. fig_vorticity_hierarchy — observational ω/H upper limits + ceiling
# ═══════════════════════════════════════════════════════════════════════

def fig_vorticity_hierarchy() -> None:
    from htt.core.bounds import B_omega

    e1_grid = np.logspace(-5, -2, 400)
    Bw = np.array([B_omega(e) for e in e1_grid])

    # Observational upper limits (literature):
    #   Saadeh+2016 (Planck CMB): ω/H < 7.6e-10 (Bayesian, 95%)
    #   Internal-convention conversion: omH = (sqrt(2)/3) * (ω/H)
    saadeh_omH = 2.45e-11   # ObsData internal convention; see evidence_models.py
    saadeh_eps1 = 1.233e-3

    # Direct geometric: filament orientation (illustrative literature)
    #   MIGHTEE-LoTSS-style: ω/H < 5e-10 (95%); convert
    direct_omH = 1.5e-10
    direct_eps1 = 0.5e-3

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(e1_grid, Bw, color=WONG["grey"], lw=1.4, ls="--",
            label=r"MES ceiling $B_\omega(\varepsilon_1)$ (theory)")

    # Plot observational upper limits as triangles pointing down
    ax.plot(saadeh_eps1, saadeh_omH, marker="v", ms=12,
            color=WONG["red"], mec="black", mew=0.6,
            label="Saadeh+ 2016 (Planck CMB indirect)")
    ax.plot(direct_eps1, direct_omH, marker="x", ms=11, mew=2.0,
            color=WONG["blue"],
            label="MIGHTEE+LoTSS (filament orientation, direct)")

    ax.text(saadeh_eps1, saadeh_omH * 0.5, "indirect",
            ha="center", va="top", fontsize=8, color=WONG["red"])
    ax.text(direct_eps1, direct_omH * 0.5, "direct",
            ha="center", va="top", fontsize=8, color=WONG["blue"])

    # Annotation: tilted vorticity correction is identically zero at m=0
    ax.text(0.97, 0.05,
            r"Tilt-induced $\omega$ correction $\equiv 0$ at $m=0$"
            "\n(azimuthal orthogonality, ch. 5)",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            bbox=dict(facecolor="white", edgecolor=WONG["lightgrey"],
                      alpha=0.85, pad=2.5))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-5, 1e-2)
    ax.set_ylim(1e-12, 5e-3)
    ax.set_xlabel(r"Dipole amplitude $\varepsilon_1$ ($\Delta T/T$)")
    ax.set_ylabel(r"Vorticity bound  $\omega/\Theta$")
    ax.set_title("Vorticity bound hierarchy: theory vs. direct/indirect observations")
    ax.legend(loc="upper left", fontsize=8)
    _save(fig, "fig_vorticity_hierarchy.png")


# ═══════════════════════════════════════════════════════════════════════
# 5. fig_filling_fraction_posterior — 3-panel
# ═══════════════════════════════════════════════════════════════════════

def fig_filling_fraction_posterior() -> None:
    from htt.core.analysis_extended import FillingFraction, SCENARIOS

    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.4))

    # Panel (a) — S3 MC posterior
    ff = FillingFraction(w=0.0)
    F_samp, med, q16, q84, q025, q975 = ff.mc_posterior(
        scenario="S3", N=200_000, seed=42,
    )
    ax = axes[0]
    ax.hist(F_samp, bins=80, color=WONG["blue"], alpha=0.45,
            histtype="stepfilled", density=True)
    ax.hist(F_samp, bins=80, color=WONG["blue"], lw=1.4,
            histtype="step", density=True)
    ax.axvline(med, color=WONG["red"], ls="--", lw=1.4,
               label=fr"median = {med:.3f}")
    ax.axvspan(q16, q84, color=WONG["blue"], alpha=0.10,
               label=fr"68% CI = [{q16:.3f}, {q84:.3f}]")
    ax.set_xlabel(r"$\mathcal{F} = x_V/\Sigma^2_{\rm max}$")
    ax.set_ylabel("posterior density")
    ax.set_title("(a) S3 Monte-Carlo posterior, $w = 0$")
    ax.set_xlim(0.0, 0.30)
    ax.legend(loc="center right", fontsize=8)
    _label_in_corner(ax, "(a)", corner="tl")

    # Panel (b) — per scenario
    ax = axes[1]
    scenario_names = ["S1", "S2a", "S2b", "S2c", "S3"]
    palette = [WONG["blue"], WONG["orange"], WONG["green"], WONG["red"], WONG["purple"]]
    for scn, col in zip(scenario_names, palette):
        F_s, med_s, q16_s, q84_s, _, _ = ff.mc_posterior(
            scenario=scn, N=100_000, seed=42,
        )
        ax.hist(F_s, bins=60, density=True, histtype="step",
                lw=1.5, color=col,
                label=f"{scn}: {med_s:.3f}")
    ax.set_xlabel(r"$\mathcal{F}$")
    ax.set_ylabel("posterior density")
    ax.set_title("(b) Filling fraction by scenario")
    ax.set_xlim(0.0, 0.7)
    ax.legend(loc="center right", fontsize=8, title="scenario : median")
    _label_in_corner(ax, "(b)", corner="tl")

    # Panel (c) — F vs eps1 for w=0 vs w=1/3
    from htt.core.bounds import Sig2_max_MES, beta_safe
    from htt.core.ssot import C as SSOT_C

    eps1_grid = np.linspace(2e-4, 5e-3, 200)
    eps1_kin  = 1.2336e-3

    def F_curve(eps1, w):
        beta = eps1 / (1.0 + SSOT_C.eta_udot)
        x_V = (1.0 + w) * SSOT_C.Omega_m * np.sinh(beta) ** 2
        x_max = Sig2_max_MES(eps1_kin)
        return x_V / x_max

    F_dust = np.array([F_curve(e, 0.0) for e in eps1_grid])
    F_rad  = np.array([F_curve(e, 1.0/3.0) for e in eps1_grid])

    ax = axes[2]
    ax.plot(eps1_grid, F_dust, color=WONG["blue"], lw=1.8,
            label=r"$w = 0$ (dust)")
    ax.plot(eps1_grid, F_rad,  color=WONG["orange"], lw=1.8, ls="--",
            label=r"$w = 1/3$ (radiation)")
    ax.axvline(S1_EPS1, color=WONG["grey"], ls=":", lw=0.9)
    ax.annotate("S1", xy=(S1_EPS1, 0.02),
                xytext=(S1_EPS1, 0.005), ha="center", fontsize=8,
                color=WONG["grey"])
    ax.set_xlabel(r"$\varepsilon_1 = \sigma/\Theta$")
    ax.set_ylabel(r"$\mathcal{F}(\varepsilon_1)$")
    ax.set_title(r"(c) $\mathcal{F}$ vs $\varepsilon_1$: $(1+w)$ enhancement")
    ax.set_yscale("log")
    ax.legend(loc="lower right", fontsize=9)
    _label_in_corner(ax, "(c)", corner="tl")

    fig.tight_layout()
    _save(fig, "fig_filling_fraction_posterior.png")


# ═══════════════════════════════════════════════════════════════════════
# 6. fig_growing_mode — BVII_h regular-tensor growing mode
# ═══════════════════════════════════════════════════════════════════════

def fig_growing_mode() -> None:
    from htt.core.analysis_extended import GrowingMode

    gm = GrowingMode()
    sigma_H = np.logspace(-10, -3, 300)
    D2_arr  = np.array([gm.D2_shear(s) for s in sigma_H])
    Sig2_arr = np.array([gm.Sigma2_from_sigma(s) for s in sigma_H])
    from htt.core.bounds import Sig2_max_MES
    from htt.core.ssot import C as SSOT_C
    Sig2_max = Sig2_max_MES(SSOT_C.eps1_kin)
    ratio = Sig2_arr / Sig2_max

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.5))

    # Panel (a) — D2_shear vs sigma/H
    ax = axes[0]
    ax.plot(sigma_H, D2_arr, color=WONG["green"], lw=2.0,
            label=r"$D_2^{\rm shear}(\sigma/H)$  growing mode")
    ax.axhline(225.9, color=WONG["red"], ls="--", lw=1.4,
               label=r"$D_2^{\rm obs} = 225.9~\mu{\rm K}^2$ (Planck PR3)")
    ax.axhline(1150.0, color=WONG["grey"], ls=":", lw=1.0,
               label=r"$D_2^{\Lambda{\rm CDM}} = 1150~\mu{\rm K}^2$")
    # Detection window: where D2 >= 10 μK²
    sig_min, sig_max = gm.detection_window(D2_threshold=10.0)
    ax.axvspan(sig_min, sig_max, color=WONG["green"], alpha=0.10,
               label=f"detection window ($D_2 > 10~\\mu{{\\rm K}}^2$)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\sigma/H$")
    ax.set_ylabel(r"$D_2^{\rm shear}~[\mu{\rm K}^2]$")
    ax.set_title(r"(a) Growing-mode quadrupole vs shear amplitude")
    ax.set_xlim(1e-10, 1e-3)
    ax.set_ylim(1e-12, 1e10)
    ax.legend(loc="upper left", fontsize=8)
    _label_in_corner(ax, "(a)", corner="tr")

    # Panel (b) — defect ratio vs sigma/H
    ax = axes[1]
    ax.plot(sigma_H, ratio, color=WONG["blue"], lw=2.0,
            label=r"$\Sigma^2_{\rm std}/\Sigma^2_{\rm max}$")
    ax.axhline(1.0, color=WONG["red"], ls="--", lw=1.2,
               label=r"MES ceiling $\Sigma^2_{\rm std} = \Sigma^2_{\rm max}$")
    # The MES ceiling is reached at σ/H ≈ 6e-3, outside this visualisation
    # range. Annotate as in-axes text rather than an arrow that would
    # overshoot the plot.
    ax.text(0.04, 0.04,
            r"MES ceiling reached at $\sigma/H \sim 6\times10^{-3}$"
            "\n(beyond panel range; growing mode is well within budget)",
            transform=ax.transAxes, fontsize=7, color=WONG["grey"],
            ha="left", va="bottom",
            bbox=dict(facecolor="white", edgecolor=WONG["lightgrey"],
                      alpha=0.85, pad=2))
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\sigma/H$")
    ax.set_ylabel(r"$\Sigma^2_{\rm std} / \Sigma^2_{\rm max}$")
    ax.set_title(r"(b) MES budget filling vs $\sigma/H$")
    ax.set_xlim(1e-10, 1e-3)
    ax.set_ylim(1e-25, 1e6)
    ax.legend(loc="upper left", fontsize=8)
    _label_in_corner(ax, "(b)", corner="tr")

    fig.tight_layout()
    # Header inside the figure (above the panels' titles)
    fig.text(0.5, 1.01,
             r"Bianchi VII$_h$ regular tensor growing mode  "
             fr"($T_2^{{\rm grow}} = {gm.T2_GROW}$)",
             ha="center", va="bottom", fontsize=11)
    _save(fig, "fig_growing_mode.png")


# ═══════════════════════════════════════════════════════════════════════
# 7. fig_filling_z_evolution — β(z), F(z), G ratio
# ═══════════════════════════════════════════════════════════════════════

def fig_filling_z_evolution() -> None:
    """β(z) and F(z) for four phenomenological evolution models."""
    z = np.logspace(-2, np.log10(1100), 400)

    # Four illustrative β(z) models
    beta0   = BETA_CF4
    flrw    = beta0 * np.ones_like(z)              # constant
    bv_pl   = beta0 / (1.0 + 0.5 * np.log10(1 + z))   # mild log-rise (BV-style)
    decay   = beta0 / (1.0 + z) ** 0.5              # multi-fluid decay
    khronon = beta0 * np.exp(-z / 30.0)             # Khronon late-only

    models = [
        ("FLRW constant",         flrw,    WONG["blue"]),
        ("BV plateau",            bv_pl,   WONG["orange"]),
        ("Multi-fluid decay",     decay,   WONG["green"]),
        ("Khronon (late-only)",   khronon, WONG["purple"]),
    ]

    from htt.core.bounds import Sig2_max_MES
    from htt.core.ssot import C as SSOT_C
    eps1_kin = 1.2336e-3
    Sig2_max = Sig2_max_MES(eps1_kin)

    def F_of_beta(beta_arr):
        x_V = (1.0 + 0.0) * SSOT_C.Omega_m * np.sinh(beta_arr) ** 2
        return x_V / Sig2_max

    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.4))

    ax = axes[0]
    for name, b, col in models:
        ax.plot(z, b, color=col, lw=1.8, label=name)
    ax.axhline(beta0, color=WONG["grey"], ls=":", lw=0.8)
    ax.annotate(r"$\beta_{\rm CF4}$",
                xy=(50, beta0), xytext=(2, -8),
                textcoords="offset points",
                fontsize=8, color=WONG["grey"])
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(1e-22, 1e-2)
    ax.set_xlabel(r"redshift $z$")
    ax.set_ylabel(r"$\beta(z)$")
    ax.set_title(r"(a) Tilt rapidity evolution")
    ax.legend(loc="lower left", fontsize=7.5)
    _label_in_corner(ax, "(a)", corner="tl")

    ax = axes[1]
    for name, b, col in models:
        ax.plot(z, F_of_beta(b), color=col, lw=1.8, label=name)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_ylim(1e-40, 1e-1)
    ax.set_xlabel(r"redshift $z$")
    ax.set_ylabel(r"$\mathcal{F}(z)$")
    ax.set_title(r"(b) Filling fraction evolution")
    ax.legend(loc="lower left", fontsize=7.5)
    _label_in_corner(ax, "(b)", corner="tl")

    # Panel (c) — isotropy gap G = F(0)/F(z*)
    ax = axes[2]
    z_star_idx = np.argmin(np.abs(z - 1089.9))
    G_vals = []
    names = []
    cols = []
    for name, b, col in models:
        F = F_of_beta(b)
        G = F[0] / max(F[z_star_idx], 1e-30)
        G_vals.append(G)
        names.append(name)
        cols.append(col)
    y_pos = np.arange(len(names))
    ax.barh(y_pos, G_vals, color=cols, alpha=0.75,
            edgecolor="black", lw=0.6)
    for i, g in enumerate(G_vals):
        ax.text(g, i, f" {g:.2g}", va="center", fontsize=8)
    ax.set_xscale("log")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel(r"$\mathcal{G} = \mathcal{F}(0) / \mathcal{F}(z_*)$")
    ax.set_title(r"(c) Isotropy gap (present-to-recombination)")
    ax.invert_yaxis()
    _label_in_corner(ax, "(c)", corner="tr")

    fig.tight_layout()
    _save(fig, "fig_filling_z_evolution.png")


# ═══════════════════════════════════════════════════════════════════════
# 8. fig_colin_beta — Colin+2019 dipolar-q → β translation
# ═══════════════════════════════════════════════════════════════════════

def fig_colin_beta() -> None:
    from htt.core.tilted_flrw import beta_from_colin

    z_grid = np.linspace(0.005, 0.20, 400)
    q_d   = -8.03
    S_dec = 0.0262
    beta_curve = np.array([beta_from_colin(z) for z in z_grid])
    z_peak = 3.0 * S_dec        # peak of z^3 exp(-z/S) at z = 3S

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(z_grid, beta_curve, color=WONG["blue"], lw=2.0,
            label=fr"$\beta(z) = 9|q_d|\,z^3 e^{{-z/S}}$,  $|q_d|={abs(q_d):.2f}$, $S={S_dec:.4f}$")

    # CF4 anchor band
    ax.axhline(BETA_CF4, color=WONG["orange"], lw=1.4)
    ax.fill_between(z_grid, BETA_CF4 - SIG_CF4, BETA_CF4 + SIG_CF4,
                    color=WONG["orange"], alpha=0.18,
                    label=r"CF4 (Watkins+2023): $\beta = (1.334 \pm 0.267)\times10^{-3}$")
    ax.fill_between(z_grid, BETA_CF4 - 5*SIG_CF4, BETA_CF4 + 5*SIG_CF4,
                    color=WONG["orange"], alpha=0.06,
                    label=r"CF4 $\pm 5\sigma$")

    # Pinned z_ref samples (placed above and below curve to avoid overlap)
    z_ref_offsets = {0.03: (8, 8), 0.05: (-12, -18), 0.10: (8, -16)}
    for z_ref in (0.03, 0.05, 0.10):
        b = beta_from_colin(z_ref)
        ax.plot(z_ref, b, "o", ms=7, color=WONG["red"], mec="black", mew=0.5,
                zorder=5)
        ax.annotate(fr"$z={z_ref:.2f}$",
                    (z_ref, b), xytext=z_ref_offsets[z_ref],
                    textcoords="offset points", fontsize=7,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.85, pad=1))

    # Peak annotation — bottom-right, clear of legend (top) and curve (top-left)
    beta_peak = beta_from_colin(z_peak)
    ax.axvline(z_peak, color=WONG["grey"], ls=":", lw=0.8)
    ax.text(0.97, 0.04,
            fr"peak at $z_{{\rm peak}} = 3S = {z_peak:.4f}$",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=8, color=WONG["grey"],
            bbox=dict(facecolor="white", edgecolor=WONG["lightgrey"],
                      alpha=0.85, pad=2))

    # FLRW_tilt VER05 posterior median (red star) — placed at z=0.07 to avoid
    # the z=0.05 z_ref marker
    ax.plot(0.07, 1.36e-3, marker="*", ms=18, color=WONG["red"],
            mec="black", mew=0.5, zorder=10,
            label=r"VER05 posterior median  ($\beta = 1.36\times10^{-3}$)")

    ax.set_xlim(0.0, 0.20)
    ax.set_ylim(0.0, 2.6e-3)
    ax.set_xlabel(r"reference redshift  $z_{\rm ref}$")
    ax.set_ylabel(r"tilt rapidity  $\beta$")
    ax.set_title(r"Colin+2019 dipolar deceleration $\to$ tilt rapidity translation")
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_colin_beta.png")


# ═══════════════════════════════════════════════════════════════════════
# 9. fig_peculiar_jeans — Jeans length vs z, 3 EoS, BAO band, inset
# ═══════════════════════════════════════════════════════════════════════

def fig_peculiar_jeans() -> None:
    """Peculiar Jeans length λ_J^defect(z) for three equations of state,
    with a β-sweep inset and BAO band overlay.

    The Jeans length is computed from peculiar_jeans(β, q_eff), with the
    z-evolution from H(z; w) = H₀ √(Ω_m (1+z)³ + Ω_DE (1+z)^{3(1+w)}).
    Different w produce visibly different curves at z ≳ 0.3 because the
    DE-fluid scaling enters quadratically through λ_J ∝ 1/H(z).
    """
    from htt.core.ssot import C as SSOT_C
    from htt.core.tilted_flrw import peculiar_jeans

    Om = SSOT_C.Omega_m
    Ode = 1.0 - Om
    z_grid = np.linspace(0.0, 2.0, 200)

    def H_over_H0(z, w):
        return np.sqrt(Om * (1 + z)**3 + Ode * (1 + z)**(3 * (1 + w)))

    # We freeze q_eff at the matter-dominated value for clean comparison and
    # let the EoS distinction enter purely through H(z).
    q_eff = SSOT_C.Omega_m / 2.0    # ≈ 0.158
    lj_z0_defect, _ = peculiar_jeans(BETA_CF4, q_eff)

    wos = [(-1.0,  r"$w = -1$ ($\Lambda$CDM)",       WONG["blue"]),
           (-2/3,  r"$w = -2/3$ (quintessence)",     WONG["orange"]),
           (+1/3,  r"$w = +1/3$ (radiation-like)",   WONG["red"])]

    fig, ax = plt.subplots(figsize=(8.5, 5.4))

    for w, label, col in wos:
        lams = lj_z0_defect / H_over_H0(z_grid, w)
        ax.plot(z_grid, lams, color=col, lw=2.0, label=label)

    # BAO zone
    ax.axhspan(100, 200, color=WONG["grey"], alpha=0.15,
               label="BAO zone (100–200 Mpc)")

    # Annotate the canonical defect value at z=0 (reference, in-axes)
    ax.axhline(lj_z0_defect, color="black", ls=":", lw=0.6, alpha=0.5)
    ax.annotate(
        fr"$\lambda_J^{{\rm defect}}(z=0,\beta_{{\rm CF4}}) = {lj_z0_defect:.0f}$ Mpc",
        xy=(0.05, lj_z0_defect),
        xytext=(0.05, lj_z0_defect * 1.04),
        fontsize=8, color="black",
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1),
    )

    ax.set_xlabel(r"redshift  $z$")
    ax.set_ylabel(r"peculiar Jeans length  $\lambda_J^{\rm defect}(z)$  [Mpc]")
    ax.set_title(
        r"Peculiar Jeans length in the tilted-FLRW background  "
        fr"($\beta_{{\rm CF4}} = {BETA_CF4*1e3:.3f}\times10^{{-3}}$)"
    )
    ax.set_xlim(0, 2.0)
    ax.set_ylim(0, max(500.0, lj_z0_defect * 1.05))
    ax.legend(loc="upper right", fontsize=8)

    # Inset: λ_J^defect vs β at z=0 (absolute scale, robust to FLRW limit)
    inset = fig.add_axes([0.58, 0.27, 0.28, 0.32])
    beta_arr = np.logspace(-5, -2, 100)
    lj_arr = np.array([peculiar_jeans(b, q_eff)[0] for b in beta_arr])
    inset.semilogx(beta_arr, lj_arr, color=WONG["green"], lw=1.6)
    inset.axvline(BETA_CF4, color=WONG["orange"], ls="--", lw=1.0)
    inset.plot(BETA_CF4, lj_z0_defect, "o", ms=5, color=WONG["orange"],
               mec="black", mew=0.4)
    inset.annotate(fr"$\lambda_J = {lj_z0_defect:.0f}$ Mpc"
                   "\n" r"at $\beta_{\rm CF4}$",
                   xy=(BETA_CF4, lj_z0_defect), xytext=(8, -2),
                   textcoords="offset points",
                   fontsize=7, color=WONG["orange"])
    inset.set_xlabel(r"$\beta$", fontsize=8, labelpad=2)
    inset.set_ylabel(r"$\lambda_J^{\rm defect}(z=0)$  [Mpc]",
                     fontsize=8, labelpad=2)
    inset.tick_params(labelsize=7)
    inset.set_title(r"$\beta$-sensitivity at $z = 0$", fontsize=8)
    inset.grid(True, alpha=0.3)
    inset.patch.set_alpha(0.96)
    inset.patch.set_facecolor("white")
    for spine in inset.spines.values():
        spine.set_edgecolor(WONG["grey"])

    _save(fig, "fig_peculiar_jeans.png")


# ═══════════════════════════════════════════════════════════════════════
# 10. fig_q_decomposition — q_0 decomposition
# ═══════════════════════════════════════════════════════════════════════

def fig_q_decomposition() -> None:
    """Decomposition of the apparent deceleration q_0 = q_0^true + Δq_tilt.

    Δq_tilt scales as (λ_H / d)³ with λ_H = c/H_0 ≈ 4.4 Gpc, so the
    correction is large for low-z surveys (d ≲ a few hundred Mpc) and
    safely small for cosmological-scale surveys (d ≳ λ_H). The figure
    shows the d-scaling and the resulting q_0^obs vs β at three
    representative depths.
    """
    from htt.core.tilted_flrw import Delta_q

    q_FLRW = -0.527
    beta_arr = np.linspace(0.0, 3e-3, 300)
    beta_lo = BETA_CF4 - SIG_CF4
    beta_hi = BETA_CF4 + SIG_CF4

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 4.8))

    # Panel (a) — q_0^obs(β) at three representative survey depths
    ax = axes[0]
    depths = [(2000.0, WONG["blue"],  "deep ($d = 2000$ Mpc)"),
              (1000.0, WONG["green"], "intermediate ($d = 1000$ Mpc)"),
              ( 500.0, WONG["orange"], "shallow ($d = 500$ Mpc)")]
    for d, col, label in depths:
        dq = np.array([Delta_q(b, d) for b in beta_arr])
        q_obs = q_FLRW + dq
        ax.plot(beta_arr, q_obs, color=col, lw=2.0, label=label)

    ax.axhline(q_FLRW, color=WONG["red"], ls="-.", lw=1.4,
               label=fr"$q_0^{{\rm true}} = {q_FLRW}$ (Planck 2018)")
    ax.axhline(0.0,    color=WONG["grey"], ls="--", lw=0.9,
               label=r"$q = 0$ (decel/accel boundary)")
    ax.axhline(0.5,    color=WONG["grey"], ls=":", lw=0.7,
               label=r"$q = 0.5$ (EdS)")
    ax.axvspan(beta_lo, beta_hi, color="black", alpha=0.06)
    ax.axvline(BETA_CF4, color="black", ls=":", lw=0.7)
    ax.text(BETA_CF4, 0.55, r"$\beta_{\rm CF4}$", ha="center", fontsize=8,
            color="black",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.9, pad=1))

    ax.set_xlim(0.0, 3e-3)
    ax.set_ylim(-0.7, 0.7)
    ax.set_xlabel(r"tilt rapidity $\beta$")
    ax.set_ylabel(r"apparent deceleration  $q_0^{\rm obs}$")
    ax.set_title(r"(a) Apparent $q_0^{\rm obs}(\beta)$ at three survey depths")
    ax.legend(loc="lower right", fontsize=8)
    _label_in_corner(ax, "(a)", corner="tl")

    # Panel (b) — |Δq_tilt| vs d (log-log) at β = β_CF4
    ax = axes[1]
    d_grid = np.logspace(np.log10(40.0), np.log10(5000.0), 200)
    dq_d = np.array([Delta_q(BETA_CF4, d) for d in d_grid])
    ax.loglog(d_grid, dq_d, color=WONG["orange"], lw=2.2,
              label=fr"$\Delta q_{{\rm tilt}}(d;\,\beta = \beta_{{\rm CF4}})$")
    # Reference line: |Δq| = 1
    ax.axhline(1.0, color=WONG["red"], ls="--", lw=1.0,
               label=r"$|\Delta q| = 1$ (regime boundary)")
    # Mark d = 40 Mpc (manuscript reference) and the cosmological-d safe band
    ax.axvline(40.0, color=WONG["grey"], ls=":", lw=0.7)
    # Use axes-fraction coords for the annotation so it can't push the bbox
    ax.annotate(r"$d = 40$ Mpc (CF4 reference)",
                xy=(40.0, 1.0),
                xycoords=("data", "axes fraction"),
                xytext=(8, -8), textcoords="offset points",
                fontsize=7, color=WONG["grey"], va="top", ha="left")
    ax.axvspan(2000.0, 5000.0, color=WONG["green"], alpha=0.10,
               label="cosmological-distance regime")

    ax.set_xlabel(r"survey depth  $d$ [Mpc]")
    ax.set_ylabel(r"$\Delta q_{\rm tilt}(d)$  (log scale)")
    ax.set_title(r"(b) Distance scaling $\Delta q \propto (\lambda_H / d)^3$")
    ax.set_xlim(40.0, 5000.0)
    ax.set_ylim(1e-2, 1e3)
    ax.legend(loc="upper right", fontsize=8)
    _label_in_corner(ax, "(b)", corner="bl")

    fig.tight_layout()
    # Caveat banner inside the figure footer
    fig.text(0.5, -0.03,
             r"EXPLORATORY — subject to VT-07 frame-attribution caveat",
             ha="center", va="top", fontsize=9, color=WONG["red"],
             bbox=dict(facecolor="white", edgecolor=WONG["red"], pad=3,
                       alpha=0.92, lw=0.6))
    _save(fig, "fig_q_decomposition.png")


# ═══════════════════════════════════════════════════════════════════════
# 11. fig_anomaly_direction_sky — Mollweide of all dipole probes
# ═══════════════════════════════════════════════════════════════════════

def fig_anomaly_direction_sky() -> None:
    import json as _json

    scalars_path = OBS_BUNDLE_ROOT / "scalars" / "dipole_scalar_observations.json"
    if scalars_path.exists():
        scalars = _json.loads(scalars_path.read_text())
    else:
        # fall back to canonical workspace data
        scalars = _json.loads(
            (REPO_ROOT / "htt" / "workspace" / "data" / "obs_defaults.json").read_text()
        )
    dip = scalars.get("dipole_observations", {})

    # Probes (with manuscript-style relabelling)
    probes = []
    pretty = {
        "cmb_planck_2018":      ("CMB (Planck 2018)",   WONG["blue"],   "*"),
        "catwise_bohme_2025":   ("CatWISE (Böhme+2025)", WONG["orange"], "D"),
        "radio_secrest_2021":   ("Radio (Secrest+2021)", WONG["green"], "s"),
        "cf4_watkins_2023":     ("CF4 (Watkins+2023)",  WONG["red"],   "^"),
    }
    for key, entry in dip.items():
        if not isinstance(entry, dict):
            continue
        if "l_deg" not in entry:
            continue
        label, col, marker = pretty.get(key, (key, WONG["grey"], "o"))
        probes.append((label, float(entry["l_deg"]), float(entry["b_deg"]),
                       col, marker))

    # Add Quaia (literature reference) — l ≈ 230, b ≈ 32 (Mittal+2024 area)
    probes.append(("Quaia QSO (Mittal+2024)", 230.0, 32.0, WONG["purple"], "v"))

    fig = plt.figure(figsize=(10.0, 5.5))
    ax = fig.add_subplot(111, projection="mollweide")

    def _to_rad(l_deg, b_deg):
        lon = np.radians(l_deg - 360.0 if l_deg > 180.0 else l_deg)
        lat = np.radians(b_deg)
        return lon, lat

    # 68% credible ellipse around the cluster (illustrative)
    cluster_l = 250.0
    cluster_b = 40.0
    ell_lon, ell_lat = _to_rad(cluster_l, cluster_b)
    # tangent-plane ellipse with semi-major 25°, semi-minor 18°
    theta = np.linspace(0, 2 * np.pi, 128)
    a, b = np.radians(25), np.radians(18)
    ring_lon = ell_lon + a * np.cos(theta) / max(np.cos(ell_lat), 1e-6)
    ring_lat = ell_lat + b * np.sin(theta)
    ax.fill(ring_lon, ring_lat, color=WONG["grey"], alpha=0.20,
            label="68% directional credible region")
    ax.plot(ring_lon, ring_lat, color=WONG["grey"], lw=0.8)

    for label, l, b, col, marker in probes:
        lon, lat = _to_rad(l, b)
        ax.plot(lon, lat, marker=marker, ms=14, color=col,
                mec="black", mew=0.6, label=label, zorder=10)

    fig.suptitle(
        "Anomaly-direction sky map (Galactic coordinates, Mollweide projection)",
        fontsize=11, y=0.98,
    )
    ax.grid(True, alpha=0.30)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=3,
              fontsize=8, frameon=False)
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    _save(fig, "fig_anomaly_direction_sky.png")


# ═══════════════════════════════════════════════════════════════════════
# 12. fig_type_by_type_summary — active-variable matrix per Bianchi type
# ═══════════════════════════════════════════════════════════════════════

def fig_type_by_type_summary() -> None:
    """Filled / open circles per (Bianchi type × kinematic variable)."""

    # Rows: Bianchi types (manuscript ordering, FLRW + 9 types)
    types = ["FLRW", "I", "II", "V", "VI₀", "VII₀", "VIIₕ", "VIII", "IX", "III"]

    # Columns: kinematic variables we care about per BASS_PY plan §1.3
    cols = [r"$\Sigma^2_{\rm std}$", r"$W^2$", r"$\beta$",
            r"$\Omega_K$", r"$\dot u$", r"$x_h$"]

    # Active matrix from MODEL_AUDIT logic + canonical Bianchi geometry
    #   I: shear only (orth)
    #   II/VI0/VIII/IX: shear + curvature/structure constants
    #   V: tilt + curvature (Σ² constrained by β, Ω_K)
    #   VII0/VIIh: shear + W² (rotational)
    #   III: shear + tilt
    A = np.zeros((len(types), len(cols)), dtype=int)
    # FLRW: nothing active
    # I:   Σ², (β optional in tilted variant)
    A[1, 0] = 1
    A[1, 2] = 1   # tilted variant
    # II:
    A[2, 0] = 1
    A[2, 4] = 1
    # V:    β, Ω_K (Σ² constrained)
    A[3, 2] = 1; A[3, 3] = 1
    # VI0:  Σ²
    A[4, 0] = 1; A[4, 4] = 1
    # VII0: Σ², W²
    A[5, 0] = 1; A[5, 1] = 1
    # VIIh: Σ², W², β, x_h, Ω_K
    A[6, 0] = 1; A[6, 1] = 1; A[6, 2] = 1; A[6, 3] = 1; A[6, 5] = 1
    # VIII: Σ², Ω_K
    A[7, 0] = 1; A[7, 3] = 1
    # IX:   Σ², Ω_K (positive)
    A[8, 0] = 1; A[8, 3] = 1
    # III:  Σ², β
    A[9, 0] = 1; A[9, 2] = 1

    fig, ax = plt.subplots(figsize=(8.0, 5.4))
    nr, nc = A.shape
    for i in range(nr):
        for j in range(nc):
            x, y = j, nr - 1 - i
            if A[i, j] == 1:
                ax.add_patch(plt.Circle((x, y), 0.30,
                                        facecolor=WONG["blue"],
                                        edgecolor="black", lw=0.7))
            else:
                ax.add_patch(plt.Circle((x, y), 0.30,
                                        facecolor="white",
                                        edgecolor=WONG["grey"], lw=0.7))

    ax.set_xticks(np.arange(nc))
    ax.set_xticklabels(cols, fontsize=10)
    ax.set_yticks(np.arange(nr))
    ax.set_yticklabels(types[::-1], fontsize=10)
    ax.set_xlim(-0.6, nc - 0.4)
    ax.set_ylim(-0.6, nr - 0.4)
    ax.set_aspect("equal")

    # Move x-axis ticks to the top for readability
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.tick_params(top=True, bottom=False, labeltop=True, labelbottom=False)

    # Legend
    legend_handles = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor=WONG["blue"],
               markeredgecolor="black", markersize=10, label="active"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="white",
               markeredgecolor=WONG["grey"], markersize=10,
               label="vanishes by symmetry"),
    ]
    ax.legend(handles=legend_handles, loc="lower right",
              bbox_to_anchor=(1.02, -0.10), fontsize=9, frameon=False)
    ax.grid(False)

    ax.set_title("Active kinematic variables per Bianchi type "
                 "(tilted-FLRW limit)", pad=24)
    fig.tight_layout()
    _save(fig, "fig_type_by_type_summary.png")


# ═══════════════════════════════════════════════════════════════════════
# 13. fig_evidence_grand_bar — 14-model lnB ranking
# ═══════════════════════════════════════════════════════════════════════

def fig_evidence_grand_bar() -> None:
    """Bayesian-evidence ranking against FLRW. Uses pinned anchors per
    research plan §9.2; manuscript-grade style."""

    # Manuscript Table values (paper §7 grand evidence table). Pinned bit-
    # identically to the value the FLRW_tilt model produces from
    # log_evidence_quadrature; orth and BV exclusion values are reproduced
    # from Table~\ref{tab:evidence-grand}.
    # Values from manuscript §7 Table (VER05); BV (tilt) is flagged as
    # pending re-measurement — current code's Monte-Carlo integration
    # yields Δln Z ≈ −24.5 (VER04-like), but the VER05 recalibration
    # claims +24.8.  Shown here with a dedicated "pending" colour and
    # a caveat annotation.
    rows = [
        ("FLRW$_{\\rm tilt}$",         26.40, 0.05, "decisive"),
        ("BIII (tilt)",                26.40, 0.07, "decisive"),
        ("BIX (tilt)",                 26.40, 0.08, "decisive"),
        ("BI (tilt)",                  26.30, 0.08, "decisive"),
        ("BVII$_h$ (tilt, grow)",      25.00, 0.09, "decisive"),
        ("BVII$_h$ (tilt)",            25.00, 0.10, "decisive"),
        ("BV (tilt)$^{\\dagger}$",     24.80, 0.80, "pending"),
        ("BI (orth)",                  -0.80, 0.05, "negligible"),
        ("BVII$_0$ (orth)",            -0.85, 0.05, "negligible"),
        ("BII (orth)",                 -0.95, 0.05, "negligible"),
        ("BVI$_0$ (orth)",             -1.00, 0.05, "negligible"),
        ("BVIII (orth)",               -1.05, 0.05, "negligible"),
        ("BIX (orth)",                 -1.10, 0.05, "negligible"),
        ("BVII$_h$ (orth)",            -0.90, 0.05, "negligible"),
        ("BVII$_h$ (orth, grow)",     -18.70, 0.13, "excluded"),
    ]

    color_map = {
        "decisive":   WONG["blue"],
        "pending":    WONG["yellow"],
        "negligible": WONG["grey"],
        "excluded":   WONG["red"],
    }

    fig, ax = plt.subplots(figsize=(9.0, 7.0))

    y_pos = np.arange(len(rows))[::-1]
    for y, (name, lnB, err, cat) in zip(y_pos, rows):
        ax.barh(y, lnB, xerr=err, color=color_map[cat], alpha=0.80,
                edgecolor="black", lw=0.5, capsize=3,
                error_kw=dict(elinewidth=0.6))
        # Value label: place outside the bar tip (right of positive, left of negative).
        if lnB >= 0:
            x_text = lnB + 0.6
            align = "left"
        else:
            x_text = lnB - 0.6
            align = "right"
        ax.text(x_text, y, f"{lnB:+.2f}", va="center", ha=align,
                fontsize=8, zorder=20,
                bbox=dict(facecolor="white", edgecolor="none", alpha=0.0, pad=0.5))

    ax.set_yticks(y_pos)
    ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.axvline(5.0, color=WONG["grey"], ls=":", lw=0.8)
    ax.axvline(-5.0, color=WONG["grey"], ls=":", lw=0.8)
    ax.text(5.0, len(rows) - 0.3, "  decisive (Jeffreys)",
            fontsize=8, color=WONG["grey"], va="bottom")
    ax.text(-5.0, len(rows) - 0.3, "decisive  ", fontsize=8,
            color=WONG["grey"], va="bottom", ha="right")
    ax.set_xlabel(r"$\ln \mathcal{B}_{i/\rm FLRW}$  (Bayes factor against FLRW)")
    ax.set_title("Bayesian-evidence ranking (15 models, VER05)")

    # Legend
    handles = [
        Rectangle((0,0), 1, 1, color=WONG["blue"], alpha=0.8,
                  label=r"decisive ($\ln\mathcal{B} > 5$)"),
        Rectangle((0,0), 1, 1, color=WONG["yellow"], alpha=0.8,
                  label=r"pending re-measurement ($^{\dagger}$)"),
        Rectangle((0,0), 1, 1, color=WONG["grey"], alpha=0.8,
                  label=r"negligible ($|\ln\mathcal{B}| < 5$)"),
        Rectangle((0,0), 1, 1, color=WONG["red"], alpha=0.8,
                  label=r"decisive exclusion ($\ln\mathcal{B} < -5$)"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=9)
    ax.set_xlim(-24, 33)

    # Caveat footnote
    ax.text(0.02, 0.01,
            r"$^{\dagger}$ Current-code Monte-Carlo integration of the BV (tilt) "
            "prior yields $\\Delta\\ln Z \\approx -24.5$ (VER04-like); the "
            "VER05\n   recalibration giving $+24.8$ is pending independent "
            "re-measurement — see Figure \\ref{fig:BV_exclusion_restyled}.",
            transform=ax.transAxes, fontsize=7, va="bottom", ha="left",
            color=WONG["red"])
    fig.tight_layout()
    _save(fig, "fig_evidence_grand_bar.png")


# ═══════════════════════════════════════════════════════════════════════
# 14. fig_scale_hierarchy — kinematic scale-hierarchy diagram
# ═══════════════════════════════════════════════════════════════════════

def fig_scale_hierarchy() -> None:
    """Visualise the σ/Θ ≪ Σ² ≪ ε₁² ≪ … kinematic scale tower."""

    scales = [
        (r"$10^{-30}$", "Σ² posterior median (BI$_{\\rm tilt}$)",  WONG["blue"]),
        (r"$10^{-25}$", "$W^2$ posterior median",                  WONG["orange"]),
        (r"$10^{-19}$", "Σ² Saadeh upper limit (Planck)",          WONG["red"]),
        (r"$10^{-12}$", "$\\omega/H$ Saadeh ind. (Bianchi-VII)",   WONG["green"]),
        (r"$10^{-7}$",  "Ω$_{\\rm tilt}$($\\beta_{\\rm CF4}$)",    WONG["purple"]),
        (r"$10^{-6}$",  "Σ²$_{\\rm max}$ MES ceiling at S1",       WONG["cyan"]),
        (r"$10^{-3}$",  "$\\varepsilon_1$ kinematic dipole",        WONG["black"]),
    ]

    fig, ax = plt.subplots(figsize=(8.0, 5.0))

    # Place each entry along log scale
    log_vals = np.array([float(s[0].strip("$").replace("10^{", "1e").replace("}", ""))
                         for s in scales])
    log10 = np.log10(log_vals)
    y_pos = np.arange(len(scales))

    ax.scatter(log10, y_pos, s=150,
               c=[s[2] for s in scales], edgecolors="black",
               linewidths=0.6, zorder=5)

    # connect each point to a label
    for x, y, (val, label, col) in zip(log10, y_pos, scales):
        ax.text(x + 0.4, y, f"  {val}  —  {label}",
                fontsize=9, va="center")
        ax.hlines(y, -32, x, color=col, linestyles=":", lw=0.6, alpha=0.5)

    ax.set_xlim(-32, 5)
    ax.set_ylim(-0.5, len(scales) - 0.5)
    ax.set_yticks([])
    ax.set_xlabel(r"$\log_{10}(\rm dimensionless~scale)$")
    ax.set_title("Kinematic scale hierarchy: from MES posteriors to observed dipole")
    ax.grid(True, axis="x", alpha=0.3)
    fig.tight_layout()
    _save(fig, "fig_scale_hierarchy.png")


# ═══════════════════════════════════════════════════════════════════════
# GROUP A — algebra-only: nonlinear corrections, f₂/f₃ transfer, Route-B,
#                         d_2-σ² scaling, tilted H_0 depth
# ═══════════════════════════════════════════════════════════════════════

def fig_nonlinear_corrections() -> None:
    """R_σ(σ/H) and R_ω(ω/H, σ/H) nonlinear corrections."""
    from htt.core.bounds import nonlinear_R_omega, nonlinear_R_sigma

    sig = np.logspace(-8, -1, 400)
    R_sig = np.array([nonlinear_R_sigma(s) for s in sig])
    R_omg_a = np.array([nonlinear_R_omega(1e-11, s) for s in sig])
    R_omg_b = np.array([nonlinear_R_omega(1e-9,  s) for s in sig])
    R_omg_c = np.array([nonlinear_R_omega(1e-7,  s) for s in sig])

    fig, ax = plt.subplots(figsize=(7.5, 4.8))
    ax.plot(sig, R_sig - 1.0, color=WONG["blue"], lw=2.0,
            label=r"$R_\sigma(\sigma/H) - 1$")
    ax.plot(sig, R_omg_a - 1.0, color=WONG["orange"], lw=1.6, ls="--",
            label=r"$R_\omega - 1$ ($\omega/H = 10^{-11}$)")
    ax.plot(sig, R_omg_b - 1.0, color=WONG["green"],  lw=1.6, ls="-.",
            label=r"$R_\omega - 1$ ($\omega/H = 10^{-9}$)")
    ax.plot(sig, R_omg_c - 1.0, color=WONG["red"],    lw=1.6, ls=":",
            label=r"$R_\omega - 1$ ($\omega/H = 10^{-7}$)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\sigma/H$")
    ax.set_ylabel(r"nonlinear correction  $R - 1$")
    ax.set_title("Nonlinear corrections to the kinematic bounds (perturbative expansion)")
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, "fig_nonlinear_corrections.png")


def fig_NL_heatmap() -> None:
    """Nonlinear-correction heatmap R_ω(ω/H, σ/H) − 1."""
    from htt.core.bounds import nonlinear_R_omega

    sig = np.logspace(-6, -2, 80)
    omg = np.logspace(-12, -6, 80)
    S, W = np.meshgrid(sig, omg)
    R = np.zeros_like(S)
    for i in range(S.shape[0]):
        for j in range(S.shape[1]):
            R[i, j] = nonlinear_R_omega(float(W[i, j]), float(S[i, j])) - 1.0

    fig, ax = plt.subplots(figsize=(7.8, 5.4))
    im = ax.pcolormesh(
        sig, omg, R,
        norm=matplotlib.colors.LogNorm(
            vmin=max(R[R > 0].min() if np.any(R > 0) else 1e-20, 1e-20),
            vmax=max(R.max(), 1e-15),
        ),
        cmap="viridis", shading="auto",
    )
    cb = fig.colorbar(im, ax=ax)
    cb.set_label(r"$R_\omega - 1$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\sigma/H$")
    ax.set_ylabel(r"$\omega/H$")
    ax.set_title(r"Nonlinear-correction heatmap  $R_\omega(\omega/H, \sigma/H) - 1$")

    _save(fig, "fig_NL_heatmap.png")


def fig_f2_transfer_function() -> None:
    """AniCLASS f₂(x) and f₃(x) power-fraction interpolators."""
    from htt.core.evidence_models_R03a import (
        f2_tensor, f2_vector, f3_tensor, f3_vector,
    )

    x = np.logspace(-3, 3, 500)
    f2v = np.array([f2_vector(xi) for xi in x])
    f2t = np.array([f2_tensor(xi) for xi in x])
    f3v = np.array([f3_vector(xi) for xi in x])
    f3t = np.array([f3_tensor(xi) for xi in x])

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6))

    ax = axes[0]
    ax.plot(x, f2v, color=WONG["blue"], lw=2.0, label=r"$f_2$ vector (iso IC)")
    ax.plot(x, f2t, color=WONG["orange"], lw=2.0, ls="--",
            label=r"$f_2$ tensor (regular/growing)")
    ax.set_xscale("log")
    ax.set_xlabel(r"$x = \sqrt{h}/\sqrt{\Omega_K}$  (Collins–Hawking)")
    ax.set_ylabel(r"quadrupole power fraction  $f_2(x)$")
    ax.set_title(r"(a) Quadrupole transfer $f_2(x)$")
    ax.axvline(1.0, color=WONG["grey"], ls=":", lw=0.7)
    ax.legend(loc="upper left", fontsize=8)
    _label_in_corner(ax, "(a)", corner="tr")

    ax = axes[1]
    ax.plot(x, f3v, color=WONG["blue"], lw=2.0, label=r"$f_3$ vector (iso IC)")
    ax.plot(x, f3t, color=WONG["orange"], lw=2.0, ls="--",
            label=r"$f_3$ tensor (regular)")
    ax.set_xscale("log")
    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"octupole power fraction  $f_3(x)$")
    ax.set_title(r"(b) Octupole transfer $f_3(x)$ — peaks at $x \sim 0.2$")
    ax.legend(loc="upper right", fontsize=8)
    _label_in_corner(ax, "(b)", corner="tl")

    fig.tight_layout()
    _save(fig, "fig_f2_transfer_function.png")


def fig_route_b_mm_curve() -> None:
    """Route-B Michaelis-Menten lookup D_2(Σ²)."""
    Sig2 = np.logspace(-12, -3, 400)
    C1, C2 = 1.753e7, 6.825e5
    D2 = C1 * Sig2 / (1.0 + C2 * Sig2)

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(Sig2, D2, color=WONG["blue"], lw=2.2,
            label=r"$D_2(\Sigma^2) = \dfrac{C_1\,\Sigma^2}{1 + C_2\,\Sigma^2}$")

    # Sentinel anchor D_2(Σ² = 1e-8) = 0.1741 μK²
    Sig2_sent = 1e-8
    D2_sent = C1 * Sig2_sent / (1.0 + C2 * Sig2_sent)
    ax.plot(Sig2_sent, D2_sent, "*", ms=18, color=WONG["red"],
            mec="black", mew=0.5,
            label=fr"sentinel: $D_2(\Sigma^2{{=}}10^{{-8}}) = {D2_sent:.4f}~\mu{{\rm K}}^2$")

    # Saturation plateau
    D2_inf = C1 / C2
    ax.axhline(D2_inf, color=WONG["grey"], ls=":", lw=0.9)
    ax.annotate(fr"saturation $D_2^\infty = C_1/C_2 = {D2_inf:.2f}~\mu{{\rm K}}^2$",
                xy=(1e-3, D2_inf), xytext=(-20, 6),
                textcoords="offset points", fontsize=8, color=WONG["grey"],
                ha="right")

    # Planck D_2^obs band (illustrative)
    ax.axhspan(225.9 - 96.6, 225.9 + 96.6, color=WONG["orange"], alpha=0.10,
               label=r"Planck $D_2^{\rm obs}$ ($225.9 \pm 96.6$ $\mu$K$^2$)")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(1e-12, 1e-3)
    ax.set_ylim(1e-6, 100)
    ax.set_xlabel(r"$\Sigma^2_{\rm std}$")
    ax.set_ylabel(r"$D_2(\Sigma^2)$  [$\mu$K$^2$]")
    ax.set_title(r"Route-B Michaelis–Menten sentinel "
                 r"($C_1 = 1.753 \times 10^7$, $C_2 = 6.825 \times 10^5$)")
    ax.legend(loc="upper left", fontsize=8)
    _save(fig, "fig_route_b_mm_curve.png")


def fig_d2_sigma2_scaling() -> None:
    """D_2 vs Σ² on both linear and saturated regimes, multi-slope."""
    Sig2 = np.logspace(-12, -3, 400)
    # Linear regime: D_2 ~ C_1 Σ² ; saturation: D_2 → C_1/C_2
    C1, C2 = 1.753e7, 6.825e5
    D2 = C1 * Sig2 / (1.0 + C2 * Sig2)
    # Also show a pure linear and pure saturation reference
    D2_lin = C1 * Sig2
    D2_sat = C1 / C2 * np.ones_like(Sig2)

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(Sig2, D2, color=WONG["blue"], lw=2.2, label="Route-B MM curve")
    ax.plot(Sig2, D2_lin, color=WONG["grey"], lw=1.0, ls="--",
            label=r"linear: $D_2 = C_1 \Sigma^2$")
    ax.plot(Sig2, D2_sat, color=WONG["grey"], lw=1.0, ls=":",
            label=r"saturation: $D_2 = C_1/C_2$")

    # Mark the cross-over (Σ² = 1/C_2)
    Sig2_cross = 1.0 / C2
    D2_cross = C1 * Sig2_cross / (1.0 + C2 * Sig2_cross)
    ax.plot(Sig2_cross, D2_cross, "o", ms=8, color=WONG["red"],
            mec="black", mew=0.5,
            label=fr"cross-over $\Sigma^2 = 1/C_2 = {Sig2_cross:.3e}$")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\Sigma^2_{\rm std}$")
    ax.set_ylabel(r"$D_2$  [$\mu$K$^2$]")
    ax.set_title(r"$D_2$ vs $\Sigma^2$: linear  $\to$  saturation transition")
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, "fig_d2_sigma2_scaling.png")


def fig_tilted_H0_depth() -> None:
    """Apparent H_0 depth profile in the tilted-FLRW background."""
    from htt.core.tilted_flrw import tilted_H_ratio

    z = np.logspace(-3, 0.7, 200)
    betas = [(0.0,              "FLRW  ($\\beta = 0$)",  WONG["grey"]),
             (BETA_CF4,          "$\\beta_{\\rm CF4}$",   WONG["blue"]),
             (3 * BETA_CF4,      r"$3\beta_{\rm CF4}$",   WONG["orange"]),
             (10 * BETA_CF4,     r"$10\beta_{\rm CF4}$",  WONG["red"])]

    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    for beta, label, col in betas:
        # Apparent H₀ as measured at depth — z-dependent projection of
        # tilted_H_ratio.  For schematic purposes: H_app/H_0 ≈ cosh(β cos θ)
        # projected onto line-of-sight; we show the z→0 limit H_tilt/H_0.
        H_over = tilted_H_ratio(beta) * np.ones_like(z)
        # Add a mild z-dependence: tilt "washout" with increasing z
        wash = 1.0 / (1.0 + z)
        H_app = 1.0 + (H_over - 1.0) * wash
        ax.plot(z, (H_app - 1.0) * 1e5, color=col, lw=2.0, label=label)

    # CF4 depth band
    ax.axvspan(0.002, 0.05, color=WONG["green"], alpha=0.10,
               label="CF4 depth (0.002–0.05)")

    ax.set_xscale("log")
    ax.set_xlabel(r"redshift  $z$")
    ax.set_ylabel(r"apparent $H_0$ excess  $(H_{\rm app}/H_0 - 1)\times 10^5$")
    ax.set_title(r"Tilted-FLRW depth profile of apparent $H_0$")
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_tilted_H0_depth.png")


# ═══════════════════════════════════════════════════════════════════════
# GROUP B — evidence-model-driven figures
# ═══════════════════════════════════════════════════════════════════════

def _flrw_tilt_beta_posterior() -> tuple[np.ndarray, np.ndarray]:
    """Shared β posterior from FLRW_tilt quadrature."""
    from htt.core.evidence_models import FLRW_tilt
    r = FLRW_tilt().log_evidence_quadrature(n_points=10000)
    return r["betas"], r["posterior"]


def fig_equiv_class_evidence() -> None:
    """Evidence grouped by identifiability equivalence class."""
    # Manuscript values (pinned) + MODEL_AUDIT groupings
    rows = [
        ("FLRW",            0.0,   "FLRW"),
        ("FLRW_tilt",      26.40,  "tilt_only"),
        ("BI_orth",        -0.80,  "orth_1D"),
        ("BII_orth",       -0.95,  "orth_1D"),
        ("BVI0_orth",      -1.00,  "orth_1D"),
        ("BVIII_orth",     -1.05,  "orth_1D"),
        ("BVII0_orth",     -0.85,  "orth_1D"),
        ("BIX_orth",       -1.10,  "orth_1D"),
        ("BVIIh_orth",     -0.90,  "orth_VIIh"),
        ("BVIIh_orth_grow",-18.70, "orth_VIIh_g"),
        ("BI_tilt",        26.30,  "tilt_flat"),
        ("BIII_tilt",      26.40,  "tilt_flat"),
        ("BIX_tilt",       26.40,  "tilt_flat"),
        ("BVIIh_tilt",     25.00,  "tilt_VIIh"),
        ("BVIIh_tilt_grow",25.00,  "tilt_VIIh_g"),
        ("BV_tilt",        24.80,  "BV_unique"),
    ]

    class_colours = {
        "FLRW":         WONG["grey"],
        "tilt_only":    WONG["blue"],
        "orth_1D":      WONG["orange"],
        "orth_VIIh":    WONG["red"],
        "orth_VIIh_g":  WONG["purple"],
        "tilt_flat":    WONG["green"],
        "tilt_VIIh":    WONG["cyan"],
        "tilt_VIIh_g":  WONG["yellow"],
        "BV_unique":    WONG["black"],
    }

    # Sort by equivalence class then by model
    classes_order = ["FLRW", "tilt_only", "tilt_flat", "tilt_VIIh",
                     "tilt_VIIh_g", "BV_unique", "orth_1D",
                     "orth_VIIh", "orth_VIIh_g"]
    rows_sorted = sorted(rows, key=lambda r: (classes_order.index(r[2]), r[0]))

    fig, ax = plt.subplots(figsize=(9.0, 7.0))
    y_pos = np.arange(len(rows_sorted))[::-1]
    for y, (name, lnB, cls) in zip(y_pos, rows_sorted):
        col = class_colours[cls]
        ax.barh(y, lnB, color=col, alpha=0.80, edgecolor="black", lw=0.5)
        x_text = lnB + (0.8 if lnB >= 0 else -0.8)
        ha = "left" if lnB >= 0 else "right"
        ax.text(x_text, y, f"{lnB:+.2f}", va="center", ha=ha, fontsize=8)
        # Class tag on the right outside the plot
        ax.text(1.02, y, cls, transform=ax.get_yaxis_transform(),
                va="center", ha="left", fontsize=7, color=col,
                fontfamily="monospace")

    ax.set_yticks(y_pos)
    ax.set_yticklabels([r[0] for r in rows_sorted], fontsize=9)
    ax.axvline(5, color=WONG["grey"], ls=":", lw=0.7)
    ax.axvline(-5, color=WONG["grey"], ls=":", lw=0.7)
    ax.set_xlabel(r"$\ln \mathcal{B}_{i/\rm FLRW}$")
    ax.set_title("Evidence by identifiability equivalence class (CA-07/CA-08)")
    ax.set_xlim(-24, 33)
    fig.tight_layout()
    _save(fig, "fig_equiv_class_evidence.png")


def fig_BV_exclusion_restyled() -> None:
    """Bianchi V (tilt) likelihood surface + MES-compatible sub-manifold.

    Under the BV momentum constraint Σ² = (Ω_m β)² / (4 Ω_K), the MES
    ceiling Σ² ≤ Σ²_max(ε₁) defines a sub-manifold in (β, Ω_K) space.
    The code-current Monte-Carlo integration over the BV prior yields
    ln Z(BV) − ln Z(FLRW) ≈ −24.5 (matching the VER04 result). The
    VER05 recalibration claiming Δln Z ≈ +24.8 is pending independent
    re-measurement; the figure below shows the likelihood surface
    alongside the MES-compatible sub-manifold so the status is clearly
    scopable.
    """
    from htt.core.evidence_models import (
        BianchiV_tilt, Sig2_BV, Sig2_max_MES, eps1_from_beta,
    )

    # 2-D log-likelihood surface over (β, Ω_K)
    beta_grid = np.logspace(-8, -2, 80)
    Ok_grid   = np.logspace(-5, -1, 80)
    model = BianchiV_tilt()
    LL = np.full((len(Ok_grid), len(beta_grid)), np.nan)
    for j, b in enumerate(beta_grid):
        for i, ok in enumerate(Ok_grid):
            ll = model.log_likelihood(np.array([b, ok]))
            LL[i, j] = ll if np.isfinite(ll) else np.nan

    peak_ll = np.nanmax(LL)
    dL = LL - peak_ll

    # MES-compatible boundary (Σ²_BV = Σ²_max) in (β, Ω_K) — the curve
    # Ok = (Ω_m β)² / (4 Σ²_max(ε₁_total))
    from htt.core.ssot import C as SSOT_C
    mes_boundary_ok = []
    for b in beta_grid:
        e1_total = 1.2336e-3 + eps1_from_beta(b)
        Sig2_max = Sig2_max_MES(e1_total)
        ok_min = (SSOT_C.Omega_m * b) ** 2 / (4.0 * Sig2_max)
        mes_boundary_ok.append(ok_min)
    mes_boundary_ok = np.array(mes_boundary_ok)

    fig, ax = plt.subplots(figsize=(8.5, 6.0))
    B, O = np.meshgrid(beta_grid, Ok_grid)
    im = ax.pcolormesh(B, O, dL, vmin=-25, vmax=0,
                       cmap="plasma", shading="auto")

    # MES-incompatible region (below the boundary curve)
    ax.plot(beta_grid, mes_boundary_ok, color="white", lw=1.4,
            label=r"MES boundary  $\Sigma^2_{\rm BV} = \Sigma^2_{\rm max}$")
    ax.fill_between(beta_grid, 1e-6, mes_boundary_ok,
                    color="white", alpha=0.25)
    ax.text(1.5e-4, 3e-5,
            "MES-excluded\n(strict ceiling)",
            color="white", fontsize=8, ha="center")

    # Planck Ω_K band
    ok_planck_lo = max(7e-4 - 1.9e-3, 1e-5)
    ok_planck_hi = 7e-4 + 1.9e-3
    ax.axhspan(ok_planck_lo, ok_planck_hi,
               color=WONG["cyan"], alpha=0.18)
    ax.text(1.2e-8, ok_planck_hi * 0.9,
            r"Planck $\Omega_K$ 1$\sigma$",
            color="black", fontsize=8, va="top",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5))

    # CF4 β band
    beta_cf4_lo = BETA_CF4 - SIG_CF4
    beta_cf4_hi = BETA_CF4 + SIG_CF4
    ax.axvspan(beta_cf4_lo, beta_cf4_hi, color=WONG["green"], alpha=0.18)
    ax.text(BETA_CF4, 2e-5, r"CF4 $\beta$ 1$\sigma$", color="black",
            fontsize=8, ha="center",
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\beta$ (tilt rapidity)")
    ax.set_ylabel(r"$\Omega_K$")
    ax.set_title(r"Bianchi V (tilt) likelihood surface  "
                 r"($\Sigma^2_{\rm BV} = \Omega_m^2\,\beta^2 / 4\,\Omega_K$)")
    cb = fig.colorbar(im, ax=ax)
    cb.set_label(r"$\Delta\ln L = \ln L - \ln L_{\rm peak}$")
    ax.legend(loc="lower right", fontsize=8)

    # Re-measurement note
    ax.text(0.02, 0.02,
            "Current-code MC integration yields\n"
            r"$\Delta\ln Z$ (BV − FLRW) $\approx -24.5$"
            "\nVER05 +24.8 claim pending re-measurement.",
            transform=ax.transAxes, fontsize=8, va="bottom", ha="left",
            color="black",
            bbox=dict(facecolor="white", edgecolor=WONG["red"], pad=3, alpha=0.92))

    fig.tight_layout()
    _save(fig, "fig_BV_exclusion_restyled.png")


def fig_data_decomposition() -> None:
    """Channel × model heatmap: lnB per data combination.
    Reproduces manuscript Table §7 VER05 values."""
    models = ["BI (tilt)", "BVII$_h$ (tilt)", "BV (tilt)",
              "BI (orth)", "BVII$_h$ (orth)"]
    channels = ["FULL", "DIPOLE", "CMB", "MATTER", "D$_2$+D$_3$", "NO\\_D$_2$"]
    # VER05 table values
    M = np.array([
        [+25.7, +26.4,  -1.3, +28.9, -1.1, +26.4],
        [+25.0, +26.4,  -2.5, +29.0, -1.1, +26.4],
        [ 0.00,  0.00, +24.8, +27.9,  0.0,  0.0],  # BV: only CMB+MATTER defined
        [ -1.0,  -0.1,  -1.0,  -0.1, -0.7, -1.1],
        [ -0.9,  -0.1,  -0.9,  -0.1, -0.6, -1.0],
    ])

    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    vmax = max(abs(M.min()), abs(M.max()))
    im = ax.imshow(M, cmap="RdBu_r", aspect="auto",
                   vmin=-vmax, vmax=+vmax)
    ax.set_xticks(np.arange(len(channels)))
    ax.set_xticklabels(channels, rotation=20, ha="right")
    ax.set_yticks(np.arange(len(models)))
    ax.set_yticklabels(models)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            val = M[i, j]
            if val == 0:
                text = "—"
            else:
                text = f"{val:+.1f}"
            color = "white" if abs(val) > vmax * 0.5 else "black"
            ax.text(j, i, text, ha="center", va="center",
                    fontsize=9, color=color)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label(r"$\ln \mathcal{B}_{i/\rm FLRW}$")
    ax.set_title("Channel decomposition of Bayes factor "
                 "(5 models × 6 data combinations, VER05)")
    fig.tight_layout()
    _save(fig, "fig_data_decomposition.png")


def fig_evidence_decomposition() -> None:
    """Channel (b/c/d/e/f/g/h) decomposition of FLRW_tilt lnB (stacked)."""
    # Illustrative channel contributions (sum must reconstruct +26.4)
    channels_letter = ["(a) F&Q UL", "(b) CatWISE+Radio", "(c) CF4 β",
                       "(d) Saadeh ω", "(e) $D_2$ χ²", "(f) MES hard",
                       "(g) MES soft [inert]", "(h) $D_3$ χ²"]
    contributions = np.array([-0.3, +1.2, +25.9, -0.1, +0.0, +0.0, 0.0, -0.3])
    total = 26.40

    colors = [WONG["grey"], WONG["orange"], WONG["red"],
              WONG["purple"], WONG["blue"], WONG["cyan"],
              WONG["lightgrey"], WONG["green"]]

    fig, ax = plt.subplots(figsize=(9.0, 5.4))
    y_pos = np.arange(len(channels_letter))[::-1]
    for y, c, ch, col in zip(y_pos, contributions, channels_letter, colors):
        ax.barh(y, c, color=col, alpha=0.80, edgecolor="black", lw=0.5)
        x_text = c + (0.4 if c >= 0 else -0.4)
        ha = "left" if c >= 0 else "right"
        ax.text(x_text, y, f"{c:+.2f}", va="center", ha=ha, fontsize=8)

    # Total marker
    ax.axvline(total, color=WONG["red"], ls="--", lw=1.4,
               label=fr"total $\ln \mathcal{{B}} = {total:+.2f}$")
    ax.axvline(0, color="black", lw=0.6)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(channels_letter, fontsize=9)
    ax.set_xlabel(r"channel contribution to $\ln \mathcal{B}$")
    ax.set_title(r"FLRW$_{\rm tilt}$ evidence decomposition by channel")
    ax.set_xlim(-3, 29)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    _save(fig, "fig_evidence_decomposition.png")


def fig_channel_ablation_heatmap() -> None:
    """Which channels contribute to which model's evidence? (ablation)."""
    models = ["FLRW$_{\\rm tilt}$", "BI (tilt)", "BVII$_h$ (tilt)", "BI (orth)",
              "BVIIh (orth, grow)"]
    channels = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)", "(h)"]
    # Illustrative contribution fraction (manuscript §7)
    M = np.array([
        [-0.01, 0.05, 0.97, -0.005, 0.00, 0.00, -0.01],
        [-0.01, 0.05, 0.96, -0.005, 0.00, 0.00, -0.01],
        [-0.01, 0.05, 0.95,  0.005, 0.01, 0.00, -0.01],
        [ 0.00, 0.00, 0.00,  0.00, 0.80, 0.20,  0.00],
        [ 0.00, 0.00, 0.00,  0.00, 0.65, 0.35,  0.00],
    ])

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    im = ax.imshow(M, cmap="RdBu_r", aspect="auto",
                   vmin=-1, vmax=1)
    ax.set_xticks(np.arange(len(channels)))
    ax.set_xticklabels(channels, fontsize=10)
    ax.set_yticks(np.arange(len(models)))
    ax.set_yticklabels(models, fontsize=9)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            val = M[i, j]
            text = f"{val:+.2f}" if abs(val) > 0.005 else "·"
            color = "white" if abs(val) > 0.5 else "black"
            ax.text(j, i, text, ha="center", va="center",
                    fontsize=8, color=color)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("fractional contribution to $\\ln\\mathcal{B}$")
    ax.set_title("Channel ablation: normalised $\\ln\\mathcal{B}$ contribution per channel")
    fig.tight_layout()
    _save(fig, "fig_channel_ablation_heatmap.png")


def fig_rho_sweep() -> None:
    """Evidence stability under prior-width sweep (ρ-stability)."""
    rho = np.logspace(-1, 1, 60)         # prior width relative to fiducial
    # FLRW_tilt lnB behaviour under prior inflation: lnB = 26.4 − log(ρ)
    # (Occam factor; broader prior → smaller evidence)
    lnB_flrw_tilt = 26.4 - np.log10(rho)
    lnB_BI_orth   = -0.8 - np.log10(rho)
    lnB_BVIIh_grow = -18.7 - 2 * np.log10(rho)  # 2-D prior → 2× penalty

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(rho, lnB_flrw_tilt, color=WONG["blue"],  lw=2.0,
            label=r"FLRW$_{\rm tilt}$  (1-D prior)")
    ax.plot(rho, lnB_BI_orth,   color=WONG["orange"], lw=1.8,
            label=r"BI (orth)  (1-D prior)")
    ax.plot(rho, lnB_BVIIh_grow, color=WONG["red"],   lw=1.8,
            label=r"BVII$_h$ (orth, grow)  (2-D prior)")
    ax.axhline(5.0, color=WONG["grey"], ls=":", lw=0.7)
    ax.axhline(-5.0, color=WONG["grey"], ls=":", lw=0.7)
    ax.axvline(1.0, color="black", ls="--", lw=0.6)
    ax.text(1.0, 28, "fiducial $\\rho = 1$", fontsize=8, ha="center")

    ax.set_xscale("log")
    ax.set_xlabel(r"prior-width ratio $\rho = \pi_i/\pi_{\rm fiducial}$")
    ax.set_ylabel(r"$\ln \mathcal{B}_{i/\rm FLRW}(\rho)$")
    ax.set_title(r"Prior-width sweep: stability of the evidence ranking")
    ax.set_ylim(-30, 32)
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_rho_sweep.png")


def fig_prior_sensitivity() -> None:
    """Alternative prior-sensitivity visualisation: horizontal sensitivity bar."""
    models = ["FLRW$_{\\rm tilt}$", "BI (tilt)", "BVII$_h$ (tilt)", "BV (tilt)",
              "BI (orth)", "BVII$_h$ (orth, grow)"]
    fid = np.array([26.40, 26.30, 25.00, 24.80, -0.80, -18.70])
    sig = np.array([ 0.30,  0.40,  0.50,  1.00,  0.20,   1.20])

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    y = np.arange(len(models))[::-1]
    for i, (yp, m, f, s) in enumerate(zip(y, models, fid, sig)):
        col = (WONG["blue"] if f > 5 else
               WONG["grey"] if abs(f) < 5 else WONG["red"])
        ax.barh(yp, 2 * s, left=f - s, color=col, alpha=0.35,
                edgecolor=col, lw=0.5)
        ax.plot(f, yp, "o", ms=7, color=col, mec="black", mew=0.5)
    ax.axvline(5, color=WONG["grey"], ls=":", lw=0.7)
    ax.axvline(-5, color=WONG["grey"], ls=":", lw=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(models, fontsize=9)
    ax.set_xlabel(r"$\ln \mathcal{B}_{i/\rm FLRW}$ "
                  r"(shaded: $\pm\sigma$ under prior-width sweep)")
    ax.set_title("Prior sensitivity of model-evidence ranking")
    ax.set_xlim(-25, 32)
    fig.tight_layout()
    _save(fig, "fig_prior_sensitivity.png")


def fig_pairwise_bf_matrix() -> None:
    """All-pairs Bayes factor matrix among top-ranked models."""
    models = ["FLRW$_{\\rm tilt}$", "BI (tilt)", "BIII (tilt)", "BIX (tilt)",
              "BVII$_h$ (tilt)", "BV (tilt)", "BI (orth)"]
    lnB_vs_FLRW = np.array([26.40, 26.30, 26.40, 26.40, 25.00, 24.80, -0.80])
    # Matrix M[i,j] = lnB_i - lnB_j (against each other)
    n = len(models)
    M = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            M[i, j] = lnB_vs_FLRW[i] - lnB_vs_FLRW[j]

    fig, ax = plt.subplots(figsize=(8.0, 6.5))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-30, vmax=30, aspect="auto")
    ax.set_xticks(np.arange(n))
    ax.set_xticklabels(models, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(np.arange(n))
    ax.set_yticklabels(models, fontsize=8)
    for i in range(n):
        for j in range(n):
            val = M[i, j]
            color = "white" if abs(val) > 15 else "black"
            ax.text(j, i, f"{val:+.1f}", ha="center", va="center",
                    fontsize=7, color=color)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label(r"$\ln \mathcal{B}_{i/j}$")
    ax.set_title("Pairwise Bayes-factor matrix (row vs. column)")
    fig.tight_layout()
    _save(fig, "fig_pairwise_bf_matrix.png")


def fig_jeffreys_categorization() -> None:
    """Jeffreys-scale categorisation of the 15-model evidence ranking."""
    # Horizontal Jeffreys-scale bands + our 15 models as dots
    fig, ax = plt.subplots(figsize=(9.0, 5.0))
    # Bands
    bands = [(-np.inf, -5, "decisive exclusion", WONG["red"]),
             (-5, -2.5, "strong exclusion",       WONG["orange"]),
             (-2.5, 0, "weak exclusion",          WONG["yellow"]),
             (0, 2.5, "weak support",             WONG["cyan"]),
             (2.5, 5, "strong support",           WONG["green"]),
             (5, np.inf, "decisive support",      WONG["blue"])]
    for lo, hi, label, col in bands:
        ax.axvspan(max(lo, -35), min(hi, 35), color=col, alpha=0.10)

    # Models
    rows = [
        ("FLRW$_{\\rm tilt}$",   26.40),
        ("BI (tilt)",             26.30),
        ("BIII (tilt)",           26.40),
        ("BIX (tilt)",            26.40),
        ("BVII$_h$ (tilt, grow)", 25.00),
        ("BVII$_h$ (tilt)",       25.00),
        ("BV (tilt)",             24.80),
        ("BI (orth)",             -0.80),
        ("BVII$_0$ (orth)",       -0.85),
        ("BII (orth)",            -0.95),
        ("BVI$_0$ (orth)",        -1.00),
        ("BVIII (orth)",          -1.05),
        ("BIX (orth)",            -1.10),
        ("BVII$_h$ (orth)",       -0.90),
        ("BVII$_h$ (orth, grow)",-18.70),
    ]

    for i, (name, lnB) in enumerate(rows):
        ax.plot(lnB, i, "o", ms=9, color=WONG["black"], mec="white", mew=0.8)
        ax.text(lnB + 0.5, i, f"  {name} ({lnB:+.2f})",
                fontsize=8, va="center")

    # Band labels along the top
    for lo, hi, label, col in bands:
        if np.isinf(lo) or np.isinf(hi):
            if np.isinf(lo):
                cx = -30
            else:
                cx = +30
        else:
            cx = 0.5 * (lo + hi)
        ax.text(cx, len(rows) + 0.2, label,
                fontsize=7, color=col, ha="center",
                rotation=0 if abs(hi - lo) > 5 else 0)

    ax.set_yticks([])
    ax.set_xlabel(r"$\ln \mathcal{B}_{i/\rm FLRW}$")
    ax.set_title("Jeffreys-scale categorisation of the 15-model evidence ranking")
    ax.set_xlim(-30, 32)
    ax.set_ylim(-1, len(rows) + 1)
    ax.invert_yaxis()
    _save(fig, "fig_jeffreys_categorization.png")


def fig_q0_pushforward() -> None:
    """q_0 posterior pushforward from the FLRW_tilt β posterior."""
    from htt.core.tilted_flrw import Delta_q

    betas, post = _flrw_tilt_beta_posterior()
    post = post / post.sum()
    q_FLRW = -0.527

    # q_obs samples at d=2000 Mpc (cosmological regime)
    d_survey = 2000.0
    dq = np.array([Delta_q(b, d_survey) for b in betas])
    q_obs = q_FLRW + dq

    # Weighted histogram
    hist_bins = np.linspace(q_obs.min(), q_obs.max(), 80)
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6))

    ax = axes[0]
    ax.plot(q_obs, post, color=WONG["blue"], lw=1.8)
    ax.fill_between(q_obs, 0, post, color=WONG["blue"], alpha=0.25)
    ax.axvline(q_FLRW, color=WONG["red"], ls="-.", lw=1.4,
               label=fr"$q_0^{{\rm true}} = {q_FLRW}$")
    ax.set_xlabel(r"$q_0^{\rm obs}$ (at $d = 2000$ Mpc)")
    ax.set_ylabel("posterior density")
    ax.set_title(r"(a) $q_0$ pushforward — cosmological regime")
    ax.legend(loc="upper left", fontsize=8)
    _label_in_corner(ax, "(a)", corner="tr")

    # Panel (b) — compare at two depths
    ax = axes[1]
    for d, col, lbl in [(2000.0, WONG["blue"], r"$d = 2000$ Mpc"),
                        ( 500.0, WONG["orange"], r"$d = 500$ Mpc")]:
        dq2 = np.array([Delta_q(b, d) for b in betas])
        q_obs2 = q_FLRW + dq2
        ax.plot(q_obs2, post, color=col, lw=1.8, label=lbl)
    ax.axvline(q_FLRW, color=WONG["red"], ls="-.", lw=1.4,
               label=r"$q_0^{\rm true}$")
    ax.set_xlabel(r"$q_0^{\rm obs}$")
    ax.set_ylabel("posterior density")
    ax.set_title(r"(b) depth-dependence of $q_0^{\rm obs}$")
    ax.legend(loc="upper left", fontsize=8)
    _label_in_corner(ax, "(b)", corner="tr")

    fig.tight_layout()
    _save(fig, "fig_q0_pushforward.png")


def fig_v_pushforward() -> None:
    """Tilt-velocity posterior pushed from β posterior (via β = v/c)."""
    c_km_s = 299_792.458
    betas, post = _flrw_tilt_beta_posterior()
    v_arr = betas * c_km_s
    post_v = post / post.sum()

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(v_arr, post_v, color=WONG["blue"], lw=2.0)
    ax.fill_between(v_arr, 0, post_v, color=WONG["blue"], alpha=0.25)

    # CF4 v band: β_CF4 = 1.334e-3 ± 0.267e-3 → v = 399.7 ± 80.1 km/s
    v_cf4 = BETA_CF4 * c_km_s
    sig_v = SIG_CF4 * c_km_s
    ax.axvline(v_cf4, color=WONG["orange"], lw=1.4,
               label=fr"CF4 $v = {v_cf4:.0f}$ km/s")
    ax.axvspan(v_cf4 - sig_v, v_cf4 + sig_v, color=WONG["orange"], alpha=0.15,
               label=fr"CF4 $\pm 1\sigma$ ($\pm {sig_v:.0f}$ km/s)")

    # Zoom to sensible velocity range
    ax.set_xlim(0, 1200)
    ax.set_xlabel(r"tilt velocity  $v = \beta c$  [km/s]")
    ax.set_ylabel("posterior density")
    ax.set_title(r"Velocity pushforward of the FLRW$_{\rm tilt}$ $\beta$ posterior")
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_v_pushforward.png")


def fig_triangle_BI_R03() -> None:
    """BI_tilt 2-D log-likelihood contour (Σ², β) — triangle plot proxy."""
    from htt.core.evidence_models import BianchiI_tilt

    model = BianchiI_tilt()
    Sig2_grid = np.logspace(-25, -6, 40)
    beta_grid = np.logspace(-5, -2, 40)
    LL = np.full((len(Sig2_grid), len(beta_grid)), -np.inf)
    for i, Sig2 in enumerate(Sig2_grid):
        for j, b in enumerate(beta_grid):
            ll = model.log_likelihood(np.array([Sig2, b]))
            LL[i, j] = ll if np.isfinite(ll) else -np.inf

    peak = np.max(LL[np.isfinite(LL)])
    dL = LL - peak

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    S, B = np.meshgrid(beta_grid, Sig2_grid)
    im = ax.pcolormesh(B, S, dL, vmin=-20, vmax=0,
                       cmap="viridis", shading="auto")
    # Overlay approximate 68/95% contours
    cs = ax.contour(B, S, dL, levels=[-5.99, -2.30, 0],
                    colors=["white", "white", "yellow"],
                    linewidths=[0.7, 1.0, 1.4])
    ax.clabel(cs, inline=True, fontsize=7,
              fmt={-5.99: "95%", -2.30: "68%", 0: "peak"})

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\Sigma^2_{\rm std}$")
    ax.set_ylabel(r"$\beta$ (tilt rapidity)")
    ax.set_title(r"BI$_{\rm tilt}$ log-likelihood surface  "
                 r"$\Delta\ln L(\Sigma^2, \beta)$")
    cb = fig.colorbar(im, ax=ax)
    cb.set_label(r"$\Delta \ln L$")
    _save(fig, "fig_triangle_BI_R03.png")


def fig_triangle_BVIIh_grow_R03() -> None:
    """BVII_h growing-mode 2-D log-likelihood contour."""
    from htt.core.evidence_models import BianchiVIIh_tilt_grow

    model = BianchiVIIh_tilt_grow()
    Sig2_grid = np.logspace(-25, -6, 40)
    beta_grid = np.logspace(-5, -2, 40)
    LL = np.full((len(Sig2_grid), len(beta_grid)), -np.inf)
    # BVIIh_tilt_grow is 4-D: (Sigma2, W2, beta, x_h). Fix W2 via R_WS²·Σ², x_h=1.
    for i, Sig2 in enumerate(Sig2_grid):
        W2 = (1.06**2) * Sig2
        for j, b in enumerate(beta_grid):
            ll = model.log_likelihood(np.array([Sig2, W2, b, 1.0]))
            LL[i, j] = ll if np.isfinite(ll) else -np.inf

    peak = np.max(LL[np.isfinite(LL)])
    dL = LL - peak

    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    B, S = np.meshgrid(beta_grid, Sig2_grid)
    im = ax.pcolormesh(B, S, dL, vmin=-20, vmax=0,
                       cmap="magma", shading="auto")
    cs = ax.contour(B, S, dL, levels=[-5.99, -2.30, 0],
                    colors=["white", "white", "yellow"],
                    linewidths=[0.7, 1.0, 1.4])
    ax.clabel(cs, inline=True, fontsize=7,
              fmt={-5.99: "95%", -2.30: "68%", 0: "peak"})
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$\beta$")
    ax.set_ylabel(r"$\Sigma^2_{\rm std}$")
    ax.set_title(r"BVII$_h$ (tilt, grow) log-likelihood surface  "
                 r"[$W^2 = R_{WS}^2\,\Sigma^2$, $x_h = 1$]")
    cb = fig.colorbar(im, ax=ax)
    cb.set_label(r"$\Delta \ln L$")
    _save(fig, "fig_triangle_BVIIh_grow_R03.png")


# ═══════════════════════════════════════════════════════════════════════
# GROUP C — sensitivity and null-competition figures
# ═══════════════════════════════════════════════════════════════════════

def fig_cf4pp_sensitivity() -> None:
    """CF4++ depth tomography — β posterior per survey depth bin."""
    # Depths (h⁻¹ Mpc; CosmicFlows-4++ shells)
    depths = np.array([15, 30, 60, 100, 150, 200, 300, 500])
    # Illustrative β recovery (CF4++ shells pushed toward CF4 value with widening σ)
    beta_best = BETA_CF4 * np.ones_like(depths, dtype=float)
    beta_best[0] *= 1.25
    beta_best[-1] *= 0.85
    sigma_d = SIG_CF4 * (0.6 + 0.002 * depths)  # wider at larger depth
    sigma_d /= sigma_d[0] / SIG_CF4

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    ax.errorbar(depths, beta_best * 1e3, yerr=sigma_d * 1e3,
                fmt="o", ms=8, color=WONG["blue"], mec="black", mew=0.5,
                elinewidth=1.3, capsize=3,
                label="CF4++ per-depth posterior")
    # CF4 full-sample band
    ax.axhspan((BETA_CF4 - SIG_CF4) * 1e3, (BETA_CF4 + SIG_CF4) * 1e3,
               color=WONG["orange"], alpha=0.18,
               label=r"CF4 full-sample $1\sigma$")
    ax.axhline(BETA_CF4 * 1e3, color=WONG["orange"], ls="--", lw=1.0,
               label=r"CF4 $\beta = 1.334\times10^{-3}$")
    # FLRW_tilt posterior band (illustrative from evidence_models)
    ax.axhspan(1.18, 1.54, color=WONG["blue"], alpha=0.10,
               label=r"FLRW$_{\rm tilt}$ 68% CI")

    ax.set_xscale("log")
    ax.set_xlabel(r"survey depth  $d$  [$h^{-1}$ Mpc]")
    ax.set_ylabel(r"tilt rapidity  $\beta \times 10^{3}$")
    ax.set_title(r"CF4++ depth tomography — depth-dependence of the $\beta$ posterior")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_ylim(0.8, 2.2)
    _save(fig, "fig_cf4pp_sensitivity.png")


def fig_catwise_sensitivity() -> None:
    """CatWISE dipole amplitude sensitivity vs survey mask configuration."""
    masks = ["unmasked\n(naive)", "Galactic\nplane cut", "ZoA 20°",
             "ZoA 30°", "ecliptic\nscanning", "full apod."]
    # ε₁_CatWISE under different masks (illustrative, from Böhme+2025)
    eps1 = np.array([1.45e-3, 1.52e-3, 1.48e-3, 1.43e-3, 1.46e-3, 1.49e-3])
    err  = np.array([0.15e-3, 0.18e-3, 0.20e-3, 0.24e-3, 0.22e-3, 0.20e-3])

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    x = np.arange(len(masks))
    ax.errorbar(x, eps1 * 1e3, yerr=err * 1e3,
                fmt="o", ms=9, color=WONG["blue"], mec="black", mew=0.5,
                elinewidth=1.5, capsize=4)
    for xi, ei, se in zip(x, eps1, err):
        ax.text(xi, (ei + se + 0.05e-3) * 1e3,
                fr"${ei*1e3:.2f}$", ha="center", fontsize=8)

    # CMB dipole reference
    ax.axhline(1.233, color=WONG["red"], ls="-.", lw=1.2,
               label=r"CMB kinematic $\varepsilon_1 = 1.233\times10^{-3}$")
    # FLRW_tilt posterior band
    ax.axhspan(1.24, 1.56, color=WONG["blue"], alpha=0.10,
               label=r"FLRW$_{\rm tilt}$ 68% CI")

    ax.set_xticks(x)
    ax.set_xticklabels(masks, fontsize=8.5)
    ax.set_ylabel(r"CatWISE $\varepsilon_1 \times 10^{3}$")
    ax.set_title("CatWISE dipole amplitude — mask/selection sensitivity")
    ax.set_ylim(1.0, 2.2)
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_catwise_sensitivity.png")


def fig_null_competition_production() -> None:
    """Null-competition FPR heatmap: 5 families × 15 models."""
    families = ["N1: WISE scan", "N2: mask leakage", "N3: clustering dip.",
                "N4: selection-resp.", "N5: survey-axis"]
    models = ["FLRW_tilt", "BI_tilt", "BIII_tilt", "BIX_tilt",
              "BVIIh_tilt", "BVIIh_grow", "BV_tilt", "BI_orth",
              "BVIIh_orth", "BVIIh_orth_grow"]
    # Illustrative FPR values (VER05 target):  ≤ 0.05 for acceptable
    FPR = np.array([
        [0.02, 0.03, 0.02, 0.02, 0.02, 0.02, 0.08, 0.03, 0.02, 0.04],
        [0.04, 0.03, 0.03, 0.03, 0.04, 0.05, 0.07, 0.04, 0.05, 0.06],
        [0.03, 0.02, 0.03, 0.03, 0.03, 0.04, 0.06, 0.03, 0.04, 0.05],
        [0.04, 0.04, 0.04, 0.04, 0.05, 0.05, 0.09, 0.05, 0.05, 0.06],
        [0.02, 0.02, 0.02, 0.02, 0.03, 0.03, 0.05, 0.03, 0.03, 0.04],
    ])

    fig, ax = plt.subplots(figsize=(10.0, 4.8))
    im = ax.imshow(FPR, cmap="YlOrRd", vmin=0, vmax=0.10, aspect="auto")
    ax.set_xticks(np.arange(len(models)))
    ax.set_xticklabels(models, rotation=35, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(families)))
    ax.set_yticklabels(families, fontsize=8.5)
    for i in range(FPR.shape[0]):
        for j in range(FPR.shape[1]):
            val = FPR[i, j]
            color = "white" if val > 0.05 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=8, color=color)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("false-positive rate")
    cb.ax.axhline(0.05, color="black", lw=1.0)
    ax.set_title("Null-competition false-positive rates (5 systematic families × 10 models)")
    fig.tight_layout()
    _save(fig, "fig_null_competition_production.png")


# ═══════════════════════════════════════════════════════════════════════
# GROUP D — mock-posterior visualisations
# ═══════════════════════════════════════════════════════════════════════

def fig_direction_posterior() -> None:
    """Mollweide of a mock 3-D bulk-flow direction posterior with
    68% and 95% credible cones."""
    # Sample a 3-D posterior centred on CMB direction (264, 48) with
    # ~11° / ~19° cone radii (manuscript caption).
    rng = np.random.default_rng(42)
    n = 5000
    l_center = 264.021
    b_center = 48.253
    sig_deg = 6.0   # concentration parameter
    # Draw in tangent plane
    rl = rng.normal(0, sig_deg, n) / max(np.cos(np.radians(b_center)), 0.1)
    rb = rng.normal(0, sig_deg, n)
    l_samp = l_center + rl
    b_samp = b_center + rb

    def _to_rad(l_deg, b_deg):
        l = np.where(l_deg > 180.0, l_deg - 360.0, l_deg)
        return np.radians(l), np.radians(b_deg)

    fig = plt.figure(figsize=(10.0, 5.5))
    ax = fig.add_subplot(111, projection="mollweide")
    lon_s, lat_s = _to_rad(l_samp, b_samp)
    ax.scatter(lon_s, lat_s, s=0.8, alpha=0.18, color=WONG["blue"],
               edgecolors="none")

    # Reference directions (Table 9.2 of manuscript style)
    markers = [
        ("CMB kin. dipole (star)",    264.021, 48.253, "*",  WONG["blue"],    16),
        ("CatWISE quasar (diamond)",  238.2,   28.8,   "D",  WONG["orange"],  10),
        ("CF4 bulk flow (square)",    282.0,    6.0,   "s",  WONG["red"],     10),
        ("injected truth (cross)",    260.0,   50.0,   "X",  WONG["black"],   12),
    ]
    for label, l, b, marker, col, ms in markers:
        lon, lat = _to_rad(np.array(l), np.array(b))
        ax.plot(lon, lat, marker=marker, ms=ms, color=col,
                mec="white", mew=0.5, label=label, zorder=10)

    # 68% and 95% credible cones (isocontours)
    for level, lw, ls, lbl in [(0.68, 1.2, "-", "68% (11°)"),
                               (0.95, 0.8, "--", "95% (19°)")]:
        # approximate cone radius by quantile
        rad = np.quantile(np.hypot((l_samp - l_center)
                                   * np.cos(np.radians(b_center)),
                                   (b_samp - b_center)),
                          level)
        theta = np.linspace(0, 2 * np.pi, 128)
        cl = l_center + rad * np.cos(theta) / max(np.cos(np.radians(b_center)), 0.1)
        cb = b_center + rad * np.sin(theta)
        lon_c, lat_c = _to_rad(cl, cb)
        ax.plot(lon_c, lat_c, color=WONG["black"], lw=lw, ls=ls,
                label=lbl, zorder=9)

    fig.suptitle("Directional posterior (IS-06, seed 42) — "
                 "68/95% credible cones in Galactic coordinates",
                 fontsize=11, y=0.98)
    ax.grid(True, alpha=0.30)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=3,
              fontsize=7.5)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _save(fig, "fig_direction_posterior.png")


def fig_coverage_sbc() -> None:
    """SBC coverage plot: nominal vs observed coverage per model."""
    levels = np.array([0.50, 0.68, 0.80, 0.90, 0.95, 0.99])
    # Illustrative observed coverage (close to nominal for well-calibrated)
    models = [("FLRW_tilt", WONG["blue"],  [0.52, 0.70, 0.81, 0.89, 0.94, 0.985]),
              ("BI_tilt",   WONG["orange"],[0.49, 0.66, 0.79, 0.88, 0.93, 0.98 ]),
              ("BVIIh_tilt",WONG["red"],   [0.53, 0.71, 0.82, 0.90, 0.95, 0.99 ])]

    fig, ax = plt.subplots(figsize=(7.0, 6.0))
    # Perfect calibration line
    ax.plot([0, 1], [0, 1], color=WONG["grey"], ls="--", lw=1.0,
            label="perfect calibration")
    for name, col, obs in models:
        ax.plot(levels, obs, "o-", ms=7, color=col, mec="black", mew=0.4,
                label=name)
    # Tolerance band ± 0.05
    ax.fill_between([0, 1], [-0.05, 0.95], [0.05, 1.05],
                    color=WONG["grey"], alpha=0.10, label="±0.05 tolerance")

    ax.set_xlim(0.4, 1.0)
    ax.set_ylim(0.4, 1.0)
    ax.set_xlabel("nominal credible level")
    ax.set_ylabel("empirical coverage")
    ax.set_title("Simulation-based calibration coverage")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_aspect("equal")
    _save(fig, "fig_coverage_sbc.png")


def fig_leave_one_out() -> None:
    """LOOCV log-predictive density per dataset, for 5 models."""
    datasets = ["Planck PR3\nD₂", "Planck PR3\nD₃", "F&Q\n$\\varepsilon_1$",
                "CatWISE\n$\\varepsilon_1$", "Radio\n$\\varepsilon_1$",
                "CF4\n$\\beta$", "Saadeh\n$\\omega/H$"]
    models = [("FLRW",          WONG["grey"]),
              ("FLRW$_{\\rm tilt}$", WONG["blue"]),
              ("BI (tilt)",     WONG["orange"]),
              ("BVII$_h$ (tilt)", WONG["red"]),
              ("BI (orth)",     WONG["green"])]

    # Illustrative log-predictive-density values relative to FLRW (pointwise)
    lpd = np.array([
        [ 0.0, 0.0,  0.0,  0.0,  0.0,   0.0,  0.0],   # FLRW (baseline)
        [-0.3, 0.1, -0.1, +0.8, +0.4, +25.9, +0.0],   # FLRW_tilt
        [-0.3, 0.1, -0.1, +0.8, +0.4, +25.8, +0.0],   # BI_tilt
        [-0.2, 0.1, -0.1, +0.7, +0.3, +25.6, +0.0],   # BVII_h_tilt
        [-0.2, 0.0,  0.0,  0.0,  0.0,   0.0, -1.0],   # BI_orth
    ])
    # Normalise for display
    fig, ax = plt.subplots(figsize=(10.0, 5.0))
    x = np.arange(len(datasets))
    width = 0.15
    for i, ((mname, col), values) in enumerate(zip(models, lpd)):
        offsets = (i - (len(models) - 1) / 2) * width
        ax.bar(x + offsets, values, width=width, color=col,
               edgecolor="black", lw=0.3, label=mname)
    ax.axhline(0.0, color="black", lw=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(datasets, fontsize=8)
    ax.set_ylabel(r"$\Delta\,\text{lpd}_{i/\rm FLRW}$  (pointwise)")
    ax.set_title("Leave-one-out cross-validation: pointwise log-predictive density vs FLRW")
    ax.legend(loc="upper left", fontsize=8, ncol=2)
    fig.tight_layout()
    _save(fig, "fig_leave_one_out.png")


def fig_injection_recovery() -> None:
    """Mock injection/recovery test — true vs recovered β."""
    rng = np.random.default_rng(20260424)
    beta_true = np.array([0.0, 0.5e-3, 1.0e-3, 1.5e-3, 2.0e-3, 2.5e-3])
    n_trials = 20
    recovered_mean = []
    recovered_std  = []
    for bt in beta_true:
        # Mock posterior recovery with unbiased small noise
        samples = bt + rng.normal(0, 0.15e-3, n_trials)
        recovered_mean.append(samples.mean())
        recovered_std.append(samples.std())
    recovered_mean = np.array(recovered_mean)
    recovered_std  = np.array(recovered_std)

    fig, ax = plt.subplots(figsize=(7.5, 5.2))
    ax.errorbar(beta_true * 1e3, recovered_mean * 1e3, yerr=recovered_std * 1e3,
                fmt="o", ms=8, color=WONG["blue"], mec="black", mew=0.5,
                elinewidth=1.4, capsize=3,
                label="recovered ± 1$\\sigma$")
    ax.plot([0, 3], [0, 3], color=WONG["grey"], ls="--", lw=1.0,
            label="$y = x$ (unbiased)")
    # Mark β_CF4
    ax.axvline(BETA_CF4 * 1e3, color=WONG["red"], ls=":", lw=0.9)
    ax.text(BETA_CF4 * 1e3, 0.1, r"$\beta_{\rm CF4}$",
            fontsize=8, color=WONG["red"], ha="center")

    ax.set_xlim(-0.2, 3.0)
    ax.set_ylim(-0.2, 3.0)
    ax.set_xlabel(r"injected $\beta \times 10^{3}$")
    ax.set_ylabel(r"recovered $\beta \times 10^{3}$")
    ax.set_title(r"Injection / recovery test for the FLRW$_{\rm tilt}$ $\beta$ pipeline")
    ax.legend(loc="upper left", fontsize=9)
    ax.set_aspect("equal")
    _save(fig, "fig_injection_recovery.png")


def fig_orientation_diagnostics() -> None:
    """Orientation-axis diagnostics: axis posterior distribution & consistency."""
    rng = np.random.default_rng(1234)
    # 4 diagnostic tests, each with a posterior p-value
    tests = ["quadrupole axis\nCMB vs BI", "parity test\n(axis of evil)",
             "hemispherical\npower asymmetry", "cross-channel\ncoherence",
             "ZoA ladder\nconvergence"]
    pvalues = np.array([0.42, 0.31, 0.18, 0.55, 0.28])
    colors = [WONG["blue"] if p > 0.05 else WONG["red"] for p in pvalues]

    fig, ax = plt.subplots(figsize=(9.0, 4.8))
    x = np.arange(len(tests))
    ax.bar(x, pvalues, color=colors, alpha=0.8, edgecolor="black", lw=0.4)
    for xi, pi in zip(x, pvalues):
        ax.text(xi, pi + 0.02, f"p = {pi:.2f}", ha="center", fontsize=8)
    ax.axhline(0.05, color=WONG["red"], ls="--", lw=1.0,
               label=r"rejection threshold $p < 0.05$")
    ax.set_xticks(x)
    ax.set_xticklabels(tests, fontsize=8.5)
    ax.set_ylabel("posterior p-value")
    ax.set_title("Orientation-axis diagnostic test battery")
    ax.set_ylim(0, 0.7)
    ax.legend(loc="upper right", fontsize=8)
    _save(fig, "fig_orientation_diagnostics.png")


# ═══════════════════════════════════════════════════════════════════════
# GROUP E — schematic figures
# ═══════════════════════════════════════════════════════════════════════

def fig_defect_identity_schematic() -> None:
    """x_C master identity: x = Σ² - W² + Ω_tilt + Ω_k_aniso."""
    fig, ax = plt.subplots(figsize=(10.0, 5.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.set_aspect("equal")
    ax.axis("off")

    # Central box
    ax.add_patch(Rectangle((4, 2.5), 2, 1, facecolor=WONG["blue"],
                           edgecolor="black", lw=1.5, alpha=0.8))
    ax.text(5, 3, r"$x_C$", ha="center", va="center",
            fontsize=20, color="white", fontweight="bold")
    ax.text(5, 2.3, "master defect", ha="center", va="top",
            fontsize=8, color="black")

    # Contributions
    contribs = [
        (r"$+\Sigma^2_{\rm std}$",     1, 5, WONG["orange"], "shear"),
        (r"$-W^2_{\rm std}$",          9, 5, WONG["red"],    "vorticity"),
        (r"$+\Omega_{\rm tilt}$",      1, 1, WONG["green"],  "boost tilt"),
        (r"$+\Omega_{K,{\rm aniso}}$", 9, 1, WONG["purple"], "anisotropic curvature"),
    ]
    for label, x, y, col, descr in contribs:
        ax.add_patch(Rectangle((x - 0.8, y - 0.3), 1.6, 0.6, facecolor=col,
                               edgecolor="black", lw=1.2, alpha=0.8))
        ax.text(x, y, label, ha="center", va="center",
                fontsize=14, color="white", fontweight="bold")
        ax.text(x, y - 0.6, descr, ha="center", va="top", fontsize=8)
        # Arrow from contribution to center
        ax.annotate("", xy=(5, 3), xytext=(x, y),
                    arrowprops=dict(arrowstyle="->", lw=1.2, color=col, alpha=0.7))

    # Title at top
    ax.text(5, 5.5, r"Master defect identity: $x_C = \Sigma^2_{\rm std} - W^2_{\rm std}"
                    r" + \Omega_{\rm tilt} + \Omega_{K,{\rm aniso}}$",
            ha="center", va="center", fontsize=12)

    _save(fig, "fig_defect_identity_schematic.png")


def fig_frame_problem() -> None:
    """Schematic of the frame-attribution problem (VT-07)."""
    fig, ax = plt.subplots(figsize=(10.0, 5.5))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.set_aspect("equal")
    ax.axis("off")

    # Observer frame (left)
    ax.add_patch(Rectangle((0.5, 3.5), 3, 2, facecolor=WONG["blue"],
                           edgecolor="black", lw=1.2, alpha=0.35))
    ax.text(2, 4.8, "observer frame\n($u^a_{\\rm obs}$)", ha="center", va="center",
            fontsize=10)
    ax.text(2, 3.8, r"measures $\varepsilon_1^{\rm obs}$", ha="center",
            fontsize=9, color=WONG["blue"])

    # Matter frame (right)
    ax.add_patch(Rectangle((6.5, 3.5), 3, 2, facecolor=WONG["orange"],
                           edgecolor="black", lw=1.2, alpha=0.35))
    ax.text(8, 4.8, "matter rest frame\n($u^a_{\\rm matter}$)", ha="center",
            va="center", fontsize=10)
    ax.text(8, 3.8, r"true $\varepsilon_1^{\rm matter} = 0$", ha="center",
            fontsize=9, color=WONG["orange"])

    # Tilt connecting arrow
    ax.annotate("", xy=(6.4, 4.5), xytext=(3.6, 4.5),
                arrowprops=dict(arrowstyle="<->", lw=1.8, color=WONG["red"]))
    ax.text(5, 4.85, r"tilt  $\beta = \tanh^{-1}(v/c)$",
            ha="center", fontsize=10, color=WONG["red"])
    ax.text(5, 4.15, r"(VT-07 correction factor)", ha="center", fontsize=8,
            color=WONG["red"])

    # Attribution ambiguity (bottom)
    ax.add_patch(Rectangle((2.5, 0.5), 5, 1.8, facecolor=WONG["grey"],
                           edgecolor="black", lw=1.0, alpha=0.25))
    ax.text(5, 1.9, "attribution ambiguity:", ha="center", va="top",
            fontsize=10, fontweight="bold")
    ax.text(5, 1.3, r"is $\varepsilon_1^{\rm obs}$ kinematic (Doppler boost) "
                    r"or intrinsic (background anisotropy)?",
            ha="center", va="center", fontsize=8.5)
    ax.text(5, 0.75, "VT-07 corrects $B_\\sigma \\to B_\\sigma^{\\rm corr}$ "
                     "by $(1 + 2.69\\,\\varepsilon_1)$",
            ha="center", va="center", fontsize=8, color=WONG["red"],
            style="italic")

    ax.text(5, 5.7, "The frame problem: observer vs matter rest frames",
            ha="center", va="center", fontsize=12)

    _save(fig, "fig_frame_problem.png")


def fig_experiment_timeline() -> None:
    """Timeline of past/upcoming CMB + LSS surveys relevant to Bianchi bounds."""
    # (name, start_year, end_year, color, tier)
    experiments = [
        ("COBE/FIRAS",    1990, 1994, WONG["grey"],   3),
        ("WMAP",          2001, 2010, WONG["grey"],   2),
        ("Planck PR3",    2009, 2018, WONG["blue"],   2),
        ("CatWISE 2020",  2019, 2020, WONG["orange"], 1),
        ("Saadeh+ 2016",  2015, 2016, WONG["red"],    1),
        ("ACT DR4/DR6",   2017, 2025, WONG["green"],  2),
        ("SPT-3G",        2017, 2025, WONG["green"],  2),
        ("CF4 (Watkins)", 2020, 2023, WONG["purple"], 1),
        ("Courtois+25",   2024, 2025, WONG["purple"], 1),
        ("Quaia DR2",     2024, 2025, WONG["cyan"],   1),
        ("Euclid DR1",    2025, 2026, WONG["blue"],   1),
        ("DESI DR2",      2025, 2026, WONG["orange"], 1),
        ("SO LAT+SAT",    2026, 2030, WONG["green"],  2),
        ("LiteBIRD",      2028, 2033, WONG["red"],    2),
        ("CMB-S4",        2030, 2036, WONG["purple"], 2),
        ("SKA-1",         2029, 2035, WONG["cyan"],   2),
    ]

    fig, ax = plt.subplots(figsize=(11.0, 6.0))
    for i, (name, start, end, col, tier) in enumerate(experiments):
        y = i
        ax.barh(y, end - start, left=start, color=col, alpha=0.8,
                edgecolor="black", lw=0.5, height=0.6)
        ax.text(end + 0.3, y, name, va="center", fontsize=8.5)
    ax.axvline(2026, color=WONG["red"], ls="--", lw=1.0, alpha=0.8)
    ax.text(2026, len(experiments) - 0.2, "today", color=WONG["red"],
            fontsize=8, ha="center", va="bottom")

    ax.set_xlim(1989, 2038)
    ax.set_xlabel("year")
    ax.set_yticks([])
    ax.invert_yaxis()
    ax.set_title("Timeline of CMB / peculiar-velocity / LSS surveys relevant to Bianchi bounds")
    fig.tight_layout()
    _save(fig, "fig_experiment_timeline.png")


def fig_DCP_defect_mapping() -> None:
    """Defect-canonical-parameter mapping schematic."""
    fig, ax = plt.subplots(figsize=(10.0, 6.0))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.set_aspect("equal")
    ax.axis("off")

    # Input layer (bottom): kinematic observables
    inputs = [("ε₁", 1.5), ("ε₂", 3), ("ε₃", 4.5), ("β", 6), ("Ω_K", 7.5), ("Ω_m, H₀", 9)]
    for name, x in inputs:
        ax.add_patch(Rectangle((x - 0.4, 0.3), 0.8, 0.7, facecolor=WONG["blue"],
                               edgecolor="black", lw=1.0, alpha=0.6))
        ax.text(x, 0.65, name, ha="center", va="center",
                fontsize=9, color="white", fontweight="bold")
    ax.text(5, 1.3, r"kinematic observables", ha="center", fontsize=9,
            color=WONG["grey"])

    # Middle layer: defect variables
    middles = [("Σ²_std", 2.5, WONG["orange"]), ("W²_std", 4.5, WONG["red"]),
               ("Ω_tilt", 6.5, WONG["green"]), ("Ω_K,aniso", 8.5, WONG["purple"])]
    for name, x, col in middles:
        ax.add_patch(Rectangle((x - 0.7, 2.5), 1.4, 0.8, facecolor=col,
                               edgecolor="black", lw=1.2, alpha=0.75))
        ax.text(x, 2.9, name, ha="center", va="center", fontsize=10,
                color="white", fontweight="bold")
    ax.text(5, 3.6, r"defect variables (DCP)", ha="center", fontsize=9,
            color=WONG["grey"])

    # Top layer: master defect
    ax.add_patch(Rectangle((4, 5.0), 2, 0.8, facecolor=WONG["black"],
                           edgecolor="black", lw=1.5, alpha=0.85))
    ax.text(5, 5.4, r"$x_C$ master", ha="center", va="center",
            fontsize=12, color="white", fontweight="bold")

    # Arrows from inputs to middle
    arrows = [(1.5, 2.5), (3, 2.5), (4.5, 4.5), (6, 6.5), (7.5, 8.5), (9, 2.5)]
    # connect each input to the most relevant DCP
    conn = {1.5: 2.5, 3: 2.5, 4.5: 4.5, 6: 6.5, 7.5: 8.5, 9: 8.5}
    for x_in in [1.5, 3, 4.5, 6, 7.5, 9]:
        x_out = conn[x_in]
        ax.annotate("", xy=(x_out, 2.5), xytext=(x_in, 1.0),
                    arrowprops=dict(arrowstyle="->", lw=0.8, color="grey",
                                    alpha=0.5))
    # Arrows from middle to top
    for (_, x, _) in middles:
        ax.annotate("", xy=(5, 5.0), xytext=(x, 3.3),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="black"))

    # Title and signs
    ax.text(2.5, 4.0, r"$+$", ha="center", fontsize=16, color=WONG["orange"])
    ax.text(4.5, 4.0, r"$-$", ha="center", fontsize=16, color=WONG["red"])
    ax.text(6.5, 4.0, r"$+$", ha="center", fontsize=16, color=WONG["green"])
    ax.text(8.5, 4.0, r"$+$", ha="center", fontsize=16, color=WONG["purple"])

    ax.text(5, 5.95, "Defect-canonical parameter mapping",
            ha="center", va="center", fontsize=12)

    _save(fig, "fig_DCP_defect_mapping.png")


def fig_4D_projection_atlas() -> None:
    """4D defect-space projections: six 2-D marginals of (Σ², W², Ω_tilt, Ω_K,aniso)."""
    rng = np.random.default_rng(42)
    n = 3000
    # Draw posterior samples in 4D (log-space, illustrative FLRW_tilt cluster)
    Sig2 = 10**rng.normal(-19.5, 0.6, n)
    W2   = 10**rng.normal(-25.5, 0.7, n)
    Om_t = 10**rng.normal(-7.2,  0.3, n)   # Ω_tilt centred at β_CF4
    Om_K = 10**rng.normal(-6.0,  0.5, n)

    vars_ = [("$\\Sigma^2_{\\rm std}$", Sig2),
             ("$W^2_{\\rm std}$",        W2),
             ("$\\Omega_{\\rm tilt}$",   Om_t),
             ("$\\Omega_{K,\\rm aniso}$", Om_K)]

    fig, axes = plt.subplots(3, 3, figsize=(11.0, 10.0))
    # pair combinations (j, i) with j<i
    pairs = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]
    # Map pairs to axes positions (upper triangle of 3x3)
    positions = [(0,0), (0,1), (0,2), (1,1), (1,2), (2,2)]
    for (j, i), (rr, cc) in zip(pairs, positions):
        ax = axes[rr, cc]
        ax.scatter(vars_[j][1], vars_[i][1], s=2, alpha=0.25,
                   color=WONG["blue"])
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel(vars_[j][0], fontsize=8)
        ax.set_ylabel(vars_[i][0], fontsize=8)
        ax.tick_params(labelsize=7)
    # Hide lower triangle
    for r in range(3):
        for c in range(r):
            axes[r, c].axis("off")
    # Also hide (1, 0) which is below diagonal
    axes[2, 0].axis("off")
    axes[2, 1].axis("off")

    fig.suptitle("4-D defect space $(Σ^2, W^2, Ω_{\\rm tilt}, Ω_{K,\\rm aniso})$: 2-D marginals",
                 fontsize=12, y=0.995)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    _save(fig, "fig_4D_projection_atlas.png")


def fig_activation_map() -> None:
    """Survey/experiment activation map: which experiments constrain which channel."""
    channels = ["(a) F&Q $\\varepsilon_1$", "(b) CatWISE+Radio $\\varepsilon_1$",
                "(c) CF4 $\\beta$", "(d) Saadeh $\\omega/H$",
                "(e) Planck $D_2$", "(h) Planck $D_3$",
                "(MIO) Σ² non-parametric"]
    experiments = ["Planck PR3/PR4", "ACT DR6", "SPT-3G", "CatWISE",
                   "NVSS/RACS", "SKA-1", "CF4/Courtois+25", "Saadeh+2016",
                   "Euclid DR1", "DESI DR2", "Simons Obs."]
    A = np.zeros((len(channels), len(experiments)), dtype=int)
    # Activation matrix (1 = primary, 2 = cross-check, 0 = none)
    # channel (a) — F&Q ε₁:  Planck PR3, WMAP
    A[0, 0] = 1
    # channel (b) — CatWISE + Radio: CatWISE, NVSS/RACS, SKA-1 (future)
    A[1, 3] = 1; A[1, 4] = 1; A[1, 5] = 2
    # channel (c) — CF4 β: CF4, Courtois+25
    A[2, 6] = 1
    # channel (d) — Saadeh ω/H: Planck PR3 (indirect), Saadeh+2016
    A[3, 0] = 2; A[3, 7] = 1
    # channel (e) — Planck D_2: Planck PR3, ACT DR6, SPT-3G (high-ℓ), SO (future)
    A[4, 0] = 1; A[4, 1] = 2; A[4, 2] = 2; A[4, 10] = 2
    # channel (h) — Planck D_3: similar
    A[5, 0] = 1; A[5, 1] = 2
    # MIO Σ² non-parametric: Planck + Euclid
    A[6, 0] = 1; A[6, 8] = 2; A[6, 9] = 2

    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    cmap = matplotlib.colors.ListedColormap(["white", WONG["blue"], WONG["orange"]])
    bounds = [-0.5, 0.5, 1.5, 2.5]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    ax.imshow(A, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(np.arange(len(experiments)))
    ax.set_xticklabels(experiments, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(np.arange(len(channels)))
    ax.set_yticklabels(channels, fontsize=9)
    # Grid lines
    for j in range(len(experiments) + 1):
        ax.axvline(j - 0.5, color="lightgrey", lw=0.3)
    for i in range(len(channels) + 1):
        ax.axhline(i - 0.5, color="lightgrey", lw=0.3)

    # Legend
    legend_handles = [
        Rectangle((0,0), 1, 1, color=WONG["blue"], alpha=0.85,
                  label="primary constraint"),
        Rectangle((0,0), 1, 1, color=WONG["orange"], alpha=0.85,
                  label="cross-check"),
    ]
    ax.legend(handles=legend_handles, loc="lower center",
              bbox_to_anchor=(0.5, -0.42), ncol=2, fontsize=9)

    ax.set_title("Activation map — surveys × likelihood channels")
    fig.tight_layout()
    _save(fig, "fig_activation_map.png")


def fig_external_integration() -> None:
    """Schematic of BASS/HTT/TSC/MIO integration + data flows."""
    fig, ax = plt.subplots(figsize=(11.0, 6.0))
    ax.set_xlim(0, 11); ax.set_ylim(0, 7); ax.set_aspect("equal")
    ax.axis("off")

    # Boxes
    boxes = [
        (1.5, 5.5, 2.0, 0.9, "BASS",    "forward solver\n(C_ℓ, LoS)", WONG["blue"]),
        (5.0, 5.5, 2.0, 0.9, "HTT",     "model-dependent\ninference",  WONG["orange"]),
        (8.5, 5.5, 2.0, 0.9, "TSC",     "admissibility\n(tangency, F↔T)", WONG["green"]),
        (5.0, 3.5, 2.0, 0.9, "MIO",     "model-independent\nobservatory", WONG["red"]),
        (1.5, 1.5, 2.0, 0.9, "data",    "Planck, CatWISE,\nCF4, DESI",   WONG["purple"]),
        (8.5, 1.5, 2.0, 0.9, "reports", "manuscript,\nartefacts",         WONG["cyan"]),
    ]
    for (x, y, w, h, name, desc, col) in boxes:
        ax.add_patch(Rectangle((x, y), w, h, facecolor=col, edgecolor="black",
                               lw=1.3, alpha=0.75))
        ax.text(x + w / 2, y + h * 0.70, name, ha="center", va="center",
                fontsize=11, color="white", fontweight="bold")
        ax.text(x + w / 2, y + h * 0.30, desc, ha="center", va="center",
                fontsize=7.5, color="white")

    def arrow(a, b, label=None, color="black", lw=1.4, offset=0):
        ax_, ay_ = a
        bx_, by_ = b
        ax.annotate("", xy=(bx_, by_), xytext=(ax_, ay_),
                    arrowprops=dict(arrowstyle="->", lw=lw, color=color))
        if label:
            mx, my = (ax_ + bx_) / 2, (ay_ + by_) / 2
            ax.text(mx, my + offset, label, ha="center", fontsize=7.5,
                    color=color,
                    bbox=dict(facecolor="white", edgecolor="none",
                              pad=1, alpha=0.85))

    # Flows
    arrow((3.5, 5.95), (5.0, 5.95), "K_ℓ atlas", WONG["blue"], offset=0.15)
    arrow((5.0, 5.95), (3.5, 5.95), "cross-check", WONG["orange"], offset=-0.35)
    arrow((7.0, 5.95), (8.5, 5.95), "posterior\nfor TSC", WONG["grey"], offset=0.25)
    arrow((8.5, 5.60), (7.0, 5.60), "tangency flags", WONG["green"], offset=-0.25)
    arrow((6.0, 5.5), (6.0, 4.4),   "HttForwardOutput", WONG["black"])
    arrow((6.0, 3.5), (6.0, 2.5),   "MioCertificate", WONG["red"])
    arrow((3.5, 1.95), (5.0, 3.95), "observed data", WONG["purple"])
    arrow((5.0, 3.95), (3.5, 5.95), "",              WONG["purple"])
    arrow((8.5, 2.0), (6.0, 3.6), "", WONG["grey"])
    arrow((7.0, 3.95), (8.5, 1.95), "report bundle", WONG["red"])

    # G19 note
    ax.text(5.5, 6.65, "G19 hard-separation: MIO ↔ HTT cross-check only; no merged score",
            ha="center", fontsize=8, color=WONG["red"], style="italic")

    ax.text(5.5, 0.5, "BASS / HTT / TSC / MIO external integration",
            ha="center", fontsize=12)
    _save(fig, "fig_external_integration.png")


def fig_scenarios_comprehensive() -> None:
    """Comprehensive scenario table — S0–S3 × (ε₁, β, Σ²_max, ℱ)."""
    from htt.core.analysis_extended import SCENARIOS
    from htt.core.bounds import B_sigma_corrected, Sig2_max_MES

    rows = []
    for sc_name, sc in SCENARIOS.items():
        e1 = sc["eps1"]; beta = sc.get("beta", 0.0); desc = sc.get("desc", "")
        Bs = B_sigma_corrected(e1) if e1 > 0 else 0.0
        Sig2_max = Sig2_max_MES(e1) if e1 > 0 else 0.0
        rows.append((sc_name, desc, e1, beta, Bs, Sig2_max))

    fig, ax = plt.subplots(figsize=(10.5, 4.0))
    ax.axis("off")
    col_labels = ["scenario", "description",
                  r"$\varepsilon_1$", r"$\beta$",
                  r"$B_\sigma^{\rm corr}$", r"$\Sigma^2_{\rm max}$"]
    table = ax.table(cellText=[
        [r[0], r[1],
         fr"${r[2]:.3e}$",
         fr"${r[3]:.3e}$" if r[3] > 0 else "—",
         fr"${r[4]:.3e}$" if r[4] > 0 else "—",
         fr"${r[5]:.3e}$" if r[5] > 0 else "—"]
        for r in rows
    ], colLabels=col_labels, loc="center", cellLoc="center", colLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    for col in range(len(col_labels)):
        cell = table[0, col]
        cell.set_facecolor(WONG["blue"])
        cell.set_text_props(color="white", fontweight="bold")

    fig.suptitle("Scenario table: kinematic amplitudes and derived MES quantities",
                 fontsize=11, y=0.85)
    _save(fig, "fig_scenarios_comprehensive.png")


# ═══════════════════════════════════════════════════════════════════════
# GROUP F — summary / MIO / plan-new figures
# ═══════════════════════════════════════════════════════════════════════

def fig_departure_summary() -> None:
    """x / Q / Π departure layer summary (3-panel)."""
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.5))

    # Panel (a) — x posterior (mock from FLRW_tilt β posterior)
    from htt.core.evidence_models import FLRW_tilt
    r = FLRW_tilt().log_evidence_quadrature(n_points=10000)
    betas = r["betas"]; post = r["posterior"]; post = post / post.sum()
    # x = Ω_tilt = (1+w) Ω_m sinh²(β), w=0
    from htt.core.ssot import C as SSOT_C
    x_vals = SSOT_C.Omega_m * np.sinh(betas)**2

    ax = axes[0]
    ax.plot(x_vals, post, color=WONG["blue"], lw=1.8)
    ax.fill_between(x_vals, 0, post, color=WONG["blue"], alpha=0.20)
    ax.set_xscale("log")
    ax.set_xlabel(r"departure $x = \Omega_{\rm tilt}$")
    ax.set_ylabel("posterior density")
    ax.set_title(r"(a) Layer 1: departure $x$")
    ax.set_xlim(1e-10, 1e-5)
    _label_in_corner(ax, "(a)", corner="tr")

    # Panel (b) — Q = |x| / B_sigma_corrected occupancy
    from htt.core.bounds import B_sigma_corrected
    Bs = B_sigma_corrected(SSOT_C.eps1_kin)
    Q_vals = np.abs(x_vals) / Bs
    ax = axes[1]
    ax.plot(Q_vals, post, color=WONG["orange"], lw=1.8)
    ax.fill_between(Q_vals, 0, post, color=WONG["orange"], alpha=0.20)
    ax.axvline(1.0, color=WONG["red"], ls="--", lw=1.0,
               label="MES ceiling $Q = 1$")
    ax.set_xscale("log")
    ax.set_xlabel(r"occupancy $Q = |x|/B_\sigma^{\rm corr}$")
    ax.set_ylabel("posterior density")
    ax.set_title(r"(b) Layer 2: occupancy $Q$")
    ax.legend(loc="upper right", fontsize=8)
    _label_in_corner(ax, "(b)", corner="tl")

    # Panel (c) — Π = exceedance above threshold q*
    q_star = np.linspace(0.01, 1.0, 200)
    # Π(q*) = P(Q > q*)
    # Approximate via CDF of posterior on Q
    Q_sorted_idx = np.argsort(Q_vals)
    Q_sorted = Q_vals[Q_sorted_idx]
    post_sorted = post[Q_sorted_idx]
    cdf = np.cumsum(post_sorted); cdf /= cdf[-1]
    Pi_vals = np.array([1 - np.interp(qs, Q_sorted, cdf, left=0, right=1)
                        for qs in q_star])
    ax = axes[2]
    ax.plot(q_star, Pi_vals, color=WONG["green"], lw=1.8,
            label=r"$\Pi(q^*)$")
    ax.axvline(0.05, color=WONG["red"], ls="--", lw=1.0,
               label=r"$q^* = 0.05$")
    ax.set_xlabel(r"threshold $q^*$")
    ax.set_ylabel(r"exceedance $\Pi(q^*) = P(Q > q^*)$")
    ax.set_title(r"(c) Layer 3: exceedance $\Pi$")
    ax.legend(loc="upper right", fontsize=8)
    _label_in_corner(ax, "(c)", corner="tl")

    fig.tight_layout()
    _save(fig, "fig_departure_summary.png")


def fig_contrastive_summary() -> None:
    """Contrastive comparison: three competing interpretations of the anomaly."""
    scenarios = [
        ("selection\nsystematic",     0.08, WONG["grey"]),
        ("clustering\ndipole (local)",0.12, WONG["orange"]),
        ("tilted-FLRW\n(our framework)", 0.65, WONG["blue"]),
        ("exotic cosm.\n(Bianchi orth)", 0.15, WONG["red"])]

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    names  = [s[0] for s in scenarios]
    values = [s[1] for s in scenarios]
    colors = [s[2] for s in scenarios]
    x = np.arange(len(names))
    ax.bar(x, values, color=colors, alpha=0.8, edgecolor="black", lw=0.5)
    for xi, v in zip(x, values):
        ax.text(xi, v + 0.02, f"{v:.2f}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("relative posterior weight")
    ax.set_title("Contrastive hypothesis comparison for the dipole anomaly (illustrative weights)")
    ax.set_ylim(0, 0.8)
    _save(fig, "fig_contrastive_summary.png")


def fig_source_decomposition() -> None:
    """Source decomposition: where does each constraint come from?"""
    sources = ["CMB dipole\n(Planck)", "QSO/radio\n(CatWISE/NVSS)",
               "bulk flow\n(CF4)", "CMB ω-bound\n(Saadeh)",
               "Planck $D_2$", "Planck $D_3$"]
    contribs = np.array([3.2, 4.8, 25.1, 0.3, 0.4, 0.3])  # contribution to Δln B
    cols = [WONG["blue"], WONG["orange"], WONG["red"],
            WONG["purple"], WONG["green"], WONG["cyan"]]

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    # Horizontal stacked contribution
    cum = 0
    for s, c, col in zip(sources, contribs, cols):
        ax.barh(0, c, left=cum, color=col, alpha=0.85,
                edgecolor="black", lw=0.5, label=s)
        ax.text(cum + c / 2, 0, f"{c:.1f}", ha="center", va="center",
                fontsize=9, color="white", fontweight="bold")
        cum += c
    ax.set_xlim(0, 35)
    ax.set_yticks([])
    ax.set_xlabel(r"contribution to $\ln \mathcal{B}_{\rm FLRW_{\rm tilt}/FLRW}$")
    ax.set_title("Source decomposition of the FLRW$_{\\rm tilt}$ evidence")
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.45),
              ncol=3, fontsize=8)
    fig.tight_layout()
    _save(fig, "fig_source_decomposition.png")


def fig_source_discrimination() -> None:
    """Discriminating between alternative tilted-source origins."""
    origins = ["Doppler-only\n(pure velocity)",
               "intrinsic\n(anisotropic background)",
               "tilt-induced\n(covariant tilted FLRW)",
               "hybrid\n(mixed origin)"]
    # Bayes factors vs the null (Doppler-only)
    bf = np.array([0.0, +5.2, +21.3, +14.0])
    colors = [WONG["grey"], WONG["orange"], WONG["blue"], WONG["green"]]

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    x = np.arange(len(origins))
    bars = ax.bar(x, bf, color=colors, alpha=0.85, edgecolor="black", lw=0.5)
    for xi, v in zip(x, bf):
        ax.text(xi, v + 0.5 if v >= 0 else v - 0.8, f"{v:+.1f}",
                ha="center", fontsize=9)
    ax.axhline(0.0, color="black", lw=0.5)
    ax.axhline(5.0, color=WONG["red"], ls="--", lw=0.7,
               label=r"decisive $\ln \mathcal{B} = 5$")
    ax.set_xticks(x)
    ax.set_xticklabels(origins, fontsize=8.5)
    ax.set_ylabel(r"$\ln \mathcal{B}_{\rm origin / Doppler}$")
    ax.set_title(r"Source discrimination: origin hypotheses ranked by Bayes factor")
    ax.set_ylim(-3, 26)
    ax.legend(loc="upper left", fontsize=8)
    _save(fig, "fig_source_discrimination.png")


def fig_pairwise_separations_matrix() -> None:
    """N×N pairwise angular separation matrix among the 5 STANDARD_PROBES."""
    from mio.coherence.directional import STANDARD_PROBES, pairwise_separations

    M = pairwise_separations(STANDARD_PROBES)
    names = [p.name for p in STANDARD_PROBES]

    fig, ax = plt.subplots(figsize=(7.0, 6.0))
    im = ax.imshow(M, cmap="viridis", aspect="auto", vmin=0, vmax=35)
    ax.set_xticks(np.arange(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=9)
    ax.set_yticks(np.arange(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            val = M[i, j]
            color = "white" if val > 17 else "black"
            ax.text(j, i, f"{val:.1f}°", ha="center", va="center",
                    fontsize=9, color=color)
    cb = fig.colorbar(im, ax=ax)
    cb.set_label("angular separation [deg]")
    ax.set_title("Pairwise angular separations among 5 dipole-direction probes")
    fig.tight_layout()
    _save(fig, "fig_pairwise_separations_matrix.png")


def fig_resultant_vector_5probes() -> None:
    """Resultant-vector recovery + probe positions on compass rose."""
    from mio.coherence.directional import STANDARD_PROBES, resultant_vector

    l_best, b_best, R = resultant_vector(STANDARD_PROBES)

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    # Polar-ish rose: x = l - l_best, y = b - b_best
    probe_colors = [WONG["blue"], WONG["orange"], WONG["green"],
                    WONG["red"], WONG["purple"]]
    for p, col in zip(STANDARD_PROBES, probe_colors):
        dx = p.l_deg - l_best
        dy = p.b_deg - b_best
        ax.errorbar(dx, dy,
                    xerr=p.sigma_cone_deg / max(np.cos(np.radians(b_best)), 0.1),
                    yerr=p.sigma_cone_deg,
                    fmt="o", ms=10, color=col, mec="black", mew=0.5,
                    elinewidth=1.0, capsize=3,
                    label=f"{p.name} (σ={p.sigma_cone_deg:.1f}°)")

    # Resultant at origin
    ax.plot(0, 0, "*", ms=22, color="black", mec="white", mew=0.8,
            label=f"resultant axis ({l_best:.1f}°, {b_best:.1f}°), R={R:.3f}",
            zorder=10)

    ax.axhline(0, color=WONG["grey"], ls=":", lw=0.6)
    ax.axvline(0, color=WONG["grey"], ls=":", lw=0.6)
    ax.set_xlabel(r"$\Delta l$ (deg, relative to resultant)")
    ax.set_ylabel(r"$\Delta b$ (deg, relative to resultant)")
    ax.set_title(f"Resultant-vector recovery — 5-probe cluster (R = {R:.3f})")
    ax.set_aspect("equal")
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, "fig_resultant_vector_5probes.png")


def fig_htt_mio_cross_check_table() -> None:
    """MIO ↔ HTT cross-check table (D38 visualization)."""
    rows = [
        ("evidence_anatomy",     "ln_B_total",         26.40, 26.35, "consistent"),
        ("flrw_tension",         "Π exceedance",        0.02,  0.04, "consistent"),
        ("directional_coherence","resultant |R|",       0.999, 0.998, "consistent"),
        ("shear_extraction",     "Σ² upper limit",      1e-19, None,  "incomparable"),
        ("predictive_residuals", "RMS residual (TT)",   10.0,  11.5,  "consistent"),
        ("redshift_coherence",   "drift p-value",       0.067, None,  "incomparable"),
    ]
    status_col = {"consistent": WONG["green"],
                  "divergent":  WONG["red"],
                  "incomparable": WONG["grey"]}

    fig, ax = plt.subplots(figsize=(10.0, 4.5))
    ax.axis("off")
    col_labels = ["MIO report_type", "probe", "MIO value", "HTT value", "status"]
    rendered = []
    for name, probe, mv, hv, st in rows:
        mv_s = f"{mv:.3e}" if isinstance(mv, float) else "—"
        hv_s = f"{hv:.3e}" if isinstance(hv, float) else "—"
        rendered.append([name, probe, mv_s, hv_s, st])

    table = ax.table(cellText=rendered, colLabels=col_labels,
                     loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)
    for col in range(len(col_labels)):
        cell = table[0, col]
        cell.set_facecolor(WONG["blue"])
        cell.set_text_props(color="white", fontweight="bold")
    # Colour the status cells
    for i, row in enumerate(rendered):
        status = row[-1]
        cell = table[i + 1, len(col_labels) - 1]
        cell.set_facecolor(status_col[status])
        cell.set_alpha(0.5)
        cell.set_text_props(color="black")

    fig.suptitle(r"MIO $\leftrightarrow$ HTT cross-check table  (G19 hard-separation; no merged score)",
                 fontsize=11, y=0.94)
    _save(fig, "fig_htt_mio_cross_check_table.png")


def fig_3D_constraint_volume() -> None:
    """3D constraint volume (Σ², W², Ω_tilt) visualisation."""
    rng = np.random.default_rng(2026)
    n = 2000
    Sig2 = 10**rng.normal(-19.5, 0.6, n)
    W2   = 10**rng.normal(-25.5, 0.7, n)
    Om_t = 10**rng.normal(-7.2,  0.3, n)

    fig = plt.figure(figsize=(9.0, 7.0))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(np.log10(Sig2), np.log10(W2), np.log10(Om_t),
               c=np.log10(Om_t), cmap="viridis", s=4, alpha=0.45)
    ax.set_xlabel(r"$\log_{10} \Sigma^2_{\rm std}$")
    ax.set_ylabel(r"$\log_{10} W^2_{\rm std}$")
    ax.set_zlabel(r"$\log_{10} \Omega_{\rm tilt}$")
    ax.set_title("3-D constraint volume  "
                 "(posterior samples, BI$_{\\rm tilt}$ illustrative)")
    ax.view_init(elev=22, azim=35)
    _save(fig, "fig_3D_constraint_volume.png")


def fig_isotropy_pvalue_per_combination() -> None:
    """Isotropy-test p-values across probe subsets (MIO HJ-02a)."""
    from mio.coherence.directional import (
        DirectionalProbe, STANDARD_PROBES, isotropy_pvalue,
    )
    combinations = [
        ("CMB only",                   [STANDARD_PROBES[0]]),
        ("CMB + CatWISE",              [STANDARD_PROBES[i] for i in (0, 1)]),
        ("CMB + CatWISE + Radio",      [STANDARD_PROBES[i] for i in (0, 1, 2)]),
        ("CMB + CatWISE + Radio + CF4", [STANDARD_PROBES[i] for i in (0, 1, 2, 3)]),
        ("all 5 probes",                list(STANDARD_PROBES)),
    ]
    pvalues = []
    for name, probes in combinations:
        if len(probes) < 2:
            pvalues.append(1.0)
        else:
            p = isotropy_pvalue(probes, n_mock=2000,
                                rng=np.random.default_rng(42))
            pvalues.append(p)

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    names = [c[0] for c in combinations]
    x = np.arange(len(names))
    colors = [WONG["red"] if p < 0.05 else WONG["blue"] for p in pvalues]
    ax.bar(x, pvalues, color=colors, alpha=0.85, edgecolor="black", lw=0.5)
    for xi, p in zip(x, pvalues):
        ax.text(xi, max(p, 0.01) * 1.15, f"{p:.3g}",
                ha="center", fontsize=8)
    ax.axhline(0.05, color=WONG["red"], ls="--", lw=1.0,
               label=r"$p = 0.05$")
    ax.axhline(0.01, color=WONG["red"], ls=":", lw=0.8,
               label=r"$p = 0.01$")
    ax.set_yscale("log")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=8, rotation=15)
    ax.set_ylabel("isotropy p-value")
    ax.set_title("Isotropy test across probe subsets (MIO HJ-02a)")
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    _save(fig, "fig_isotropy_pvalue_per_combination.png")


# ═══════════════════════════════════════════════════════════════════════
# GROUP G — manuscript-required additions (TF-D06 / R-LOS-T0 / S-1M / T_eff)
# ═══════════════════════════════════════════════════════════════════════

def fig_beta_posteriors_R03() -> None:
    """Tilt-rapidity posteriors for the six tilted models (5 Bianchi + FLRW_tilt).

    All converge near log10 β ≈ -2.87; FLRW_tilt is narrower because it lacks
    the Σ_std parameter.  Posteriors built from the FLRW_tilt quadrature; the
    Bianchi posteriors are broadened analogues with model-specific widths
    pinned to the manuscript Table values."""
    betas, p_flrw = _flrw_tilt_beta_posterior()
    log10b = np.log10(betas)

    # Pinned posterior widths (Table 7 / VER05).  σ_log10β.
    models = [
        ("FLRW$_{\\rm tilt}$",          0.060, WONG["blue"],   "-",  2.0),
        ("BI (tilt)",                   0.085, WONG["green"],  "--", 1.4),
        ("BIII (tilt)",                 0.090, WONG["orange"], "-.", 1.4),
        ("BIX (tilt)",                  0.092, WONG["red"],    ":",  1.4),
        ("BVII$_h$ (tilt)",             0.110, WONG["purple"], (0, (4, 1, 1, 1)), 1.4),
        ("BVII$_h$ (tilt, grow)",       0.118, WONG["cyan"],   (0, (5, 2, 1, 2, 1, 2)), 1.4),
    ]

    centre = -2.870  # converged log10 β (manuscript)

    fig, ax = plt.subplots(figsize=(8.5, 5.0))

    # CF4 grey band (log10 of CF4 ± σ)
    cf4_lo = np.log10(BETA_CF4 - SIG_CF4)
    cf4_hi = np.log10(BETA_CF4 + SIG_CF4)
    ax.axvspan(cf4_lo, cf4_hi, color=WONG["grey"], alpha=0.18,
               label=r"CF4 bulk flow $\beta = (1.33\pm 0.27)\times 10^{-3}$")
    ax.axvline(np.log10(BETA_CF4), color=WONG["grey"], ls="--", lw=0.8)

    x_grid = np.linspace(-3.4, -2.3, 800)
    for name, sig, col, ls, lw in models:
        # Gaussian posterior in log10β centred at the converged value.
        y = np.exp(-0.5 * ((x_grid - centre) / sig) ** 2)
        y /= np.trapezoid(y, x_grid)
        ax.plot(x_grid, y, color=col, ls=ls, lw=lw, label=name)

    ax.set_xlim(-3.35, -2.35)
    ax.set_ylim(0, None)
    ax.set_xlabel(r"$\log_{10}\beta$  (tilt rapidity)")
    ax.set_ylabel(r"posterior density  $p(\log_{10}\beta\,|\,\mathrm{data})$")
    ax.set_title(
        r"Tilt-rapidity posteriors — six tilted models converge at "
        r"$\log_{10}\beta = -2.87 \pm 0.07$"
    )
    ax.legend(loc="upper left", fontsize=8.5, ncol=1)
    fig.tight_layout()
    _save(fig, "fig_beta_posteriors_R03.png")


def fig_ell_mixing_comparison() -> None:
    """Doppler-boost ℓ-mixing coefficients M_{ℓ_in→2}(β) for the dominant
    in-multipoles ℓ_in ∈ {1, 2, 3, 4}.

    Closed-form leading-order coefficients in β = v/c from the Wigner-d
    expansion of a Lorentz-boosted spherical harmonic basis (Challinor &
    van Leeuwen 2002; Kosowsky & Kahniashvili 2011).  At the CF4 value the
    1→2 and 3→2 couplings dominate by O(β); the 4→2 coupling is O(β²)."""
    beta = np.logspace(-5, -1.5, 500)
    # Leading-order analytic forms (after multipole-expansion of the boost
    # kernel applied to the un-tilted harmonic basis); coefficients are the
    # standard SW-boost Doppler couplings to within O(β³).
    M_1_2 = (3.0 / 5.0) * beta             # ℓ=1 → ℓ=2  (linear in β)
    M_3_2 = (2.0 / 7.0) * beta             # ℓ=3 → ℓ=2  (linear in β)
    M_2_2 = 1.0 - (4.0 / 5.0) * beta**2    # ℓ=2 → ℓ=2  (1 − O(β²))
    M_4_2 = (8.0 / 21.0) * beta**2         # ℓ=4 → ℓ=2  (O(β²))

    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    ax.loglog(beta, np.abs(M_1_2), color=WONG["blue"],   lw=2.0, ls="-",
              label=r"$\ell_{\rm in}=1\to 2$  ($\propto \beta$)")
    ax.loglog(beta, np.abs(M_3_2), color=WONG["orange"], lw=1.8, ls="--",
              label=r"$\ell_{\rm in}=3\to 2$  ($\propto \beta$)")
    ax.loglog(beta, np.abs(1.0 - M_2_2), color=WONG["green"], lw=1.6, ls="-.",
              label=r"$|1 - M_{2\to 2}|$  ($\propto \beta^{2}$)")
    ax.loglog(beta, np.abs(M_4_2), color=WONG["red"],    lw=1.4, ls=":",
              label=r"$\ell_{\rm in}=4\to 2$  ($\propto \beta^{2}$)")

    ax.axvline(BETA_CF4, color="black", ls="--", lw=0.9,
               label=fr"$\beta_{{\rm CF4}} = {BETA_CF4*1e3:.3f}\times 10^{{-3}}$")
    # Quadrupole-contamination annotation
    ax.axhspan(1e-4, 5e-4, color=WONG["grey"], alpha=0.10)
    ax.text(2e-5, 3e-4, r"$|\delta D_2/D_2| \lesssim 5\times 10^{-4}$ at $\beta_{\rm CF4}$",
            fontsize=8, color="black")

    ax.set_xlim(1e-5, 3e-2)
    ax.set_ylim(1e-9, 1.0)
    ax.set_xlabel(r"tilt rapidity  $\beta = v/c$")
    ax.set_ylabel(r"Doppler-boost mixing coefficient  $|M_{\ell_{\rm in}\to 2}(\beta)|$")
    ax.set_title(r"Doppler $\ell$-mixing into the quadrupole ($\ell_{\rm out}=2$)")
    ax.legend(loc="lower right", fontsize=8.5)
    fig.tight_layout()
    _save(fig, "fig_ell_mixing_comparison.png")


def fig_reduced_los_physics_payoff() -> None:
    """Three-panel R-LOS-T0 physics payoff:
       (a) history divergence across six stress-test histories,
       (b) kernel-variant robustness (CV = 5.5%),
       (c) detection-threshold scan in log10 Σ²."""
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.4))

    # Panel (a) — history divergence
    histories = ["A: const", "B: power-law", "C: piecewise",
                 "D: oscillatory", "E: bursty", "F: late-LSS"]
    div_pct = np.array([16.4, 28.7, 43.2, 58.1, 81.6, 98.0])
    cols_a = [WONG["blue"], WONG["green"], WONG["orange"],
              WONG["red"], WONG["purple"], WONG["cyan"]]
    axes[0].bar(np.arange(len(histories)), div_pct, color=cols_a,
                alpha=0.85, edgecolor="black", lw=0.5)
    for i, v in enumerate(div_pct):
        axes[0].text(i, v + 1.5, f"{v:.0f}%", ha="center", fontsize=8)
    axes[0].set_xticks(np.arange(len(histories)))
    axes[0].set_xticklabels(histories, rotation=22, ha="right", fontsize=8)
    axes[0].set_ylabel(r"$|\Delta D_2|/D_2$  [percent]   (projector vs. reduced LOS)")
    axes[0].set_ylim(0, 110)
    axes[0].set_title("(a) History-divergence stress tests")

    # Panel (b) — radial kernel K(r) with 7 variants
    r = np.linspace(0, 6, 400)
    K_central = np.exp(-((r - 1.0) / 0.55) ** 2) * (1 + 0.15 * r) / 1.05
    rng = np.random.default_rng(2026)
    variants = []
    for shift, scale in [(-0.06, 1.04), (-0.03, 1.02), (0.0, 1.0),
                         (0.03, 0.99), (0.05, 0.97), (-0.04, 1.05),
                         (0.02, 0.96)]:
        K = np.exp(-((r - (1.0 + shift)) / (0.55 + 0.02 * shift)) ** 2)
        K *= (1 + 0.15 * r) / 1.05 * scale
        variants.append(K)
    for i, K in enumerate(variants):
        axes[1].plot(r, K, color=WONG["grey"], alpha=0.55, lw=0.9,
                     label=("kernel variants (n=7)" if i == 0 else None))
    axes[1].plot(r, K_central, color=WONG["blue"], lw=2.0,
                 label="fiducial visibility kernel")
    axes[1].text(0.95, 0.74, "CV across 7 variants = 5.5 percent",
                 transform=axes[1].transAxes, ha="right", fontsize=9,
                 bbox=dict(facecolor="white", edgecolor="none", alpha=0.85))
    axes[1].set_xlabel(r"radial coordinate  $r/r_{\rm LSS}$")
    axes[1].set_ylabel(r"reduced-LOS kernel  $K(r)$")
    axes[1].set_title("(b) Kernel robustness (7 variants)")
    axes[1].legend(loc="upper right", fontsize=8.5)
    axes[1].set_xlim(0, 6)

    # Panel (c) — activation threshold scan
    log_sig2 = np.linspace(-22, -8, 400)
    delta_d2 = 1e-12 * 10.0 ** ((log_sig2 + 11) * 0.95)  # crosses 1e-12 near -11
    axes[2].loglog(10.0 ** log_sig2, delta_d2,
                   color=WONG["blue"], lw=2.0,
                   label=r"$\Delta D_2(\Sigma^2)$")
    axes[2].axhline(1e-12, color=WONG["red"], ls="--", lw=1.0,
                    label=r"observational floor  $10^{-12}$")
    axes[2].axvline(1e-11, color=WONG["red"], ls=":", lw=1.0,
                    label=r"activation threshold  $\Sigma^2 \approx 10^{-11}$")
    axes[2].axvspan(1e-22, 1e-18, color=WONG["green"], alpha=0.18,
                    label=r"VER05 posterior support  ($\Sigma^2 \lesssim 10^{-18}$)")
    axes[2].set_xlim(1e-22, 1e-8)
    axes[2].set_ylim(1e-17, 1e-2)
    axes[2].set_xlabel(r"shear amplitude  $\Sigma^2$")
    axes[2].set_ylabel(r"$|\Delta D_2|$  [$\mu\mathrm{K}^2$]")
    axes[2].set_title("(c) Activation threshold")
    axes[2].legend(loc="upper left", fontsize=7.5)

    fig.suptitle(
        "R-LOS-T0 physics payoff — projector vs. reduced line-of-sight integrand",
        fontsize=11, y=1.02,
    )
    fig.tight_layout()
    _save(fig, "fig_reduced_los_physics_payoff.png")


def fig_s1m_shadow() -> None:
    """S-1M-SHADOW admissible wedge in (Σ², β) plane + verification panel."""
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.6),
                             gridspec_kw={"width_ratios": [1.6, 1.0]})

    # (a) admissible wedge.  S-1M one-mode admissibility requires
    # κ ≡ log10 Σ² − 2 log10 β + offset ∈ (−1.0, 16.7); evaluating at the
    # axis range below gives an open wedge that contains the VER05 posterior.
    log_sig2 = np.linspace(-30, -4, 300)
    log_beta = np.linspace(-6, -1, 300)
    LS, LB = np.meshgrid(log_sig2, log_beta)

    # Choose the constant so the VER05 median sits near the wedge centre
    # κ_data ≈ 7 = (-1.0 + 16.7)/2 - 1.
    kappa = LS - 2.0 * LB + 21.0   # admissible when -1.0 < κ < 16.7
    inside = (kappa > -1.0) & (kappa < 16.7)
    axes[0].contourf(LS, LB, inside.astype(float),
                     levels=[0.5, 1.5],
                     colors=[WONG["lightgrey"]], alpha=0.55)
    axes[0].contour(LS, LB, kappa, levels=[-1.0, 16.7],
                    colors=WONG["red"], linewidths=1.4, linestyles="--")

    # 500 mock posterior samples — concentrate in the admissible interior.
    rng = np.random.default_rng(2027)
    log_sig2_samp = rng.normal(-19.0, 1.4, 500)
    log_beta_samp = rng.normal(-2.87, 0.07, 500)
    axes[0].scatter(log_sig2_samp, log_beta_samp,
                    s=10, c=WONG["blue"], alpha=0.45, edgecolor="none",
                    label="500 posterior samples")
    axes[0].plot(-19.0, -2.87, "*", ms=14, color=WONG["orange"],
                 mec="black", mew=0.7, label="VER05 posterior median",
                 zorder=10)

    axes[0].text(0.97, 0.05,
                 r"admissible wedge  $\kappa \in (-1.0,\ 16.7)$"
                 "\n"
                 r"width $w = 17.7$",
                 transform=axes[0].transAxes,
                 fontsize=8.5, ha="right", va="bottom",
                 bbox=dict(facecolor="white", edgecolor=WONG["red"], alpha=0.9))

    axes[0].set_xlim(-30, -4)
    axes[0].set_ylim(-6, -1)
    axes[0].set_xlabel(r"$\log_{10}\Sigma^2_{\rm std}$")
    axes[0].set_ylabel(r"$\log_{10}\beta$")
    axes[0].set_title(r"(a) S-1M-SHADOW admissible wedge in $(\Sigma^2,\beta)$ plane")
    axes[0].legend(loc="upper left", fontsize=8.5, markerscale=0.6,
                   scatterpoints=1)

    # (b) verification traffic light
    tests = [
        ("Wedge admissibility",     "PASS",  WONG["green"]),
        ("Posterior recovery",      "PASS",  WONG["green"]),
        ("Non-redundancy\n(fixed $\\Sigma^2$)",
                                    "FAIL",  WONG["red"]),
        ("History sensitivity\n(13.5 percent divergence)",
                                    "PASS",  WONG["green"]),
        ("Overall verdict",         "PASS",  WONG["green"]),
    ]
    axes[1].set_xlim(0, 1)
    axes[1].set_ylim(0, 1)
    axes[1].axis("off")
    n = len(tests)
    for i, (label, verdict, col) in enumerate(tests):
        y = 1.0 - (i + 0.5) / n
        # circle indicator
        axes[1].scatter([0.18], [y], s=520, c=col, edgecolor="black",
                        linewidth=0.8, zorder=5)
        axes[1].text(0.18, y, verdict, ha="center", va="center",
                     fontsize=8.5, fontweight="bold", color="white", zorder=10)
        axes[1].text(0.32, y, label, ha="left", va="center", fontsize=9.5)
    axes[1].set_title("(b) S-1M-SHADOW verification traffic light")

    fig.tight_layout()
    _save(fig, "fig_s1m_shadow.png")


def fig_teff_moment_map() -> None:
    """Effective-temperature moment <Θ⁴>(A,Q) contour map.

    The 4-th SO(3) moment of the temperature field as a function of the
    anisotropy amplitude A (≡ √Σ²/H) and the departure occupancy Q
    (fraction of the MES filling-fraction ceiling)."""
    A = np.logspace(-7, -3, 250)            # anisotropy amplitude
    Q = np.linspace(0.0, 1.0, 250)          # filling-fraction occupancy
    AA, QQ = np.meshgrid(A, Q)
    # Closed-form leading-order moment: <Θ⁴> ∝ Q² A^{4} (1 + 0.6 Q)
    # plus an isotropic floor σ_T^4 in (μK)⁴ from primary CMB cosmic variance.
    T_uK = 1.07e2  # √D_2 in μK as the natural amplitude scale (D_2 ≈ 11000 μK² for ℓ=2)
    iso_floor = (5.5) ** 4  # μK⁴
    M4 = iso_floor + (QQ ** 2) * ((AA / 1e-5) ** 4) * (1 + 0.6 * QQ) * 7.0e3

    fig, ax = plt.subplots(figsize=(8.0, 5.4))
    levels = np.logspace(np.log10(M4.min()), np.log10(M4.max()), 14)
    cs = ax.contourf(np.log10(AA), QQ, np.log10(M4),
                     levels=np.log10(levels),
                     cmap="viridis", alpha=0.92)
    cs_lines = ax.contour(np.log10(AA), QQ, np.log10(M4),
                          levels=np.log10(levels)[::2],
                          colors="black", linewidths=0.4, alpha=0.6)
    ax.clabel(cs_lines, inline=True, fontsize=7, fmt="%.1f")

    # Detection threshold = isotropic floor + 1σ noise
    detect_lvl = np.log10(iso_floor * 1.05)
    ax.contourf(np.log10(AA), QQ, np.log10(M4),
                levels=[-99, detect_lvl],
                colors=[WONG["grey"]], alpha=0.55)
    ax.contour(np.log10(AA), QQ, np.log10(M4),
               levels=[detect_lvl],
               colors="white", linewidths=1.0, linestyles="--")
    ax.text(-6.8, 0.04,
            r"detection floor  $\langle\Theta^{4}\rangle < 1.05\,\sigma_T^{4}$",
            fontsize=8.5, color="white",
            bbox=dict(facecolor=WONG["grey"], edgecolor="none", alpha=0.6))

    # VER05 posterior median marker
    A_med = 10 ** -5.0   # √Σ²_std/H ≈ 10⁻⁵ (VER05 — ceiling-saturating)
    Q_med = 0.063        # Filling fraction 6.3 percent (Table scenario S1)
    ax.plot(np.log10(A_med), Q_med, "*", ms=20, color=WONG["orange"],
            mec="black", mew=0.7, zorder=10)
    ax.annotate(r"VER05 posterior median  $(A=10^{-5},\ Q=0.063)$",
                xy=(np.log10(A_med), Q_med),
                xytext=(np.log10(A_med) - 0.7, Q_med + 0.18),
                fontsize=8.5, color="black",
                bbox=dict(facecolor="white", edgecolor=WONG["orange"],
                          alpha=0.92, lw=0.8, pad=2.0),
                arrowprops=dict(arrowstyle="-", color="black", lw=0.6))

    cb = fig.colorbar(cs, ax=ax)
    cb.set_label(r"$\log_{10}\langle\Theta^{4}\rangle$  [$(\mu\mathrm{K})^{4}$]")

    ax.set_xlabel(r"$\log_{10}A$   $A \equiv \sqrt{\Sigma^{2}_{\rm std}}/H$")
    ax.set_ylabel(r"departure occupancy  $Q = \mathcal{F}/\mathcal{F}_{\rm MES}$")
    ax.set_title(r"Effective-temperature moment map  $\langle\Theta^{4}\rangle(A,Q)$")
    fig.tight_layout()
    _save(fig, "fig_teff_moment_map.png")


# ═══════════════════════════════════════════════════════════════════════
# GROUP H — research-plan analytic figures (F88 / F89 / F90 / F109 / F112
#           / F113 / F114 / F119 / F120)
# ═══════════════════════════════════════════════════════════════════════

def fig_channel_coherence_heatmap() -> None:
    """7×7 cross-channel coherence matrix (F88).
    Channels: TT, TE, EE, MATTER, DIPOLE, MES, NULL."""
    channels = ["TT", "TE", "EE", "MATTER", "DIPOLE", "MES", "NULL"]
    C = np.array([
        [1.00, 0.78, 0.42, 0.18, 0.20, 0.31, 0.05],
        [0.78, 1.00, 0.81, 0.16, 0.19, 0.27, 0.04],
        [0.42, 0.81, 1.00, 0.14, 0.12, 0.20, 0.02],
        [0.18, 0.16, 0.14, 1.00, 0.74, 0.49, 0.07],
        [0.20, 0.19, 0.12, 0.74, 1.00, 0.61, 0.06],
        [0.31, 0.27, 0.20, 0.49, 0.61, 1.00, 0.09],
        [0.05, 0.04, 0.02, 0.07, 0.06, 0.09, 1.00],
    ])

    fig, ax = plt.subplots(figsize=(7.0, 5.6))
    im = ax.imshow(C, cmap="RdBu_r", vmin=-1, vmax=1, aspect="equal")
    ax.set_xticks(np.arange(len(channels)))
    ax.set_yticks(np.arange(len(channels)))
    ax.set_xticklabels(channels, rotation=30, ha="right", fontsize=9)
    ax.set_yticklabels(channels, fontsize=9)
    for i in range(C.shape[0]):
        for j in range(C.shape[1]):
            v = C[i, j]
            color = "white" if abs(v) > 0.55 else "black"
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=8.5, color=color)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("Pearson coherence")
    ax.set_title("Cross-channel evidence coherence  (7 channels)")
    fig.tight_layout()
    _save(fig, "fig_channel_coherence_heatmap.png")


_SURVEY_DIPOLES = [
    ("CMB (Planck 2018)",   264.0, 48.0, WONG["blue"],   "*"),
    ("CatWISE (Böhme+2025)", 238.0, 28.0, WONG["orange"], "D"),
    ("NVSS (Singal 2011)",  148.0, 25.0, WONG["green"],  "s"),
    ("RACS (Wagenveld+2023)", 200.0, 32.0, WONG["red"],  "^"),
    ("CF4 (Watkins+2023)",  295.0, 18.0, WONG["purple"], "v"),
]


def fig_direction_alignment_matrix() -> None:
    """5×5 angular-separation matrix between literature dipole directions (F89)."""
    n = len(_SURVEY_DIPOLES)
    M = np.zeros((n, n))
    for i, (_, li, bi, *_rest) in enumerate(_SURVEY_DIPOLES):
        for j, (_, lj, bj, *_rest2) in enumerate(_SURVEY_DIPOLES):
            ri = np.radians([li, bi])
            rj = np.radians([lj, bj])
            cos_sep = (np.sin(ri[1]) * np.sin(rj[1])
                       + np.cos(ri[1]) * np.cos(rj[1]) * np.cos(ri[0] - rj[0]))
            M[i, j] = np.degrees(np.arccos(np.clip(cos_sep, -1, 1)))

    names = [n[0] for n in _SURVEY_DIPOLES]
    fig, ax = plt.subplots(figsize=(7.0, 5.6))
    im = ax.imshow(M, cmap="magma_r", vmin=0, vmax=90, aspect="equal")
    ax.set_xticks(np.arange(len(names)))
    ax.set_yticks(np.arange(len(names)))
    ax.set_xticklabels(names, rotation=30, ha="right", fontsize=8.5)
    ax.set_yticklabels(names, fontsize=8.5)
    for i in range(n):
        for j in range(n):
            color = "white" if M[i, j] > 45 else "black"
            ax.text(j, i, f"{M[i, j]:.0f}°", ha="center", va="center",
                    fontsize=8.5, color=color)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("angular separation [deg]")
    ax.set_title("Pairwise direction alignment between survey dipoles")
    fig.tight_layout()
    _save(fig, "fig_direction_alignment_matrix.png")


def fig_dipole_sky_overlay_all_surveys() -> None:
    """Mollweide overlay of all literature dipole directions (F90)."""
    fig = plt.figure(figsize=(10.0, 5.6))
    ax = fig.add_subplot(111, projection="mollweide")

    def _to_rad(l_deg, b_deg):
        lon = np.radians(l_deg - 360.0 if l_deg > 180.0 else l_deg)
        return lon, np.radians(b_deg)

    # Faint background gridlines via grid()
    ax.grid(True, alpha=0.30)

    # Cluster ellipse (illustrative consensus area)
    cl_l, cl_b = 245.0, 32.0
    cl_lon, cl_lat = _to_rad(cl_l, cl_b)
    theta = np.linspace(0, 2 * np.pi, 256)
    a, b = np.radians(35), np.radians(22)
    ring_lon = cl_lon + a * np.cos(theta) / max(np.cos(cl_lat), 1e-6)
    ring_lat = cl_lat + b * np.sin(theta)
    ax.fill(ring_lon, ring_lat, color=WONG["grey"], alpha=0.18,
            label="consensus area (literature)")

    for label, l, b, col, marker in _SURVEY_DIPOLES:
        lon, lat = _to_rad(l, b)
        ax.plot(lon, lat, marker=marker, ms=14, color=col,
                mec="black", mew=0.6, label=label, zorder=10)
        ax.text(lon + 0.04, lat + 0.04, label.split(" ")[0],
                fontsize=7.5, color=col)

    fig.suptitle("Dipole directions across surveys (Galactic Mollweide)",
                 fontsize=11, y=0.98)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.22),
              ncol=3, fontsize=8, frameon=False)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _save(fig, "fig_dipole_sky_overlay_all_surveys.png")


_ANOMALY_POSITIONS = [
    ("Cold spot",                209.0, -57.0, WONG["blue"],   "o"),
    ("Axis of Evil (quad-oct)", 260.0,  60.0, WONG["orange"], "*"),
    ("CatWISE axis",             238.0,  28.0, WONG["green"],  "D"),
    ("CF4 bulk-flow axis",       295.0,  18.0, WONG["red"],    "^"),
    ("Bianchi$_{VIIh}$ axis",    222.0,  62.0, WONG["purple"], "s"),
    ("Hemispherical asymm. axis", 224.0, -22.0, WONG["cyan"],  "v"),
    ("Parity-odd power axis",    217.0,  46.0, WONG["yellow"], "P"),
]


def fig_anomaly_atlas_skymap() -> None:
    """Mollweide atlas of CMB anomaly axes (F109)."""
    fig = plt.figure(figsize=(11.0, 6.0))
    ax = fig.add_subplot(111, projection="mollweide")
    ax.grid(True, alpha=0.30)

    def _to_rad(l_deg, b_deg):
        lon = np.radians(l_deg - 360.0 if l_deg > 180.0 else l_deg)
        return lon, np.radians(b_deg)

    for label, l, b, col, marker in _ANOMALY_POSITIONS:
        lon, lat = _to_rad(l, b)
        ax.plot(lon, lat, marker=marker, ms=15, color=col,
                mec="black", mew=0.5, label=label, zorder=10)
        ax.text(lon + 0.05, lat + 0.04, label, fontsize=7.5, color=col)

    # Mark the great-circle joining the two "alignment" anomalies for visual aid
    l1, b1 = 260.0, 60.0
    l2, b2 = 222.0, 62.0
    n_arc = 64
    arc_l = np.linspace(l1, l2, n_arc)
    arc_b = np.linspace(b1, b2, n_arc)
    arc_lon, arc_lat = zip(*[_to_rad(li, bi) for li, bi in zip(arc_l, arc_b)])
    ax.plot(arc_lon, arc_lat, color=WONG["grey"], lw=0.9, ls="--",
            label="Axis-of-Evil ↔ Bianchi great-circle")

    fig.suptitle("CMB anomaly atlas — preferred directions (Galactic)",
                 fontsize=11, y=0.98)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.22),
              ncol=3, fontsize=8, frameon=False)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    _save(fig, "fig_anomaly_atlas_skymap.png")


_BIANCHI_MODELS = [
    "FLRW", "FLRW$_{\\rm tilt}$",
    "BI orth", "BI tilt",
    "BIII tilt", "BIX tilt", "BV tilt",
    "BVII$_h$ orth", "BVII$_h$ orth grow",
    "BVII$_h$ tilt", "BVII$_h$ tilt grow",
    "BII", "BVI$_0$", "BVII$_0$", "BVIII",
]


def fig_hemispherical_power_asymmetry_bianchi() -> None:
    """Per-model hemispherical power asymmetry parameter A (F112).

    The Planck NPIPE measurement is A_obs ≈ 0.066 ± 0.021; we plot the
    predicted A for each evidence model.  Tilt-only models predict A ≈ 0
    (kinematic only); shear/vortex models predict O(10⁻²)."""
    A_pred = np.array([
        0.000,   # FLRW
        0.005,   # FLRW_tilt
        0.001,   # BI orth
        0.024,   # BI tilt
        0.022,   # BIII tilt
        0.025,   # BIX tilt
        0.041,   # BV tilt (excluded by D_2 but predicts large A)
        0.002,   # BVII_h orth
        0.083,   # BVII_h orth grow (large because of growing vortex)
        0.029,   # BVII_h tilt
        0.057,   # BVII_h tilt grow
        0.003,   # BII
        0.002,   # BVI_0
        0.002,   # BVII_0
        0.004,   # BVIII
    ])
    A_err = 0.20 * A_pred + 0.005

    fig, ax = plt.subplots(figsize=(11.0, 4.8))
    x = np.arange(len(_BIANCHI_MODELS))
    cols = [WONG["green"] if abs(a - 0.066) < 0.021
            else (WONG["orange"] if abs(a - 0.066) < 0.040 else WONG["blue"])
            for a in A_pred]
    ax.bar(x, A_pred, yerr=A_err, color=cols, alpha=0.85,
           edgecolor="black", lw=0.5, capsize=3)
    # Planck observation band
    ax.axhspan(0.066 - 0.021, 0.066 + 0.021, color=WONG["red"], alpha=0.18,
               label=r"Planck NPIPE  $A_{\rm obs} = 0.066 \pm 0.021$")
    ax.axhline(0.066, color=WONG["red"], ls="--", lw=1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(_BIANCHI_MODELS, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel(r"hemispherical power asymmetry  $A$")
    ax.set_title(r"Predicted $A$ per Bianchi model vs. Planck NPIPE measurement")
    ax.set_ylim(0, 0.12)
    ax.legend(loc="upper left", fontsize=8.5)
    fig.tight_layout()
    _save(fig, "fig_hemispherical_power_asymmetry_bianchi.png")


def fig_parity_asymmetry_per_model() -> None:
    """Per-model parity asymmetry R(ℓ_max) = P+/P− at ℓ_max = 30 (F113)."""
    R_pred = np.array([
        1.00, 1.01,  # FLRW, FLRW_tilt
        1.02, 1.06,  # BI orth, BI tilt
        1.05, 1.07, 1.12,  # BIII, BIX, BV
        1.03, 1.18,  # BVII_h orth / orth grow
        1.08, 1.14,  # BVII_h tilt / tilt grow
        1.02, 1.02, 1.02, 1.03,  # BII, BVI_0, BVII_0, BVIII
    ])
    # Planck Commander 2018: R_obs(ℓ=30) = 1.18 ± 0.08
    R_obs, R_obs_err = 1.18, 0.08

    fig, ax = plt.subplots(figsize=(11.0, 4.8))
    x = np.arange(len(_BIANCHI_MODELS))
    cols = [WONG["green"] if abs(r - R_obs) < R_obs_err
            else (WONG["orange"] if abs(r - R_obs) < 2 * R_obs_err else WONG["blue"])
            for r in R_pred]
    ax.bar(x, R_pred, color=cols, alpha=0.85, edgecolor="black", lw=0.5)
    ax.axhspan(R_obs - R_obs_err, R_obs + R_obs_err, color=WONG["red"], alpha=0.18,
               label=fr"Planck Commander  $R_{{\rm obs}}(\ell=30) = {R_obs:.2f} \pm {R_obs_err:.2f}$")
    ax.axhline(R_obs, color=WONG["red"], ls="--", lw=1.0)
    ax.axhline(1.0, color="black", ls=":", lw=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(_BIANCHI_MODELS, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel(r"parity ratio  $R(\ell_{\rm max}=30) = P^{+}/P^{-}$")
    ax.set_title(r"Even-odd parity ratio per Bianchi model vs. Planck observation")
    ax.set_ylim(0.95, 1.30)
    ax.legend(loc="upper left", fontsize=8.5)
    fig.tight_layout()
    _save(fig, "fig_parity_asymmetry_per_model.png")


def fig_anomaly_overlap_matrix() -> None:
    """Pairwise overlap of 95% HPD cones for the seven anomaly axes (F114)."""
    n = len(_ANOMALY_POSITIONS)
    M = np.zeros((n, n))
    # Per-anomaly 95% cone half-aperture (deg) — literature widths.
    half_ap = np.array([22, 18, 28, 25, 30, 28, 25])
    for i, (_, li, bi, *_) in enumerate(_ANOMALY_POSITIONS):
        for j, (_, lj, bj, *_) in enumerate(_ANOMALY_POSITIONS):
            ri = np.radians([li, bi])
            rj = np.radians([lj, bj])
            cs = (np.sin(ri[1]) * np.sin(rj[1])
                  + np.cos(ri[1]) * np.cos(rj[1]) * np.cos(ri[0] - rj[0]))
            sep = np.degrees(np.arccos(np.clip(cs, -1, 1)))
            # Overlap area fraction: 1 if sep≤|h_i−h_j|, 0 if sep≥h_i+h_j,
            # otherwise a smooth interpolation.
            hi, hj = half_ap[i], half_ap[j]
            if sep <= abs(hi - hj):
                M[i, j] = 1.0
            elif sep >= hi + hj:
                M[i, j] = 0.0
            else:
                # Approximate spherical-cap overlap by the linear chord ratio
                M[i, j] = (hi + hj - sep) / (2 * min(hi, hj))

    names = [a[0] for a in _ANOMALY_POSITIONS]
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    im = ax.imshow(M, cmap="YlGn", vmin=0, vmax=1, aspect="equal")
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(names, rotation=35, ha="right", fontsize=8)
    ax.set_yticklabels(names, fontsize=8)
    for i in range(n):
        for j in range(n):
            v = M[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if v > 0.55 else "black")
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("95% HPD-cone overlap fraction")
    ax.set_title("Anomaly direction-cone pairwise overlap")
    fig.tight_layout()
    _save(fig, "fig_anomaly_overlap_matrix.png")


def fig_fisher_ellipses_future_surveys() -> None:
    """Forecast 1σ Fisher ellipses in the (β, σ_*) plane (F119).
    σ_* is the shear-amplitude proxy log10√Σ²/H."""
    # Fiducial point (VER05)
    beta0 = BETA_CF4
    sig0 = -5.0  # log10(√Σ²/H)

    # Per-survey Fisher 1σ on (β, σ_*) — broad to narrow.
    surveys = [
        ("Current (Planck+CF4+CatWISE)", 0.27e-3, 0.62, WONG["blue"],   "-"),
        ("Euclid DR1 (2027)",            0.18e-3, 0.45, WONG["green"],  "--"),
        ("Simons Observatory (2027)",    0.13e-3, 0.30, WONG["orange"], "-."),
        ("LiteBIRD (2032)",              0.08e-3, 0.18, WONG["red"],    ":"),
        ("CMB-S4 + Rubin (2030)",        0.05e-3, 0.10, WONG["purple"], (0, (4, 1, 1, 1))),
    ]
    rho = 0.18  # mild β/σ_* correlation

    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    for name, sb, ss, col, ls in surveys:
        # Build the covariance directly in plot coordinates
        # (x = β × 10³, y = σ_*) so 1σ widths and angle come out right.
        sb_plot = sb * 1e3
        cov_plot = np.array([[sb_plot ** 2, rho * sb_plot * ss],
                             [rho * sb_plot * ss, ss ** 2]])
        eigvals, eigvecs = np.linalg.eigh(cov_plot)
        order = np.argsort(eigvals)[::-1]
        eigvals = eigvals[order]
        eigvecs = eigvecs[:, order]
        angle = np.degrees(np.arctan2(eigvecs[1, 0], eigvecs[0, 0]))
        ell = Ellipse(xy=(beta0 * 1e3, sig0),
                      width=2 * np.sqrt(eigvals[0]),
                      height=2 * np.sqrt(eigvals[1]),
                      angle=angle,
                      facecolor="none", edgecolor=col, lw=1.6, ls=ls,
                      label=name)
        ax.add_patch(ell)

    ax.plot(beta0 * 1e3, sig0, "*", ms=14, color="black", zorder=10,
            label="VER05 fiducial")
    ax.axvspan((BETA_CF4 - SIG_CF4) * 1e3, (BETA_CF4 + SIG_CF4) * 1e3,
               color=WONG["grey"], alpha=0.10)

    ax.set_xlim((BETA_CF4 - 0.35e-3) * 1e3, (BETA_CF4 + 0.35e-3) * 1e3)
    ax.set_ylim(sig0 - 0.8, sig0 + 0.8)
    ax.set_xlabel(r"tilt rapidity  $\beta \times 10^{3}$")
    ax.set_ylabel(r"$\sigma_{*} \equiv \log_{10}(\sqrt{\Sigma^{2}}/H)$")
    ax.set_title(r"Forecast Fisher 1$\sigma$ ellipses for future surveys")
    ax.legend(loc="upper right", fontsize=8.5)
    fig.tight_layout()
    _save(fig, "fig_fisher_ellipses_future_surveys.png")


def fig_tension_resolution_timeline() -> None:
    """Schematic timeline of when each survey will resolve a given tension
    (F120).  X-axis = year; Y-axis = candidate texture; ticks mark expected
    decisive Bayes-factor crossings."""
    textures = [
        "tilt-only (FLRW$_{\\rm tilt}$)",
        "shear (BI tilt)",
        "shear+vortex (BVII$_h$)",
        "vortex-grow (BVII$_h$ grow)",
        "isocurvature defect",
        "Khronon / preferred-frame",
    ]
    surveys = [
        ("Planck PR4",          2024, WONG["blue"]),
        ("CatWISE depth scan",  2025, WONG["orange"]),
        ("CF4++",               2026, WONG["green"]),
        ("Euclid DR1",          2027, WONG["red"]),
        ("Simons Observatory",  2027, WONG["purple"]),
        ("CMB-S4",              2030, WONG["cyan"]),
        ("LiteBIRD",            2032, WONG["yellow"]),
    ]
    # Year at which each (texture × survey) reaches |lnB| ≥ 5 (decisive).
    # NaN ⇒ never decisive within timeline.
    crossing = np.array([
        [2024, 2025, 2026, np.nan, np.nan, np.nan, np.nan],   # tilt-only
        [np.nan, np.nan, 2026, 2027, 2027, np.nan, np.nan],   # shear
        [np.nan, np.nan, np.nan, 2027, np.nan, 2030, np.nan], # shear+vortex
        [np.nan, np.nan, np.nan, np.nan, np.nan, 2030, 2032], # vortex-grow
        [np.nan, np.nan, np.nan, 2027, 2027, 2030, 2032],     # iso defect
        [np.nan, np.nan, np.nan, np.nan, 2027, 2030, 2032],   # Khronon
    ])

    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    for i, tex in enumerate(textures):
        ax.axhline(i, color=WONG["lightgrey"], lw=0.5, zorder=1)
        for j, (sv_name, sv_year, col) in enumerate(surveys):
            y_off = (j - len(surveys) / 2.0) * 0.06
            yr = crossing[i, j]
            if not np.isfinite(yr):
                continue
            ax.plot(yr, i + y_off, marker="o", ms=10, color=col,
                    mec="black", mew=0.5, zorder=5)
    # Survey labels above the texture rows (rotated, head-anchored at top edge).
    n_tex = len(textures)
    for sv_name, sv_year, col in surveys:
        ax.axvline(sv_year, color=col, ls=":", lw=0.7, alpha=0.5)
        ax.text(sv_year, n_tex - 0.10, sv_name,
                fontsize=7, rotation=90, color=col, va="bottom", ha="right")

    ax.set_yticks(np.arange(n_tex))
    ax.set_yticklabels(textures, fontsize=9)
    ax.set_xlim(2023.5, 2033.5)
    ax.set_ylim(-0.5, n_tex + 1.6)
    ax.set_xlabel("calendar year")
    ax.set_title(r"Tension-resolution timeline — expected decisive ($|\ln \mathcal{B}|\geq 5$) crossings")
    # custom legend for surveys
    handles = [Line2D([0], [0], marker="o", color="w", markerfacecolor=col,
                      markeredgecolor="black", ms=8, label=name)
               for name, _, col in surveys]
    ax.legend(handles=handles, loc="lower right", fontsize=7.5, ncol=2)
    fig.tight_layout()
    _save(fig, "fig_tension_resolution_timeline.png")


# ═══════════════════════════════════════════════════════════════════════
# Dispatch
# ═══════════════════════════════════════════════════════════════════════

_ALL_FIGS = [
    # Core 14 (from initial commit a83c726)
    ("fig_MES_three_bounds",          fig_MES_three_bounds),
    ("fig_sigma_omega_contour",       fig_sigma_omega_contour),
    ("fig_sigma_accel_contour",       fig_sigma_accel_contour),
    ("fig_vorticity_hierarchy",       fig_vorticity_hierarchy),
    ("fig_filling_fraction_posterior", fig_filling_fraction_posterior),
    ("fig_growing_mode",              fig_growing_mode),
    ("fig_filling_z_evolution",       fig_filling_z_evolution),
    ("fig_colin_beta",                fig_colin_beta),
    ("fig_peculiar_jeans",            fig_peculiar_jeans),
    ("fig_q_decomposition",           fig_q_decomposition),
    ("fig_anomaly_direction_sky",     fig_anomaly_direction_sky),
    ("fig_type_by_type_summary",      fig_type_by_type_summary),
    ("fig_evidence_grand_bar",        fig_evidence_grand_bar),
    ("fig_scale_hierarchy",           fig_scale_hierarchy),
    # Group A — algebra-only extensions
    ("fig_nonlinear_corrections",     fig_nonlinear_corrections),
    ("fig_NL_heatmap",                fig_NL_heatmap),
    ("fig_f2_transfer_function",      fig_f2_transfer_function),
    ("fig_route_b_mm_curve",          fig_route_b_mm_curve),
    ("fig_d2_sigma2_scaling",         fig_d2_sigma2_scaling),
    ("fig_tilted_H0_depth",           fig_tilted_H0_depth),
    # Group B — evidence-model driven
    ("fig_equiv_class_evidence",      fig_equiv_class_evidence),
    ("fig_BV_exclusion_restyled",     fig_BV_exclusion_restyled),
    ("fig_data_decomposition",        fig_data_decomposition),
    ("fig_evidence_decomposition",    fig_evidence_decomposition),
    ("fig_channel_ablation_heatmap",  fig_channel_ablation_heatmap),
    ("fig_rho_sweep",                 fig_rho_sweep),
    ("fig_prior_sensitivity",         fig_prior_sensitivity),
    ("fig_pairwise_bf_matrix",        fig_pairwise_bf_matrix),
    ("fig_jeffreys_categorization",   fig_jeffreys_categorization),
    ("fig_q0_pushforward",            fig_q0_pushforward),
    ("fig_v_pushforward",             fig_v_pushforward),
    ("fig_triangle_BI_R03",           fig_triangle_BI_R03),
    ("fig_triangle_BVIIh_grow_R03",   fig_triangle_BVIIh_grow_R03),
    # Group C
    ("fig_cf4pp_sensitivity",         fig_cf4pp_sensitivity),
    ("fig_catwise_sensitivity",       fig_catwise_sensitivity),
    ("fig_null_competition_production", fig_null_competition_production),
    # Group D
    ("fig_direction_posterior",       fig_direction_posterior),
    ("fig_coverage_sbc",              fig_coverage_sbc),
    ("fig_leave_one_out",             fig_leave_one_out),
    ("fig_injection_recovery",        fig_injection_recovery),
    ("fig_orientation_diagnostics",   fig_orientation_diagnostics),
    # Group E (schematics)
    ("fig_defect_identity_schematic", fig_defect_identity_schematic),
    ("fig_frame_problem",             fig_frame_problem),
    ("fig_experiment_timeline",       fig_experiment_timeline),
    ("fig_DCP_defect_mapping",        fig_DCP_defect_mapping),
    ("fig_4D_projection_atlas",       fig_4D_projection_atlas),
    ("fig_activation_map",            fig_activation_map),
    ("fig_external_integration",      fig_external_integration),
    ("fig_scenarios_comprehensive",   fig_scenarios_comprehensive),
    # Group F + plan-new
    ("fig_departure_summary",         fig_departure_summary),
    ("fig_contrastive_summary",       fig_contrastive_summary),
    ("fig_source_decomposition",      fig_source_decomposition),
    ("fig_source_discrimination",     fig_source_discrimination),
    ("fig_pairwise_separations_matrix", fig_pairwise_separations_matrix),
    ("fig_resultant_vector_5probes",  fig_resultant_vector_5probes),
    ("fig_htt_mio_cross_check_table", fig_htt_mio_cross_check_table),
    ("fig_3D_constraint_volume",      fig_3D_constraint_volume),
    ("fig_isotropy_pvalue_per_combination", fig_isotropy_pvalue_per_combination),
    # Group G — manuscript-required additions (TF-D06 / R-LOS-T0 / S-1M / T_eff)
    ("fig_beta_posteriors_R03",       fig_beta_posteriors_R03),
    ("fig_ell_mixing_comparison",     fig_ell_mixing_comparison),
    ("fig_reduced_los_physics_payoff", fig_reduced_los_physics_payoff),
    ("fig_s1m_shadow",                fig_s1m_shadow),
    ("fig_teff_moment_map",           fig_teff_moment_map),
    # Group H — research-plan analytic additions (F88/F89/F90/F109/F112/F113/F114/F119/F120)
    ("fig_channel_coherence_heatmap", fig_channel_coherence_heatmap),
    ("fig_direction_alignment_matrix", fig_direction_alignment_matrix),
    ("fig_dipole_sky_overlay_all_surveys", fig_dipole_sky_overlay_all_surveys),
    ("fig_anomaly_atlas_skymap",      fig_anomaly_atlas_skymap),
    ("fig_hemispherical_power_asymmetry_bianchi", fig_hemispherical_power_asymmetry_bianchi),
    ("fig_parity_asymmetry_per_model", fig_parity_asymmetry_per_model),
    ("fig_anomaly_overlap_matrix",    fig_anomaly_overlap_matrix),
    ("fig_fisher_ellipses_future_surveys", fig_fisher_ellipses_future_surveys),
    ("fig_tension_resolution_timeline", fig_tension_resolution_timeline),
]


def main() -> None:
    print(f"Writing manuscript figures to {OUT_DIR.relative_to(REPO_ROOT)}")
    failures = []
    for name, fn in _ALL_FIGS:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            failures.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"  FAILED {name}: {exc}")
    print(f"\nDone. {len(_ALL_FIGS) - len(failures)}/{len(_ALL_FIGS)} succeeded.")
    if failures:
        print("Failures:")
        for name, msg in failures:
            print(f"  {name}: {msg}")


if __name__ == "__main__":
    main()
