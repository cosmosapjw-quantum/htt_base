#!/usr/bin/env python3
"""Measure a finite depth-dependent STF response and check angular linearization.

The slope is d(kappa)/d(z/zstar), not a proper-time derivative of local shear.
The exact-log comparison assumes an angular multiplicative distance response
D_L(z,n)=D_L_fid(z)/(1+h(n)); it is a response-closure diagnostic, not an
Einstein solution or a complete finite-z cosmographic model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg,optimize,stats

BASELINE='fb6ae9f21585e194ef29dabc91d79a529e0ac57e'
SOURCE='docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS'
RADIAL='docs/research_program/observational_publication_20261015/R60_COVARIANCE_CALIBRATION_20261117/RESULTS/RADIAL'
ZPIVOT=.05
ZSTAR=.05


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def clean(x):
    if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [clean(v) for v in x]
    if isinstance(x,np.ndarray):return clean(x.tolist())
    if isinstance(x,np.integer):return int(x)
    if isinstance(x,np.bool_):return bool(x)
    if isinstance(x,(float,np.floating)):
        if not np.isfinite(x):raise ValueError('nonfinite output')
        return float(x)
    return x


def run(root,output):
    start=time.perf_counter();root=Path(root).resolve();out=Path(output).resolve()
    if out.exists() and any(out.iterdir()):raise ValueError('refusing to overwrite results')
    out.mkdir(parents=True,exist_ok=True)
    sys.path[:0]=[str(root/'scripts/r58'),str(root/'htt'),str(root/'htt/src')]
    import run_r58_owned_tensor as old
    de,_,cf,mt=old.import_modules(root,None)
    from htt.htt.infer.r61_kinematic_images import norm_ellipsoid_range,quadratic_ball_extreme,stf_basis
    checked={p:sha(root/p) for p in old.PINS}
    bad=[p for p,h in checked.items() if h!=old.PINS[p] and h not in old.ALLOWED_REPAIRED_HASHES.get(p,())]
    if bad:raise ValueError('R58 pinned dependency changed: '+str(bad))
    source=root/SOURCE/'OWNED_TENSOR_CARRIERS.npz';ref=root/SOURCE/'OWNED_TENSOR_RESULT.json'
    if sha(source)!=json.loads(ref.read_text())['carrier_sha256']:raise ValueError('R58 carrier hash differs')
    radial_source=root/RADIAL/'RADIAL_RESPONSE_CARRIERS.npz'
    radial_ref=json.loads((root/RADIAL/'RADIAL_VELOCITY_RESULT.json').read_text())
    if sha(radial_source)!=radial_ref['response_file_sha256']:raise ValueError('R60 radial response hash differs')
    radial=np.load(radial_source,allow_pickle=False)
    saved=np.load(source,allow_pickle=False);data=cf.load();cat=data['cat']
    n,z=cat['n_J2000'],cat['z_CMB']
    lr=de.log_distance_ratio(cat['dmzp'],z,cf.OMEGA_M);eta,g=lr['eta'],lr['g_per_km_s']
    tau2=de.log_noise_variance(cat['e_dmzp'],g,cf.SIGMA_STAR)
    with np.load(cf.OUT_DIR/'R54_L04_SURVEY_LABELS.npz',allow_pickle=False) as lab:
        if not np.array_equal(lab['group_id'],cat['group_id']):raise ValueError('survey labels out of order')
        survey=dict(labels=lab['survey'].copy(),raw_labels=lab['survey_unpooled'].copy(),min_side=100)
    ops,_=cf.build_operators(cat,data['a_raw'],tau2,survey=survey)
    angular=de.multipole_basis(n)[:,1:]
    design=np.column_stack((g[:,None]*n,angular));raw_slope=((z-ZPIVOT)/ZSTAR)[:,None]*angular[:,3:]
    scale=saved['parameter_scale'];scale16=np.r_[scale,np.full(5,.01)]
    row=saved['row_indices32'];cut16=float(stats.chi2.ppf(.95,16));cut5=float(stats.chi2.ppf(.95,5))
    result={};arrays={};E=stf_basis()
    zgrid=np.linspace(0.,.1,51)
    for name in old.VARIANTS:
        op=ops[name][row]; y=saved[name+'__y32'];C=saved[name+'__cov32'];X=saved[name+'__response32x11']
        parity={'y_max_abs':float(np.max(np.abs(op@eta-y))),
            'design_scaled_max_abs':float(np.max(np.abs((op@design-X)*scale))),
            'monopole_response_max_abs':float(np.max(np.abs(op@np.ones(len(z)))))}
        if max(parity.values())>2e-10:raise ValueError('source/operator parity failed '+name)
        X16=np.column_stack((X,op@raw_slope));base=mt.fit_linear(y,C,X,scale)
        fit=mt.fit_linear(y,C,X16,scale16)
        if fit['rank']!=16:raise ValueError('slope response is not identified at declared scales')
        h,cov=fit['estimate'],fit['covariance'];hs=h[11:];cs=cov[11:,11:]
        w=float(hs@linalg.solve(cs,hs,assume_a='pos'))
        delta=base['residual_chi2']-fit['residual_chi2']
        if abs(w-delta)>2e-8:raise ValueError('slope Wald/LR identity failed')
        # A common additive angular calibration is exactly in the intercept
        # columns. The depth contrast annihilates it in this full-rank model.
        calibration_shift=np.r_[np.zeros(3),[.013,-.021,.008],
                        [.017,-.011,.009,.023,-.006],np.zeros(5)]
        injected=mt.fit_linear(y+X16@calibration_shift,C,X16,scale16)
        calibration_invariance=float(np.max(np.abs(injected['estimate'][11:]-hs)))
        if calibration_invariance>1e-11:raise ValueError('common angular calibration changed the slope')
        dz=(.08-.02)/ZSTAR
        deltaK=dz*hs;deltaCov=dz*dz*cs
        contrast_norm=norm_ellipsoid_range(deltaK,deltaCov,cutoff=cut16)
        contrast_rms={k:float(np.sqrt(2./15.)*contrast_norm[k]) for k in ['lower','upper','feasible_lower','feasible_upper']}
        Zvel=radial[name+'__response32x14_physical'][:,-3:]
        bias16=cov@X16.T@linalg.solve(C,Zvel,assume_a='pos')
        Bcontrast=dz*bias16[11:]
        contrast_budget={}
        for bvel in [0.,1000.,3000.]:
            extra=float(np.sqrt(2./15.)*bvel*np.linalg.norm(Bcontrast,2))
            contrast_budget[str(bvel)]={'lower':max(0.,contrast_rms['lower']-extra),
                  'upper':contrast_rms['upper']+extra,'extra_radius':extra,
                  'geometry':'conservative norm enclosure from the exact linear bias image; residual slope information not used'}
        depth_contrast={'z_low':.02,'z_high':.08,'delta_kappa':deltaK,'covariance':deltaCov,
             'full_sky_angular_rms_point':float(np.sqrt(2./15.)*np.linalg.norm(deltaK)),
             'simultaneous16_rms_interval':contrast_rms,
             'common_calibration_slope_max_abs':calibration_invariance,
             'constant_angular_calibration':'annihilated exactly by the slope contrast in this declared additive log-distance model',
             'depth_dependent_calibration':'a calibration difference with full-sky RMS<=rho_delta enlarges this RMS interval by rho_delta',
             'velocity_slope_bias_map':Bcontrast,'bounded_velocity_slope_km_s':contrast_budget}
        pivot=ZPIVOT-ZSTAR*float(np.trace(cov[6:11,11:]))/float(np.trace(cs))
        summaries={};curve=[]
        for zz in [0.,.02,.05,.08,float(pivot)]:
            t=(zz-ZPIVOT)/ZSTAR;L=np.zeros((5,16));L[:,6:11]=np.eye(5);L[:,11:]=t*np.eye(5)
            k=L@h;ck=L@cov@L.T
            nr=norm_ellipsoid_range(k,ck,cutoff=cut16)
            marginal=norm_ellipsoid_range(k,ck,cutoff=cut5)
            summaries[str(zz)]={'redshift':zz,'kappa':k,'covariance':ck,
                  'Sigma_point':float(np.linalg.norm(k)/np.sqrt(6.)),
                  'Sigma_simultaneous16':{'lower':nr['lower']/np.sqrt(6.),'upper':nr['upper']/np.sqrt(6.)},
                  'Sigma_marginal5':{'lower':marginal['lower']/np.sqrt(6.),'upper':marginal['upper']/np.sqrt(6.)},
                  'zero_wald':float(k@linalg.solve(ck,k,assume_a='pos')),
                  'zero_nominal_p5':float(stats.chi2.sf(k@linalg.solve(ck,k,assume_a='pos'),5)),
                  'coordinate_sd':np.sqrt(np.diag(ck))}
        for zz in zgrid:
            t=(zz-ZPIVOT)/ZSTAR;L=np.zeros((5,16));L[:,6:11]=np.eye(5);L[:,11:]=t*np.eye(5)
            k=L@h;ck=L@cov@L.T;nr=norm_ellipsoid_range(k,ck,cutoff=cut16)
            curve.append([zz,float(np.linalg.norm(k)/np.sqrt(6)),nr['lower']/np.sqrt(6),nr['upper']/np.sqrt(6)])
        # Nonlinear angular response retains the same observations and fixed C.
        lc=linalg.cholesky(C,lower=True);Wop=linalg.solve_triangular(lc,op,lower=True)
        yw=linalg.solve_triangular(lc,y,lower=True);XV=linalg.solve_triangular(lc,X[:,:3],lower=True)
        hb=base['estimate'];Cb=base['covariance'];sd=np.sqrt(np.diag(Cb))
        def residual(p):
            alpha=p*scale;factor=1.+angular@alpha[3:]
            return XV@alpha[:3]+Wop@np.log(factor)-yw
        def jacobian(p):
            alpha=p*scale;factor=1.+angular@alpha[3:]
            return np.column_stack((XV,Wop@(angular/factor[:,None])))*scale
        limits=np.r_[np.full(3,10000.),np.full(8,.2)]/scale
        fits=[]
        for initial in [hb/scale,np.zeros(11)]:
            opt=optimize.least_squares(residual,initial,jac=jacobian,bounds=(-limits,limits),
                    ftol=1e-11,xtol=1e-11,gtol=1e-11,max_nfev=120)
            if not opt.success or np.any(opt.active_mask):raise ValueError('nonlinear diagnostic optimizer failed/in active numerical bounds')
            fits.append(opt)
        opt=min(fits,key=lambda o:o.fun@o.fun);hn=opt.x*scale
        nonlinear_difference=float(np.max(np.abs((fits[0].x-fits[1].x))))
        if nonlinear_difference>2e-5:raise ValueError('two nonlinear fit starts disagree')
        raw_h=angular@hb[3:];delta_y=op@(np.log1p(raw_h)-raw_h)
        whitened_delta=linalg.solve_triangular(lc,delta_y,lower=True)
        bias=Cb@X.T@linalg.cho_solve((lc,True),delta_y)
        K=np.einsum('a,aij->ij',hn[6:],E)
        lo=quadratic_ball_extreme(K,.5*hn[3:6])
        hi=quadratic_ball_extreme(K,.5*hn[3:6],sense='max')
        closure={'model':'eta=nuisance+g*n.V+log(1+n.dH+n.K.n); common fiducial distance shape retained',
          'linear_estimate11':hb,'log_response_estimate11':hn,
          'shift_over_linear_sd':(hn-hb)/sd,'max_abs_shift_over_linear_sd':float(np.max(np.abs((hn-hb)/sd))),
          'linear_residual_chi2':base['residual_chi2'],'log_response_residual_chi2':float(opt.fun@opt.fun),
          'fixed_linear_point_whitened_remainder_norm':float(np.linalg.norm(whitened_delta)),
          'linear_bias_from_remainder':bias,'linear_bias_over_sd':bias/sd,
          'raw_max_abs_log_remainder':float(np.max(np.abs(np.log1p(raw_h)-raw_h))),
          'source_factor_min':float(np.min(1+angular@hn[3:])),
          'all_sky_factor_lower_bound':1+lo['bound'],'all_sky_factor_upper_bound':1+hi['bound'],
          'same_minimum_two_starts_scaled_difference':nonlinear_difference,
          'numerical_parameter_bounds_alpha':limits*scale,'active_bound':False,
          'nfev':[o.nfev for o in fits],
          'interpretation':'response-closure sensitivity at fitted states; no new scalar likelihood-ratio law and no global nonlinear confidence region'}
        cp=cov[6:11,6:11]
        c0=summaries['0.0']['covariance'];copt=summaries[str(float(pivot))]['covariance']
        result[name]={'estimate16':h,'covariance16':cov,'rank':fit['rank'],
          'condition_scaled':float(fit['singular_values_scaled'][0]/fit['singular_values_scaled'][-1]),
          'condition_equilibrated':float(fit['singular_values_equilibrated'][0]/fit['singular_values_equilibrated'][-1]),
          'slope_test':{'wald':w,'delta_chi2':delta,'dof':5,'p':float(stats.chi2.sf(w,5))},
          'depth_contrast_002_008':depth_contrast,
          'adequacy_p':fit['adequacy_p'],'residual_chi2':fit['residual_chi2'],'residual_dof':fit['dof'],
          'trace_minimizing_redshift':pivot,'depth_images':summaries,
          'z0_sd_over_constant':np.sqrt(np.diag(c0)/np.diag(base['covariance'])[6:]),
          'z0_sd_over_optimal_pivot':np.sqrt(np.diag(c0)/np.diag(copt)),
          'sqrt_trace_z0_over_optimal_pivot':float(np.sqrt(np.trace(c0)/np.trace(copt))),
          'curve_z_point_lower_upper':curve,'source_parity':parity,'angular_log_closure':closure}
        arrays[name+'__response32x16']=X16
    union_curve=np.array([[zz,min(v['curve_z_point_lower_upper'][i][2] for v in result.values()),
                    max(v['curve_z_point_lower_upper'][i][3] for v in result.values())] for i,zz in enumerate(zgrid)])
    np.savez_compressed(out/'DEPTH_RESPONSE_CARRIERS.npz',**arrays)
    report={'schema':'htt.r61.kinematic_depth/1','baseline':BASELINE,
      'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
      'source':{'carrier':str(source.relative_to(root)),'sha256':sha(source),'n_groups':len(z),'raw_dependencies_sha256':checked,
           'radial_response':str(radial_source.relative_to(root)),'radial_response_sha256':sha(radial_source)},
      'contract':{'mean':'eta=nuisance+g(z)n.V+n.dH+n.[Kp+((z-.05)/.05)K1].n',
         'parameter_order':['Vx_km_s','Vy_km_s','Vz_km_s','dHx','dHy','dHz']+['Kp_'+str(i) for i in range(5)]+['K1_'+str(i) for i in range(5)],
         'z_pivot':ZPIVOT,'z_scale':ZSTAR,'z_sample_min':float(z.min()),'z_sample_max':float(z.max()),
         'cutoff_simultaneous16':cut16,'cutoff_marginal5':cut5,
         'interpretation':'finite observed-depth STF variation, conditional on constant flow/dipole and fixed cosmic covariance; K(0) is a model extrapolation',
         'time_derivative':'K1 is not dot(sigma) or a local field equation coefficient'},
      'variants':result,'model_max_p_slope':max(v['slope_test']['p'] for v in result.values()),
      'model_union_depth_contrast_rms':{str(b):{
           'lower':min(v['depth_contrast_002_008']['bounded_velocity_slope_km_s'][str(b)]['lower'] for v in result.values()),
           'upper':max(v['depth_contrast_002_008']['bounded_velocity_slope_km_s'][str(b)]['upper'] for v in result.values())}
           for b in [0.,1000.,3000.]},
      'model_union_Sigma_curve':union_curve,
      'implementation':{'runner_sha256':sha(__file__),'image_module_sha256':sha(root/'htt/htt/htt/infer/r61_kinematic_images.py'),
          'fit_module_sha256':sha(Path(mt.__file__)),'numpy':np.__version__,'scipy':scipy.__version__,'python':platform.python_version()},
      'limitations':['The depth alternative is a response sensitivity model chosen after prior data analyses; p-values are fixed-model nominal tests, not selection-adjusted discovery probabilities.',
          'No new cosmic covariance or empirical angular calibration is generated.',
          'The zero-redshift intercept needs a controlled finite-z cosmographic remainder and smoothing/congruence interpretation to become a local shear measurement.',
          'The exact-log comparison fixes a multiplicative angular distance response and first-order Doppler kernel, not a full general-spacetime distance law.',
          'Two optimizer starts and inactive numerical bounds support the reported diagnostic stationary fit; global nonlinear optimum/coverage is not asserted.'],
      'runtime_seconds':time.perf_counter()-start}
    (out/'KINEMATIC_DEPTH.json').write_text(json.dumps(clean(report),indent=2,allow_nan=False)+'\n')
    plot(report,out)
    print(json.dumps(clean({'model_max_p_slope':report['model_max_p_slope'],
         'variants':{k:{'slope_p':v['slope_test']['p'],'pivot':v['trace_minimizing_redshift'],
             'z0_sd_inflation':v['z0_sd_over_constant'],'log_shift_sd':v['angular_log_closure']['max_abs_shift_over_linear_sd']} for k,v in result.items()},
         'runtime_seconds':time.perf_counter()-start}),indent=2))
    return report


def plot(report,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(12,4.6),constrained_layout=True)
    u=np.asarray(report['model_union_Sigma_curve'])
    axes[0].fill_between(u[:,0],u[:,1],u[:,2],color='#4a749a',alpha=.22,label='Seven-model simultaneous envelope')
    for name,v in report['variants'].items():
        a=np.asarray(v['curve_z_point_lower_upper']);axes[0].plot(a[:,0],a[:,1],lw=1.1,label=name.replace('log_',''))
    axes[0].axvspan(0.,report['contract']['z_sample_min'],color='gray',alpha=.12,label='Extrapolation below sample')
    axes[0].set(xlabel='Observed redshift',ylabel=r'$\|K(z)\|_F/\sqrt{6}$',title='Finite-depth tensor amplitude')
    axes[0].legend(fontsize=7,frameon=False,ncol=2);axes[0].grid(alpha=.2)
    names=list(report['variants']);p=[report['variants'][n]['trace_minimizing_redshift'] for n in names]
    v=[report['variants'][n]['sqrt_trace_z0_over_optimal_pivot'] for n in names]
    axes[1].barh([n.replace('log_','') for n in names],v,color='#24567a')
    for i,(x,z) in enumerate(zip(v,p)):axes[1].text(x+.04,i,f'pivot z={z:.3f}',va='center',fontsize=8)
    axes[1].set_xlim(0,max(v)*1.48);axes[1].invert_yaxis();axes[1].set(xlabel='RMS component error at z=0 / at optimal pivot',title='Cost of extrapolating to the observer')
    axes[1].grid(axis='x',alpha=.2)
    fig.suptitle('CF4: linear STF depth response; fixed covariance and constant velocity/dipole',fontsize=12)
    fig.savefig(out/'KINEMATIC_DEPTH.png',dpi=180);fig.savefig(out/'KINEMATIC_DEPTH.pdf');plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo-root',default='.');p.add_argument('--output',required=True)
    a=p.parse_args();run(a.repo_root,a.output)
