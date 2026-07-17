#!/usr/bin/env python3
"""
VC-03: (|σ|/Θ , |u̇|/Θ) Shear–Acceleration Constraint Plane
==============================================================
Four-panel figure:
  (a) MES rectangular bounds + barotropic coupling line
  (b) Bianchi V dipole closure: β-parameterised curve
  (c) ω=0 vs ω=ω_max comparison (Saadeh)
  (d) Raychaudhuri-derived constraint and nonlinear correction
"""

# SSOT_NOTE: Cosmological constants (H₀=67.36, Ω_m=0.3153) are from
# workspace/data/obs_defaults.json (Planck 2018 FLRW fit). These are
# FLRW-fitted values; Bianchi corrections O(Σ²) ~ 10⁻⁶ are negligible
# for figure-generation purposes.

import numpy as np
import matplotlib

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import (
    current_mes_successor_registry,
    legacy_reproduction_coefficients,
)

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id
_MES_LEGACY_COEFFS = legacy_reproduction_coefficients()
_C_SIG1, _C_SIG2, _C_SIG3 = (float(c) for c in _MES_LEGACY_COEFFS["sigma"])
_C_OM1, _C_OM2, _C_OM3 = (float(c) for c in _MES_LEGACY_COEFFS["omega"])
_C_AC1, _C_AC2, _C_AC3 = (float(c) for c in _MES_LEGACY_COEFFS["accel"])
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import OrderedDict

# =====================================================================
#  Constants (SSOT)
# =====================================================================
# Constants (from ssot if available; hardcoded fallback)
try:
    from ssot import C as _C
    eps2 = _C.eps2
    eps3 = _C.eps3
except ImportError:
    eps2 = 3.559629e-6
    eps3 = 6.065291e-6
eta_ud = 1.0 / 12.0          # w/(3(1+w)) for w=1/3
w_rad = 1.0 / 3.0
Omega_m = 0.3153
Omega_L = 0.6847
Omega_k = 0.0007

def B_sigma(e1):
    return _C_SIG1 * e1 + _C_SIG2 * eps2 + _C_SIG3 * eps3

def B_accel(e1):
    return _C_AC1 * e1 + _C_AC2 * eps2 + _C_AC3 * eps3

def beta_safe(e1):
    return e1 / (1.0 + eta_ud)

def udot_from_beta(beta):
    """u̇/Θ = η_u̇ × β for barotropic w=1/3."""
    return eta_ud * beta

# Stoeger-Araujo-Gebbie (1997) COBE bound
STOEGER_UDOT = 1.0e-4

# Saadeh vorticity
omega_T_saadeh = 5.0e-11 / 3.0

scenarios = OrderedDict([
    ("S1",  {"eps1": 1.233e-3, "label": "S1 (Ferreira–Quartin)"}),
    ("S2",  {"eps1": 1.476e-3, "label": "S2 (CatWISE)"}),
    ("S2c", {"eps1": 2.586e-3, "label": "S2c (NVSS+RACS)"}),
    ("S3",  {"eps1": 3.296e-3, "label": "S3 (Böhme+2025)"}),
])

# Colorblind-friendly (Wong 2011)
C_BLUE   = "#0072B2"
C_ORANGE = "#E69F00"
C_RED    = "#D55E00"
C_PURPLE = "#CC79A7"
C_CYAN   = "#56B4E9"
C_GREEN  = "#009E73"
C_BLACK  = "#000000"
C_GREY   = "#999999"

SC_COL = {"S1": C_BLUE, "S2": C_ORANGE, "S2c": C_PURPLE, "S3": C_RED}

def set_style():
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 300,
        "font.size": 13,
        "axes.titlesize": 18, "axes.labelsize": 16,
        "xtick.labelsize": 13, "ytick.labelsize": 13,
        "legend.fontsize": 10.5, "legend.framealpha": 0.92,
        "axes.linewidth": 1.2, "lines.linewidth": 2.0,
        "axes.grid": True, "grid.alpha": 0.20, "grid.linewidth": 0.5,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "mathtext.fontset": "cm",
    })


