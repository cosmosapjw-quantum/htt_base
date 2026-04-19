#!/usr/bin/env python3
"""
fig_scale_hierarchy.py — Distance Scale Hierarchy (updated for TF-series)
=========================================================================
Horizontal log-scale showing all relevant distance scales from SH0ES
to λ_H, with contamination zone shading and new tilted-FLRW scales.

Output: fig_scale_hierarchy.pdf
Insert: figures_ch08.tex (replaces existing version)
"""

# SSOT_NOTE: Cosmological constants (H₀=67.36, Ω_m=0.3153) are from
# workspace/data/obs_defaults.json (Planck 2018 FLRW fit). These are
# FLRW-fitted values; Bianchi corrections O(Σ²) ~ 10⁻⁶ are negligible
# for figure-generation purposes.

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS
from tilted_flrw import peculiar_jeans, _lambda_H

apply_style()

beta = 1.334e-3
C_OLD = COLS['blue']       # existing scales
C_NEW = COLS['purple']     # new tilted-FLRW scales
C_OBS = COLS['orange']     # observational surveys
C_CONT = COLS['red']       # contamination zone
C_SAFE = COLS['green']     # safe zone

# ═══════════════════════════════════════════════════════════
#  SCALES: (position_Mpc, label, row, colour, style)
#  row: 0 = top (physical scales), 1 = bottom (surveys)
# ═══════════════════════════════════════════════════════════
lJ_EdS = peculiar_jeans(beta, 0.5)[0]    # ~297
lJ_Son = peculiar_jeans(beta, 0.09)[0]   # ~526

# Colin decay scale: d_S = S × c/H₀
S_colin = 0.0262; c_km = 299792.458; H0 = 67.36
d_S = S_colin * c_km / H0  # ~117

# Physical scales (upper row)
# Physical scales (upper row) — stagger heights to avoid overlap
phys_heights = {
    'd_S':    1.6,
    'lJ_EdS': 1.3,
    'lJ_Son': 1.6,
    'lH':     1.3,
}

phys_scales = [
    (d_S,       r'$d_S$ (Colin)',                   C_NEW, phys_heights['d_S']),
    (lJ_EdS,    r'$\lambda_J^{\rm pec}$' + '\n(EdS)', C_NEW, phys_heights['lJ_EdS']),
    (lJ_Son,    r'$\lambda_J^{\rm pec}$' + '\n(Son)', C_NEW, phys_heights['lJ_Son']),
    (_lambda_H, r'$\lambda_H$',                      C_OLD, phys_heights['lH']),
]

# Observational surveys (lower row)
obs_scales = [
    (30,   'Cepheid\nhosts',     C_OBS),
    (50,   'SH0ES\nmedian',      C_OBS),
    (75,   'TRGB',               C_OBS),
    (200,  'CF4\nouter',         C_OBS),
    (500,  'BAO\nlow-$z$',       C_OBS),
    (2700, 'Euclid\ndepth',      C_OBS),
]

# ═══════════════════════════════════════════════════════════
#  FIGURE
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7.0, 3.2))

ax.set_xlim(15, 6500)
ax.set_ylim(-1.5, 2.8)
ax.set_xscale('log')

# Remove y-axis
ax.set_yticks([])
ax.spines['left'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['top'].set_visible(False)

ax.set_xlabel(r'Comoving distance $d$ (Mpc)')

# ── Contamination zone (d < λ_J → tilt affects observables) ──
ax.axvspan(15, lJ_EdS, color=C_CONT, alpha=0.06, zorder=0)
ax.axvspan(lJ_EdS, lJ_Son, color=C_CONT, alpha=0.03, zorder=0)

# ── Agreement zone (d > λ_J → all observers agree) ──
ax.axvspan(lJ_Son, 6500, color=C_SAFE, alpha=0.04, zorder=0)

# Zone labels
ax.text(55, 2.5, 'tilt contamination zone',
        fontsize=8, color=C_CONT, ha='center', va='center',
        style='italic', alpha=0.7)
ax.text(2000, 2.5, 'agreement zone',
        fontsize=8, color=C_SAFE, ha='center', va='center',
        style='italic', alpha=0.7)

# ── Central axis line ──
ax.axhline(0.5, color='#CCCCCC', lw=0.5, zorder=1)

# ── Physical scales (above axis) ──
for d, label, col, ht in phys_scales:
    ax.plot([d, d], [0.5, ht], color=col, lw=1.2, zorder=3)
    ax.plot(d, ht, 'v', color=col, ms=6, mec='k', mew=0.3, zorder=4)
    ax.text(d, ht + 0.15, label, fontsize=7, ha='center', va='bottom',
            color=col, fontweight='bold', linespacing=1.1)

# ── Observational surveys (below axis) ──
for d, label, col in obs_scales:
    ax.plot([d, d], [-0.5, 0.5], color=col, lw=1.0, zorder=3)
    ax.plot(d, -0.5, '^', color=col, ms=5, mec='k', mew=0.3, zorder=4)
    ax.text(d, -0.7, label, fontsize=6.5, ha='center', va='top',
            color=col, linespacing=1.1)

# (λ_J range bracket removed — staggered labels are self-explanatory)

# ── Row labels ──
ax.text(17, 1.5, 'Physical\nscales', fontsize=6.5, color='#888888',
        ha='left', va='center', style='italic')
ax.text(17, -0.5, 'Surveys', fontsize=6.5, color='#888888',
        ha='left', va='center', style='italic')

# ── Legend ──
handles = [
    mpatches.Patch(fc=C_CONT, alpha=0.15, ec=C_CONT,
                   label='Tilt contamination'),
    mpatches.Patch(fc=C_SAFE, alpha=0.12, ec=C_SAFE,
                   label='Agreement zone'),
    plt.Line2D([0], [0], marker='v', color=C_NEW, ms=6, ls='',
               mec='k', mew=0.3, label='New (tilted-FLRW)'),
    plt.Line2D([0], [0], marker='v', color=C_OLD, ms=6, ls='',
               mec='k', mew=0.3, label='Existing'),
]
ax.legend(handles=handles, loc='upper right', fontsize=6.5,
          framealpha=0.92, ncol=2, columnspacing=0.8,
          bbox_to_anchor=(0.99, 0.98))

fig.tight_layout()
save_fig(fig, 'fig_scale_hierarchy')
print("ok fig_scale_hierarchy.pdf saved")
