#!/usr/bin/env python3
"""
VC-04: 3D Constraint Volume in (|σ|/Θ, |ω|/Θ, β) Space
=========================================================
Six-panel figure:
  Top row:    (a,b) u̇ = 0 slice from two viewing angles
  Middle row: (c,d) u̇ = u̇_max slice from two viewing angles
  Bottom row: (e) slice comparison overlay  (f) 2D projections consistency
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
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
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
eta_ud = 1.0 / 12.0
w_rad = 1.0 / 3.0

def B_sigma(e1): return _C_SIG1*e1 + _C_SIG2*eps2 + _C_SIG3*eps3
def B_omega(e1): return _C_OM1*e1 + _C_OM2*eps2 + _C_OM3*eps3
def B_accel(e1): return _C_AC1*e1 + _C_AC2*eps2 + _C_AC3*eps3
def beta_safe(e1): return e1 / (1. + eta_ud)
def udot_from_beta(beta): return eta_ud * beta

omega_T_saadeh = 5.0e-11 / 3.0

scenarios = OrderedDict([
    ("S1",  {"eps1": 1.233e-3, "label": "S1"}),
    ("S2",  {"eps1": 1.476e-3, "label": "S2"}),
    ("S2c", {"eps1": 2.586e-3, "label": "S2c"}),
    ("S3",  {"eps1": 3.296e-3, "label": "S3"}),
])

C_BLUE   = "#0072B2"
C_ORANGE = "#E69F00"
C_RED    = "#D55E00"
C_PURPLE = "#CC79A7"
C_CYAN   = "#56B4E9"
C_GREEN  = "#009E73"
C_BLACK  = "#000000"
C_GREY   = "#888888"
SC_COL = {"S1": C_BLUE, "S2": C_ORANGE, "S2c": C_PURPLE, "S3": C_RED}


def set_style():
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 300,
        "font.size": 11, "axes.titlesize": 16,
        "axes.labelsize": 13, "xtick.labelsize": 10, "ytick.labelsize": 10,
        "legend.fontsize": 9.5, "legend.framealpha": 0.92,
        "axes.linewidth": 1.0, "lines.linewidth": 1.8,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "mathtext.fontset": "cm",
    })


# =====================================================================
#  Construct the allowed volume boundary for a given scenario
# =====================================================================
def allowed_boundary(e1, N=60):
    """
    For scenario with intrinsic dipole ε₁, the allowed volume in
    (σ/Θ, ω/Θ, β) is bounded by:
      σ/Θ  ∈ [0, B_σ(ε₁)]
      ω/Θ  ∈ [0, B_ω(ε₁)]
      β    ∈ [0, ε₁/(1+η_u̇)]
    with additional constraints:
      Hamiltonian: 3σ² - 3ω² > 0 for physical models → σ ≥ ω
      Defect: x = 3σ² - 3ω² + (1+w)Ω_m sinh²β ≥ 0 (always satisfied)
    
    Returns vertices of the 3D box with the σ ≥ ω diagonal cut.
    """
    Bs = B_sigma(e1)
    Bo = B_omega(e1)
    bmax = beta_safe(e1)

    sig = np.linspace(0, Bs, N)
    omg = np.linspace(0, Bo, N)
    bet = np.linspace(0, bmax, N)

    return Bs, Bo, bmax, sig, omg, bet


def draw_box_wireframe(ax, Bs, Bo, bmax, color, alpha=0.3, lw=1.5):
    """Draw the MES box edges in 3D."""
    # 12 edges of the box [0,Bs] × [0,Bo] × [0,bmax]
    s_scale = 1e3  # ×10⁻³
    o_scale = 1e3
    b_scale = 1e3

    corners = np.array([
        [0, 0, 0], [Bs, 0, 0], [Bs, Bo, 0], [0, Bo, 0],
        [0, 0, bmax], [Bs, 0, bmax], [Bs, Bo, bmax], [0, Bo, bmax]
    ])
    corners[:, 0] *= s_scale
    corners[:, 1] *= o_scale
    corners[:, 2] *= b_scale

    edges = [
        (0,1),(1,2),(2,3),(3,0),  # bottom
        (4,5),(5,6),(6,7),(7,4),  # top
        (0,4),(1,5),(2,6),(3,7),  # verticals
    ]
    for i, j in edges:
        ax.plot3D(*zip(corners[i], corners[j]),
                  color=color, alpha=alpha, lw=lw, ls='-')


def draw_diagonal_surface(ax, Bs, Bo, bmax, color, alpha=0.08):
    """Draw the σ = ω diagonal constraint surface (Hamiltonian positivity)."""
    s_scale = 1e3
    o_scale = 1e3
    b_scale = 1e3

    # Surface: ω = σ for σ ∈ [0, min(Bs, Bo)], β ∈ [0, bmax]
    sig_max = min(Bs, Bo)
    N = 20
    sig = np.linspace(0, sig_max, N)
    bet = np.linspace(0, bmax, N)
    SIG, BET = np.meshgrid(sig, bet)
    OMG = SIG  # diagonal

    ax.plot_surface(SIG * s_scale, OMG * o_scale, BET * b_scale,
                    color=color, alpha=alpha, zorder=1)


def draw_iso_defect_surface(ax, x_val, w, Bs, Bo, bmax, color, alpha=0.12, N=30):
    """
    Iso-defect surface: x = 3σ² - 3ω² + (1+w)Ω_m × sinh²β = const
    → ω = √(σ² + [(1+w)Ω_m sinh²β - x]/3)  ... only physical part
    """
    Omega_m = 0.3153
    s_scale, o_scale, b_scale = 1e3, 1e3, 1e3
    sig = np.linspace(1e-6, Bs, N)
    bet = np.linspace(0, bmax, N)
    SIG, BET = np.meshgrid(sig, bet)

    tilt_term = (1. + w) * Omega_m * np.sinh(BET)**2
    omg_sq = SIG**2 - (x_val - tilt_term) / 3.
    omg_sq = np.where(omg_sq >= 0, omg_sq, np.nan)
    OMG = np.sqrt(omg_sq)

    # Clip to box
    mask = (OMG <= Bo) & np.isfinite(OMG)
    OMG_clipped = np.where(mask, OMG, np.nan)

    ax.plot_surface(SIG * s_scale, OMG_clipped * o_scale, BET * b_scale,
                    color=color, alpha=alpha, zorder=2)


def draw_scenario_points(ax, scenarios_dict, udot_fixed=None):
    """Plot scenario markers in 3D."""
    s_scale, o_scale, b_scale = 1e3, 1e3, 1e3
    for sname, sc in scenarios_dict.items():
        e1 = sc['eps1']
        Bs = B_sigma(e1)
        Bo = B_omega(e1)
        bmax = beta_safe(e1)
        col = SC_COL[sname]

        # Physical point: on the barotropic coupling line
        # (σ at MES bound, ω at MES bound, β at safe-route)
        ax.scatter([Bs * s_scale], [Bo * o_scale], [bmax * b_scale],
                   color=col, s=60, zorder=10, edgecolors='white',
                   linewidths=1.0, depthshade=False)
        ax.text(Bs * s_scale, Bo * o_scale, bmax * b_scale + 0.15,
                sname, fontsize=9, color=col, fontweight='bold',
                ha='center', zorder=11)


def setup_3d_axes(ax, title, elev=25, azim=-60):
    """Common 3D axes formatting."""
    ax.set_title(title, fontsize=14, pad=12)
    ax.set_xlabel(r"$|\sigma|/\Theta$ ($\times 10^{-3}$)", fontsize=11, labelpad=8)
    ax.set_ylabel(r"$|\omega|/\Theta$ ($\times 10^{-3}$)", fontsize=11, labelpad=8)
    ax.set_zlabel(r"$\beta$ ($\times 10^{-3}$)", fontsize=11, labelpad=8)
    ax.view_init(elev=elev, azim=azim)
    ax.tick_params(axis='both', labelsize=9)
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.xaxis.pane.set_edgecolor('grey')
    ax.yaxis.pane.set_edgecolor('grey')
    ax.zaxis.pane.set_edgecolor('grey')
    ax.grid(True, alpha=0.15)


# =====================================================================
#  Panel (a,b): u̇ = 0 slice — two viewing angles
# =====================================================================
def panel_udot_zero(ax, elev, azim, label):
    """u̇ = 0 ↔ β = 0 (geometry frame, geodesic observers).
    The 3D volume collapses to the β = 0 plane, but we show
    the structure of the MES boxes at different β values too."""

    setup_3d_axes(ax, f"({label}) " + r"$\dot u = 0$ slice" +
                  f"\n(elev={elev}°, azim={azim}°)", elev, azim)

    # Draw scenario boxes
    for sname in ["S1", "S3"]:
        e1 = scenarios[sname]['eps1']
        Bs, Bo, bmax, _, _, _ = allowed_boundary(e1)
        col = SC_COL[sname]
        draw_box_wireframe(ax, Bs, Bo, bmax, col, alpha=0.35, lw=1.5)

    # Diagonal surface (Hamiltonian: σ ≥ ω)
    e1_S3 = scenarios['S3']['eps1']
    Bs3, Bo3, bm3, _, _, _ = allowed_boundary(e1_S3)
    draw_diagonal_surface(ax, Bs3, Bo3, bm3, C_GREY, alpha=0.06)

    # Iso-defect surfaces for Bianchi I (x = Σ²_std = 3σ²)
    # At β = 0: x = 3σ² - 3ω², so iso-x is a hyperbolic cylinder in (σ,ω,β)
    x_S1 = 1.5 * B_sigma(scenarios['S1']['eps1'])**2
    x_S3 = 1.5 * B_sigma(scenarios['S3']['eps1'])**2
    draw_iso_defect_surface(ax, x_S1, w_rad, Bs3, Bo3, bm3, C_BLUE, alpha=0.08)
    draw_iso_defect_surface(ax, x_S3, w_rad, Bs3, Bo3, bm3, C_RED, alpha=0.08)

    # Scenario markers
    draw_scenario_points(ax, scenarios)

    ax.set_xlim(0, 6.5)
    ax.set_ylim(0, 3.5)
    ax.set_zlim(0, 3.5)


# =====================================================================
#  Panel (c,d): u̇ = u̇_max slice — two viewing angles
# =====================================================================
def panel_udot_max(ax, elev, azim, label):
    """u̇ = u̇_max: β is at its maximum safe-route value.
    For each ε₁, β_max = ε₁/(1+η_u̇), and u̇_max = η_u̇ × β_max."""

    setup_3d_axes(ax, f"({label}) " + r"$\dot u = \dot u_{\max}$ slice" +
                  f"\n(elev={elev}°, azim={azim}°)", elev, azim)

    # Draw scenario boxes
    for sname in ["S1", "S3"]:
        e1 = scenarios[sname]['eps1']
        Bs, Bo, bmax, _, _, _ = allowed_boundary(e1)
        col = SC_COL[sname]
        draw_box_wireframe(ax, Bs, Bo, bmax, col, alpha=0.35, lw=1.5)

    # Physical constraint: β parameterises a LINE in (σ, ω, β) space
    # At each β, the MES bounds are:
    #   σ/Θ < B_σ(ε₁) where ε₁ = (1+η_u̇)β
    #   ω/Θ < B_ω(ε₁)
    # So the physical volume is a "growing box" as β increases.

    # Draw the β-parameterised boundary surface: σ = B_σ((1+η_u̇)β)
    N = 80
    betas = np.linspace(0, beta_safe(scenarios['S3']['eps1']), N)
    for sname in ["S1", "S3"]:
        e1 = scenarios[sname]['eps1']
        bmax = beta_safe(e1)
        b_arr = np.linspace(0, bmax, N)
        # Sigma boundary as function of β (growing box)
        sig_bound = np.array([B_sigma((1.+eta_ud)*b) for b in b_arr])
        omg_bound = np.array([B_omega((1.+eta_ud)*b) for b in b_arr])
        col = SC_COL[sname]

        # Draw the σ-max boundary wall
        ax.plot(sig_bound * 1e3, omg_bound * 1e3, b_arr * 1e3,
                '-', color=col, lw=2.5, alpha=0.8, zorder=5)
        # Project onto σ-β plane (ω=0)
        ax.plot(sig_bound * 1e3, np.zeros_like(b_arr), b_arr * 1e3,
                ':', color=col, lw=1.0, alpha=0.4)
        # Project onto ω-β plane (σ=0)
        ax.plot(np.zeros_like(b_arr), omg_bound * 1e3, b_arr * 1e3,
                ':', color=col, lw=1.0, alpha=0.4)

    # Diagonal surface
    draw_diagonal_surface(ax, Bs, Bo, bmax, C_GREY, alpha=0.04)

    # Scenario markers
    draw_scenario_points(ax, scenarios)

    ax.set_xlim(0, 6.5)
    ax.set_ylim(0, 3.5)
    ax.set_zlim(0, 3.5)


# =====================================================================
#  Panel (e): Slice comparison — u̇=0 vs u̇=u̇_max overlay
# =====================================================================
def panel_comparison(ax, elev=30, azim=-50):
    """Overlay the two slices to show the volume change."""

    setup_3d_axes(ax, "(e) Slice Comparison:\n" +
                  r"$\dot u{=}0$ (blue) vs $\dot u{=}\dot u_{\max}$ (red)",
                  elev, azim)

    e1 = scenarios['S3']['eps1']
    Bs, Bo, bmax, _, _, _ = allowed_boundary(e1)

    # u̇ = 0: the full box
    draw_box_wireframe(ax, Bs, Bo, bmax, C_BLUE, alpha=0.5, lw=2.0)

    # u̇ = u̇_max: physically identical box (β determines ε₁ determines bounds)
    # The point is that the BOX IS THE SAME — u̇ is derived, not independent
    draw_box_wireframe(ax, Bs, Bo, bmax, C_RED, alpha=0.3, lw=1.5)

    # Barotropic coupling line
    N = 50
    e1_line = np.linspace(0, e1, N)
    sig_l = np.array([B_sigma(e) for e in e1_line])
    omg_l = np.array([B_omega(e) for e in e1_line])
    bet_l = np.array([beta_safe(e) for e in e1_line])
    ax.plot(sig_l * 1e3, omg_l * 1e3, bet_l * 1e3,
            '-', color=C_BLACK, lw=3.0, zorder=8, label='Physical locus')

    # Corner markers
    ax.scatter([Bs*1e3], [Bo*1e3], [bmax*1e3],
               color=C_RED, s=80, zorder=10, edgecolors='white',
               linewidths=1.5, depthshade=False)
    ax.scatter([Bs*1e3], [Bo*1e3], [0],
               color=C_BLUE, s=60, zorder=10, marker='^',
               edgecolors='white', linewidths=1.0, depthshade=False)

    # Annotation
    ax.text(3.0, 1.5, 3.0,
            "Boxes IDENTICAL\nfor barotropic fluid:\n" +
            r"$\dot u$ is derived from $\beta$",
            fontsize=9, ha='center', color=C_BLACK,
            bbox=dict(fc='white', ec=C_BLACK, alpha=0.85, pad=3))

    ax.set_xlim(0, 6.5)
    ax.set_ylim(0, 3.5)
    ax.set_zlim(0, 3.5)
    ax.legend(loc='upper left', fontsize=9)


# =====================================================================
#  Panel (f): 2D projections — consistency check
# =====================================================================
def panel_projections(ax):
    """Show the three 2D projections of the 3D volume."""
    ax.set_title("(f) 2D Projections of 3D Volume", fontsize=14, pad=8)

    # Three sub-regions within the 2D panel
    # Layout: (σ,ω) top-left, (σ,β) top-right, (ω,β) bottom-left

    e1_S3 = scenarios['S3']['eps1']
    Bs = B_sigma(e1_S3) * 1e3
    Bo = B_omega(e1_S3) * 1e3
    bm = beta_safe(e1_S3) * 1e3

    # Relative layout in normalised coords
    # (σ, ω) projection
    rect_w, rect_h = Bs, Bo
    ax.add_patch(plt.Rectangle((0.5, 4.5), Bs, Bo,
                                fc=C_RED, alpha=0.12, ec=C_RED, lw=2.0))
    ax.text(0.5 + Bs/2, 4.5 + Bo + 0.15,
            r"$(\sigma/\Theta, \omega/\Theta)$" + "\n= VC-02 Fig (a)",
            fontsize=9, ha='center', va='bottom', color=C_RED)

    # (σ, β) projection
    ax.add_patch(plt.Rectangle((0.5, 0.5), Bs, bm,
                                fc=C_BLUE, alpha=0.12, ec=C_BLUE, lw=2.0))
    ax.text(0.5 + Bs/2, 0.5 + bm + 0.15,
            r"$(\sigma/\Theta, \beta)$",
            fontsize=9, ha='center', va='bottom', color=C_BLUE)

    # Barotropic line in (σ,β) plane
    e1_line = np.linspace(0, e1_S3, 100)
    sig_l = np.array([B_sigma(e)*1e3 for e in e1_line])
    bet_l = np.array([beta_safe(e)*1e3 for e in e1_line])
    ax.plot(0.5 + sig_l, 0.5 + bet_l, '-', color=C_BLACK, lw=2.0)

    # (ω, β) projection
    omg_l = np.array([B_omega(e)*1e3 for e in e1_line])
    ax.add_patch(plt.Rectangle((8.0, 0.5), Bo, bm,
                                fc=C_GREEN, alpha=0.12, ec=C_GREEN, lw=2.0))
    ax.text(8.0 + Bo/2, 0.5 + bm + 0.15,
            r"$(\omega/\Theta, \beta)$",
            fontsize=9, ha='center', va='bottom', color=C_GREEN)
    ax.plot(8.0 + omg_l, 0.5 + bet_l, '-', color=C_BLACK, lw=2.0)

    # Labels for physical line
    ax.text(0.5 + Bs*0.4, 0.5 + bm*0.5, "Physical\nlocus",
            fontsize=8, ha='center', color=C_BLACK, style='italic')
    ax.text(8.0 + Bo*0.4, 0.5 + bm*0.5, "Physical\nlocus",
            fontsize=8, ha='center', color=C_BLACK, style='italic')

    # Dimension annotations
    ax.annotate("", xy=(0.5+Bs, 4.3), xytext=(0.5, 4.3),
                arrowprops=dict(arrowstyle='<->', color=C_RED, lw=1.2))
    ax.text(0.5+Bs/2, 4.1, f"B_σ={Bs:.1f}" + r"$\times 10^{-3}$",
            fontsize=8, ha='center', color=C_RED)

    ax.set_xlim(-0.5, 12)
    ax.set_ylim(-0.5, 9.5)
    ax.set_aspect('equal')
    ax.axis('off')


# =====================================================================
#  MAIN
# =====================================================================
def main():
    set_style()

    fig = plt.figure(figsize=(18, 24))
    fig.suptitle(
        r"3D Constraint Volume in $(\,|\sigma|/\Theta,\;|\omega|/\Theta,\;\beta\,)$ Space",
        fontsize=22, fontweight='bold', y=0.98)

    # Top row: u̇ = 0 slice, two angles
    ax1 = fig.add_subplot(3, 2, 1, projection='3d')
    panel_udot_zero(ax1, elev=25, azim=-60, label='a')

    ax2 = fig.add_subplot(3, 2, 2, projection='3d')
    panel_udot_zero(ax2, elev=40, azim=-135, label='b')

    # Middle row: u̇ = u̇_max slice, two angles
    ax3 = fig.add_subplot(3, 2, 3, projection='3d')
    panel_udot_max(ax3, elev=25, azim=-60, label='c')

    ax4 = fig.add_subplot(3, 2, 4, projection='3d')
    panel_udot_max(ax4, elev=40, azim=-135, label='d')

    # Bottom row: comparison + projections
    ax5 = fig.add_subplot(3, 2, 5, projection='3d')
    panel_comparison(ax5, elev=30, azim=-55)

    ax6 = fig.add_subplot(3, 2, 6)
    panel_projections(ax6)

    fig.tight_layout(rect=[0, 0, 1, 0.96], h_pad=4.0, w_pad=2.0)

    outpath = "fig_3D_constraint_volume.png"
    fig.savefig(outpath, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {outpath}")

    import shutil
    shutil.copy(outpath, "/mnt/user-data/outputs/fig_3D_constraint_volume.png")
    print("  Copied to /mnt/user-data/outputs/")


if __name__ == "__main__":
    main()
