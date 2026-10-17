"""R8/C8 source-conditional contrast and numerical-stability analysis.

Loads precomputed and SHA-pinned Planck POL geometry coefficients. There is no
observed Q/U, astrophysical high-ell amplitude or Planck null likelihood.
The estimator domain is ell=6..8 real spin-2 coefficients and a fixed pair
of masks, with ell=2..5 real Q/U OLS outputs.
"""
from __future__ import annotations
import argparse
import json
import math
import time
from pathlib import Path
import numpy as np
from scipy import linalg
from l01_k_spectral_certificate import (
    audit_native_receipt, coefficient_complex_structure, digest_file,
    eb_indices, inspect_operator, verify_receipt,
)

EXPECTED_USER_NATIVE_SHA = '7b4763afe8e5d30a02be296b0d4f7281a30f4e80937975dcda5f929643c2a7b6'
EXPECTED_USER_DELTA_NORM = 0.43962877239085046
SOURCE_SCOPE = 'UNIT_ELL6TO8_REAL_EB_COEFFICIENT_NORM__NO_PHYSICAL_PRIOR'


def validate_reported_native_input(native_receipt: str | Path, spectral_receipt: str | Path):
    """Byte pins and the user-native R7/C7 certificate, not a new source lock."""
    native_receipt = Path(native_receipt)
    spectral_receipt = Path(spectral_receipt)
    if digest_file(native_receipt) != EXPECTED_USER_NATIVE_SHA:
        raise ValueError('USER_NATIVE_JSON_SHA_DRIFT')
    native_meta, pair = verify_receipt(native_receipt, enforce_reported_pins=True)
    summary = json.loads(spectral_receipt.read_text(encoding='utf-8'))
    if summary.get('schema') != 'htt.L01_real_native_K_spectral_audit/1':
        raise ValueError('SPECTRAL_RECEIPT_SCHEMA_MISMATCH')
    if summary.get('native_receipt_file_sha256') != EXPECTED_USER_NATIVE_SHA:
        raise ValueError('SPECTRAL_CERT_SOURCE_SHA_DRIFT')
    claimed = summary.get('common_vs_three_way',{}).get('spectral_norm_K_difference')
    if claimed is None or not math.isfinite(float(claimed)) or not np.isclose(
       float(claimed), EXPECTED_USER_DELTA_NORM, atol=2e-11, rtol=2e-10):
        raise ValueError('USER_NATIVE_DELTA_NORM_REPORT_MISMATCH')
    if summary.get('paper_submission') != 'NOT_READY_TO_SUBMIT':
        raise ValueError('INCOMPATIBLE_PHYSICAL_CLAIM_GATE')
    recomputed = audit_native_receipt(native_receipt)
    got = recomputed['common_vs_three_way']['spectral_norm_K_difference']
    if not np.isclose(got, EXPECTED_USER_DELTA_NORM, atol=2e-11, rtol=2e-10):
        raise ValueError('RAW_NPZ_DELTA_NORM_MISMATCH')
    if not np.isclose(got, float(claimed), atol=2e-11, rtol=2e-10):
        raise ValueError('SPECTRAL_RECEIPT_DELTA_NORM_MISMATCH')
    # Independent flags from actual output; absence is not a failure of geometry.
    all_m = summary.get('all_m_spin_check', 'NOT_RUN')
    if isinstance(all_m, dict) and all_m.get('status') != 'ALL_M_ELL2_TO8_SIGN_FRAME_MATCH':
        raise ValueError('ALL_M_NATIVE_CONVENTION_FAILURE')
    return pair, {
        'user_native_sha256':EXPECTED_USER_NATIVE_SHA,
        'user_spectral_receipt_sha256':digest_file(spectral_receipt),
        'all_m_native_spin': all_m.get('status') if isinstance(all_m,dict) else all_m,
        'actual_source_byte_pins':'VERIFIED_BY_EXISTING_R7_C7_CHECKS',
        'operator_source_sha':'REPORTED_USER_LOCAL_AND_RECOMPUTED_IN_NEW_LOCAL_RUN',
    }


