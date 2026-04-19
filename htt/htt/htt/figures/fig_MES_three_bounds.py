#!/usr/bin/env python3
"""
fig_MES_three_bounds.py — MES Three-Bound Hierarchy (v3, post-audit)
====================================================================
B_σ > B_ω > B_u̇ as functions of ε₁, with scenario markers.
S1 ε₁ corrected to 1.233e-3. S0 removed (ε₁=0 off log scale).
Legend simplified; formulas moved to caption.

Output: fig_MES_three_bounds.pdf
"""
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, '/mnt/project')
from bounds import B_sigma, B_omega, B_accel
from ssot import C
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS

apply_style()

# ═══════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════
e1_arr = np.logspace(-5, -1.5, 500)
Bs_arr = np.array([B_sigma(e) for e in e1_arr])
Bw_arr = np.array([B_omega(e) for e in e1_arr])
Ba_arr = np.array([B_accel(e) for e in e1_arr])

# Scenarios — standard SC palette colours (consistent with other figures)
# Caption clarifies markers are placed on B_σ curve
scenarios = [
    ('S1',   1.2336e-3, 'o', COLS['blue'],   (-6, 8)),
    ('S2a',  1.476e-3,  's', COLS['orange'], (8, 6)),
    ('S2c',  3.296e-3,  '^', COLS['red'],    (8, 5)),
]

# ═══════════════════════════════════════════════════════════
#  FIGURE
# ═══════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7.0, 3.5))

# R2: Simplified legend labels (formulas → caption)
ax.plot(e1_arr, Bs_arr, color=COLS['blue'], lw=1.8, ls='-',
        label=r'$B_\sigma$  (shear)', zorder=3)
ax.plot(e1_arr, Bw_arr, color=COLS['orange'], lw=1.8, ls='--',
        label=r'$B_\omega$  (vorticity)', zorder=3)
ax.plot(e1_arr, Ba_arr, color=COLS['red'], lw=1.5, ls=(0,(4,2,1,2)),
        label=r'$B_{\dot{u}}$  (acceleration)', zorder=3)

# Scenario markers on B_σ curve (R1: S0 removed)
for name, e1, marker, col, (dx, dy) in scenarios:
    bs = B_sigma(e1)
    ax.plot(e1, bs, marker=marker, color=col, ms=7,
            mec='k', mew=0.35, zorder=5)
    ax.annotate(name, (e1, bs),
                textcoords='offset points', xytext=(dx, dy),
                fontsize=8, color=col, fontweight='medium')

# R4: Single right-edge label (B_σ only; B_ω/B_u̇ identified by legend)
e_right = 2.5e-2
ax.text(e_right * 1.05, B_sigma(e_right), r'$B_\sigma$',
        fontsize=9, color=COLS['blue'], va='center', ha='left',
        fontweight='bold')

# R7: Darkened regime labels
ax.text(2e-5, 1.5e-5, r'$\varepsilon_2, \varepsilon_3$-dominated',
        fontsize=8, color='#666666', style='italic')

# R5: Ratio + regime in lower-right zone (single box)
ax.text(8e-3, 4e-5,
        r'$\varepsilon_1$-dominated'
        '\n'
        r'$B_\omega/B_\sigma \approx B_{\dot{u}}/B_\sigma \approx 0.45$',
        fontsize=7.5, color='#555555', style='italic',
        bbox=dict(fc='white', ec='#CCCCCC', pad=2, alpha=0.9,
                  boxstyle='round,pad=0.3'))

# Hierarchy gap annotation: at ε₁ = 8e-3 where gap is visually clear
e1_gap = 8e-3
bs_gap = B_sigma(e1_gap)
bw_gap = B_omega(e1_gap)
ax.annotate('', xy=(e1_gap, bw_gap), xytext=(e1_gap, bs_gap),
            arrowprops=dict(arrowstyle='<->', color='#888888', lw=0.7))
ax.text(e1_gap * 1.15, (bs_gap * bw_gap)**0.5,
        r'$\times\!2.2$', fontsize=8, color='#666666', va='center')

# Axes
ax.set_xscale('log')
ax.set_yscale('log')
ax.set_xlim(8e-6, 3.5e-2)
ax.set_ylim(3e-6, 1e-1)

ax.set_xlabel(r'CMB dipole amplitude $\varepsilon_1$')
ax.set_ylabel(r'MES bound combination')

# Legend (R2: compact)
ax.legend(loc='upper left', fontsize=8.5, framealpha=0.92,
          handlelength=2.5)

fig.tight_layout()
save_fig(fig, 'fig_MES_three_bounds')
print("ok fig_MES_three_bounds.pdf saved (v3, post-audit)")
