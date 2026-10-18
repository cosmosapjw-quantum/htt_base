#!/usr/bin/env python3
"""Real SMICA paired high-mode leakage conditional finite-null lab.

Use existing six processing variants of the SAME 300 simulation skies:
  L = ell0..5 low, D = ell0..12 low - ell0..5 low.
For each mask, all training-only ridge choices + baseline are jointly calibrated
with heldout 240 complete sky vectors. Observed sky is used for scoring only.
The reported finite rank is RETROSPECTIVE and conditional on an unverified
actual sky / delivered simulation exchangeability law, not a physical p-value.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
import resource

import numpy as np
from scipy.stats import beta as beta_distribution

from obsstat.paired_highmode_control import run_fixed_family, transform_rows
from obsstat.processed_boost_theory_bridge import (
    first_order_sky_generator, processed_boost_jacobian,
    real_harmonics_with_gradients)
from obsstat.r7_cmb_product_response import pixel_fit_geometry
from run_smica_reboot_pilot import build_ols_projector, validate_realization_ids
from fit_cmb_smica_noise_modes import require_gated_cache

ROOT=Path(__file__).resolve().parents[1]
COEFF=ROOT/'docs/observational_reboot_20261014/results/smica_response_scan_v2/processing_coefficients.npz'
PILOT=ROOT/'docs/observational_reboot_20261014/results/smica_pilot/pilot_features_coefficients.npz'
CACHE=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
GATE=ROOT/'docs/generated/k1_e2e_cache_gate_ffp10_smica.json'
DIPOLE=ROOT/'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json'
SOURCE_RECEIPT=ROOT/'docs/observational_reboot_20261014/results/smica_response_scan_v2/response.json'
PRIOR=ROOT/'docs/research_program/theory_obs_application_20261015/results/cmb_processed_boost_v2/result.json'
RIDGES=(.25,1.,4.)
COV_SHRINK=.2
NTRAIN=60
NMASK=2
NROW=300


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_paired():
    with np.load(COEFF,allow_pickle=False) as data:
        observed=np.asarray(data['observed'],dtype=float)
        paired=np.asarray(data['paired'],dtype=float)
    if observed.shape!=(6,32) or paired.shape!=(6,300,32):
        raise ValueError('frozen six processing choices/three hundred joint skies required')
    with np.load(PILOT,allow_pickle=False) as f:
        validate_realization_ids(f['cmb_ids'],f['noise_ids'],count=NROW)
        np.testing.assert_allclose(observed[0],f['observed_retained_coefficients'],atol=1e-10,rtol=0)
        np.testing.assert_allclose(paired[0],f['paired_retained_coefficients'],atol=1e-10,rtol=0)
    a=np.zeros((2,2,32),float)
    b=np.zeros((300,2,2,32),float)
    for mask in range(2):
        a[mask,0]=observed[mask*3]
        a[mask,1]=observed[mask*3+2]-observed[mask*3]
        b[:,mask,0]=paired[mask*3]
        b[:,mask,1]=paired[mask*3+2]-paired[mask*3]
    return a,b


def physics_tangents(training_models, observed_sky):
    n,_=pixel_fit_geometry()
    harmonic=real_harmonics_with_gradients(n,lmax=12)
    beta=np.asarray(json.loads(DIPOLE.read_text())['beta_xyz'],float)
    old=json.loads(PRIOR.read_text())
    physical=[]
    for mask_index,threshold in enumerate((.5,.8)):
        mask=observed_sky['mask']>threshold
        support5,p5,m5=build_ols_projector(harmonic[0][:,:36],mask.astype(float))
        support12,p12,m12=build_ols_projector(harmonic[0],mask.astype(float))
        if not np.array_equal(support5,support12):
            raise ValueError('same masked sky support required')
        coeff12=p12@observed_sky['map'][support12]
        gen=first_order_sky_generator(n,harmonic,coeff12)
        j5=processed_boost_jacobian(gen,support5,p5)
        j12=p12[4:36]@gen[support12]
        for rec in old['records']:
            if rec['mask_threshold']==threshold and rec['source_fit_lmax']==12:
                np.testing.assert_allclose(np.linalg.norm(j5),
                    rec['jacobian_frobenius_microk_per_beta'],atol=1e-7,rtol=1e-9)
        for lab in ('baseline','0.25','1','4'):
            model=training_models[f'{mask_index}:{lab}']
            jr=j5 - model.operator.T@(j12-j5)
            info=jr.T@np.linalg.solve(model.covariance,jr)
            info=(info+info.T)/2
            physical.append({
             'label':f'{mask_index}:{lab}',
             'mask_threshold':threshold,
             'source_cutoff_ell':12,
             'sampling_covariance':'shrinked covariance from independent 60 training skies',
             'reference_beta_increment_norm':float(np.linalg.norm(beta)),
             'incremental_beta_tangent_norm_microK':float(np.linalg.norm(jr@beta)),
             'fisher_eigenvalues_proxy':np.linalg.eigvalsh(info).tolist(),
             'reference_increment_over_conditional_training_scatter':
                     float(np.sqrt(max(0.,beta@info@beta))),
             'physical_velocity_estimate':False,
             'input_intrinsic_unboosted_sky':'NOT_KNOWN; re-fit of observed delivered SMICA map',
             'source_reprojection_condition5':m5['design_condition'],
             'source_reprojection_condition12':m12['design_condition'],
            })
    return physical


def cp_interval(k,B,confidence=.95):
    a=(1-confidence)/2
    return [0. if k==0 else float(beta_distribution.ppf(a,k,B-k+1)),
            1. if k==B else float(beta_distribution.ppf(1-a,k+1,B-k))]


def run(out):
    if out.exists():raise ValueError('fresh output directory needed')
    start=time.perf_counter()
    a,b=get_paired()
    receipt=json.loads(SOURCE_RECEIPT.read_text())
    if receipt.get('rows')!=300 or receipt.get('source_cache_sha256')!=('sha256:'+json.loads(GATE.read_text())['cache_hash'].split(':',1)[-1]):
        raise ValueError('six-processor receipt/skymap pair genealogy mismatch')
    stat=run_fixed_family(a,b[:NTRAIN],b[NTRAIN:],
                          ridge_multipliers=RIDGES,cov_shrink=COV_SHRINK)
    if stat['train_count']!=60 or stat['calibration_count']!=240:
        raise ValueError('training and heldout sky units split drift')
    with np.load(CACHE,allow_pickle=False) as f:
        reference={'map':np.asarray(f['observed_map'],float),
                   'mask':np.asarray(f['common_mask'],float)}
    identity=require_gated_cache(CACHE,json.loads(GATE.read_text()))
    phys=physics_tangents(stat['training_models'],reference)
    per=stat['per_feature']
    globalp=stat['global_rank']
    for obj in per:
        obj['null_tail_q_95pct_CP']=cp_interval(obj['marginal_rank']['exceedances'],240)
        obj['joint_max_q_95pct_CP']=cp_interval(obj['joint_max_adjusted_rank']['exceedances'],240)
    # Matched-outcome diagnostic: conditional on IID heldout null, compare
    # actual predictive squared error in complete paired sky units. Never
    # post-select the best ridge from observed score for the current p-rank.
    predictive=[]
    bootrng=np.random.default_rng(20261015)
    for m in range(2):
        yy=b[NTRAIN:,m,0,:];hh=b[NTRAIN:,m,1,:]
        baseline=stat['training_models'][f'{m}:baseline']
        base_sq=np.sum(transform_rows(yy,hh,baseline)**2,axis=1)
        for lam in RIDGES:
            label=f'{m}:{lam:g}'
            model=stat['training_models'][label]
            adj_sq=np.sum(transform_rows(yy,hh,model)**2,axis=1)
            ratio=float(np.mean(adj_sq)/np.mean(base_sq)-1.)
            picks=bootrng.integers(0,len(base_sq),size=(1200,len(base_sq)))
            paired_ratios=np.mean(adj_sq[picks],axis=1)/np.mean(base_sq[picks],axis=1)-1
            predictive.append({
               'label':label,'heldout_count':len(base_sq),
               'baseline_MSE':float(np.mean(base_sq)),
               'controlled_MSE':float(np.mean(adj_sq)),
               'controlled_minus_baseline_relative_MSE':ratio,
               'paired_iid_null_bootstrap_relative_MSE_95pct':
                  np.quantile(paired_ratios,[.025,.975]).tolist(),
               'claim':'paired heldout simulation prediction only; no physical observed source decontamination guarantee'})
    # Group sky ID is unique within 300 pairs in prior declared source. No new sky.
    result={
      'schema':'htt.same-sky-high-mode-regression-stat/1',
      'status':'EXECUTED_RETROSPECTIVE_CONDITIONAL_MATCHED_PRODUCT_ONLY',
      'source_head_before_run':'13d8d85fa470d645d008986e8f77d8d0f70fdf54',
      'fixed_source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in (COEFF,PILOT,GATE,DIPOLE,SOURCE_RECEIPT)},
      'full_gated_cache_sha256':identity,
      'law':'Y=selected-sky OLS retained ell2..5; H=Y_ell12_jointfit - Y_ell5_jointfit from same exact sky and same mask',
      'model':'train-only ridge prediction of Y given H; empirical shrinkage of residual-score covariance',
      'registered_hyperparameters':{'ridge_multipliers':list(RIDGES),'covariance_shrink_to_scalar_identity':COV_SHRINK,'train_rows':60,'calibration_rows':240},
      'families':'two masks times baseline plus three fixed ridge candidates; one joint maximum over eight features; retrospective choices do not adjust entire older project search',
      'null_law_limit':'FFP10 delivered CMB+noise map pairs are used only under conditional actual-observed/simulated exchangeability; physical null unknown',
      'same_sky_not_independent':True,
      'physical_closure_missing':['true unboosted CMB sky and beam/component-separation response',
        'foreground/split-systematics adequacy and real observed vs FFP null exchangeability',
        'all prior exploratory feature choices, survey source selection'],
      'global_rank':globalp,
      'global_observed_max_score':stat['global_observed_max_score'],
      'global_q_95pct_CP':cp_interval(globalp['exceedances'],240),
      'features':per,
      'heldout_predictive_ablation':predictive,
      'incremental_local_boost_surrogate_fisher':phys,
      'elapsed_seconds':time.perf_counter()-start,
      'rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    out.mkdir(parents=True,exist_ok=False)
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'score_vectors.npz',
       observed_scores=stat['observed_scores'],
       null_joint_maxima=stat['null_maxima'],
       feature_names=np.asarray(stat['labels']))
    lines=['# 2026-10-15: 동일 Planck 하늘의 고차 누출 공동통계',
      '', '등급: **실제 SMICA 관측-모의 산출물에 대한 탐색적 조건부 결과.**',
      '',
      '보정 이후 p-rank는 해당 모형의 actual/null 교환가능성이 참일 때만 유효.',
      '동일 하늘의 여러 mask/처리방식을 독립 사건으로 세지 않았다.',
      '',
      '| Mask/feature | observed standardized score | marginal p-rank | joint-max adjusted p-rank |',
      '|---|---:|---:|---:|']
    for q in per:
        lines.append(f"| {q['label']} | {q['transformed_observed_score']:.6g} | {q['marginal_rank']['p_rank']:.6g} | {q['joint_max_adjusted_rank']['p_rank']:.6g} |")
    lines.extend(['', '## 독립 보정 240개 하늘의 predictive error 대조',
      '', '| mask/ridge | baseline MSE | leakage-corrected MSE | 상대 증가율 | bootstrap 95% |',
      '|---|---:|---:|---:|---|'])
    for q in predictive:
        bounds=q['paired_iid_null_bootstrap_relative_MSE_95pct']
        lines.append(f"| {q['label']} | {q['baseline_MSE']:.4g} | {q['controlled_MSE']:.4g} | {q['controlled_minus_baseline_relative_MSE']:.3%} | [{bounds[0]:.3%}, {bounds[1]:.3%}] |")
    lines.extend(['', f"8-feature same-sky joint max-rank: {globalp['exceedances']+1}/241 = {globalp['p_rank']:.8f}",
       '', '대조변수 H는 ell12,ell5 fit 차이이므로 물리적 high-mode coefficient의 독립적인 측정이 아니다.',
       '추정된 회귀 B는 training60 하늘에서만 추정하고 관측 및 나머지 240 null 하늘에는 같은 변환을 적용한다.',
       'CP는 주어진 관측 문턱의 iid null exceedance q 구간이지 finite rank 자체의 CI가 아니다.',
       'source-surrogate boost Fisher는 물리적 속도/기울기 posterior나 Bianchi/전단 검출이 아니다.',
       '', '원전: Planck Collaboration IV (2020); Phipson & Smyth (2010); Hemerik & Goeman (2018); HTT GR/STAT report and prior processed Jacobian.',
    ])
    (out/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    ax.hist(stat['null_maxima'],bins=30,label='240 joint-null sky max scores',alpha=.75)
    ax.axvline(stat['global_observed_max_score'],label=f'Observed, rank {globalp["p_rank"]:.4f}',color='black')
    ax.set(xlabel='Max of 8 training-standardized quadratic scores',ylabel='Complete paired sky rows',title='Conditional retrospective high-mode leakage control')
    ax.legend()
    fig.savefig(out/'conditional_joint_max.png',dpi=170)
    plt.close(fig)
    print(json.dumps({'status':result['status'],'global_rank':globalp,
         'marginal':[(x['label'],x['marginal_rank']['p_rank']) for x in per],
         'physics_snr':[(x['label'],x['reference_increment_over_conditional_training_scatter']) for x in phys],
         'elapsed_s':result['elapsed_seconds']},ensure_ascii=False,indent=2))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',type=Path,required=True)
    opt=p.parse_args()
    run(opt.output_dir)
