#!/usr/bin/env python3
"""SF08 fixed-count conditional campaign; predeclared, resumable paired checkpoints."""
from __future__ import annotations
import argparse,json,sys,time,traceback,hashlib,platform,subprocess
from pathlib import Path
from dataclasses import replace,asdict
import numpy as np
REPO=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
sys.path.insert(0,str(REPO/'scripts'))
import run_solver_free_cf4_crosslaw as x

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
def initial_contract(path):
    prior_path=REPO/'docs/solver_free_research_20261014/results/cf4_crosslaw/result.json'
    prior=json.loads(prior_path.read_text());target=.015
    maximum=max(s['paired_mean_MCSE'][0] for s in prior['summary'])
    needed=int(np.ceil(16*(maximum/target)**2));rounded=8*int(np.ceil(needed/8))
    assert rounded==32
    d=x.load_repo(REPO);source=x.source_identity(REPO,d)
    packet,design,sources=d.intake(REPO,REPO/'docs/observational_reboot_20261014/task_packets/RB07_selected_scenario.json')
    c={'task':'SF08','question':'paired selection-semantics endpoint sensitivity and one calibration-width case on frozen CF4 24-slot design',
       'base_head':source['actual_head'],'source_identity':source,'source_design':sources,
       'crosslaw_driver_sha256':digest(x.__file__),'execution_driver_sha256':digest(__file__),
       'prior_result_sha256':digest(prior_path),'prior_result_path':str(prior_path),
       'truth_H_B':x.TRUTH.tolist(),'baseline':packet['baseline'],'fit_laws':list(x.LABELS),
       'target':{'coordinate':'H','units':'km/s/Mpc','pooled_baseline_mean_MCSE':target,'prior_pairs_per_law':16,
                 'prior_max_H_MCSE':maximum,'formula':'ceil(16*(max_prior_MCSE/target)^2), rounded up to complete 8-pair batches',
                 'minimum_total_pairs_per_law':needed,'fixed_pooled_pairs_per_law':rounded,
                 'predicted_pooled_H_MCSE_by_law':[s['paired_mean_MCSE'][0]*np.sqrt(16/rounded) for s in prior['summary']],
                 'status':'design forecast; observed MCSE evaluated once after fixed count; no adaptive outcome stopping'},
       'cases':[{'id':'baseline','s_eta_mag':.05,'new_pairs_per_law':16,'seed_base':2026101408},
                {'id':'width_002','s_eta_mag':.02,'new_pairs_per_law':16,'seed_base':2026401408}],
       'batch_size_per_law':8,'seed_formula':'seed_base+100000*generating_law_index+catalogue_index',
       'width_case_precision':'fixed equal new count; width-specific precision measured, not guaranteed from baseline SD',
       'numerical_contract':{'fit_reuse':'original fine_fit: same starts, maxiter400 and 1e-6 logL checks; first2 indices audited percase/law',
          'one_refit_control_per_case_generator':[0],'refit_order':[384,96],'check_order':[512,128],
          'max_H_refit_difference_km_s_Mpc':.001,'max_B_refit_difference_km_s':.05,
          'refit_status':'measured optimizer/grid sensitivity control, not rigorous total-error bound'},
       'scope':'conditional generated catalogues; endpoint coefficients; declared population/measurement/calibration scenario',
       'owner':'HTT','claim_tier':'CONDITIONAL_DIAGNOSTIC','artifact_mode':'finite_experiment','transfer_source':'solver independent',
       'null_mock_status':'two declared generating laws; no empirical survey null','sky_support_status':'frozen J2000 directions; count/cohort/method/error proxies conditioned',
       'runtime':{'requested':'gpt-6.1-sol/high','observed':'UNKNOWN'},
       'stopping_rule':'execute fixed64newcatalogues128fits; preserve all failures; no replacement or extra samples by outcome',
       'profile':'first catalogue of eachcase/generator; retained inside fixed sample, not extra pilot samples'}
    c['baseline_checkpoint_dir']=str(Path(__file__).parent/'campaign/baseline')
    original=Path(__file__).parent/'PREDECLARED.json'
    failure=Path(__file__).parent/'FIRST_FAILURE_SEED_OVERLAP.json'
    c['seed_repair']={'original_contract_sha256':digest(original),'original_contract_path':str(original),'failure_receipt_sha256':digest(failure),'failure_receipt_path':str(failure),'approved_by':'parent explicit message','scope':'change widthseedbase2026201408 to2026401408 only; reuse completedbaseline rows without attribution rewrite'}
    c['reused_baseline_rows']={p.name:digest(p) for p in Path(c['baseline_checkpoint_dir']).glob('catalogue_g*.json')}
    planned_seeds=[case['seed_base']+100000*g+i for case in c['cases'] for g in range(2) for i in range(16)]
    if len(set(planned_seeds))!=64:raise ValueError('predeclared case seed overlap')
    write(path,c);print(json.dumps({'contract':str(path),'sha256':digest(path),'target':c['target']}),flush=True)

