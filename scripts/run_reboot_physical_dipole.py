#!/usr/bin/env python3
"""Conditional solar-dipole inference and processor-bound boost diagnostics."""
from __future__ import annotations
import argparse,json,time
from pathlib import Path
import numpy as np
from htt.infer.physical_dipole import (measurement_proxy,physical_reference_dipole,direction,
    log_density,kinematic_quadrupole,compose_velocities,T_REF_K,A_REF_MICROK,C_KM_S,SOURCES)
from htt.infer.nuisance_rank import nuisance_projected_rank
from obsstat.r7_cmb_product_response import pixel_fit_geometry
from obsstat.boost_response import first_order_quadrupole_boost
from obsstat.lorentz_sky_pullback import pullback_thermodynamic_temperature_field
from run_smica_reboot_pilot import build_ols_projector
from calibrate_reboot_statistics import file_sha256

ROOT=Path(__file__).resolve().parents[1]


def render(result,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    beta=np.array(result['beta_xyz']);norm=np.linalg.norm(beta);axis=beta/norm
    speed=result['kinematic_speed_km_s'];sigmaspeed=result['conditional_speed_sigma_km_s']
    checks=result['finite_difference']
    fig,axes=plt.subplots(1,3,figsize=(11,3.7))
    v=np.linspace(speed-4*sigmaspeed,speed+4*sigmaspeed,201)
    log=np.array([log_density(axis*t/C_KM_S,extra_dipole=np.zeros(3)) for t in v])
    axes[0].plot(v,np.exp(log-log.max()));axes[0].set(xlabel='kinematic speed (km/s)',ylabel='relative conditional likelihood')
    angles=np.linspace(0,np.pi,200);axes[1].plot(np.rad2deg(angles),T_REF_K*1e6*norm**2*(np.cos(angles)**2-1/3))
    axes[1].set(xlabel='angle to apex (degrees)',ylabel='derived quadrupole\n(microK, true temperature)')
    axes[2].loglog([r['central_step_beta'] for r in checks],[r['retained_relative_frobenius'] for r in checks],'o-')
    axes[2].set(xlabel='finite difference beta step',ylabel='processed derivative relative error')
    fig.suptitle('Solar dipole Gaussian proxy and conditional endpoint response')
    fig.tight_layout(rect=(0,0,1,.92))
    for ext in ('png','pdf'):fig.savefig(out/f'dipole_response.{ext}',dpi=170)
    plt.close(fig)


def run(out):
    start=time.perf_counter()
    if out.exists():raise ValueError('fresh output directory required')
    beta,c=measurement_proxy();norm=np.linalg.norm(beta);axis=beta/norm
    speed=C_KM_S*norm;sigmaspeed=C_KM_S*np.sqrt(axis@c@axis)
    qkin=kinematic_quadrupole(beta,T_REF_K*1e6)
    nominal=3364.5*direction(264.,48.24)
    difference=physical_reference_dipole(T_REF_K)-nominal
    n,y=pixel_fit_geometry()
    cache=ROOT/'workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz'
    with np.load(cache) as a:mask=a['common_mask']
    support,operator,fit=build_ols_projector(y,mask)
    tensor_source=ROOT/'docs/observational_reboot_20261014/results/tensor_family_v1/tensor_features.npz'
    with np.load(tensor_source) as a:q=a['observed_Q']
    # Signed anisotropy is evaluated inside a strictly positive polynomial sky.
    source=lambda directions: T_REF_K*1e6+np.einsum('ni,ij,nj->n',directions,q,directions)
    thermal=source(n)
    analytic=np.column_stack([T_REF_K*1e6*n[:,i]+first_order_quadrupole_boost(q,np.eye(3)[i],n) for i in range(3)])
    projected=operator@analytic[support]
    checks=[]
    for h in (1e-3,1e-4,1e-5,1e-6):
        numerical=np.column_stack([(pullback_thermodynamic_temperature_field(n,h*np.eye(3)[i],source)-
                        pullback_thermodynamic_temperature_field(n,-h*np.eye(3)[i],source))/(2*h) for i in range(3)])
        error=(operator@numerical[support]-projected)[4:]
        checks.append({'central_step_beta':h,'retained_max_abs_microK_per_beta':float(np.max(abs(error))),
            'retained_relative_frobenius':float(np.linalg.norm(error)/np.linalg.norm(projected[4:]))})
    if min(r['retained_relative_frobenius'] for r in checks)>1e-5:
        raise ValueError('processed exact/analytic derivative check failed')
    remainder=[]
    for scale in (.25,.5,1.,2.):
        b=scale*beta;exact=pullback_thermodynamic_temperature_field(n,b,lambda z:np.full(len(z),T_REF_K*1e6))
        second=T_REF_K*1e6*(1+n@b+(n@b)**2-(b@b)/2)
        remainder.append({'beta_norm':float(np.linalg.norm(b)),
            'max_abs_pixel_remainder_microK':float(np.max(abs(exact-second))),
            'retained_max_abs_remainder_microK':float(np.max(abs((operator@(exact-second)[support])[4:])) )})
    j=np.column_stack((np.eye(3),np.eye(3)))
    endpoint=nuisance_projected_rank(j,None,c)
    free_intrinsic=nuisance_projected_rank(j,np.eye(3),c)
    payload=lambda a:{**a.as_payload(),'condition_number':None if not np.isfinite(a.condition_number) else a.condition_number,
                     'condition_status':'UNIDENTIFIED' if not a.full_rank else 'FINITE'}
    frequencies=np.array([100.,143.,217.,353.])*1e9
    x=6.62607015e-34*frequencies/(1.380649e-23*T_REF_K)
    qnu=(x/2)/np.tanh(x/2)
    result={'tasks':['RB05','RB06','RB08_ENDPOINT_ONLY','RB09_ENDPOINT_ONLY'],
        'owner':'HTT','claim_tier':'CONDITIONAL_SOURCE_ERROR_PROXY_AND_RESPONSE_DIAGNOSTIC',
        'source_urls':list(SOURCES),'dipole_errors_microK':{'stat':.09,'syst':.45,'calibration':.45},
        'covariance_model':'diagonal Gaussian proxy using linear-sum published errors; correlations unavailable; not official likelihood',
        'beta_xyz':beta.tolist(),'covariance_beta':c.tolist(),'kinematic_speed_km_s':speed,
        'conditional_speed_sigma_km_s':sigmaspeed,'kinematic_model':'intrinsic/late/foreground dipole explicitly fixed to zero in this declared branch',
        'T0_reference_K':T_REF_K,'T0_sigma_K':.00057,
        'T0_handling':'orbital calibration amplitude scales with T0; dimensionless ratio cancels shared factor',
        'nominal_to_best_dipole_microK':difference.tolist(),
        'removed_template_status':'reference difference only, not residual map measurement; map quadrupole correction not applied',
        'kinematic_Q_microK':qkin.tolist(),'kinematic_C2_microK2':float(8*np.pi/75*np.sum(qkin*qkin)),
        'frequency_GHz':(frequencies/1e9).tolist(),'central_frequency_Qnu':qnu.tolist(),
        'frequency_scope':'single-frequency examples; actual bandpass and component weights not supplied',
        'finite_difference':checks,'finite_remainder_grid':remainder,'endpoint_rank':payload(endpoint),
        'free_intrinsic_dipole_rank':payload(free_intrinsic),
        'boost_source_model':'T0 plus processed observed-Q polynomial surrogate; no restored physical sky; cache-stage NSIDE64 mask/OLS only',
        'global_transfer':'HOLD background/matter/congruence/epoch/boundary/tilt-history/provider absent',
        'physical_local_global_inference':'HOLD CF4 selected law and sourced global transfer absent',
        'fit':fit,'science_status':'CONDITIONAL; no shear/vorticity/family inference'}
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    np.savez(out/'processed_boost_response.npz',full_response=projected,kinematic_Q=qkin,
        dipole_beta=beta,dipole_covariance=c,local_global_jacobian=j)
    render(result,out)
    (out/'report.md').write_text(f'''# G02: 물리 solar dipole와 endpoint response

Planck III/I의 source-bound dipole에 선형합 오차의 대각 Gaussian proxy를 명시적으로 적용하면, 순수 kinematic branch의 속도는 {speed:.6f} ± {sigmaspeed:.6f} km/s다. source systematic/calibration errors를 확률 law로 해석하는 추가 전제이며 공식 likelihood나 완전 공분산이 아니다. intrinsic/late/foreground dipole은 이 branch에서 명시적으로0으로 고정했다. 일반 branch는 누락 성분을 공급해야 한다.

orbital dipole의 T0 보정과 분모는 같은 nuisance다. 무차원 dipole에서 T0가 상쇄되고, physical-K amplitude에는 한 번 남는다. nominal removed template과 best reference의 차이는 {np.linalg.norm(difference):.6f} microK며 관측 residual ell1이 아니다. true-temperature derived kinematic C2={result['kinematic_C2_microK2']:.6f} microK², 실제 SMICA에 correction을 적용하지 않았다. 강도 지도 second-order Qnu는 bandpass/weight 없이는 component correction으로 사용할 수 없다.

같은 NSIDE64 cache-stage mask/OLS에 exact Lorentz pullback와 기존 analytic quadrupole boost를 통과시켜 finite differences/remainder를 계산했다. 그 source는 처리된 fitted-Q를 이용한 positive polynomial surrogate다. upstream raw downgrade/beam/compsep와 physical global history는 검증하지 않는다. finite remainder grid는 전역 certified bound가 아니다.

dipole-only local/global endpoint [I,I]는6모수에서 rank3이며 nullspace(h,-h)가 남는다. unconstrained intrinsic dipole nuisance를 사영하면 rank0이다. 작은 physical covariance를 거부하던 unit-dependent threshold와 rectangular rank deficiency에서 condition1을 표시하던 helper 결함은 회귀검사를 통해 수정했다. 물리 global transfer와 CF4 selected law가 없어서 actual local/global 공동 적합은 HOLD다.

![dipole와 endpoint 응답](dipole_response.png)

source constants·units·frame·covariance proxy·response·finite steps는 result.json에, 실제 code/input/시간은 execution_receipt.json에 있다. [Planck III]({SOURCES[0]}), [Planck I]({SOURCES[1]}), [Fixsen]({SOURCES[2]}), [boost convention](https://arxiv.org/pdf/1403.6117).
''')
    receipt={'code_sha256':file_sha256(__file__),'dipole_module_sha256':file_sha256(ROOT/'htt/htt/htt/infer/physical_dipole.py'),
        'tensor_source_sha256':file_sha256(tensor_source),'elapsed_seconds':time.perf_counter()-start,
        'requested_parent':'gpt-6.1-sol/high','physics_requested':'gpt-6-astra/xhigh','observed':'UNKNOWN',
        'command':'/usr/bin/python -B scripts/run_reboot_physical_dipole.py --output-dir '+str(out),
        'environment':'PYTHONPATH=htt:htt/htt:htt/src; OPENBLAS_NUM_THREADS=1; OMP_NUM_THREADS=1'}
    (out/'execution_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'speed_km_s':speed,'rank':endpoint.projected_rank,'free_intrinsic_rank':free_intrinsic.projected_rank}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--render-only',action='store_true')
    a=p.parse_args()
    if a.render_only:render(json.loads((a.output_dir/'result.json').read_text()),a.output_dir)
    else:run(a.output_dir)
