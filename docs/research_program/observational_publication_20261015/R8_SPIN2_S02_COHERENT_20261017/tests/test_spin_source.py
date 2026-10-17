import sys
from pathlib import Path
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from healpix_ring_coords import pix2ang_ring
from r8_spin2_source_pilot import audit_source_mask
from native_planck_pol_response import choose_support,response_from_binary_mask,verify_native_files


def test_ring_reference_at_nside1():
    th,ph=pix2ang_ring(1)
    assert th.shape==(12,)
    assert np.allclose(np.cos(th)[:4],2/3)
    assert np.allclose(ph[:4],[np.pi/4,3*np.pi/4,5*np.pi/4,7*np.pi/4])
    assert np.allclose(np.cos(th)[-4:],-2/3)
    assert abs(np.mean(np.cos(th)))<1e-15


def test_ring_multiple_nsides():
    for n in (2,4,16,64):
        th,ph=pix2ang_ring(n)
        assert len(th)==12*n*n
        assert 0 <= th.min() <= th.max() <= np.pi
        assert 0 <= ph.min() and ph.max()<2*np.pi
        assert abs(np.sum(np.cos(th)))<5e-10
        assert np.allclose(np.cos(th[:4]),1-1/(3*n*n))
        assert np.allclose(np.cos(th[-4:]),-1+1/(3*n*n))


def test_ring_rejects_indices_and_bad_nside():
    for n in (0,3,-4):
        with pytest.raises(ValueError):pix2ang_ring(n)
    for ix in ([-1],[12],[0,12]):
        with pytest.raises(ValueError):pix2ang_ring(1,np.asarray(ix))


def test_r8_real_mask_source():
    result,k=audit_source_mask(ROOT/'source/r8_cmb_controls.npz')
    assert result['source_selected_pixels']==36433
    assert result['matrix_shape']==[64,90]
    assert np.isclose(result['response_operator_norm'],1.470709145964529,atol=2e-10)
    assert np.isclose(result['four_block_norms']['B_from_E'],.883765109051463,atol=2e-10)
    assert result['source']['official_PR3_POL_mask']=='NOT_PROVIDED'
    assert k.shape==(64,90)


def test_r8_exact_low_identity():
    result,_=audit_source_mask(ROOT/'source/r8_cmb_controls.npz')
    assert result['low_identity_residual']<1e-12
    assert result['low_condition']<2.25


def test_spin2_full_sky_low_high_small_mask():
    k,meta=response_from_binary_mask(np.ones(12*8*8,dtype=bool),8)
    # Equal-area HEALPix RING quadrature not mathematically exact but highly accurate.
    assert k.shape==(64,90)
    assert np.linalg.norm(k,2)<.05
    assert meta['low_identity_residual']<1e-12


def test_spin2_cut_sky_has_nonzero_leakage():
    n=8;p=np.arange(12*n*n);th,ph=pix2ang_ring(n)
    mask=np.cos(th)>-0.3
    k,meta=response_from_binary_mask(mask,n)
    assert np.linalg.norm(k,2)>.05
    assert meta['low_identity_residual']<1e-12


def test_choose_polarization_masks_intersection():
    d={'common':np.array([1.,1.,0.,.5]),'HM':np.array([1.,0.,1.,1.]),'OE':np.array([1.,1.,1.,1.])}
    out,count=choose_support(d,threshold=.5)
    assert count=={'common':2,'HM':3,'OE':4}
    assert np.array_equal(out['three_way_intersection'],[True,False,False,False])
    assert np.array_equal(out['common'],[True,True,False,False])


def test_choose_rejects_malformed_masks():
    d={'common':np.ones(3),'HM':np.ones(3),'OE':np.ones(2)}
    with pytest.raises(ValueError):choose_support(d)
    d['OE']=np.array([1.,2.,0.])
    with pytest.raises(ValueError):choose_support(d)
    with pytest.raises(ValueError):choose_support({'common':np.ones(3)})


def test_source_digest_rejects_tampered_npz(tmp_path):
    src=ROOT/'source/r8_cmb_controls.npz'
    q=tmp_path/'copy.npz';q.write_bytes(src.read_bytes()+b'x')
    with pytest.raises(ValueError):audit_source_mask(q)


def test_native_verifier_mock_accept_and_reject(tmp_path):
    p=tmp_path/'planck/PR3/masks';p.mkdir(parents=True)
    data=b'SIMPLE  ='+b' '*73 + b'payload'
    f=p/'example.fits';f.write_bytes(data)
    import hashlib
    names={'common':'example.fits'}
    hashes={'common':hashlib.sha256(data).hexdigest()}
    assert verify_native_files(tmp_path,names,hashes,len(data))['common']['source_size_bytes']==len(data)
    with pytest.raises(ValueError):verify_native_files(tmp_path,names,{'common':'0'*64},len(data))


def test_source_type_not_native_polarization():
    result,_=audit_source_mask(ROOT/'source/r8_cmb_controls.npz')
    assert 'TEMPERATURE_MASK' in result['response_status']
    assert result['physical_gate'].startswith('L01_PENDING')


def test_spin2_l2_m0_analytic_normalization():
    # Independent analytic harmonic: _2Y_20= sqrt(15/32pi)*sin(theta)^2.
    from spin2_finite import spin2_shell
    th=np.linspace(.1,3.,41);ph=np.linspace(.2,5.,41)
    a=spin2_shell(th,ph,2)
    expect=-np.sqrt(15/(32*np.pi))*np.sin(th)**2
    assert np.max(np.abs(a[:len(th),0]-expect))<4e-15
    assert np.max(np.abs(a[len(th):,0]))<4e-15