# =====================================================================
#  Panel (a): MES rectangles + barotropic coupling line
# =====================================================================
def panel_a(ax):
    ax.set_title(
        r"(a) MES Bounds + Barotropic Coupling",
        fontsize=16, pad=12)

    Bs_max = B_sigma(3.5e-3)
    Bu_max = B_accel(3.5e-3)

    # Barotropic coupling line: u̇/Θ = η_u̇ × β,  σ/Θ ~ B_σ(ε₁)
    # Parametrise by ε₁
    e1_line = np.linspace(0, 3.5e-3, 300)
    sig_line = np.array([B_sigma(e) for e in e1_line])
    udot_line = np.array([udot_from_beta(beta_safe(e)) for e in e1_line])

    # Draw scenario rectangles (largest first)
    for sname in reversed(list(scenarios.keys())):
        sc = scenarios[sname]
        e1 = sc["eps1"]
        Bs = B_sigma(e1)
        Bu = B_accel(e1)
        col = SC_COL[sname]
        rect = mpatches.Rectangle(
            (0, 0), Bs, Bu,
            linewidth=2.0, edgecolor=col,
            facecolor=col, alpha=0.08, zorder=2)
        ax.add_patch(rect)
        # Corner marker
        ax.plot(Bs, Bu, "s", color=col, ms=7, zorder=6,
                markeredgecolor="white", markeredgewidth=0.6)

    # Barotropic coupling line (the physical locus)
    ax.plot(sig_line, udot_line, "-", color=C_BLACK, lw=2.5, zorder=8,
            label=r"Barotropic: $|\dot u|/\Theta = \eta_{\dot u}\,\beta$")

    # Mark scenario points ON the coupling line
    for sname, sc in scenarios.items():
        e1 = sc["eps1"]
        sig_pt = B_sigma(e1)
        udot_pt = udot_from_beta(beta_safe(e1))
        col = SC_COL[sname]
        ax.plot(sig_pt, udot_pt, "o", color=col, ms=9, zorder=10,
                markeredgecolor="white", markeredgewidth=1.2,
                label=sc["label"])

    # Stoeger bound horizontal
    ax.axhline(STOEGER_UDOT, color=C_GREEN, ls="--", lw=1.5, alpha=0.7,
               label=r"Stoeger+ 1997: $|\dot u|/\Theta < 10^{-4}$")

    # Floor
    Bs_floor = B_sigma(0)
    Bu_floor = B_accel(0)
    ax.plot(Bs_floor, Bu_floor, "D", color=C_GREY, ms=7, zorder=7,
            label=r"$\varepsilon_1{=}0$ floor")

    ax.set_xlabel(r"$|\sigma|/\Theta$", fontsize=16)
    ax.set_ylabel(r"$|\dot u|/\Theta$", fontsize=16)
    ax.set_xlim(0, Bs_max * 1.12)
    ax.set_ylim(0, Bu_max * 1.15)
    ax.legend(loc="upper left", fontsize=9, framealpha=0.88)

    # Annotation: rectangle vs line
    ax.annotate(
        "Physical locus is\na LINE, not a box",
        xy=(B_sigma(2.5e-3), udot_from_beta(beta_safe(2.5e-3))),
        xytext=(B_sigma(0.5e-3), Bu_max * 0.75),
        fontsize=10, color=C_BLACK,
        arrowprops=dict(arrowstyle="->", color=C_BLACK, lw=1.2),
        bbox=dict(fc="white", ec=C_BLACK, alpha=0.85, pad=3))


