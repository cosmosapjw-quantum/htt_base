#!/usr/bin/env python3
"""Finite CF4 fixed-design cross-law experiment; conditional generated catalogues."""
from __future__ import annotations
import argparse, hashlib, importlib, json, platform, subprocess, sys, time, traceback
from pathlib import Path
from dataclasses import asdict, replace
import numpy as np
from scipy.special import logsumexp
from scipy.stats import truncnorm
TRUTH=np.array([73.,100.,-200.,50.])
LABELS=('PRESELECTION_SHARED_PRIOR','SELECTED_SLOT_PRIOR')
SCALE=np.array([1.,100.,100.,100.])
EXPECTED_HEAD='89621f4c9a6f63449813587a0fadeb13287f8e10'
D=None
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def load_repo(repo):
    global D
    sys.path.insert(0,str(repo/'scripts'))
    D=importlib.import_module('run_reboot_cf4_selected')
    return D
def eta_weights(model,truth=TRUTH):
    _,z=model.row_terms(truth)
    logw=model.log_eta_w.copy()
    if model.scenario.selection_semantics==LABELS[0]:logw=logw+z.sum(axis=0)
    return np.exp(logw-logsumexp(logw)),z
def moments(model,truth=TRUTH):
    ew,z=eta_weights(model,truth);s=model.scenario;dist=np.exp(model.x)
    m=truth[0]*dist[None,:]+(model.sample.direction@truth[1:])[:,None]+s.kappa*(75*dist)**2/D.module.C
    mean=25+D.module.A*model.x[None,:]+D.module.K*m
    sd=np.sqrt(model.sample.sigma_mu[:,None]**2+D.module.K**2*s.s_u_km_s**2)
    result=[float(ew@model.eta/s.s_eta_mag),float(ew@(model.eta**2)/s.s_eta_mag**2)]
    for i in range(len(model.sample.group_id)):
        lo=(31-mean[i,:,None]-model.eta)/sd[i,:,None]
        hi=(35-mean[i,:,None]-model.eta)/sd[i,:,None]
        ls=D.module.log_cdf_interval(lo,hi)
        joint=np.exp(model.log_gw[:,None]+ls-z[i])*ew
        result.extend([float(np.sum(joint*model.x[:,None])),float(np.sum(joint*model.x[:,None]**2))])
        for cut in (33,34):
            lc=D.module.log_cdf_interval(lo,(cut-mean[i,:,None]-model.eta)/sd[i,:,None])
            result.append(float(np.sum(joint*np.exp(lc-ls))))
    return np.array(result)
def generate(model,seed,truth=TRUTH):
    """Existing RB07 selected generator with explicit eta semantics."""
    rng=np.random.default_rng(seed);ew,_=eta_weights(model,truth)
    ei=int(rng.choice(len(model.eta),p=ew));eta=float(model.eta[ei])
    s=model.scenario;dist=np.exp(model.x);n=len(model.sample.group_id)
    mu=np.empty(n);vh=np.empty(n);x=np.empty(n);t=np.empty(n)
    for i in range(n):
        m=truth[0]*dist+model.sample.direction[i]@truth[1:]+s.kappa*(75*dist)**2/D.module.C
        mean=25+D.module.A*model.x+D.module.K*m+eta
        var=model.sample.sigma_mu[i]**2+D.module.K**2*s.s_u_km_s**2;sd=np.sqrt(var)
        lo=(31-mean)/sd;hi=(35-mean)/sd
        lp=model.log_gw+D.module.log_cdf_interval(lo,hi)
        ix=int(rng.choice(len(dist),p=np.exp(lp-logsumexp(lp))))
        x[i]=model.x[ix];mu[i]=truncnorm.rvs(lo[ix],hi[ix],loc=mean[ix],scale=sd,random_state=rng)
        tm=m[ix]+D.module.K*s.s_u_km_s**2/var*(mu[i]-mean[ix])
        tv=s.s_u_km_s**2-(D.module.K*s.s_u_km_s**2)**2/var
        t[i]=rng.normal(tm,np.sqrt(tv))
        vh[i]=D.module.C*np.expm1((t[i]+rng.normal(0,s.s_spec_km_s))/D.module.C)
    return {'mu':mu,'Vh':vh,'x_log_dA':x,'t_km_s':t,'eta':eta,'eta_index':ei,'seed':seed}
def sample_from(design,raw):
    return D.Sample(design.group_id,raw['mu'],design.sigma_mu,raw['Vh'],design.direction)
