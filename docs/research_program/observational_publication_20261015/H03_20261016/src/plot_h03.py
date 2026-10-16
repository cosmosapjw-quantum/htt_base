"""Generate three explicitly conditional / not physical figures for H03."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def plot(source:Path,out:Path):
 d=json.loads(source.read_text());out.mkdir(parents=True,exist_ok=True)
 rows=d['monopole_dipole_STF2_windows'];z=np.array([x['z_center'] for x in rows]);H=np.array([x['H0_working_km_s_Mpc'] for x in rows]);H01=np.array([x['H01_monopole_only_formula'] for x in rows]);e=np.array([x['conditional_diagonal_std9'][0] for x in rows])
 fig,ax=plt.subplots(figsize=(7.6,4.5));ax.errorbar(z,H,yerr=e,marker='o',capsize=3,label='H03 9D fit, formal diagonal-working SD');ax.plot(z,H01,marker='s',ls='--',label='H01 monopole-only');ax.set_xlabel('Window center $z$');ax.set_ylabel('Apparent $H_W$ [km s$^{-1}$ Mpc$^{-1}$]');ax.set_title('CF4 35,970 groups, same source, uncalibrated selection');ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'H03_WINDOW_MONOPOLE.png',dpi=160);plt.close(fig)
 fig,ax=plt.subplots(figsize=(7.6,4.5));ax.plot(z,[x['dipole_norm_km_s_Mpc'] for x in rows],marker='o',label='Apparent Cartesian dipole norm');ax.plot(z,[x['STF2_frobenius_km_s_Mpc'] for x in rows],marker='s',label='Apparent STF2 Frobenius norm');ax.set_xlabel('Window center $z$');ax.set_ylabel('Fitted angular coefficient norm [km s$^{-1}$ Mpc$^{-1}$]');ax.set_title('Working angular shapes, NOT physical expansion or shear');ax.legend(fontsize=8);ax.grid(alpha=.2);fig.tight_layout();fig.savefig(out/'H03_ANGULAR_NORMS.png',dpi=160);plt.close(fig)
 R=np.array(d['joint_correlation_36x36']);idx=[0,9,18,27];rr=R[np.ix_(idx,idx)];fig,ax=plt.subplots(figsize=(5.5,4.8));im=ax.imshow(rr,vmin=-1,vmax=1);ax.set_xticks(range(4),[str(x) for x in z]);ax.set_yticks(range(4),[str(x) for x in z]);ax.set_xlabel('Window center $z$');ax.set_ylabel('Window center $z$');ax.set_title('Shared-source monopole correlations',fontsize=11)
 fig.text(0.5,0.01,'Conditional diagonal group errors only; not released CF4 covariance',ha='center',fontsize=8);fig.colorbar(im,ax=ax);fig.tight_layout();fig.savefig(out/'H03_SHARED_WINDOW_CORRELATION.png',dpi=160);plt.close(fig)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--result',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();plot(a.result,a.output)