def run(contract_path,out,profile=False):
    c=json.loads(contract_path.read_text());assert c['task']=='SF08'
    if digest(__file__)!=c['execution_driver_sha256']:raise ValueError('execution driver drift')
    if digest(x.__file__)!=c['crosslaw_driver_sha256']:raise ValueError('imported crosslaw driver drift')
    if digest(c['prior_result_path'])!=c['prior_result_sha256']:raise ValueError('frozen previous result drift')
    d=x.load_repo(REPO);source=x.source_identity(REPO,d)
    if source!=c['source_identity']:raise ValueError('frozen execution source/head changed')
    packet,design,sources=d.intake(REPO,REPO/'docs/observational_reboot_20261014/task_packets/RB07_selected_scenario.json')
    if sources!=c['source_design'] or packet['baseline']!=c['baseline']:raise ValueError('design/scenario drift')
    out.mkdir(parents=True,exist_ok=True);seal=out/'contract.json'
    if seal.exists():
        if seal.read_bytes()!=contract_path.read_bytes():raise ValueError('campaign contract differs')
    else:
        if any(out.iterdir()):raise ValueError('unattributed nonempty output')
        seal.write_bytes(contract_path.read_bytes())
    t0=time.monotonic();progress=[]
    for case in c['cases']:
        caseout=Path(c['baseline_checkpoint_dir']) if case['id']=='baseline' else out/case['id'];caseout.mkdir(exist_ok=True)
        scenario=replace(d.Scenario(**packet['baseline']),s_eta_mag=case['s_eta_mag'])
        sempath=caseout/'semantic_tests.json'
        if not sempath.exists():write(sempath,x.semantic_tests(design,scenario))
        for gi,gl in enumerate(x.LABELS):
            generator=d.SelectedLaw(design,replace(scenario,selection_semantics=gl),256,64)
            for index in range(1 if profile else case['new_pairs_per_law']):
                rowpath=caseout/f'catalogue_g{gi}_{index:02d}.json';npzpath=caseout/f'generated_g{gi}_{index:02d}.npz'
                seed=case['seed_base']+100000*gi+index
                if rowpath.exists():
                    row=json.loads(rowpath.read_text())
                    expected_contract=digest(seal)
                    if case['id']=='baseline' and rowpath.name in c['reused_baseline_rows']:
                        if digest(rowpath)!=c['reused_baseline_rows'][rowpath.name]:raise ValueError('reused baseline row content drift')
                        expected_contract=c['seed_repair']['original_contract_sha256']
                    if row['seed']!=seed or row['generated_law']!=gl or row['contract_sha256']!=expected_contract or row['generated_sha256']!=digest(npzpath):raise ValueError('checkpoint identity mismatch')
                    continue
                if npzpath.exists():
                    raw=dict(np.load(npzpath));raw={k:raw[k] for k in ('mu','Vh','x_log_dA','t_km_s','eta','eta_index','seed')}
                    if int(raw['seed'])!=seed:raise ValueError('raw-only checkpoint seed mismatch')
                    # Regeneration compares content; preserve stored bytes. Exact generator replay seals interrupted checkpoints.
                    replay=x.generate(generator,seed)
                    for key in raw:np.testing.assert_array_equal(raw[key],replay[key])
                else:
                    raw=x.generate(generator,seed)
                    np.savez(npzpath,**raw,group_id=design.group_id,direction=design.direction,sigma_mu=design.sigma_mu,truth_H_B=x.TRUTH)
                sample=x.sample_from(design,raw);fits=[];scores=[];failures=[]
                for fl in x.LABELS:
                    fs=replace(scenario,selection_semantics=fl)
                    try:scores.append(d.SelectedLaw(sample,fs,512,128).log_likelihood(x.TRUTH))
                    except Exception:scores.append(None);failures.append({'stage':'truthscore','law':fl,'traceback':traceback.format_exc()})
                    try:fit=x.fine_fit(sample,fs,index)
                    except Exception:fit={'status':'FIT_FAILURE','failure':traceback.format_exc()}
                    fits.append({'fitted_law':fl,**fit})
                row={'case':case['id'],'s_eta_mag':case['s_eta_mag'],'generated_law':gl,'index':index,'seed':seed,
                     'contract_sha256':digest(seal),'generated_sha256':digest(npzpath),'eta_generated_mag':float(raw['eta']),
                     'fits':fits,'same_truth_logL_post_minus_pre':scores[1]-scores[0] if None not in scores else None,'failures':failures}
                if index==0:
                    controls=[]
                    for fl,fit in zip(x.LABELS,fits):
                        try:
                            fs=replace(scenario,selection_semantics=fl)
                            model=d.SelectedLaw(sample,fs,384,96)
                            high=model.fit(starts=[np.array(fit['theta'])/x.SCALE],maxiter=400)
                            high_theta=np.array(high['best']['theta']);diff=high_theta-np.array(fit['theta'])
                            finer=d.SelectedLaw(sample,fs,512,128)
                            dl=abs(model.log_likelihood(high_theta)-finer.log_likelihood(high_theta))
                            controls.append({'law':fl,'refit':high,'theta_refit_minus_primary':diff.tolist(),'logL_refinement_difference':dl,
                                             'status':'PASS' if abs(diff[0])<.001 and np.max(abs(diff[1:]))<.05 and dl<1e-6 else 'HOLD_NUMERICAL_CONTROL'})
                        except Exception:controls.append({'law':fl,'status':'CONTROL_FAILURE','failure':traceback.format_exc()})
                    row['refit_controls']=controls
                write(rowpath,row);record={'case':case['id'],'progress':[gi,index],'fits':[f['status'] for f in fits],'elapsed_seconds':time.monotonic()-t0};progress.append(record)
                print(json.dumps(record),flush=True)
        rows=[json.loads(p.read_text()) for p in sorted(caseout.glob('catalogue_g*.json'))]
        write(caseout/'checkpoint_summary.json',{'case':case['id'],'planned_per_law':case['new_pairs_per_law'],'rows_completed':len(rows),'summary':x.summarize(rows)})
    write(out/('profile_receipt.json' if profile else 'execution_receipt.json'),{'command':sys.argv,'cwd':str(Path.cwd()),'exit_code':0,'elapsed_seconds':time.monotonic()-t0,
          'completed_this_invocation':len(progress),'contract_sha256':digest(seal),'executable':sys.executable,'python':platform.python_version(),'numpy':np.__version__,
          'scipy':__import__('scipy').__version__,'matplotlib':__import__('matplotlib').__version__,'runtime':c['runtime']})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--declare',type=Path);p.add_argument('--contract',type=Path);p.add_argument('--output',type=Path);p.add_argument('--profile',action='store_true');a=p.parse_args()
    if a.declare:initial_contract(a.declare)
    else:run(a.contract,a.output,a.profile)
