#!/usr/bin/env python3
"""
VC-06: 4D Projection Atlas — All C(4,2)=6 2D Projections
==========================================================
Conference-ready 3×2 figure showing every pairwise projection of the
4D kinematic constraint space (Σ²_std, W²_std, A²_std, β).

Each panel overlays:
  - MES rectangular bounds (filled, per scenario)
  - Barotropic coupling locus (black line)
  - Bianchi type-specific constraint curves
  - Saadeh et al. (2016) model-dependent bound (green)
  - Stoeger (1997) acceleration bound (teal)
  - S1 solid, S0 dashed grey, S3 dashed red
"""

# SSOT_NOTE: Cosmological constants (H₀=67.36, Ω_m=0.3153) are from
# workspace/data/obs_defaults.json (Planck 2018 FLRW fit). These are
# FLRW-fitted values; Bianchi corrections O(Σ²) ~ 10⁻⁶ are negligible
# for figure-generation purposes.

import numpy as np
import matplotlib
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
eta_ud    = 1.0 / 12.0     # w/(3(1+w)), w=1/3
w_rad     = 1.0 / 3.0
Omega_m   = 0.3153
Omega_k   = 0.0007

def B_sigma(e1): return (5./3)*e1 + 3.*eps2 + (3./7)*eps3
def B_omega(e1): return (3./4)*e1 + 2.*eps2 + (2./7)*eps3
def B_accel(e1): return (3./4)*e1 + eps2 + (3./14)*eps3
def beta_sr(e1): return e1 / (1. + eta_ud)

def Sig2(e1):    return 1.5 * B_sigma(e1)**2
def W2(e1):      return 1.5 * B_omega(e1)**2
def A2(e1):      return B_accel(e1)**2
def beta_max(e1):return beta_sr(e1)

# Barotropic: u̇/Θ = η β, A²_std = η² β²
def A2_from_beta(beta): return (eta_ud * beta)**2

# Saadeh bounds
omega_T_saa = 5.0e-11 / 3.0
W2_saa      = 3.0 * omega_T_saa**2        # ~ 8.3e-22
# Stoeger bound
udot_T_sto  = 1.0e-4
A2_sto      = udot_T_sto**2               # 1e-8

# Scenarios
SC = OrderedDict([
    ("S0",  {"eps1": 0.0,      "ls": ":",  "lw": 1.5, "alpha": 0.5}),
    ("S1",  {"eps1": 1.233e-3, "ls": "-",  "lw": 2.2, "alpha": 1.0}),
    ("S3",  {"eps1": 3.296e-3, "ls": "--", "lw": 2.0, "alpha": 0.8}),
])

# Wong (2011) colorblind-friendly
C_BLUE   = "#0072B2"
C_ORANGE = "#E69F00"
C_RED    = "#D55E00"
C_PURPLE = "#CC79A7"
C_CYAN   = "#56B4E9"
C_GREEN  = "#009E73"
C_BLACK  = "#000000"
C_GREY   = "#888888"
C_YELLOW = "#F0E442"

# Bianchi type colours
TYPE_COL = {
    "I":     C_BLUE,
    "V":     C_RED,
    "VII_h": C_ORANGE,
    "IX":    C_PURPLE,
}

SC_COL = {"S0": C_GREY, "S1": C_BLUE, "S3": C_RED}


def set_style():
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 300,
        "font.size": 13, "axes.titlesize": 18,
        "axes.labelsize": 16, "xtick.labelsize": 12, "ytick.labelsize": 12,
        "legend.fontsize": 9.5, "legend.framealpha": 0.90,
        "axes.linewidth": 1.2, "lines.linewidth": 2.0,
        "axes.grid": True, "grid.alpha": 0.18, "grid.linewidth": 0.5,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "mathtext.fontset": "cm",
    })


# =====================================================================
#  Parametric loci: barotropic coupling parameterised by ε₁
# =====================================================================
N_PARAM = 200
E1P = np.linspace(1e-5, 3.8e-3, N_PARAM)

SIG2_P  = np.array([Sig2(e)    for e in E1P])
W2_P    = np.array([W2(e)      for e in E1P])
A2_P    = np.array([A2(e)      for e in E1P])
BETA_P  = np.array([beta_max(e) for e in E1P])


