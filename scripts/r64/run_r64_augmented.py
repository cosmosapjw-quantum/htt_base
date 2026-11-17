#!/usr/bin/env python3
"""R64 bounded resolution check using already-owned correlated source rows.

This does not add independent galaxies. It recovers more of the existing
catalogue information from the joint L05 cache, including all cross blocks.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
from scipy import linalg, stats

from run_r64_directional_hubble import clean, save_fit, nested_angular_null


def profile_nuisance(y, cov, x, nuisance, fit_linear, scales):
    """Exact fixed-C Gaussian profiling using an orthonormal complement.

    Keeps the full covariance information before projection. The projected
    likelihood is normalized for its own residual experiment, not a Bayes
    factor across different nuisance models. No stochastic calibration prior.
    """
    chol=linalg.cholesky(cov,lower=True)
    yw=linalg.solve_triangular(chol,y,lower=True)
    xw=linalg.solve_triangular(chol,x,lower=True)
    nw=linalg.solve_triangular(chol,nuisance,lower=True)
    if nw.shape[1]:
        norm=np.linalg.norm(nw,axis=0)
        if np.any(norm==0):raise ValueError('zero nuisance columns require an explicit reduced chart')
        u,s,_=linalg.svd(nw/norm,full_matrices=True)
        rank=int(np.sum(s>1e-12*s[0]))
        q=u[:,rank:]
    else:
        rank=0;q=np.eye(len(y))
    yy,xx=q.T@yw,q.T@xw
    fit=fit_linear(yy,np.eye(len(yy)),xx,scales)
    return fit,yy,xx,dict(nuisance_rank=rank,complement=q,
        whitening=chol,whitened_nuisance=nw,
        profile_rows=len(yy),total_mean_rank=rank+fit['rank'])


def run(root, output):
    start=time.perf_counter();root=Path(root).resolve();output=Path(output).resolve()
    if output.exists() and any(output.iterdir()):raise ValueError('refusing to overwrite augmentation')
    output.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(root/'scripts/r58'),str(root/'htt'),str(root/'htt/src')]
    import run_r58_owned_tensor as old
    de,fv,cf,mt=old.import_modules(root,None)
    from htt.htt.infer import r64_directional_hubble as dh
    data=cf.load();cat=data['cat'];n,z=cat['n_J2000'],cat['z_CMB']
    lr=de.log_distance_ratio(cat['dmzp'],z,cf.OMEGA_M);g=lr['g_per_km_s']
    smooth=dh.background_factors(z,cf.OMEGA_M)
    eta=lr['eta']+np.log(smooth['chi_hat']/lr['chi_hat'])
    tau2=de.log_noise_variance(cat['e_dmzp'],g,cf.SIGMA_STAR)
    ops,_=cf.build_operators(cat,data['a_raw'],tau2)
    cache=cf.OUT_DIR/'R54_L05_COSMIC_COV.npz'
    expected='f0acb8e1be3f09d212303967ff7678178fd59364ec0131ab12ba3f5149879cae'
    if old.sha256(cache)!=expected:raise ValueError('L05 joint-cache identity changed')
    for p,h in old.PINS.items():
        actual=old.sha256(root/p)
        if actual!=h and actual not in old.ALLOWED_REPAIRED_HASHES.get(p,()):
            raise ValueError('source/code identity changed: '+p)
    body,layout,reuse=old.cached_rows(cache,ops,g,cf,n,de.C_KM_S/cf.H_FID*lr['chi_hat'])
    velocity_stack=np.concatenate([op*((1+z) if name=='lin' else g)[None,:] for name,op in ops.items()])
    actual_fp=str(cf.operator_fingerprint(velocity_stack))
    reuse['correct_original_velocity_stack_fingerprint']=actual_fp
    reuse['correct_original_velocity_stack_bytes_equal']=actual_fp==reuse['operator_fingerprint_recorded']
    reuse['compatibility_helper_note']='R58 compatibility helper uses g for all rows; original unused lin block uses1+z. Correct full-stack fingerprint is recorded separately; selected rows are all log-eta rows.'
    old_result=json.loads((cf.OUT_DIR/'R54_L05_CF4_EXACT.json').read_text())
    mrows=np.arange(layout['log_method'].start,layout['log_method'].stop)
    ym=ops['log_method']@lr['eta']
    cm=de.white_covariance(ops['log_method'],tau2)+body[np.ix_(mrows,mrows)]
    old_per=old_result['common_mode']['white_plus_exact_body']['per_method']
    parity_method=max(float(np.max(abs(ym[8*j:8*j+3]-old_per[name]['delta']))) for j,name in enumerate(cf.METHODS))
    parity_sd=max(float(np.max(abs(np.sqrt(np.diag(cm))[8*j:8*j+3]-old_per[name]['sd']))) for j,name in enumerate(cf.METHODS))
    if parity_method>2e-9 or parity_sd>2e-9:raise ValueError('new method rows fail original R54 numerical parity')
    reuse['method_dipole_mean_original_R54_maxerror']=parity_method
    reuse['method_dipole_sd_original_R54_maxerror']=parity_sd
    b=de.multipole_basis(n)
    method_nuisance=np.column_stack([(cat['method_family']==m)[:,None]*b[:,1:] for m in ('FP','SN','TF')])
    src={j:dh.source_design(z,n,g,j) for j in (1,2,3)}
    original_path=root/'docs/research_program/observational_publication_20261015/R64_DIRECTIONAL_HUBBLE_20261117/RESULTS/OBSERVED/DIRECTIONAL_HUBBLE_CARRIERS.npz'
    original=np.load(original_path,allow_pickle=False)
    directions=original['directions_ICRS']
    combinations=[('log_method',('log','log_method')),('mono_method',('log_mono','log_method')),
                  ('split_method',('log_split','log_method')),('log_sky',('log','jk_no_equator'))]
    arrays={};records={};input_checks={}
    for tag,names in combinations:
        indices=np.concatenate([np.arange(layout[name].start,layout[name].stop) for name in names])
        op=np.concatenate([ops[name] for name in names])
        y=op@eta;white=de.white_covariance(op,tau2);cosmic=body[np.ix_(indices,indices)]
        cov=white+cosmic;chol=linalg.cholesky(cov,lower=True)
        # The first36 must reproduce the initial experiment exactly up to the
        # declared native numerical reconstruction tolerance.
        yyerr=float(np.max(abs(y[:36]-original[names[0]+'__y36'])))
        cerr=float(np.max(abs(cov[:36,:36]-original[names[0]+'__cov36'])))
        if yyerr>2e-10 or cerr>2e-10:raise ValueError('existing36 carrier not preserved')
        input_checks[tag]=dict(rows=len(y),first36_eta_parity=yyerr,first36_cov_parity=cerr,
            covariance_min_eigenvalue=float(linalg.eigvalsh(cov)[0]),
            covariance_condition=float(np.linalg.cond(cov)),
            operator_sha256=hashlib.sha256(np.ascontiguousarray(op).tobytes()).hexdigest(),
            blocks=list(names),cache_rows=indices.tolist())
        arrays[tag+'__y']=y;arrays[tag+'__covariance']=cov
        for degree in (1,2,3):
            x=op@src[degree];p=x.shape[1]
            scale=np.r_[np.full(3,300.),np.full(p-3,.01)]
            families=('common_field','method_angular_nuisance') if tag!='log_sky' else ('common_field',)
            for family in families:
                nuisance=op@method_nuisance if family=='method_angular_nuisance' else np.zeros((len(y),0))
                fit,yp,xp,meta=profile_nuisance(y,cov,x,nuisance,mt.fit_linear,scale)
                key=tag+f'__J{degree}__'+family
                rec=save_fit(arrays,key,fit,xp)
                arrays[key+'__original_response']=x
                arrays[key+'__nuisance_response']=nuisance
                arrays[key+'__profile_complement']=meta['complement']
                rec.update(experiment=tag,degree=degree,calibration_family=family,
                    n_observed_original=len(y),profile_rows=meta['profile_rows'],
                    nuisance_rank=meta['nuisance_rank'],total_mean_rank=meta['total_mean_rank'])
                rec['angular_radial_null']=nested_angular_null(yp,np.eye(len(yp)),xp,degree,scale,fit,mt.fit_linear)
                # The added rows' innovation relative to the original36 is an
                # exact joint-data factorization, not independent evidence.
                ctt=cov[:36,:36];a=linalg.solve(ctt,cov[:36,36:],assume_a='pos').T
                innovation=y[36:]-a@y[:36];sx=x[36:]-a@x[:36]
                sc=cov[36:,36:]-a@cov[:36,36:]
                rec['additional_rows']=dict(count=len(y)-36,innovation_norm=float(np.linalg.norm(innovation)),
                    conditional_cov_min_eigenvalue=float(linalg.eigvalsh(sc)[0]),
                    meaning='correlated additional summaries of the same catalogue; no independent-tracer claim')
                if family=='common_field':
                    first=mt.fit_linear(y[:36],cov[:36,:36],x[:36],scale)
                    null_prediction=sx@first['null_basis']
                    # A fitted representative has a prediction only if the
                    # actual conditional mean kills all training nulls.
                    predictive_identified=(not null_prediction.size or np.linalg.norm(null_prediction)<1e-9*max(np.linalg.norm(sx*scale),1e-300))
                    if predictive_identified:
                        err=innovation-sx@first['estimate']
                        pv=sc+sx@first['covariance']@sx.T
                        stat=float(err@linalg.solve(pv,err,assume_a='pos'))
                        rec['additional_rows']['predictive']={'status':'IDENTIFIED','chi2':stat,'df':len(err),'nominal_p':float(stats.chi2.sf(stat,len(err)))}
                    else:rec['additional_rows']['predictive']={'status':'INGREDIENT_UNIDENTIFIED'}
                maps=[]
                for iz,zz in enumerate((.025,.04,.06,.08)):
                    for ni,nn in enumerate(directions):
                        maps.append(dict(z_index=iz,direction_index=ni,
                            ratio=dh.radial_hubble_interval(fit,zz,.04,nn,degree,cf.OMEGA_M,cf.H_FID,.95),
                            q=dh.q_interval(fit,zz,nn,degree,cf.OMEGA_M,cf.H_FID,.95),
                            point=dh.point_image(fit['estimate'],zz,nn,degree,cf.OMEGA_M,cf.H_FID)))
                rec['maps']=maps
                rec['optical_coefficients_identified']=fit['rank']==p
                rec['mean_family_scope']='same source polynomial, free V and common angular field; optional24 independent method-angular zero-point contrasts, no stochastic calibration prior'
                records[key]=rec
                print(json.dumps({k:rec[k] for k in ('experiment','degree','calibration_family','rank','n_parameters','dof','adequacy_p')}),flush=True)
    out=dict(schema='htt.r64.owned_augmentation/1',source_rows=len(z),cache_sha256=expected,cache_reuse=reuse,
        input_checks=input_checks,models=records,elapsed_s=time.perf_counter()-start,
        baseline_original36_sha256=old.sha256(original_path),
        amendment_reason='R8 identified existing correlated extra functionals; resolve the concrete compression-rank limitation, not a second loop or new catalogue',
        new_independent_sources=0,new_pair_sum=False,publication_status='NOT_READY_TO_SUBMIT',
        module_sha256=old.sha256(Path(dh.__file__)),script_sha256=old.sha256(Path(__file__)))
    (output/'AUGMENTED_RESULT.json').write_text(json.dumps(clean(out),indent=2,allow_nan=False)+'\n')
    np.savez_compressed(output/'AUGMENTED_CARRIERS.npz',**arrays)
    print(json.dumps({'completed_models':len(records),'elapsed_s':out['elapsed_s']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default='.')
    p.add_argument('--output',required=True);args=p.parse_args();run(args.root,args.output)
