#!/usr/bin/env python3
"""
VC-05: Nonlinear Correction Heatmaps in the (ε₁, |ω|/Θ) Plane
================================================================
Six-panel figure:
  (a) Δ_σ(ε₁, ω/Θ)  — shear correction
  (b) Δ_ω(ε₁, ω/Θ)  — vorticity bound correction
  (c) Δ_u̇(ε₁, ω/Θ)  — acceleration bound correction
  (d) 1% validity boundary + scenario overlay
  (e) ε₁-dependence cross-section (ω/Θ = 0 vs Saadeh vs MES)
  (f) ω/Θ-dependence cross-section (fixed ε₁ = S3)

Key result: ALL heatmaps have vertical contours → ω is irrelevant.
"""
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
from matplotlib.colors import LogNorm
from scipy.special import roots_legendre
from collections import OrderedDict

# =====================================================================
#  Constants
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

_NGL = 200
_MU, _W = roots_legendre(_NGL)

def B_sigma_lin(e1):
    return _C_SIG1*e1 + _C_SIG2*eps2 + _C_SIG3*eps3
def B_omega_lin(e1):
    return _C_OM1*e1 + _C_OM2*eps2 + _C_OM3*eps3
def B_accel_lin(e1):
    return _C_AC1*e1 + _C_AC2*eps2 + _C_AC3*eps3

def _Theta(mu, A, Q):
    return 1.0 + A*mu + Q*(mu**2 - 1./3)
def _int_Bsq(ell):
    return {0:2., 1:2./3, 2:8./45, 3:8./175}[ell]
def _Bell(mu, ell):
    if ell == 0: return np.ones_like(mu)
    if ell == 1: return mu
    if ell == 2: return mu**2 - 1./3
    if ell == 3: return mu**3 - 3.*mu/5
    raise ValueError

def compute_R(e1, bound_type='sigma'):
    """Nonlinear correction ratio R_X = B_X^nl / B_X^lin."""
    if e1 <= 0:
        return 1.0
    A, Q = e1, eps2
    Th = _Theta(_MU, A, Q)
    if np.any(Th <= 0):
        return 1.0
    F = Th**4
    mp = {}
    for ell in range(4):
        Bl = _Bell(_MU, ell)
        mp[ell] = np.dot(_W, F * Bl) / _int_Bsq(ell)
    e1e = abs(mp[1]) / 4.
    e2e = abs(mp[2]) / 4.
    e3e = abs(mp.get(3, 0.)) / 4.

    if bound_type == 'sigma':
        Bl = B_sigma_lin(e1)
        Bnl = _C_SIG1*e1e + _C_SIG2*e2e + _C_SIG3*(eps3 + e3e)
    elif bound_type == 'omega':
        Bl = B_omega_lin(e1)
        Bnl = _C_OM1*e1e + _C_OM2*e2e + _C_OM3*(eps3 + e3e)
    elif bound_type == 'accel':
        Bl = B_accel_lin(e1)
        Bnl = _C_AC1*e1e + _C_AC2*e2e + _C_AC3*(eps3 + e3e)
    else:
        raise ValueError
    return Bnl / Bl if Bl > 0 else 1.0

# Pre-compute correction grids
def build_correction_grid(e1_arr, omega_arr, bound_type):
    """
    Build Δ_X(ε₁, ω/Θ) grid.
    
    From VN-01b: the vorticity modification to Δ_X is
      δΔ_X(ω) = Δ_X(σ-only) × (ω/ω_MES)² × 3×10⁻¹⁰
    where ω_MES ~ B_ω(ε₁).
    
    So Δ_X(ε₁, ω) = Δ_X(ε₁, 0) × [1 + 3×10⁻¹⁰ × (ω/B_ω(ε₁))²]
    The ω-dependence is at the 10⁻¹⁰ level — essentially zero.
    """
    Ne = len(e1_arr)
    No = len(omega_arr)
    Delta = np.zeros((No, Ne))
    
    for i, e1 in enumerate(e1_arr):
        R0 = compute_R(e1, bound_type)
        D0 = R0 - 1.0  # correction at ω = 0
        
        Bo = B_omega_lin(e1) if e1 > 0 else 1e-10
        for j, omg in enumerate(omega_arr):
            # Vorticity modification (VN-01b): δΔ/Δ ~ 3e-10 × (ω/B_ω)²
            vort_factor = 1.0 + 3e-10 * (omg / Bo)**2 if Bo > 0 else 1.0
            Delta[j, i] = D0 * vort_factor
    
    return Delta

