#!/usr/bin/env python3
"""Bounded OBS03-SYNTH-v1 validation; actual CF4 is descriptive geometry only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'htt'),str(ROOT/'htt/htt'),str(ROOT/'htt/src')]
import numpy as np
import scipy
from scipy.stats import binom,binomtest
from htt.infer.cf4_latent_modulus import (TRUTH,SCALE,BOUNDS,ORDERS,SEED,generate_catalogue,fit_catalogue,
    refined_fit,check_quadrature,LatentModulusLikelihood,observed_hessian,local_response_svd)


def catalogue_record(cat):
    return {'slot_ids':cat.slot_id.tolist(),'directions':cat.direction.tolist(),'shell':cat.shell.tolist(),
            'method':cat.method.tolist(),'mu':cat.mu.tolist(),'Vh':cat.vh.tolist(),'shared_anchor':cat.anchor,
            'selected':cat.selected,'proposal_counts':cat.proposals.tolist()}


def curvature_record(cat,fit):
    if fit['estimate'] is None:
        return {'status':'NUMERICAL_HOLD'}
    theta=np.array(fit['estimate']);like=LatentModulusLikelihood(cat,tuple(fit['order']))
    results={}
    for anchored in (False,True):
        try:
            h=observed_hessian(like,theta/SCALE,.01)
            if not anchored:h[2,2]-=(SCALE[2]/.03)**2
            eig=np.linalg.eigvalsh(h);tol=8*np.finfo(float).eps*3*np.linalg.norm(h,2)
            results['anchor_augmented' if anchored else 'data_only']={
                'observed_information_scaled':h.tolist(),'eigenvalues':eig.tolist(),
                'positive_rank':int(np.sum(eig>tol)),'negative_eigenvalue_count':int(np.sum(eig < -tol)),
                'tolerance':float(tol),'scale':SCALE.tolist()}
        except ValueError as e:results['anchor_augmented' if anchored else 'data_only']={'status':'HOLD','reason':str(e)}
    return results


def controls(cat,order,child_seed):
    truth_svd={};fit=fit_catalogue(cat,order)
    truth_svd['truth']={'data_only':local_response_svd(cat,TRUTH),'anchor_augmented':local_response_svd(cat,TRUTH,anchor=True)}
    if fit['estimate'] is not None:
        truth_svd['optimum']={'data_only':local_response_svd(cat,fit['estimate']),
                              'anchor_augmented':local_response_svd(cat,fit['estimate'],anchor=True)}
    omissions=[]
    for method in (0,1):
        retained=cat.subset(cat.method!=method);ff=fit_catalogue(retained,order)
        omissions.append({'omitted_method':method,'retained_slot_ids':retained.slot_id.tolist(),'fit':ff,
            'truth_svd':local_response_svd(retained,TRUTH,anchor=True),
            'optimum_svd':local_response_svd(retained,ff['estimate'],anchor=True) if ff['estimate'] is not None else None})
    depths=[]
    for shell in (0,1):
        retained=cat.subset(cat.shell==shell);ff=fit_catalogue(retained,order)
        depths.append({'retained_shell':shell,'retained_slot_ids':retained.slot_id.tolist(),'fit':ff,
            'finite_width_truth_svd':local_response_svd(retained,TRUTH,anchor=True),
            'zero_shell_width_control':local_response_svd(retained,TRUTH,anchor=True,zero_shell_width=True),
            'estimable_zero_width_combination':'B+%g*A'%[40,100][shell]})
    complete=generate_catalogue(np.random.default_rng(child_seed),selected=False)
    complete_fit=fit_catalogue(complete,order)
    negative=fit_catalogue(cat,order,omit_selection_normalizer=True)
    inject=generate_catalogue(np.random.default_rng(child_seed),method1_bias=.08)
    injected_fit=fit_catalogue(inject,order)
    removed=inject.subset(inject.method!=1);removed_fit=fit_catalogue(removed,order)
    return {'local_response_svd':truth_svd,'replicate0_observed_curvature':curvature_record(cat,fit),
            'method_leave_one_out':omissions,'shell_deletions':depths,
            'S1_control':{'catalogue':catalogue_record(complete),'fit':complete_fit,
                'normalizer_log_values':LatentModulusLikelihood(complete,order).row_terms(TRUTH)[1].tolist()},
            'selected_data_omitted_normalizer_negative_control':negative,
            'unmodelled_method1_plus_0_08_mag':{'catalogue':catalogue_record(inject),'fit':injected_fit,
                'method1_omission_fit':removed_fit,'retained_slot_ids':removed.slot_id.tolist()},
            'negative_control_interpretation':'observed contrasts only; no required noisy sign or significance gate'}


def descriptive_cf4(output):
    """Read coordinates/moduli for coverage and reuse reviewed response machinery."""
    from obsstat.catalogs.cf4_grouped_observations import load_grouped_observations,METHODS
    from htt.infer.cf4_information import NoiseScenario,profiled_rows,information
    cat=load_grouped_observations(ROOT/'workdir/raw/cf4_full/table3.dat.gz',ROOT/'workdir/raw/cf4_full/table4.dat.gz',ROOT/'workdir/raw/cf4_full/ReadMe')
    x,n,r,z=profiled_rows(cat,NoiseScenario('descriptive_100_300',100,300,True,True))
    masks={'full':np.ones(len(r),bool),'central49_51':(r>=np.quantile(r,.49))&(r<=np.quantile(r,.51))}
    masks.update({'delete_presence_'+name:~cat.method_presence[:,i] for i,name in enumerate(METHODS)})
    spectra={name:information(x,n,mask) for name,mask in masks.items() if mask.any()}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(1,2,figsize=(12,4.5))
    for j,name in enumerate(METHODS):
        ax[0].hist(r[cat.method_presence[:,j]],bins=np.geomspace(max(r.min(),.01),r.max(),30),histtype='step',label=name)
    ax[0].set_xscale('log');ax[0].set_xlabel('fiducial DMzp/Vh distance proxy [Mpc]');ax[0].set_ylabel('group count; method presence overlaps')
    for name,inf in spectra.items():
        s=np.array(inf['singular_values']);s[s<=inf['rank_tolerance']]=np.nan
        ax[1].semilogy(np.arange(1,len(s)+1),s,'o-',label=name)
    ax[1].set_xlabel('singular mode');ax[1].set_ylabel('OBS02 fixed-scale local response / scenario noise')
    for a in ax:a.legend(fontsize=6);a.grid(alpha=.2)
    fig.suptitle('Real CF4 descriptive coverage only; no response fit; selection not bound')
    fig.tight_layout();fig.savefig(output/'real_cf4_descriptive.png',dpi=160);fig.savefig(output/'real_cf4_descriptive.pdf');plt.close(fig)
    return {'row_count':len(r),'provenance':cat.provenance,'selection':'SELECTION_LAW_NOT_BOUND','physical_fit':'NOT_PERFORMED',
        'spectra':{name:{k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in inf.items()} for name,inf in spectra.items()},
        'method_presence_counts':dict(zip(METHODS,cat.method_presence.sum(axis=0).tolist()))}


def coverage_summary(records):
    n=len(records);valid=[r for r in records if r['fit']['status']=='FIT_NUMERICALLY_STABLE' and r['quadrature']['passed']]
    estim=np.array([r['fit']['estimate'] for r in valid])
    failed=n-len(valid);values={}
    for j,name in enumerate(('B','A')):
        k=sum(r['fit']['interval95'][j][0]<=TRUTH[j]<=r['fit']['interval95'][j][1] for r in valid)
        ci=binomtest(k,n).proportion_ci(confidence_level=.95,method='exact')
        mean=float(np.mean(estim[:,j])) if len(valid)>1 else None
        sd=float(np.std(estim[:,j],ddof=1)) if len(valid)>1 else None
        bias_z=float((mean-TRUTH[j])/(sd/np.sqrt(n))) if sd and failed==0 else None
        values[name]={'covered':int(k),'denominator':n,'coverage':k/n,'exact_binomial_CI95':[float(ci.low),float(ci.high)],
            'undercoverage_p':float(binom.cdf(k,n,.95)),'mean_estimate':mean,'sample_SD':sd,'bias_MC_z':bias_z}
    passed=n==128 and failed==0 and all(abs(v['bias_MC_z'])<=3.5 and v['undercoverage_p']>=.005 for v in values.values())
    return {'status':'SCOPED_MANUFACTURED_RECOVERY_PASS' if passed else ('PILOT_ONLY' if n!=128 else 'SCOPED_MANUFACTURED_RECOVERY_FAIL'),
        'failed_boundary_unstable_or_quadrature_fits':failed,'primary_contrasts':values,
        'scope':'approximate marginal Wald interval Monte Carlo; manufactured law only, not exact theorem or real-data coverage'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/observational_methods_20261013/OBS-03')
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=True)
    children=np.random.SeedSequence(SEED).spawn(128)
    start=time.monotonic();cat0=generate_catalogue(np.random.default_rng(children[0]));ref=refined_fit(cat0)
    report={'task':'OBS03-SYNTH-v1','frozen_base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'truth':TRUTH.tolist(),'parameter_box':BOUNDS.tolist(),'seed':SEED,'rng':'PCG64 with SeedSequence.spawn(128)',
        'requested_runtime':'gpt-6.1-sol/medium','observed_runtime':'UNKNOWN','python':sys.executable,'numpy':np.__version__,
        'scipy':scipy.__version__,'python_version':platform.python_version(),'refinement_pilot':ref,
        'claim_tier':'diagnostic_only','transfer_source':'none','real_scientific_admission':'HOLD','records':[]}
    if ref['status']!='QUADRATURE_ACCEPTED':
        report['status']='NUMERICAL_HOLD'
        (out/('pilot.json' if args.pilot else 'validation.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'status':report['status'],'elapsed_seconds':time.monotonic()-start}));return
    order=tuple(ref['accepted_order']);low_order=ORDERS[ORDERS.index(order)-1]
    report['accepted_common_order']=list(order)
    report['replicate0_catalogue']=catalogue_record(cat0)
    report['controls']=controls(cat0,order,children[0])
    count=1 if args.pilot else 128
    for i in range(count):
        cat=cat0 if i==0 else generate_catalogue(np.random.default_rng(children[i]))
        high=ref['fits'][-1] if i==0 else fit_catalogue(cat,order)
        low=ref['fits'][-2] if i==0 else fit_catalogue(cat,low_order)
        check=check_quadrature(cat,low_order,order,low,high)
        record={'replicate':i,'seed_spawn_key':list(children[i].spawn_key),'catalogue':catalogue_record(cat),
            'fit':high,'lower_order_fit':low,'quadrature':check}
        report['records'].append(record)
        # Durable bounded checkpoint includes failures; failed fits stay denominator.
        if (i+1)%16==0:
            (out/'validation.partial.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
            print(json.dumps({'completed':i+1,'elapsed_seconds':time.monotonic()-start}),flush=True)
    report['coverage']=coverage_summary(report['records'])
    report['status']='NUMERICAL_HOLD' if any(not r['quadrature']['passed'] for r in report['records']) else report['coverage']['status']
    report['real_cf4_descriptive']=descriptive_cf4(out)
    report['elapsed_seconds']=time.monotonic()-start
    report['source_file_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        (ROOT/'htt/htt/htt/infer/cf4_latent_modulus.py',ROOT/'scripts/cf4_latent_modulus_validation.py',ROOT/'tests/htt/test_cf4_latent_modulus.py')}
    (out/('pilot.json' if args.pilot else 'validation.json')).write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':report['status'],'replicates':count,'elapsed_seconds':report['elapsed_seconds'],
        'coverage':report['coverage']}),flush=True)
if __name__=='__main__':main()
