import numpy as np
import l01_smica_processed_bands as qu


def test_account_exact_low_mid_and_nonzero_tail():
    low=np.array([2.,-3.]);mid=np.array([-5./3,10./3]);tail=np.array([7./3,28./3])
    result=qu.account_projected_bands(low+mid+tail,low,mid,tail)
    assert isinstance(result,dict), 'Finite-band accounting has not been implemented'
    assert result['closure_relative']<1e-14
    assert np.allclose(result['tail_9_to_L_K_CMB'],tail)

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pytest
from healpix_ring_coords import pix2ang_ring
from spin2_finite import block_design, response_from_design


@pytest.mark.parametrize('scale',[1.,1e-6,1e-16])
def test_omitted_nonzero_tail_fails_at_every_unit_scale(scale):
    x=np.array([2.,3.])*scale
    with pytest.raises(ValueError,match='BAND_CLOSURE'):
        qu.account_projected_bands(x,x/2,np.zeros(2),np.zeros(2))


def test_zero_band_and_cancellation_roundoff():
    z=np.zeros(64)
    assert qu.account_projected_bands(z,z,z,z)['closure_relative']==0
    tiny=np.ones(64)*1e-25
    r=qu.account_projected_bands(tiny,z,z,z,reference_scale=1e-6)
    assert r['closure_relative']<1e-15


@pytest.mark.parametrize('bad',[np.array([np.nan]),np.array([1j]),np.ones((2,2))])
def test_malformed_band_is_not_admitted(bad):
    with pytest.raises(ValueError):qu.account_projected_bands(bad,bad,bad,bad)


