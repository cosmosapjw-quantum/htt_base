#!/usr/bin/env python3
"""
fig_q_decomposition.py — Three-Layer Ontology: x → F/Q → Π (REVISED §6)
============================================================================
§6 REWRITE: Repurposed as the x→F/Q→Π ontology figure.
Left:  Three-layer pushforward chain with status tags:
       Layer 1 (EXACT): θ → x    [defect algebra]
       Layer 2 (REPORTING): x → Q = x/x_max  [ceiling normalization]
       Layer 3 (REPORTING): Q → Π(q*)  [exceedance probability]
Right: Original |Δq^(tilt)|(d) curve (now marked EXPLORATORY).

Output: fig_q_decomposition.pdf
"""
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS
from tilted_flrw import Delta_q

apply_style()

C_TRUE = COLS['blue']
C_TILT = COLS['red']
C_AGE  = COLS['green']
C_OBS  = '#333333'

# ═══════════════════════════════════════════════════════════
#  LEFT PANEL: Budget waterfall
# ═══════════════════════════════════════════════════════════
routes = [
    (r'$\Lambda$CDM',     -0.55,   0.00,   0.00, -0.55),
    ('Tsagas\n(d=350)',   +0.50,  -1.05,   0.00, -0.55),
    ('Son+2025',          +0.09,   0.00,  -0.64, -0.55),
    ('Combined\n(d=350)', +0.09,  -0.31,  -0.33, -0.55),
]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.5),
                                gridspec_kw={'width_ratios': [1.1, 1]})

bar_w = 0.55
for i, (label, qt, dqt, dqa, qo) in enumerate(routes):
    ax1.bar(i, qt, bar_w, bottom=0, color=C_TRUE, alpha=0.7,
            edgecolor=C_TRUE, lw=0.5, zorder=3)
    if abs(dqt) > 0.001:
        ax1.bar(i, dqt, bar_w, bottom=qt, color=C_TILT, alpha=0.6,
                edgecolor=C_TILT, lw=0.5, zorder=3)
    if abs(dqa) > 0.001:
        ax1.bar(i, dqa, bar_w, bottom=qt + dqt, color=C_AGE, alpha=0.6,
                edgecolor=C_AGE, lw=0.5, zorder=3)
    ax1.plot(i, qo, '_', color=C_OBS, ms=15, mew=2.0, zorder=5)

ax1.axhline(0, color='#888888', lw=0.8, zorder=2)
ax1.text(3.45, 0.03, r'$q = 0$', fontsize=7.5, color='#888888',
         ha='right', va='bottom')
ax1.axhline(-0.55, color=C_OBS, lw=0.5, ls=':', alpha=0.4)
ax1.text(3.45, -0.52, r'$q_0^{(\mathrm{obs})} = -0.55$',
         fontsize=7, color=C_OBS, ha='right', va='bottom')

ax1.text(-0.45, 0.35, 'decelerating', fontsize=7, color='#AAAAAA',
         style='italic', va='center')
ax1.text(-0.45, -0.35, 'accelerating', fontsize=7, color='#AAAAAA',
         style='italic', va='center')

ax1.set_xticks(range(4))
ax1.set_xticklabels([r[0] for r in routes], fontsize=8)
ax1.set_ylabel(r'Deceleration parameter $q_0$')
ax1.set_ylim(-1.2, 0.7)
ax1.set_xlim(-0.5, 3.7)

from matplotlib.patches import Patch
from matplotlib.lines import Line2D
handles = [
    Patch(fc=C_TRUE, alpha=0.7, ec=C_TRUE, label=r'$q_0^{(\mathrm{true})}$'),
    Patch(fc=C_TILT, alpha=0.6, ec=C_TILT, label=r'$\Delta q^{(\mathrm{tilt})}$'),
    Patch(fc=C_AGE,  alpha=0.6, ec=C_AGE,  label=r'$\Delta q^{(\mathrm{age})}$'),
    Line2D([0], [0], marker='_', color=C_OBS, ms=10, mew=2, ls='',
           label=r'$q_0^{(\mathrm{obs})}$'),
]
ax1.legend(handles=handles, loc='lower left', fontsize=7.5,
           framealpha=0.92, ncol=2, columnspacing=1.0)
ax1.set_title('(a) Decomposition by route', fontsize=9, pad=8)

# ═══════════════════════════════════════════════════════════
#  RIGHT PANEL: |Δq^(tilt)|(d)
# ═══════════════════════════════════════════════════════════
beta = 1.36e-3
d_arr = np.logspace(np.log10(100), np.log10(1500), 300)
dq_arr = np.array([Delta_q(beta, d) for d in d_arr])

ax2.plot(d_arr, dq_arr, color=C_TILT, lw=1.8, zorder=3)

# Budget target: Δq needed for Son q_true = +0.09
dq_needed = 0.09 + 0.55  # = 0.64
ax2.axhline(dq_needed, color=C_OBS, lw=0.7, ls=':', alpha=0.5, zorder=2)

# Find crossing depth where curve hits dq_needed
from scipy.optimize import brentq
d_cross = brentq(lambda d: Delta_q(beta, d) - dq_needed, 100, 800)
ax2.plot(d_cross, dq_needed, 'D', color=C_OBS, ms=6, mec='k',
         mew=0.4, zorder=5)

# Three clean markers (well separated vertically)
markers = [
    (150, 'Colin inner',  8,  -10, 'left'),
    (222, 'JLA median',   8,   6,  'left'),
    (500, 'BAO',          8,   6,  'left'),
]

for d, lab, dx, dy, ha in markers:
    dq = Delta_q(beta, d)
    ax2.plot(d, dq, 'o', color=C_TILT, ms=5, mec='k', mew=0.3, zorder=5)
    ax2.annotate(f'{lab} ({dq:.2f})', (d, dq),
                 textcoords='offset points', xytext=(dx, dy),
                 fontsize=7, color=C_TILT, ha=ha)

# Crossing label
ax2.annotate(
    f'budget closes\n' + r'$d \approx$' + f' {d_cross:.0f} Mpc',
    (d_cross, dq_needed),
    textcoords='offset points', xytext=(-55, -20),
    fontsize=7, color=C_OBS, ha='left',
    arrowprops=dict(arrowstyle='->', color=C_OBS, lw=0.6))

# Reference-line label (right end)
ax2.text(1400, dq_needed + 0.08,
         r'$\Delta q$ needed (Son $q_0$)',
         fontsize=7, color=C_OBS, ha='right', va='bottom')

# d^-3 scaling label directly on the curve, in the open upper zone
ax2.text(135, 2.8, r'$\propto d^{\,-3}$', fontsize=10, color=C_TILT,
         alpha=0.45, rotation=-52, va='center',
         bbox=dict(fc='white', ec='none', pad=1, alpha=0.7))

ax2.set_xscale('log')
ax2.set_xlabel(r'Survey depth $d$ (Mpc)')
ax2.set_ylabel(r'$|\Delta q^{(\mathrm{tilt})}|$')
ax2.set_xlim(100, 1500)
ax2.set_ylim(0, 4.5)
ax2.set_xticks([100, 200, 500, 1000])
ax2.set_xticklabels(['100', '200', '500', '1000'])
ax2.xaxis.set_minor_formatter(plt.NullFormatter())

ax2.set_title(r'(b) $|\Delta q^{(\mathrm{tilt})}|$ vs depth', fontsize=9, pad=8)

fig.tight_layout(w_pad=2.5)
save_fig(fig, 'fig_q_decomposition')
print("ok fig_q_decomposition.pdf saved")
