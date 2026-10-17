import hashlib
import json
import sys
from pathlib import Path
import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'src'))
from l01_k_spectral_certificate import (
    inspect_operator, coefficient_complex_structure, eb_indices,
    verify_receipt, audit_native_receipt, SCHEMA, V2_INPUT_HASHES,
    PINNED_V2_MANIFEST_SHA, SUPPORTED_POLICY)


def fake_complex_operator(seed=42):
    rng=np.random.default_rng(seed)
    A=rng.normal(size=(32,45))*.08
    B=rng.normal(size=(32,45))*.03
    e_l,b_l=eb_indices((2,3,4,5))
    e_h,b_h=eb_indices((6,7,8))
    K=np.zeros((64,90))
    K[np.ix_(e_l,e_h)] = A
    K[np.ix_(e_l,b_h)] = B
    K[np.ix_(b_l,e_h)] = -B
    K[np.ix_(b_l,b_h)] = A
    return K


def make_receipt(tmp_path, K=None):
    if K is None:
        K=fake_complex_operator()
    result={
       'schema':SCHEMA,'component':'POLARIZATION PMASK',
       'source_nside':2048,'source_order':'NESTED',
       'effective_nside':64,'effective_order':'RING','threshold':.5,
       'support_policy':SUPPORTED_POLICY,
       'source_qualification':{
            'source_lock':'v2',
            'source_lock_v2_manifest_sha256':PINNED_V2_MANIFEST_SHA,
            'reference_qualification':{'OE':'REFERENCE_BYTE_IDENTICAL_TO_PINNED_SOURCE'}},
       'mask_native_sha256':V2_INPUT_HASHES,
       'independent_spin2_reference':{'status':'HEALPY_NATIVE_SIGN_FRAME_MATCH'},
    }
    for name,n in [('common',40000),('three_way_intersection',36000)]:
        path=tmp_path/(name+'.npz')
        kk=K if name=='common' else K*1.1
        np.savez_compressed(path,K_low2to5_high6to8=kk)
        result[name]={
          'selected_pixels':n,'shape':[64,90],
          'ring64_binary_mask_sha256':'a'*64,
          'norm':float(np.linalg.norm(kk,2)),
          'K_npz_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'output_npz':str(path)}
    receipt_path=tmp_path/'native.json'
    receipt_path.write_text(json.dumps(result)+'\n')
    return receipt_path


def test_intertwining_exact_structure():
    K=fake_complex_operator()
    jl=coefficient_complex_structure((2,3,4,5))
    jh=coefficient_complex_structure((6,7,8))
    assert np.linalg.norm(jl@jl+np.eye(64))==0
    assert np.linalg.norm(jh@jh+np.eye(90))==0
    assert np.linalg.norm(K@jh-jl@K)<1e-13
    out=inspect_operator(K)
    assert out['complex_structure_relative_residual']<2e-15
    assert out['block_pair_max_abs_residual']==0.
    assert out['singular_value_pair_max_abs_residual']<1e-13
    assert out['kernel_dimension']==26
    assert out['numerical_rank']==64
    assert out['norm_E_high_to_B_low']==pytest.approx(out['norm_B_high_to_E_low'])


def test_B_from_E_injection_sharp():
    K=fake_complex_operator()
    el,bl=eb_indices((2,3,4,5))
    eh,bh=eb_indices((6,7,8))
    be=K[np.ix_(bl,eh)]
    u,s,vt=np.linalg.svd(be,full_matrices=False)
    h=np.zeros(90)
    h[eh]=vt[0]
    assert np.linalg.norm(K[np.ix_(bl,np.arange(90))]@h)==pytest.approx(s[0],abs=1e-12)
    r=inspect_operator(K)
    assert r['sharp_one_unit_high_E_to_low_B_bound']==pytest.approx(s[0])


def test_fixed_contrast_source_optimizer_is_attainable():
    K=fake_complex_operator()
    _,bl=eb_indices((2,3,4,5))
    v=np.zeros(64);v[bl[0]]=1
    h=K.T@v
    r=np.linalg.norm(h)
    assert abs(v@K@(h/r)-r)<1e-14
    assert inspect_operator(K)['minimum_high_coefficient_norm_for_unit_first_B_contrast']==pytest.approx(1/r)


def test_reject_asymmetric_Q_U_or_frame_response():
    K=fake_complex_operator()
    K[2,6]+=.06
    with pytest.raises(ValueError,match='E_B_COMPLEX_STRUCTURE_BROKEN'):
        inspect_operator(K)


@pytest.mark.parametrize('mutation', [
    lambda k: np.full((64,90),np.nan),
    lambda k: np.zeros((64,89)),
    lambda k: np.zeros((64,90),dtype=complex)])
def test_fail_closed_bad_matrices(mutation):
    with pytest.raises(ValueError):inspect_operator(mutation(fake_complex_operator()))


def test_receipt_identity_and_sharp_delta(tmp_path):
    path=make_receipt(tmp_path)
    receipt,matrices=verify_receipt(path, enforce_reported_pins=False)
    assert len(matrices)==2
    v=audit_native_receipt(path, enforce_reported_pins=False)
    assert v['paper_submission']=='NOT_READY_TO_SUBMIT'
    assert v['common_vs_three_way']['removed_pixels']==4000
    assert v['common_vs_three_way']['spectral_norm_K_difference'] == pytest.approx(.1*np.linalg.norm(matrices['common'],2))
    assert v['common_vs_three_way']['reverse_triangle_lower_bound']<=v['common_vs_three_way']['spectral_norm_K_difference']+1e-12


def test_fail_closed_npz_hash_even_if_semantic_matrix_equal(tmp_path):
    path=make_receipt(tmp_path)
    obj=json.loads(path.read_text())
    src=Path(obj['common']['output_npz'])
    src.write_bytes(src.read_bytes()+b'Z')
    with pytest.raises(ValueError,match='NPZ_BYTE_IDENTITY_MISMATCH'):
        audit_native_receipt(path, enforce_reported_pins=False)


def test_fail_closed_nside_and_policy(tmp_path):
    path=make_receipt(tmp_path)
    obj=json.loads(path.read_text());obj['support_policy']='threshold_before_ud_grade'
    path.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match='NATIVE_RECEIPT_CONTRACT_MISMATCH'):
        audit_native_receipt(path, enforce_reported_pins=False)


