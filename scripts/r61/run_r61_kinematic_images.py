#!/usr/bin/env python3
"""Measure conditional nonlinear kinematic images of the owned CF4 experiment."""
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
from scipy import stats

BASELINE='fb6ae9f21585e194ef29dabc91d79a529e0ac57e'
SOURCE='docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117/RESULTS'


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
    sys.path[:0]=[str(root/'htt'),str(root/'htt/src')]
    from htt.htt.infer.r58_mixed_tensor_likelihood import fit_linear
    from htt.htt.infer.r61_kinematic_images import (kinematic_images,norm_ellipsoid_range,
             directional_expansion_support,stf_basis,MAG_PER_LOG_DISTANCE)
    sp=root/SOURCE;source=sp/'OWNED_TENSOR_CARRIERS.npz';ref=sp/'OWNED_TENSOR_RESULT.json'
    prior=json.loads(ref.read_text())
    if sha(source)!=prior['carrier_sha256']:raise ValueError('source carrier hash mismatch')
    data=np.load(source,allow_pickle=False);rows=data['row_indices32'];scale=data['parameter_scale']
    levels={'simultaneous11':float(stats.chi2.ppf(.95,11)),
            'marginal_shear5':float(stats.chi2.ppf(.95,5))}
    mags=[0.,.001,.005,.01]; variants={};sky={};maxparity=0.
    lon=np.linspace(-np.pi,np.pi,145);lat=np.linspace(-np.pi/2,np.pi/2,73)
    ll,bb=np.meshgrid(lon,lat);directions=np.column_stack((np.cos(bb).ravel()*np.cos(ll).ravel(),
                 np.cos(bb).ravel()*np.sin(ll).ravel(),np.sin(bb).ravel()))
    for name in sorted(prior['variants']):
        y=data[name+'__y32'];X=data[name+'__response32x11']
        N=data[name+'__white36'][np.ix_(rows,rows)];S=data[name+'__body36'][np.ix_(rows,rows)]
        parity=float(np.max(np.abs(N+S-data[name+'__cov32'])))
        if parity>1e-11:raise ValueError('covariance decomposition parity mismatch')
        maxparity=max(maxparity,parity);vr={}
        for lam in [1.,1.25]:
            fit=fit_linear(y,N+lam*S,X,scale)
            if fit['rank']!=11:raise ValueError('identified 11D experiment required')
            h,C=fit['estimate'],fit['covariance']
            if lam==1.:
                err=float(np.max(np.abs((h-data[name+'__estimate11'])/scale)))
                if err>1e-9:raise ValueError('source estimate parity failed')
            images={str(mag):kinematic_images(h,C,cutoff=levels['simultaneous11'],
                          rho=mag/MAG_PER_LOG_DISTANCE) for mag in mags}
            marginal=norm_ellipsoid_range(h[6:],C[6:,6:],cutoff=levels['marginal_shear5'])
            vr[str(lam)]={'estimate11':h,'covariance11':C,'images_by_rms_mag':images,
                 'marginal_shear5_sigma_interval':dict(lower=marginal['lower']/np.sqrt(6),
                     upper=marginal['upper']/np.sqrt(6),cutoff=levels['marginal_shear5']),
                 'marginal_shear5_calibration_zero_threshold_mag':
                     marginal['lower']/np.sqrt(7.5)*MAG_PER_LOG_DISTANCE,
                 'adequacy_p':fit['adequacy_p'],'rank':fit['rank']}
            if lam==1.:
                sk=directional_expansion_support(h,C,directions,cutoff=levels['simultaneous11'])
                sky[name]=sk
        variants[name]=vr
    union={}
    for lam in ['1.0','1.25']:
        union[lam]={}
        for mag in map(str,mags):
            u={}
            for target in ['Sigma','acceleration_over_cH','relative_speed_over_c','directional_expansion_rms']:
                u[target]=dict(lower=min(v[lam]['images_by_rms_mag'][mag][target]['lower'] for v in variants.values()),
                        upper=max(v[lam]['images_by_rms_mag'][mag][target]['upper'] for v in variants.values()))
            u['beta_dot_a']=dict(lower=min(v[lam]['images_by_rms_mag'][mag]['beta_dot_a']['with_calibration']['lower'] for v in variants.values()),
                  upper=max(v[lam]['images_by_rms_mag'][mag]['beta_dot_a']['with_calibration']['upper'] for v in variants.values()))
            union[lam][mag]=u
    sky_arrays={'longitude_rad':ll,'latitude_rad':bb,
         'union_lower':np.min([s['lower'] for s in sky.values()],axis=0).reshape(ll.shape),
         'union_upper':np.max([s['upper'] for s in sky.values()],axis=0).reshape(ll.shape)}
    for name,sk in sky.items():
        for key in ['center','lower','upper']:sky_arrays[name+'__'+key]=sk[key].reshape(ll.shape)
    np.savez_compressed(out/'DIRECTIONAL_SUPPORT.npz',**sky_arrays)
    report=dict(schema='htt.r61.kinematic_images/1',baseline=BASELINE,
      source_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
      source={'carrier':str(source.relative_to(root)),'sha256':sha(source),
              'fit_result':str(ref.relative_to(root)),'fit_result_sha256':sha(ref),'n_groups':prior['n_groups']},
      contract={'parameter_order':['Vx_km_s','Vy_km_s','Vz_km_s','dHx','dHy','dHz']+['kappa'+str(i) for i in range(5)],
                'physical_pullback':'beta=V/c; a=-dH+dcal; s=kappa-qcal',
                'kinematics':'s=sigma/H, a=A/(cH), Sigma=sqrt(s:s/6)',
                'frame':'ICRS/J2000, sourceward; fixed source and CMB-redshift convention',
                'calibration':'rho²=|dcal|²/3+2|qcal|²/15; deterministic full-sky RMS log-distance',
                'confidence':'same simultaneous11 95% ellipsoid for all primary functions; finite nuisance-model union',
                'cutoffs':levels,'calibration_rms_magnitude_grid':mags,'cosmic_variance_multipliers':[1.,1.25],
                'absolute_expansion':'unidentified: retained32D removes all four monopole rows',
                'vorticity':'no column in the retained distance response',
                'local_interpretation':'conditional first-order constant finite-depth response; no inferred history or spatial smoothing transfer'},
      variants=variants,model_union=union,
      checks={'covariance_decomposition_max_abs':maxparity},
      implementation={'numpy':np.__version__,'scipy':scipy.__version__,'python':platform.python_version(),
         'runner_sha256':sha(__file__),
         'image_module_sha256':sha(root/'htt/htt/htt/infer/r61_kinematic_images.py'),
         'fit_module_sha256':sha(root/'htt/htt/htt/infer/r58_mixed_tensor_likelihood.py')},
      limitations=['Fixed Gaussian covariance is inherited, not newly empirically calibrated.',
         'Calibration magnitudes and covariance multipliers are declared sensitivity inputs.',
         'Nonlinear image intervals are confidence-set projections, not scalar chi-square intervals or new independent detections.',
         'A component box is an outer enclosure of the same joint set, not an independent-factor likelihood.',
         'Mixed beta.a calibration enlargement is conservative; at zero calibration the trust-region endpoints are global.',
         'Directional maps sample the analytic simultaneous band; no global sky extremum is inferred from the grid.'],
      runtime_seconds=time.perf_counter()-start)
    (out/'KINEMATIC_IMAGES.json').write_text(json.dumps(clean(report),indent=2,allow_nan=False)+'\n')
    make_figures(report,sky_arrays,out)
    print(json.dumps(clean({'model_union':union,'box_width_ratios':{n:v['1.0']['images_by_rms_mag']['0.0']['beta_dot_a']['coordinate_box_comparator']['width_ratio'] for n,v in variants.items()},
                   'runtime_seconds':time.perf_counter()-start}),indent=2))
    return report


