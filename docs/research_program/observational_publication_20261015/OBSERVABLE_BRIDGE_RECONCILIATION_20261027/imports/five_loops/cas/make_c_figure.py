"""Render LOOP C analytic local-kinematics figure; no observational inputs.

Run from any directory: python /absolute/path/to/cas/make_c_figure.py
Outputs are written to ../figures/figure_c_kinematics.{pdf,png}.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'figures'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                     'axes.titlesize': 11, 'axes.titleweight': 'semibold',
                     'axes.labelsize': 10, 'pdf.fonttype': 42,
                     'axes.spines.top': False, 'axes.spines.right': False})
blue, gold, ink, gray = '#24649A', '#B17816', '#25313A', '#DCE2E7'

# Rate coordinates in units of arbitrary Gamma>0:
# h/Gamma=2; S/Gamma=diag(1,-1,0); alpha/Gamma=0;
# v/Gamma=(0,0,0.65), with project omega_ij=epsilon_ijk omega_k.
S = np.diag([1., -1., 0.])
v = np.array([0., 0., .65])
lon = np.linspace(-np.pi, np.pi, 721)
lat = np.linspace(-np.pi/2, np.pi/2, 361)
L, B = np.meshgrid(lon, lat)
n = np.stack([np.cos(B)*np.cos(L), np.cos(B)*np.sin(L), np.sin(B)], -1)
rad = np.einsum('...i,ij,...j->...', n, S, n)
assert np.allclose(rad, np.cos(B)**2*np.cos(2*L))

ne = np.stack([np.cos(lon), np.sin(lon), np.zeros_like(lon)], -1)
ephi = np.stack([-np.sin(lon), np.cos(lon), np.zeros_like(lon)], -1)
sn = ne @ S.T
muE = sn - ne*np.einsum('...i,...i->...', ne,sn)[...,None]
muB = np.cross(ne,v)
eastE = np.einsum('...i,...i->...', muE,ephi)
eastB = np.einsum('...i,...i->...', muB,ephi)
assert np.allclose(eastE, -np.sin(2*lon))
assert np.allclose(eastB, -.65)
assert np.allclose(muE[:,2],0) and np.allclose(muB[:,2],0)

fig = plt.figure(figsize=(12.1,8.25), facecolor='white')
gs = fig.add_gridspec(2,2, left=.065, right=.97, top=.81, bottom=.12,
                      height_ratios=[1.42,1.0], width_ratios=[1.1,1.],
                      hspace=.54, wspace=.28)
fig.suptitle('Local radial and transverse kinematics', x=.065, y=.97,
             ha='left', fontsize=18, fontweight='bold', color=ink)
fig.text(.065,.922, 'Analytic example  •  arbitrary rate unit Γ > 0  •  no observational data',
         color='#52606B',fontsize=11)
fig.text(.065,.875, r'$h/\Gamma=2,\quad S/\Gamma=\mathrm{diag}(1,-1,0),\quad '
         r'\alpha=0,\quad v/\Gamma=(0,0,0.65),\quad\Omega=0$', fontsize=12,color=ink)
ax = fig.add_subplot(gs[0,0], projection='mollweide')
im = ax.pcolormesh(L,B,rad, cmap='RdBu_r', norm=TwoSlopeNorm(vmin=-1,vcenter=0,vmax=1),
                   rasterized=True, shading='auto')
ax.grid(color='white',alpha=.5,linewidth=.6)
ax.set_xticks(np.deg2rad([-120,-60,0,60,120]))
ax.set_xticklabels(['−120°','−60°','0°','60°','120°'],fontsize=8)
ax.set_yticks(np.deg2rad([-60,-30,0,30,60]))
ax.set_yticklabels(['−60°','−30°','0°','30°','60°'],fontsize=8)
ax.set_title('a  Radial anisotropy over the full sky',loc='left',pad=14)
cbar=fig.colorbar(im, ax=ax, orientation='horizontal', fraction=.065,pad=.14,
                  shrink=.88, ticks=[-1,-.5,0,.5,1])
cbar.set_label(r'$(d-h)/\Gamma = \cos^2 b\,\cos 2\phi$',labelpad=4)
cbar.outline.set_linewidth(.6)

ax2=fig.add_subplot(gs[0,1])
x=np.rad2deg(lon)
ax2.plot(x,eastE,color=blue,lw=2.5,label=r'E2 shear: $\mu^E_\phi/\Gamma=-\sin 2\phi$')
ax2.plot(x,eastB,color=gold,lw=2.5,ls='--',label=r'B1 rotation: $\mu^B_\phi/\Gamma=-0.65$')
ax2.axhline(0,color='#687783',lw=.8,zorder=0)
ax2.set(xlim=(-180,180),ylim=(-1.2,1.25),xticks=[-180,-90,0,90,180],
        yticks=[-1,-.5,0,.5,1],xlabel='Longitude φ on the equator (degrees)',
        ylabel=r'Eastward angular rate $\mu_\phi/\Gamma$')
ax2.set_title('b  Exact transverse components on the equator',loc='left',pad=14)
ax2.grid(axis='y',color=gray,linewidth=.7)
ax2.legend(loc='upper center',bbox_to_anchor=(.5,-.26),frameon=False,fontsize=9,
           handlelength=3)
ax2.text(.02,.96,'Northward components vanish on this slice.',transform=ax2.transAxes,
         va='top',fontsize=9,color='#52606B')

ax3=fig.add_subplot(gs[1,:]); ax3.axis('off')
ax3.set_title('c  Full-sphere linear response rank',loc='left',pad=10)
rows=[['Radial only',r'$h,\ S,\ \alpha$','9 / 12'],
      ['Proper motion only',r'$S,\ v$','8 / 12'],
      ['Joint, calibrated frame',r'$h,\ S,\ \alpha,\ v$','12 / 12'],
      ['Joint, unknown triad spin',r'$h,\ S,\ \alpha,\ v+\Omega$','12 / 15']]
table=ax3.table(cellText=rows,colLabels=['Observation channels','Surviving coefficients','Rank / parameter count'],
                colWidths=[.36,.34,.30],cellLoc='left',colLoc='left',bbox=[0,.02,1,.84])
table.auto_set_font_size(False);table.set_fontsize(10)
for (r,c),cell in table.get_celld().items():
    cell.set_edgecolor('#DEE4E8');cell.set_linewidth(.6);cell.PAD=.14
    if r==0:
        cell.set_facecolor('#EDF1F4');cell.set_text_props(weight='semibold',color=ink)
    else:
        cell.set_facecolor('white');cell.set_text_props(color=ink)
ax3.text(0,-.1,'Ranks apply to the complete leading local response, not to the displayed equatorial slice.',
         fontsize=9,color='#52606B',transform=ax3.transAxes)
fig.text(.065,.043,'Outward sky direction n; east is increasing φ. The B1 sign follows ωᵢⱼ = εᵢⱼₖ ωₖ. '
         'An uncalibrated rotating triad measures v + Ω.',fontsize=8.6,color='#52606B')
for ext in ('pdf','png'):
    target=OUT/f'figure_c_kinematics.{ext}'
    fig.savefig(target,dpi=190,facecolor='white',metadata={'Title':'LOOP C analytic local kinematics',
                 'Creator':'cas/make_c_figure.py'})
    print(target)
plt.close(fig)
