#!/usr/bin/env python3
"""
fig_vorticity_hierarchy.py — Vorticity Scale Hierarchy (v2)
===========================================================
Vertical log-scale spanning 21 decades. Clean two-column layout:
equations on left, descriptions on right, brackets on far right.

Output: fig_vorticity_hierarchy.pdf
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import sys, os

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS

apply_style()

C_GEOM = COLS['blue']
C_MATT = COLS['red']
C_GRAY = '#888888'

# ═══════════════════════════════════════════════════════════
#  DATA  (log10 value, equation, description, frame)
# ═══════════════════════════════════════════════════════════
levels = [
    (-20.6, r'$2.5\!\times\!10^{-21}$',
            'Saadeh et al. 2016\n(Planck template)', 'geom'),
    (-16.5, r'$3\!\times\!10^{-17}$',
            'Tilt–shear coupling\n(S3 anomaly)', 'matt'),
    (-6.0,  r'$10^{-6}$',
            'MES algebraic\nbound', 'geom'),
    (-2.0,  r'$10^{-2}$',
            'Structure formation\n(perturbative)', 'matt'),
    (0.0,   r'$O(1)$',
            'Tudorache filament\n(MIGHTEE-HI 2025)', 'matt'),
]

# ═══════════════════════════════════════════════════════════
#  FIGURE — double-column width, moderate height
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7.0, 4.8))

y_lo, y_hi = -23, 2.5
ax.set_ylim(y_lo, y_hi)
ax.set_xlim(-3.0, 8.5)

# Remove x-axis
ax.set_xticks([])
ax.spines['top'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_position(('data', -0.3))

ax.set_ylabel(r'$\log_{10}\,(\omega/H)_0$  or  $\log_{10}\,W^2_{\mathrm{std}}$',
              fontsize=10)

ax.set_yticks(list(range(-20, 5, 5)))

# ── Background shading ──
ax.axhspan(y_lo, -5, color=C_GEOM, alpha=0.035, zorder=0)
ax.axhspan(-1, y_hi, color=C_MATT, alpha=0.035, zorder=0)

# Frame labels (far left, rotated)
ax.text(-2.5, -13.5, 'geometry frame', fontsize=7.5, color=C_GEOM,
        ha='center', va='center', rotation=90, style='italic', alpha=0.5)
ax.text(-2.5, -0.5, 'matter\nframe', fontsize=7.5, color=C_MATT,
        ha='center', va='center', style='italic', alpha=0.5)

# Central spine
x_spine = 1.5
ax.plot([x_spine, x_spine], [y_lo + 0.5, y_hi - 0.5],
        color='#E0E0E0', lw=0.6, zorder=0)

# ── Level markers ──
for log_val, eq_str, desc, frame in levels:
    col = C_GEOM if frame == 'geom' else C_MATT
    marker = 's' if frame == 'geom' else 'o'

    # Horizontal bar
    ax.plot([0.5, 2.5], [log_val, log_val], color=col, lw=2.0,
            solid_capstyle='round', zorder=3)

    # Marker at centre
    ax.plot(x_spine, log_val, marker=marker, color=col, ms=8,
            mec='white', mew=1.8, zorder=4)

    # Equation (left of bar)
    ax.text(0.3, log_val, eq_str, fontsize=9, color=col,
            ha='right', va='center', fontweight='bold')

    # Description (right of bar)
    ax.text(2.8, log_val, desc, fontsize=8, color='#333333',
            ha='left', va='center', linespacing=1.25)

# ── Gap annotations (far right, clean brackets) ──
def gap_bracket(y1, y2, x, label):
    """Minimal bracket with centred label."""
    # Vertical line
    ax.plot([x, x], [y1 + 0.6, y2 - 0.6], color=C_GRAY, lw=0.6,
            zorder=1)
    # Caps
    for yy in [y1 + 0.6, y2 - 0.6]:
        ax.plot([x - 0.15, x + 0.15], [yy, yy], color=C_GRAY,
                lw=0.6, zorder=1)
    # Label
    ymid = (y1 + y2) / 2
    ax.text(x + 0.3, ymid, label, fontsize=7.5, color=C_GRAY,
            ha='left', va='center', style='italic')

# Three key gaps
gap_bracket(-20.6, -16.5, 5.5, '4 orders')
gap_bracket(-20.6, -6.0,  6.5, '15 orders')
gap_bracket(-6.0,  0.0,   5.5, '6 orders')

# ── Legend ──
from matplotlib.lines import Line2D
handles = [
    Line2D([0], [0], marker='s', color=C_GEOM, lw=2, ms=7,
           mec='white', mew=1.2, label='Geometry frame'),
    Line2D([0], [0], marker='o', color=C_MATT, lw=2, ms=7,
           mec='white', mew=1.2, label='Matter frame'),
]
ax.legend(handles=handles, fontsize=8,
          framealpha=0.92, borderpad=0.6,
          loc='center', bbox_to_anchor=(0.35, 0.42))

fig.tight_layout()
save_fig(fig, 'fig_vorticity_hierarchy')
print("ok fig_vorticity_hierarchy.pdf saved")