def make_alms(lmax,seed=25):
    rng=np.random.default_rng(seed)
    a=(rng.normal(size=(2,(lmax+1)*(lmax+2)//2))+1j*rng.normal(size=(2,(lmax+1)*(lmax+2)//2)))*1e-6
    a[:,:lmax+1]=a[:,:lmax+1].real
    return a


def test_real_packing_cos_sin_has_orthonormal_factors():
    a=np.zeros((2,6),complex)  # lmax=2
    a[0,2]=3.;a[0,4]=2.-4.j;a[0,5]=-1.+7.j
    r=qu.packed_real(a,2,2,2)
    np.testing.assert_allclose(r[:5],[3,2*np.sqrt(2),4*np.sqrt(2),-np.sqrt(2),-7*np.sqrt(2)])
    np.testing.assert_equal(r[5:],0)
    assert np.dot(r,r)==pytest.approx(9+2*(4+16+1+49))


def test_filter_disjoint_complete_and_unchanged_input():
    a=make_alms(9);original=a.copy()
    low=qu.filter_alm(a,9,2,5);mid=qu.filter_alm(a,9,6,8);tail=qu.filter_alm(a,9,9,9)
    np.testing.assert_array_equal(low+mid+tail,qu.filter_alm(a,9,2,9))
    assert not np.any((low!=0)&(mid!=0))
    assert not np.any((tail!=0)&(mid!=0))
    np.testing.assert_array_equal(original,a)
    np.testing.assert_equal(qu.filter_alm(a,9,9,9,e_only=True)[1],0)


def test_complex_m0_and_nonfinite_rejected():
    a=make_alms(9);a[0,2]+=1j
    with pytest.raises(ValueError,match='M0_NOT_REAL'):qu.check_alms(a,9)
    a=make_alms(9);a[1,-1]=np.inf
    with pytest.raises(ValueError,match='NONFINITE'):qu.check_alms(a,9)


def test_fixed_window_zeros_outside_without_changing_source():
    w=np.array([True,False,False]);field=np.array([1e-6,np.nan,-1.6375e30])
    r=qu.masked_field(field,w)
    np.testing.assert_array_equal(r,[1e-6,0.,0.]);assert np.isnan(field[1])
    with pytest.raises(ValueError,match='INSIDE_FIXED'):qu.masked_field(field,np.ones(3,bool))
    with pytest.raises(ValueError,match='SHAPE'):qu.masked_field(field,w.astype(float))


def test_projector_matches_independent_lstsq_and_rejects_singular():
    rng=np.random.default_rng(6);low=rng.normal(size=(100,5));m=np.ones(50,bool);m[:4]=False
    p=qu.Projector.from_design(low,m);d=rng.normal(size=100)
    expected=np.linalg.lstsq(low[np.r_[m,m]],d[np.r_[m,m]],rcond=None)[0]
    np.testing.assert_allclose(p.apply(d),expected,atol=1e-14)
    with pytest.raises(ValueError,match='RANK_OR_CONDITION'):qu.Projector.from_design(np.ones((100,5)),m)
    with pytest.raises(ValueError,match='INSUFFICIENT_ROWS'):qu.Projector.from_design(low,np.zeros(50,bool))


class ReferenceSynthesis:
    """Tests the native-library boundary with the read, pinned Wigner source.

    Not a healpy implementation verification. Its separate optional test is below.
    """
    def __init__(self,nside=8,lmax=9):
        th,ph=pix2ang_ring(nside);self.design=block_design(th,ph,2,lmax)
    def alm2map_spin(self,a,nside,spin,lmax,mmax):
        assert spin==2 and mmax==lmax
        c=qu.packed_real(a,lmax,2,lmax)
        d=self.design@c
        return np.split(d,2)


@pytest.fixture(scope='module')
def geometry():
    th,ph=pix2ang_ring(8)
    low=block_design(th,ph,2,5);mid=block_design(th,ph,6,8)
    masks={'common':np.cos(th)>-.6,'three_way_intersection':(np.cos(th)>-.6)&(np.cos(ph)>-.8)}
    proj={k:qu.Projector.from_design(low,m) for k,m in masks.items()}
    mat={k:response_from_design(low,mid,m)[0] for k,m in masks.items()}
    return ReferenceSynthesis(),proj,mat


def test_three_band_synthetic_spin_projection_and_real_tail(geometry):
    hp,proj,k=geometry
    r=qu.analyze_alms(make_alms(9),9,hp,proj,k,nside=8)
    assert r['two_mask_difference']['closure_relative']<1e-10
    assert r['masks']['common']['mid_K_direct_relative']<1e-11
    assert r['masks']['common']['component_norms_K_CMB']['tail']>1e-8
    assert r['beam_applied_again'] is False and r['p_value'] is None
    assert r['tail_beyond_L']=='NOT_BOUNDED'


def test_pure_low_mode_does_not_fail_due_to_difference_cancellation(geometry):
    hp,proj,k=geometry;a=make_alms(9);a=qu.filter_alm(a,9,2,5)
    r=qu.analyze_alms(a,9,hp,proj,k,nside=8)
    assert r['two_mask_difference']['closure_relative']<1e-10
    assert r['masks']['common']['component_norms_K_CMB']['mid']==0


def test_changed_K_and_mid_sine_sign_are_detected(geometry):
    hp,proj,k=geometry;k={n:a.copy() for n,a in k.items()};k['common'][0,1]+=.1
    with pytest.raises(ValueError,match='STORED_K'):qu.analyze_alms(make_alms(9),9,hp,proj,k,nside=8)


def test_same_window_half_difference_commutes_with_analysis(geometry):
    hp,proj,k=geometry;a=make_alms(9);b=make_alms(9,seed=13)
    ra=qu.analyze_alms(a,9,hp,proj,k,nside=8)
    rb=qu.analyze_alms(b,9,hp,proj,k,nside=8)
    rd=qu.analyze_alms(qu.half_difference(a,b),9,hp,proj,k,nside=8)
    for m in k:
        expected=(np.array(ra['masks'][m]['total_K_CMB'])-rb['masks'][m]['total_K_CMB'])/2
        np.testing.assert_allclose(rd['masks'][m]['total_K_CMB'],expected,atol=2e-19,rtol=2e-12)


def test_checkpoint_reuse_contract_and_byte_mismatch(tmp_path):
    a=make_alms(9);contract={'lmax':9,'window':'same','source_sha':'fixture'}
    assert qu.load_checkpoint(tmp_path,'full',contract) is None
    qu.save_checkpoint(tmp_path,'full',a,{'p_value':None},contract)
    np.testing.assert_array_equal(qu.load_checkpoint(tmp_path,'full',contract),a)
    with pytest.raises(ValueError,match='IDENTITY'):qu.load_checkpoint(tmp_path,'full',dict(contract,window='different'))
    with pytest.raises(ValueError,match='ALREADY_EXISTS'):qu.save_checkpoint(tmp_path,'full',a,{},contract)
    p=tmp_path/'full.npz';p.write_bytes(p.read_bytes()+b'x')
    with pytest.raises(ValueError,match='IDENTITY'):qu.load_checkpoint(tmp_path,'full',contract)


def test_partial_checkpoint_does_not_become_success(tmp_path):
    (tmp_path/'full.npz').write_bytes(b'incomplete')
    with pytest.raises(ValueError,match='INCOMPLETE'):qu.load_checkpoint(tmp_path,'full',{'lmax':9})


def test_source_registry_uses_user_full_digest_and_split_allowlist(tmp_path):
    assert qu.SOURCE_SHA['full']=='60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac'
    assert len(qu.SOURCE_SHA)==5
    assert qu.source_path(tmp_path,'full').name=='COM_CMB_IQU-smica_2048_R3.00_full.fits'
    with pytest.raises(ValueError):qu.source_path(tmp_path,'../x')


def test_help_does_not_require_healpy_and_has_contract():
    p=subprocess.run([sys.executable,qu.__file__,'--help'],capture_output=True,text=True,timeout=20)
    assert p.returncode==0,p.stderr
    assert '--check-inputs-only' in p.stdout and '--lmax' in p.stdout


def test_real_healpy_boundary_optional():
    hp=pytest.importorskip('healpy')
    from l01_k_spectral_certificate import spin2_full_ell_healpy_check
    assert spin2_full_ell_healpy_check()['status']=='ALL_M_ELL2_TO8_SIGN_FRAME_MATCH'
    a=make_alms(9);packed=qu.packed_real(a,9,2,9)
    th,ph=pix2ang_ring(8);reference=block_design(th,ph,2,9)@packed
    native=np.concatenate(hp.alm2map_spin(a,8,spin=2,lmax=9))
    np.testing.assert_allclose(native,reference,atol=2e-15,rtol=1e-8)


def tiny_header(cards):
    text=''.join((f"{k:<8}= {repr(v) if isinstance(v,str) and v!='T' else v}").ljust(80) for k,v in cards.items())+'END'.ljust(80)
    data=text.encode('ascii');return data+b' '*(-len(data)%2880)


def tiny_split_file(path):
    h0=tiny_header({'SIMPLE':'T','BITPIX':32,'NAXIS':0,'EXTEND':'T'})
    h={'XTENSION':'BINTABLE','BITPIX':8,'NAXIS':2,'NAXIS1':12,'NAXIS2':12,'PCOUNT':0,'GCOUNT':1,'TFIELDS':3,
        'NSIDE':2048,'ORDERING':'NESTED','COORDSYS':'GALACTIC','POLCCONV':'COSMO','METHOD':'SMICA','PIXTYPE':'HEALPIX'}
    for i,name in enumerate(('I_STOKES','Q_STOKES','U_STOKES'),1):
        h[f'TTYPE{i}']=name;h[f'TFORM{i}']='1E';h[f'TUNIT{i}']='K_CMB'
    values=np.arange(36,dtype='>f4').reshape(12,3)*1e-6
    raw=values.astype('>f4').tobytes();path.write_bytes(h0+tiny_header(h)+raw+b'\0'*(-len(raw)%2880))
    return values


def test_native_memorymap_reads_QU_columns_and_zeros_shared_window(tmp_path):
    p=tmp_path/'test.fits';v=tiny_split_file(p);w=np.ones(12,bool);w[0]=False
    class NativeBoundary:
        seen=[]
        def reorder(self,x,n2r):
            assert n2r is True;self.seen.append(x.copy());return x.copy()
        def map2alm_spin(self,maps,spin,lmax,mmax):
            assert spin==2 and lmax==mmax==9
            np.testing.assert_array_equal(maps[0][1:],v[1:,1].astype(float))
            np.testing.assert_array_equal(maps[1][1:],v[1:,2].astype(float))
            assert maps[0][0]==maps[1][0]==0
            return np.zeros((2,55),complex)
    hp=NativeBoundary();got=qu.native_alms(p,'hm1',w,9,hp)
    assert got.shape==(2,55) and len(hp.seen)==2


def test_actual_structural_checker_and_input_sha_are_both_used(tmp_path,monkeypatch):
    import l01_smica_fits_integrity as fi
    p=qu.source_path(tmp_path,'hm1');p.parent.mkdir(parents=True);tiny_split_file(p)
    real=fi.inspect_smica_fits
    monkeypatch.setattr(fi,'inspect_smica_fits',lambda path,product:real(path,product,expected_npix=12))
    monkeypatch.setitem(qu.SOURCE_SHA,'hm1',qu.digest_file(p))
    receipt=qu.check_sources(tmp_path,['hm1'])
    assert receipt['hm1']['layout']['status']=='COMPLETE_DECLARED_HDU_STRUCTURE'
    with p.open('r+b') as f:f.seek(-1,2);f.write(b'X')
    with pytest.raises(ValueError,match='SOURCE_SHA_MISMATCH'):qu.check_sources(tmp_path,['hm1'])


def test_nonfinite_closure_scale_and_large_values_fail_closed():
    z=np.zeros(2)
    with pytest.raises(ValueError,match='REFERENCE_SCALE'):qu.account_projected_bands(z,z,z,z,reference_scale=float('nan'))
    x=np.ones(2)*1e300
    with np.errstate(over='ignore'):
        with pytest.raises(ValueError,match='OVERFLOW'):qu.account_projected_bands(x,x,z,z)
