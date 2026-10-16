"""Actual-source bounded S02 and L01 readiness, not a physics posterior.

No synthetic/manufactured values are relabeled observed. Fails closed if source
identities or estimator types depart from the preserved upstream reports.
"""
import hashlib, json, zipfile
from pathlib import Path
import numpy as np
from publication_frame_kinematics import source_frame_packet, C_SI, radial_operator, antisymmetric_from_pseudovector
from build_ready_ledgers import sha256, canonical
ROOT=Path(__file__).resolve().parent
INPUT=ROOT.parent/'inputs'
P3_ZIP=Path('/mnt/data/htt_inputs_current/S2_SOURCE_CONDITIONAL_FINAL.zip')
P2_ZIP=Path('/mnt/data/htt_inputs_current/HTT_SIX_PAPER_P2_L01_FINITE_SOURCE_v1_20261016.zip')

def run():
    if sha256(P3_ZIP.read_bytes())!='303c78ff655237edf87db972ce882142837fac8588d269d6cd861c76346fb219':
        raise ValueError('P3 source checkpoint mismatch')
    if sha256(P2_ZIP.read_bytes())!='43cf6a29dea7cbece3e81f6367101db6c2e15b6f4f39b8e14f67baa888edbf0e':
        raise ValueError('P2 source checkpoint mismatch')
    with zipfile.ZipFile(P3_ZIP) as z:
        d=json.loads(z.read('htt_six_paper_h03/results/source_h03_v1/H03_SOURCE_TOMOGRAPHY.json'))
    if d['source_SHA256']!='86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c' or d['source_groups']!=35970:raise ValueError('actual source mismatch')
    windows=d['monopole_dipole_STF2_windows'];assert len(windows)==4
    h=[float(x['theta9'][0]) for x in windows]
    p3={
       'claim_kind':'ACTUAL_CF4_CONDITIONAL_WORKING_HUBBLE_ONLY',
       'source_sha256':d['source_SHA256'],'groups':35970,
       'window_centers':d['four_gaussian_window_centers'],
       'H_eff_working_km_s_Mpc':h,
       'joint_covariance36_PSD_min':float(np.linalg.eigvalsh(d['joint_covariance_36x36'])[0]),
       'source_method_selection_covariance_status':'UNKNOWN',
       'physical_x_C_defined_on_this_sample':False,
       'physical_x_C_not_defined_reason':'No one-congruence optical inverse map of working H0/STF2 to sigma,omega,curvature,tilt; no normalized HTT joint x_C posterior',
       'physical_Q_Pi_F_status':'INPUT_BLOCKED',
       'would_be_total_unknown_mass':1.0,
       'formal_outer_Pi_interval_only_if_physical_completion_exists':[0.,1.],
       'permission_to_calculate_physical_p_value':False,
       'S02_state':'pending',
    }
    with np.load(INPUT/'source/baseline_response_matrices.npz',allow_pickle=False) as z0, np.load(INPUT/'source/ell17_32_mask_response.npz',allow_pickle=False) as z1:
        kt=np.hstack([z0['K_ell2to5_32x253'],z1['K_ell2to5_32x800']]);
        singular=np.linalg.svd(kt,compute_uv=False)
    with np.load(INPUT/'source/retained_common_support_coefficients.npz',allow_pickle=False) as z:
        names=list(map(str,z['names_T']));namep=list(map(str,z['names_EB']))
    p2={
      'claim_kind':'ACTUAL_T_MASK_FINITE_L6_32_NOT_FULL_PHYSICAL_EB',
      'source_archive_sha256':sha256(P2_ZIP.read_bytes()),
      'real_temperature_mask_matrix_shape':list(kt.shape),
      'K_T_spectral_norm':float(singular[0]),
      'K_T_frobenius_norm':float(np.linalg.norm(kt)),
      'T_products':names,'EB_products':namep,
      'SMICA_noSZ_FULL_polarized_source':'ABSENT_NOT_ZERO',
      'independent_cosmic_sky_count':1,
      'native_P_sky_mask_spin2_ell6_8_response':'UNVERIFIED',
      'physical_beam_compsep_e2e':'UNVERIFIED',
      'L01_state':'pending',
    }
    if abs(p2['K_T_spectral_norm']-2.4328695605629203)>1e-11:raise ValueError('mask spectral norm wrong')
    return {'schema':'htt.real_source_S02_L01_conditional_readiness/1','P1_S02':p3,'P2_L01':p2,'publication_admission':False}

if __name__=='__main__':
    result=run()
    (ROOT/'S02_L01_SOURCE_READINESS.json').write_text(canonical(result))
    print(json.dumps({'H_eff_working_km_s_Mpc':result['P1_S02']['H_eff_working_km_s_Mpc'],'P3_min_eigen':result['P1_S02']['joint_covariance36_PSD_min'],'K_T_norm2':result['P2_L01']['K_T_spectral_norm'],'K_T_Frobenius':result['P2_L01']['K_T_frobenius_norm'],'S02_state':result['P1_S02']['S02_state'],'L01_state':result['P2_L01']['L01_state']},indent=2))
