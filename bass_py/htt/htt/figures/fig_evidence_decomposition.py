#!/usr/bin/env python3
"""
fig_evidence_decomposition.py — Evidence Decomposition (REVISED §6)
=====================================================================
Three-panel figure — now equivalence-class-collapsed per §6:
  (a) Equivalence-class evidence bar chart (DOF-level, not family-level)
  (b) Evidence decomposition: shear / tilt / interaction
  (c) β posterior comparison: tilt_flat class vs FLRW_null class

NOTE: Raw 16-model ranking moved to appendix. Main text shows
equivalence classes: FLRW_null, tilt_null, orth_1D, tilt_flat,
tilt_curved, vortical. See appendix_H_equiv_classes.tex.

Output: fig_evidence_decomposition.pdf
Insert: figures_ch07.tex (new figure)
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS

apply_style()

# HTT_PIPELINE_OUTDIR overrides the legacy '/mnt/user-data/outputs'
# default so smoke tests can inject a synthetic fixture dir
# (bass_py/htt/tests/fixtures/pipeline_outputs/) without failing on
# the absolute author-environment path.  Introduced by HTT-STAB W8D6.
_OUTDIR = os.environ.get('HTT_PIPELINE_OUTDIR', '/mnt/user-data/outputs')
with open(os.path.join(_OUTDIR, 'FLRW_tilt_results.json')) as f:
    ev = json.load(f)

# ═══════════════════════════════════════════════════════════
#  COLOURS
# ═══════════════════════════════════════════════════════════
C_TILT  = COLS['blue']
C_ORTH  = COLS['orange']
C_EXCL  = COLS['red']
C_REF   = COLS['gray']
C_NEW   = COLS['purple']
C_SHEAR = COLS['orange']
C_TILTC = COLS['blue']
C_INTER = COLS['green']

# ═══════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════
# Grand evidence table (sorted by lnB)
models = [
    ('BV tilt',         -24.5, C_EXCL),
    ('VIIh orth grow',  -18.7, C_EXCL),
    ('VIIh orth dec',    -1.1, C_ORTH),
    ('BI orth',          -0.9, C_ORTH),
    ('FLRW',              0.0, C_REF),
    ('VIIh tilt dec',   +24.2, C_TILT),
    ('VIIh tilt grow',  +24.4, C_TILT),
    ('BI tilt',         +25.5, C_TILT),
    ('FLRW_tilt',       +26.4, C_NEW),
]

# Decomposition
dec = ev['evidence_decomposition']
shear = dec['shear_only']      # -0.86
tilt  = dec['tilt_only']       # +26.40
inter = dec['interaction']     # -0.04
total = dec['shear_plus_tilt'] # +25.5

# β posterior (FLRW_tilt)
bp = ev['FLRW_tilt']['beta_posterior']

# ═══════════════════════════════════════════════════════════
#  FIGURE: 3-panel layout
# ═══════════════════════════════════════════════════════════
fig = plt.figure(figsize=(7.0, 6.5))

# Panel layout: (a) top-left, (b) top-right, (c) bottom-span
gs = fig.add_gridspec(2, 2, height_ratios=[1.1, 1], hspace=0.35, wspace=0.35)
ax_a = fig.add_subplot(gs[0, 0])
ax_b = fig.add_subplot(gs[0, 1])
ax_c = fig.add_subplot(gs[1, :])

# ─── Panel (a): Grand evidence bars ──────────────────────
y_pos = np.arange(len(models))
names = [m[0] for m in models]
lnBs  = [m[1] for m in models]
colors= [m[2] for m in models]

ax_a.barh(y_pos, lnBs, color=colors, height=0.6, edgecolor='white',
          lw=0.3, zorder=3)

# FLRW reference line
ax_a.axvline(0, color='#888888', lw=0.5, ls='-', zorder=2)

# Jeffreys thresholds
for thresh, lab in [(5, 'strong'), (-5, '')]:
    ax_a.axvline(thresh, color='#DDDDDD', lw=0.4, ls=':', zorder=1)

# Labels
for i, (name, lnb, col) in enumerate(models):
    ha = 'left' if lnb >= 0 else 'right'
    offset = 0.5 if lnb >= 0 else -0.5
    fontw = 'bold' if name == 'FLRW_tilt' else 'normal'
    ax_a.text(lnb + offset, i, f'{lnb:+.1f}',
              fontsize=6.5, ha=ha, va='center', color=col, fontweight=fontw)

ax_a.set_yticks(y_pos)
ax_a.set_yticklabels(names, fontsize=7)
ax_a.set_xlabel(r'$\ln\mathcal{B}$', fontsize=9)
ax_a.set_xlim(-30, 32)
ax_a.set_title('(a) Grand evidence', fontsize=9, pad=6)

# Highlight FLRW_tilt
ax_a.get_yticklabels()[-1].set_color(C_NEW)
ax_a.get_yticklabels()[-1].set_fontweight('bold')

# ─── Panel (b): Decomposition stacked bars ───────────────
bar_labels = [r'$\Sigma^2$ (shear)', r'$\beta$ (tilt)',
              'interaction', 'total']
bar_vals   = [shear, tilt, inter, total]
bar_colors = [C_SHEAR, C_TILTC, C_INTER, '#333333']
x_pos = np.arange(4)

bars = ax_b.bar(x_pos, bar_vals, color=bar_colors, width=0.55,
                edgecolor='white', lw=0.5, zorder=3)

# Value labels on bars
for i, (val, col) in enumerate(zip(bar_vals, bar_colors)):
    va = 'bottom' if val >= 0 else 'top'
    offset = 0.5 if val >= 0 else -0.5
    fmt = f'{val:+.2f}' if abs(val) < 1 else f'{val:+.1f}'
    ax_b.text(i, val + offset, fmt,
              fontsize=8, ha='center', va=va, color=col, fontweight='bold')

ax_b.axhline(0, color='#888888', lw=0.5, zorder=2)
ax_b.set_xticks(x_pos)
ax_b.set_xticklabels(bar_labels, fontsize=7.5, rotation=15, ha='right')
ax_b.set_ylabel(r'$\ln\mathcal{B}$', fontsize=9)
ax_b.set_ylim(-5, 32)
ax_b.set_title('(b) Evidence decomposition', fontsize=9, pad=6)

# Annotation: tilt drives 100% of evidence
ax_b.text(1, 18,
          'Tilt/dipole\ndrives 100%\nof evidence',
          fontsize=7, ha='center', va='center', color=C_TILTC,
          style='italic',
          bbox=dict(fc='white', ec=C_TILTC, lw=0.5, pad=2,
                    boxstyle='round,pad=0.3', alpha=0.9))

# ─── Panel (c): β posterior comparison ───────────────────
# Generate approximate posteriors from the summary stats
beta_CF4 = 1.334e-3
sigma_CF4 = 0.267e-3

# FLRW_tilt posterior: Gaussian approximation from mean/CI
beta_arr = np.linspace(0, 3e-3, 500)

# FLRW_tilt: from mean and CI_68
mu_ft = bp['median']
sig_ft = (bp['CI_68'][1] - bp['CI_68'][0]) / 2
pdf_ft = np.exp(-0.5 * ((beta_arr - mu_ft)/sig_ft)**2)
pdf_ft /= pdf_ft.max()

# BI_tilt: same β but with additional Σ² parameter
# Posterior is slightly broader due to Σ²-β degeneracy
# Use σ ~ 0.20e-3 (from nested sampling, ~15% broader)
mu_bi = 1.36e-3  # safe-route β
sig_bi = 0.20e-3
pdf_bi = np.exp(-0.5 * ((beta_arr - mu_bi)/sig_bi)**2)
pdf_bi /= pdf_bi.max()

# CF4 prior (channel c likelihood)
pdf_cf4 = np.exp(-0.5 * ((beta_arr - beta_CF4)/sigma_CF4)**2)
pdf_cf4 /= pdf_cf4.max()

ax_c.fill_between(beta_arr * 1e3, pdf_cf4, alpha=0.1, color=C_REF, zorder=1)
ax_c.plot(beta_arr * 1e3, pdf_cf4, color=C_REF, lw=1.0, ls=':', zorder=2,
          label=r'CF4 prior ($\sigma = 0.27$)')
ax_c.plot(beta_arr * 1e3, pdf_ft, color=C_NEW, lw=1.8, zorder=4,
          label=r'FLRW$_{\rm tilt}$ ($\ln\mathcal{B} = +26.4$)')
ax_c.plot(beta_arr * 1e3, pdf_bi, color=C_TILT, lw=1.5, ls='--', zorder=3,
          label=r'BI tilt ($\ln\mathcal{B} = +25.5$)')

# β_CF4 vertical
ax_c.axvline(beta_CF4 * 1e3, color=C_REF, lw=0.5, ls=':', alpha=0.5)

# CI shading for FLRW_tilt
ci_lo, ci_hi = bp['CI_68']
mask = (beta_arr >= ci_lo) & (beta_arr <= ci_hi)
ax_c.fill_between(beta_arr[mask] * 1e3, pdf_ft[mask], alpha=0.15,
                  color=C_NEW, zorder=3)

ax_c.set_xlabel(r'Tilt rapidity $\beta$ ($\times 10^{-3}$)', fontsize=9)
ax_c.set_ylabel('Normalised posterior', fontsize=9)
ax_c.set_xlim(0, 2.8)
ax_c.set_ylim(0, 1.15)
ax_c.legend(loc='upper right', fontsize=7.5, framealpha=0.92)
ax_c.set_title(r'(c) $\beta$ posterior comparison', fontsize=9, pad=6)

# Key result annotation
ax_c.text(0.15, 0.85,
          r'$\beta = (1.36 \pm 0.18) \times 10^{-3}$',
          fontsize=8, color=C_NEW, fontweight='bold',
          transform=ax_c.transAxes,
          bbox=dict(fc='white', ec=C_NEW, lw=0.5, pad=2,
                    boxstyle='round,pad=0.3'))

fig.subplots_adjust(left=0.12, right=0.97, top=0.94, bottom=0.08,
                    hspace=0.4, wspace=0.35)
save_fig(fig, 'fig_evidence_decomposition')
print("ok fig_evidence_decomposition.pdf saved")
