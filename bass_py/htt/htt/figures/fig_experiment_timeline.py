#!/usr/bin/env python3
"""
fig_experiment_timeline.py — Experiment-to-Claim Forecast (REVISED §6)
==========================================================================
§6 REWRITE: Updated experiment statuses and mapped to claim-status labels.
Each experiment is now tied to a specific status-tested claim per §5.
Predictions attached to status labels, not rhetoric.

Status mapping:
  Rubin LSST: INFERENTIAL (anomaly adjudication via photometric dipole)
  Euclid DR1: INFERENTIAL (BAO curvature test → equiv-class breaking)
  SPHEREx: CONDITIONAL (near-IR dipole cross-check)
  SKAO: INFERENTIAL (radio continuum dipole at higher precision)
  LiteBIRD: CONDITIONAL (CMB B-mode → vorticity bound update)
  CMB-S4: CONDITIONAL (improved low-ℓ quadrupole → MES bound)

Output: fig_experiment_timeline.pdf
"""
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import sys, os
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS

apply_style()

C_CMB = COLS['blue']
C_LSS = COLS['orange']
C_NEW = COLS['purple']

# (name, start, end, category, full_label, alpha)
# New predictions shown via colour in the figure; the label is a single
# pre-formatted string rendered once.
experiments = [
    ('Simons Obs (SAT)',  2024.5, 2031,   'cmb', 'P4, P5',               1.0, False),
    ('Simons Obs (LAT)',  2024.5, 2034,   'cmb', 'P5, P6',               1.0, False),
    ('LiteBIRD',          2033.5, 2037,   'cmb', 'P1, P2, P4, P5',      0.45, False),
    ('Euclid',            2023.5, 2029.5, 'lss', 'P1, P3, P7, P9',      1.0, True),
    ('DESI',              2021.0, 2026.5, 'lss', 'P7, P8',               1.0, True),
    ('Vera Rubin LSST',   2025.5, 2035.5, 'lss', 'P3, P7, P8, P11',    1.0, True),
    ('SPHEREx',           2025.0, 2027.5, 'lss', 'P1, P7',               1.0, False),
    ('eROSITA',           2019.5, 2028,   'lss', 'P6, P10',              1.0, True),
    ('SKA Phase 1',       2027.5, 2034,   'lss', 'P3, P7, P10',          0.65, True),
]

milestones = [
    (2025.5, 'Rubin\nfirst light'),
    (2026.8, 'Euclid\nDR1'),
]

fig, ax = plt.subplots(figsize=(7.0, 4.0))

n = len(experiments)
y_pos = list(range(n - 1, -1, -1))
bar_h = 0.5

for yi, (name, t0, t1, cat, label, alpha, has_new) in zip(y_pos, experiments):
    col = C_CMB if cat == 'cmb' else C_LSS
    ax.barh(yi, t1 - t0, left=t0, height=bar_h,
            color=col, alpha=alpha, edgecolor=col, lw=0.5, zorder=3)

    # Name (left)
    ax.text(t0 - 0.15, yi, name, fontsize=7.5, ha='right', va='center',
            color='#333333')

    # Label (right) — single text, with colour indicating new predictions
    label_col = C_NEW if has_new else '#666666'
    label_wt = 'bold' if has_new else 'normal'
    ax.text(t1 + 0.2, yi, label,
            fontsize=7, ha='left', va='center',
            color=label_col, fontweight=label_wt)

# ── CMB / LSS separator ──
sep_y = y_pos[2] - 0.45
ax.axhline(sep_y, color='#E0E0E0', lw=0.6, xmin=0.02, xmax=0.98)
ax.text(2019.3, sep_y + 0.15, 'CMB', fontsize=6.5, color=C_CMB,
        style='italic', va='bottom')
ax.text(2019.3, sep_y - 0.15, 'LSS', fontsize=6.5, color=C_LSS,
        style='italic', va='top')

# ── Decisive windows ──
ax.axvspan(2027, 2030, color=COLS['green'], alpha=0.06, zorder=0)
ax.axvspan(2029, 2032, color=C_NEW, alpha=0.04, zorder=0)

ax.text(2027.2, -0.75, '2027–2030\ndecisive window',
        fontsize=7, ha='left', va='top', color=COLS['green'],
        style='italic')
ax.text(2031.5, -0.75, '2029–2032\ntilted-FLRW window',
        fontsize=7, ha='left', va='top', color=C_NEW,
        style='italic')

# ── Milestones ──
for year, label in milestones:
    ax.axvline(year, color='#CCCCCC', lw=0.5, ls=':', zorder=1)
    ax.text(year, n - 0.5, label, fontsize=6, ha='center', va='bottom',
            color='#999999')

# ── Axes ──
ax.set_xlim(2019, 2038.5)
ax.set_ylim(-1.5, n + 0.2)
ax.set_yticks([])
ax.set_xlabel('Year')
ax.set_xticks(range(2020, 2039, 2))

# ── Legend ──
handles = [
    Patch(fc=C_CMB, alpha=0.9, label='CMB'),
    Patch(fc=C_LSS, alpha=0.9, label='LSS'),
    Patch(fc=C_CMB, alpha=0.4, label='Funded (not yet obs.)'),
]

ax.legend(handles=handles, loc='upper right', fontsize=7,
          framealpha=0.92, ncol=1)

# Note about purple labels
ax.text(2038.3, n - 1.8,
        'Bold purple labels\ninclude P8–P11\n(tilted-FLRW)',
        fontsize=6, ha='right', va='top', color=C_NEW,
        style='italic',
        bbox=dict(fc='white', ec=C_NEW, lw=0.6, pad=2,
                  boxstyle='round,pad=0.3', alpha=0.9))

fig.tight_layout()
save_fig(fig, 'fig_experiment_timeline')
print("ok fig_experiment_timeline.pdf saved")
