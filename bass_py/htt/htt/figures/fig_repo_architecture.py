#!/usr/bin/env python3
"""
fig_repo_architecture.py — BASS/HTT/MIO/Workspace Data Flow
==============================================================
§5 new #3. Shows repo ownership and data flow between packages.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path


def main():
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis('off')

    # Boxes
    boxes = {
        'BASS': (0.5, 4.5, 3.5, 2.0, '#56B4E9'),
        'HTT':  (0.5, 1.5, 3.5, 2.0, '#E69F00'),
        'MIO':  (6.0, 3.0, 3.5, 2.0, '#009E73'),
        'WS':   (3.0, 0.0, 4.0, 1.0, '#999999'),
    }

    for name, (x, y, w, h, color) in boxes.items():
        rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.15',
                                        facecolor=color, alpha=0.2, edgecolor=color, lw=2)
        ax.add_patch(rect)
        label = {'BASS': 'BASS\nForward physics',
                 'HTT': 'HTT\nInference engine',
                 'MIO': 'MIO\nEpistemic control',
                 'WS': 'Workspace (contracts + runners)'}[name]
        ax.text(x + w/2, y + h/2, label, ha='center', va='center',
                fontsize=11, fontweight='bold')

    # Arrows
    arrows = [
        ((4.0, 5.5), (6.0, 4.5), 'R_σ, f₂/f₃'),
        ((4.0, 2.5), (6.0, 3.5), 'x, Q, Π, ln B'),
        ((2.25, 4.5), (2.25, 3.5), 'Family scan'),
    ]
    for (x1, y1), (x2, y2), label in arrows:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                     arrowprops=dict(arrowstyle='->', color='#333', lw=1.5))
        mx, my = (x1+x2)/2 + 0.3, (y1+y2)/2
        ax.text(mx, my, label, fontsize=9, ha='left', va='center', style='italic')

    ax.set_title('Repository ownership and data flow', fontsize=16, pad=15)
    plt.tight_layout()

    outdir = Path(__file__).parent / 'output'
    outdir.mkdir(exist_ok=True)
    plt.savefig(outdir / 'fig_repo_architecture.png', dpi=300)
    print(f"Saved: {outdir / 'fig_repo_architecture.png'}")
    plt.close()


if __name__ == '__main__':
    main()