# =====================================================================
#  Panel (b): Bianchi V dipole closure β-parameterised curve
# =====================================================================
def panel_b(ax):
    ax.set_title(
        r"(b) Bianchi V: Dipole Closure Coupling",
        fontsize=16, pad=12)

    # For tilted Bianchi V, both σ and u̇ are functions of β:
    #   Σ²_std from momentum constraint couples to β
    #   u̇/Θ = η_u̇ β
    # The dipole closure β ≤ ε₁/(1+η_u̇) parameterises a 1D curve.
    #
    # Specifically: in the DCP (VT-09b), the momentum constraint gives
    #   Σ²_std = [(1+w)Ω_m]² β² / (4 Ω_k)
    # So σ/Θ = √(6 Σ²_std) = √(6) × [(1+w)Ω_m]/(2√Ω_k) × β
    # This is LINEAR in β, like u̇/Θ = η_u̇ β.

    # Coefficient: σ/Θ = C_σβ × β
    C_sig_beta = np.sqrt(6) * (1 + w_rad) * Omega_m / (2.0 * np.sqrt(max(Omega_k, 1e-10)))
    # This gives C_sig_beta ~ √6 × (4/3) × 0.3153 / (2 × 0.0265) ≈ 12.2

    # But this is the DCP momentum constraint — much tighter than MES!
    # The MES bound gives σ/Θ < B_σ = (5/3)ε₁ + floor
    # while the DCP gives σ/Θ ~ 12 × β ~ 12 × ε₁/1.083 ~ 11 ε₁

    # For the plot, show both:
    # (i) MES box corner (B_σ, B_u̇) — algebraic bound
    # (ii) DCP locus (C_σβ × β, η_u̇ × β) — dynamical coupling
    # (iii) Safe-route locus (B_σ(ε₁), η_u̇ × ε₁/(1+η_u̇)) — combined

    beta_range = np.linspace(0, 4.5e-3, 300)

    # DCP momentum constraint locus
    sig_DCP = C_sig_beta * beta_range
    udot_DCP = eta_ud * beta_range
    ax.plot(sig_DCP, udot_DCP, "-", color=C_RED, lw=2.5, zorder=5,
            label=rf"DCP momentum: $\sigma/\Theta = {C_sig_beta:.1f}\,\beta$")

    # MES algebraic locus (parametric in ε₁, with β = ε₁/(1+η))
    e1_range = np.linspace(0, 3.5e-3, 300)
    sig_MES = np.array([B_sigma(e) for e in e1_range])
    udot_MES = eta_ud * e1_range / (1.0 + eta_ud)
    ax.plot(sig_MES, udot_MES, "-", color=C_BLACK, lw=2.0, zorder=6,
            label=r"MES safe-route locus")

    # Scenario markers on both curves
    for sname, sc in scenarios.items():
        e1 = sc["eps1"]
        beta = beta_safe(e1)
        col = SC_COL[sname]

        # MES point
        ax.plot(B_sigma(e1), udot_from_beta(beta), "o",
                color=col, ms=9, zorder=10,
                markeredgecolor="white", markeredgewidth=1.2)
        # DCP point
        ax.plot(C_sig_beta * beta, udot_from_beta(beta), "^",
                color=col, ms=8, zorder=10,
                markeredgecolor="white", markeredgewidth=0.8)

    # Legend for scenarios
    for sname, sc in scenarios.items():
        ax.plot([], [], "o", color=SC_COL[sname], ms=7, label=sc["label"])

    # Show that DCP is tighter than MES for shear
    ax.annotate(
        "DCP tighter\nthan MES",
        xy=(C_sig_beta * beta_safe(2e-3), udot_from_beta(beta_safe(2e-3))),
        xytext=(0.001, 3e-4),
        fontsize=10, color=C_RED,
        arrowprops=dict(arrowstyle="->", color=C_RED, lw=1.2),
        bbox=dict(fc="white", ec=C_RED, alpha=0.85, pad=3))

    ax.set_xlabel(r"$|\sigma|/\Theta$", fontsize=16)
    ax.set_ylabel(r"$|\dot u|/\Theta$", fontsize=16)
    ax.set_xlim(0, B_sigma(3.5e-3) * 1.15)
    Bu_S3 = B_accel(3.296e-3)
    ax.set_ylim(0, max(Bu_S3 * 0.25, udot_from_beta(beta_safe(3.5e-3)) * 1.4))
    ax.legend(loc="upper left", fontsize=9, framealpha=0.88)


