#!/usr/bin/env python3
"""Run the frozen RB07 selected CF4 scenario in bounded stages."""
from __future__ import annotations

import argparse
import importlib.util
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
for sub in ('htt','htt/src','htt/htt'):
    sys.path.insert(0,str(ROOT/sub))
from obsstat.catalogs.cf4_grouped_observations import load_grouped_observations
module_path=Path(os.environ.get('HTT_RB07_MODULE_PATH',
    ROOT/'htt/htt/htt/infer/reboot_cf4_selected_law.py'))
spec=importlib.util.spec_from_file_location('rb07_selected_law',module_path)
module=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=module
spec.loader.exec_module(module)
Sample=module.Sample
Scenario=module.Scenario
SelectedLaw=module.SelectedLaw
selected_sample=module.selected_sample
importance_posterior=module.importance_posterior
posterior_latent_bridge=module.posterior_latent_bridge


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):
            sha.update(block)
    return sha.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False,default=lambda x:
        x.item() if isinstance(x,np.generic) else x.tolist() if isinstance(x,np.ndarray) else str(x))+'\n')


def intake(root, packet_path):
    packet = json.loads(packet_path.read_text())
    if packet['task']!='RB07' or packet['base_head']!='d1064878534b7ac6b32669d6e335e7b60e722754':
        raise ValueError('frozen RB07 task/base identity changed')
    sources = {}
    for rel, expected in packet['source_sha256'].items():
        path = root/rel
        actual = digest(path)
        if actual!=expected:
            raise ValueError('frozen source SHA mismatch: '+rel)
        sources[rel] = {'sha256':actual,'size_bytes':path.stat().st_size}
    base = root/'workdir/raw/cf4_full'
    catalog = load_grouped_observations(base/'table3.dat.gz',base/'table4.dat.gz',base/'ReadMe')
    sample = selected_sample(catalog,packet)
    return packet,sample,{'source_files':sources,'selected_group_ids':sample.group_id.tolist(),
        'selected_rows':len(sample.group_id),'candidate_groups':len(catalog.group_id),
        'selection':packet['subset']['selection'],'release':catalog.provenance['release'],
        'source_frame':catalog.provenance['frame'],'packet_sha256':digest(packet_path),
        'method_presence_role':'SNIa-only eligibility, never modulus mixing weight'}


def make_law(sample,scenario,order=(192,40)):
    return SelectedLaw(sample,scenario,distance_order=order[0],eta_order=order[1])


def profile(sample,scenario):
    records = []
    for size in (1,len(sample.group_id)):
        sub = Sample(*(np.asarray(getattr(sample,name))[:size] for name in
                        ('group_id','mu','sigma_mu','raw_vh','direction')))
        law=make_law(sub,scenario,(128,24))
        start=time.monotonic();f,z=law.row_terms([73,0,0,0])
        records.append({'rows':size,'distance_order':128,'eta_order':24,
                        'elapsed_seconds':time.monotonic()-start,
                        'finite_f':bool(np.isfinite(f).all()),'finite_Z':bool(np.isfinite(z).all())})
    return records


def fit_and_convergence(sample,scenario):
    law=make_law(sample,scenario)
    fit=law.fit()
    theta=fit['best']['theta']
    grids=[]
    for d,e in ((128,24),(192,40),(256,64)):
        start=time.monotonic();v=make_law(sample,scenario,(d,e)).log_likelihood(theta)
        grids.append({'distance':d,'eta':e,'logL_at_fitted_theta':v,
                      'elapsed_seconds':time.monotonic()-start})
    difference=abs(grids[1]['logL_at_fitted_theta']-grids[2]['logL_at_fitted_theta'])
    return law,{'fit':fit,'quadrature':grids,'refined_abs_logL_difference':difference,
                'quadrature_acceptance':difference<1e-6}


