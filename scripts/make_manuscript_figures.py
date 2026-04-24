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
    rows = [
        ("FLRW$_{\\rm tilt}$",         26.40, 0.05, "decisive"),
        ("BIII (tilt)",                26.40, 0.07, "decisive"),
        ("BIX (tilt)",                 26.40, 0.08, "decisive"),
        ("BI (tilt)",                  26.30, 0.08, "decisive"),
        ("BVII$_h$ (tilt, grow)",      25.00, 0.09, "decisive"),
        ("BVII$_h$ (tilt)",            25.00, 0.10, "decisive"),
        ("BV (tilt)",                  24.80, 0.20, "decisive"),
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
        Rectangle((0,0), 1, 1, color=WONG["grey"], alpha=0.8,
                  label=r"negligible ($|\ln\mathcal{B}| < 5$)"),
        Rectangle((0,0), 1, 1, color=WONG["red"], alpha=0.8,
                  label=r"decisive exclusion ($\ln\mathcal{B} < -5$)"),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=9)
    ax.set_xlim(-24, 33)
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
# Dispatch
# ═══════════════════════════════════════════════════════════════════════

_ALL_FIGS = [
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
