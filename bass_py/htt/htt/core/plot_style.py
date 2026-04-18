#!/usr/bin/env python3
"""
plot_style.py — Unified Figure Style for the Bianchi Defect Manuscript
======================================================================
Target: PRD / CQG / JCAP (single-col 3.4", double-col 7.0")

Usage:
    from plot_style import apply_style, SC, COLS, save_fig, FIG_1COL, FIG_2COL

    apply_style()
    fig, ax = plt.subplots(figsize=FIG_1COL)
    ax.plot(x, y, **SC['S3'])
    save_fig(fig, 'fig_myplot')
"""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

__all__ = [
    'apply_style', 'save_fig',
    'FIG_1COL', 'FIG_2COL', 'FIG_2COL_TALL', 'FIG_2COL_WIDE',
    'COLS', 'SC', 'MODEL_STYLE', 'TIER_COLOR',
]

# ═══════════════════════════════════════════════════════════
#  FIGURE SIZES (inches)
# ═══════════════════════════════════════════════════════════
FIG_1COL      = (3.4, 2.8)     # single-column default
FIG_1COL_TALL = (3.4, 3.4)     # single-column square
FIG_2COL      = (7.0, 2.8)     # double-column default (3 panels)
FIG_2COL_TALL = (7.0, 4.5)     # double-column tall (bar chart)
FIG_2COL_WIDE = (7.0, 3.2)     # double-column wider

# ═══════════════════════════════════════════════════════════
#  OKABE-ITO COLORBLIND-SAFE PALETTE
# ═══════════════════════════════════════════════════════════
COLS = {
    'blue':    '#0072B2',
    'orange':  '#E69F00',
    'green':   '#009E73',
    'red':     '#D55E00',
    'purple':  '#CC79A7',
    'cyan':    '#56B4E9',
    'yellow':  '#F0E442',
    'black':   '#000000',
    'gray':    '#999999',
}

# ═══════════════════════════════════════════════════════════
#  SCENARIO STYLES (colour + marker + linestyle)
# ═══════════════════════════════════════════════════════════
SC = {
    'S0':  {'color': COLS['gray'],   'marker': 'x',  'ls': ':',  'lw': 0.8, 'ms': 4, 'label': 'S0 (FLRW)'},
    'S1':  {'color': COLS['blue'],   'marker': 'o',  'ls': '-',  'lw': 1.0, 'ms': 4, 'label': 'S1 (F&Q)'},
    'S2a': {'color': COLS['orange'], 'marker': 's',  'ls': '-',  'lw': 1.0, 'ms': 4, 'label': 'S2a (CatWISE)'},
    'S2b': {'color': COLS['green'],  'marker': 'D',  'ls': '--', 'lw': 1.0, 'ms': 4, 'label': 'S2b (kin)'},
    'S2c': {'color': COLS['red'],    'marker': '^',  'ls': '--', 'lw': 1.0, 'ms': 4, 'label': 'S2c (radio)'},
    'S3':  {'color': COLS['purple'], 'marker': 'v',  'ls': '-',  'lw': 1.2, 'ms': 5, 'label': 'S3 (full)'},
}

# ═══════════════════════════════════════════════════════════
#  MODEL STYLES (for evidence comparison figures)
# ═══════════════════════════════════════════════════════════
MODEL_STYLE = {
    'BI_tilt':          {'color': COLS['blue'],   'marker': 'o', 'label': 'BI'},
    'BIII_tilt':        {'color': COLS['green'],  'marker': 's', 'label': 'BIII'},
    'BIX_tilt':         {'color': COLS['orange'], 'marker': 'D', 'label': 'BIX'},
    'BVIIh_tilt':       {'color': COLS['red'],    'marker': '^', 'label': r'BVII$_h$'},
    'BVIIh_tilt_grow':  {'color': COLS['purple'], 'marker': 'v', 'label': r'BVII$_h$ (grow)'},
    'BV_tilt':          {'color': '#8B0000',      'marker': 'X', 'label': 'BV'},
    'BVIIh_orth':       {'color': COLS['cyan'],   'marker': 'p', 'label': r'BVII$_h$ (orth)'},
}

TIER_COLOR = {
    'decisive':  COLS['blue'],
    'negligible': COLS['gray'],
    'excluded':  COLS['red'],
}

# ═══════════════════════════════════════════════════════════
#  STYLE APPLICATION
# ═══════════════════════════════════════════════════════════
def apply_style():
    """Apply unified journal style to all subsequent figures."""
    plt.rcParams.update({
        # Font
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'DejaVu Serif', 'serif'],
        'mathtext.fontset': 'dejavuserif',

        # Sizes
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 9,
        'legend.title_fontsize': 10,

        # Axes
        'axes.linewidth': 0.7,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'xtick.minor.width': 0.4,
        'ytick.minor.width': 0.4,
        'xtick.major.size': 4.0,
        'ytick.major.size': 4.0,
        'xtick.minor.size': 2.0,
        'ytick.minor.size': 2.0,
        'xtick.direction': 'in',
        'ytick.direction': 'in',
        'xtick.top': True,
        'ytick.right': True,

        # Lines
        'lines.linewidth': 1.0,
        'lines.markersize': 4,

        # Legend
        'legend.framealpha': 0.92,
        'legend.edgecolor': '#cccccc',
        'legend.handlelength': 1.5,

        # Figure
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.03,
    })


def save_fig(fig, name, outdir=None):
    """Save figure as PNG + PDF.
    
    Args:
        fig: matplotlib Figure
        name: filename without extension
        outdir: output directory (default: /mnt/user-data/outputs/)
    """
    d = outdir or '/mnt/user-data/outputs'
    for ext in ['png', 'pdf']:
        fig.savefig(f'{d}/{name}.{ext}', dpi=300, bbox_inches='tight', pad_inches=0.03)
    plt.close(fig)
