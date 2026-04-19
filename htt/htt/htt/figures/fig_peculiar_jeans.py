#!/usr/bin/env python3
"""
fig_peculiar_jeans.py — Peculiar Jeans Length vs Tilt Rapidity
==============================================================
lambda_J^pec(beta) for q = 0.5 (EdS) and q = 0.09 (Son+2025).

Output: fig_peculiar_jeans.pdf
Insert: figures_ch02.tex, referenced in S2.7.8

STATUS: EXPLORATORY — Appendix-grade output only (HB-4).
This figure must NOT appear in core results (Ch. 2-7).
Target: appendix_J_bridge_quarantine.tex
"""
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS
from tilted_flrw import peculiar_jeans

apply_style()

# Data
beta_arr = np.logspace(-3.6, -1.5, 400)
lJ_eds = np.array([peculiar_jeans(b, 0.5)[0] for b in beta_arr])
lJ_son = np.array([peculiar_jeans(b, 0.09)[0] for b in beta_arr])

# Scenarios: beta, label, marker, colour, (dx,dy) offset
scenarios = [
    (1.138e-3, 'S1',      'o', COLS['blue'],   (-6, -12)),
    (1.362e-3, 'S2a/S3',  's', COLS['orange'], (7, 5)),
    (1.40e-3,  'CF4',     'D', COLS['green'],  (7, -12)),
    (2.10e-3,  r'CF4$^+$','v', COLS['purple'], (7, -12)),
    (3.042e-3, 'S2c',     '^', COLS['red'],    (7, 4)),
]

beta_cf4 = 1.334e-3
sigma_cf4 = 0.267e-3

fig, ax = plt.subplots(figsize=(7.0, 3.8))

# Horizontal bands
ax.axhspan(200, 440, color='#E0E0E0', alpha=0.4, zorder=0)
ax.axhspan(500, 1200, color=COLS['cyan'], alpha=0.07, zorder=0)

# Vertical beta_CF4 band
ax.axvspan(beta_cf4 - sigma_cf4, beta_cf4 + sigma_cf4,
           color=COLS['yellow'], alpha=0.22, zorder=0)
ax.axvline(beta_cf4, color=COLS['orange'], lw=0.5, ls=':', alpha=0.5)

# Main curves
ax.plot(beta_arr, lJ_eds, color=COLS['blue'], lw=1.6, ls='-',
        label=r'$q = 0.5\;$(EdS)', zorder=3)
ax.plot(beta_arr, lJ_son, color=COLS['red'], lw=1.6, ls='--',
        label=r'$q = 0.09\;$(Son+ 2025)', zorder=3)

# Scenario markers (EdS curve only)
for beta_s, name, marker, color, (dx, dy) in scenarios:
    lJ_e = peculiar_jeans(beta_s, 0.5)[0]
    ax.plot(beta_s, lJ_e, marker=marker, color=color, ms=6.5,
            mec='k', mew=0.35, zorder=5)
    ax.annotate(name, (beta_s, lJ_e), textcoords='offset points',
                xytext=(dx, dy), fontsize=7, color=color,
                fontweight='medium')

# Connecting lines EdS -> Son for two key scenarios
for beta_s in [1.362e-3, 3.042e-3]:
    lJ_e = peculiar_jeans(beta_s, 0.5)[0]
    lJ_s = peculiar_jeans(beta_s, 0.09)[0]
    ax.plot([beta_s, beta_s], [lJ_e, lJ_s],
            color='#BBBBBB', lw=0.6, ls=':', zorder=2)

# Power-law guide
beta_ref = 1.362e-3
lJ_ref = peculiar_jeans(beta_ref, 0.5)[0]
beta_guide = np.logspace(-3.3, -1.6, 50)
lJ_guide = lJ_ref * (beta_guide / beta_ref)**(1.0/3)
ax.plot(beta_guide, lJ_guide, color='#C0C0C0', lw=0.6, ls=':',
        zorder=1)
ax.text(8e-3, lJ_ref * (8e-3/beta_ref)**(1./3) * 1.05,
        r'$\propto\!\beta^{1/3}$',
        fontsize=7.5, color='#AAAAAA', va='bottom')

# Zone labels
ax.text(3.0e-4, 310, 'CF4 depth',
        fontsize=7.5, color='#888888', ha='center', va='center',
        style='italic')
ax.text(3.0e-4, 750, 'BAO zone',
        fontsize=7.5, color=COLS['blue'], ha='center', va='center',
        style='italic', alpha=0.6)
ax.text(beta_cf4, 128, r'$\beta_{\mathrm{CF4}}$',
        fontsize=7.5, color=COLS['orange'], ha='center', va='top')

# Axes
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(2.5e-4, 1.2e-2)
ax.set_ylim(120, 1200)
ax.set_xlabel(r'Tilt rapidity $\beta$')
ax.set_ylabel(r'$\lambda_J^{\mathrm{pec}}$ (Mpc)')
ax.set_yticks([150, 200, 300, 500, 800, 1000])
ax.set_yticklabels(['150', '200', '300', '500', '800', '1000'])
ax.yaxis.set_minor_formatter(plt.NullFormatter())

ax.legend(loc='upper left', fontsize=8, framealpha=0.92,
          handlelength=2.0)

fig.tight_layout()
save_fig(fig, 'fig_peculiar_jeans')
print("ok fig_peculiar_jeans.pdf saved")
