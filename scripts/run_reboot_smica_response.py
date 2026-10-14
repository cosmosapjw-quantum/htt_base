#!/usr/bin/env python3
"""Finite retrospective mask/fit-limit response scan under delivered SMICA null.

One sky row contains every processing/statistic choice. Calibration never counts
the choices as additional independent skies. The scan cannot certify physical
foreground/systematic adequacy or an omitted-mode remainder bound.
"""
from __future__ import annotations
import argparse,json,resource,time
from pathlib import Path
import numpy as np
from obsstat.r7_cmb_product_response import pixel_fit_geometry,real_design
from obsstat.reboot_tensor_features import FEATURE_NAMES,feature_matrix,feature_vector
from run_smica_reboot_pilot import build_ols_projector,validate_realization_ids
from fit_cmb_smica_noise_modes import require_gated_cache
from calibrate_reboot_statistics import calibrate,write_result,file_sha256

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/observational_reboot_20261014'
CHOICES=[(mask,lmax) for mask in (.5,.8) for lmax in (5,8,12)]


def scan(cache,rows):
    directions,_=pixel_fit_geometry()
    y=real_design(directions,ell_max=16)
    retained=np.r_[np.zeros(4,dtype=bool),np.ones(32,dtype=bool)]
    observed=cache['observed_map'];mask=cache['common_mask']
    signal=cache['cmb_maps'][:rows];noise=cache['noise_maps'][:rows]
    observations=[];pairs=[];diagnostics=[]
    for threshold,lmax in CHOICES:
        fit=y[:,: (lmax+1)**2]
        support,operator,meta=build_ols_projector(fit,(mask>threshold).astype(float))
        obs=operator@observed[support]
        coeff=signal[:,support].astype(float)@operator.T+noise[:,support].astype(float)@operator.T
        shell=y[support,36:]
        response=operator[4:36]@shell
        # Low rows include ell0/1 nuisance in each simultaneous fit.
        low_response=operator@fit[support]
        shell_rows=[]
        for ell in range(6,17):
            r=operator[4:36]@y[support,ell*ell:(ell+1)**2]
            if ell<=lmax and np.max(abs(r))>1e-8:raise ValueError('included shell leakage exceeds numerical tolerance')
            shell_rows.append({'ell':ell,'included_in_fit':ell<=lmax,'operator_norm':float(np.linalg.norm(r,2))})
        diagnostics.append({'mask_threshold':threshold,'fit_lmax':lmax,
            'selected_pixels':int(support.sum()),'fit_condition':meta['design_condition'],
            'low_injection_max_abs':float(np.max(abs(low_response-np.eye(len(operator))))),
            'omitted_shell':'orthonormal-real ell6..16 coefficients; fixed finite injection basis',
            'shell_response_spectral_norm':float(np.linalg.norm(response,2)),
            'shell_response_frobenius_norm':float(np.linalg.norm(response)),
            'per_shell':shell_rows,
            'residual_ell1_microK':obs[1:4].tolist(),
            'residual_ell1_role':'cut-sky fit nuisance, not physical dipole',
            'observed_C2_microK2':float(obs[4:9]@obs[4:9]/5)})
        observations.append(obs[4:36]);pairs.append(coeff[:,4:36])
    return np.array(observations),np.array(pairs),diagnostics


