#!/usr/bin/env python3
"""
fig_direction_posterior.py — Directional posterior on the sky
==============================================================
Mollweide projection showing the (l, b) posterior density from
IS-06 3D catalog sampling, with credible cones and reference
directions (CMB dipole, CatWISE, CF4).
"""
import sys
import os
import numpy as np

sys.path.insert(0, '/mnt/project')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from scipy.stats import gaussian_kde

from plot_style import apply_style, save_fig, COLS

apply_style()

# HTT_PIPELINE_OUTDIR overrides the legacy '/mnt/user-data/outputs'
# default so smoke tests can inject the repo-local synthetic fixture
# (bass_py/htt/tests/fixtures/pipeline_outputs/IS06_3D_posterior.npz)
# without depending on the original author mount.
_OUTDIR = os.environ.get('HTT_PIPELINE_OUTDIR', '/mnt/user-data/outputs')

# ─── Load IS-06 posterior ─────────────────────────────────────
d = np.load(os.path.join(_OUTDIR, 'IS06_3D_posterior.npz'), allow_pickle=True)
if 'l_rad' in d and 'b_rad' in d:
    l_deg = np.degrees(d['l_rad'])
    b_deg = np.degrees(d['b_rad'])
elif 'l' in d and 'b' in d:
    l_deg = np.asarray(d['l'], dtype=float)
    b_deg = np.asarray(d['b'], dtype=float)
else:
    raise KeyError(
        "IS06_3D_posterior.npz must contain either (l_rad, b_rad) or (l, b)"
    )

# Truth (injection)
L_TRUE, B_TRUE = 264.0, 48.0

# Reference directions (Galactic coordinates)
REFS = {
    'CMB dipole':    (264.0, 48.3,  COLS['red'],    '*', 12),
    'CatWISE':       (240.5, 41.4,  COLS['orange'], 's', 7),
    'CF4 bulk flow': (298.0, -8.0,  COLS['green'],  'D', 7),
    'Injected truth':(L_TRUE, B_TRUE, COLS['blue'], 'o', 8),
}

# ─── Convert to Mollweide coordinates ─────────────────────────
# Mollweide uses (longitude, latitude) in radians
# longitude ∈ [-π, π], latitude ∈ [-π/2, π/2]
# Galactic l ∈ [0, 360] → shift to [-180, 180]

def gal_to_moll(l_deg, b_deg):
    """Convert Galactic (l, b) in degrees to Mollweide (lon, lat) in radians."""
    lon = np.where(l_deg > 180, l_deg - 360, l_deg)
    return np.radians(lon), np.radians(b_deg)


# ─── Compute 2D KDE density on a grid ────────────────────────
# Work in shifted Galactic coordinates for the KDE
l_shift = np.where(l_deg > 180, l_deg - 360, l_deg)
b_shift = b_deg

# KDE in (l, b) space
try:
    kde = gaussian_kde(np.vstack([l_shift, b_shift]), bw_method=0.3)
    # Evaluate on grid
    l_grid = np.linspace(l_shift.min() - 15, l_shift.max() + 15, 200)
    b_grid = np.linspace(b_shift.min() - 15, b_shift.max() + 15, 100)
    L_mg, B_mg = np.meshgrid(l_grid, b_grid)
    positions = np.vstack([L_mg.ravel(), B_mg.ravel()])
    Z = kde(positions).reshape(L_mg.shape)
    has_kde = True
except Exception:
    has_kde = False

# ─── Credible cones ──────────────────────────────────────────
med_l = np.median(l_shift)
med_b = np.median(b_shift)

# Angular separation from median for each sample
def ang_sep_deg(l1, b1, l2, b2):
    l1r, b1r = np.radians(l1), np.radians(b1)
    l2r, b2r = np.radians(l2), np.radians(b2)
    cos_sep = (np.sin(b1r)*np.sin(b2r) +
               np.cos(b1r)*np.cos(b2r)*np.cos(l1r - l2r))
    return np.degrees(np.arccos(np.clip(cos_sep, -1, 1)))

seps = ang_sep_deg(l_shift, b_shift, med_l, med_b)
cone_68 = np.percentile(seps, 68)
cone_95 = np.percentile(seps, 95)

# ─── Figure ───────────────────────────────────────────────────
fig = plt.figure(figsize=(7.0, 4.5))
ax = fig.add_subplot(111, projection='mollweide')

# Scatter the posterior samples
lon_samp, lat_samp = gal_to_moll(l_deg, b_deg)
ax.scatter(lon_samp, lat_samp, s=0.3, alpha=0.15, color=COLS['blue'],
           rasterized=True, zorder=1)

# Contour from KDE (if available)
if has_kde:
    lon_mg_rad = np.radians(L_mg)
    lat_mg_rad = np.radians(B_mg)
    levels = np.percentile(Z[Z > 0], [10, 40, 70, 90])
    ax.contour(lon_mg_rad, lat_mg_rad, Z, levels=levels,
               colors=COLS['blue'], linewidths=[0.4, 0.6, 0.8, 1.0],
               alpha=0.7, zorder=2)
    ax.contourf(lon_mg_rad, lat_mg_rad, Z, levels=[levels[-1], Z.max()*2],
                colors=[COLS['blue']], alpha=0.15, zorder=1)

# Posterior median
lon_med, lat_med = gal_to_moll(np.array([med_l + (360 if med_l < 0 else 0)]),
                                np.array([med_b]))
ax.plot(lon_med, lat_med, '+', ms=10, mew=1.5, color=COLS['blue'], zorder=8)

# Reference directions
for name, (l, b, color, marker, ms) in REFS.items():
    lon_r, lat_r = gal_to_moll(np.array([l]), np.array([b]))
    ax.plot(lon_r, lat_r, marker=marker, ms=ms, color=color,
            markeredgecolor='k', markeredgewidth=0.4, zorder=10,
            label=f'{name} ({l:.0f}°, {b:.0f}°)')

# Credible cone annotation
ax.text(0.02, 0.02,
        f'68% cone: {cone_68:.0f}°\n95% cone: {cone_95:.0f}°\n'
        f'Median: ({med_l+360 if med_l<0 else med_l:.0f}°, {med_b:.0f}°)',
        transform=ax.transAxes, fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  edgecolor=COLS['gray'], alpha=0.9),
        va='bottom', zorder=15)

# Grid and labels
ax.grid(True, alpha=0.3, lw=0.4)
ax.set_xlabel('Galactic longitude $l$', fontsize=10, labelpad=5)
ax.set_ylabel('Galactic latitude $b$', fontsize=10)

# Legend
ax.legend(fontsize=7.5, loc='upper right', framealpha=0.9,
          markerscale=1.0, handletextpad=0.3)

fig.tight_layout()
save_fig(fig, 'fig_direction_posterior')
print("Saved fig_direction_posterior.pdf + .png")
