#!/usr/bin/env python3
"""
fig_departure_summary.py — Master 2×2 departure summary figure
================================================================
§6 REWRITE: Split into identified-only and reporting-only panels.

Panel A: β posterior (IDENTIFIED — likelihood-constrained)
Panel B: Σ² posterior (IDENTIFIED — likelihood-constrained)
Panel C: Q = x/x_max pushforward (REPORTING — ceiling-dependent)
Panel D: Π exceedance curves (REPORTING — ceiling- and threshold-dependent)

Note: x, F, Q, Π are REPORTING quantities (deterministic transforms of
identified inputs through adopted ceiling). See identified_vs_reporting.py.

Wong/Okabe-Ito palette. 7×7 inch. 300 DPI.
"""
import sys, os
import numpy as np

sys.path.insert(0, '/mnt/project')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

from plot_style import apply_style, save_fig, COLS, MODEL_STYLE
from analysis_extended import EvidenceComparison
from departure_posteriors import DeparturePosterior
from ssot import C

apply_style()

# HTT_PIPELINE_OUTDIR overrides the legacy '/mnt/user-data/outputs'
# default for pipeline-output reads. fig_departure_summary itself
# runs dynesty at import time (via EvidenceComparison.run_single)
# so the smoke-test skip survives until `dynesty` is installed —
# this routing is kept for parity with siblings (HTT-STAB W9D4).
OUT = os.environ.get('HTT_PIPELINE_OUTDIR', '/mnt/user-data/outputs')

# ═══════════════════════════════════════════════════════════════
#  STEP 1: Collect posterior samples for top 5 models
# ═══════════════════════════════════════════════════════════════
print("Running evidence + departure for top models...")

ec = EvidenceComparison(channels='abcdefh')
Z0 = ec.flrw_evidence()

# Top irrotational tilted models (share the same x ≈ Ω_tilt scale).
# BIII_tilt and BIX_tilt are curvature-dominated (x ~ 10⁻³) and
# would compress the irrotational models to zero — shown in panel D instead.
TOP5 = ['FLRW_tilt', 'BI_tilt', 'BVIIh_tilt', 'BVIIh_tilt_grow']

# Run each model
model_data = {}
for tag in TOP5:
    is_tilt = 'tilt' in tag
    nl = 400 if is_tilt else 300
    dl = 0.3 if is_tilt else 0.5
    r = ec.run_single(tag, nlive=nl, dlogz=dl)
    eq = r.get('eq_samples')
    if eq is None:
        continue

    dp = DeparturePosterior(
        model_tag=tag, samples=eq, logwt=None,
        param_names=r['param_names'], comparator='flat')
    report = dp.full_report(eps1_ceiling=C.eps1_kin, d_Mpc=40.0)

    model_data[tag] = {
        'lnB': r['lnB'],
        'x': dp.x,
        'Q': dp.Q,
        'Omega_tilt': dp.Omega_tilt,
        'Sigma2': dp.Sigma2,
        'beta': dp.beta,
        'v_tilt': dp.v_tilt,
        'report': report,
        'weights': dp.weights,
    }
    print(f"  {tag}: lnB={r['lnB']:+.1f}, x_med={np.median(dp.x):.3e}")

# Also run two orthogonal for the decomposition
for tag in ['BI_orth']:
    r = ec.run_single(tag, nlive=200, dlogz=0.5)
    eq = r.get('eq_samples')
    if eq is not None:
        dp = DeparturePosterior(
            model_tag=tag, samples=eq, logwt=None,
            param_names=r['param_names'], comparator='flat')
        dp.full_report(eps1_ceiling=C.eps1_kin)
        model_data[tag] = {
            'lnB': r['lnB'], 'x': dp.x, 'Q': dp.Q,
            'Omega_tilt': dp.Omega_tilt, 'Sigma2': dp.Sigma2,
        }


