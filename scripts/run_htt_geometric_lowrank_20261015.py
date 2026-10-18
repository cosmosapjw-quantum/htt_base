#!/usr/bin/env python3
"""Actually execute fixed-geometry 1-3D CMB leakage controls on 300 paired skies.

Source data: masked Planck PR3 SMICA and released FFP10 simulation products.
No physical Planck null, velocity, Bianchi or shear detection is claimed.
All nuisance hyperparameters are selected using training60 only. The paired
heldout240 are used to inspect prediction, not select or re-tune the score.
"""
from __future__ import annotations

import argparse,hashlib,json,time,resource
from pathlib import Path
import numpy as np

from obsstat.r7_cmb_product_response import real_design,pixel_fit_geometry
from obsstat.processed_boost_theory_bridge import (real_harmonics_with_gradients,first_order_sky_generator,processed_boost_jacobian)
from obsstat.geometric_lowrank_control import (
    geometry_directions,fit_geometric_control,cv_select_control,
    score_selected_mask,rank_two_mask_joint)
from obsstat.paired_highmode_control import (
    fit_family,transform_rows,rank_upper_tail)
from run_smica_reboot_pilot import build_ols_projector,validate_realization_ids
from fit_cmb_smica_noise_modes import require_gated_cache
from scipy.stats import beta as beta_dist

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
GATE=ROOT/'docs/generated/k1_e2e_cache_gate_ffp10_smica.json'
COEFF=ROOT/'docs/observational_reboot_20261014/results/smica_response_scan_v2/processing_coefficients.npz'
PILOT=ROOT/'docs/observational_reboot_20261014/results/smica_pilot/pilot_features_coefficients.npz'
SOURCE_RECEIPT=ROOT/'docs/observational_reboot_20261014/results/smica_response_scan_v2/response.json'
DIPOLE=ROOT/'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json'
PRIOR_J=ROOT/'docs/research_program/theory_obs_application_20261015/results/cmb_processed_boost_v2/result.json'
RANKS=(1,2,3)
RIDGES=(.25,1.,4.)
SHRINK=.2


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cp(k,b):
    return [0 if k==0 else float(beta_dist.ppf(.025,k,b-k+1)),
            1 if k==b else float(beta_dist.ppf(.975,k+1,b-k))]


