#!/usr/bin/env python3
"""make_preliminary_figures.py — unified preliminary figure generator.

Companion to docs/BASS_PY_FAST_TRACK_2026-04-18.md. Produces the
preliminary figure bundle described in §4-6 of the plan.

Usage
-----
    # From repo root:
    venv/bin/python scripts/make_preliminary_figures.py --tier A
    venv/bin/python scripts/make_preliminary_figures.py --tier A --only A1
    venv/bin/python scripts/make_preliminary_figures.py --list

Phase A (this file, Tier A bass_py-only figures):
    A1  fig_route_b_sentinel      (bass.spectrum.cl_assembly, Route B M-M)
    A2  fig_MES_three_bounds      (htt.core.bounds, pure analytic)
    A3  fig_colin_beta            (htt.core.tilted_flrw.beta_from_colin)
    A8a fig_sigma_omega_contour   (htt.core.bounds, pure analytic)
    A8b fig_sigma_accel_contour   (htt.core.bounds, pure analytic)

Later phases will add:
    A4/A5/A6 evidence decomposition, departure summary, type-by-type
             (needs dynesty pipeline — Phase C/D migration from legacy)
    A7       fig_visibility_g (bass.recombination W8-02)
    B1/B2/B3 CAMB V-gate + fig_d2_sigma2_scaling (Phase E)
    C1/C2/C3 minimal 3-template synthetic (Phase E)

Output location: figures/preliminary/TIER_{A,B,C}/  (PNG+PDF, 300 dpi).
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from figure_env import REPO_ROOT, configure_repo_paths  # noqa: E402

OUT_A = REPO_ROOT / 'figures' / 'preliminary' / 'TIER_A'

# Ensure the active `htt/` tree is on path for `bass.*` / `htt.*` imports.
configure_repo_paths()

from htt.core.plot_style import apply_style, COLS, FIG_1COL, FIG_2COL  # noqa: E402


# ════════════════════════════════════════════════════════════════════
# Shared helpers
# ════════════════════════════════════════════════════════════════════

def _save(fig, name: str, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(outdir / f'{name}.{ext}', dpi=300,
                    bbox_inches='tight', pad_inches=0.04)
    plt.close(fig)
    print(f'  [ok] {outdir.name}/{name}.{{png,pdf}}')


def _write_caption(name: str, outdir: Path, text: str) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f'{name}.caption.txt').write_text(text.strip() + '\n')


# ════════════════════════════════════════════════════════════════════
# A.1 — Route B M-M sentinel overlay
# ════════════════════════════════════════════════════════════════════

def fig_A1_route_b_sentinel(outdir: Path = OUT_A) -> None:
    """D_2 Route B Michaelis-Menten curve over Σ² ∈ [1e-12, 1e-4].

    Overlay the production sentinel at Σ² = 1e-8, D_2 = 0.1741 μK².
    Data: bass_py/bass/spectrum/cl_assembly.py (W10-01).
    """
    from bass.spectrum.cl_assembly import (
        ROUTE_B_C1, ROUTE_B_C2, ROUTE_B_D2_AT_SIGMA2_1EM8, route_b_d2_lookup,
    )

    sigma2 = np.geomspace(1.0e-12, 1.0e-4, 400)
    d2 = route_b_d2_lookup(sigma2)

    # Asymptote for reference: D_2 → C_1/C_2 as Σ² → ∞
    d2_sat = ROUTE_B_C1 / ROUTE_B_C2

    # Small-Σ² linear regime D_2 ≈ C_1 Σ²
    sigma2_lin = np.geomspace(1.0e-12, 3.0e-8, 60)
    d2_lin = ROUTE_B_C1 * sigma2_lin

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    ax.loglog(sigma2, d2, color=COLS['blue'], lw=1.9,
              label=r'Route B M-M: $D_2 = C_1 \Sigma^2 / (1 + C_2 \Sigma^2)$')
    ax.loglog(sigma2_lin, d2_lin, color=COLS['gray'], ls='--', lw=1.1,
              label=r'linear regime $D_2 \simeq C_1 \Sigma^2$')
    ax.axhline(d2_sat, color=COLS['orange'], ls=':', lw=1.0,
               label=rf'saturation $D_2 \to C_1/C_2 = {d2_sat:.2f}\;\mu\mathrm{{K}}^2$')

    sentinel_s2 = 1.0e-8
    sentinel_d2 = ROUTE_B_D2_AT_SIGMA2_1EM8
    ax.plot(sentinel_s2, sentinel_d2, marker='o', ms=9, color=COLS['red'],
            mec='k', mew=0.4, zorder=5,
            label=(rf'sentinel: $\Sigma^2=10^{{-8}},\;D_2={sentinel_d2:.4f}\;'
                   r'\mu\mathrm{K}^2$'))
    ax.annotate(rf'$D_2 = {sentinel_d2:.4f}\;\mu\mathrm{{K}}^2$',
                xy=(sentinel_s2, sentinel_d2),
                xytext=(2.2e-10, 3.0),
                fontsize=8.5, color=COLS['red'],
                arrowprops=dict(arrowstyle='->', color=COLS['red'], lw=0.7))

    ax.set_xlabel(r'Shear amplitude $\Sigma^2$')
    ax.set_ylabel(r'$D_2^{TT}\;[\mu\mathrm{K}^2]$')
    ax.set_xlim(1.0e-12, 1.0e-4)
    ax.set_ylim(1.0e-5, 1.0e2)
    ax.grid(True, which='major', alpha=0.25)
    ax.grid(True, which='minor', alpha=0.08)
    ax.legend(fontsize=8.0, loc='upper left', framealpha=0.9)
    ax.set_title(r'Route B Michaelis-Menten sentinel (bass_py W10-01)',
                 fontsize=10)

    _save(fig, 'fig_route_b_sentinel', outdir)
    _write_caption(
        'fig_route_b_sentinel', outdir,
        f"""
