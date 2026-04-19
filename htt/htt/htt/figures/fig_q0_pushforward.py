#!/usr/bin/env python3
"""
fig_q0_pushforward.py — q₀ apparent deceleration pushforward figure
=====================================================================
Panel A: q₀_apparent pushforward PDF for FLRW_tilt at d=40 Mpc
Panel B: q₀_apparent vs scenario (S0–S3) with 95% HPD error bars
Panel C: Δq_tilt vs β at d=40 Mpc with posterior-mapped band

7×3 inch (wide format). 300 DPI. Okabe-Ito palette.

STATUS: EXPLORATORY — Appendix-grade output only (HB-4).
This figure must NOT appear in core results (Ch. 2-7).
Target: appendix_J_bridge_quarantine.tex
"""
import sys, os
import numpy as np

sys.path.insert(0, '/mnt/project')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

from plot_style import apply_style, save_fig, COLS
from evidence_models_R03a import FLRW_tilt
from departure_posteriors import DeparturePosterior
from tilted_flrw import Delta_q
from ssot import C

apply_style()
OUT = '/mnt/user-data/outputs'

# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════
D_MPC = 40.0
q0_true = 0.5 * C.Omega_m - (1.0 - C.Omega_m)   # -0.5271
H0 = C.h * 100.0
c_kms = 299792.458
lambda_H = c_kms / H0   # ≈ 4452 Mpc

SCENARIOS = {
    'S0':  {'beta': 0.0,       'sigma_beta': 0.0,       'label': 'S0\n(FLRW)'},
    'S1':  {'beta': 0.0,       'sigma_beta': 0.0,       'label': 'S1\n(kin.)'},
    'S2a': {'beta': 1.362e-3,  'sigma_beta': 0.28e-3,   'label': 'S2a\n(CatWISE)'},
    'S2c': {'beta': 3.042e-3,  'sigma_beta': 0.55e-3,   'label': 'S2c\n(radio)'},
    'S3':  {'beta': 1.334e-3,  'sigma_beta': 0.267e-3,  'label': 'S3\n(CF4)'},
}

# ═══════════════════════════════════════════════════════════════
#  STEP 1: FLRW_tilt posterior β samples
# ═══════════════════════════════════════════════════════════════
print("Getting FLRW_tilt posterior...")

ft = FLRW_tilt(channels='abcdefh')
r = ft.log_evidence_quadrature(n_points=50000)
cum = np.cumsum(r['posterior']); cum /= cum[-1]
rng = np.random.default_rng(7)
idx = np.clip(np.searchsorted(cum, rng.uniform(0, 1, 5000)), 0, len(r['betas'])-1)
beta_post = r['betas'][idx]

# Compute q₀ pushforward
dp = DeparturePosterior('FLRW_tilt', beta_post.reshape(-1, 1), param_names=['beta'])
dp.full_report(d_Mpc=D_MPC)

q0_app = dp.q0_apparent
Dq_tilt = dp.Dq_tilt

q0_med = np.median(q0_app)
q0_lo, q0_hi = np.percentile(q0_app, [2.5, 97.5])
Dq_med = np.median(Dq_tilt)

print(f"  q0_true = {q0_true:.4f}")
print(f"  q0_app median = {q0_med:.2f}, 95% HPD = [{q0_lo:.2f}, {q0_hi:.2f}]")
print(f"  Dq_tilt median = {Dq_med:.2f}")


# ═══════════════════════════════════════════════════════════════
#  STEP 2: Scenario q₀ pushforward (MC propagation)
# ═══════════════════════════════════════════════════════════════
print("Computing scenario q₀ pushforwards...")

N_MC = 10000
rng_mc = np.random.default_rng(42)
scenario_q0 = {}

