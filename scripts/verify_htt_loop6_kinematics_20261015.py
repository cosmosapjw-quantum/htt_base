#!/usr/bin/env python3
"""Read back Loop6 actual numerical results with their source and physics boundaries.

Does not re-run a physical CMB/CF4 likelihood, and is not a model
verification of the observer/source congruence and selection functions.
"""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
from obsstat.cf4_apparent_kinematic_distribution import stf2_orthonormal
from obsstat.cf4_cmb_stf_frame_and_orientation import (
 icrs_to_galactic_rotation,stf_tensor_cosine)
from obsstat.reboot_tensor_features import tensors_from_real

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO/'docs/research_program/theory_obs_application_20261015/loop6_kinematics'
R=ROOT/'results'
P=REPO/'docs/research_program/theory_obs_application_20261015/loop5/results/planck_multisplit_spin_v1'


def read(path):return json.loads(path.read_text())

def run():
    before=read(R/'cf4_rawgroup_appHubble_STF2_v1/result.json')
    pool=read(R/'cf4_rawgroup_appHubble_STF2_pooled_methods_v2/result.json')
    legacy=read(R/'legacy_defect_actual_source_bridge_v1/result.json')
    same=read(R/'cf4_planck_STF_morphology_orient_v1/result.json')
    assert pool['n_release_groups']==before['n_release_groups']==38053
    assert pool['n_z01_10']==before['n_z01_10']==35970
    assert pool['selected_id_sha256']=='f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88'
    assert pool['source_table3_sha256']=='c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d'
    assert pool['source_table4_sha256']=='b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94'
    assert pool['method_pool_rare_CAL_SBF_MIXED_OTHER_into_OTHER'] is True
    assert before.get('method_pool_rare_CAL_SBF_MIXED_OTHER_into_OTHER',False) is False
    assert len(pool['cases'])==len(before['cases'])==9
    assert sum(j.get('STATUS')=='NEEDS_DIAGNOSIS' for j in before['fiducial_leave_one_healpix_nside1_region_out'])==2
    assert len(pool['fiducial_leave_one_healpix_nside1_region_out'])==12
    assert not any('STATUS' in x for x in pool['fiducial_leave_one_healpix_nside1_region_out'])
    c=pool['cases']['fiducial_slope_f015_v250_z01_10']
    b=before['cases']['fiducial_slope_f015_v250_z01_10']
    assert abs(c['norm_five_STF_apparent_shear_fraction']-b['norm_five_STF_apparent_shear_fraction'])<.0001
    assert abs(c['norm_five_STF_apparent_shear_fraction']-.03325774236166811)<1e-12
    assert c['claim'].endswith('ANGULAR_DISTANCE_RESIDUAL_ONLY')
    assert c['source_count']==35970
    v=np.asarray(c['five_STF_apparent_shear_directional_H_fraction_coordinates'])
    C=np.asarray(c['five_STF_conditional_covariance'])
    assert v.shape==(5,) and C.shape==(5,5) and np.linalg.eigvalsh(C)[0]>0
    assert abs(np.linalg.norm(v)**2/6-
      (c['apparent_shear_sqrt_sigma2overTheta2']**2)*1.5)<1e-14
    dd=c['formal_conditioned_distribution']
    assert np.all(np.diff(dd['quantiles_025_16_50_84_975_sigma_over_theta'])>0)
    with np.load(R/'cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz',allow_pickle=False) as n:
        ids=n['group_id']
        assert ids.shape==(35970,)
        assert hashlib.sha256(np.asarray(ids,dtype='<i8').tobytes()).hexdigest()==pool['selected_id_sha256']
        assert np.isfinite(n['n_J2000']).all()
        assert set(np.unique(n['method_family']))=={'FP','OTHER','SN','TF'}
    with np.load(R/'cf4_rawgroup_appHubble_STF2_pooled_methods_v2/conditional_fiducial_stf2_proxy_draws.npz',allow_pickle=False) as draws:
        sample=draws['five_stf_shear_proxy']
        assert sample.shape==(30000,5)
        quant=np.quantile(np.linalg.norm(sample,axis=1)/3,[.025,.16,.5,.84,.975])
        np.testing.assert_allclose(quant,dd['quantiles_025_16_50_84_975_sigma_over_theta'],atol=1e-14)

    assert legacy['uploaded_legacy_HTT_zip_sha256']=='3696f806b2639be1f9ea0fc17e96e89124a8ec5802e58dd7a31b710667e6d8c3'
    assert legacy['uploaded_legacy_main_FINAL_pdf_sha256']=='c1aefb6ab9d27b423a75274cb6887fe6cb494b7f21e1e2f750577b43c07e0942'
    assert len(legacy['source_scenario_pushforwards'])==81
    assert legacy['actual_shear_vorticity_acceleration_background_posterior']=='NOT_IDENTIFIED_BY_THE_USED_SOURCE_DATA'
    central=legacy['fiducial_2023_CF4_R200_scenario']
    assert abs(central['conditional_pushforward']['occupancy_quantiles'][2]-.095143617898398)<1e-12
    assert abs(central['conditional_pushforward']['x_quantiles'][2]-6.159884131006994e-7)<1e-16
    assert abs(legacy['naive_application_of_actual_CF4_angular_STF2_proxy_to_legacy_MES_ceiling']['ratio_025_16_50_84_975'][2]-30.070041451439955)<1e-10
    actual_source_names=set(legacy['actual_same_sky_planck_map_multipole_scalar_conventions'])
    assert len(actual_source_names)==9

    Rmat=icrs_to_galactic_rotation()
    np.testing.assert_allclose(Rmat,same['ICRS_to_GAL_cartesian_matrix'],atol=1e-12)
    assert np.linalg.det(Rmat)>0
    V=np.einsum('k,kij->ij',v,stf2_orthonormal())
    V=Rmat@V@Rmat.T
    with np.load(P/'retained_common_support_coefficients.npz',allow_pickle=False) as f:
        m=dict(zip(list(f['names_T']),f['coeff_T']))
        for k in ('SMICA_FULL','NILC_FULL','SMICA_noSZ_FULL'):
            q,_=tensors_from_real(m[k])
            val=stf_tensor_cosine(V,q)
            assert abs(val-same['Planck_maps_Q_STF_tensor_results'][k]['same_frame_coordinate_invariant_tensor_cosine'])<1e-12
    assert abs(same['bulk_proxy_CMB_beta_axis_angle_deg']-30.812880228100404)<1e-10
    assert 'NOT_BIANCHI_SHEAR' in same['status']

    result={
     'status':'PASS_RECORDED_SOURCE_BOUNDED_COMPUTATION_ONLY',
     'CF4_source_group_rows':pool['n_z01_10'],
     'CF4_6method_jackknife_failed':2,
     'CF4_4method_pooled_jackknife_passed':12,
     'formal_conditional_sigma_proxy_over_theta_median':
         dd['quantiles_025_16_50_84_975_sigma_over_theta'][2],
     'legacy_conditional_Q_Cf4_R200_median':
         central['conditional_pushforward']['occupancy_quantiles'][2],
     'legacy_scenario_count':len(legacy['source_scenario_pushforwards']),
     'geometry_frame_sigma_omega_accel_beta_posteriors':'NOT_MEASURED',
     'Planck_CF4_rotated_STF_tensors':'NUMERICAL_READBACK_VERIFIED'
    }
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=='__main__':
    run()
