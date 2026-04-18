#!/usr/bin/env python3
"""
fig_rho_sweep.py — ρ (CatWISE-Radio correlation) robustness sweep
===================================================================
4-panel figure showing how all key quantities degrade with ρ.
Data from IS-09 robustness_sweeps_integrated.json, sweep A.
"""
import sys, json
import numpy as np

sys.path.insert(0, '/mnt/project')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from plot_style import apply_style, save_fig, COLS

apply_style()

# ─── Load data ────────────────────────────────────────────────
with open('/mnt/user-data/outputs/robustness_sweeps_integrated.json') as f:
    data = json.load(f)

pts = data['sweep_A_rho']
rho = np.array([p['rho'] for p in pts])
lnB = np.array([p['lnB'] for p in pts])
beta = np.array([p['beta_median'] for p in pts])
Q = np.array([p['Q_median'] for p in pts])
Pi_01 = np.array([p['Pi_01'] for p in pts])

# ─── Figure ───────────────────────────────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.5), sharex=True)
ax_A, ax_B = axes[0]
ax_C, ax_D = axes[1]

mkw = dict(marker='o', ms=5, markeredgecolor='k', markeredgewidth=0.4, zorder=5)


# Panel A: ln B vs ρ
ax_A.plot(rho, lnB, '-', color=COLS['blue'], lw=1.3, **mkw)
ax_A.axhline(5, color=COLS['gray'], ls=':', lw=0.6, alpha=0.6)
ax_A.text(0.82, 6.5, 'decisive', fontsize=7.5, color=COLS['gray'])
ax_A.axhline(0, color=COLS['gray'], ls=':', lw=0.6, alpha=0.4)
ax_A.set_ylabel(r'$\ln\mathcal{B}$')
ax_A.set_ylim(-2, 33)
ax_A.text(0.04, 0.93, '(a)', transform=ax_A.transAxes,
          fontsize=11, fontweight='bold', va='top')


# Panel B: β_median vs ρ
ax_B.plot(rho, beta * 1e3, '-', color=COLS['orange'], lw=1.3, **mkw)
ax_B.axhline(1.334, color=COLS['red'], ls='--', lw=0.7, alpha=0.6)
ax_B.text(0.55, 1.38, r'$\beta_{\rm CF4}$', fontsize=8, color=COLS['red'])
ax_B.set_ylabel(r'$\tilde{\beta}\;\;(\times 10^{-3})$')
ax_B.set_ylim(0, 1.6)
ax_B.text(0.04, 0.93, '(b)', transform=ax_B.transAxes,
          fontsize=11, fontweight='bold', va='top')


# Panel C: Q_median vs ρ
ax_C.plot(rho, Q, '-', color=COLS['green'], lw=1.3, **mkw)
ax_C.axhline(0.01, color=COLS['gray'], ls=':', lw=0.6, alpha=0.5)
ax_C.text(0.82, 0.015, '$q_\\star=0.01$', fontsize=7.5, color=COLS['gray'])
ax_C.set_xlabel(r'$\rho$ (CatWISE–Radio correlation)')
ax_C.set_ylabel(r'$\tilde{Q} = x / x_{\rm max}$')
ax_C.set_ylim(0, 0.11)
ax_C.text(0.04, 0.93, '(c)', transform=ax_C.transAxes,
          fontsize=11, fontweight='bold', va='top')


# Panel D: Π(0.1) vs ρ
ax_D.plot(rho, Pi_01, '-', color=COLS['purple'], lw=1.3, **mkw)
ax_D.axhline(0.95, color=COLS['gray'], ls=':', lw=0.6, alpha=0.5)
ax_D.text(0.02, 0.97, r'$\Pi=0.95$', fontsize=7.5, color=COLS['gray'])
ax_D.axhline(0.05, color=COLS['gray'], ls=':', lw=0.6, alpha=0.5)
ax_D.text(0.02, 0.08, r'$\Pi=0.05$', fontsize=7.5, color=COLS['gray'])

# Shade the "robust" region
ax_D.fill_between([0, 0.5], 0.95, 1.0, alpha=0.05, color=COLS['purple'])

ax_D.set_xlabel(r'$\rho$ (CatWISE–Radio correlation)')
ax_D.set_ylabel(r'$\Pi(q_\star = 0.1)$')
ax_D.set_ylim(-0.03, 1.05)
ax_D.text(0.04, 0.55, '(d)', transform=ax_D.transAxes,
          fontsize=11, fontweight='bold', va='top')


# ─── Shared x-axis formatting ────────────────────────────────
for ax in axes.flat:
    ax.set_xlim(-0.02, 1.0)

fig.tight_layout(w_pad=2.0, h_pad=1.5)
save_fig(fig, 'fig_rho_sweep')
print("Saved fig_rho_sweep.pdf + .png")
