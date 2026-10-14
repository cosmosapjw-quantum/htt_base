#!/usr/bin/env python3
"""Project one SMICA cache observation and its 300 FFP10 noise maps identically.

The simulation scatter is a diagnostic until common simulation components and
processor response are identified. It is not a calibrated measurement covariance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import cho_factor, cho_solve

ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/'htt/src',ROOT/'htt',ROOT/'htt/htt'):
    sys.path.insert(0,str(path))
from obsstat.r7_cmb_product_response import pixel_fit_geometry


def require_gated_cache(path, gate):
    if not gate['cache_reproducibility_green']:
        raise ValueError('source cache lacks accepted reproducibility gate')
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024), b''):
            digest.update(chunk)
    identity='sha256:'+digest.hexdigest()
    if identity!=gate['cache_hash']:
        raise ValueError('selected cache hash differs from accepted source gate')
    return identity


def project(observed, noise, mask, design):
    observed=np.asarray(observed,dtype=float)
    noise=np.asarray(noise,dtype=float)
    mask=np.asarray(mask,dtype=float)
    if (observed.shape!=(49152,) or noise.ndim!=2 or noise.shape[1]!=49152
            or noise.shape[0]<64 or mask.shape!=observed.shape or design.shape!=(49152,36)):
        raise ValueError('one NSIDE64 observation, >=64 noise maps, and ell0..5 design required')
    support=np.isfinite(mask)&(mask>.5)
    if support.sum()<36 or not np.isfinite(observed[support]).all() or not np.isfinite(noise[:,support]).all():
        raise ValueError('finite common selected-sky observation and noise maps required')
    y=design[support]
    gram=y.T@y
    factor=cho_factor(gram,check_finite=True)
    rhs_obs=y.T@observed[support]
    rhs_noise=noise[:,support]@y
    obs=cho_solve(factor,rhs_obs)[4:]
    sims=cho_solve(factor,rhs_noise.T).T[:,4:]
    probe=np.zeros(36);probe[[4,13,35]]=[1.,-.5,.25]
    recovered=cho_solve(factor,y.T@(y@probe))
    if np.max(np.abs(recovered-probe))>1e-10:
        raise ValueError('low-mode injection recovery failed')
    centered=sims-sims.mean(axis=0)
    cov=centered.T@centered/(len(sims)-1)
    eig=np.linalg.eigvalsh(cov)
    if eig[0]<=0 or not np.isfinite(eig).all():
        raise ValueError('simulated low-mode noise covariance is not positive definite')
    half=len(sims)//2
    ca=np.cov(sims[:half],rowvar=False);cb=np.cov(sims[half:],rowvar=False)
    selected=noise[:,support]
    selected=selected-selected.mean(axis=1,keepdims=True)
    normalized=selected/np.linalg.norm(selected,axis=1)[:,None]
    correlations=normalized@normalized.T
    mean_pair_correlation=float((correlations.sum()-len(sims))/(len(sims)*(len(sims)-1)))
    return {'observed_microK':obs,'simulation_mean_microK':sims.mean(axis=0),
            'simulation_scatter_cov_microK2':cov,'selected_pixels':int(support.sum()),
            'fit_rank':int(np.linalg.matrix_rank(gram)),
            'injection_max_abs_microK':float(np.max(np.abs(recovered-probe))),
            'noise_simulations':len(sims),'noise_eigen_min_microK2':float(eig[0]),
            'noise_eigen_max_microK2':float(eig[-1]),
            'noise_condition':float(eig[-1]/eig[0]),
            'half_split_cov_frobenius_relative':float(np.linalg.norm(ca-cb)/np.linalg.norm(cov)),
            'mean_pairwise_selected_map_correlation':mean_pair_correlation,
            'max_abs_simulation_mean_mode_microK':float(np.max(np.abs(sims.mean(axis=0))))}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--cache',type=Path,default=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz')
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    gate=json.loads((ROOT/'docs/generated/k1_e2e_cache_gate_ffp10_smica.json').read_text())
    cache_identity=require_gated_cache(args.cache,gate)
    with np.load(args.cache) as cache:
        _,design=pixel_fit_geometry()
        result=project(cache['observed_map'],cache['noise_maps'],cache['common_mask'],design)
        result['noise_ids']=[int(x) for x in cache['noise_ids']]
    result.update({'task':'OA06','owner':'obsstat simulation-scatter diagnostic',
        'status':'DESCRIPTIVE_SMICA_SIMULATION_SCATTER_PHYSICAL_LAW_HOLD','claim_tier':'C0',
        'source_cache':str(args.cache),'source_cache_sha256':cache_identity,
        'source_gate':'docs/generated/k1_e2e_cache_gate_ffp10_smica.json',
        'processing_id':'K1_PREMASK_NSIDE64_SMICA_COMMON_MASK_GT_0p5_ELL0_TO_5_OLS_RETAIN_ELL2_TO_5',
        'harmonic_layout':'ORTHONORMAL_REAL_M0_COS_SIN',
        'map_units':'microK_CMB','covariance_units':'microK_CMB_squared',
        'measurement_model':'UNAVAILABLE: common spatial pattern and nonzero ensemble mean require processor/source interpretation',
        'mask_rule':'K1 cache common_mask > 0.5, same support for observation and all 300 noise maps',
        'covariance_role':'SIMULATION_SCATTER_NOT_CALIBRATED_MEASUREMENT_COVARIANCE',
        'simulation_dependence_status':'UNRESOLVED_FROM_SPATIAL_PAIR_CORRELATION; effective independent simulation count unknown',
        'same_sky_status':'ONE_SMICA_OBSERVATION; other map products not independent data',
        'physical_posterior_status':'HOLD_MISSING_RELEASE_RESPONSE_FOREGROUND_SYSTEMATIC_COVARIANCE_AND_PHYSICAL_SKY_MODEL',
        'F4_status':'UNAVAILABLE_MISSING_PHYSICAL_T0_DIPOLE_AND_OMITTED_MODE_CONTROL',
        'references':['https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html']})
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=False)
    cov=result['simulation_scatter_cov_microK2'];obs=result['observed_microK']
    sd=np.sqrt(np.diag(cov))
    fig,(ax,bx)=plt.subplots(2,1,figsize=(9,7),gridspec_kw={'height_ratios':[1,1.2]})
    x=np.arange(32)
    ax.errorbar(x,obs,yerr=sd,fmt='o',ms=3,lw=.8,color='#0072B2',ecolor='#56B4E9')
    ax.axhline(0,color='.4',lw=.8)
    for cut in (5,12,21):ax.axvline(cut-.5,color='.7',lw=.6)
    ax.set(xlabel='real harmonic coefficient index, ell=2..5',ylabel='microK_CMB',
           title='SMICA selected-sky modes; bars show uncalibrated simulation scatter')
    image=bx.imshow(cov,origin='lower',cmap='viridis',aspect='auto')
    bx.set(xlabel='mode index',ylabel='mode index',title='Full 32 x 32 centered simulation scatter')
    fig.colorbar(image,ax=bx,label='microK_CMB squared')
    fig.text(.01,.005,'K1 cache; common spatial pattern unresolved. Scatter is not a calibrated measurement error.',fontsize=8)
    fig.tight_layout(rect=(0,.025,1,1))
    for suffix in ('png','pdf'):fig.savefig(out/f'smica_noise_modes.{suffix}',dpi=170)
    plt.close(fig)
    for key,value in tuple(result.items()):
        if isinstance(value,np.ndarray):result[key]=value.tolist()
    (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':str(out),'selected_pixels':result['selected_pixels'],
                      'noise_simulations':result['noise_simulations'],
                      'noise_condition':result['noise_condition']}))


if __name__=='__main__':main()
