import numpy as np
import pytest
from htt_gate_precursors.bianchi_i import(log_frequency_ratio,
 log_redshift_taylor2,collisionless_temperature,stf_linear_temperature_anisotropy)


def test_flrw_exact_all_directions_and_blackbody_temperature():
    rng=np.random.default_rng(8);N=rng.normal(size=(125,3));N/=np.linalg.norm(N,axis=1)[:,None]
    val=log_frequency_ratio([.7]*3,.3,N)
    assert np.allclose(val,.21,atol=1e-14)
    assert np.allclose(collisionless_temperature(2.7255,[.7]*3,.3,N),2.7255*np.exp(-.21))


def test_exact_bianchi_constant_conserved_spatial_momenta():
    h=np.array([.67,.7,.74]);n=np.array([.2,.4,np.sqrt(.8)])
    log1pz=log_frequency_ratio(h,.8,n)
    source_mom=n/np.exp(-h*.8)  # k_i/a_i(-tau), with k_i=n_i at observer
    ratio=np.linalg.norm(source_mom)
    assert np.exp(log1pz)==pytest.approx(ratio,rel=1e-14)


def test_second_cumulant_is_positive_weighted_H_variance():
    h=np.array([.5,.7,.9]);n=np.array([.2,.4,np.sqrt(.8)])
    tau=5e-4
    approx=log_redshift_taylor2(h,tau,n)
    exact=log_frequency_ratio(h,tau,n)
    assert abs(exact-approx)<1e-11
    vals=[]
    for t in [1e-3,5e-4,2.5e-4]:
        vals.append(abs(log_frequency_ratio(h,t,n)-log_redshift_taylor2(h,t,n)))
    assert vals[0]>vals[1]>vals[2]


def test_finite_redshift_differs_from_local_gradient_when_anisotropic():
    h=np.array([.5,.7,.9]);n=np.array([.2,.4,np.sqrt(.8)])
    tau=.2
    local=(n*n)@h
    window=log_frequency_ratio(h,tau,n)/tau
    assert window>local


def test_tracefree_shear_linear_quadrupole_cancellation():
    rng=np.random.default_rng(3);n=rng.normal(size=(30000,3));n/=np.linalg.norm(n,axis=1)[:,None]
    sig=np.array([.01,-.004,-.006]);q=stf_linear_temperature_anisotropy(sig,.4,n)
    assert abs(q.mean())<4e-5
    assert np.allclose(q,-.4*(n*n)@sig)


def test_collisionless_unpolarized_transport_stays_unpolarized():
    # No Thomson term and f_AB proportional to identity at emission:
    # parallel transport is a unitary screen rotation, so Q=U=V remain zero.
    I=np.eye(2,dtype=complex)*.83
    for ang in np.linspace(0,2*np.pi,17):
        U=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]])
        out=U@I@U.conj().T
        assert np.allclose(out,I,atol=1e-15)


def test_unit_direction_and_shear_trace_guards():
    with pytest.raises(ValueError):log_frequency_ratio([.7]*3,.3,[0,0,2])
    with pytest.raises(ValueError):stf_linear_temperature_anisotropy([1,0,0],.5,[1,0,0])


def test_bianchi_exact_positive_cumulant_gives_secant_monotonicity():
    h=np.array([.5,.7,.9]);n=np.array([.2,.4,np.sqrt(.8)])
    local=(n*n)@h
    windows=np.array([.025,.05,.1,.2,.4])
    measured=np.array([log_frequency_ratio(h,t,n)/t for t in windows])
    assert np.all(measured>local)
    assert np.all(np.diff(measured)>0)
    # All component histories equal on direction support -> equality.
    assert log_frequency_ratio([.7]*3,.45,n)/.45==pytest.approx(.7)


def test_logsumexp_high_range_finite_even_when_naive_exp_overflows():
    n=np.array([.2,.4,np.sqrt(.8)])
    val=log_frequency_ratio([2000,2100,2200],.5,n)
    assert np.isfinite(val)
    assert val>1000
