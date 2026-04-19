#!/usr/bin/env python3
"""
fig_v_pushforward.py — Derived observable and departure component comparison
==============================================================================
Panel A: v_tilt pushforward PDF — LABELED "derived physical observable"
Panel B: Ω_tilt pushforward PDF — LABELED "framework departure component"
Panel C: β comparison (SS 7-channel vs catalog 3D)

Ontology enforcement:
  v_tilt = c × tanh(β)         → derived physical observable
  Ω_tilt = (1+w)Ω_m sinh²β    → departure identity component

These two must NEVER be conflated (IS-22 hostile review criterion #9).
"""
import sys, os
from pathlib import Path
import numpy as np

sys.path.insert(0, '/mnt/project')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde

from plot_style import apply_style, save_fig, COLS
from ssot import C

apply_style()

c_kms = 299792.458

# HTT_PIPELINE_OUTDIR overrides the legacy '/mnt/user-data/outputs'
# default so smoke tests can inject a synthetic fixture
# (bass_py/htt/tests/fixtures/pipeline_outputs/IS06_3D_posterior.npz)
# without failing on the absolute author-environment path. Introduced
# by HTT-STAB W9D4.
_OUTDIR = os.environ.get('HTT_PIPELINE_OUTDIR', '/mnt/user-data/outputs')

# ─── Load posteriors ──────────────────────────────────────────
# IS-06 catalog 3D posterior (best seed)
cat_data = np.load(os.path.join(_OUTDIR, 'IS06_3D_posterior.npz'))
beta_cat = cat_data['beta']

# SS FLRW_tilt posterior
_beta_ss_path = Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'beta_ss_samples.npy'
beta_ss = np.load(str(_beta_ss_path)) if _beta_ss_path.exists() else beta_cat

# ─── Compute derived quantities ───────────────────────────────
# v_tilt
v_cat = c_kms * np.tanh(beta_cat)
v_ss  = c_kms * np.tanh(beta_ss)

# Ω_tilt = (1+w) Ω_m sinh²β
w = 0.0
Om = C.Omega_m
Otilt_cat = (1 + w) * Om * np.sinh(beta_cat)**2
Otilt_ss  = (1 + w) * Om * np.sinh(beta_ss)**2


# ─── Figure: 1×3 ─────────────────────────────────────────────
fig, (ax_A, ax_B, ax_C) = plt.subplots(1, 3, figsize=(7.0, 3.0))


# ─── Panel A: v_tilt PDF ─────────────────────────────────────
kde_v_ss = gaussian_kde(v_ss, bw_method=0.25)
kde_v_cat = gaussian_kde(v_cat, bw_method=0.25)
vg = np.linspace(0, max(v_ss.max(), v_cat.max()) * 1.1, 300)

ax_A.plot(vg, kde_v_ss(vg), color=COLS['blue'], lw=1.5,
          label='SS (7-channel)')
ax_A.fill_between(vg, kde_v_ss(vg), alpha=0.12, color=COLS['blue'])
ax_A.plot(vg, kde_v_cat(vg), color=COLS['orange'], lw=1.3, ls='--',
          label='Catalog (3D)')
ax_A.fill_between(vg, kde_v_cat(vg), alpha=0.08, color=COLS['orange'])

# CF4 reference
v_CF4 = c_kms * np.tanh(1.334e-3)
ax_A.axvline(v_CF4, color=COLS['red'], ls=':', lw=0.8, alpha=0.7)
ax_A.text(v_CF4 + 10, max(kde_v_ss(vg)) * 0.85,
          f'CF4\n{v_CF4:.0f} km/s', fontsize=7, color=COLS['red'])

ax_A.set_xlabel(r'$v_{\rm tilt} = c\,\tanh\beta$ [km/s]')
ax_A.set_ylabel('Posterior density')
ax_A.set_xlim(0, None)
ax_A.legend(fontsize=7, loc='upper right', framealpha=0.9)

# Ontology label
ax_A.text(0.5, 0.98, 'derived physical observable',
          transform=ax_A.transAxes, fontsize=7, fontstyle='italic',
          color=COLS['gray'], ha='center', va='top')

