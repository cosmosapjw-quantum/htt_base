"""Render stored diagnostics only. No integration, SVD, fitting, or matrix actions."""
from pathlib import Path
import json,csv,hashlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'data/RESULT.json').read_text());bs=d['branches'];labels=list(bs)
plt.rcParams.update({'font.family':'serif','font.size':10,'pdf.fonttype':42})
colors=plt.cm.tab10.colors
fig,axs=plt.subplots(1,2,figsize=(10,4.5),sharey=True)
for ax,f in zip(axs,['F1','F2']):
 for i,(name,b) in enumerate(bs.items()):
  vals=b[f]['normalized_singular_values'];ax.semilogy(range(1,len(vals)+1),vals,'o-',color=colors[i],label=name.replace('_BT_',' / '),markersize=4,alpha=.8)
 ax.axhline(1e-10,color='black',ls='--',lw=1,label='resolved threshold')
 ax.axhline(1e-12,color='gray',ls=':',lw=1,label='unresolved threshold')
 ax.set(title=f+' unit-column singular spectrum',xlabel='Singular-value index',ylim=(1e-13,4));ax.grid(alpha=.2)
axs[0].set_ylabel('Stored singular value');axs[1].legend(fontsize=7,loc='lower left',ncol=2)
fig.tight_layout();fig.savefig(R/'figures/spectra.pdf');plt.close(fig)
fig,axs=plt.subplots(3,1,figsize=(10,8),gridspec_kw={'height_ratios':[1,1,0.8]})
for i,(name,b) in enumerate(bs.items()):
 lab=name.replace('_BT_',' / ')
 axs[0].plot(range(7),b['F1']['w'],'o-',color=colors[i],label=lab,alpha=.8,ms=4)
 axs[1].plot(range(9),b['F2']['cmb_in_foreground_coefficients_9'],'o-',color=colors[i],alpha=.8,ms=4)
 axs[2].plot(i,b['F1']['resolved_condition'],'o',color=colors[i]);axs[2].plot(i,b['F2']['resolved_condition'],'s',color=colors[i]);axs[2].plot(i,b['F1']['w_norm2'],'^',color=colors[i])
axs[0].set_xticks(range(7),['30','44','70','100','143','217','353 PSB']);axs[0].set(ylabel='Signed F1 weight',xlabel='Frequency channel (GHz)');axs[0].legend(fontsize=8,ncol=3)
axs[1].set_xticks(range(9),['s',r'$s_{,\beta}$','d',r'$d_{,\beta}$',r'$d_{,t}$',r'$s_{,\beta\beta}$',r'$d_{,\beta\beta}$',r'$d_{,\beta t}$',r'$d_{,tt}$']);axs[1].set(ylabel='Signed F2 coefficient',xlabel='Moment column (unscaled basis)')
axs[2].set_xticks(range(6),[x.replace('_BT_','\n') for x in labels]);axs[2].set(yscale='log',ylabel='Euclidean quantity');axs[2].plot([],[],'ko',label=r'$\kappa(F_1)$');axs[2].plot([],[],'ks',label=r'$\kappa(F_2)$');axs[2].plot([],[],'k^',label=r'$\|w\|_2$');axs[2].legend(ncol=3,fontsize=8)
for ax in axs:ax.axhline(0,color='gray',lw=.4) if ax!=axs[2] else None;ax.grid(alpha=.2)
fig.tight_layout();fig.savefig(R/'figures/weights_witnesses.pdf');plt.close(fig)
rows=[]
for name,b in bs.items():
 f,g=b['F1'],b['F2'];rows.append([name,f['resolved_rank'],g['resolved_rank'],f['resolved_condition'],g['resolved_condition'],f['principal_angle_sine'],g['principal_angle_sine'],f['w_norm2'],g['cmb_reconstruction_relative_residual'],max(g['full24_degeneracy_relative_residuals'])])
with (R/'generated/branch_summary.csv').open('w') as o:
 w=csv.writer(o);w.writerow(['branch','F1_rank','F2_rank','F1_condition','F2_condition','F1_principal_sine','F2_principal_sine','F1_weight_norm','F2_spectral_witness_residual','F2_max24_witness_residual']);w.writerows(rows)
with (R/'generated/branch_table.tex').open('w') as o:
 for row in rows:
  n,r1,r2,k1,k2,s1,s2,wn,res,mres=row
  o.write(f"{n.replace('_BT_', '/').replace('1e-', '$10^{-')+'}$'} & {r1}/{r2} & {k1:.3f} & {k2:.3f} & {s1:.6f} & {s2:.2e} & {wn:.5f} & {mres:.2e} \\\\ " + "\n")
# Separate exact stored source for every figure; all coordinates and controls remain in RESULT.
(R/'generated/plot_data.json').write_text(json.dumps({n:{f:{k:b[f][k] for k in (['normalized_singular_values','w','w_norm2','resolved_condition'] if f=='F1' else ['normalized_singular_values','cmb_in_foreground_coefficients_9','resolved_condition'])} for f in ['F1','F2']} for n,b in bs.items()},indent=2)+'\n')
manifest={'owner':'obsstat','scope':'finite nominal Planck spectral-table conditional common-spatial-response model','claim_tier':'C0_CONDITIONAL_MODEL_DIAGNOSTIC','transfer_source':'none','sky_support_status':'NO_SKY_USED','null_mock_status':'NO_NOISE_OR_NULL_LAW','generation':'python code/assemble.py; stored fields only','source_sha256':hashlib.sha256((R/'data/RESULT.json').read_bytes()).hexdigest(),'figures':{'spectra.pdf':'normalized_singular_values; thresholds from frozen contract','weights_witnesses.pdf':'F1.w,F1.w_norm2,F1/F2.resolved_condition,F2.cmb_in_foreground_coefficients_9'},'caveats':['Numerically resolved ranks do not establish exact physical ranks','No actual-sky fit or noise variance','Six branches are not a calibrated uncertainty set']}
(R/'generated/FIGURE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