Route B Michaelis-Menten D_2(Σ²) = C_1 Σ² / (1 + C_2 Σ²) over Σ² ∈ [10⁻¹²,
10⁻⁴] with SSOT constants C_1 = {ROUTE_B_C1:.3e}, C_2 = {ROUTE_B_C2:.3e}
(bass_py W10-01; SSOT mirror of bass_rs/d2_convention.rs). The production
sentinel Σ² = 10⁻⁸ → D_2 = {sentinel_d2:.4f} μK² is marked; linear
(D_2 ≈ C_1 Σ²) and saturation (D_2 → C_1/C_2 = {d2_sat:.2f} μK²) regimes
are shown.
""")


# ════════════════════════════════════════════════════════════════════
# A.2 — MES three-bound hierarchy  (pure analytic, htt.core.bounds)
# ════════════════════════════════════════════════════════════════════

def fig_A2_MES_three_bounds(outdir: Path = OUT_A) -> None:
    """B_σ > B_ω > B_u̇ as functions of ε₁, with S1/S2a/S2c markers."""
    from htt.core.bounds import B_sigma, B_omega, B_accel

    e1 = np.logspace(-5, -1.5, 400)
    Bs = np.array([B_sigma(e) for e in e1])
    Bw = np.array([B_omega(e) for e in e1])
    Ba = np.array([B_accel(e) for e in e1])

    scenarios = [
        ('S1',  1.2336e-3, 'o', COLS['blue']),
        ('S2a', 1.476e-3,  's', COLS['orange']),
        ('S2c', 3.296e-3,  '^', COLS['red']),
    ]

    fig, ax = plt.subplots(figsize=(7.0, 3.7))
    ax.plot(e1, Bs, color=COLS['blue'],   lw=1.8, ls='-',
            label=r'$B_\sigma$  (shear)')
    ax.plot(e1, Bw, color=COLS['orange'], lw=1.8, ls='--',
            label=r'$B_\omega$  (vorticity)')
    ax.plot(e1, Ba, color=COLS['red'],    lw=1.5, ls=(0, (4, 2, 1, 2)),
            label=r'$B_{\dot{u}}$  (acceleration)')

    for name, e, marker, col in scenarios:
        bs = B_sigma(e)
        ax.plot(e, bs, marker=marker, color=col, ms=7,
                mec='k', mew=0.35, zorder=5)
        ax.annotate(name, (e, bs),
                    textcoords='offset points', xytext=(7, 6),
                    fontsize=8, color=col, fontweight='medium')

    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel(r'Dipole asymmetry $\varepsilon_1$')
    ax.set_ylabel(r'MES bound')
    ax.set_xlim(1e-5, 3e-2)
    ax.grid(True, which='major', alpha=0.25)
    ax.legend(fontsize=9.0, loc='lower right', framealpha=0.9)
    ax.set_title(r'MES three-bound hierarchy', fontsize=10)

    _save(fig, 'fig_MES_three_bounds', outdir)
    _write_caption(
        'fig_MES_three_bounds', outdir, """
