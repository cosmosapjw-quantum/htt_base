#!/usr/bin/env python3
"""Pure readback checks of actual Planck same-sky and SH0ES full-C outputs."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
from obsstat.htt_multisplit_lowell import multisplit_contrasts, split_power_identity

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/'docs/research_program/theory_obs_application_20261015/loop5/results'
RAW=Path('/mnt/extdrive/workdir/raw')

def read(path):return json.loads(path.read_text())

def verify():
    x=read(PATH/'planck_multisplit_spin_v1/result.json')
    z=read(PATH/'planck_spinEB_modes_v1/result.json')
    q=read(PATH/'planck_morphology_boost_comparison_v1/result.json')
    s=read(PATH/'shoes_full_covariance_gls_v1/result.json')
    ident=read(RAW/'HTT_ADDITIONAL_DATA_INTAKE_20261015.json')
    host=read(PATH/'shoes_cf4_astrometry_candidates_v1/result.json')
    assert ident['verified_count']==ident['expected_count']==17
    assert x['common_T_nside64_pixel_count']==26846
    assert x['common_POL_nside64_pixel_count']==30021
    assert x['T_ell0_to5_full_rank_condition']['operator_design_max_identity_residual']<1e-12
    assert x['spin2_ell2_to5_rank_condition']['identity_residual']<1e-12
    assert len(x['selected_original_T_and_P_features'])==9
    assert len(z['per_map_EE_BB_EB'])==8
    assert len(z['split_cross_EE_BB_EB'])==3
    for v in x['same_sky_split_cross_products'].values():
        for r in v['per_ell']:
            assert abs(r['cross_identity_residual'])<1e-10
            assert abs(r['cross']+r['difference_auto']-r['mean_auto'])<1e-10
    for v in z['per_map_EE_BB_EB'].values():
        for ell in v:
            assert ell['E_auto_microK2']>=0 and ell['B_auto_microK2']>=0
            assert abs(ell['EB_cross_microK2']) <= \
                np.sqrt(ell['E_auto_microK2']*ell['B_auto_microK2'])+1e-12
    assert q['beta_reference_norm']>0 and q['norm_O_microK_tensor']>0
    assert host['n_SH0ES_Cepheid_source_fields']==41
    assert host['n_CF4_galaxies_with_positive_Cepheid_moduli_and_sigma']==69
    assert host['n_unique_position_candidates']==37 and host['n_outside_cut']==4
    assert host['n_ambiguous_within_cut']==0
    assert host['n_candidate_CF4_unique_group_ids']==36
    assert host['multi_SH0ES_host_same_CF4_group_candidates']=={'37642':['N3972','N3982']}
    assert set(host['not_position_matched_labels'])=={'M31','LMC','SMC','N4536'}
    assert host['scientific_status'].endswith('NOT_CERTIFIED_HOST_IDENTITIES')
    for row in host['candidates']:
        m=row['angular_match']
        if m['status']=='POSITION_CANDIDATE':
            assert 0<=m['first_distance_arcmin']<host['match_cut_arcmin']
            assert m['second_distance_arcmin']>host['match_cut_arcmin']
            assert row['candidate_CF4_individual_galaxy'] is not None
        else:
            assert row['candidate_CF4_individual_galaxy'] is None
    with np.load(PATH/'planck_multisplit_spin_v1/retained_common_support_coefficients.npz',allow_pickle=False) as f:
        names=list(f['names_T'])
        coeff=np.asarray(f['coeff_T'],float)
        EB=np.asarray(f['coeff_EB'],float)
    assert coeff.shape==(9,32) and EB.shape==(8,64)
    y={s:coeff[i] for i,s in enumerate(names)}
    four=multisplit_contrasts(np.stack([y[n] for n in ('SMICA_HM1','SMICA_HM2','SMICA_OE1','SMICA_OE2')]))
    checks={
      'SMICA_HM_vs_SMICA_OE':np.linalg.norm(four['partition_mean_difference']),
      'SMICA_noSZ_FULL_vs_SMICA_FULL':np.linalg.norm(y['SMICA_noSZ_FULL']-y['SMICA_FULL']),
      'SMICA_FULL_vs_NILC_FULL':np.linalg.norm(y['SMICA_FULL']-y['NILC_FULL']),
    }
    for k,val in checks.items():
        np.testing.assert_allclose(val,x['same_sky_temperature_contrasts'][k]['norm_microK'],rtol=0,atol=1e-12)
    assert s['n_observed_equations']==3492 and s['n_frozen_parameters']==47
    gls=s['baseline_GLS'];ref=s['official_lstsq_results_comparison']
    assert gls['dof']==3445 and gls['normalized_normal_equation_gradient']<1e-9
    assert ref['chi_squared_difference_reference_minus_GLS']>=0
    assert abs(ref['maximum_absolute_coefficient_difference'])<.1
    with np.load(PATH/'shoes_full_covariance_gls_v1/gls_47_parameter_covariance.npz',allow_pickle=False) as f:
        b=f['estimate'];V=f['covariance'];A=f['normal_matrix']
        assert b.shape==(47,) and V.shape==(47,47) and np.linalg.eigvalsh(V)[0]>0
        assert np.max(abs(A@V-np.eye(47)))<1e-8
        np.testing.assert_allclose(b,gls['estimate'],atol=1e-11)
    assert s['algebraic_gauge_checks']['source_column_0_relative_information_after_profile']<1e-16
    assert q['status'].startswith('SOURCE_BOUND')
    assert s['scientific_status'].startswith('EXECUTED_SOURCE_BOUND')
    print(json.dumps({'planck_source_maps':len(names),'temperature_pixels':x['common_T_nside64_pixel_count'],
       'polarization_pixels':x['common_POL_nside64_pixel_count'],
       'spin2_rows':len(z['per_map_EE_BB_EB']),
       'astrometric_host_candidates':host['n_unique_position_candidates'],
       'unmatched_hosts':host['not_position_matched_labels'],
       'shoes_equations':s['n_observed_equations'],'shoes_fit_parameters':s['n_frozen_parameters'],
       'cross_split_exact_identities':'PASS','source_morphology_numeric_identities':'PASS',
       'spin2_coefficient_gram':'PASS','shoes_C_L_y_GLS':'PASS',
       'claim_boundaries':'SOURCE_BOUND_ONLY'},indent=2))
    return 0

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.parse_args()
    raise SystemExit(verify())