def _timed_svd(A: np.ndarray, repeats:int=5) -> dict:
    if repeats<1 or repeats>100:
        raise ValueError('benchmark repeats must be 1..100')
    # No expensive simulations. Both algorithms solve the same finite spectral task.
    numpy_times, scipy_times = [], []
    for _ in range(repeats):
        tic=time.perf_counter()
        _=np.linalg.svd(A,compute_uv=False)
        numpy_times.append(time.perf_counter()-tic)
        tic=time.perf_counter()
        _=linalg.svdvals(A,check_finite=False)
        scipy_times.append(time.perf_counter()-tic)
    return {
        'numpy_svd_median_ms':float(np.median(numpy_times)*1000),
        'scipy_svdvals_median_ms':float(np.median(scipy_times)*1000),
        'repeats':repeats,
        'bench_note':'Local run only, tiny-matrix overhead-sensitive, not a speedup claim',
    }


def _signed_structure(K:np.ndarray):
    le,lb=eb_indices((2,3,4,5));he,hb=eb_indices((6,7,8))
    A=K[np.ix_(le,he)]
    B=K[np.ix_(le,hb)]
    return A-1j*B, K[np.ix_(lb,he)], (le,lb,he,hb)


def contrast_certificate(K_common:np.ndarray, K_triple:np.ndarray,
                         *, numerical_error_upper:float|None=None,
                         benchmark_repeats:int=5) -> dict:
    """Sharp same-source two-mask contrast under a *hypothetical* coefficient ball.

    All theoretical norm bounds are exact in finite dimension; numeric values
    are estimates from double precision SVD. ``numerical_error_upper`` denotes
    an externally justified bound on ||E||_2 for the *difference matrix*, not
    a tolerance automatically invented from machine epsilon.
    """
    c=np.asarray(K_common,float);t=np.asarray(K_triple,float)
    for v in (c,t):
        if v.shape!=(64,90) or not np.all(np.isfinite(v)):
            raise ValueError('FINITE_REAL_64_BY_90_OPERATOR_REQUIRED')
        inspect_operator(v)
    if numerical_error_upper is not None and (
        not math.isfinite(numerical_error_upper) or numerical_error_upper<0):
        raise ValueError('EXTERNAL_OPERATOR_ERROR_MUST_BE_NONNEGATIVE_FINITE')
    d=t-c
    dmeta=inspect_operator(d)
    s_numpy=np.linalg.svd(d,compute_uv=False)
    U,s,Vh=np.linalg.svd(d,full_matrices=False)
    s_scipy=linalg.svdvals(d,check_finite=False)
    comp,BE,(le,lb,he,hb)=_signed_structure(d)
    complex_s=linalg.svdvals(comp,check_finite=False)
    BE_s=linalg.svdvals(BE,check_finite=False)
    largest=float(s[0]);smallest=float(s[-1]);blockmax=float(BE_s[0])
    # Saturating real singular vector, where direction is unimportant.
    witness=Vh[0].copy();witness/=np.linalg.norm(witness)
    sharp_resid=abs(np.linalg.norm(d@witness)-largest)
    # Unit vector in low-B output, chosen before any source prior.
    v=np.zeros(64);v[lb[0]]=1
    width=float(np.linalg.norm(d.T@v))
    h=d.T@v / width if width>0 else np.zeros(90)
    projection_residual=abs(float(v @ d @ h)-width) if width>0 else 0.
    # E-only nuisance can affect low-B via 32x45 real block.
    right_E=np.linalg.svd(BE, full_matrices=False)[2][0]
    E_inj=np.zeros(90);E_inj[he]=right_E
    sharp_E_resid=abs(np.linalg.norm((d@E_inj)[lb])-blockmax)
    norm_common=float(np.linalg.norm(c,2));norm_triple=float(np.linalg.norm(t,2))
    pairing=float(np.max(abs(s[0::2]-s[1::2])))
    sv_backend_diff=float(np.max(abs(s_numpy-s_scipy)))
    if pairing>1e-9*max(1.,largest):raise ArithmeticError('DELTA_SVD_DOUBLET_FAILURE')
    if sv_backend_diff>1e-9*max(1.,largest):raise ArithmeticError('NUMPY_SCIPY_SVD_DISAGREEMENT')
    if sharp_resid>5e-11*max(1.,largest) or sharp_E_resid>5e-11*max(1.,blockmax):
        raise ArithmeticError('SINGULAR_WITNESS_FAILED')
    rank_delta=int(np.count_nonzero(s>max(d.shape)*np.finfo(float).eps*largest))
    rank_BE=int(np.count_nonzero(BE_s>max(BE.shape)*np.finfo(float).eps*blockmax))
    error_rank={
        'operator_error_upper':numerical_error_upper,
        'status':'NOT_CERTIFIED_NO_EXTERNAL_OPERATOR_ERROR_BOUND',
        'full_row_rank_stable':None,
        'singular_value_lower':None,
        'singular_value_upper':None,
    }
    if numerical_error_upper is not None:
        eps=float(numerical_error_upper)
        error_rank={
            'operator_error_upper':eps,
            'status':'CONDITIONAL_ON_SUPPLIED_OPERATOR_ERROR_BOUND',
            'full_row_rank_stable':bool(smallest>eps),
            'singular_value_lower':[float(max(0.,x-eps)) for x in s],
            'singular_value_upper':[float(x+eps) for x in s],
            'weyl_rank_note':'Rank stability proven only if smallest singular > justified ||E|| upper',
        }
    return {
        'schema':'htt.L01_two_mask_R8_C8_spectral_stability/1',
        'domain':SOURCE_SCOPE,
        'shape':[64,90],
        'source':'same ell6..8 high real E/B coefficients for both masks',
        'delta_orientation':'K_triple - K_common',
        'norm_common':norm_common,
        'norm_triple':norm_triple,
        'norm_delta':largest,
        'relative_delta_to_common':float(largest/norm_common) if norm_common>0 else None,
        'relative_delta_to_triple':float(largest/norm_triple) if norm_triple>0 else None,
        'norm_only_difference_lower':abs(norm_triple-norm_common),
        'norm_only_difference_information_fraction':float(abs(norm_triple-norm_common)/largest) if largest>0 else None,
        'sharp_unit_joint_high_response_contrast':largest,
        'sharp_unit_high_E_to_low_B_difference':blockmax,
        'numerical_rank_delta':rank_delta,
        'numerical_rank_delta_B_from_E':rank_BE,
        'minimum_singular_delta':smallest,
        'singular_values':s.tolist(),
        'singular_values_complex_32':complex_s.tolist(),
        'singular_values_BE_32':BE_s.tolist(),
        'complex_structure_relative_residual':dmeta['complex_structure_relative_residual'],
        'paired_singular_max_abs_residual':pairing,
        'numpy_scipy_singular_max_abs_difference':sv_backend_diff,
        'svd_backend_independence':'NUMPY_SCIPY_MAY_SHARE_LAPACK; AGREEMENT_ONLY_NOT_INDEPENDENT_PROOF',
        'complex_reduction_max_abs_difference':float(np.max(abs(s[0::2]-complex_s))),
        'sharp_real_witness_residual':float(sharp_resid),
        'sharp_high_E_to_B_witness_residual':float(sharp_E_resid),
        'first_low_B_unit_contrast_maximum':width,
        'first_low_B_contrast_witness_residual':float(projection_residual),
        'weyl_perturbation_certificate':error_rank,
        'performance_local':{
            'real_64x90':_timed_svd(d,benchmark_repeats),
            'complex_32x45':_timed_svd(comp,benchmark_repeats),
        },
        'physical_tail_ell_greater_8':'UNBOUNDED_IN_THIS_MODEL_UNLESS_EXTERNAL_TAIL_CONSTRAINT_SUPPLIED',
        'beam_noise_foreground_FFP_null':'NOT_EVALUATED',
        'paper_gate':'NOT_READY_TO_SUBMIT',
    }


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-receipt',required=True)
    ap.add_argument('--spectral-receipt',required=True)
    ap.add_argument('--out',required=True)
    ap.add_argument('--operator-error-upper',type=float,default=None,
        help='Only use a separately justified numerical/operator error upper for delta K')
    ap.add_argument('--benchmark-repeats',type=int,default=5)
    args=ap.parse_args(argv)
    pair,evidence=validate_reported_native_input(args.native_receipt,args.spectral_receipt)
    output=contrast_certificate(pair['common'],pair['three_way_intersection'],
                numerical_error_upper=args.operator_error_upper,
                benchmark_repeats=args.benchmark_repeats)
    output['provenance']=evidence
    output['input_native_receipt_sha256']=digest_file(args.native_receipt)
    output['input_spectral_receipt_sha256']=digest_file(args.spectral_receipt)
    outfile=Path(args.out)
    outfile.parent.mkdir(parents=True,exist_ok=True)
    outfile.write_text(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({
        'status':'PASS_FINITE_TWO_MASK_NUMERICAL_CONTRAST',
        'input_native_receipt_sha256':output['input_native_receipt_sha256'],
        'delta_norm':output['norm_delta'],
        'delta_E_high_to_B_low_norm':output['sharp_unit_high_E_to_low_B_difference'],
        'delta_rank_numeric':output['numerical_rank_delta'],
        'physical_tail':output['physical_tail_ell_greater_8'],
        'output':str(outfile),
    },indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