The Maartens-Ellis-Stoeger kinematic bounds B_σ (shear), B_ω (vorticity),
B_{u̇} (acceleration) as functions of the dipole asymmetry ε₁. Scenario
markers: S1 (ε₁ = 1.234×10⁻³), S2a (1.476×10⁻³, CatWISE), S2c
(3.296×10⁻³). The hierarchy B_σ > B_ω > B_{u̇} holds uniformly on the
ε₁-dominated branch.
""")


# ════════════════════════════════════════════════════════════════════
# A.3 — Colin β(z) dipolar-q to tilt rapidity translation
# ════════════════════════════════════════════════════════════════════

def fig_A3_colin_beta(outdir: Path = OUT_A) -> None:
    """β_SNe(z) = 9 |q_d| z³ exp(-z/S) with β_CF4 band and ratio axis."""
    from htt.core.tilted_flrw import beta_from_colin
    from scipy.optimize import brentq

    z = np.linspace(0.005, 0.22, 500)
    beta = np.array([beta_from_colin(zi) for zi in z])

    beta_cf4 = 1.334e-3
    sigma_cf4 = 0.267e-3
    ratio = beta / beta_cf4

    z_tab = np.array([0.02, 0.03, 0.05, 0.08, 0.10, 0.15])
    b_tab = np.array([beta_from_colin(zi) for zi in z_tab])
    i_pk = int(np.argmax(beta))
    z_peak, b_peak = z[i_pk], beta[i_pk]

    try:
        z_cross = brentq(lambda zi: beta_from_colin(zi) / beta_cf4 - 1.0,
                         0.03, 0.07)
    except ValueError:
        z_cross = None

    fig, ax1 = plt.subplots(figsize=(7.0, 3.7))
    ax1.axhspan((beta_cf4 - sigma_cf4) * 1e3, (beta_cf4 + sigma_cf4) * 1e3,
                color=COLS['yellow'], alpha=0.25, zorder=0,
                label=r'$\beta_{\rm CF4}\pm1\sigma$')
    ax1.axhline(beta_cf4 * 1e3, color=COLS['orange'], lw=0.6, ls=':', alpha=0.6)

    ax1.plot(z, beta * 1e3, color=COLS['blue'], lw=1.8, zorder=3,
             label=r'$\beta_{\rm SNe}(z) = 9\,|q_d|\,z^3\,e^{-z/S}$')
    ax1.plot(z_tab, b_tab * 1e3, 'o', color=COLS['blue'], ms=5,
             mec='k', mew=0.3, zorder=5)
    ax1.plot(z_peak, b_peak * 1e3, '*', color=COLS['red'], ms=11, mec='k',
             mew=0.4, zorder=6,
             label=rf'peak: $z={z_peak:.3f},\;\beta={b_peak*1e3:.2f}\times 10^{{-3}}$')

    if z_cross is not None:
        ax1.axvline(z_cross, color=COLS['gray'], ls='--', lw=0.8, alpha=0.8)
        ax1.text(z_cross + 0.003, 0.1,
                 rf'crossover $z={z_cross:.3f}$',
                 fontsize=8, color=COLS['gray'], rotation=90, va='bottom')

    ax1.set_xlabel(r'Redshift $z$')
    ax1.set_ylabel(r'$\beta_{\rm SNe}(z)\;[\times 10^{-3}]$')
    ax1.set_xlim(0, 0.22)
    ax1.grid(True, alpha=0.25)
    ax1.legend(fontsize=8.5, loc='upper right', framealpha=0.9)
    ax1.set_title(r'Colin et al.\ 2025 dipolar-$q$ $\to$ tilt rapidity',
                  fontsize=10)

    ax2 = ax1.twinx()
    ax2.plot(z, ratio, color=COLS['green'], lw=0.8, alpha=0.6)
    ax2.set_ylabel(r'$\beta_{\rm SNe}/\beta_{\rm CF4}$',
                   color=COLS['green'], fontsize=9)
    ax2.tick_params(axis='y', labelcolor=COLS['green'], labelsize=8)

    _save(fig, 'fig_colin_beta', outdir)
    _write_caption(
        'fig_colin_beta', outdir, """
