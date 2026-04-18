#!/usr/bin/env python3
"""
fig_equiv_class_evidence.py — Equivalence-Class Collapsed Evidence
===================================================================
P-25 deliverable. Horizontal bar chart of lnB by equivalence class,
CF4++ primary. Wong (2011) colorblind-friendly palette.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plot_style import apply_style

apply_style()

# Data (CF4++ primary)
classes = [
    ('FLRW$_{\\rm tilt}$', 44.0, 1, 'tilt'),
    ('tilt\\_flat (3)', 43.2, 3, 'tilt'),
    ('BVIIh$_{\\rm t,g}$', 42.1, 1, 'tilt'),
    ('BVIIh$_{\\rm t}$', 41.7, 1, 'tilt'),
    ('FLRW', 0.0, 1, 'ref'),
    ('orth\\_1D (6)', -0.9, 6, 'orth'),
    ('BVIIh$_{\\rm o}$', -1.0, 1, 'orth'),
    ('BVIIh$_{\\rm o,g}$', -19.0, 1, 'excl'),
    ('BV$_{\\rm t}$', -24.5, 1, 'excl'),
]

labels = [c[0] for c in classes]
lnBs = [c[1] for c in classes]
types = [c[3] for c in classes]

# Wong palette
colors = {
    'tilt': '#009E73',   # bluish green
    'ref': '#56B4E9',    # sky blue
    'orth': '#E69F00',   # orange
    'excl': '#CC79A7',   # reddish purple
}
bar_colors = [colors[t] for t in types]

fig, ax = plt.subplots(figsize=(8, 5))
y = np.arange(len(labels))

bars = ax.barh(y, lnBs, color=bar_colors, edgecolor='k', linewidth=0.5)

# Add value labels
for i, (v, bar) in enumerate(zip(lnBs, bars)):
    xpos = v + 1 if v >= 0 else v - 1
    ha = 'left' if v >= 0 else 'right'
    ax.text(xpos, i, f'{v:+.1f}', va='center', ha=ha, fontsize=12)

ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=13)
ax.set_xlabel('$\\ln\\mathcal{B}$ (CF4++ primary)', fontsize=16)
ax.set_title('Equivalence-class collapsed evidence', fontsize=18)
ax.axvline(x=0, color='k', linewidth=0.8, linestyle='-')
ax.axvline(x=5, color='grey', linewidth=0.5, linestyle='--', alpha=0.5)
ax.axvline(x=-5, color='grey', linewidth=0.5, linestyle='--', alpha=0.5)
ax.invert_yaxis()

# Legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=colors['tilt'], label='Tilted (decisive)'),
    Patch(facecolor=colors['ref'], label='FLRW reference'),
    Patch(facecolor=colors['orth'], label='Orthogonal (negligible)'),
    Patch(facecolor=colors['excl'], label='Excluded'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=11)

plt.tight_layout()
plt.savefig('fig_equiv_class_evidence.pdf', dpi=300, bbox_inches='tight')
plt.savefig('fig_equiv_class_evidence.png', dpi=300, bbox_inches='tight')
print("Saved fig_equiv_class_evidence.pdf/png")
