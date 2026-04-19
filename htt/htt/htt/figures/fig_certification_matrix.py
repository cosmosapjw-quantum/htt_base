#!/usr/bin/env python3
"""
fig_certification_matrix.py — Certification Matrix Figure
==========================================================
§5 new #1. Class-by-class status of x_max and F from MIO.

Visualizes the 5 ceiling families with their certification status:
  NUMERICALLY_CERTIFIED (green), ADOPTED (amber), BLOCKED (red).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / 'mio'))

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from mio.core.ceiling_families import CEILING_FAMILIES, CeilingStatus


def main():
    fig, ax = plt.subplots(figsize=(10, 5))

    families = list(CEILING_FAMILIES.values())
    names = [f.name.replace('_', '\n') for f in families]
    n_models = [len(f.models) for f in families]

    colors = []
    for f in families:
        if f.status == CeilingStatus.NUMERICALLY_CERTIFIED:
            colors.append('#009E73')  # green
        elif f.status == CeilingStatus.THEOREM_GRADE:
            colors.append('#0072B2')  # blue
        elif f.status == CeilingStatus.ADOPTED:
            colors.append('#E69F00')  # amber
        elif f.status == CeilingStatus.BLOCKED:
            colors.append('#D55E00')  # red
        else:
            colors.append('#999999')

    bars = ax.barh(range(len(families)), n_models, color=colors, edgecolor='k', linewidth=0.5)
    ax.set_yticks(range(len(families)))
    ax.set_yticklabels(names, fontsize=12)
    ax.set_xlabel('Number of models', fontsize=14)
    ax.set_title('Ceiling family certification matrix', fontsize=16)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#009E73', label='Numerically certified'),
        Patch(facecolor='#E69F00', label='Adopted (uncertified)'),
        Patch(facecolor='#D55E00', label='Blocked'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=11)

    ax.invert_yaxis()
    plt.tight_layout()

    outdir = Path(__file__).parent / 'output'
    outdir.mkdir(exist_ok=True)
    plt.savefig(outdir / 'fig_certification_matrix.png', dpi=300)
    print(f"Saved: {outdir / 'fig_certification_matrix.png'}")
    plt.close()


if __name__ == '__main__':
    main()
