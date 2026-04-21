#!/usr/bin/env python3
"""
fig_cf4pp_sensitivity.py — CF4 vs CF4++ vs WFH2009 β Sensitivity
=================================================================
P-25 deliverable. Shows lnB vs β for the three CF4 compilations.
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from plot_style import apply_style

def main() -> None:
    apply_style()

    # Three CF4 versions
    versions = {
        'WFH2009\n(legacy)': {'beta': 1.334e-3, 'sigma': 0.267e-3, 'lnB': 26.3, 'color': '#E69F00'},
        'Watkins+2023': {'beta': 1.318e-3, 'sigma': 0.097e-3, 'lnB': 105.8, 'color': '#56B4E9'},
        'CF4++\n(primary)': {'beta': 1.051e-3, 'sigma': 0.133e-3, 'lnB': 44.0, 'color': '#009E73'},
    }

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left panel: β ± σ
    names = list(versions.keys())
    betas = [v['beta']*1e3 for v in versions.values()]
    sigmas = [v['sigma']*1e3 for v in versions.values()]
    colors = [v['color'] for v in versions.values()]
    y = np.arange(len(names))

    ax1.barh(y, betas, xerr=sigmas, color=colors, edgecolor='k',
             linewidth=0.5, capsize=4)
    ax1.set_yticks(y)
    ax1.set_yticklabels(names, fontsize=13)
    ax1.set_xlabel('$\\beta \\times 10^{3}$', fontsize=16)
    ax1.set_title('Tilt rapidity', fontsize=18)
    ax1.invert_yaxis()

    # Right panel: lnB
    lnBs = [v['lnB'] for v in versions.values()]
    ax2.barh(y, lnBs, color=colors, edgecolor='k', linewidth=0.5)
    for i, v in enumerate(lnBs):
        ax2.text(v + 2, i, f'{v:+.1f}', va='center', fontsize=12)
    ax2.set_yticks(y)
    ax2.set_yticklabels(names, fontsize=13)
    ax2.set_xlabel('$\\ln\\mathcal{B}$ (FLRW$_{\\rm tilt}$)', fontsize=16)
    ax2.set_title('Evidence', fontsize=18)
    ax2.axvline(x=5, color='grey', linewidth=0.5, linestyle='--', alpha=0.5)
    ax2.invert_yaxis()

    plt.tight_layout()
    outdir = Path(__file__).parent / 'output'
    outdir.mkdir(exist_ok=True)
    plt.savefig(outdir / 'fig_cf4pp_sensitivity.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(outdir / 'fig_cf4pp_sensitivity.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {outdir / 'fig_cf4pp_sensitivity.pdf'}")
    print(f"Saved: {outdir / 'fig_cf4pp_sensitivity.png'}")
    plt.close(fig)


if __name__ == '__main__':
    main()
