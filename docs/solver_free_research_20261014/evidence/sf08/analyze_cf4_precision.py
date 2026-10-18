#!/usr/bin/env python3
"""Analyze exactly predeclared SF08 rows and retained historical campaign."""
import json,sys,hashlib,time
from pathlib import Path
import numpy as np
ROOT=Path('/tmp/htt_sf08_worker_20261014');OUT=ROOT/'campaign_final'
REPO=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
sys.path.insert(0,str(REPO/'scripts'))
import run_solver_free_cf4_crosslaw as x

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def main():
 c=json.loads((OUT/'contract.json').read_text());prior_path=Path(c['prior_result_path']);prior=json.loads(prior_path.read_text())
 assert digest(prior_path)==c['prior_result_sha256']
 cases=[];allrows=[]
 for case in c['cases']:
  folder=OUT/case['id'];rows=[]
  for gi,gl in enumerate(x.LABELS):
   for idx in range(case['new_pairs_per_law']):
    p=folder/f'catalogue_g{gi}_{idx:02d}.json';r=json.loads(p.read_text());npz=folder/f'generated_g{gi}_{idx:02d}.npz'
    assert r['case']==case['id'] and r['generated_law']==gl and r['index']==idx
    assert r['seed']==(case.get('replacement_seed_base',case['seed_base']) if idx<10 else case['seed_base'])+gi*100000+idx and r['generated_sha256']==digest(npz)
    expected=digest(OUT/'contract.json')
    reuse_key=case['id']+'/'+p.name
    if reuse_key in c['reused_rows']:
     assert digest(p)==c['reused_rows'][reuse_key]['row_sha256']
     expected=c['reused_rows'][reuse_key]['contract_sha256']
    assert r['contract_sha256']==expected
    assert [f['fitted_law'] for f in r['fits']]==list(x.LABELS)
    raw=np.load(npz)
    np.testing.assert_array_equal(raw['group_id'],c['source_design']['selected_group_ids'])
    np.testing.assert_array_equal(raw['truth_H_B'],c['truth_H_B'])
    assert float(raw['seed'])==r['seed'] and np.all((raw['mu']>=31)&(raw['mu']<=35))
    rows.append({**r,'source_row_path':str(p),'source_raw_path':str(npz)})
  cases.append({'id':case['id'],'s_eta_mag':case['s_eta_mag'],'summary':x.summarize(rows),'rows':rows,
                'semantic_tests':json.loads((folder/'semantic_tests.json').read_text())})
  allrows.extend(rows)
 # Separate historical catalogue identity from analysis display indices; no original file mutation.
 old=[{**r,'campaign_epoch':'historical16','original_index':r['index'],'source_raw_path':str(prior_path.parent/f'generated_g{x.LABELS.index(r["generated_law"])}_{r["index"]:02d}.npz')} for r in prior['rows']]
 new=[{**r,'campaign_epoch':'new16','original_index':r['index'],'index':r['index']+16} for r in cases[0]['rows']]
 assert not (set(r['seed'] for r in old)&set(r['seed'] for r in allrows))
 assert len(set(r['seed'] for r in allrows))==64
 pooled=x.summarize(old+new);width=cases[1]['summary']
 contrasts=[]
 for a,b in zip(pooled,width):
  ma=np.array(a['paired_post_minus_pre_mean']);mb=np.array(b['paired_post_minus_pre_mean'])
  se=np.sqrt(np.array(a['paired_mean_MCSE'])**2+np.array(b['paired_mean_MCSE'])**2)
  contrasts.append({'generated_law':a['generated_law'],'baseline_pooled_minus_width_mean':(ma-mb).tolist(),'independent_MCSE':se.tolist(),
                    'formula':'difference of independent case means; sqrt(MCSE_baseline^2+MCSE_width^2)','scope':'finite scenario comparison; approximate Monte Carlo precision, not survey coverage'})
 controls=[{**f,'case':r['case'],'generated_law':r['generated_law'],'index':r['index']} for r in allrows for f in r.get('refit_controls',[])]
 deltas=[v for r in allrows for f in r['fits'] for check in f.get('checks',[]) for v in check['delta_logL_truth_fit']]
 accepted=sum(f['status']=='ACCEPTED_CONDITIONAL_FIT' for r in allrows for f in r['fits'])
 failures=[{'case':r['case'],'generated_law':r['generated_law'],'index':r['index'],'fits':r['fits'],'score_failures':r.get('failures',[])} for r in allrows if r.get('failures') or any(f['status']!='ACCEPTED_CONDITIONAL_FIT' for f in r['fits'])]
 numerical={'primary_fit_count':128,'accepted_primary_fit_count':accepted,'failure_rows':failures,
            'max_abs_logL_grid_delta':max(deltas),'refit_controls':controls,
            'max_abs_H_refit_shift':max(abs(f['theta_refit_minus_primary'][0]) for f in controls if 'theta_refit_minus_primary' in f),
            'max_abs_B_refit_shift':max(max(abs(v) for v in f['theta_refit_minus_primary'][1:]) for f in controls if 'theta_refit_minus_primary' in f),
            'numerical_control_status':'PASS' if all(f['status']=='PASS' for f in controls) else 'HOLD'}
 achieved=all(s['paired_mean_MCSE'][0]<=c['target']['pooled_baseline_mean_MCSE'] for s in pooled)
 result={'task':'SF08','owner':'HTT','scope':c['scope'],'claim_tier':'CONDITIONAL_DIAGNOSTIC','artifact_mode':'finite_experiment',
         'transfer_source':'solver independent','source_commit':c['base_head'],'source_identity':c['source_identity'],'source_design':c['source_design'],
         'sky_support_status':c['sky_support_status'],'null_mock_status':c['null_mock_status'],
         'covariance_status':'declared fixed per-slot Gaussian proxies and shared eta; only eta width changes between cases',
         'allowed_use':'conditional methods sensitivity, paired Monte Carlo precision and width-case comparison',
         'caveats':['Generator laws and calibration widths are declared scenarios; empirical CF4 completeness/selection remains input-blocked.',
                    'H/B are heliocentric endpoint coefficients, without physical H0/global-tilt or native-Bianchi admission.',
                    'MCSE uses sample SD/sqrt(accepted pairs); conditional descriptive estimate; n=16 widthcase.',
                    'Quadrature and refit diagnostics are measured controls, not a rigorous total numerical error bound.',
                    'Bias/RMSE sample uncertainty is much larger than the paired-difference uncertainty.'],
         'contract_sha256':digest(OUT/'contract.json'),'prior_result_sha256':digest(prior_path),'truth_H_B':c['truth_H_B'],
         'historical_summary_reused':prior['summary'],'cases':cases,'baseline_pooled_summary':pooled,'baseline_pooled_analysis_rows':old+new,
         'width_contrasts':contrasts,'precision_target':{**c['target'],'observed_achieved':achieved,'observed_H_MCSE_by_law':[s['paired_mean_MCSE'][0] for s in pooled]},
         'numerical':numerical,'runtime':c['runtime'],
         'actual_execution_driver':{'path':str(ROOT/'run_cf4_precision_final.py'),'sha256':digest(ROOT/'run_cf4_precision_final.py')},
         'seed_repair':c['seed_repair'],'first_failure':json.loads(Path(c['seed_repair']['failure_receipt_path']).read_text()),
         'analysis_driver':{'path':str(Path(__file__)),'sha256':digest(__file__)},
         'independent_review':'PENDING_PARENT_REVIEW','scientific_admission':'NOT_EVALUATED'}
 write(OUT/'result.json',result)
 import matplotlib;matplotlib.use('Agg')
 from matplotlib import pyplot as plt
 fig,axes=plt.subplots(1,2,figsize=(11,4.3))
 for gi,(a,b) in enumerate(zip(pooled,width)):
  xs=np.array([0,2])+gi
  axes[0].errorbar(xs,[b['paired_post_minus_pre_mean'][0],a['paired_post_minus_pre_mean'][0]],
                   yerr=[b['paired_mean_MCSE'][0],a['paired_mean_MCSE'][0]],fmt=['o','s'][gi],capsize=5,label=['preselection generator','selected-slot generator'][gi])
  axes[1].bar(np.array([0,1])+(-.16,.16)[gi],[a['RMSE'][gi][0],a['paired_post_minus_pre_sd'][0]],width=.30,label=['preselection generator','selected-slot generator'][gi])
 axes[0].set(xlabel='Declared width (mag) / generating law',ylabel='Paired H fit difference (km/s/Mpc)',xticks=[0,1,2,3],xticklabels=['.02 / PRE','.02 / SLOT','.05 / PRE','.05 / SLOT'],xlim=(-.5,3.5))
 axes[0].axhline(0,color='gray',lw=.7);axes[0].legend(fontsize=8)
 axes[0].set_title('Selected-slot fit minus preselection fit\nBars: one MCSE; n=16 (.02), n=32 (.05)')
 axes[1].set(xticks=[0,1],xticklabels=['Matched-law H RMSE','Paired difference SD'],ylabel='km/s/Mpc')
 axes[1].set_title('Baseline (.05 mag), pooled n=32\nEstimator scatter and paired-law scatter')
 fig.suptitle('Conditional generated catalogues on frozen CF4 24-slot design',fontsize=12)
 fig.tight_layout()
 for suffix in ('png','pdf','svg'):fig.savefig(OUT/f'paired_precision.{suffix}',dpi=160)
 plt.close(fig)
 lines=['# SF08 CF4 paired Monte Carlo precision and calibration width','','The fixed extension generated64newcatalogues and128pairedprimaryfits. Previous32catalogues remain unchanged. OwnerHTT; claimtierCONDITIONAL_DIAGNOSTIC. This is a conditional methods experiment on the frozen24-slot design.','',
 '## Predeclared design','',f"The prior n=16 maximum paired H MCSE was{c['target']['prior_max_H_MCSE']:.9f} km/s/Mpc. Target pooled MCSE .015 required{c['target']['minimum_total_pairs_per_law']}pairs perlaw; complete8-pair batches fixed32total (16old+16new). Before any new generation, target, counts, truth, laws and width case were declared in original PREDECLARED.json (b61b816d8c26ce0c263af6ee95fe7cbc8fd77861acad967e4df44076bd090d45). Seed repairs retained that design; the final replacement contract is PREDECLARED_FINAL.json ({digest(OUT/'contract.json')}), sealed before its replacement catalogues were generated. Widthcase count16perlaw was fixed and its precision is measured rather than guaranteed from baseline SD.",'',
 'Generator law stays fixed within each case/law. Truth H/B=[73,100,-200,50], alpha2,s_u250km/s,s_spec30km/s,kappa.725. Baseline etaSD.05mag; newwidth.02mag. Seeds baseline 2026601408+100000*g+i for i0..9 and retained 2026101408+100000*g+i for i10..15, corrected width 2026401408+100000*g+i; these64seeds are disjoint from original32. Early profiles established runtime. Corrected width profile catalogues remain in the final fixed count; profiles affected by seed defects are excluded and preserved.','',
 '## Results','', '| case / generating law | accepted pairs | paired H mean | paired H MCSE | matched-law H bias | matched-law H RMSE |','|---|---:|---:|---:|---:|---:|']
 for label,summary in [('original .05',prior['summary']),('new .05',cases[0]['summary']),('pooled .05',pooled),('new .02',width)]:
  for gi,s in enumerate(summary):lines.append(f"|{label} / {['PRE','SLOT'][gi]}|{s['paired_accepted']}/{s['total_denominator']}|{s['paired_post_minus_pre_mean'][0]:+.8f}|{s['paired_mean_MCSE'][0]:.8f}|{s['bias'][gi][0]:+.8f}|{s['RMSE'][gi][0]:.8f}|")
 lines+=['','H quantities have units km/s/Mpc. Paired statistics are computed from two fits to each identical generated catalogue. MCSE is sampleSD/sqrt(n); it describes simulation precision conditional on this law and design. It is separate from the much larger bias/estimator-scatter uncertainty.', '',f"Observed baseline target achieved: {achieved}. All fixed samples were executed irrespective of interim outcomes. No extra samples were generated to meet the target.",'',
 '## Width comparison and mechanism','']
 for z in contrasts:lines.append(f"{z['generated_law']}: pooledbaseline minus.02width pairedHshift = {z['baseline_pooled_minus_width_mean'][0]:.8f} ± {z['independent_MCSE'][0]:.8f} (MCSE). The two case estimates use disjoint seeds; error propagation uses the sum of their estimated variances.")
 for case in cases:
  eta=case['semantic_tests'][0]['selected_eta_mean_mag'];prediction=x.TRUTH[0]*np.expm1(-eta/x.D.module.A) if x.D else 73*np.expm1(-eta/(5/np.log(10)))
  lines.append(f"Declaredwidth{case['s_eta_mag']:.2f}: conditional PRE eta mean={eta:.10f}mag; first scale approximation73*(exp(-eta_mean/A)-1)={prediction:.8f}km/s/Mpc. This approximation omits finite-distance and velocity/latent-shape corrections; actual fits above use the full frozen law.")
 lines+=['','PRE likelihood integrates shared eta numerator and joint-selection denominator separately; SLOT integrates per-eta normalized slotdensities with its own eta prior. These are distinct normalized generatorlaws. Width sensitivity follows from the change in PRE selection-conditioned eta weights, without selecting an empirical CF4 law.','',
 '## Numerical controls and execution','',f"Primaryfits accepted{accepted}/128; failure rows{len(failures)}. Max truth/fitpoint quadrature |delta logL|={numerical['max_abs_logL_grid_delta']:.9g}, below frozen1e-6. Eight384/96 reoptimization controls checked512/128, status{numerical['numerical_control_status']}; maxHshift={numerical['max_abs_H_refit_shift']:.9g}, maxBshift={numerical['max_abs_B_refit_shift']:.9g}. These measured controls are smaller than pairedMCSE and compare grids/optimization; they are not rigorous global error bounds.",'',
 'An initial seed overlap was reproduced and parent-approved for bounded correction. The original contract/driver, failed execution log, and two excluded width profile catalogues are preserved in FIRST_FAILURE_SEED_OVERLAP.json. A second overlap with the original campaign duplicated 20 baseline raw arrays exactly; PRIOR_SEED_OVERLAP_FALSIFIER.json preserves this failure. Parent approved replacing only those 20 baseline catalogues from independent seeds. The 12 nonoverlapping baseline catalogues and all 32 corrected width catalogues were retained by exact row/raw identity. Two initial width and 20 duplicated baseline catalogues remain preserved but excluded; one interrupted fit is retained in the exit130 log. Thus 64 valid catalogues contribute 128 primary fits, plus 22 excluded historical catalogues with 44 completed primary fits and an interrupted attempt whose partial optimization count is not measured. Counts, target, truth, generator laws and scientific tolerances are unchanged. All raw NPZ were written before fitting, and each row seals its raw SHA and predeclaredcontract. Resume preserves completed rows; raw-only interrupted checkpoints are compared against exact generator replay. Six affected crosslaw tests passed. Profile and extension process receipts, stdout/stderr logs and original executioncopy are retained. Requestedgpt-6.1-sol/high; observedUNKNOWN. Independent review is pending the parent.','',
 '![paired precision and calibration sensitivity](paired_precision.png)','',
 '## Scope and continuation','',
 'This conditional experiment does not provide empirical CF4 selection/completeness, physical H0/globaltilt, coverage of an observed survey, native solver output, or Bayes odds. Actual empirical selection and calibration covariance remain SF13 input requirements. The next useful method step is a source-based correspondence with existing hierarchical selection implementations; do not rerun this completed fixed campaign for assurance.','',
 'The archived result remains bound to its actual scratch execution driver and original source heads. Its raw files and result can be verified byte for byte against the archive manifest. A repository wrapper declares a new source-bound contract for fresh computation after commit; it does not retroactively change the archived contract. A fresh rerun uses the same finite scientific design and seeds, with a new execution/source binding. Commands for a fresh output directory:','','```bash',
 'OPENBLAS_NUM_THREADS=1 /usr/bin/python3 -B scripts/run_solver_free_cf4_precision.py --repo . --declare /tmp/NEW_PREDECLARED.json',
 'OPENBLAS_NUM_THREADS=1 /usr/bin/python3 -B scripts/run_solver_free_cf4_precision.py --repo . --contract /tmp/NEW_PREDECLARED.json --output /tmp/NEW_CAMPAIGN',
 '```']
 (OUT/'report.md').write_text('\n'.join(lines)+'\n')
 paths=sorted(p for p in OUT.rglob('*') if p.is_file() and p.name!='ARTIFACT_MANIFEST.json')
 manifest={'task':'SF08','contract_sha256':digest(OUT/'contract.json'),'files':[{ 'path':str(p.relative_to(OUT)),'sha256':digest(p),'size_bytes':p.stat().st_size} for p in paths]}
 write(OUT/'ARTIFACT_MANIFEST.json',manifest)
 print(json.dumps({'precision':result['precision_target'],'pooled':pooled,'width':width,'numerical':{k:v for k,v in numerical.items() if k!='refit_controls'}},indent=2))
if __name__=='__main__':main()
