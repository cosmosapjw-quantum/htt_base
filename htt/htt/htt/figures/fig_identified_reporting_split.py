#!/usr/bin/env python3
"""
fig_identified_reporting_split.py — Identified vs Reporting Split
===================================================================
§5 new #5. Two-panel figure showing which quantities are identified
(likelihood-constrained) vs reporting (derived, ceiling-dependent).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / 'mio'))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mio.reporting.identified_vs_reporting import QUANTITY_REGISTRY, QuantityType


def main():
    identified = {k: v for k, v in QUANTITY_REGISTRY.items()
                  if v.quantity_type == QuantityType.IDENTIFIED}
    reporting = {k: v for k, v in QUANTITY_REGISTRY.items()
                 if v.quantity_type == QuantityType.REPORTING}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel 1: Identified
    names_id = [f"${v.symbol}$  ({k})" for k, v in identified.items()]
    ax1.barh(range(len(names_id)), [1]*len(names_id),
             color='#009E73', alpha=0.4, edgecolor='#009E73')
    ax1.set_yticks(range(len(names_id)))
    ax1.set_yticklabels(names_id, fontsize=12)
    ax1.set_xlim(0, 1.5)
    ax1.set_xticks([])
    ax1.set_title('Identified\n(likelihood-constrained)', fontsize=14, color='#009E73')
    ax1.invert_yaxis()
    for i, (k, v) in enumerate(identified.items()):
        ax1.text(1.05, i, v.physical_interpretation[:35], fontsize=9, va='center')

    # Panel 2: Reporting
    names_rp = [f"${v.symbol}$  ({k})" for k, v in reporting.items()]
    colors_rp = ['#D55E00' if v.ceiling_dependent else '#E69F00' for v in reporting.values()]
    ax2.barh(range(len(names_rp)), [1]*len(names_rp),
             color=colors_rp, alpha=0.4, edgecolor=colors_rp)
    ax2.set_yticks(range(len(names_rp)))
    ax2.set_yticklabels(names_rp, fontsize=12)
    ax2.set_xlim(0, 1.5)
    ax2.set_xticks([])
    ax2.set_title('Reporting\n(derived, ceiling-dependent)', fontsize=14, color='#D55E00')
    ax2.invert_yaxis()
    for i, (k, v) in enumerate(reporting.items()):
        txt = '⚠ ' + v.warning[:30] if v.warning else v.physical_interpretation[:30]
        ax2.text(1.05, i, txt, fontsize=8, va='center')

    plt.suptitle('Identified vs reporting posterior quantities', fontsize=16, y=1.02)
    plt.tight_layout()

    outdir = Path(__file__).parent / 'output'
    outdir.mkdir(exist_ok=True)
    plt.savefig(outdir / 'fig_identified_reporting_split.png', dpi=300, bbox_inches='tight')
    print(f"Saved: {outdir / 'fig_identified_reporting_split.png'}")
    plt.close()


if __name__ == '__main__':
    main()
