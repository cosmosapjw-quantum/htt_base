#!/usr/bin/env python3
"""
fig_tilted_H0_depth.py — Tilted H0 Correction vs Survey Depth
==============================================================
DeltaH = beta*c/(3d) with tension lines and survey markers.
Focused on the physically relevant range; Bianchi beta^2/2
noted in legend annotation rather than plotted.

Output: fig_tilted_H0_depth.pdf
Insert: figures_ch08.tex, referenced in S8.3.4

STATUS: EXPLORATORY — Appendix-grade output only (HB-4).
This figure must NOT appear in core results (Ch. 2-7).
Target: appendix_J_bridge_quarantine.tex
"""
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS
from tilted_flrw import tilted_H_perturbative, _H0, _lambda_H

apply_style()

beta = 1.334e-3
tension_shoes = 5.6
tension_trgb  = 2.4

# Curve
d_arr = np.logspace(np.log10(15), np.log10(2000), 400)
dH_arr = np.array([tilted_H_perturbative(beta, d)[1] * _H0 for d in d_arr])

# Surveys
surveys = [
    ('Cepheids',  30,  COLS['red'],    ( 10, -14)),
    ('SH0ES',     50,  COLS['orange'], ( 10, 6)),
    ('TRGB',      75,  COLS['green'],  ( 10, 6)),
    ('CF4',      200,  COLS['blue'],   ( 10, 6)),
    ('BAO',      500,  COLS['purple'], (-12, 8)),
]

# ═══════════════════════════════════════════════════════════
fig, ax1 = plt.subplots(figsize=(7.0, 3.5))

# ── Tension reference lines ──
ax1.axhline(tension_shoes, color=COLS['red'], lw=0.8, ls='--', alpha=0.5)
ax1.axhline(tension_trgb, color=COLS['green'], lw=0.8, ls='--', alpha=0.5)

# Labels for tension lines
ax1.text(20, tension_shoes + 0.08,
         r'SH0ES–Planck ($5.6$ km/s/Mpc)',
         fontsize=7, color=COLS['red'], va='bottom', ha='left')
ax1.text(350, tension_trgb + 0.08,
         r'TRGB–Planck ($2.4$ km/s/Mpc)',
         fontsize=7, color=COLS['green'], va='bottom', ha='left')

# ── Main curve ──
ax1.plot(d_arr, dH_arr, color=COLS['blue'], lw=1.8, zorder=3,
         label=r'$\Delta H = \beta\,c\,/\,(3d)$')

# ── Survey markers ──
for name, d, col, (dx, dy) in surveys:
    _, dHH = tilted_H_perturbative(beta, d)
    dH_val = dHH * _H0
    pct = dH_val / tension_shoes * 100
    ax1.plot(d, dH_val, 'o', color=col, ms=7, mec='k', mew=0.35,
             zorder=5)
    ax1.annotate(f'{name} ({pct:.0f}%)',
                 (d, dH_val), textcoords='offset points',
                 xytext=(dx, dy), fontsize=7.5, color=col, ha='left')

# ── Axes ──
ax1.set_xscale('log')
ax1.set_xlim(15, 2000)
ax1.set_ylim(0, 6.5)

ax1.set_xlabel(r'Survey depth $d$ (Mpc)')
ax1.set_ylabel(r'$\Delta H$ (km s$^{-1}$ Mpc$^{-1}$)')

ax1.set_xticks([20, 50, 100, 200, 500, 1000])
ax1.set_xticklabels(['20', '50', '100', '200', '500', '1000'])
ax1.xaxis.set_minor_formatter(plt.NullFormatter())

# ── Right axis: % of SH0ES tension ──
ax2 = ax1.twinx()
ax2.set_ylim(0, 6.5 / tension_shoes * 100)
ax2.set_ylabel(r'$\%$ of SH0ES tension', color='#555555')
ax2.tick_params(axis='y', colors='#555555')

# ── d^{-1} scaling label along the curve ──
ax1.text(140, 1.55, r'$\propto d^{\,-1}$', fontsize=10, color=COLS['blue'],
         rotation=-35, ha='center', va='center', alpha=0.5,
         bbox=dict(fc='white', ec='none', pad=1, alpha=0.7))

# ── Legend with Bianchi note ──
from matplotlib.lines import Line2D
handles = [
    Line2D([0], [0], color=COLS['blue'], lw=1.8,
           label=r'$\Delta H = \beta\,c/(3d)$  (perturbative)'),
]
leg = ax1.legend(handles=handles, loc='upper right', fontsize=8,
                 framealpha=0.92, handlelength=2.0)

# Bianchi annotation as text note in lower-left empty space
ax1.text(18, 0.15,
         r'Homogeneous Bianchi: $\Delta H = \beta^2 H_0/2'
         r'\approx 6\!\times\!10^{-5}$ km/s/Mpc'
         '\n(five orders below this range)',
         fontsize=7, color='#555555', ha='left', va='bottom',
         style='italic',
         bbox=dict(fc='#F5F5F5', ec='#AAAAAA', pad=3, alpha=0.95,
                   boxstyle='round,pad=0.3'))

fig.tight_layout()
save_fig(fig, 'fig_tilted_H0_depth')
print("ok fig_tilted_H0_depth.pdf saved")
