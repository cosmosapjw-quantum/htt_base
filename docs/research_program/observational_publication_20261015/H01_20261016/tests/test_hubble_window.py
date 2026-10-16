import os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pytest
from hubble_window import (moments,distance_proxy_mpc,errors_proxy_km_s,radial_weights,
  dipole_bulk_principal_cosines,inject_response,cross_window_covariance,load_cf4,window_hubble,SOURCE_SHA)

def fake(N=300):
 rng=np.random.default_rng(12)
 n=rng.normal(size=(N,3));n/=np.linalg.norm(n,axis=1)[:,None]
 d=np.linspace(50,400,N)
 w=np.linspace(.1,1.0,N)
 return d,n,w

def test_distance_modulus_and_errors():
 assert distance_proxy_mpc(np.array([25.,30.])).tolist()==[1.,10.]
 assert np.isfinite(errors_proxy_km_s([100.],[.4])).all()
 with pytest.raises(ValueError):distance_proxy_mpc(np.array([float('nan')]))

def test_isotropic_exact_no_window_bias():
 d,n,w=fake();H=73.2;mono=np.zeros(3);Q=np.zeros((3,3))
 for a in [w,np.abs(n[:,2])*w,np.zeros_like(w)+.5]:
  direct,pred=inject_response(d,n,a,H,mono,mono,Q)
  assert abs(direct-H)<5e-13; assert abs(direct-pred)<5e-13

def test_dipole_bulk_stf_moment_exact():
 d,n,w=fake(); D=np.array([2.,-1.5,3.]);B=np.array([280.,-120.,75.]);Q=np.diag([1.,-1.,0.]);Q*=1.5
 direct,pred=inject_response(d,n,w,70.,D,B,Q)
 assert np.isclose(direct,pred,rtol=0,atol=1e-12)
 assert abs(np.trace(moments(d,n,w)['quadrupole_moment']))<1e-12

def test_angular_window_coupling():
 d,n,w=fake(); D=np.array([0.,0.,5.]); m1=moments(d,n,w)['angular_moment'];m2=moments(d,n,w*(1+.8*n[:,2]))['angular_moment']
 assert abs(D@(m2-m1))>.3

def test_zero_depth_leverage_dipole_bulk_degenerate():
 d,n,w=fake();deg=d*0+100.
 c= dipole_bulk_principal_cosines(deg,n,w)
 np.testing.assert_allclose(c,np.ones(3),atol=2e-12)
 c2=dipole_bulk_principal_cosines(d,n,w)
 assert max(c2)<.999

def test_psd_cross_window_covariance():
 d,n,w=fake();a=moments(d,n,w)['alpha'];b=moments(d,n,np.roll(w,20))['alpha']
 C,R=cross_window_covariance([a,b],np.ones(len(d))*200.)
 assert np.min(np.linalg.eigvalsh(C))>=0
 assert 0<R[0,1]<1
 with pytest.raises(ValueError):cross_window_covariance([a,b],np.array([1.]))

def test_failclosed_source_hash(tmp_path):
 f=tmp_path/'fake.npz';np.savez(f,ids=[1,2])
 with pytest.raises(ValueError,match='SHA mismatch'):load_cf4(f)

def test_source_data_replay():
 p=Path(__file__).resolve().parents[1]/'source/selected_source_observables.npz'
 if not p.exists():pytest.skip('pinned real source NPZ not supplied to this sandbox')
 x=load_cf4(p)
 assert len(x.z)==35970
 w,d,sig=radial_weights(x,.045,.014)
 h,m=window_hubble(d,x.n,x.z,w)
 assert 0<h<200 and abs(np.trace(m['quadrupole_moment']))<1e-12
 assert abs(np.linalg.norm(x.n,axis=1).mean()-1)<1e-12

def test_antipodal_fullsky_moments_and_anisotropic_mask_leakage():
    # Exact equal-area, antipodal sky: dipole and STF quadrupole cancel.
    n=np.vstack([np.eye(3),-np.eye(3)]).astype(float)
    d=np.full(6,150.0); w=np.ones(6)
    m=moments(d,n,w)
    np.testing.assert_allclose(m['angular_moment'],np.zeros(3),atol=3e-16)
    np.testing.assert_allclose(m['quadrupole_moment'],np.zeros((3,3)),atol=3e-16)
    np.testing.assert_allclose(m['bulk_inverse_mpc'],np.zeros(3),atol=3e-18)
    skew=moments(d,n,w*(1+.6*n[:,2]))
    assert skew['angular_moment'][2] > 0.19
    dipole=np.array([0,0,5.]); bulk=np.zeros(3); quad=np.zeros((3,3))
    full=inject_response(d,n,w,71.,dipole,bulk,quad)[0]
    cut=inject_response(d,n,w*(1+.6*n[:,2]),71.,dipole,bulk,quad)[0]
    assert np.isclose(full,71.,atol=1e-13)
    assert cut>71.9


def test_constant_modulus_shift_with_frozen_weights():
    # Mpc scaling lambda=10**(Delta mu /5) => H_window /lambda,
    # ONLY if the previously declared weights are held fixed.
    d,n,w=fake(); v=np.linspace(4300,19000,len(d))
    a=moments(d,n,w)['alpha']; h0=float(a@v)
    lam=10**(.2/5)
    hnew=float(moments(lam*d,n,w)['alpha']@v)
    assert np.isclose(hnew,h0/lam,rtol=0,atol=1e-12)
    assert hnew < h0


def test_same_rows_cross_window_correlation_not_independent():
    d,n,w=fake()
    sig=np.ones(len(d))*200
    a=moments(d,n,w)['alpha']
    C,R=cross_window_covariance([a,a.copy()],sig)
    np.testing.assert_allclose(C[0,0],C[0,1],rtol=0,atol=1e-13)
    np.testing.assert_allclose(R,np.ones((2,2)),atol=1e-13)
