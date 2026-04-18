#!/usr/bin/env python3
"""
fig_channel_ablation_heatmap.py — Channel ablation matrix heatmap
==================================================================
Rows: channel combinations. Columns: lnB, β̃, Q̃, Π(0.1), q₀.
Cell colour encodes normalised value (fraction of full-channel result).
"""
import sys, json
import numpy as np

sys.path.insert(0, '/mnt/project')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm

from plot_style import apply_style, save_fig, COLS

apply_style()

# ─── Load data ────────────────────────────────────────────────
with open('/mnt/user-data/outputs/robustness_sweeps_integrated.json') as f:
    data = json.load(f)

pts = data['sweep_D_channels']

# Row order (top to bottom: most informative → least)
row_order = [
    'All (abcdefh)',
    'No CF4 (abdefh)',
    'Dipole only (ab)',
    'CF4 only (c)',
    'No dipole (cdefh)',
    'CMB only (defh)',
    'Minimal (ef)',
]

# Build lookup
lookup = {p['config']: p for p in pts}

# Columns
col_keys = ['lnB', 'beta_median', 'Q_median', 'Pi_01', 'q0_mean']
col_labels = [r'$\ln\mathcal{B}$', r'$\tilde{\beta}$',
              r'$\tilde{Q}$', r'$\Pi(0.1)$', r'$\hat{q}_0$']

# Extract matrix
n_rows = len(row_order)
n_cols = len(col_keys)
raw = np.zeros((n_rows, n_cols))
for i, rname in enumerate(row_order):
    p = lookup[rname]
    for j, k in enumerate(col_keys):
        raw[i, j] = p[k]

# Reference (full channels = row 0) for normalisation
ref = raw[0, :].copy()

# Normalised matrix: fraction of full-channel value
# For lnB: use absolute scale (some are negative)
# For others: ratio to full
norm_mat = np.zeros_like(raw)
for j in range(n_cols):
    if ref[j] != 0:
        norm_mat[:, j] = raw[:, j] / ref[j]
    else:
        norm_mat[:, j] = 0

# ─── Row labels with channel letters highlighted ─────────────
row_labels = [
    'All (abcdefh)',
    'No CF4 (abdefh)',
    'Dipole only (ab)',
    'CF4 only (c)',
    'No dipole (cdefh)',
    'CMB only (defh)',
    'Minimal (ef)',
]

# ─── Cell text: raw values with appropriate formatting ────────
def fmt_cell(val, col_idx):
    k = col_keys[col_idx]
    if k == 'lnB':
        return f'{val:+.1f}'
    elif k == 'beta_median':
        return f'{val:.2e}'
    elif k == 'Q_median':
        return f'{val:.4f}'
    elif k == 'Pi_01':
        return f'{val:.3f}'
    elif k == 'q0_mean':
        return f'{val:.0f}'
    return f'{val:.3f}'

# ─── Figure ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.0, 3.8))

# Custom diverging colormap: red (0) → white (0.5) → blue (1.0)
# Normalised values: 0 = zero, 1.0 = full channel value
cmap = LinearSegmentedColormap.from_list('ablation', [
    (0.0, '#d73027'),    # strong red at 0
    (0.15, '#fc8d59'),   # orange
    (0.4, '#fee090'),    # light yellow
    (0.6, '#e0f3f8'),    # light cyan
    (0.85, '#91bfdb'),   # medium blue
    (1.0, '#4575b4'),    # strong blue at 1
])

# Clamp normalised values for colour mapping
norm_clamped = np.clip(norm_mat, -0.1, 1.1)

im = ax.imshow(norm_clamped, cmap=cmap, aspect='auto',
               vmin=-0.1, vmax=1.1)

# Cell text
for i in range(n_rows):
    for j in range(n_cols):
        val = raw[i, j]
        txt = fmt_cell(val, j)
        # Text colour: white on dark, black on light
        nv = norm_clamped[i, j]
        tc = 'white' if nv < 0.2 or nv > 0.9 else 'black'
        ax.text(j, i, txt, ha='center', va='center',
                fontsize=8.5, color=tc, fontweight='bold' if i == 0 else 'normal')

# Axes
ax.set_xticks(range(n_cols))
ax.set_xticklabels(col_labels, fontsize=10)
ax.set_yticks(range(n_rows))
ax.set_yticklabels(row_labels, fontsize=9)

# Move x labels to top
ax.xaxis.set_ticks_position('top')
ax.xaxis.set_label_position('top')

# Colorbar
cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
cbar.set_label('Fraction of full-channel value', fontsize=9)
cbar.set_ticks([0, 0.25, 0.5, 0.75, 1.0])
cbar.set_ticklabels(['0', '0.25', '0.5', '0.75', '1.0'])

# Grid lines between rows
for i in range(n_rows + 1):
    ax.axhline(i - 0.5, color='white', lw=1.5)
for j in range(n_cols + 1):
    ax.axvline(j - 0.5, color='white', lw=1.5)

# Highlight the full-channel row
ax.axhline(-0.5, color='k', lw=1.5)
ax.axhline(0.5, color='k', lw=1.5)

# Highlight the "No CF4" row (catalog comparison)
rect = plt.Rectangle((-0.5, 0.5), n_cols, 1, linewidth=1.5,
                      edgecolor=COLS['orange'], facecolor='none',
                      linestyle='--', zorder=10)
ax.add_patch(rect)
ax.text(n_cols + 0.15, 1.0, '← catalog\n   comparison',
        fontsize=7.5, color=COLS['orange'], va='center')

fig.tight_layout()
save_fig(fig, 'fig_channel_ablation_heatmap')
print("Saved fig_channel_ablation_heatmap.pdf + .png")