def make_figures(report,sky,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    names=list(report['variants']);fig,axes=plt.subplots(1,3,figsize=(14,5.5),constrained_layout=True)
    targets=[('Sigma',r'$\Sigma=\sqrt{\sigma_{ab}\sigma^{ab}/(6H^2)}$'),
             ('acceleration_over_cH',r'$|A|/(cH)$'),('relative_speed_over_c',r'$|\beta|$')]
    for ax,(target,label) in zip(axes,targets):
        for j,name in enumerate(names):
            for mag,color,dy in [('0.0','#24567a',-.12),('0.005','#d56b2b',.12)]:
                row=report['variants'][name]['1.0']['images_by_rms_mag'][mag][target]
                ax.plot([row['lower'],row['upper']],[j+dy]*2,color=color,lw=2.5,
                        label=('0 mmag' if mag=='0.0' else '5 mmag') if j==0 else None)
        ax.set_yticks(range(len(names)),[x.replace('log_','') for x in names]);ax.invert_yaxis()
        ax.set_xlabel(label);ax.grid(axis='x',alpha=.22);ax.legend(frameon=False,fontsize=9)
    fig.suptitle('CF4: simultaneous 95% kinematic confidence images\nFixed covariance; finite angular-calibration allowance',fontsize=14)
    fig.savefig(out/'KINEMATIC_CONSTRAINTS.png',dpi=180);fig.savefig(out/'KINEMATIC_CONSTRAINTS.pdf');plt.close(fig)
    fig=plt.figure(figsize=(12,4.7),layout='constrained')
    for j,(arr,title) in enumerate([(sky['log_mono__center'],'Apparent directional expansion: log_mono'),
               ((sky['union_upper']-sky['union_lower'])/2,'Half-width of seven-model simultaneous envelope')],1):
        ax=fig.add_subplot(1,2,j,projection='mollweide')
        p=ax.pcolormesh(sky['longitude_rad'],sky['latitude_rad'],100*arr,shading='auto',
                       cmap='coolwarm' if j==1 else 'viridis')
        ax.grid(alpha=.25);ax.set_title(title,fontsize=11)
        fig.colorbar(p,ax=ax,orientation='horizontal',pad=.1,label='100 × dimensionless angular coefficient')
    fig.suptitle('ICRS directions; zero additional calibration; fixed constant-response model',fontsize=12)
    fig.savefig(out/'KINEMATIC_SKY.png',dpi=180);fig.savefig(out/'KINEMATIC_SKY.pdf');plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--repo-root',default='.');p.add_argument('--output',required=True)
    a=p.parse_args();run(a.repo_root,a.output)