# =====================================================================
#  Helper: draw a single 2D projection panel
# =====================================================================
def draw_panel(ax, xkey, ykey, title, xlabel, ylabel):
    """
    xkey, ykey ∈ {'Sig2', 'W2', 'A2', 'beta'}
    """
    locus = {"Sig2": SIG2_P, "W2": W2_P, "A2": A2_P, "beta": BETA_P}
    bounds_func = {
        "Sig2":  Sig2, "W2": W2, "A2": A2, "beta": beta_max,
    }

    ax.set_title(title, fontsize=16, pad=10)

    # ----- Scenario rectangles -----
    for sname, sp in SC.items():
        e1 = sp["eps1"]
        xv = bounds_func[xkey](e1)
        yv = bounds_func[ykey](e1)
        col = SC_COL[sname]
        if xv > 0 and yv > 0:
            rect = mpatches.Rectangle(
                (0, 0), xv, yv,
                linewidth=sp["lw"], edgecolor=col,
                facecolor=col, alpha=0.06 * sp["alpha"],
                ls=sp["ls"], zorder=2)
            ax.add_patch(rect)
            ax.plot(xv, yv, "o", color=col, ms=6, zorder=7,
                    markeredgecolor="white", markeredgewidth=0.6)

    # ----- Barotropic coupling locus -----
    ax.plot(locus[xkey], locus[ykey], "-", color=C_BLACK, lw=2.5,
            zorder=8, label="Barotropic locus")

    # ----- Scenario markers on locus -----
    for sname, sp in SC.items():
        e1 = sp["eps1"]
        if e1 == 0:
            continue
        xv = bounds_func[xkey](e1)
        yv = bounds_func[ykey](e1)
        col = SC_COL[sname]
        # Physical point on barotropic locus
        # For (Sig2, W2) both at MES bounds — these are the upper-right corners
        # For (Sig2, beta) the coupling is Sig2 = f(beta) through ε₁
        ax.plot(xv, yv, "D", color=col, ms=8, zorder=10,
                markeredgecolor="white", markeredgewidth=1.2)

    # ----- Saadeh vorticity bound -----
    if ykey == "W2":
        ax.axhline(W2_saa, color=C_GREEN, ls="--", lw=1.5, alpha=0.8,
                   label=f"Saadeh+2016", zorder=3)
    if xkey == "W2":
        ax.axvline(W2_saa, color=C_GREEN, ls="--", lw=1.5, alpha=0.8,
                   label=f"Saadeh+2016", zorder=3)

    # ----- Stoeger acceleration bound -----
    if ykey == "A2":
        ax.axhline(A2_sto, color=C_CYAN, ls="-.", lw=1.5, alpha=0.8,
                   label="Stoeger+1997", zorder=3)
    if xkey == "A2":
        ax.axvline(A2_sto, color=C_CYAN, ls="-.", lw=1.5, alpha=0.8,
                   label="Stoeger+1997", zorder=3)

    # ----- Bianchi type constraint curves -----
    # Type I: x_I = Σ² (no dependence on others)
    # Type V: Ω_tilt = (1+w)Ω_m sinh²β, coupling Σ² to β through momentum constraint
    # These appear as specific curves in each projection.

    e1_S1 = SC["S1"]["eps1"]

    if xkey == "Sig2" and ykey == "beta":
        # DCP momentum constraint: Σ² = [(1+w)Ω_m]²β²/(4|Ω_k|)
        # Direct formula (Eq. 3.30)
        beta_line = np.linspace(0, beta_sr(3.8e-3), 100)
        Sig2_DCP = ((1. + w_rad) * Omega_m)**2 * beta_line**2 / (4. * max(Omega_k, 1e-6))
        mask = Sig2_DCP <= Sig2(3.8e-3) * 1.2
        ax.plot(Sig2_DCP[mask], beta_line[mask], "-",
                color=TYPE_COL["V"], lw=1.8, alpha=0.7,
                label=r"Type V (DCP)", zorder=5)

    if xkey == "Sig2" and ykey == "W2":
        # Extended defect: x = Σ² - W² + Ω_tilt
        # At fixed β = β_S1: iso-x contour is W² = Σ² - x + Ω_tilt
        x_I_S1 = Sig2(e1_S1)
        sig2_line = np.linspace(0, Sig2(3.8e-3), 100)
        # Iso-x for Type I (no tilt): x = Σ² - W² → W² = Σ² - x_I_S1
        W2_iso = sig2_line - x_I_S1
        mask = W2_iso >= 0
        ax.plot(sig2_line[mask], W2_iso[mask], ":",
                color=TYPE_COL["I"], lw=1.5, alpha=0.6,
                label=r"$x_I^{\max}$(S1) contour", zorder=4)

    if xkey == "A2" and ykey == "beta":
        # Barotropic: A² = η²β² → β = √(A²)/η
        A2_line = np.linspace(0, A2(3.8e-3), 100)
        beta_from_A = np.sqrt(A2_line) / eta_ud
        mask = beta_from_A <= beta_sr(3.8e-3) * 1.1
        ax.plot(A2_line[mask], beta_from_A[mask], "-",
                color=C_GREEN, lw=2.0, alpha=0.7,
                label=r"$\beta = |\dot u|/(\eta_{\dot u}\Theta)$", zorder=5)

    if xkey == "W2" and ykey == "A2":
        # No direct coupling between W² and A² in MES
        # But both scale with ε₁ → parametric curve
        ax.text(0.5, 0.5,
                "No direct\ncoupling\n(both scale\n" + r"with $\varepsilon_1$)",
                transform=ax.transAxes, fontsize=11, ha='center', va='center',
                color=C_GREY, style='italic',
                bbox=dict(fc='white', ec=C_GREY, alpha=0.7, pad=4))

    # ----- Labels -----
    ax.set_xlabel(xlabel, fontsize=16)
    ax.set_ylabel(ylabel, fontsize=16)

    # Auto-range
    xmax_vals = [bounds_func[xkey](SC[s]["eps1"]) for s in SC if SC[s]["eps1"] > 0]
    ymax_vals = [bounds_func[ykey](SC[s]["eps1"]) for s in SC if SC[s]["eps1"] > 0]
    if xmax_vals:
        ax.set_xlim(0, max(xmax_vals) * 1.18)
    if ymax_vals:
        ax.set_ylim(0, max(ymax_vals) * 1.18)

    ax.legend(loc="upper left", fontsize=8.5, framealpha=0.85)

    # Scenario labels near markers
    for sname in ["S1", "S3"]:
        e1 = SC[sname]["eps1"]
        xv = bounds_func[xkey](e1)
        yv = bounds_func[ykey](e1)
        col = SC_COL[sname]
        ax.text(xv * 1.04, yv * 0.92, sname, fontsize=9,
                color=col, fontweight='bold')


