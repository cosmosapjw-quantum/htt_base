"""Optional figures for the finite source-conditional diagnostics."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def main():
    h=json.loads((ROOT/'results/H02_ACTUAL_SELECTED_SOURCE_FISHER.json').read_text())
    l=json.loads((ROOT/'results/L03_ACTUAL_SOURCE_PAIRED_SCAN.json').read_text())
    tau=np.array([x['tau_mag_per_angular_basis'] for x in h['grid'][1:-1]])
    vals=np.array([x['std_beta_mag_raw_basis'] for x in h['grid'][1:-1]])
    fig,ax=plt.subplots(figsize=(7,4.8));ax.loglog(tau,np.min(vals,axis=1),'o-',label='smallest conditional SE');ax.loglog(tau,np.max(vals,axis=1),'s-',label='largest conditional SE');ax.loglog(tau,tau/2,':',label=r'$\tau/\sqrt{4}$ (large-uncertainty limit)');ax.set_xlabel('Assumed method-specific angular calibration prior $\\tau$ [mag]'.replace('\\\\','\\'));ax.set_ylabel('Conditional global angular coefficient SE [mag]');ax.legend();ax.set_title('CF4: exact nuisance gauge; conditional prior sensitivity');fig.tight_layout();fig.savefig(ROOT/'results/H02_SOURCE_CALIBRATION_SENSITIVITY.png',dpi=160);plt.close(fig)
    c=np.array(l['method_energy_correlation_lower_tri'])
    fig,ax=plt.subplots(figsize=(6,5.2));image=ax.imshow(c,vmin=0,vmax=1);ax.set_xticks(range(6));ax.set_yticks(range(6));ax.set_xlabel('Processing condition index');ax.set_ylabel('Processing condition index');ax.set_title('Paired low-$\\ell$ processing response\n(200 held-out sky rows)'.replace('\\\\','\\'));fig.colorbar(image,ax=ax,fraction=.046);fig.tight_layout();fig.savefig(ROOT/'results/L03_PAIRED_CONDITION_CORRELATIONS.png',dpi=160);plt.close(fig)
if __name__=='__main__':main()