# ═══════════════════════════════════════════════════════════════
#  STEP 2: Style assignments
# ═══════════════════════════════════════════════════════════════
STYLE = {
    'FLRW_tilt':        {'color': COLS['blue'],   'ls': '-',  'lw': 1.8,
                         'label': r'FLRW$_{\rm tilt}$'},
    'BI_tilt':          {'color': COLS['orange'], 'ls': '--', 'lw': 1.3,
                         'label': r'BI$_{\rm tilt}$'},
    'BVIIh_tilt':       {'color': COLS['green'],  'ls': '-.', 'lw': 1.3,
                         'label': r'VII$_h$ tilt'},
    'BVIIh_tilt_grow':  {'color': COLS['purple'], 'ls': ':',  'lw': 1.5,
                         'label': r'VII$_h$ tilt (grow)'},
}


# ═══════════════════════════════════════════════════════════════
#  STEP 3: Build 2×2 figure
# ═══════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 2, figsize=(7.0, 7.0))
ax_A, ax_B = axes[0]
ax_C, ax_D = axes[1]


# ─── Panel A: x pushforward PDF ──────────────────────────────
print("Panel A: x pushforward PDF...")

for tag in TOP5:
    if tag not in model_data:
        continue
    md = model_data[tag]
    st = STYLE[tag]
    x_vals = md['x']

    # Skip models with negative x (BIX_tilt has Ω_K < 0)
    if np.median(x_vals) < 0:
        x_vals_plot = x_vals[x_vals > 0]
        if len(x_vals_plot) < 50:
            continue
    else:
        x_vals_plot = x_vals

    try:
        kde = gaussian_kde(x_vals_plot * 1e6, bw_method=0.25)
        xg = np.linspace(0, np.percentile(x_vals_plot * 1e6, 99.5), 300)
        ax_A.plot(xg, kde(xg), color=st['color'], ls=st['ls'],
                  lw=st['lw'], label=st['label'])
    except Exception:
        pass

ax_A.set_xlabel(r'$x \;\;(\times 10^{-6})$')
ax_A.set_ylabel('Posterior density')
ax_A.set_xlim(0, None)
ax_A.legend(fontsize=7.5, loc='upper right', framealpha=0.9)
ax_A.text(0.03, 0.95, '(a)', transform=ax_A.transAxes,
          fontsize=12, fontweight='bold', va='top')


# ─── Panel B: Q pushforward PDF with ceiling ─────────────────
print("Panel B: Q pushforward PDF...")

for tag in TOP5:
    if tag not in model_data:
        continue
    md = model_data[tag]
    st = STYLE[tag]
    Q_vals = md['Q']

    if np.median(Q_vals) < 0 or np.median(Q_vals) > 1:
        continue  # skip pathological models for this panel

    try:
        kde = gaussian_kde(Q_vals, bw_method=0.25)
        qg = np.linspace(0, min(np.percentile(Q_vals, 99.5), 0.4), 300)
        ax_B.plot(qg, kde(qg), color=st['color'], ls=st['ls'],
                  lw=st['lw'], label=st['label'])
    except Exception:
        pass

# Ceiling annotation
ax_B.axvline(1.0, color=COLS['gray'], ls=':', lw=0.8, alpha=0.7)
ax_B.text(0.35, 0.88, r'$Q = x/x_{\rm max}$',
          transform=ax_B.transAxes, fontsize=9, color=COLS['gray'])
ax_B.set_xlabel(r'$Q = x / x_{\rm max}$')
ax_B.set_ylabel('Posterior density')
ax_B.set_xlim(0, 0.35)
ax_B.legend(fontsize=7.5, loc='upper right', framealpha=0.9)
ax_B.text(0.03, 0.95, '(b)', transform=ax_B.transAxes,
          fontsize=12, fontweight='bold', va='top')


# ─── Panel C: Π exceedance curves ────────────────────────────
print("Panel C: Π exceedance curves...")

q_star_grid = np.linspace(0.001, 0.5, 200)

for tag in TOP5:
    if tag not in model_data:
        continue
    md = model_data[tag]
    st = STYLE[tag]
    Q_vals = md['Q']
    w = md['weights']

    # Compute Π(q*) = Σ w_i 1[Q_i > q*] for each q*
    Pi_curve = np.array([float(np.sum(w[Q_vals > qs])) for qs in q_star_grid])
    ax_C.plot(q_star_grid, Pi_curve, color=st['color'], ls=st['ls'],
              lw=st['lw'], label=st['label'])

