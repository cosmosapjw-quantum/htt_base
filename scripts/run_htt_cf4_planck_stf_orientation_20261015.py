#!/usr/bin/env python3
"""Compare two observed same-frame STF2 morphology *proxies*, not cosmic shear.

CF4 group angular Hubble modulus tracer is source conditional in ICRS;
Planck Q is in Galactic.  The rotated tensor contraction is a valid
coordinate-invariant descriptor, not a physical-template/Bianchi posterior.
"""
from __future__ import annotations
import argparse,json,resource,time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from obsstat.cf4_cmb_stf_frame_and_orientation import (
  icrs_to_galactic_rotation,stf_tensor_cosine,stf_principal_axis_separation)
from obsstat.cf4_apparent_kinematic_distribution import (
  model_matrix,weighted_lsq,stf2_orthonormal)
from obsstat.reboot_tensor_features import tensors_from_real

ROOT=Path(__file__).resolve().parents[1]
B=ROOT/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results'
P=ROOT/'docs/research_program/theory_obs_application_20261015/loop5/results/planck_multisplit_spin_v1'


def run(out,nsamples=32000):
    if out.exists():raise ValueError('create-only source analysis')
    st=time.perf_counter()
    j=json.loads((B/'cf4_rawgroup_appHubble_STF2_pooled_methods_v2/result.json').read_text())
    measured=j['cases']['fiducial_slope_f015_v250_z01_10']
    with np.load(B/'cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz',allow_pickle=False) as f:
        z=np.asarray(f['z_CMB'],float);dirs=np.asarray(f['n_J2000'],float)
        mu=np.asarray(f['dmzp'],float);err_mu=np.asarray(f['e_dmzp'],float)
        mm=np.asarray(f['method_family']).astype('U32')
    if len(z)!=35970:raise ValueError('source selected group cohort changed')
    method=np.where(np.isin(mm,['CAL','SBF','MIXED_OTHER']),'OTHER',mm)
    M=model_matrix(z,dirs,method,include_method_slope=True)
    sigma=np.sqrt(err_mu**2+.15**2+(250*M['redshift_velocity_width_basis_mag_per_kms'])**2)
    fit=weighted_lsq(M['design'],mu-M['reference_mu_mag'],sigma)
    sel=M['slices']['shear'];bulk=M['slices']['bulk']
    np.testing.assert_allclose(fit['beta'][sel],
        measured['five_STF_apparent_shear_directional_H_fraction_coordinates'],rtol=1e-9,atol=1e-12)
    R=icrs_to_galactic_rotation()
    S=np.einsum('k,kij->ij',fit['beta'][sel],stf2_orthonormal())
    SG=R@S@R.T
    rng=np.random.default_rng(20261015)
    draws=rng.multivariate_normal(fit['beta'],fit['cov'],size=nsamples)
    cf4_stf=np.einsum('nk,kij->nij',draws[:,sel],stf2_orthonormal(),optimize=True)
    cf4_stf_G=np.einsum('ai,nij,bj->nab',R,cf4_stf,R,optimize=True)
    normS=np.linalg.norm(cf4_stf_G,axis=(1,2))
    result_maps={}
    with np.load(P/'retained_common_support_coefficients.npz',allow_pickle=False) as f:
        names=list(f['names_T']);coeff=np.asarray(f['coeff_T'],float)
    for name,vec in zip(names,coeff):
        Q,O=tensors_from_real(vec)
        p=float(stf_tensor_cosine(SG,Q))
        cos=np.einsum('nij,ij->n',cf4_stf_G,Q)/(normS*np.linalg.norm(Q))
        quant=np.quantile(cos,[.025,.16,.5,.84,.975])
        result_maps[name]={
           'same_frame_coordinate_invariant_tensor_cosine':p,
           'abs_tensor_cosine':abs(p),
           'dominant_positive_eigenaxis_acute_sep_deg':stf_principal_axis_separation(SG,Q),
           'formal_CF4_diagonal_gaussian_95pct_cos_quantiles':quant.tolist(),
           'fraction_of_conditional_draws_with_negative_STF_cosine':float(np.mean(cos<0))
        }
    cmb=json.loads((ROOT/'docs/observational_reboot_20261014/results/physical_dipole_v2/result.json').read_text())
    beta=np.asarray(cmb['beta_xyz'],float)
    bs=np.einsum('ij,nj->ni',R,draws[:,bulk])
    nor=np.linalg.norm(bs,axis=1)
    aligned=bs@beta/(nor*np.linalg.norm(beta))
    angles=np.rad2deg(np.arccos(np.clip(aligned,-1,1)))
    bmean=R@fit['beta'][bulk]
    mean_cos=float(bmean@beta/(np.linalg.norm(bmean)*np.linalg.norm(beta)))
    results={
     'schema':'htt.CF4_apparent_STF2_vs_Planck_Q_same_SKY_ICRS_GAL_orient/1',
     'status':'EXECUTED_ACTUAL_COORDINATE_ALIGNED_OBSERVABLE_MORPHOLOGY_NOT_BIANCHI_SHEAR',
     'frame':'CF4 Table3 J2000 ICRS to Planck SMICA/NILC Galactic using astropy validated SO3 transform',
     'ICRS_to_GAL_cartesian_matrix':R.tolist(),
     'orthogonality_residual':float(np.max(abs(R.T@R-np.eye(3)))),
     'source_parent_result':str(B/'cf4_rawgroup_appHubble_STF2_pooled_methods_v2/result.json'),
     'Planck_parent_source':str(P/'retained_common_support_coefficients.npz'),
     'survey_processed_same_sky':'nine Planck alternative algorithm maps are a single CMB sky, not independent comparisons',
     'CF4_real_kinematic_proxy_STF2_coeff_norm_H':float(np.linalg.norm(fit['beta'][sel])),
     'Planck_maps_Q_STF_tensor_results':result_maps,
     'bulk_velocity_group_WLS_internal_ICRS_to_GAL_vector_km_s':bmean.tolist(),
     'CMB_referred_kine_beta_vector_Galactic':beta.tolist(),
     'bulk_proxy_CMB_beta_vector_cosine':mean_cos,
     'bulk_proxy_CMB_beta_axis_angle_deg':float(np.rad2deg(np.arccos(np.clip(mean_cos,-1,1)))),
     'formal_CF4_conditional_bulk_CMB_angle_quantiles_deg':np.quantile(angles,[.025,.16,.5,.84,.975]).tolist(),
     'formal_CF4_conditional_bulk_CMB_cosine_quantiles':np.quantile(aligned,[.025,.16,.5,.84,.975]).tolist(),
     'n_joint_formal_draws':nsamples,
     'statistical_scope':'fixed design and CF4 diagonal sigma from method-pooled group data; Gaussian posterior source sensitivity not calibrated astrophysical null or physical frame/observer congruence posterior',
     'not':'no independent CMB kinematic shear, geometry-frame sigma/omega/a or matter tilt detection',
     'wall_seconds':time.perf_counter()-st,
     'peak_rss_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    }
    out.mkdir(parents=True)
    (out/'result.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    doc=['# CF4 apparent STF2 tensor와 Planck CMB Q tensor의 공통 Galactic frame 기하학적 비교',
      '','legacy geometry frame과 현재 source/model residual frame을 혼동하지 않는다.',
      'CF4 ICRS에서 Planck Galactic으로 SO(3) 회전 후 정규화된 STF2 내적과 conditional bulk alignment를 계산하였다.',
      'Planck map은 동일한 물리 하늘을 다른 방법으로 처리했으므로 독립 표본이 아니다.',
      '','| Planck product | STF2 cosine vs CF4 Hubble-pattern proxy | positive-max eigenaxis separation deg |',
      '|---|---:|---:|']
    for k,r in result_maps.items():
        doc.append(f"| {k} | {r['same_frame_coordinate_invariant_tensor_cosine']:.5g} | {r['dominant_positive_eigenaxis_acute_sep_deg']:.5g} |")
    doc+=['',f"CF4 conditional group-fit bulk vector vs published Planck dipole axis: {results['bulk_proxy_CMB_beta_axis_angle_deg']:.4g} degrees.",
    'This angular result is a fixed-source morphology descriptor. It is not a valid cosmic-axis p-value: survey window, shared calibration, cosmic variance, mask, observer/congruence and physical transfer remain unmodelled.',
    'The same-object CF4 bulk fit cannot be equated to WFH2009/Watkins2023 MV window amplitude or global homogeneous tilt.',
    ]
    (out/'REPORT_KO.md').write_text('\n'.join(doc)+'\n')
    fig,ax=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    # conditional one-sky sensitivity, not a null sigma
    Q=tensors_from_real(coeff[names.index('SMICA_FULL')])[0]
    stfc=np.einsum('nij,ij->n',cf4_stf_G,Q)/(normS*np.linalg.norm(Q))
    ax[0].hist(stfc,bins=72,density=True,histtype='step')
    ax[0].axvline(result_maps['SMICA_FULL']['same_frame_coordinate_invariant_tensor_cosine'],ls='--',color='k',lw=.9)
    ax[0].set(title='Same-frame tensor cosine',xlabel='CF4 apparent S : Planck SMICA Q (norm.)',ylabel='Formal conditional density')
    ax[1].hist(angles,bins=72,density=True,histtype='step')
    ax[1].axvline(results['bulk_proxy_CMB_beta_axis_angle_deg'],ls='--',color='k',lw=.9)
    ax[1].set(title='CF4 conditional bulk proxy vs CMB dipole',xlabel='Galactic-frame angle (degrees)')
    fig.savefig(out/'formal_joint_morphology_orientation_distributions.png',dpi=160)
    plt.close(fig)
    print(json.dumps({'SMICA_FULL_tensor_cosine':result_maps['SMICA_FULL']['same_frame_coordinate_invariant_tensor_cosine'],
      'NILC_FULL_tensor_cosine':result_maps['NILC_FULL']['same_frame_coordinate_invariant_tensor_cosine'],
      'CMB_bulk_conditional_angle_deg':results['bulk_proxy_CMB_beta_axis_angle_deg'],
      'formal_95pc_angle_deg':results['formal_CF4_conditional_bulk_CMB_angle_quantiles_deg'][[0,-1][0]] if False else results['formal_CF4_conditional_bulk_CMB_angle_quantiles_deg'],
      'seconds':results['wall_seconds']},indent=2))
    return results


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output-dir',required=True,type=Path)
    a=p.parse_args()
    run(a.output_dir)
