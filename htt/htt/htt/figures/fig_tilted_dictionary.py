#!/usr/bin/env python3
"""
fig_tilted_dictionary.py — Tilted Defect Dictionary Schematic (v2)
==================================================================
Redesigned after MAPS/Reflexion audit (10 defects fixed).

Design principles:
  - Equal-width boxes for visual symmetry
  - Bridge η_u̇ as central visual element (not marginal annotation)
  - No redundant arrows (redistribution, amplification removed)
  - Tsagas box: compact, single-line equation
  - All text ≥ 8pt at 7" width → ≥ 5.5pt at 3.4" single-col
  - Nothing extends past margins

Output: fig_tilted_dictionary.pdf
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(__file__) or '.')
from plot_style import apply_style, save_fig, COLS

apply_style()

# ═══════════════════════════════════════════════════════════
#  PALETTE
# ═══════════════════════════════════════════════════════════
C_GEOM   = COLS['blue']
C_MATT   = COLS['red']
C_TSAG   = COLS['green']
C_BOOST  = '#B87333'        # warm bronze for arrows (distinct from orange text)
C_BRIDGE = COLS['purple']

# ═══════════════════════════════════════════════════════════
#  LAYOUT CONSTANTS
# ═══════════════════════════════════════════════════════════
FW = 7.0                    # figure width
FH = 6.8                    # figure height
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(0, 10)
ax.set_ylim(-1.05, 9.6)
ax.axis('off')

# Column centres
XL = 2.0                    # geometry frame (left)
XC = 5.0                    # centre (boost labels)
XR = 8.0                    # matter frame (right)

# Box dimensions (uniform)
BW = 2.8                    # box width (same left and right)
BH = 0.65                   # box height

# Row y-positions (top to bottom, spacing 1.4)
ROW_Y = {'H': 7.8, 'sig': 6.4, 'om': 5.0, 'A': 3.6, 'q': 2.2}
HDR_Y = 9.1                 # column headers

# ═══════════════════════════════════════════════════════════
#  DRAWING HELPERS
# ═══════════════════════════════════════════════════════════
def box(x, y, txt, color, w=BW, h=BH, fs=10):
    """Draw a rounded box with centred text."""
    r = FancyBboxPatch((x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.06", fc=color, ec=color, alpha=0.13, lw=0)
    ax.add_patch(r)
    r2 = FancyBboxPatch((x - w/2, y - h/2), w, h,
        boxstyle="round,pad=0.06", fc='none', ec=color, alpha=0.55, lw=0.9)
    ax.add_patch(r2)
    ax.text(x, y, txt, fontsize=fs, ha='center', va='center', color='#1a1a1a')

def arrow(x1, y, x2, color=C_BOOST, lw=0.9):
    """Horizontal arrow at fixed y."""
    ax.annotate('', xy=(x2, y), xytext=(x1, y),
        arrowprops=dict(arrowstyle='->', color=color, lw=lw))

def boost_label(y, txt, fs=8):
    """Label above a horizontal arrow, centred in the boost column."""
    ax.text(XC, y + 0.32, txt, fontsize=fs, ha='center', va='bottom',
            color=C_BOOST, style='italic')

# ═══════════════════════════════════════════════════════════
#  COLUMN HEADERS
# ═══════════════════════════════════════════════════════════
hkw = dict(fontsize=11.5, fontweight='bold', ha='center', va='center')
ax.text(XL, HDR_Y, 'Geometry frame', color=C_GEOM, **hkw)
ax.text(XR, HDR_Y, 'Matter frame', color=C_MATT, **hkw)

skw = dict(fontsize=8, ha='center', va='center', color='#666666', style='italic')
ax.text(XL, HDR_Y - 0.38, r'$u^a$  (geodesic, irrotational)', **skw)
ax.text(XR, HDR_Y - 0.38, r'$\hat{u}^a$  (tilted observer)', **skw)

# Centre column label
ax.text(XC, HDR_Y, 'King–Ellis boost', fontsize=10, fontweight='bold',
        ha='center', va='center', color=C_BOOST)
ax.text(XC, HDR_Y - 0.38, r'$\hat{u}^a = \gamma(u^a + v^a)$', **skw)

# Header separator
ax.plot([0.3, 9.7], [HDR_Y - 0.62, HDR_Y - 0.62], color='#D0D0D0', lw=0.7)

# ═══════════════════════════════════════════════════════════
#  ROW 1: EXPANSION
# ═══════════════════════════════════════════════════════════
y = ROW_Y['H']
box(XL, y, r'$H$', C_GEOM)
box(XR, y, r'$\hat{H} = H\cosh\beta$', C_MATT)
arrow(XL + BW/2 + 0.08, y, XR - BW/2 - 0.08)
boost_label(y, r'$\times\cosh\beta\,(1 + \xi)$')

# ═══════════════════════════════════════════════════════════
#  ROW 2: SHEAR
# ═══════════════════════════════════════════════════════════
y = ROW_Y['sig']
box(XL, y, r'$\Sigma^2$', C_GEOM)
box(XR, y, r'$\hat{\Sigma}^2 \approx \Sigma^2(1-\beta^2)$', C_MATT)
arrow(XL + BW/2 + 0.08, y, XR - BW/2 - 0.08)
boost_label(y, 'PSTF re-projection')

# ═══════════════════════════════════════════════════════════
#  ROW 3: VORTICITY
# ═══════════════════════════════════════════════════════════
y = ROW_Y['om']
box(XL, y, r'$W^2 = 0$', C_GEOM)
box(XR, y, r'$\hat{W}^2 \leq \Sigma^2 \sinh^4\!\beta$', C_MATT)
arrow(XL + BW/2 + 0.08, y, XR - BW/2 - 0.08)
boost_label(y, 'shear–tilt coupling')

# ═══════════════════════════════════════════════════════════
#  ROW 4: ACCELERATION
# ═══════════════════════════════════════════════════════════
y = ROW_Y['A']
box(XL, y, r'$A^2 = 0$', C_GEOM)
box(XR, y, r'$\hat{A}^2 = \eta_{\dot{u}}^2 \sinh^2\!\beta\,/\,6$', C_MATT)
arrow(XL + BW/2 + 0.08, y, XR - BW/2 - 0.08)
boost_label(y, 'Euler equation')

# ═══════════════════════════════════════════════════════════
#  ROW 5: DECELERATION
# ═══════════════════════════════════════════════════════════
y = ROW_Y['q']
box(XL, y, r'$q$', C_GEOM)
box(XR, y, r'$\hat{q} = q + \Delta q^{(\mathrm{SH})}$', C_MATT)
arrow(XL + BW/2 + 0.08, y, XR - BW/2 - 0.08)
boost_label(y, r'$O(\beta^2) \sim 10^{-6}$')

# ═══════════════════════════════════════════════════════════
#  LEFT MARGIN LABEL
# ═══════════════════════════════════════════════════════════
mid_y = (ROW_Y['H'] + ROW_Y['q']) / 2
ax.text(0.25, mid_y, 'SH Bianchi\n' + r'($k = 0$)',
        fontsize=8, ha='center', va='center', color='#999999',
        rotation=90, style='italic')

# (Column separators removed — audit found them visually noisy)

# ═══════════════════════════════════════════════════════════
#  BRIDGE: η_u̇ = k → 0 limit  (CENTRAL ELEMENT)
# ═══════════════════════════════════════════════════════════
# Place bridge in the centre column, between the grid and the Tsagas box
bridge_y = 0.85
bridge_w = 5.6
bridge_h = 0.95

bx = FancyBboxPatch((XC - bridge_w/2, bridge_y - bridge_h/2),
    bridge_w, bridge_h, boxstyle="round,pad=0.1",
    fc=C_BRIDGE, ec=C_BRIDGE, alpha=0.10, lw=0)
ax.add_patch(bx)
bx2 = FancyBboxPatch((XC - bridge_w/2, bridge_y - bridge_h/2),
    bridge_w, bridge_h, boxstyle="round,pad=0.1",
    fc='none', ec=C_BRIDGE, alpha=0.6, lw=1.2)
ax.add_patch(bx2)

# Line 1: equation (larger, centred upper)
ax.text(XC, bridge_y + 0.18,
    r'$\eta_{\dot{u}} = \frac{w}{3(1+w)}$',
    fontsize=10, ha='center', va='center', color=C_BRIDGE,
    fontweight='bold')

# Line 2: label (smaller, centred lower)
ax.text(XC, bridge_y - 0.20,
    r'$k \to 0$ bridge:  Bianchi  $\longleftrightarrow$  Tsagas',
    fontsize=8.5, ha='center', va='center', color=C_BRIDGE)

# Arrow from q-row down to bridge (clear gap at both ends)
ax.annotate('', xy=(XC, bridge_y + bridge_h/2 + 0.08),
    xytext=(XC, ROW_Y['q'] - BH/2 - 0.15),
    arrowprops=dict(arrowstyle='->', color=C_BRIDGE, lw=1.3))

# ═══════════════════════════════════════════════════════════
#  TSAGAS BOX (compact, below bridge)
# ═══════════════════════════════════════════════════════════
tsag_y = -0.30
tsag_w = 7.4
tsag_h = 0.60

tb = FancyBboxPatch((XC - tsag_w/2, tsag_y - tsag_h/2),
    tsag_w, tsag_h, boxstyle="round,pad=0.08",
    fc=C_TSAG, ec=C_TSAG, alpha=0.08, lw=0)
ax.add_patch(tb)
tb2 = FancyBboxPatch((XC - tsag_w/2, tsag_y - tsag_h/2),
    tsag_w, tsag_h, boxstyle="round,pad=0.08",
    fc='none', ec=C_TSAG, alpha=0.45, lw=1.1, ls='--')
ax.add_patch(tb2)

ax.text(XC, tsag_y + 0.02,
    r'Tsagas  ($k > 0$):  '
    r'$\Delta\hat{q} \approx \frac{\beta}{9}'
    r'\left(\frac{\lambda_H}{d}\right)^{3}'
    r'\sim O(1)$  at  $d = 100\;\mathrm{Mpc}$',
    fontsize=8.5, ha='center', va='center', color='#1a1a1a')

# Arrow from bridge down to Tsagas
ax.annotate('', xy=(XC, tsag_y + tsag_h/2 + 0.03),
    xytext=(XC, bridge_y - bridge_h/2 - 0.03),
    arrowprops=dict(arrowstyle='->', color=C_TSAG, lw=1.0, ls='--'))

# ═══════════════════════════════════════════════════════════
#  LEGEND (compact, inline)
# ═══════════════════════════════════════════════════════════
ly = -0.82
gap = 2.6
x0 = 0.6
for i, (col, label) in enumerate([
    (C_GEOM,   'Geometry frame'),
    (C_MATT,   'Matter frame'),
    (C_BRIDGE, r'$\eta_{\dot{u}}$ bridge'),
    (C_TSAG,   'Tsagas ($k > 0$)'),
]):
    xi = x0 + i * gap
    ls = '--' if col == C_TSAG else '-'
    ax.plot([xi, xi + 0.45], [ly, ly], color=col, lw=2, ls=ls)
    ax.text(xi + 0.55, ly, label, fontsize=7.5, va='center',
            ha='left', color=col)

save_fig(fig, 'fig_tilted_dictionary')
print("✓ fig_tilted_dictionary.pdf saved (v2)")