# Scenarios
scenarios = OrderedDict([
    ("S1",  {"eps1": 1.233e-3, "label": "S1"}),
    ("S2",  {"eps1": 1.476e-3, "label": "S2"}),
    ("S2b", {"eps1": 2.096e-3, "label": "S2b"}),
    ("S2c", {"eps1": 2.586e-3, "label": "S2c"}),
    ("S3",  {"eps1": 3.296e-3, "label": "S3"}),
])

# Colors
C_BLUE   = "#0072B2"
C_ORANGE = "#E69F00"
C_RED    = "#D55E00"
C_PURPLE = "#CC79A7"
C_GREEN  = "#009E73"
C_CYAN   = "#56B4E9"
C_BLACK  = "#000000"
C_GREY   = "#888888"
C_YELLOW = "#F0E442"
SC_COL = {"S1": C_BLUE, "S2": C_ORANGE, "S2b": C_YELLOW,
          "S2c": C_PURPLE, "S3": C_RED}

omega_T_saadeh = 5.0e-11 / 3.0
omega_T_MES_S3 = B_omega_lin(3.296e-3)

def set_style():
    plt.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 300,
        "font.size": 12, "axes.titlesize": 16, "axes.labelsize": 14,
        "xtick.labelsize": 11, "ytick.labelsize": 11,
        "legend.fontsize": 10, "legend.framealpha": 0.92,
        "axes.linewidth": 1.1, "lines.linewidth": 2.0,
        "axes.grid": False,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "mathtext.fontset": "cm",
    })


# =====================================================================
#  Grids
# =====================================================================
Ne = 150
No = 120
e1_arr = np.linspace(1e-4, 4e-3, Ne)
# Log-spaced ω/Θ from Saadeh to MES
omega_arr = np.logspace(-11, -2.3, No)  # 10⁻¹¹ to ~5×10⁻³


# =====================================================================
#  Panel helper
# =====================================================================
def heatmap_panel(ax, Delta, title, cmap, label_letter):
    """Common heatmap rendering."""
    ax.set_title(f"({label_letter}) {title}", fontsize=14, pad=10)
    
    # Use δΣ²/Σ² = 2Δ (approximate) in percent
    dSig2_pct = 2.0 * Delta * 100.0  # percent
    dSig2_pct = np.clip(dSig2_pct, 1e-5, None)
    
    E1, OMG = np.meshgrid(e1_arr * 1e3, omega_arr)
    
    pcm = ax.pcolormesh(E1, OMG, dSig2_pct,
                        cmap=cmap, norm=LogNorm(vmin=0.001, vmax=5.0),
                        shading='auto', rasterized=True)
    
    # 1% contour
    cs = ax.contour(E1, OMG, dSig2_pct, levels=[1.0],
                    colors='white', linewidths=2.5, linestyles='-')
    ax.clabel(cs, fmt='1%%', fontsize=10, colors='white')
    
    # 0.1% contour
    cs2 = ax.contour(E1, OMG, dSig2_pct, levels=[0.1],
                     colors='white', linewidths=1.5, linestyles='--')
    ax.clabel(cs2, fmt='0.1%%', fontsize=9, colors='white')
    
    # Saadeh bound horizontal
    ax.axhline(omega_T_saadeh, color=C_GREEN, ls='--', lw=1.5, alpha=0.9)
    ax.text(0.15, omega_T_saadeh * 3, "Saadeh+2016",
            fontsize=8, color=C_GREEN, fontweight='bold')
    
    # Scenario markers
    for sname, sc in scenarios.items():
        e1 = sc['eps1']
        Bo = B_omega_lin(e1)
        col = SC_COL[sname]
        # Physical point at (ε₁, ω = 0) — but log scale, so use Saadeh
        ax.plot(e1 * 1e3, omega_T_saadeh, 'o', color=col, ms=7, zorder=10,
                markeredgecolor='white', markeredgewidth=0.8)
    
    ax.set_yscale('log')
    ax.set_xlabel(r"$\varepsilon_1$ ($\times 10^{-3}$)", fontsize=14)
    ax.set_ylabel(r"$|\omega|/\Theta$", fontsize=14)
    ax.set_xlim(e1_arr[0]*1e3, e1_arr[-1]*1e3)
    ax.set_ylim(omega_arr[0], omega_arr[-1])
    
    return pcm