# =====================================================================
#  Panel (c): ω = 0 vs ω = ω_max (Saadeh)
# =====================================================================
def panel_c(ax):
    ax.set_title(
        r"(c) Vorticity Effect:  $\omega{=}0$ vs $\omega{=}\omega_{\rm Saadeh}$",
        fontsize=15, pad=12)

    e1_S3 = 3.296e-3
    Bs = B_sigma(e1_S3)
    Bu = B_accel(e1_S3)
    beta = beta_safe(e1_S3)

    # ω = 0 rectangle
    rect0 = mpatches.Rectangle(
        (0, 0), Bs, Bu,
        linewidth=2.5, edgecolor=C_RED, facecolor=C_RED,
        alpha=0.10, zorder=2, label=r"S3, $\omega=0$")
    ax.add_patch(rect0)

    # ω = Saadeh: the rectangle is IDENTICAL
    # Because vorticity does not modify B_σ or B_u̇ (azimuthal orthogonality)
    rect_s = mpatches.Rectangle(
        (0, 0), Bs, Bu,
        linewidth=2.0, edgecolor=C_GREEN, facecolor="none",
        ls="--", zorder=3, label=r"S3, $\omega = \omega_{\rm Saadeh}$")
    ax.add_patch(rect_s)

    # Extended defect with vorticity: x = Σ² - W²
    # W²_std(Saadeh) = 3 × (1.67e-11)² ≈ 8.3e-22
    W2_saadeh = 3.0 * omega_T_saadeh ** 2

    # For Bianchi I extended: x = (3/2)B_σ² - W²
    # Iso-defect at x = x_I(ω=0) - W²:
    S2_max = 1.5 * Bs**2
    x_with_omega = S2_max - W2_saadeh
    # Fractional change
    dx_frac = W2_saadeh / S2_max

    # Barotropic coupling line (same for both)
    e1_line = np.linspace(0, 3.5e-3, 200)
    sig_line = np.array([B_sigma(e) for e in e1_line])
    udot_line = np.array([udot_from_beta(beta_safe(e)) for e in e1_line])
    ax.plot(sig_line, udot_line, "-", color=C_BLACK, lw=2.0, zorder=5,
            label="Barotropic locus")

    # S3 point
    ax.plot(Bs, udot_from_beta(beta), "o", color=C_RED, ms=10, zorder=8,
            markeredgecolor="white", markeredgewidth=1.5)

    # The two rectangles overlap perfectly — annotate this
    ax.annotate(
        f"Rectangles are IDENTICAL\n"
        r"$\delta x / x = $" + f"{dx_frac:.1e}",
        xy=(Bs * 0.5, Bu * 0.5),
        fontsize=12, color=C_BLACK, fontweight="bold",
        ha="center", va="center",
        bbox=dict(fc="white", ec=C_BLACK, alpha=0.92, pad=5))

    ax.set_xlabel(r"$|\sigma|/\Theta$", fontsize=16)
    ax.set_ylabel(r"$|\dot u|/\Theta$", fontsize=16)
    ax.set_xlim(0, Bs * 1.15)
    ax.set_ylim(0, Bu * 1.15)
    ax.legend(loc="upper left", fontsize=10, framealpha=0.88)


