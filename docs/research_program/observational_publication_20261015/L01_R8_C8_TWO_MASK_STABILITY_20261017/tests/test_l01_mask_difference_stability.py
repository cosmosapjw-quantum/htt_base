import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from l01_mask_difference_stability import contrast_certificate, validate_reported_native_input
from l01_k_spectral_certificate import audit_native_receipt,digest_file
from test_l01_k_certificate import fake_complex_operator, make_receipt


def test_real_and_complex_delta_agree_and_doublet():
    c=fake_complex_operator()
    t=fake_complex_operator(seed=123)
    a=contrast_certificate(c,t,benchmark_repeats=1)
    assert a['norm_delta']>0
    assert a['paired_singular_max_abs_residual']<1e-12
    assert a['numpy_scipy_singular_max_abs_difference']<1e-12
    assert a['complex_reduction_max_abs_difference']<1e-12
    assert a['sharp_real_witness_residual']<1e-12
    assert a['sharp_high_E_to_B_witness_residual']<1e-12
    assert a['first_low_B_contrast_witness_residual']<1e-12
    assert a['physical_tail_ell_greater_8'].startswith('UNBOUNDED')


def test_equal_mask_zero_difference_and_no_divzero():
    c=fake_complex_operator()
    r=contrast_certificate(c,c,benchmark_repeats=1)
    assert r['norm_delta']==0
    assert r['sharp_unit_high_E_to_low_B_difference']==0
    assert r['first_low_B_unit_contrast_maximum']==0
    assert r['weyl_perturbation_certificate']['status'].startswith('NOT_CERTIFIED')


def test_doubled_singular_weyl_stable_rank_and_failure():
    c=np.zeros((64,90));t=fake_complex_operator()
    s=np.linalg.svd(t,compute_uv=False)
    r=contrast_certificate(c,t,numerical_error_upper=float(s[-1]*.5),benchmark_repeats=1)
    assert r['weyl_perturbation_certificate']['full_row_rank_stable']
    r=contrast_certificate(c,t,numerical_error_upper=float(s[-1]*2),benchmark_repeats=1)
    assert not r['weyl_perturbation_certificate']['full_row_rank_stable']
    assert min(r['weyl_perturbation_certificate']['singular_value_lower'])==0


@pytest.mark.parametrize('bad', [-1., float('nan'),float('inf')])
def test_reject_inadmissible_uncertainty(bad):
    with pytest.raises(ValueError):contrast_certificate(fake_complex_operator(),fake_complex_operator(seed=5), numerical_error_upper=bad,benchmark_repeats=1)


def test_reject_inconsistent_basis():
    c=fake_complex_operator();t=c.copy();t[4,18]+=.09
    with pytest.raises(ValueError,match='E_B_COMPLEX_STRUCTURE_BROKEN'):
        contrast_certificate(c,t,benchmark_repeats=1)


def test_no_unpinned_false_admission(tmp_path):
    native=make_receipt(tmp_path)
    spectral=tmp_path/'spectral.json'
    spectral.write_text(json.dumps({'schema':'htt.L01_real_native_K_spectral_audit/1',
                                    'native_receipt_file_sha256':digest_file(native),
                                    'common_vs_three_way':{'spectral_norm_K_difference':.43962877239085046},
                                    'paper_submission':'NOT_READY_TO_SUBMIT'}))
    with pytest.raises(ValueError, match='USER_NATIVE_JSON_SHA_DRIFT'):
        validate_reported_native_input(native,spectral)


def test_nonfinite_and_badshape():
    with pytest.raises(ValueError):contrast_certificate(np.zeros((64,90)),np.full((64,90),np.nan),benchmark_repeats=1)
    with pytest.raises(ValueError):contrast_certificate(np.zeros((64,90)),np.ones((64,89)),benchmark_repeats=1)


def test_zero_rank_not_falsely_certified():
    z=np.zeros((64,90));r=contrast_certificate(z,z,numerical_error_upper=0,benchmark_repeats=1)
    assert not r['weyl_perturbation_certificate']['full_row_rank_stable']
    assert r['numerical_rank_delta']==0


def test_two_real_spin2_mask_geometries_sharp_difference():
    from healpix_ring_coords import pix2ang_ring
    from native_planck_pol_response import response_from_binary_mask
    n=8
    th,ph=pix2ang_ring(n)
    common=np.cos(th) > -.28
    triple=common & (np.cos(ph) > -.83)
    assert triple.sum()<common.sum()
    c,_=response_from_binary_mask(common,n)
    t,_=response_from_binary_mask(triple,n)
    out=contrast_certificate(c,t,benchmark_repeats=1)
    assert out['norm_delta'] > out['norm_only_difference_lower']
    assert out['complex_structure_relative_residual']<3e-12
    assert out['sharp_real_witness_residual']<1e-11
    assert out['sharp_high_E_to_B_witness_residual']<1e-11
    assert out['paired_singular_max_abs_residual']<1e-11