# =====================================================================
#  Panels (a,b,c): Δ_σ, Δ_ω, Δ_u̇ heatmaps
# =====================================================================
def main():
    set_style()
    
    print("  Computing correction grids...")
    Delta_sig = build_correction_grid(e1_arr, omega_arr, 'sigma')
    Delta_omg = build_correction_grid(e1_arr, omega_arr, 'omega')
    Delta_acc = build_correction_grid(e1_arr, omega_arr, 'accel')
    print("  Done.")
    
    fig = plt.figure(figsize=(18, 22))
    fig.suptitle(
        r"Nonlinear Corrections $\Delta_X(\varepsilon_1,\,|\omega|/\Theta)$"
        r" — Vorticity Irrelevance",
        fontsize=20, fontweight='bold', y=0.985)
    
    # --- (a) Δ_σ ---
    ax1 = fig.add_subplot(3, 2, 1)
    pcm1 = heatmap_panel(ax1, Delta_sig,
                         r"$\delta\Sigma^2_\sigma/\Sigma^2_\sigma$  (shear bound)",
                         'YlOrRd', 'a')
    plt.colorbar(pcm1, ax=ax1, label=r"$\delta\Sigma^2/\Sigma^2$ (%)",
                 shrink=0.85, pad=0.02)
    
    # --- (b) Δ_ω ---
    ax2 = fig.add_subplot(3, 2, 2)
    pcm2 = heatmap_panel(ax2, Delta_omg,
                         r"$\delta W^2_\omega/W^2_\omega$  (vorticity bound)",
                         'YlGnBu', 'b')
    plt.colorbar(pcm2, ax=ax2, label=r"$\delta W^2/W^2$ (%)",
                 shrink=0.85, pad=0.02)
    
    # --- (c) Δ_u̇ ---
    ax3 = fig.add_subplot(3, 2, 3)
    pcm3 = heatmap_panel(ax3, Delta_acc,
                         r"$\delta\mathcal{A}^2_{\dot u}/\mathcal{A}^2_{\dot u}$"
                         r"  (acceleration bound)",
                         'PuBuGn', 'c')
    plt.colorbar(pcm3, ax=ax3, label=r"$\delta\mathcal{A}^2/\mathcal{A}^2$ (%)",
                 shrink=0.85, pad=0.02)
    
    # --- (d) 1% validity boundary + scenarios ---
    ax4 = fig.add_subplot(3, 2, 4)
    ax4.set_title(r"(d) $1\%$ Validity Boundary + Scenarios", fontsize=14, pad=10)
    
    dSig2_sig = 2.0 * Delta_sig * 100.0
    E1, OMG = np.meshgrid(e1_arr * 1e3, omega_arr)
    
    # Fill: green = valid (<1%), red = correction needed (>1%)
    ax4.contourf(E1, OMG, dSig2_sig, levels=[0, 1.0, 100],
                 colors=[C_GREEN, C_RED], alpha=0.15)
    ax4.contour(E1, OMG, dSig2_sig, levels=[1.0],
                colors=[C_BLACK], linewidths=3.0)
    ax4.contour(E1, OMG, dSig2_sig, levels=[0.1],
                colors=[C_GREY], linewidths=1.5, linestyles='--')
    
    # 1% threshold label
    # Find ε₁ at which 1% is crossed (from VN-04: ε₁ ~ 2.12e-3)
    ax4.text(2.25, 1e-5, "1% boundary",
             fontsize=12, color=C_BLACK, fontweight='bold',
             rotation=90, ha='center', va='center')
    ax4.text(1.0, 1e-5, r"$<1\%$" + "\n(linearised\nvalid)",
             fontsize=11, color=C_GREEN, fontweight='bold',
             ha='center', va='center')
    ax4.text(3.5, 1e-5, r"$>1\%$" + "\n(correction\nneeded)",
             fontsize=11, color=C_RED, fontweight='bold',
             ha='center', va='center')
    
    # Saadeh horizontal
    ax4.axhline(omega_T_saadeh, color=C_GREEN, ls='--', lw=1.8, alpha=0.9)
    
    # Scenario markers with labels
    for sname, sc in scenarios.items():
        e1 = sc['eps1']
        col = SC_COL[sname]
        # Vertical line at each scenario
        ax4.axvline(e1 * 1e3, color=col, ls=':', lw=1.0, alpha=0.5)
        ax4.plot(e1 * 1e3, omega_T_saadeh, 'o', color=col, ms=9, zorder=10,
                 markeredgecolor='white', markeredgewidth=1.2)
        ax4.text(e1 * 1e3, omega_T_saadeh * 0.15, sname,
                 fontsize=10, color=col, fontweight='bold', ha='center')
    
    ax4.set_yscale('log')
    ax4.set_xlabel(r"$\varepsilon_1$ ($\times 10^{-3}$)", fontsize=14)
    ax4.set_ylabel(r"$|\omega|/\Theta$", fontsize=14)
    ax4.set_xlim(e1_arr[0]*1e3, e1_arr[-1]*1e3)
    ax4.set_ylim(omega_arr[0], omega_arr[-1])
    
    # --- (e) ε₁ cross-section at different ω/Θ values ---
    ax5 = fig.add_subplot(3, 2, 5)
    ax5.set_title(r"(e) $\varepsilon_1$ Cross-Section:  $\delta\Sigma^2/\Sigma^2$"
                  r" at Fixed $|\omega|/\Theta$", fontsize=13, pad=10)
    
    # Three ω values: 0, Saadeh, MES-level
    omega_vals = [
        (1e-15, r"$\omega = 0$", C_BLACK, '-', 2.5),
        (omega_T_saadeh, r"$\omega = \omega_{\rm Saadeh}$", C_GREEN, '--', 2.0),
        (1e-5, r"$\omega/\Theta = 10^{-5}$", C_CYAN, '-.', 1.8),
        (1e-3, r"$\omega/\Theta = 10^{-3}$ (MES-level)", C_PURPLE, ':', 1.8),
    ]
    
    for omg_val, lab, col, ls, lw in omega_vals:
        dSig2 = []
        for e1 in e1_arr:
            R = compute_R(e1, 'sigma')
            D = R - 1.0
            Bo = B_omega_lin(e1) if e1 > 0 else 1e-10
            vf = 1.0 + 3e-10 * (omg_val / Bo)**2 if Bo > 0 else 1.0
            dSig2.append(2.0 * D * vf * 100.0)
        ax5.plot(e1_arr * 1e3, dSig2, ls=ls, color=col, lw=lw, label=lab)
    
    # 1% threshold
    ax5.axhline(1.0, color=C_GREY, ls=':', lw=1.0, alpha=0.5)
    ax5.text(0.5, 1.05, "1% threshold", fontsize=9, color=C_GREY)
    
    # Scenario markers
    for sname, sc in scenarios.items():
        e1 = sc['eps1']
        R = compute_R(e1, 'sigma')
        dS2 = 2.0 * (R - 1.) * 100.
        col = SC_COL[sname]
        ax5.plot(e1 * 1e3, dS2, 'o', color=col, ms=8, zorder=10,
                 markeredgecolor='white', markeredgewidth=1.0)
        ax5.text(e1 * 1e3 + 0.05, dS2 + 0.08, sname, fontsize=9,
                 color=col, fontweight='bold')
    
    ax5.set_xlabel(r"$\varepsilon_1$ ($\times 10^{-3}$)", fontsize=14)
    ax5.set_ylabel(r"$\delta\Sigma^2/\Sigma^2$ (%)", fontsize=14)
    ax5.set_xlim(0, 4.0)
    ax5.set_ylim(0, 3.5)
    ax5.legend(loc='upper left', fontsize=9, framealpha=0.88)
    ax5.grid(True, alpha=0.2)
    
    # --- (f) ω/Θ cross-section at fixed ε₁ = S3 ---
    ax6 = fig.add_subplot(3, 2, 6)
    ax6.set_title(r"(f) $|\omega|/\Theta$ Cross-Section at $\varepsilon_1 = \varepsilon_1^{\rm S3}$",
                  fontsize=13, pad=10)
    
    e1_S3 = 3.296e-3
    R_S3 = compute_R(e1_S3, 'sigma')
    D_S3 = R_S3 - 1.0
    Bo_S3 = B_omega_lin(e1_S3)
    
    omega_fine = np.logspace(-12, -2, 500)
    dSig2_omg = []
    for omg in omega_fine:
        vf = 1.0 + 3e-10 * (omg / Bo_S3)**2
        dSig2_omg.append(2.0 * D_S3 * vf * 100.0)
    dSig2_omg = np.array(dSig2_omg)
    
    ax6.semilogx(omega_fine, dSig2_omg, '-', color=C_RED, lw=2.5,
                 label=r"$\delta\Sigma^2_\sigma/\Sigma^2_\sigma$ (S3)")
    
    # Show that the curve is FLAT
    ax6.axhline(2.0 * D_S3 * 100., color=C_GREY, ls=':', lw=1.0, alpha=0.5)
    
    # Mark Saadeh
    ax6.axvline(omega_T_saadeh, color=C_GREEN, ls='--', lw=1.5)
    ax6.text(omega_T_saadeh * 5, 1.71, "Saadeh",
             fontsize=9, color=C_GREEN, ha='left')
    
    # Mark MES level
    ax6.axvline(Bo_S3, color=C_PURPLE, ls='--', lw=1.5)
    ax6.text(Bo_S3 * 0.2, 1.71, "MES",
             fontsize=9, color=C_PURPLE, ha='right')
    
    # Flat annotation
    dS_min = dSig2_omg[0]
    dS_max = dSig2_omg[-1]
    rel_change = (dS_max - dS_min) / dS_min
    
    ax6.text(1e-7, 1.82,
             f"FLAT: relative change = {rel_change:.1e}",
             fontsize=12, color=C_BLACK, fontweight='bold',
             ha='center',
             bbox=dict(fc='white', ec=C_BLACK, alpha=0.9, pad=4))
    
    ax6.set_xlabel(r"$|\omega|/\Theta$", fontsize=14)
    ax6.set_ylabel(r"$\delta\Sigma^2/\Sigma^2$ (%)", fontsize=14)
    ax6.set_xlim(1e-12, 1e-2)
    ax6.set_ylim(1.70, 1.85)
    ax6.legend(loc='lower right', fontsize=10, framealpha=0.88)
    ax6.grid(True, alpha=0.2)
    
    # === Finalise ===
    fig.tight_layout(rect=[0, 0, 1, 0.975], h_pad=3.5, w_pad=3.0)
    
    outpath = "fig_nonlinear_heatmap_vorticity_accel.png"
    fig.savefig(outpath, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  Saved: {outpath}")
    
    import shutil
    shutil.copy(outpath, "/mnt/user-data/outputs/fig_nonlinear_heatmap_vorticity_accel.png")
    print("  Copied to /mnt/user-data/outputs/")


if __name__ == "__main__":
    main()
