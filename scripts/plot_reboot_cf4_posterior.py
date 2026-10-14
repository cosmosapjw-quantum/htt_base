#!/usr/bin/env python3
"""Render same-ID CF4 posterior and latent/repeated-measurement PPC artifacts."""
from pathlib import Path
import hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1]/'docs/observational_reboot_20261014/results/cf4'
def main():
 import matplotlib;matplotlib.use('Agg');from matplotlib import pyplot as plt
 from scipy.stats import chi2
 p=R/'posterior_v1/result.json';r=json.loads(p.read_text())['posterior'];theta=np.array(r['parameter_draws_H_B']);w=np.array(r['normalized_weights']);fig,axes=plt.subplots(2,2,figsize=(9,6))
 for i,ax in enumerate(axes.ravel()):
  ax.hist(theta[w>0,i],weights=w[w>0],bins=35,density=True);ax.set(xlabel=['H endpoint(km/s/Mpc)','Bx endpoint(km/s)','By endpoint(km/s)','Bz endpoint(km/s)'][i],ylabel='conditional posterior density')
 fig.suptitle('CF4 finite-box declared-scenario posterior; no H0/tilt admission');fig.tight_layout()
 for ext in('png','pdf'):fig.savefig(R/'posterior_v1'/f'posterior.{ext}',dpi=160)
 plt.close(fig)
 d=R/'latent_v1';a=np.load(d/'posterior_latent_repeated_measurement.npz');ok=a['normalized_weight']>0;ww=a['normalized_weight'][ok];summary=json.loads((d/'result.json').read_text())['latent_bridge'];fig,axes=plt.subplots(1,2,figsize=(11,4))
 quant=np.array(summary['same_state_distance_pushforward']['dA_Mpc_weighted_quantiles']);idx=np.arange(24);axes[0].errorbar(idx,quant[1],yerr=np.stack((quant[1]-quant[0],quant[2]-quant[1])),fmt='.',label='5/50/95% same-draw dA');axes[0].set(xlabel='frozen group index',ylabel='latent dA(Mpc)');axes[0].legend()
 for key,label in [('chi_square_48_observed_conditional','observed with same latent state'),('chi_square_48_replicated_conditional','repeated measurement')]:axes[1].hist(a[key][ok],weights=ww,bins=35,density=True,histtype='step',label=label)
 grid=np.linspace(10,100,300);axes[1].plot(grid,chi2.pdf(grid,48),'--',label='conditional chi-square48');axes[1].set(xlabel='same-state discrepancy',ylabel='weighted density');axes[1].legend(fontsize=8)
 fig.suptitle('CF4 latent distances and repeated-measurement PPC (no reselection)');fig.tight_layout()
 for ext in('png','pdf'):fig.savefig(d/f'latent_ppc.{ext}',dpi=160)
 plt.close(fig)
 (d/'report.md').write_text('# CF4 same-posterior latent distances and PPC\n\n2029 positive-weight of2048 retained importance draws. Original draw IDs/weights are preserved, including zero-weight statuses. Shared eta conditional uses observed f, not selection Z. dL=dA(1+ztrue)^2 holds on every applicable state.\n\nRepeated-measurement weighted PPC exceedance='+str(summary['repeated_measurement_ppc']['weighted_exceedance_descriptive'])+'; observed mean discrepancy='+str(summary['repeated_measurement_ppc']['observed_chi2_weighted_mean'])+', replicated='+str(summary['repeated_measurement_ppc']['replicated_chi2_weighted_mean'])+'. This is a posterior predictive quantity, not a uniform null p or posterior exceedance Pi. Fresh selected-population prediction is a different target.\n\n![sameposterior](latent_ppc.png)\n\nDeclared CF4 population, widths, absolute calibration, selection and finite-distance polynomial are scenarios, not established empirical laws. Physical MES mapping is unavailable; unknown mass1, no physical sectors set to0.\n')
 (d/'plot_receipt.json').write_text(json.dumps({'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'posterior_result_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'latent_npz_sha256':hashlib.sha256((d/'posterior_latent_repeated_measurement.npz').read_bytes()).hexdigest(),'scope':'same stored draw IDs/weights, no rerun or selection','outputs':['posterior_v1/posterior.png','posterior_v1/posterior.pdf','latent_v1/latent_ppc.png','latent_v1/latent_ppc.pdf']},indent=2)+'\n')
if __name__=='__main__':main()
