#!/usr/bin/env python3
"""One finite radial-velocity alternative on the existing CF4 tensor carrier.

V(z)=V0+V1*z/zstar is a declared kinematic response, not a homogeneous-tilt
solution. The first-order Doppler approximation and its velocity scale are
reported explicitly. No survey covariance is recalculated or null law fitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg, optimize, stats

BASELINE = '6fe19c5139004a1f281ec85c592e5ab4c7590d5f'
SOURCE_DIR = 'docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS'
ZSTAR = .05


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(x):
    if isinstance(x, dict): return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, np.ndarray): return clean(x.tolist())
    if isinstance(x, np.integer): return int(x)
    if isinstance(x, np.bool_): return bool(x)
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else ('inf' if x>0 else '-inf')
    return x


def block_test(h, c, ix):
    h, c = h[ix], c[np.ix_(ix,ix)]
    w = float(h @ linalg.solve(c,h,assume_a='pos'))
    return dict(wald=w,dof=len(ix),p=float(stats.chi2.sf(w,len(ix))))


def run(root, output):
    root,output=Path(root).resolve(),Path(output).resolve()
    if output.exists() and any(output.iterdir()):
        raise ValueError('refusing to overwrite existing results')
    output.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(root/'scripts/r58'),str(root/'htt'),str(root/'htt/src')]
    import run_r58_owned_tensor as old
    de, _, cf, mt = old.import_modules(root,None)
    from htt.htt.infer.r60_covariance_calibration import linear_budget_distance
    checked={p:sha(root/p) for p in old.PINS}
    bad=[p for p,h in checked.items() if h!=old.PINS[p]
         and h not in old.ALLOWED_REPAIRED_HASHES.get(p,())]
    if bad: raise ValueError('R58 pinned dependency changed: '+str(bad))
    source=root/SOURCE_DIR/'OWNED_TENSOR_CARRIERS.npz'
    ref=root/SOURCE_DIR/'OWNED_TENSOR_RESULT.json'
    if sha(source)!=json.loads(ref.read_text())['carrier_sha256']:
        raise ValueError('R58 carrier hash differs')
    saved=np.load(source,allow_pickle=False)
    data=cf.load();cat=data['cat']
    n,z=cat['n_J2000'],cat['z_CMB']
    lr=de.log_distance_ratio(cat['dmzp'],z,cf.OMEGA_M)
    eta,g=lr['eta'],lr['g_per_km_s']
    tau2=de.log_noise_variance(cat['e_dmzp'],g,cf.SIGMA_STAR)
    with np.load(cf.OUT_DIR/'R54_L04_SURVEY_LABELS.npz',allow_pickle=False) as lab:
        if not np.array_equal(lab['group_id'],cat['group_id']):
            raise ValueError('survey labels out of order')
        survey=dict(labels=lab['survey'].copy(),raw_labels=lab['survey_unpooled'].copy(),min_side=100)
    ops,_=cf.build_operators(cat,data['a_raw'],tau2,survey=survey)
    base_design=np.column_stack((g[:,None]*n,de.multipole_basis(n)[:,1:]))
    # gamma=(V0,d_eff,kappa,V1), beta=(V0,dH,kappa,V1).
    # d_eff=dH+V1/(c*zstar); beta=T*gamma and gamma=A*beta.
    T=np.eye(14);T[3:6,11:14]=-np.eye(3)/(de.C_KM_S*ZSTAR)
    A=np.eye(14);A[3:6,11:14]=np.eye(3)/(de.C_KM_S*ZSTAR)
    residual_kernel=g*z/ZSTAR-1.0/(de.C_KM_S*ZSTAR)
    scale=np.r_[saved['parameter_scale'],[300.]*3]
    rows=saved['row_indices32'];result={};arrays={}
    for name in old.VARIANTS:
        op=ops[name][rows]
        y=saved[name+'__y32'];c=saved[name+'__cov32'];x=saved[name+'__response32x11']
        rebuilt_y=op@eta;rebuilt_x=op@base_design
        parity=dict(y_max_abs=float(np.max(np.abs(y-rebuilt_y))),
                    scaled_design_max_abs=float(np.max(np.abs((x-rebuilt_x)*scale[:11]))),
                    noise_max_abs=float(np.max(np.abs(de.white_covariance(op,tau2)-saved[name+'__white36'][np.ix_(rows,rows)]))))
        if max(parity.values())>2e-10:raise ValueError('R58 reconstruction parity failed: '+name)
        slope=op@(residual_kernel[:,None]*n)
        xc=np.column_stack((x,slope))
        xp=np.column_stack((x,op@((g*z/ZSTAR)[:,None]*n)))
        if np.max(np.abs((xc@A-xp)*scale))>1e-11:
            raise ValueError('physical/chart response identity failed')
        base=mt.fit_linear(y,c,x,scale[:11])
        fit=mt.fit_linear(y,c,xc,scale)
        direct=mt.fit_linear(y,c,xp,scale)
        if fit['rank']!=14 or direct['rank']!=14:
            raise ValueError('finite radial model not full rank; no df3 law admitted')
        h=T@fit['estimate'];cov=T@fit['covariance']@T.T
        checks=dict(estimate_scaled_max_abs=float(np.max(np.abs((h-direct['estimate'])/scale))),
            covariance_scaled_max_relative=float(np.max(np.abs((cov-direct['covariance'])/scale[:,None]/scale[None,:]))/
                                                 np.max(np.abs(cov/scale[:,None]/scale[None,:]))),
            residual_chi2_abs=float(abs(fit['residual_chi2']-direct['residual_chi2'])))
        if checks['estimate_scaled_max_abs']>1e-7 or checks['covariance_scaled_max_relative']>1e-9:
            raise ValueError('physical-chart fit parity failed')
        delta=base['residual_chi2']-fit['residual_chi2']
        slope_test=block_test(h,cov,np.arange(11,14))
        if abs(delta-slope_test['wald'])>1e-8:raise ValueError('nested LR/Wald identity failed')
        v0,v1=h[:3],h[11:14]
        endpoint_speeds=[float(np.linalg.norm(v0+v1*zz/ZSTAR)) for zz in [float(z.min()),float(z.max())]]
        tests={key:block_test(h,cov,np.array(ix)) for key,ix in {
            'all14':range(14),'physical_angular8':range(3,11),
            'quadrupole5':range(6,11),'physical_dipole3':range(3,6),
            'velocity0_3':range(3),'velocity_slope3':range(11,14)}.items()}
        # For each fixed V1 the original estimator satisfies
        # alpha_hat_constant = alpha_true + bias_map*V1 + Gaussian error.
        # Its union over a deterministic ball is E + (-bias_map*ball_b).
        # This conservative marginal construction ignores residual information.
        bias_map=base['covariance'] @ x.T @ linalg.solve(c,xp[:,11:14],assume_a='pos')
        bounded={}
        for key,ix in [('physical_angular8',np.arange(3,11)),('quadrupole5',np.arange(6,11)),
                       ('physical_dipole3',np.arange(3,6))]:
            hb=base['estimate'][ix];cb=base['covariance'][np.ix_(ix,ix)];H=bias_map[ix]
            lc=linalg.cholesky(cb,lower=True)
            wfree=linalg.lstsq(linalg.solve_triangular(lc,H,lower=True),
                              linalg.solve_triangular(lc,hb,lower=True))[0]
            upper=float(np.linalg.norm(wfree))
            threshold=float(stats.chi2.ppf(.95,len(ix)))
            zero=linear_budget_distance(hb,cb,H,0.)
            free=linear_budget_distance(hb,cb,H,upper*(1+1e-12))
            if zero['distance2']<=threshold:
                critical=0.
            elif free['distance2']>threshold:
                critical=None
            else:
                critical=optimize.brentq(lambda b:linear_budget_distance(hb,cb,H,b)['distance2']-threshold,
                                        0.,upper*(1+1e-12),xtol=1e-7,rtol=1e-12)
            budgets={}
            for b in [0.,300.,1000.,3000.]:
                ans=linear_budget_distance(hb,cb,H,b)
                budgets[str(b)]=dict(**ans,zero_compatible=bool(ans['distance2']<=threshold))
            bounded[key]=dict(threshold=threshold,dof=len(ix),critical_V1_norm_km_s=critical,
                critical_status='FINITE' if critical is not None else 'NO_INTERSECTION_EVEN_WITH_UNBOUNDED_SLOPE',
                unconstrained_distance2=free['distance2'],budgets=budgets,
                meaning='95% marginal confidence ellipsoid plus deterministic slope-image body; no chi-square law assigned to optimized distance')
        result[name]=dict(rank=fit['rank'],rank_equilibrated=fit['rank_equilibrated'],
            scaled_condition=float(fit['singular_values_scaled'][0]/fit['singular_values_scaled'][-1]),
            equilibrated_condition=float(fit['singular_values_equilibrated'][0]/fit['singular_values_equilibrated'][-1]),
            physical_estimate14=h,physical_covariance14=cov,
            chart_estimate14=fit['estimate'],chart_covariance14=fit['covariance'],
            tests=tests,nested_constant_velocity_test=dict(delta_chi2=delta,dof=3,
                p=float(stats.chi2.sf(delta,3)),meaning='V1=0 with V0,dH,kappa profiled at fixed inherited covariance'),
            residual_chi2=fit['residual_chi2'],residual_dof=fit['dof'],adequacy_p=fit['adequacy_p'],
            physical_dH_sd=np.sqrt(np.diag(cov)[3:6]),
            dH_sd_inflation=np.sqrt(np.diag(cov)[3:6]/np.diag(base['covariance'])[3:6]),
            quadrupole_sd_inflation=np.sqrt(np.diag(cov)[6:11]/np.diag(base['covariance'])[6:11]),
            V0_norm_km_s=float(np.linalg.norm(v0)),V1_norm_km_s=float(np.linalg.norm(v1)),
            bestfit_endpoint_speed_km_s=endpoint_speeds,
            bestfit_max_speed_over_c=max(endpoint_speeds)/de.C_KM_S,
            first_order_velocity_scope='unconstrained linear response; inspect speed/c before assigning a physical velocity-history interpretation',
            original_response_parity=parity,physical_chart_checks=checks,
            bounded_velocity_slope=bounded,constant_estimator_bias_map14slope_to11=bias_map,
            support_widening_per_1000_km_s=1000.*np.linalg.norm(bias_map,axis=1))
        arrays[name+'__response32x14_physical']=xp
        arrays[name+'__response32x14_chart']=xc
    robust={key:max(v['tests'][key]['p'] for v in result.values()) for key in next(iter(result.values()))['tests']}
    q0=1.5*cf.OMEGA_M-1.
    zz=np.array([1e-5,2e-5,5e-5,1e-4])
    small=de.log_distance_ratio(np.full(zz.size,35.),zz,cf.OMEGA_M)
    limit=(small['g_per_km_s']*de.C_KM_S*zz-1.)/zz
    out=dict(schema='htt.r60.radial_velocity/1',baseline=BASELINE,
        source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        source=dict(carrier=str(source.relative_to(root)),sha256=sha(source),n_groups=int(z.size),
                    raw_dependencies_sha256=checked),
        design=dict(zstar=ZSTAR,z_min=float(z.min()),z_max=float(z.max()),c_km_s=de.C_KM_S,
            frame='ICRS/J2000, sourceward n, frozen z_CMB',
            physical_parameter_order=['V0_x_km_s','V0_y_km_s','V0_z_km_s','dH_x','dH_y','dH_z']+
                ['kappa_'+str(i) for i in range(5)]+['V1_x_km_s','V1_y_km_s','V1_z_km_s'],
            mean='eta = nuisance + g(z)*n.[V0+V1*z/zstar] + n.dH + n.K.n',
            chart='d_eff=dH+V1/(c*zstar); residual slope kernel g(z)*z/zstar-1/(c*zstar)',
            T_chart_to_physical=T,A_physical_to_chart=A,parameter_scale=scale,
            approximation='first order in velocities/c; exact inherited flat LCDM luminosity-distance response; no homogeneous tilt dynamics',
            low_z_expansion='c*z*g(z)=1-(1+q0)*z/2+O(z^2)',q0=q0,
            low_z_limit_expected=-.5*(1+q0),low_z_z=zz,low_z_limit_evaluated=limit),
        variants=result,model_max_p=robust,
        bounded_slope_model_union={key:dict(
            minimum_critical_V1_norm_km_s=min([v['bounded_velocity_slope'][key]['critical_V1_norm_km_s']
                for v in result.values() if v['bounded_velocity_slope'][key]['critical_V1_norm_km_s'] is not None],default=None),
            budgets={str(b):any(v['bounded_velocity_slope'][key]['budgets'][str(float(b))]['zero_compatible']
                               for v in result.values()) for b in [0,300,1000,3000]})
            for key in ['physical_angular8','quadrupole5','physical_dipole3']},
        max_p_nested_constant_velocity=max(v['nested_constant_velocity_test']['p'] for v in result.values()),
        limitations=['This finite slope is a response sensitivity model, not a fitted Bianchi or global-tilt solution.',
            'The input CMB-frame redshift convention is retained; observer-frame corrections are not re-estimated.',
            'All tests are conditional on the same fixed Gaussian covariance and selected 32D carrier.',
            'The new slope alternative is post-hoc; its fixed-model p-value is not selection-adjusted discovery significance.',
            'Large unconstrained velocities can leave the perturbative regime; reported formal covariance is not a global relativistic bound.',
            'Finite slope budgets are declared sensitivity inputs, not measured constraints. Their confidence union uses the original constant-model estimator and ignores residual information.',
            'Physical dH is recovered by an explicit linear back-transform. The conditioned chart d_eff is not reported as acceleration.',
            'Different nuisance models transform the same data, and are combined only by a confidence-set union/max-p sensitivity rule.'],
        implementation=dict(runner_sha256=sha(__file__),fit_module_sha256=sha(Path(mt.__file__)),
                            sensitivity_module_sha256=sha(root/'htt/htt/htt/infer/r60_covariance_calibration.py'),
                            numpy=np.__version__,scipy=scipy.__version__,python=platform.python_version()))
    np.savez_compressed(output/'RADIAL_RESPONSE_CARRIERS.npz',**arrays)
    out['response_file_sha256']=sha(output/'RADIAL_RESPONSE_CARRIERS.npz')
    (output/'RADIAL_VELOCITY_RESULT.json').write_text(json.dumps(clean(out),indent=2,allow_nan=False)+'\n')
    print(json.dumps(clean(dict(model_max_p=robust,max_p_nested_constant_velocity=out['max_p_nested_constant_velocity'],
        bounded_slope_model_union=out['bounded_slope_model_union'],
        variants={k:{q:v[q] for q in ['nested_constant_velocity_test','dH_sd_inflation','V1_norm_km_s',
                                    'bestfit_max_speed_over_c','adequacy_p']} for k,v in result.items()})),indent=2))
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.root,a.output)