# =====================================================================
#  Panel (d): Raychaudhuri constraint + nonlinear correction
# =====================================================================
def panel_d(ax):
    ax.set_title(
        r"(d) Raychaudhuri + $T_{\rm eff}$ Corrections in $(\sigma, \dot u)$",
        fontsize=14, pad=12)

    # The Raychaudhuri equation adds:
    #   Δ(Θ̇)/Θ² = ∇_a u̇^a + u̇² ≈ u̇² (homogeneous)
    # Relative to the shear term 2σ²:
    #   Δ(Raych) / σ-term = u̇² / (2σ²) = (u̇/σ)² / 2

    sig_grid = np.linspace(1e-5, 6e-3, 200)
    udot_grid = np.linspace(0, 8e-4, 200)
    SIG, UDOT = np.meshgrid(sig_grid, udot_grid)

    # Raychaudhuri correction: Δq = u̇²/Θ² relative to 2σ²/Θ²
    # (u̇/Θ)² / (2(σ/Θ)²)
    with np.errstate(divide="ignore", invalid="ignore"):
        raych_ratio = UDOT**2 / (2.0 * SIG**2)
        raych_ratio = np.where(np.isfinite(raych_ratio), raych_ratio, 0)

    raych_pct = raych_ratio * 100.0

    levels = [0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0]
    cf = ax.contourf(SIG * 1e3, UDOT * 1e4, raych_pct,
                     levels=levels, cmap="PuBuGn", alpha=0.55, extend="max")
    cs = ax.contour(SIG * 1e3, UDOT * 1e4, raych_pct,
                    levels=[0.1, 1.0, 10.0],
                    colors="k", linewidths=0.8, alpha=0.6)
    ax.clabel(cs, fontsize=9, fmt="%.1f%%")

    # Scenario markers
    for sname, sc in scenarios.items():
        e1 = sc["eps1"]
        Bs = B_sigma(e1)
        udot = udot_from_beta(beta_safe(e1))
        col = SC_COL[sname]
        ax.plot(Bs * 1e3, udot * 1e4, "o", color=col, ms=9, zorder=10,
                markeredgecolor="white", markeredgewidth=1.2)
        # Label offset depends on scenario
        offsets = {"S1": (-0.5, 0.2), "S2": (0.15, -0.3),
                   "S2c": (-0.6, 0.2), "S3": (0.15, 0.2)}
        dx, dy = offsets.get(sname, (0.15, 0.15))
        ax.text(Bs * 1e3 + dx, udot * 1e4 + dy, sname,
                fontsize=10, color=col, fontweight="bold")

    # Barotropic locus
    e1_line = np.linspace(0.5e-3, 3.5e-3, 200)
    sig_line = np.array([B_sigma(e) for e in e1_line])
    udot_line = np.array([udot_from_beta(beta_safe(e)) for e in e1_line])
    ax.plot(sig_line * 1e3, udot_line * 1e4, "-", color=C_BLACK, lw=2.0,
            zorder=7, label="Barotropic locus")

    # Stoeger horizontal
    ax.axhline(STOEGER_UDOT * 1e4, color=C_GREEN, ls="--", lw=1.5,
               alpha=0.7, label=r"Stoeger+ 1997")

    # 1% contour annotation
    ax.annotate(
        r"$|\dot u|^2/(2\sigma^2) = 1\%$" + "\n(Raychaudhuri correction)",
        xy=(1.5, 5.5), fontsize=10, ha="center",
        bbox=dict(fc="white", ec=C_GREY, alpha=0.9, pad=3))

    cbar = plt.colorbar(cf, ax=ax,
                        label=r"$|\dot u|^2 / (2\sigma^2)$ (%)",
                        shrink=0.85, pad=0.02)

    ax.set_xlabel(r"$|\sigma|/\Theta$ ($\times 10^{-3}$)", fontsize=16)
    ax.set_ylabel(r"$|\dot u|/\Theta$ ($\times 10^{-4}$)", fontsize=16)
    ax.legend(loc="upper left", fontsize=9.5, framealpha=0.88)


# =====================================================================
#  MAIN
# =====================================================================
def main():
    set_style()

    fig, axes = plt.subplots(2, 2, figsize=(16.5, 14.5))
    fig.suptitle(
        r"The $(\,|\sigma|/\Theta\;,\;|\dot u|/\Theta\,)$"
        r" Shear–Acceleration Constraint Plane",
        fontsize=20, fontweight="bold", y=0.98)

    panel_a(axes[0, 0])
    panel_b(axes[0, 1])
    panel_c(axes[1, 0])
    panel_d(axes[1, 1])

    fig.tight_layout(rect=[0, 0, 1, 0.96], h_pad=3.5, w_pad=3.5)

    outpath = "fig_sigma_accel_contour.png"
    fig.savefig(outpath, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  Saved: {outpath}")

    import shutil
    shutil.copy(outpath, "/mnt/user-data/outputs/fig_sigma_accel_contour.png")
    print("  Copied to /mnt/user-data/outputs/")


if __name__ == "__main__":
    main()