Translation of Colin et al. 2025 dipolar deceleration q_d(z) into tilt
rapidity β(z) = 9 |q_d| z³ exp(-z/S). The CF4 bulk-flow amplitude
β_CF4 = (1.334 ± 0.267)×10⁻³ band is shown in yellow. The β_SNe(z) curve
peaks near z ≈ 0.06 and crosses β_CF4 around z ≈ 0.04; the amplitude
agreement at CF4 depth supports the tilt interpretation of the
low-redshift SNe dipole.
""")


# ════════════════════════════════════════════════════════════════════
# A.8 — σ-ω and σ-accel contour plots (pure analytic)
# ════════════════════════════════════════════════════════════════════

def _sigma_bound_contour(ax, e1, sigma_max, y_arr, y_label, y_log=True):
    """Shared layout: fill allowed MES region below sigma_max(ε₁) curve."""
    ax.plot(e1, sigma_max, color=COLS['blue'], lw=1.9,
            label=r'$B_\sigma(\varepsilon_1)$ MES bound')
    ax.fill_between(e1, 0, sigma_max, color=COLS['blue'], alpha=0.10,
                    label='MES allowed')
    if y_log:
        ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_xlabel(r'$\varepsilon_1$')
    ax.set_ylabel(y_label)
    ax.grid(True, which='major', alpha=0.25)
    ax.legend(fontsize=8.5, loc='upper left', framealpha=0.9)


def fig_A8a_sigma_omega_contour(outdir: Path = OUT_A) -> None:
    from htt.core.bounds import B_sigma, B_omega
    e1 = np.logspace(-5, -1.5, 300)
    sigma_max = np.array([B_sigma(e) for e in e1])
    omega_max = np.array([B_omega(e) for e in e1])
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    _sigma_bound_contour(ax, e1, sigma_max,
                         omega_max, r'$\sigma, \omega$')
    ax.plot(e1, omega_max, color=COLS['orange'], lw=1.6, ls='--',
            label=r'$B_\omega(\varepsilon_1)$')
    ax.legend(fontsize=8.5, loc='upper left')
    ax.set_title(r'$\sigma$-$\omega$ MES contour', fontsize=10)
    _save(fig, 'fig_sigma_omega_contour', outdir)
    _write_caption(
        'fig_sigma_omega_contour', outdir, """
Shear σ and vorticity ω MES upper bounds as functions of the dipole
asymmetry ε₁. The blue shaded region is the MES-allowed (ε₁, σ) domain;
the dashed orange line is the concurrent ω ceiling B_ω(ε₁). For realistic
ε₁ ∈ [10⁻⁴, 10⁻²] the bounds differ by a factor of about 2.
""")


def fig_A8b_sigma_accel_contour(outdir: Path = OUT_A) -> None:
    from htt.core.bounds import B_sigma, B_accel
    e1 = np.logspace(-5, -1.5, 300)
    sigma_max = np.array([B_sigma(e) for e in e1])
    accel_max = np.array([B_accel(e) for e in e1])
    fig, ax = plt.subplots(figsize=(6.0, 4.0))
    _sigma_bound_contour(ax, e1, sigma_max,
                         accel_max, r'$\sigma, \dot u$')
    ax.plot(e1, accel_max, color=COLS['red'], lw=1.5, ls=(0, (4, 2, 1, 2)),
            label=r'$B_{\dot{u}}(\varepsilon_1)$')
    ax.legend(fontsize=8.5, loc='upper left')
    ax.set_title(r'$\sigma$-$\dot u$ MES contour', fontsize=10)
    _save(fig, 'fig_sigma_accel_contour', outdir)
    _write_caption(
        'fig_sigma_accel_contour', outdir, """
Shear σ and peculiar acceleration u̇ MES upper bounds as functions of
ε₁. The blue shaded region is the MES-allowed (ε₁, σ) domain; the dashed
red line is the concurrent u̇ ceiling B_{u̇}(ε₁). The B_{u̇} curve lies
below B_σ for the ε₁-dominated branch, reflecting the tighter
acceleration constraint from geodesic focusing arguments.
""")


# ════════════════════════════════════════════════════════════════════
# Dispatcher
# ════════════════════════════════════════════════════════════════════

FIG_REGISTRY = {
    'A1':  ('Tier A',  fig_A1_route_b_sentinel),
    'A2':  ('Tier A',  fig_A2_MES_three_bounds),
    'A3':  ('Tier A',  fig_A3_colin_beta),
    'A8a': ('Tier A',  fig_A8a_sigma_omega_contour),
    'A8b': ('Tier A',  fig_A8b_sigma_accel_contour),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--tier', choices=['A', 'B', 'C', 'D', 'all'],
                    default='A', help='which tier to render (default: A)')
    ap.add_argument('--only', default=None,
                    help='only render a specific figure id (e.g. A1)')
    ap.add_argument('--list', action='store_true',
                    help='list available figures and exit')
    args = ap.parse_args()

    if args.list:
        print('Available figures:')
        for fid, (tier, fn) in FIG_REGISTRY.items():
            print(f'  {fid:<5} {tier:<8} {fn.__name__}')
        return 0

    apply_style()
    targets = (
        [args.only] if args.only else
        [fid for fid, (tier, _) in FIG_REGISTRY.items()
         if args.tier == 'all' or tier.endswith(args.tier)]
    )
    if not targets:
        print(f'No figures matched tier={args.tier} only={args.only}')
        return 1

    print(f'Rendering {len(targets)} figures...')
    for fid in targets:
        if fid not in FIG_REGISTRY:
            print(f'  [skip] {fid}: not in registry')
            continue
        _, fn = FIG_REGISTRY[fid]
        print(f'[{fid}] {fn.__name__}')
        fn()
    print('Done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