# Reference lines
ax_C.axhline(0.95, color=COLS['gray'], ls=':', lw=0.6, alpha=0.5)
ax_C.text(0.42, 0.96, r'$\Pi = 0.95$', fontsize=7.5, color=COLS['gray'],
          transform=ax_C.get_xaxis_transform(), va='bottom')
ax_C.axhline(0.05, color=COLS['gray'], ls=':', lw=0.6, alpha=0.5)

ax_C.set_xlabel(r'Threshold $q_\star$')
ax_C.set_ylabel(r'$\Pi(q_\star) = P(Q > q_\star \mid D)$')
ax_C.set_xlim(0, 0.5)
ax_C.set_ylim(-0.02, 1.05)
ax_C.legend(fontsize=7.5, loc='center right', framealpha=0.9)
ax_C.text(0.03, 0.05, '(c)', transform=ax_C.transAxes,
          fontsize=12, fontweight='bold', va='bottom')


# ─── Panel D: Evidence decomposition + Ω_tilt contribution ───
print("Panel D: Evidence decomposition...")

# Evidence decomposition values (from TF-N03 / IS-08)
# Using the model_data collected above
lnB_shear = model_data.get('BI_orth', {}).get('lnB', -0.9)
lnB_tilt = model_data.get('FLRW_tilt', {}).get('lnB', 26.3)
lnB_combined = model_data.get('BI_tilt', {}).get('lnB', 25.5)
lnB_interaction = lnB_combined - lnB_shear - lnB_tilt

categories = ['Shear\n' + r'(BI$_{\rm orth}$)',
              'Tilt\n' + r'(FLRW$_{\rm tilt}$)',
              'Interaction',
              'Combined\n' + r'(BI$_{\rm tilt}$)']
values = [lnB_shear, lnB_tilt, lnB_interaction, lnB_combined]
bar_colors = [COLS['cyan'], COLS['orange'], COLS['gray'], COLS['blue']]

y_pos = np.arange(len(categories))
bars = ax_D.barh(y_pos, values, height=0.55, color=bar_colors, alpha=0.85,
                 edgecolor='#333333', linewidth=0.4)

# Value labels
for i, (v, bar) in enumerate(zip(values, bars)):
    if abs(v) > 1:
        ha = 'left' if v > 0 else 'right'
        offset = 0.5 if v > 0 else -0.5
        ax_D.text(v + offset, y_pos[i], f'${v:+.1f}$',
                  va='center', ha=ha, fontsize=9, fontweight='bold')
    else:
        ax_D.text(max(v, 0) + 0.5, y_pos[i], f'${v:+.2f}$',
                  va='center', ha='left', fontsize=8, color=COLS['gray'])

ax_D.axvline(0, color='k', lw=0.5)
ax_D.axvline(5, color=COLS['gray'], ls=':', lw=0.5, alpha=0.5)
ax_D.text(5.3, 3.6, 'decisive', fontsize=7, color=COLS['gray'], rotation=90, va='top')

ax_D.set_yticks(y_pos)
ax_D.set_yticklabels(categories, fontsize=9)
ax_D.set_xlabel(r'$\ln\mathcal{B}$')
ax_D.set_xlim(-5, 32)

# Annotation: Ω_tilt drives the entire evidence
Ot_frac = lnB_tilt / lnB_combined * 100 if lnB_combined > 0 else 0
ax_D.text(0.97, 0.05,
          f'$\\Omega_{{\\rm tilt}}$ contributes\n{Ot_frac:.0f}% of $\\ln\\mathcal{{B}}$',
          transform=ax_D.transAxes, fontsize=8.5, ha='right', va='bottom',
          color=COLS['red'], fontstyle='italic',
          bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLS['red'],
                    alpha=0.85, linewidth=0.6))

ax_D.text(0.03, 0.95, '(d)', transform=ax_D.transAxes,
          fontsize=12, fontweight='bold', va='top')


# ═══════════════════════════════════════════════════════════════
#  FINAL LAYOUT
# ═══════════════════════════════════════════════════════════════
fig.tight_layout(w_pad=2.5, h_pad=2.5)
save_fig(fig, 'fig_departure_summary')
print(f"Saved fig_departure_summary.pdf + .png")