def fine_fit(sample,scenario,index):
    """Frozen1e-6 checks, with high-order audit for first2 per generator."""
    t0=time.monotonic();checks=[];fit=None;status='NOT_RUN'
    for order,next_order in [((192,40),(256,64)),((384,96),(512,128))]:
        model=D.SelectedLaw(sample,scenario,*order)
        starts=None if fit is None else [np.array(fit['best']['theta'])/SCALE]
        fit=model.fit(starts=starts,maxiter=400);theta=np.array(fit['best']['theta'])
        finer=D.SelectedLaw(sample,scenario,*next_order)
        delta=[abs(model.log_likelihood(v)-finer.log_likelihood(v)) for v in (TRUTH,theta)]
        checks.append({'fit_order':list(order),'check_order':list(next_order),'delta_logL_truth_fit':delta})
        if max(delta)<1e-6:
            if order==(192,40) and index<2:
                coarse=D.SelectedLaw(sample,scenario,384,96);fine=D.SelectedLaw(sample,scenario,512,128)
                audit=[abs(coarse.log_likelihood(v)-fine.log_likelihood(v)) for v in (TRUTH,theta)]
                checks.append({'audit_orders':[[384,96],[512,128]],'delta_logL_truth_fit':audit})
                if max(audit)>=1e-6:continue
            q=theta/SCALE
            boundary=bool(np.any(np.isclose(q,np.array(D.module.BOUNDS)[:,0],atol=1e-5)) or np.any(np.isclose(q,np.array(D.module.BOUNDS)[:,1],atol=1e-5)))
            status='ACCEPTED_CONDITIONAL_FIT' if not boundary else 'BOUNDARY_FIT_EXCLUDED'
            break
    return {'status':status if status!='NOT_RUN' else 'QUADRATURE_UNRESOLVED','theta':fit['best']['theta'],'logL':fit['best']['logL'],'fit_success':fit['best']['success'],'checks':checks,'seconds':time.monotonic()-t0}
def semantic_tests(design,scenario):
    tests=[];models=[D.SelectedLaw(design,replace(scenario,selection_semantics=s),256,64) for s in LABELS]
    for model in models:
        f,z=model.row_terms(TRUTH)
        manual=(logsumexp(model.log_eta_w+f.sum(0))-logsumexp(model.log_eta_w+z.sum(0))) if model.scenario.selection_semantics==LABELS[0] else logsumexp(model.log_eta_w+(f-z).sum(0))
        err=abs(float(manual)-model.log_likelihood(TRUTH));assert err<1e-12
        md=float(np.max(abs(moments(model)-moments(D.SelectedLaw(design,model.scenario,384,96)))))
        assert md<1e-4
        ew,_=eta_weights(model);eta_mean=float(ew@model.eta);eta_sd=float(np.sqrt(ew@(model.eta-eta_mean)**2))
        raw=generate(model,12345);assert np.all((raw['mu']>=31)&(raw['mu']<=35));assert np.isfinite(raw['Vh']).all()
        if model.scenario.selection_semantics==LABELS[1]:
            assert abs(eta_mean)<1e-12 and abs(eta_sd-scenario.s_eta_mag)<1e-12
        tests.append({'law':model.scenario.selection_semantics,'formula_error':err,'moment_grid_max_scaled_delta':md,'selected_eta_mean_mag':eta_mean,'selected_eta_sd_mag':eta_sd,'selection_support':'PASS'})
    return tests
def summarize(rows):
    result=[]
    for gl in LABELS:
        allrows=[r for r in rows if r['generated_law']==gl]
        accepted=[r for r in allrows if all(f.get('status')=='ACCEPTED_CONDITIONAL_FIT' for f in r['fits'])]
        group={'generated_law':gl,'total_denominator':len(allrows),'paired_accepted':len(accepted),'excluded_indices':[r['index'] for r in allrows if r not in accepted]}
        if accepted:
            arr=np.array([[f['theta'] for f in r['fits']] for r in accepted]);err=arr-TRUTH
            diff=arr[:,1]-arr[:,0]
            group.update(fit_law_order=list(LABELS),bias=err.mean(0).tolist(),RMSE=np.sqrt((err**2).mean(0)).tolist(),paired_post_minus_pre_mean=diff.mean(0).tolist(),paired_post_minus_pre_sd=diff.std(0,ddof=1).tolist() if len(diff)>1 else None,paired_mean_MCSE=(diff.std(0,ddof=1)/np.sqrt(len(diff))).tolist() if len(diff)>1 else None,paired_difference_range=[diff.min(0).tolist(),diff.max(0).tolist()],same_truth_logL_post_minus_pre_mean=float(np.mean([r['same_truth_logL_post_minus_pre'] for r in accepted])))
            if len(accepted)>1:group['bias_MCSE']=(err.std(0,ddof=1)/np.sqrt(len(accepted))).tolist()
        result.append(group)
    return result
