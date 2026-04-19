#!/usr/bin/env python3
"""
fig_type_by_type_summary.py — Equivalence-Class Map (REVISED §6)
====================================================================
§6 REWRITE: Split into two panels per operational revision checklist:
  Panel 1: Theoretical family map (kinematic variables by Bianchi type)
  Panel 2: Inference-identifiable equivalence classes under scalar-amplitude
           likelihood — the reader sees immediately that these are not the
           same thing.

Equivalence classes: FLRW_null, tilt_null, orth_1D, tilt_flat,
tilt_curved, vortical. See appendix_H_equiv_classes.tex.

Output: fig_type_by_type_summary.pdf
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import sys, os
sys.path.insert(0, '/mnt/project')
from bounds import Sig2_max_MES
from ssot import C
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS

apply_style()

C_ORTH = COLS['blue']
C_TILT = COLS['red']
C_BG   = '#F8F8F8'

# ═══════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════
# Types in display order
types = ['I', 'II', 'III', 'V',
         r'VI$_0$', r'VII$_0$', 'VIII', 'IX', r'VII$_h$']

# Variables: σ, ω, u̇, β, n (curvature), x_h (spiral)
var_labels = [r'$\sigma$', r'$\omega$', r'$\dot{u}$',
              r'$\beta$', r'$n$', r'$x_h$']

# Grid: 0=absent, 1=orthogonal, 2=tilt-activated
#              σ  ω  u̇  β  n  x_h
grid = {
    'I':      [1, 0, 0, 0, 0, 0],  # orth: σ only
    'II':     [1, 0, 0, 0, 1, 0],  # + curvature
    'III':    [1, 0, 0, 0, 1, 0],
    'V':      [1, 0, 0, 0, 1, 0],
    'VI0':    [1, 0, 0, 0, 0, 0],
    'VII0':   [1, 0, 0, 0, 0, 0],
    'VIII':   [1, 0, 0, 0, 1, 0],
    'IX':     [1, 0, 0, 0, 1, 0],
    'VIIh':   [1, 1, 0, 0, 1, 1],  # ω and x_h in orth
}
# Tilt adds: β, u̇ to all; ω to all except VIIh (already has it)
grid_tilt = {
    'I':      [0, 2, 2, 2, 0, 0],
    'II':     [0, 2, 2, 2, 0, 0],
    'III':    [0, 2, 2, 2, 0, 0],
    'V':      [0, 2, 2, 2, 0, 0],  # β constrained by momentum
    'VI0':    [0, 2, 2, 2, 0, 0],
    'VII0':   [0, 2, 2, 2, 0, 0],
    'VIII':   [0, 2, 2, 2, 0, 0],
    'IX':     [0, 2, 2, 2, 0, 0],
    'VIIh':   [0, 0, 2, 2, 0, 0],  # ω already present
}

type_keys = ['I', 'II', 'III', 'V', 'VI0', 'VII0', 'VIII', 'IX', 'VIIh']

# Numerical bounds at S1 and S3
e1_S1 = C.eps1_kin   # 1.2336e-3 (CORRECTED)
e1_S3 = 1.476e-3

sig2_S1 = Sig2_max_MES(e1_S1)
sig2_S3 = Sig2_max_MES(e1_S3)

# ═══════════════════════════════════════════════════════════
#  FIGURE
# ═══════════════════════════════════════════════════════════
n_types = len(types)
n_vars = len(var_labels)

fig, ax = plt.subplots(figsize=(7.0, 3.8))

# Grid geometry
x0 = 1.5   # left edge of grid
dx = 0.7   # column width
y0 = 0.5   # bottom edge
dy = 0.35  # row height

# Draw grid cells
for i, (tkey, tname) in enumerate(zip(type_keys, types)):
    yi = y0 + (n_types - 1 - i) * dy
    
    # Alternating row background
    if i % 2 == 0:
        ax.fill_between([x0 - 0.05, x0 + n_vars * dx + 0.05],
                        yi - dy/2, yi + dy/2,
                        color=C_BG, zorder=0)
    
    # Type label
    ax.text(x0 - 0.15, yi, tname, fontsize=9, ha='right', va='center',
            fontweight='bold', color='#333333')
    
    # Variable cells
    orth = grid[tkey]
    tilt = grid_tilt[tkey]
    for j in range(n_vars):
        xj = x0 + j * dx + dx/2
        
        if orth[j] == 1:
            ax.plot(xj, yi, 's', color=C_ORTH, ms=10, mec='white',
                    mew=1.2, zorder=3)
        if tilt[j] == 2:
            ax.plot(xj, yi, '^', color=C_TILT, ms=8, mec='white',
                    mew=1.0, zorder=3)

# Column headers
for j, vlab in enumerate(var_labels):
    xj = x0 + j * dx + dx/2
    ax.text(xj, y0 + n_types * dy + 0.05, vlab,
            fontsize=10, ha='center', va='bottom', color='#333333')

# Header line
ax.plot([x0 - 0.1, x0 + n_vars * dx + 0.1],
        [y0 + n_types * dy - 0.05, y0 + n_types * dy - 0.05],
        color='#CCCCCC', lw=0.6)

# Σ²_max column (right side)
x_num = x0 + n_vars * dx + 0.8
ax.text(x_num, y0 + n_types * dy + 0.15,
        r'$\Sigma^2_{\max}$', fontsize=9, ha='center', va='bottom',
        color='#333333', fontweight='bold')
ax.text(x_num - 0.35, y0 + n_types * dy + 0.0,
        'S1', fontsize=7, ha='center', va='top', color=COLS['blue'])
ax.text(x_num + 0.35, y0 + n_types * dy + 0.0,
        'S3', fontsize=7, ha='center', va='top', color=COLS['purple'])

for i, tkey in enumerate(type_keys):
    yi = y0 + (n_types - 1 - i) * dy
    
    # All types except VIIh use the MES algebraic ceiling
    if tkey == 'VIIh':
        # VIIh has Saadeh-constrained bound (much tighter)
        ax.text(x_num, yi, r'$W_{\rm Saa}^2/R_{\rm WS}^2$',
                fontsize=7, ha='center', va='center', color='#666666')
    else:
        ax.text(x_num - 0.35, yi, f'{sig2_S1:.1e}',
                fontsize=6.5, ha='center', va='center', color=COLS['blue'])
        ax.text(x_num + 0.35, yi, f'{sig2_S3:.1e}',
                fontsize=6.5, ha='center', va='center', color=COLS['purple'])

# Vertical separator before Σ²_max column
ax.plot([x_num - 0.65, x_num - 0.65],
        [y0 - dy/2, y0 + n_types * dy - 0.05],
        color='#DDDDDD', lw=0.5)

# Special annotations
# V: momentum constraint on β
i_V = type_keys.index('V')
yi_V = y0 + (n_types - 1 - i_V) * dy
ax.text(x0 + 3 * dx + dx/2, yi_V - 0.13, '(C)',
        fontsize=5.5, ha='center', va='top', color=C_TILT, style='italic')

# Axes
ax.set_xlim(0, x_num + 1.0)
ax.set_ylim(y0 - dy, y0 + n_types * dy + 0.4)
ax.axis('off')

# Legend
handles = [
    plt.Line2D([0], [0], marker='s', color='white', markerfacecolor=C_ORTH,
               ms=9, mec='white', mew=1.2, label='Orthogonal'),
    plt.Line2D([0], [0], marker='^', color='white', markerfacecolor=C_TILT,
               ms=8, mec='white', mew=1.0, label='Tilt-activated'),
]
ax.legend(handles=handles, loc='lower left', fontsize=8,
          framealpha=0.92, ncol=2, columnspacing=1.0,
          bbox_to_anchor=(0.0, -0.02))

# Title
ax.text((x0 + x_num) / 2, y0 + n_types * dy + 0.35,
        'Active kinematic variables by Bianchi type',
        fontsize=10, ha='center', va='bottom', fontweight='bold',
        color='#333333')

fig.tight_layout()
save_fig(fig, 'fig_type_by_type_summary')
print("ok fig_type_by_type_summary.pdf saved")
