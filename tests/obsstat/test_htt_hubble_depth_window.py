"""Derived survey leakage identities and source-conditioned cross-window tests."""
import numpy as np
import pytest
from obsstat.htt_hubble_depth_window import (
    C_KM_S,K_LOG,HubbleWindowError,source_log_hubble,
    directional_window_summary,injected_window_deviation,
)


def _data(n=300,seed=11):
    rng=np.random.default_rng(seed)
    z=rng.uniform(.011,.099,n)
    sky=rng.normal(size=(n,3));sky/=np.linalg.norm(sky,axis=1)[:,None]
    mu=25+5*np.log10(C_KM_S*z/74)
    return z,sky,mu,np.full(n,.2),np.where(np.arange(n)%3==0,"FP","TF"),np.arange(n)


def _fit(z,sky,mu,err,method,idx,windows=None):
    y,sigma=source_log_hubble(z,mu,err,velocity_dispersion_kms=220)
    return directional_window_summary(z,sky,y,sigma,method,idx,
        [{"id":"all","min_z":.01,"max_z":.10}] if windows is None else windows,
        min_sources=10)


def test_exact_log_distance_law_at_constant_h():
    z,n,mu,err,method,idx=_data()
    y,s=source_log_hubble(z,mu,err)
    # Observed log/exp double rounding residual 3.55271368e-15; bound =5e-15.
    np.testing.assert_allclose(y,np.log(74.),rtol=0,atol=5e-15)
    assert np.all(s>0)
    out=_fit(z,n,mu,err,method,idx)
    assert out["H_eff_km_s_Mpc"][0]==pytest.approx(74.,rel=2e-15)


def test_isotropic_octant_geometry_bulk_and_stf_leakage_vanish():
    # Eight cube-corner directions provide exact rank-2 isotropic moments.
    from itertools import product
    sky=np.asarray(list(product((-1.,1.),repeat=3)))/np.sqrt(3.)
    z=np.full(8,.05);h=np.full(8,np.log(74.));sigma=np.ones(8)
    r=directional_window_summary(z,sky,h,sigma,
       np.array(["F"]*8),np.arange(8),[{"id":"all","min_z":.01,"max_z":.10}],
       min_sources=8)
    np.testing.assert_allclose(r["bulk_response_per_300_km_s"],0,atol=1e-17)
    np.testing.assert_allclose(r["angular_dipole_response"],0,atol=1e-17)
    # Observed tensor roundoff residual 1.110223024e-16; bound =2e-16.
    np.testing.assert_allclose(r["STF2_angular_quadrupole_response"],0,atol=2e-16)


def test_nonuniform_mask_induces_bulk_mixing_and_exact_response():
    z,n,mu,err,m,idx=_data()
    n[:,2]=np.abs(n[:,2])
    n/=np.linalg.norm(n,axis=1)[:,None]
    a=_fit(z,n,mu,err,m,idx)
    beta=np.array((0.,0.,300.))
    inject=(n@beta)/(C_KM_S*z)
    _,std=source_log_hubble(z,mu,err,velocity_dispersion_kms=220)
    direct=(a["weight_operator"]@inject)[0]
    predicted=injected_window_deviation(a,bulk_velocity_kms=beta)[0]
    assert abs(predicted-direct)<5e-17
    assert predicted>0.001


def test_cross_window_overlap_is_not_diagonal_and_different_windows_separate():
    z,n,mu,err,m,idx=_data()
    w=[{"id":"near","min_z":.01,"max_z":.05},
       {"id":"all","min_z":.01,"max_z":.10},
       {"id":"far","min_z":.05,"max_z":.10}]
    a=_fit(z,n,mu,err,m,idx,w)
    cov=a["covariance_logH_working_diagonal_only"]
    assert cov[0,1]>0 and cov[2,1]>0
    assert cov[0,2]==pytest.approx(0.,abs=1e-18)
    assert np.linalg.eigvalsh(cov).min()>-1e-14
    np.testing.assert_allclose(a["correlation_logH_working_diagonal_only"],
        a["correlation_logH_working_diagonal_only"].T,atol=1e-14)


def test_exact_symmetric_traceless_STF_and_response():
    z,n,mu,err,m,idx=_data()
    a=_fit(z,n,mu,err,m,idx)
    S=np.diag([.01,-.01,0])
    expected=a["weight_operator"]@np.einsum("ni,ij,nj->n",n,S,n)
    got=injected_window_deviation(a,stf2=S)
    np.testing.assert_allclose(got,expected,atol=1e-17)
    assert np.max(np.abs(np.trace(a["STF2_angular_quadrupole_response"],axis1=1,axis2=2)))<1e-14


def test_missing_group_duplicate_nonpositive_or_rank_unsupported_fail():
    z,n,mu,err,m,idx=_data()
    with pytest.raises(HubbleWindowError,match="group-unique"):
        _fit(z,n,mu,err,m,np.zeros(len(idx),int))
    with pytest.raises(HubbleWindowError,match="redshifts"):
        source_log_hubble(z*0,mu,err)
    with pytest.raises(HubbleWindowError,match="under-supported"):
        _fit(z,n,mu,err,m,idx,[{"id":"bad","min_z":.001,"max_z":.003}])
    with pytest.raises(HubbleWindowError,match="tracefree"):
        injected_window_deviation(_fit(z,n,mu,err,m,idx),stf2=np.eye(3))