def plot(out,result):
    import matplotlib;matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(10,6))
    for gi,gl in enumerate(LABELS):
        rows=[r for r in result['rows'] if r['generated_law']==gl and all(f.get('status')=='ACCEPTED_CONDITIONAL_FIT' for f in r['fits'])]
        for i,ax in enumerate(axes.ravel()):
            ax.scatter([r['index']+gi*.18 for r in rows],[r['fits'][1]['theta'][i]-r['fits'][0]['theta'][i] for r in rows],label=['preselection generated','selected-slot generated'][gi],marker=['o','x'][gi])
            ax.axhline(0,color='k',lw=.6);ax.set(xlabel='catalogue index',ylabel=['delta H (km/s/Mpc)','delta Bx (km/s)','delta By (km/s)','delta Bz (km/s)'][i])
    axes[0,0].legend(fontsize=8);fig.suptitle('Paired fit difference: selected-slot minus preselection\nConditional generated catalogues; real24-slot design')
    fig.tight_layout();fig.savefig(out/'paired_crosslaw.svg');plt.close(fig)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--catalogues',type=int,default=16);parser.add_argument('--seed',type=int,default=2026101402)
    parser.add_argument('--tests-only',action='store_true');args=parser.parse_args()
    if not 1<=args.catalogues<=32:parser.error('campaign bound1..32 per generating law')
    repo=args.repo.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    head=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    if head!=EXPECTED_HEAD:raise ValueError('source HEAD differs from frozen experiment identity')
    d=load_repo(repo);packet,design,sources=d.intake(repo,repo/'docs/observational_reboot_20261014/task_packets/RB07_selected_scenario.json')
    scenario=d.Scenario(**packet['baseline']);tests=semantic_tests(design,scenario);write(out/'semantic_tests.json',tests)
    if args.tests_only:print(json.dumps({'tests':tests}));return
    t0=time.monotonic();rows=[]
    for gi,gl in enumerate(LABELS):
        generator=d.SelectedLaw(design,replace(scenario,selection_semantics=gl),256,64)
        for index in range(args.catalogues):
            rowpath=out/f'catalogue_g{gi}_{index:02d}.json'
            if rowpath.exists():
                row=json.loads(rowpath.read_text())
                if row['seed']!=args.seed+gi*100000+index:raise ValueError('resume seed differs')
                rows.append(row);continue
            seed=args.seed+gi*100000+index;raw=generate(generator,seed);sample=sample_from(design,raw)
            npzpath=out/f'generated_g{gi}_{index:02d}.npz'
            np.savez(npzpath,**raw,group_id=design.group_id,direction=design.direction,sigma_mu=design.sigma_mu,truth_H_B=TRUTH)
            fits=[];scores=[]
            for fl in LABELS:
                fs=replace(scenario,selection_semantics=fl)
                scores.append(d.SelectedLaw(sample,fs,512,128).log_likelihood(TRUTH))
                try:fit=fine_fit(sample,fs,index)
                except Exception:fit={'status':'FIT_FAILURE','failure':traceback.format_exc()}
                fits.append({'fitted_law':fl,**fit})
            row={'generated_law':gl,'index':index,'seed':seed,'generated_sha256':digest(npzpath),'eta_generated_mag':raw['eta'],'fits':fits,'same_truth_logL_post_minus_pre':scores[1]-scores[0]}
            rows.append(row);write(rowpath,row);print(json.dumps({'progress':[gi,index],'fits':[f['status'] for f in fits],'seconds':time.monotonic()-t0}),flush=True)
    result={'source_commit':head,'owner':'HTT','scope':'paired selected-law fits to conditional generated catalogues using actual frozen24design; no new CF4 measurements or physical coverage','claim_tier':'CONDITIONAL_DIAGNOSTIC','artifact_mode':'finite_experiment','transfer_source':'solver independent','null_status':'two declared generative laws; no physical null admission','covariance_status':'same fixed per-slot Gaussian proxies and shared eta scenario','allowed_use':'method semantics sensitivity and conditional paired bias/RMSE','forbidden_uses':['physicalH0/globaltilt','actualsurvey coverage','nativeBianchi result','Bayes odds from crosslaw logL differences'],'truth_H_B':TRUTH.tolist(),'scenario_except_semantics':{k:v for k,v in asdict(scenario).items() if k!='selection_semantics'},'seed':args.seed,'catalogues_per_law':args.catalogues,'source_design':sources,'semantic_tests':tests,'rows':rows,'summary':summarize(rows),'seconds':time.monotonic()-t0,'runtime':{'executable':sys.executable,'python':platform.python_version(),'numpy':np.__version__,'requested':'gpt-6.1-sol/high','observed':'UNKNOWN'},'source_code':{'experiment_sha256':digest(__file__),'original_injection_generator_sha256':digest(repo/'scripts/run_reboot_cf4_injections.py'),'law_sha256':digest(d.module_path)}}
    write(out/'result.json',result);plot(out,result)
    print(json.dumps({'summary':result['summary'],'seconds':result['seconds']}),flush=True)
if __name__=='__main__':main()