def plot(output, sample, result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes=plt.subplots(1,2,figsize=(10,4))
    axes[0].errorbar(np.arange(len(sample.group_id)),sample.mu,yerr=sample.sigma_mu,
                     fmt='.',ms=5,lw=.7)
    axes[0].axhspan(31,35,alpha=.1,color='tab:green')
    axes[0].set(xlabel='Frozen selected group index',ylabel='DMzp (mag)')
    q=result.get('quadrature',[])
    if q:
        axes[1].plot([x['distance'] for x in q],[x['logL_at_fitted_theta'] for x in q],'o-')
        axes[1].set(xlabel='Distance quadrature order',ylabel='Selected log L at fitted theta')
    else:
        axes[1].text(.1,.5,'Profile/intake stage',transform=axes[1].transAxes)
    fig.suptitle('RB07 conditional selected CF4 SNIa scenario; diagnostic only')
    fig.tight_layout()
    for suffix in ('png','pdf'):
        fig.savefig(output/('diagnostic.'+suffix),dpi=150)
    plt.close(fig)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=('profile','fit','campaign','posterior','latent'),required=True)
    parser.add_argument('--repo-root',type=Path,default=ROOT)
    parser.add_argument('--packet',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reuse-sensitivities',type=Path,help='preserved failed campaign sensitivity checkpoints; exact source/scenario checked')
    parser.add_argument('--fit-json',type=Path,help='fit/campaign result JSON for posterior stage')
    parser.add_argument('--posterior-json',type=Path,help='posterior result JSON for latent stage')
    args=parser.parse_args(argv)
    root=args.repo_root.resolve();output=args.output.resolve()
    packet_path=args.packet or root/'docs/observational_reboot_20261014/task_packets/RB07_selected_scenario.json'
    output.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    receipt={'task':'RB07','stage':args.stage,'command':sys.argv,'cwd':os.getcwd(),
             'python':sys.version,'numpy':np.__version__,'platform':platform.platform(),
             'requested_author_runtime':'gpt-6-sol/high','observed_author_runtime':'UNKNOWN',
             'scientific_admission':'NOT_EVALUATED'}
    for key,cmd in (('git_head',['rev-parse','HEAD']),('git_status',['status','--porcelain=v1'])):
        run=subprocess.run(['git','-C',str(root),*cmd],capture_output=True,text=True)
        receipt[key]=run.stdout.strip() if run.returncode==0 else 'UNAVAILABLE'
    try:
        packet,sample,sources=intake(root,packet_path)
        scenario=Scenario(**packet['baseline'])
        write_json(output/'source_subset_receipt.json',sources)
        result={'task':'RB07','owner':'HTT','claim_tier':'CONDITIONAL_DIAGNOSTIC',
                'scope':'24 selected SNIa-only CF4 heliocentric endpoint scenario',
                'selection_semantics':scenario.selection_semantics,'scenario':asdict(scenario),
                'group_ids':sample.group_id.tolist(),'transfer_source':'none',
                'null_status':'NOT_CALIBRATED','covariance_status':'DECLARED_CONDITIONAL_GAUSSIAN',
                'allowed_use':'fixed selected-sample scenario sensitivity only',
                'forbidden_uses':['H0 measurement','CMB velocity','global tilt','Bianchi family identification'],
                'source_subset_receipt':'source_subset_receipt.json'}
        if args.stage=='profile':
            result['profile']=profile(sample,scenario)
        elif args.stage in ('fit','campaign'):
            result['profile']=profile(sample,scenario)
            law,baseline=fit_and_convergence(sample,scenario)
            result.update(baseline)
            if not baseline['quadrature_acceptance']:
                raise RuntimeError('192/40 to 256/64 quadrature acceptance failed')
            result['reference_difference']={'H':baseline['fit']['best']['theta'][0]-packet['reference']['H'],
                'B':(np.array(baseline['fit']['best']['theta'][1:])-packet['reference']['B']).tolist(),
                'logL':baseline['fit']['best']['logL']-packet['reference']['logL']}
            result['fitted_predictive']=law.predictive(baseline['fit']['best']['theta'],draws=128)
            if args.stage=='campaign':
                sensitivity=[]
                for i,change in enumerate(packet['finite_sensitivities']):
                    variant=replace(scenario,**change)
                    saved=args.reuse_sensitivities/f'sensitivity_{i:02d}.json' if args.reuse_sensitivities else None
                    if saved is not None and saved.exists():
                        prior_sources=json.loads((saved.parent/'source_subset_receipt.json').read_text())
                        row=json.loads(saved.read_text())
                        if prior_sources!=sources or row['index']!=i or row['change']!=change:
                            raise ValueError('sensitivity checkpoint identity mismatch')
                        result.setdefault('reused_checkpoints',[]).append({'path':str(saved),'sha256':digest(saved)})
                    else:
                        _,check=fit_and_convergence(sample,variant)
                        row={'index':i,'change':change,**check}
                    sensitivity.append(row)
                    write_json(output/f'sensitivity_{i:02d}.json',row)
                result['sensitivities']=sensitivity
                loo=[]
                for j,gid in enumerate(sample.group_id):
                    # Optimize the retained selected-slot law: known held slot Z_j
                    # stays in the numerator and every Z stays in the denominator.
                    def objective(q):
                        return -law.log_likelihood([q[0],*(100*q[1:])],held_index=j)
                    start_q=np.array([baseline['fit']['best']['theta'][0],
                                      *(np.array(baseline['fit']['best']['theta'][1:])/100)])
                    opt=minimize(objective,start_q,method='L-BFGS-B',bounds=[(40,110),(-15,15),(-15,15),(-15,15)],
                                 options={'maxiter':400,'ftol':2e-12,'gtol':1e-6})
                    if not opt.success:
                        raise RuntimeError(f'LOO fit failed for group {int(gid)}: {opt.message}')
                    held_theta=[float(opt.x[0]),*(100*opt.x[1:])]
                    full=law.log_likelihood(held_theta)
                    held=law.log_likelihood(held_theta,held_index=j)
                    row={'group_id':int(gid),'fit_theta':held_theta,'held_logL':held,
                         'held_predictive_logdensity':full-held,'optimizer_success':bool(opt.success),
                         'optimizer_message':str(opt.message),'nfev':int(opt.nfev)}
                    loo.append(row);write_json(output/f'loo_{j:02d}.json',row)
                result['leave_one_group_out']=loo
        elif args.stage=='posterior':
            if args.fit_json is None:
                raise ValueError('posterior stage requires --fit-json')
            prior=json.loads(args.fit_json.read_text())
            if prior.get('task')!='RB07' or prior.get('group_ids')!=sample.group_id.tolist() or \
                    prior.get('scenario')!=asdict(scenario) or \
                    prior.get('selection_semantics')!='PRESELECTION_SHARED_PRIOR' or \
                    prior.get('quadrature_acceptance') is not True:
                raise ValueError('posterior input fit identity/convergence mismatch')
            prior_sources=json.loads((args.fit_json.parent/'source_subset_receipt.json').read_text())
            if prior_sources != sources:
                raise ValueError('posterior source/subset receipt differs')
            result['input_fit_sha256']=digest(args.fit_json)
            result['posterior']=importance_posterior(make_law(sample,scenario),prior['fit']['best']['theta'])
            if 'posterior_predictive' in result['posterior']:
                result['posterior']['posterior_predictive']['generator_scope']='FRESH_SELECTED_CATALOGUE'
        else:
            if args.posterior_json is None:
                raise ValueError('latent stage requires --posterior-json')
            prior=json.loads(args.posterior_json.read_text())
            if prior.get('task')!='RB07' or prior.get('group_ids')!=sample.group_id.tolist() or \
                    prior.get('scenario')!=asdict(scenario) or \
                    prior.get('selection_semantics')!='PRESELECTION_SHARED_PRIOR':
                raise ValueError('latent input posterior identity/scenario mismatch')
            prior_sources=json.loads((args.posterior_json.parent/'source_subset_receipt.json').read_text())
            if prior_sources!=sources:
                raise ValueError('latent input source/subset receipt differs')
            result['input_posterior_sha256']=digest(args.posterior_json)
            posterior=prior.get('posterior',{})
            if posterior.get('status')!='NUMERICAL_POSTERIOR_DIAGNOSTIC_ONLY':
                result['latent_bridge']={'status':'HOLD_POSTERIOR_IMPORTANCE_DIAGNOSTICS',
                                         'upstream_status':posterior.get('status','MISSING'),
                                         'physical_MES':{'status':'UNKNOWN_PHYSICAL_SECTOR','unknown_mass':1.0}}
            else:
                arrays,summary=posterior_latent_bridge(make_law(sample,scenario),posterior)
                path=output/'posterior_latent_repeated_measurement.npz'
                np.savez_compressed(path,**arrays)
                summary['array_artifact']=path.name
                summary['array_sha256']=digest(path)
                summary['array_fields']={name:{'shape':list(value.shape),'dtype':str(value.dtype)}
                                         for name,value in arrays.items()}
                result['latent_bridge']=summary
        write_json(output/'result.json',result)
        plot(output,sample,result)
        report='# RB07 selected CF4 scenario\n\n'
        report+='HTT conditional diagnostic using 24 frozen SNIa-only groups. H/B are heliocentric endpoint coefficients.\n\n'
        report+='Shared eta is integrated once. Preselection and selected-slot-prior normalizers are different laws. Population, widths, calibration and finite-distance kappa are declared scenarios.\n\n'
        report+='No CF4 completeness claim, H0 admission, CMB-velocity/global-tilt inference, or physical remainder bound follows.\n\n'
        report+='Fresh selected-catalogue prediction and same-state repeated-measurement PPC are distinct. Physical MES mapping remains unknown.\n\n'
        report+='See result.json and source_subset_receipt.json for numerical/source detail.\n'
        (output/'report.md').write_text(report)
        receipt['exit_code']=0
    except Exception as exc:
        receipt['exit_code']=1;receipt['error']=type(exc).__name__+': '+str(exc)
        (output/'failure.log').write_text(traceback.format_exc())
    receipt['elapsed_seconds']=time.monotonic()-start
    receipt['code_sha256']=digest(Path(__file__))
    receipt['law_sha256']=digest(module_path)
    write_json(output/'execution_receipt.json',receipt)
    print(json.dumps({'stage':args.stage,'exit_code':receipt['exit_code'],
                      'output':str(output),'elapsed_seconds':receipt['elapsed_seconds']}))
    return receipt['exit_code']

if __name__=='__main__':
    raise SystemExit(main())