# =====================================================================
#  MAIN
# =====================================================================
def main():
    set_style()

    fig, axes = plt.subplots(3, 2, figsize=(17, 22))
    fig.suptitle(
        r"4D Projection Atlas:  All $\binom{4}{2}=6$ Projections of"
        r"  $(\Sigma^2,\,W^2,\,\mathcal{A}^2,\,\beta)$",
        fontsize=20, fontweight='bold', y=0.995)

    # (a) Σ² vs W²
    draw_panel(axes[0, 0], "Sig2", "W2",
               r"(a)  $\Sigma^2_{\rm std}$ vs $W^2_{\rm std}$",
               r"$\Sigma^2_{\rm std}$", r"$W^2_{\rm std}$")

    # (b) Σ² vs A²
    draw_panel(axes[0, 1], "Sig2", "A2",
               r"(b)  $\Sigma^2_{\rm std}$ vs $\mathcal{A}^2_{\rm std}$",
               r"$\Sigma^2_{\rm std}$", r"$\mathcal{A}^2_{\rm std}$")

    # (c) Σ² vs β
    draw_panel(axes[1, 0], "Sig2", "beta",
               r"(c)  $\Sigma^2_{\rm std}$ vs $\beta$",
               r"$\Sigma^2_{\rm std}$", r"$\beta$")

    # (d) W² vs A²
    draw_panel(axes[1, 1], "W2", "A2",
               r"(d)  $W^2_{\rm std}$ vs $\mathcal{A}^2_{\rm std}$",
               r"$W^2_{\rm std}$", r"$\mathcal{A}^2_{\rm std}$")

    # (e) W² vs β
    draw_panel(axes[2, 0], "W2", "beta",
               r"(e)  $W^2_{\rm std}$ vs $\beta$",
               r"$W^2_{\rm std}$", r"$\beta$")

    # (f) A² vs β
    draw_panel(axes[2, 1], "A2", "beta",
               r"(f)  $\mathcal{A}^2_{\rm std}$ vs $\beta$",
               r"$\mathcal{A}^2_{\rm std}$", r"$\beta$")

    fig.tight_layout(rect=[0, 0, 1, 0.975], h_pad=3.5, w_pad=3.0)

    outpath = "fig_4D_projection_atlas.png"
    fig.savefig(outpath, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {outpath}")

    import shutil
    shutil.copy(outpath, "/mnt/user-data/outputs/fig_4D_projection_atlas.png")
    shutil.copy(__file__, "/mnt/user-data/outputs/fig_4D_projection_atlas.py")
    print("  Copied to /mnt/user-data/outputs/")


if __name__ == "__main__":
    main()
