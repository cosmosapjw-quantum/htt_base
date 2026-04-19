#!/usr/bin/env python3
"""
VC-02: (|σ|/Θ , |ω|/Θ) Constraint Plane Visualisation
========================================================
Four-panel figure:
  (a) MES rectangular bounds per scenario + iso-defect contours
  (b) Log–log view of the full hierarchy (MES → Saadeh → zero)
  (c) Bianchi-type iso-defect anatomy (hyperbolic curves)
  (d) Error budget: shear vs vorticity nonlinear corrections
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.colors import LinearSegmentedColormap
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
eta_ud = 1./12  # w/(3(1+w)) for w=1/3

def B_sigma(e1): return (5./3)*e1 + 3.*eps2 + (3./7)*eps3
def B_omega(e1): return (3./4)*e1 + 2.*eps2 + (2./7)*eps3
def B_accel(e1): return (3./4)*e1 + eps2 + (3./14)*eps3

# Saadeh et al. (2016)
omega_T_saadeh = 5.0e-11 / 3.0   # |ω|/Θ

# Scenarios
scenarios = OrderedDict([
    ("S1",  {"eps1": 1.233e-3, "label": "S1 (Ferreira–Quartin)"}),
    ("S2",  {"eps1": 1.476e-3, "label": "S2 (CatWISE)"}),
    ("S2c", {"eps1": 2.586e-3, "label": "S2c (NVSS+RACS)"}),
    ("S3",  {"eps1": 3.296e-3, "label": "S3 (Böhme+2025)"}),
])

# Colourblind-friendly (Wong 2011)
C_BLUE   = "#0072B2"
C_ORANGE = "#E69F00"
C_RED    = "#D55E00"
C_PURPLE = "#CC79A7"
C_CYAN   = "#56B4E9"
C_GREEN  = "#009E73"
C_BLACK  = "#000000"
C_GREY   = "#999999"

SC_COLORS = {"S1": C_BLUE, "S2": C_ORANGE, "S2c": C_PURPLE, "S3": C_RED}

# =====================================================================
#  Style
# =====================================================================
def set_style():
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 300,
        "font.size": 13,
        "axes.titlesize": 18, "axes.labelsize": 16,
        "xtick.labelsize": 13, "ytick.labelsize": 13,
        "legend.fontsize": 11, "legend.framealpha": 0.92,
        "axes.linewidth": 1.2,
        "lines.linewidth": 2.0,
        "axes.grid": True, "grid.alpha": 0.20, "grid.linewidth": 0.5,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "mathtext.fontset": "cm",
    })

# =====================================================================
#  Panel (a): Linear-scale MES rectangular bounds + defect contours
# =====================================================================
def panel_a(ax):
    """MES allowed regions for each scenario."""
    ax.set_title(r"(a) MES Allowed Region:  $|\sigma|/\Theta$ vs $|\omega|/\Theta$",
                 fontsize=16, pad=12)
    
    # Draw scenario rectangles from largest to smallest
    for sname in reversed(list(scenarios.keys())):
        sc = scenarios[sname]
        e1 = sc['eps1']
        Bs = B_sigma(e1)
        Bo = B_omega(e1)
        col = SC_COLORS[sname]
        
        rect = mpatches.Rectangle((0, 0), Bs, Bo,
                                   linewidth=2.2, edgecolor=col,
                                   facecolor=col, alpha=0.10,
                                   label=sc['label'], zorder=2)
        ax.add_patch(rect)
        # Corner marker
        ax.plot(Bs, Bo, 'o', color=col, ms=7, zorder=5)
    
    # Iso-defect contours for Bianchi I extended: x = 3(σ/Θ)² - 3(ω/Θ)²
    Bs_max = B_sigma(3.5e-3)
    sig_grid = np.linspace(0, Bs_max*1.05, 300)
    
    # Defect values to contour (as Σ²_std = (3/2)B_σ² for each scenario)
    x_levels = []
    for sname in ["S1", "S3"]:
        e1 = scenarios[sname]['eps1']
        Bs = B_sigma(e1)
        x_levels.append(((3./2)*Bs**2, sname))
    
    for xval, sname in x_levels:
        # x = 3σ² - 3ω² → ω² = σ² - x/3
        omega_sq = sig_grid**2 - xval/3.
        mask = omega_sq >= 0
        if np.any(mask):
            omega_line = np.sqrt(omega_sq[mask])
            ax.plot(sig_grid[mask], omega_line,
                    '--', color=SC_COLORS[sname], alpha=0.5, lw=1.5,
                    label=rf"$x_{{\mathrm{{I}}}}$ = {xval:.1e} ({sname})")
    
    # Diagonal: σ/Θ = ω/Θ (Hamiltonian positivity boundary)
    diag = np.linspace(0, Bs_max*1.05, 100)
    ax.plot(diag, diag, ':', color=C_GREY, lw=1.2, alpha=0.5, zorder=1)
    # Label at the bottom of the visible diagonal
    ax.text(Bs_max*0.25, Bs_max*0.30, r"$|\sigma|{=}|\omega|$",
            fontsize=10, color=C_GREY, rotation=42, ha='center',
            bbox=dict(fc='white', ec='none', alpha=0.7, pad=1))
    
    ax.set_xlabel(r"$|\sigma|/\Theta$", fontsize=16)
    ax.set_ylabel(r"$|\omega|/\Theta$", fontsize=16)
    ax.set_xlim(0, Bs_max*1.08)
    ax.set_ylim(0, B_omega(3.5e-3)*1.12)
    ax.legend(loc='upper left', fontsize=9.5, framealpha=0.85)
    
    # Annotation: floor values
    Bs_floor = B_sigma(0.)
    Bo_floor = B_omega(0.)
    ax.axvline(Bs_floor, color=C_GREY, ls=':', lw=0.8, alpha=0.4)
    ax.axhline(Bo_floor, color=C_GREY, ls=':', lw=0.8, alpha=0.4)

# =====================================================================
#  Panel (b): Log-log hierarchy showing the 17-order gap
# =====================================================================
def panel_b(ax):
    """Log-log view: MES algebraic vs Saadeh model-dependent."""
    ax.set_title(r"(b) Bound Hierarchy: MES vs Saadeh", fontsize=16, pad=12)
    
    # Scenario points: (B_σ, B_ω) and Saadeh horizontal
    for sname, sc in scenarios.items():
        e1 = sc['eps1']
        Bs = B_sigma(e1)
        Bo = B_omega(e1)
        col = SC_COLORS[sname]
        ax.plot(Bs, Bo, 'o', color=col, ms=10, zorder=10, label=sc['label'])
    
    # MES locus: parametric in ε₁
    e1_range = np.linspace(1e-4, 4e-3, 200)
    Bs_arr = np.array([B_sigma(e) for e in e1_range])
    Bo_arr = np.array([B_omega(e) for e in e1_range])
    ax.plot(Bs_arr, Bo_arr, '-', color=C_BLACK, lw=1.8, alpha=0.7,
            label='MES bound locus')
    
    # Saadeh horizontal band
    ax.axhspan(0, omega_T_saadeh, color=C_GREEN, alpha=0.15, zorder=1)
    ax.axhline(omega_T_saadeh, color=C_GREEN, ls='--', lw=1.8,
               label=rf"Saadeh+2016: $|\omega|/\Theta < {omega_T_saadeh:.1e}$")
    
    # Gap annotation
    Bo_S3 = B_omega(3.296e-3)
    mid_y = np.sqrt(omega_T_saadeh * Bo_S3)
    ax.annotate("", xy=(B_sigma(3.296e-3)*0.7, omega_T_saadeh*5),
                xytext=(B_sigma(3.296e-3)*0.7, Bo_S3*0.3),
                arrowprops=dict(arrowstyle='<->', color=C_RED, lw=1.5))
    ax.text(B_sigma(3.296e-3)*0.55, mid_y*3,
            r"$\sim 10^{6}$ gap",
            fontsize=13, color=C_RED, fontweight='bold', ha='center')
    
    # Floor: ε₁ = 0
    Bs_floor = B_sigma(0.)
    Bo_floor = B_omega(0.)
    ax.plot(Bs_floor, Bo_floor, 's', color=C_GREY, ms=8,
            label=rf"$\varepsilon_1=0$ floor", zorder=8)
    
    ax.set_xlabel(r"$|\sigma|/\Theta$ bound  ($B_\sigma$)", fontsize=16)
    ax.set_ylabel(r"$|\omega|/\Theta$ bound", fontsize=16)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(3e-6, 8e-3)
    ax.set_ylim(5e-12, 5e-3)
    ax.legend(loc='upper left', fontsize=9, framealpha=0.85)

# =====================================================================
#  Panel (c): Bianchi-type iso-defect anatomy
# =====================================================================
def panel_c(ax):
    """Iso-defect contours showing how vorticity lowers x."""
    ax.set_title(r"(c) Iso-Defect Contours: $x = 3(\sigma/\Theta)^2 - 3(\omega/\Theta)^2$",
                 fontsize=14, pad=12)
    
    # S3 parameters
    e1 = 3.296e-3
    Bs = B_sigma(e1)
    Bo = B_omega(e1)
    
    # Draw MES box
    rect = mpatches.Rectangle((0, 0), Bs, Bo,
                               linewidth=2.0, edgecolor=C_RED,
                               facecolor='none', zorder=3, ls='-')
    ax.add_patch(rect)
    
    # Iso-defect curves: x = 3σ² − 3ω² → ω = √(σ² − x/3)
    sig_fine = np.linspace(0, Bs*1.15, 500)
    
    x_contours = [
        (1.5*Bs**2,              C_RED,    2.0, '-',  r"$x_I^{\max}$ (S3)"),
        (1.5*B_sigma(1.233e-3)**2, C_BLUE, 1.5, '-',  r"$x_I^{\max}$ (S1)"),
        (0.5*1.5*Bs**2,         C_ORANGE, 1.3, '--', r"$x = \frac{1}{2}x_I^{\max}$"),
        (0.1*1.5*Bs**2,         C_PURPLE, 1.3, ':',  r"$x = 0.1\,x_I^{\max}$"),
        (0.0,                    C_GREY,   1.5, '-',  r"$x = 0$ (FLRW)"),
    ]
    
    for xval, col, lw, ls, lab in x_contours:
        omg_sq = sig_fine**2 - xval/3.
        mask = omg_sq >= 0
        if np.any(mask):
            omg_line = np.sqrt(omg_sq[mask])
            # Only draw within the box
            in_box = omg_line <= Bo * 1.05
            if np.any(in_box):
                ax.plot(sig_fine[mask][in_box], omg_line[in_box],
                        ls=ls, color=col, lw=lw, label=lab, zorder=4)
    
    # x = 0 line is σ = ω (45° diagonal)
    # x < 0 region: shade (unphysical if we demand x ≥ 0)
    # For models where x can be negative (vorticity-dominated), shade differently
    fill_sig = np.linspace(0, min(Bs, Bo)*1.05, 200)
    ax.fill_between(fill_sig, fill_sig, Bo*1.1,
                    color=C_GREEN, alpha=0.07, zorder=1)
    ax.text(Bs*0.55, Bo*0.92, r"$x < 0$  (ω-dominated)",
            fontsize=10, color=C_GREEN, ha='center', style='italic')
    
    ax.fill_between(fill_sig, 0, fill_sig,
                    color=C_RED, alpha=0.04, zorder=1)
    ax.text(Bs*0.85, Bo*0.08, r"$x > 0$" + "\n(σ-dominated)",
            fontsize=10, color=C_RED, ha='center', style='italic')
    
    # Arrow showing vorticity reduces defect
    ax.annotate("",
                xy=(Bs*0.55, Bo*0.60),
                xytext=(Bs*0.55, Bo*0.35),
                arrowprops=dict(arrowstyle='->', color=C_BLACK, lw=2.0))
    ax.text(Bs*0.58, Bo*0.48, r"$\omega$ reduces $x$",
            fontsize=11, color=C_BLACK, fontweight='bold')
    
    ax.set_xlabel(r"$|\sigma|/\Theta$", fontsize=16)
    ax.set_ylabel(r"$|\omega|/\Theta$", fontsize=16)
    ax.set_xlim(0, Bs*1.15)
    ax.set_ylim(0, Bo*1.10)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.88)

# =====================================================================
#  Panel (d): Nonlinear correction landscape in (σ, ω) plane
# =====================================================================
def panel_d(ax):
    """Heatmap of δΣ²/Σ² as function of σ/Θ, showing ω irrelevance."""
    ax.set_title(r"(d) $T_{\rm eff}$ Correction $\delta\Sigma^2/\Sigma^2$: "
                 r"$\omega$ Irrelevance",
                 fontsize=14, pad=12)
    
    # The T_eff correction depends on Σ₂ = A²/3 + 4Q²/45 ≈ (ε₁)²/3
    # It does NOT depend on ω (VN-01: f(ω) = 0)
    # So the heatmap has vertical contours only
    
    sig_grid = np.linspace(1e-5, 6e-3, 200)
    omg_grid = np.linspace(0, 4e-3, 200)
    SIG, OMG = np.meshgrid(sig_grid, omg_grid)
    
    # δΣ²/Σ² ≈ 10 × (σ/Θ)²  (empirical fit from VN-04)
    # More precise: R_σ² - 1 ≈ 2Δ_σ ≈ 2 × 0.82 × (ε₁/Θ)² (rough)
    # Using exact computation would require T_eff quadrature
    # Simplified: δΣ²/Σ² = c × Σ₂ where Σ₂ = A²/3 ≈ (σ/Θ)²/3
    # c ≈ 10 (alpha(alpha+1)/2 = 10 for alpha=4)
    # So δΣ²/Σ² ≈ 10 × (σ/Θ)²/3 ≈ 3.33 × (σ/Θ)²
    # This is independent of ω!
    correction = 10.0/3.0 * SIG**2 * 100.  # in percent
    
    # Contour plot
    levels = [0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
    cf = ax.contourf(SIG*1e3, OMG*1e3, correction, levels=levels,
                     cmap='YlOrRd', alpha=0.6, extend='max')
    cs = ax.contour(SIG*1e3, OMG*1e3, correction, levels=levels,
                    colors='k', linewidths=0.8, alpha=0.5)
    ax.clabel(cs, levels[:-1], fontsize=9, fmt='%.1f%%')
    
    # Scenario markers
    for sname, sc in scenarios.items():
        e1 = sc['eps1']
        Bs = B_sigma(e1)
        Bo = B_omega(e1)
        col = SC_COLORS[sname]
        ax.plot(Bs*1e3, Bo*1e3, 'o', color=col, ms=8, zorder=10,
                markeredgecolor='white', markeredgewidth=1.0)
        ax.text(Bs*1e3 + 0.08, Bo*1e3 + 0.05, sname,
                fontsize=10, color=col, fontweight='bold')
    
    # Key annotation: vertical contours = ω irrelevance
    ax.annotate("Contours are vertical\n" + r"$\Rightarrow$ $\omega$ has zero effect",
                xy=(4.5, 1.5), fontsize=11, color=C_BLACK,
                bbox=dict(boxstyle='round,pad=0.4', fc='white', ec=C_BLACK, alpha=0.9),
                ha='center')
    
    cbar = plt.colorbar(cf, ax=ax, label=r'$\delta\Sigma^2/\Sigma^2$ (%)',
                        shrink=0.85, pad=0.02)
    
    ax.set_xlabel(r"$|\sigma|/\Theta$ ($\times 10^{-3}$)", fontsize=16)
    ax.set_ylabel(r"$|\omega|/\Theta$ ($\times 10^{-3}$)", fontsize=16)

# =====================================================================
#  MAIN
# =====================================================================
def main():
    set_style()
    
    fig, axes = plt.subplots(2, 2, figsize=(16.5, 14.5))
    fig.suptitle(
        r"The $(\,|\sigma|/\Theta\;,\;|\omega|/\Theta\,)$ Kinematic Constraint Plane",
        fontsize=20, fontweight='bold', y=0.98)
    
    panel_a(axes[0, 0])
    panel_b(axes[0, 1])
    panel_c(axes[1, 0])
    panel_d(axes[1, 1])
    
    fig.tight_layout(rect=[0, 0, 1, 0.96], h_pad=3.5, w_pad=3.5)
    
    outpath = "fig_sigma_omega_contour.png"
    fig.savefig(outpath, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {outpath}")
    
    # Also save to outputs
    import shutil
    shutil.copy(outpath, "/mnt/user-data/outputs/fig_sigma_omega_contour.png")
    print(f"  Copied to /mnt/user-data/outputs/")

if __name__ == "__main__":
    main()
