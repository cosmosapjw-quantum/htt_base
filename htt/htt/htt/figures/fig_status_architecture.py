#!/usr/bin/env python3
"""
fig_status_architecture.py — Report Status Architecture Figure
================================================================
§5 new #2. Shows the four-block report structure:
  EXACT → CONDITIONAL → INFERENTIAL → EXPLORATORY
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


def main():
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 4)
    ax.axis('off')

    blocks = [
        ('EXACT', 0.5, '#009E73', 'Ch. 2: Defect algebra\nThm/Prop/Def'),
        ('CONDITIONAL', 3.5, '#56B4E9', 'Ch. 3,5: MES bounds\nCertification, T_eff'),
        ('INFERENTIAL', 6.5, '#E69F00', 'Ch. 4,6,7: Evidence\nEquiv classes, Nulls'),
        ('EXPLORATORY', 9.5, '#D55E00', 'Ch. 8,9: Bridge\nΔH, q₀, λ_J'),
    ]

    for name, x, color, desc in blocks:
        rect = mpatches.FancyBboxPatch((x, 0.8), 2.5, 2.4, boxstyle='round,pad=0.1',
                                        facecolor=color, alpha=0.3, edgecolor=color, linewidth=2)
        ax.add_patch(rect)
        ax.text(x + 1.25, 2.6, name, ha='center', va='center',
                fontsize=13, fontweight='bold', color=color)
        ax.text(x + 1.25, 1.6, desc, ha='center', va='center',
                fontsize=9, color='#333333')

    # Arrows between blocks
    for i in range(3):
        x1 = blocks[i][1] + 2.5
        x2 = blocks[i+1][1]
        ax.annotate('', xy=(x2, 2.0), xytext=(x1, 2.0),
                     arrowprops=dict(arrowstyle='->', color='#666666', lw=1.5))

    ax.set_title('Report status architecture', fontsize=16, pad=15)
    plt.tight_layout()

    outdir = Path(__file__).parent / 'output'
    outdir.mkdir(exist_ok=True)
    plt.savefig(outdir / 'fig_status_architecture.png', dpi=300)
    print(f"Saved: {outdir / 'fig_status_architecture.png'}")
    plt.close()


if __name__ == '__main__':
    main()