def run(out,rows):
    start=time.perf_counter()
    if out.exists():raise ValueError('fresh output directory required')
    cache_path=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
    gate_path=ROOT/'docs/generated/k1_e2e_cache_gate_ffp10_smica.json'
    identity=require_gated_cache(cache_path,json.loads(gate_path.read_text()))
    with np.load(cache_path,allow_pickle=False) as data:
        validate_realization_ids(data['cmb_ids'],data['noise_ids'])
        observations,pairs,diagnostics=scan(data,rows)
    with np.load(BASE/'results/smica_pilot/pilot_features_coefficients.npz',allow_pickle=False) as prior:
        np.testing.assert_allclose(observations[0],prior['observed_retained_coefficients'],rtol=1e-10,atol=1e-10)
        np.testing.assert_allclose(pairs[0],prior['paired_retained_coefficients'][:rows],rtol=1e-10,atol=1e-10)
    out.mkdir(parents=True)
    receipt={'tasks':['RB01','RB03','RB04'],'source_cache_sha256':identity,
        'source_gate_sha256':file_sha256(gate_path),'code_sha256':file_sha256(__file__),
        'elapsed_seconds':time.perf_counter()-start,
        'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'rows':rows,'seed':'delivered fixed realization IDs, no new random seed',
        'response':diagnostics,'physical_adequacy':'HOLD_RELEASE_EFFECTIVE_TRANSFER_FOREGROUND_SYSTEMATIC_LAW',
        'remainder':'NSIDE64 cache-stage finite shell sensitivity only; upstream downgrade/beam/compsep and all omitted modes not bounded',
        'requested_parent':'gpt-6.1-sol/high','observed_parent':'UNKNOWN',
        'sources':['https://arxiv.org/html/1807.06208v2'],
        'processing':'native released fixed-weight products -> direct ud_grade NSIDE64 -> thresholded common mask -> simultaneous OLS; no effective-beam deconvolution'}
    from astropy.io import fits
    raw=ROOT/'workdir/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits'
    with fits.open(raw,memmap=True) as hdus:
        receipt['released_transfer']={'source':str(raw.relative_to(ROOT)),
            'coordinate':'GALACTIC','source_ordering':hdus[1].header.get('ORDERING'),
            'beam_column':'HDU2 INT_BEAM','ell0_to16':hdus[2].data['INT_BEAM'][:17].astype(float).tolist(),
            'role':'released effective full-sky transfer table; no masked direction-dependent operator calibration; ell0/1 zero cannot restore physical dipole'}
    (out/'response.json').write_text(json.dumps(receipt,indent=2)+'\n')
    np.savez(out/'processing_coefficients.npz',observed=observations,paired=pairs)
    if rows==300:
        obs=np.concatenate([feature_vector(x) for x in observations])
        features=np.concatenate([feature_matrix(x) for x in pairs],axis=1)
        meta=json.loads((BASE/'results/tensor_family_v1/declaration.json').read_text())
        meta['declaration_id']='retrospective-six-processing-eight-feature-jointscan-v1'
        meta['analysis_label']='Conditional SMICA joint morphology and processing sensitivity'
        meta['statistics']=[{'name':f'mask{mask}_L{lmax}_{name}','tail':'two-sided' if i<5 or i==7 else 'upper'}
                for mask,lmax in CHOICES for i,name in enumerate(FEATURE_NAMES)]
        meta['current_selection']['mask']=['>0.5','>0.8'];meta['current_selection']['fit_lmax']=[5,8,12]
        meta['current_selection']['residual_dipole']='fit nuisance retained descriptively, excluded from rank family'
        meta['observation_pipeline']=meta['null_pipeline']=meta['training_pipeline']='K1-six-common-processors-tensor8-v1'
        (out/'declaration.json').write_text(json.dumps(meta,indent=2)+'\n')
        result=calibrate(obs,features[60:],meta,features[:60])
        result['scientific_admission']='EXPLORATORY_RETROSPECTIVE_CONDITIONAL_ONLY; same sky/simulation rows as RB00'
        result['interpretation']['rank']='Max over all48 current processing/statistic choices; conditional delivered-simulation exchangeability assumed. Historical unrecorded choices and physical adequacy unresolved.'
        write_result(result,obs,features[60:],features[:60],out)
        print(json.dumps(result['global_joint_null']))
    else:print(json.dumps({'profile_rows':rows,'seconds':receipt['elapsed_seconds'],'rss_kib':receipt['peak_rss_kib_linux']}))
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(9,3.6))
    labels=[f"{d['mask_threshold']}, L{d['fit_lmax']}" for d in diagnostics]
    axes[0].bar(labels,[d['observed_C2_microK2'] for d in diagnostics]);axes[0].set_ylabel('fitted C2 (microK²)')
    axes[1].bar(labels,[d['shell_response_spectral_norm'] for d in diagnostics]);axes[1].set_ylabel('ell6..16 -> ell2..5 operator norm')
    for ax in axes:ax.tick_params(axis='x',rotation=35)
    fig.suptitle('SMICA finite processing sensitivity; no physical remainder bound');fig.tight_layout()
    for ext in ('png','pdf'):fig.savefig(out/f'response_sensitivity.{ext}',dpi=170)
    plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True)
    p.add_argument('--rows',type=int,choices=(16,300),default=300);a=p.parse_args();run(a.output_dir,a.rows)
