#!/usr/bin/env python3
"""Actual SMICA map -> finite-source Lorentz response -> conditional Fisher stress.

Source is *a band-limited re-fit of the delivered observed map*, not the
true full-sky foreground/beam-deconvolved sky. No physical Planck inference.
Same-sky retrospective exploration, not a confirmatory detection test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import time

import numpy as np

from obsstat.processed_boost_theory_bridge import (
    first_order_sky_generator, fisher_with_high_mode_stress,
    processed_boost_jacobian, real_harmonics_with_gradients,
)
from obsstat.r7_cmb_product_response import pixel_fit_geometry, real_design
from fit_cmb_smica_noise_modes import require_gated_cache
from run_smica_reboot_pilot import build_ols_projector

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / 'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
GATE = ROOT / 'docs/generated/k1_e2e_cache_gate_ffp10_smica.json'
COEFF = ROOT / 'docs/observational_reboot_20261014/results/smica_response_scan_v2/processing_coefficients.npz'
DIPOLE = ROOT / 'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json'
MASKS = (.5, .8)
SOURCE_CUTOFFS = (5, 8, 12)
STRESS_MICROK = (0., .1, 1., 3., 10.)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute(*, mask, observed_map, source_packet, prior_processed, beta):
    """Six processed-source Jacobians (2 masks x 3 source cutoffs)."""
    n, (all_y, all_dt, all_dp) = pixel_fit_geometry()[0], source_packet
    full_design = real_design(n, ell_max=5)
    if not np.allclose(full_design, all_y[:, :36], rtol=0, atol=2e-13):
        raise ValueError('real harmonic basis convention drift')
    records=[]
    for im, threshold in enumerate(MASKS):
        support, p5, info = build_ols_projector(full_design, (mask > threshold).astype(float))
        obs_target = p5[4:36] @ observed_map[support]
        fitted_target = prior_processed[im * 3]  # L5
        if not np.allclose(obs_target, fitted_target, atol=4e-8, rtol=0):
            raise ValueError('stored six-processor observations differ from map replay')
        # Monopole T0 boost response is a fitted ell1, not a retained ell2..5
        mono_residual=float(np.max(np.abs(p5[4:36] @ n[support])))
        if mono_residual>1e-9:raise ValueError('joint-fit dipole cancellation violated')
        null = prior_processed[im*3] if False else None  # same processor rows bound below
        k = p5[4:36] @ all_y[support, 36:169]
        kval=np.linalg.svd(k,compute_uv=False)
        for isrc, lmax in enumerate(SOURCE_CUTOFFS):
            size=(lmax+1)**2
            selected_sky=all_y[:, :size]
            source_support, source_p, meta = build_ols_projector(selected_sky,(mask>threshold).astype(float))
            if not np.array_equal(source_support,support):
                raise ValueError('source and target masks differ')
            a=source_p@observed_map[support]
            generated=first_order_sky_generator(n,
                      (all_y[:,:size],all_dt[:,:size],all_dp[:,:size]),a)
            j=processed_boost_jacobian(generated,support,p5)
            delta=j@beta
            records.append({
                'mask_threshold':threshold,'source_fit_lmax':lmax,
                'source_fitted_coefficients':int(size),
                'source_fit_selected_pixels':meta['selected_pixels'],
                'source_fit_condition':meta['design_condition'],
                'target_fit_condition':info['design_condition'],
                'monopole_dipole_cancellation_max':mono_residual,
                'source_excluded_monopole_perturbation':'T0*n is fitted ell1 at first beta order',
                'observed_retained_norm_microk':float(np.linalg.norm(obs_target)),
                'jacobian_frobenius_microk_per_beta':float(np.linalg.norm(j)),
                'jacobian_singular_values_microk_per_beta':np.linalg.svd(j,compute_uv=False).tolist(),
                'reference_beta_tangent_shift_norm_microk':float(np.linalg.norm(delta)),
                'reference_beta_tangent_shift_ratio':float(np.linalg.norm(delta)/np.linalg.norm(obs_target)),
                'reference_beta_tangent_shift_max_abs_microk':float(np.max(np.abs(delta))),
                'source_high_mode_regression_rms_microk_per_coefficient':
                     float(np.linalg.norm(a[36:])/np.sqrt(max(1,len(a)-36))) if lmax>5 else None,
                '_J':j, '_K':k,'_K_singular':kval,
            })
    return records


def run(outdir: Path):
    if outdir.exists():
        raise ValueError('fresh output directory required: results are immutable')
    start=time.perf_counter()
    gate=json.loads(GATE.read_text())
    cache_sha=require_gated_cache(CACHE,gate)
    with np.load(CACHE,allow_pickle=False) as source:
        observed_map=np.asarray(source['observed_map'],dtype=np.float64)
        mask=np.asarray(source['common_mask'],dtype=np.float64)
    if (observed_map.shape!=(49152,) or mask.shape!=(49152,)
        or not np.isfinite(observed_map).all()
        or not np.isfinite(mask).all()):
        raise ValueError('gated NSIDE64 observed-map/mask dimensions invalid')
    with np.load(COEFF,allow_pickle=False) as coeff:
        stored_obs=np.asarray(coeff['observed'],dtype=float)
        stored_pairs=np.asarray(coeff['paired'],dtype=float)
    if stored_obs.shape!=(6,32) or stored_pairs.shape!=(6,300,32):
        raise ValueError('expected 6 x 300 x 32 released fitted coefficient rows')
    beta=np.array(json.loads(DIPOLE.read_text())['beta_xyz'],dtype=float)
    if beta.shape!=(3,) or not np.isfinite(beta).all() or np.linalg.norm(beta)>=1:
        raise ValueError('reference beta invalid')
    directions,_=pixel_fit_geometry(nside=64)
    packed=real_harmonics_with_gradients(directions,lmax=12)
    records=compute(mask=mask,observed_map=observed_map,source_packet=packed,
                    prior_processed=stored_obs,beta=beta)
    for rec in records:
        idx=MASKS.index(rec['mask_threshold'])*3
        null=stored_pairs[idx,60:]  # disjoint calibration IDs, same sky family.
        sampling=np.cov(null,rowvar=False,ddof=1)
        scov=np.linalg.eigvalsh(sampling)
        if scov[0]<=0 or scov[-1]/scov[0]>1e12:
            raise ValueError('released finite-null covariance unsupported')
        fisher=[]
        for stress in STRESS_MICROK:
            f=fisher_with_high_mode_stress(rec['_J'],sampling,rec['_K'],stress)
            fisher.append({'extra_high_mode_sigma_microk':stress,
                           'fisher_eigenvalues':np.linalg.eigvalsh(f).tolist(),
                           'beta_reference_response_over_conditional_scatter':
                                  float(np.sqrt(max(0,beta@f@beta))),
                           'fisher_trace':float(np.trace(f))})
        if any(fisher[j]['fisher_trace']+1e-8<fisher[j+1]['fisher_trace']
               for j in range(len(fisher)-1)):
            raise ValueError('Loewner monotonicity of high-mode stress violated')
        rec['conditional_null_covariance_condition']=float(scov[-1]/scov[0])
        rec['sample_covariance_rows']=len(null)
        rec['omitted_ell6_to12_response_rank'] = int(np.sum(
            rec['_K_singular']>rec['_K_singular'][0]*1e-10))
        rec['omitted_ell6_to12_response_smallest_singular'] = float(rec['_K_singular'][-1])
        rec['fisher_stress']=fisher
        if rec['source_fit_lmax']==12:
            # Paired-sky unit is one entire 32-dimensional row.
            rng=np.random.default_rng(20261015+idx)
            bvals=[]
            for _ in range(250):
                sampled=null[rng.integers(0,len(null),size=len(null))]
                cb=np.cov(sampled,rowvar=False,ddof=1)
                fb=fisher_with_high_mode_stress(rec['_J'],cb,rec['_K'],0.)
                bvals.append(float(np.sqrt(max(0.,beta@fb@beta))))
            rec['conditional_covariance_sampling_bootstrap']={
                'iid_null_assumption':'conditional delivered 240 unique sky rows; not physical null',
                'replicates':len(bvals),
                'p025_median_p975':np.quantile(bvals,[.025,.5,.975]).tolist(),
                'quantity':'sqrt(beta_ref^T J^T C_hat^{-1} J beta_ref)',
                'not':'not a parameter CI; not an independent new simulation; inverse sample covariance may bias'}
        del rec['_J'],rec['_K'],rec['_K_singular']
    for threshold in MASKS:
        subset=[r for r in records if r['mask_threshold']==threshold]
        ref=subset[0]['jacobian_frobenius_microk_per_beta']
        for row in subset:
            row['relative_norm_to_lmax5']=row['jacobian_frobenius_microk_per_beta']/ref
    result={
     'schema':'htt.theory-to-observed-smica-processed-boost/1',
     'source_commit': '13d8d85fa470d645d008986e8f77d8d0f70fdf54',
     'scientific_status':'EXECUTED_EXPLORATORY_FIXED_PRODUCT_CONDITIONAL_NOT_PHYSICAL_LIKELIHOOD',
     'source_observation':'Planck PR3 SMICA temperature fixed NSIDE64 delivered map',
     'raw_observed_input_units':'microK thermodynamic temperature FLUCTUATIONS',
     'fixed_beta_reference':beta.tolist(),
     'reference_beta_role':'Hypothetical incremental local boost tangent to a source surrogate already reconstructed from the OBSERVED delivered sky, not an attribution of the observed CMB pattern or measurement of additional velocity','fixed_beta_norm':float(np.linalg.norm(beta)),
     'sampling':'300 same paired CMB+noise realizations already used in earlier pilot; 60 training, 240 calibration; NOT independent new evidence',
     'bootstrap':'For L=12 only, 250 IID-with-replacement resamples of delivered 240 paired null rows, conditional sampling-covariance uncertainty only; not a physical parameter confidence interval',
     'source_model':'selected-sky OLS reconstruction ell<=5,8,12; not full-sky astrophysical T or all-mode transfer',
     'target_model':'same mask >0.5 or >0.8; fixed ell0..5 simultaneous OLS; retain ell2..5',
     'additional_high_mode_stress':'A^2 K K.T for ell6..12, A in microK per independent real harmonic coefficient; only a hypothetical ADDITIONAL nuisance covariance beyond delivered null; may double count existing uncertainty if treated as a survey likelihood',
     'model_closure_missing':['true full-sky source T with frequency-dependent foreground and beam',
         'high-ell tail above12 and upstream map downgrade/transfer','physical observed/null exchangeability',
         'actual sky intrinsic octupole, shared-source dipole law, global tilt/Bianchi transfer'],
     'source_sha256': {str(p.relative_to(ROOT)):digest(p) for p in (GATE,COEFF,DIPOLE)},
     'gated_cache_identity':cache_sha,
     'n_pixels':len(mask),'elapsed_seconds':time.perf_counter()-start,
     'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     'records':records,
    }
    outdir.mkdir(parents=True)
    (outdir/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=[
      '# HTT 기존 boost·식별성 정리의 실제 Planck 지도 적용',
      '',
      '결과 등급: **실제 원자료/관측상품 계산 완료, 모델 조건부 탐색적 진단**.',
      '',
      '계산은 동일 SMICA 관측 하늘을 여러 source cutoff로 재구성한 제한 모델이며,',
      '추정 속도, 전단 또는 Bianchi family 검출이 아니다. Planck 원자료를 재보정한 결과도 아니다.',
      '',
      '| mask threshold | source L | ||J||F [microK/beta] | ||J beta_ref|| [microK] | relative to observed low-l norm | extra-stress A=0 conditional sigma |',
      '|---|---:|---:|---:|---:|---:|',
     ]
    for v in records:
        lines.append(f"| {v['mask_threshold']} | {v['source_fit_lmax']} | {v['jacobian_frobenius_microk_per_beta']:.6g} | {v['reference_beta_tangent_shift_norm_microk']:.6g} | {v['reference_beta_tangent_shift_ratio']:.6g} | {v['fisher_stress'][0]['beta_reference_response_over_conditional_scatter']:.6g} |")
    lines.extend(['','## 물리적 해석 경계',
      '',
      '조건부 Fisher 행렬은 실제 kinematic beta의 추정치가 아니라, **이미 관측된 하늘을 다시 재구성한 source surrogate에 주입하는 추가 미소 boost의 접선 응답**이다.',
      'C_null은 동일 저장 모의하늘 240개의 샘플 공분산이다. 추가 A²KKᵀ를 실제 nuisance로 사용할 경우 기존 하늘의 cosmic variance 중복계산 가능성을 평가해야 한다.',
      'T0의 일차 도플러 dipole은 joint-fit의 ell1에 흡수되므로 retained ell2..5에 기여하지 않는다.',
      'mask/fit 효과는 *cache 단계*에서만 계산; upstream Planck compsep, true full-sky high modes, emission physics는 포함하지 않는다.',
      'Finite cutoff 변화를 bias 인증이나 사후 유의성 재보정으로 해석하지 않는다.',
      'L12 조건부 부트스트랩 250회는 covariance 추정의 MC 변동이지 관측 velocity posterior 또는 p-value가 아니다.',
      '',
      '연관 정리: HTT Report A의 local-observer temperature pullback, WU-010, nuisance projection, covariance-whitening.',
      '선행 문헌: Planck Collaboration 2014 A&A Doppler Boosting (aa21556-13); Challinor & van Leeuwen 2002; Dai & Chluba 2014 aberration kernels.',
    ])
    (outdir/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(1,2,figsize=(10,3.6),layout='constrained')
    for threshold in MASKS:
        sub=[r for r in records if r['mask_threshold']==threshold]
        axs[0].plot(SOURCE_CUTOFFS,
            [r['reference_beta_tangent_shift_norm_microk'] for r in sub],
            marker='o',label=f'mask>{threshold}')
        for r in sub:
            axs[1].plot(STRESS_MICROK,
                [f['beta_reference_response_over_conditional_scatter'] for f in r['fisher_stress']],
                marker='.',label=f"m>{threshold}, L{r['source_fit_lmax']}")
    axs[0].set(xlabel='Source reconstruction cutoff L',ylabel='||J beta_ref|| [microK]',
               title='Fixed observed SMICA source-model sensitivity')
    axs[1].set(xlabel='Extra high-mode sigma [microK/coefficient]',
               ylabel='sqrt(beta_ref^T F beta_ref)',
               title='Additional nuisance stress (conditional)')
    axs[0].legend(fontsize=8)
    axs[1].legend(fontsize=6,ncol=2)
    for ext in ('png','pdf'):
        fig.savefig(outdir/f'processed_boost_theory_stress.{ext}',dpi=170)
    plt.close(fig)
    return result


def main():
    a=argparse.ArgumentParser()
    a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args()
    result=run(args.output_dir)
    print(json.dumps({'status':result['scientific_status'],
       'records':len(result['records']),
       'computed_seconds':result['elapsed_seconds'],
       'input_cache_sha256':result['gated_cache_identity'],
       'results':[{k:v for k,v in r.items() if k in (
           'mask_threshold','source_fit_lmax','reference_beta_tangent_shift_norm_microk',
           'reference_beta_tangent_shift_ratio','relative_norm_to_lmax5')} for r in result['records']]},
       ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
