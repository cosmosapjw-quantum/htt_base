#!/usr/bin/env python3
"""
fig_colin_beta.py — Colin dipolar-q to tilt rapidity translation
================================================================
β_SNe(z) = 9|q_d|z³exp(−z/S) with β_CF4 band and ratio axis.

Output: fig_colin_beta.pdf
Insert: figures_ch08.tex, referenced in §8.3.2
"""
import matplotlib.pyplot as plt
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS
from tilted_flrw import beta_from_colin

apply_style()

# ═══════════════════════════════════════════════════════════
#  DATA
# ═══════════════════════════════════════════════════════════
z_arr = np.linspace(0.005, 0.22, 500)
beta_arr = np.array([beta_from_colin(z) for z in z_arr])

beta_cf4 = 1.334e-3
sigma_cf4 = 0.267e-3
ratio_arr = beta_arr / beta_cf4

# Table points from ch08 §8.3.2
z_tab = np.array([0.02, 0.03, 0.05, 0.08, 0.10, 0.15])
b_tab = np.array([beta_from_colin(z) for z in z_tab])

# Peak
i_pk = np.argmax(beta_arr)
z_peak = z_arr[i_pk]
b_peak = beta_arr[i_pk]

# Crossing at ratio = 1
from scipy.optimize import brentq
z_cross = brentq(lambda z: beta_from_colin(z)/beta_cf4 - 1.0, 0.03, 0.07)

# ═══════════════════════════════════════════════════════════
#  FIGURE
# ═══════════════════════════════════════════════════════════
fig, ax1 = plt.subplots(figsize=(7.0, 3.6))

# ── β_CF4 horizontal band ──
ax1.axhspan((beta_cf4 - sigma_cf4)*1e3, (beta_cf4 + sigma_cf4)*1e3,
            color=COLS['yellow'], alpha=0.25, zorder=0)
ax1.axhline(beta_cf4*1e3, color=COLS['orange'], lw=0.6, ls=':', alpha=0.5)

# ── Main curve ──
ax1.plot(z_arr, beta_arr * 1e3, color=COLS['blue'], lw=1.8, zorder=3,
         label=r'$\beta_{\mathrm{SNe}}(z) = 9\,|q_d|\,z^3\,e^{-z/S}$')

# ── Table markers ──
ax1.plot(z_tab, b_tab * 1e3, 'o', color=COLS['blue'], ms=5,
         mec='k', mew=0.3, zorder=5)

# ── JLA median depth marker ──
ax1.axvline(0.05, color=COLS['gray'], lw=0.6, ls='--', alpha=0.5)

# Crossing point highlight (where β_SNe = β_CF4)
ax1.plot(0.05, beta_from_colin(0.05)*1e3, 'D', color=COLS['green'],
         ms=7, mec='k', mew=0.4, zorder=6)
ax1.annotate(r'$z = 0.05$: $\beta_{\mathrm{SNe}} = \beta_{\mathrm{CF4}}$',
             (0.05, beta_from_colin(0.05)*1e3),
             textcoords='offset points', xytext=(8, -15),
             fontsize=7.5, color=COLS['green'], fontweight='medium')

# ── Peak marker ──
ax1.plot(z_peak, b_peak * 1e3, 'v', color=COLS['red'], ms=6,
         mec='k', mew=0.3, zorder=5)
ax1.annotate(f'peak: $z = {z_peak:.3f}$',
             (z_peak, b_peak*1e3), textcoords='offset points',
             xytext=(8, 5), fontsize=7, color=COLS['red'])

# ── β_CF4 label ──
ax1.text(0.208, (beta_cf4 + sigma_cf4 + 0.03e-3)*1e3,
         r'$\beta_{\mathrm{CF4}} \pm 20\%$',
         fontsize=8, color=COLS['orange'], ha='right', va='bottom')

# ── Left axis ──
ax1.set_xlabel(r'Reference redshift $z_{\mathrm{ref}}$')
ax1.set_ylabel(r'$\beta_{\mathrm{SNe}}\;\;(\times 10^{-3})$')
ax1.set_xlim(0, 0.22)
ax1.set_ylim(0, 2.1)

# ── Right axis: ratio ──
ax2 = ax1.twinx()
# Scale: ratio = β / β_CF4, and left axis is β × 10³
# so ratio = (left_value × 10⁻³) / β_CF4
# right ticks should show ratio values
ratio_ticks = [0, 0.5, 1.0, 1.5]
ax2.set_ylim(0, 2.1e-3 / beta_cf4)  # same physical range
ax2.set_yticks(ratio_ticks)
ax2.set_yticklabels([f'{r:.1f}' for r in ratio_ticks])
ax2.set_ylabel(r'$\beta_{\mathrm{SNe}} / \beta_{\mathrm{CF4}}$',
               color='#555555')
ax2.tick_params(axis='y', colors='#555555')

# ── ratio = 1 line on right axis ──
ax2.axhline(1.0, color='#AAAAAA', lw=0.5, ls='-', alpha=0.4)

# ── Legend ──
ax1.legend(loc='upper right', fontsize=8, framealpha=0.92)

fig.tight_layout()
save_fig(fig, 'fig_colin_beta')
print("ok fig_colin_beta.pdf saved")