def test_fail_closed_missing_reference_receipt(tmp_path):
    path=make_receipt(tmp_path)
    obj=json.loads(path.read_text());obj['source_qualification']['reference_qualification']['OE']='NOT_ADMITTED'
    path.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match='OE_REFERENCE_QUALIFICATION_MISSING'):
        audit_native_receipt(path, enforce_reported_pins=False)


def test_fail_closed_swapped_mask_labels(tmp_path):
    path=make_receipt(tmp_path)
    obj=json.loads(path.read_text())
    obj['common']['selected_pixels']=35000
    path.write_text(json.dumps(obj))
    with pytest.raises(ValueError,match='TRIPLE_INTERSECTION_CANNOT_EXCEED_COMMON'):
        audit_native_receipt(path, enforce_reported_pins=False)


def test_native_spin2_basis_intertwines_healpix_mask_without_healpy():
    from native_planck_pol_response import response_from_binary_mask
    from healpix_ring_coords import pix2ang_ring
    n=8
    th,ph=pix2ang_ring(n)
    mask=(np.cos(th)>-.33) & (np.sin(ph)>.1)
    K,meta=response_from_binary_mask(mask,n)
    assert meta['low_identity_residual']<1e-11
    r=inspect_operator(K)
    assert r['complex_structure_relative_residual']<3e-12
    assert r['norm_E_high_to_B_low']>1e-2


def test_spin2_full_injection_can_detect_missing_healpy():
    from l01_k_spectral_certificate import spin2_full_ell_healpy_check
    if __import__('importlib').util.find_spec('healpy') is None:
        with pytest.raises(ModuleNotFoundError):spin2_full_ell_healpy_check(nside=8)
    else:
        assert spin2_full_ell_healpy_check(nside=8)['status']=='ALL_M_ELL2_TO8_SIGN_FRAME_MATCH'


def test_user_reported_input_pins_are_separate_from_computed_npz(tmp_path):
    path=make_receipt(tmp_path)
    with pytest.raises(ValueError,match='USER_REPORTED_NATIVE_OUTPUT_PIN_MISMATCH'):
        audit_native_receipt(path)