ax_A.text(0.04, 0.90, '(a)', transform=ax_A.transAxes,
          fontsize=11, fontweight='bold', va='top')


# ─── Panel B: Ω_tilt PDF ─────────────────────────────────────
kde_O_ss = gaussian_kde(Otilt_ss * 1e6, bw_method=0.25)
kde_O_cat = gaussian_kde(Otilt_cat * 1e6, bw_method=0.25)
og = np.linspace(0, max(Otilt_ss.max(), Otilt_cat.max()) * 1e6 * 1.15, 300)

ax_B.plot(og, kde_O_ss(og), color=COLS['blue'], lw=1.5,
          label='SS (7-channel)')
ax_B.fill_between(og, kde_O_ss(og), alpha=0.12, color=COLS['blue'])
ax_B.plot(og, kde_O_cat(og), color=COLS['orange'], lw=1.3, ls='--',
          label='Catalog (3D)')
ax_B.fill_between(og, kde_O_cat(og), alpha=0.08, color=COLS['orange'])

# Ω_tilt at CF4
Otilt_CF4 = (1 + w) * Om * np.sinh(1.334e-3)**2
ax_B.axvline(Otilt_CF4 * 1e6, color=COLS['red'], ls=':', lw=0.8, alpha=0.7)

ax_B.set_xlabel(r'$\Omega_{\rm tilt}\;\;(\times 10^{-6})$')
ax_B.set_ylabel('Posterior density')
ax_B.set_xlim(0, None)
ax_B.legend(fontsize=7, loc='upper right', framealpha=0.9)

# Ontology label
ax_B.text(0.5, 0.98, 'departure identity component',
          transform=ax_B.transAxes, fontsize=7, fontstyle='italic',
          color=COLS['gray'], ha='center', va='top')

ax_B.text(0.04, 0.90, '(b)', transform=ax_B.transAxes,
          fontsize=11, fontweight='bold', va='top')


# ─── Panel C: β comparison SS vs catalog ──────────────────────
kde_b_ss = gaussian_kde(beta_ss * 1e3, bw_method=0.25)
kde_b_cat = gaussian_kde(beta_cat * 1e3, bw_method=0.25)
bg = np.linspace(0, max(beta_ss.max(), beta_cat.max()) * 1e3 * 1.15, 300)

ax_C.plot(bg, kde_b_ss(bg), color=COLS['blue'], lw=1.5,
          label='SS (7-channel)')
ax_C.fill_between(bg, kde_b_ss(bg), alpha=0.12, color=COLS['blue'])
ax_C.plot(bg, kde_b_cat(bg), color=COLS['orange'], lw=1.3, ls='--',
          label='Catalog (3D)')
ax_C.fill_between(bg, kde_b_cat(bg), alpha=0.08, color=COLS['orange'])

# CF4 reference
ax_C.axvline(1.334, color=COLS['red'], ls=':', lw=0.8, alpha=0.7)
ax_C.text(1.38, max(kde_b_ss(bg)) * 0.85,
          r'$\beta_{\rm CF4}$', fontsize=8, color=COLS['red'])

# Hellinger annotation
from catalog_likelihood import hellinger_distance
H = hellinger_distance(beta_ss, beta_cat)
ax_C.text(0.97, 0.75, f'$H = {H:.2f}$',
          transform=ax_C.transAxes, fontsize=8.5, ha='right',
          bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                    edgecolor=COLS['gray'], alpha=0.9))

ax_C.set_xlabel(r'$\beta\;\;(\times 10^{-3})$')
ax_C.set_ylabel('Posterior density')
ax_C.set_xlim(0, None)
ax_C.legend(fontsize=7, loc='upper right', framealpha=0.9)

ax_C.text(0.04, 0.90, '(c)', transform=ax_C.transAxes,
          fontsize=11, fontweight='bold', va='top')


# ═══════════════════════════════════════════════════════════════
fig.tight_layout(w_pad=2.0)
save_fig(fig, 'fig_v_pushforward')
print("Saved fig_v_pushforward.pdf + .png")