for sn, sc in SCENARIOS.items():
    if sc['beta'] > 0:
        beta_samp = np.clip(rng_mc.normal(sc['beta'], sc['sigma_beta'], N_MC), 0, None)
        Dq_samp = np.array([Delta_q(b, D_MPC) for b in beta_samp])
    else:
        beta_samp = np.zeros(N_MC)
        Dq_samp = np.zeros(N_MC)
    q0_samp = q0_true + Dq_samp
    scenario_q0[sn] = {
        'median': float(np.median(q0_samp)),
        'lo95': float(np.percentile(q0_samp, 2.5)),
        'hi95': float(np.percentile(q0_samp, 97.5)),
        'Dq_median': float(np.median(Dq_samp)),
        'beta': sc['beta'],
    }
    print(f"  {sn}: q0_app = {scenario_q0[sn]['median']:.2f} "
          f"[{scenario_q0[sn]['lo95']:.2f}, {scenario_q0[sn]['hi95']:.2f}]")


# ═══════════════════════════════════════════════════════════════
#  FIGURE: 1×3 wide layout
# ═══════════════════════════════════════════════════════════════
fig, (ax_A, ax_B, ax_C) = plt.subplots(1, 3, figsize=(7.0, 3.0))


# ─── Panel A: q₀ pushforward PDF ─────────────────────────────
print("Panel A: q0 pushforward PDF...")

kde = gaussian_kde(q0_app, bw_method=0.2)
qg = np.linspace(np.percentile(q0_app, 0.5), np.percentile(q0_app, 99.5), 300)
pdf_vals = kde(qg)

ax_A.plot(qg, pdf_vals, color=COLS['blue'], lw=1.5)
ax_A.fill_between(qg, pdf_vals, alpha=0.12, color=COLS['blue'])

# 95% HPD shading
mask_95 = (qg >= q0_lo) & (qg <= q0_hi)
ax_A.fill_between(qg[mask_95], pdf_vals[mask_95], alpha=0.25,
                   color=COLS['blue'], label='95% HPD')

# Median line
ax_A.axvline(q0_med, color=COLS['blue'], ls='--', lw=0.8, alpha=0.7)

# q₀_true (FLRW) line
ax_A.axvline(q0_true, color=COLS['red'], ls='-', lw=1.2,
             label=f'$q_{{0,\\rm true}} = {q0_true:.2f}$')

# Annotation
ax_A.annotate(
    r'$\Delta q_{\rm tilt} \gg |q_{0,{\rm true}}|$',
    xy=(q0_true, max(pdf_vals) * 0.3),
    xytext=(q0_med * 0.5, max(pdf_vals) * 0.7),
    fontsize=7.5, color=COLS['red'],
    arrowprops=dict(arrowstyle='->', color=COLS['red'], lw=0.7))

ax_A.set_xlabel(r'$\hat{q}_0(d=40\;\mathrm{Mpc})$')
ax_A.set_ylabel('Posterior density')
ax_A.legend(fontsize=7, loc='upper right', framealpha=0.9)
ax_A.text(0.04, 0.95, '(a)', transform=ax_A.transAxes,
          fontsize=11, fontweight='bold', va='top')


# ─── Panel B: q₀ vs scenario ─────────────────────────────────
print("Panel B: q0 vs scenario...")

sn_names = list(SCENARIOS.keys())
x_pos = np.arange(len(sn_names))
medians = [scenario_q0[sn]['median'] for sn in sn_names]
lo95 = [scenario_q0[sn]['lo95'] for sn in sn_names]
hi95 = [scenario_q0[sn]['hi95'] for sn in sn_names]
yerr_lo = [m - l for m, l in zip(medians, lo95)]
yerr_hi = [h - m for m, h in zip(medians, hi95)]

# Color by tilt presence
colors = [COLS['gray'] if SCENARIOS[sn]['beta'] == 0 else COLS['blue']
          for sn in sn_names]

# Error bars only (no markers)
ax_B.errorbar(x_pos, medians, yerr=[yerr_lo, yerr_hi],
              fmt='none', capsize=3, capthick=1.0,
              ecolor=COLS['blue'], zorder=4)

# Individual coloured markers
for i, (xp, med, col) in enumerate(zip(x_pos, medians, colors)):
    ax_B.plot(xp, med, 'o', ms=6, color=col, markeredgecolor=COLS['black'],
              markeredgewidth=0.5, zorder=6)