def run(out):
    start=time.perf_counter()
    if out.exists():raise ValueError('create-only output required')
    with np.load(COEFF,allow_pickle=False) as src:
        observed=np.asarray(src['observed'],dtype=float)
        paired=np.asarray(src['paired'],dtype=float)
    if observed.shape!=(6,32) or paired.shape!=(6,300,32):
        raise ValueError('frozen 6 x 300 x 32 per-sky coefficients needed')
    with np.load(PILOT,allow_pickle=False) as prior:
        ids=validate_realization_ids(prior['cmb_ids'],prior['noise_ids'])
        np.testing.assert_allclose(observed[0],prior['observed_retained_coefficients'],rtol=0,atol=1e-9)
        np.testing.assert_allclose(paired[0],prior['paired_retained_coefficients'],rtol=0,atol=1e-9)
    receipt=json.loads(SOURCE_RECEIPT.read_text())
    if receipt['rows']!=300:
        raise ValueError('source receipt must identify 300 paired skies')
    cache_identity=require_gated_cache(CACHE,json.loads(GATE.read_text()))
    if receipt['source_cache_sha256']!=cache_identity:
        raise ValueError('source receipt/cache identity mismatch')
    with np.load(CACHE,allow_pickle=False) as s:
        mask=np.asarray(s['common_mask'],float)
        observed_map=np.asarray(s['observed_map'],float)
    sky,_=pixel_fit_geometry()
    packet=real_harmonics_with_gradients(sky,lmax=12)
    y=packet[0]
    np.testing.assert_allclose(y[:10,:36],real_design(sky[:10],ell_max=5),rtol=0,atol=3e-13)
    beta=np.asarray(json.loads(DIPOLE.read_text())['beta_xyz'],dtype=float)
    j_prior=json.loads(PRIOR_J.read_text())
    rows=[]
    mask_scored=[]
    rng=np.random.default_rng(20261015)
    for i,threshold in enumerate((.5,.8)):
        selection,p,meta=build_ols_projector(y[:,:36],(mask>threshold).astype(float))
        k=p[4:36]@y[selection,36:]
        U,sing=geometry_directions(k,rank=3)
        y0=observed[3*i]
        h0=observed[3*i+2]-observed[3*i]
        ym=paired[3*i]
        hm=paired[3*i+2]-ym
        # Frozen 300 sky IDs; train60, independent calibration240 under
        # delivered simulation source law. Same ID appears in both y and h.
        train_y,cal_y=ym[:60],ym[60:]
        train_h,cal_h=hm[:60],hm[60:]
        fitted=cv_select_control(train_y,train_h,U,rank_choices=RANKS,
                         ridge_choices=RIDGES,cov_shrink=SHRINK,
                         folds=5,minimum_gain_fraction=.005)
        chosen=score_selected_mask(fitted,y0,h0,cal_y,cal_h)
        mask_scored.append(chosen)
        base=fit_family(train_y,cov_shrink=SHRINK)
        # Source surrogate was re-fitted on the observed sky. This is a
        # hypothetical additional boost derivative, not actual solar motion
        # estimation or a global Bianchi transfer result.
        support12,p12,_=build_ols_projector(y,(mask>threshold).astype(float))
        if not np.array_equal(selection,support12):
            raise ValueError('L5/L12 mask support mismatch')
        a12=p12@observed_map[support12]
        generator=first_order_sky_generator(sky,packet,a12)
        J5=processed_boost_jacobian(generator,selection,p)
        J12=p12[4:36]@generator[support12]
        old=[r for r in j_prior['records'] if r['mask_threshold']==threshold and r['source_fit_lmax']==12]
        if len(old)!=1 or not np.isclose(np.linalg.norm(J5),
             old[0]['jacobian_frobenius_microk_per_beta'],rtol=1e-10,atol=1e-9):
            raise ValueError('previous physical surrogate Jacobian identity mismatch')
        def conditional_reference(j,c):
            f=j.T@np.linalg.solve(c,j)
            return float(np.sqrt(max(0,beta@f@beta)))
        model=fitted['model']
        Jr=J5-model.operator.T@(J12-J5)
        tangent={
            'beta_reference_norm':float(np.linalg.norm(beta)),
            'source_reconstruction_ell_cutoff':12,
            'reference_beta_tangent_norm_microK':float(np.linalg.norm(Jr@beta)),
            'baseline_reference_tangent_norm_microK':float(np.linalg.norm(J5@beta)),
            'score_selected_reference_beta_over_conditional_training_scatter':
              conditional_reference(Jr,model.covariance),
            'baseline_reference_beta_over_conditional_training_scatter':
              conditional_reference(J5,base.covariance),
            'linear_jacobian_identity':'J_R=J5-B_training.T@(J12-J5)',
            'physical_estimate':False,
            'not':'No observed physical velocity or Bianchi tilt; source is already the observed SMICA sky, not the unboosted intrinsic sky.'
        }
        baseline_loss=np.sum(transform_rows(cal_y,cal_h,base)**2,axis=1)
        selected_loss=np.sum(chosen['null_residuals']**2,axis=1)
        ratio=float(np.mean(selected_loss)/np.mean(baseline_loss)-1.)
        pidx=rng.integers(0,240,size=(1000,240))
        bt=np.mean(selected_loss[pidx],axis=1)/np.mean(baseline_loss[pidx],axis=1)-1
        candidates=[]
        for candidate in fitted['candidates']:
            model=fit_geometric_control(train_y,train_h,U,rank=candidate['rank'],
                ridge_multiplier=candidate['ridge_multiplier'],cov_shrink=SHRINK)
            energy=np.sum(transform_rows(cal_y,cal_h,model)**2,axis=1)
            candidates.append({
                **candidate,
                'heldout_relative_mse_not_used_for_selection':float(np.mean(energy)/np.mean(baseline_loss)-1.)
            })
        geom=[float(np.mean(np.sum((cal_h@U[:,:k])**2,axis=1))/np.mean(np.sum(cal_h**2,axis=1))) for k in RANKS]
        rows.append({
            'mask_threshold':threshold,'selected_pixels':meta['selected_pixels'],
            'geometry_K_shape':[32,133],
            'K_singular_first_three':sing[:3].tolist(),
            'K_smallest_singular':float(sing[-1]),
            'K_full_rank':int(np.linalg.matrix_rank(k,tol=sing[0]*1e-10)),
            'train_cv':{
                'selected':fitted['selected'],
                'selected_training_CV_ratio':fitted['cv_ratio'],
                'rank_candidates':list(RANKS),'rho_candidates':list(RIDGES),
                'folds':fitted['cv_folds'],
                'selection_only_training':True,
                'minimum_CV_gain_fraction':.005,
                'candidates':candidates},
            'hypothetical_local_boost_tangent':tangent,
            'heldout_diagnostics':{
                'n_same_sky_null_rows':240,
                'relative_MSE_selected_minus_baseline':ratio,
                'paired_bootstrap_1000_lower_upper':np.quantile(bt,[.025,.975]).tolist(),
                'heldout_MSE_selected':float(np.mean(selected_loss)),
                'heldout_MSE_baseline':float(np.mean(baseline_loss)),
                'preassigned_rank_1_2_3_geometry_energy_fraction_of_difference':geom,
                'not_validated_physical_decontamination':True
            },
            'observed_score':float(chosen['observed']),
            'finite_marginal_rank':rank_upper_tail(float(chosen['observed']),chosen['null']),
            'input_y_source':'same-sky selected mask fitted low ell2..5',
            'input_h_source':'same sky Y12 - Y5, not an independent physical high-mode measurement'
        })
    joint=rank_two_mask_joint(mask_scored)
    b=int(joint['B']);ge=int(joint['exceedances'])
    data={
        'schema':'htt.mask-geometric-lowrank-leakage/1',
        'status':'EXECUTED_FIXED_GEOMETRY_TRAIN60_SELECTOR_CALIB240_CONDITIONAL_ONLY',
        'source_head':'13d8d85fa470d645d008986e8f77d8d0f70fdf54',
        'planck_cache_sha256':cache_identity,
        'sources':{str(p.relative_to(ROOT)):sha(p) for p in (GATE,COEFF,PILOT,SOURCE_RECEIPT,DIPOLE,PRIOR_J)},
        'n_simulation_pairs':300,'n_independent_training_sky_pairs':60,
        'n_calibration_sky_pairs':240,
        'geometry_def':'left singular vectors of K=P_low_mask Y_high(ell6..12), from fixed mask and harmonic basis',
        'selection':'five-fold CV on 60 training skies only; baseline if no candidate reduces CV MSE by more than .5%; no heldout tuning',
        'same_sky_joint_max':{
            'exceedances':ge,'B':b,'p_rank':joint['p_rank'],
            'observed_max':joint['observed_joint_max_score'],
            'iid_exceedance_probability_CP_95':cp(ge,b)},
        'recorded':rows,
        'source_realization_ids':'paired CMB/noise IDs 0..299, complete sky as one statistical unit',
        'actual_sky_exchangeable_under_delivered_null':'UNVERIFIED',
        'historical_sky_selection':'RETROSPECTIVE; current finite rank is not confirmatory physical p',
        'reference_beta_role':'Additional infinitesimal observer boost of already observed surrogate T_L12; not the source velocity or tilt',
        'MSE_interpretation':'same-sky heldout simulation prediction, not observed CMB truth',
        'native_bianchi_transfer':'ABSENT',
        'elapsed_seconds':time.perf_counter()-start,
        'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    np.savez_compressed(out/'joint_scores.npz',
        observed_scores=np.asarray([q['observed'] for q in mask_scored]),
        calibration_scores=np.column_stack([q['null'] for q in mask_scored]),
        joint_maxima=joint['null_joint_max_scores'],
        physical_units='low real harmonics microK, score dimensionless')
    lines=['# Planck 고차누출 모드의 실제 mask 기하 기반 저차원 제어',
        '',
        '대상: 동일 실제 SMICA 관측 하늘, 저장된 300 paired FFP10 CMB+noise 모의 하늘.',
        '조건부 순위 및 예측력만 평가하며 실제 FFP10=observed sky 완전한 물리 null은 검증되지 않았다.',
        '',
        '| mask | 선택 train-only | CV MSE 변화 | heldout MSE 변화 | paired 95% 구간 |',
        '|---|---|---:|---:|---|']
    for row in rows:
        v=row['heldout_diagnostics'];lo,hi=v['paired_bootstrap_1000_lower_upper']
        lines.append(f"| {row['mask_threshold']} | {row['train_cv']['selected']} | {(row['train_cv']['selected_training_CV_ratio']-1):.4%} | {v['relative_MSE_selected_minus_baseline']:.4%} | [{lo:.3%},{hi:.3%}] |")
    lines.extend(['',f"Conditional 2-mask joint rank: {ge+1}/241 = {joint['p_rank']:.7f}",
        '', '상위 고차 누출 기하모드를 이용한 통계적 회귀는 반드시 예측력이 개선된다는 뜻이 아니다.',
        '같은 하늘의 mask 변형·모드 상한을 독립 모의실현으로 취급하지 않았고, 240 heldout 행에서 모델을 선택하지 않았다.',
        '대체로 현재 원본의 noise/systematics와 CMB cosmic variance에 대한 물리적 모델 확인이 필요하다.',
        '선행 연구: Gruetjen & Shellard (arXiv:1212.6945), Planck 2018 IV (A&A 641 A4), HTT prior processed boost/Jacobian.',
    ])
    (out/'REPORT_KO.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,4),layout='constrained')
    for row in rows:
        vals=row['train_cv']['candidates']
        names=[f"k{c['rank']} r{c['ridge_multiplier']:g}" for c in vals]
        ax.plot(range(len(vals)),[c['cv_relative_mse'] for c in vals],
            marker='o',label=f"train-CV mask>{row['mask_threshold']}")
        ax.plot(range(len(vals)),[c['heldout_relative_mse_not_used_for_selection'] for c in vals],
            marker='.',linestyle='--',label=f"heldout mask>{row['mask_threshold']}")
    ax.axhline(0,color='gray',lw=1)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names,rotation=45,ha='right',fontsize=8)
    ax.set(ylabel='Relative MSE change vs baseline (negative = improvement)',
          title='Physics-geometry rank k=1..3; training-only CV vs independent heldout')
    ax.legend(fontsize=7)
    fig.savefig(out/'geometry_lowrank_CV_vs_heldout.png',dpi=170)
    plt.close(fig)
    print(json.dumps({'status':data['status'],'joint_rank':data['same_sky_joint_max'],
        'rows':[{key:item[key] for key in ('mask_threshold','K_singular_first_three',
               'observed_score')}|{'selected':item['train_cv']['selected'],
               'trainCV':item['train_cv']['selected_training_CV_ratio']-1.,
               'heldoutMSE':item['heldout_diagnostics']['relative_MSE_selected_minus_baseline']}
                for item in rows],
        'elapsed_seconds':data['elapsed_seconds']},ensure_ascii=False,indent=2))
    return data


if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--output-dir',type=Path,required=True)
    args=a.parse_args()
    run(args.output_dir)