# q₀_true reference
ax_B.axhline(q0_true, color=COLS['red'], ls='-', lw=1.0, alpha=0.7,
             label=f'$q_{{0,\\rm true}}$')

# Crossover line at 0
ax_B.axhline(0, color=COLS['gray'], ls=':', lw=0.5, alpha=0.5)

ax_B.set_xticks(x_pos)
ax_B.set_xticklabels([SCENARIOS[sn]['label'] for sn in sn_names],
                      fontsize=7.5)
ax_B.set_ylabel(r'$\hat{q}_0(d=40\;\mathrm{Mpc})$')
ax_B.legend(fontsize=7, loc='upper left', framealpha=0.9)
ax_B.text(0.04, 0.95, '(b)', transform=ax_B.transAxes,
          fontsize=11, fontweight='bold', va='top')

# Log-like y-axis to accommodate the range
ax_B.set_yscale('symlog', linthresh=1.0)
ax_B.set_ylim(-2, 600)


# ─── Panel C: Δq vs β at d=40 Mpc ───────────────────────────
print("Panel C: Δq vs β at d=40 Mpc...")

beta_grid = np.linspace(1e-5, 3e-3, 300)
Dq_grid = np.array([Delta_q(b, D_MPC) for b in beta_grid])

ax_C.plot(beta_grid * 1e3, Dq_grid, color=COLS['black'], lw=1.2,
          label=r'$\Delta q = \frac{\beta}{9}\left(\frac{\lambda_H}{d}\right)^3$')

# Shade the posterior β range
beta_lo, beta_hi = np.percentile(beta_post, [2.5, 97.5])
beta_med_val = np.median(beta_post)

mask_post = (beta_grid >= beta_lo) & (beta_grid <= beta_hi)
ax_C.fill_between(beta_grid[mask_post] * 1e3, Dq_grid[mask_post],
                   alpha=0.2, color=COLS['blue'],
                   label=f'Posterior 95% CI')

# Mark median
Dq_at_med = Delta_q(beta_med_val, D_MPC)
ax_C.plot(beta_med_val * 1e3, Dq_at_med, 'o', ms=5,
          color=COLS['blue'], markeredgecolor='k', markeredgewidth=0.5,
          zorder=5)
ax_C.annotate(
    f'$\\beta_{{\\rm med}}$\n$\\Delta q = {Dq_at_med:.0f}$',
    xy=(beta_med_val * 1e3, Dq_at_med),
    xytext=(beta_med_val * 1e3 + 0.4, Dq_at_med * 0.55),
    fontsize=7, color=COLS['blue'],
    arrowprops=dict(arrowstyle='->', color=COLS['blue'], lw=0.6))

# |q₀_true| reference line
ax_C.axhline(abs(q0_true), color=COLS['red'], ls=':', lw=0.8, alpha=0.7)
ax_C.text(2.7, abs(q0_true) * 1.3, r'$|q_{0,{\rm true}}|$',
          fontsize=7.5, color=COLS['red'], ha='right')

# CF4 β marker
ax_C.axvline(1.334, color=COLS['orange'], ls='--', lw=0.7, alpha=0.6)
ax_C.text(1.38, max(Dq_grid) * 0.85, r'$\beta_{\rm CF4}$',
          fontsize=7.5, color=COLS['orange'])

ax_C.set_xlabel(r'$\beta \;\;(\times 10^{-3})$')
ax_C.set_ylabel(r'$\Delta q_{\rm tilt}(d=40\;\mathrm{Mpc})$')
ax_C.legend(fontsize=7, loc='upper left', framealpha=0.9)
ax_C.set_xlim(0, 3)
ax_C.text(0.04, 0.95, '(c)', transform=ax_C.transAxes,
          fontsize=11, fontweight='bold', va='top')


# ═══════════════════════════════════════════════════════════════
fig.tight_layout(w_pad=2.0)
save_fig(fig, 'fig_q0_pushforward')
print("Saved fig_q0_pushforward.pdf + .png")
