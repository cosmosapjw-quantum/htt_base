"""Scope-falsifying tests against frozen source and synthetic independent oracles."""
import sys
from pathlib import Path
import numpy as np
import pytest

HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/'src'))
from finite_power_envelope import (SOURCE_SHA256,ELLS,EnvelopeInputError,
  source_operator,locate_source,shell_slice,shell_gram,independent_power_covariance,
  sharp_ellipsoid_bound,shared_mode_correlated_covariance,
  correlation_agnostic_bound,leak_trace_fractions,default_templates)

@pytest.fixture(scope='module')
def K():
    return source_operator(locate_source(HERE))


def test_source_sha_and_partitions(K,tmp_path):
    assert K.shape==(32,253)
    assert np.linalg.norm(K,2)==pytest.approx(2.255720291177002,abs=1e-13)
    assert sum(shell_slice(l).stop-shell_slice(l).start for l in ELLS)==253
    q=locate_source(HERE)
    bad=tmp_path/'corrupted.npz';bad.write_bytes(q.read_bytes()+b'X')
    with pytest.raises(EnvelopeInputError):source_operator(bad)
    with pytest.raises(EnvelopeInputError):source_operator(q,expected_sha256='0'*64)


def test_source_trace_white_normalization(K):
    templates=default_templates()
    p=templates['WHITE_UNIT_VARIANCE_EXPLICIT']
    C=independent_power_covariance(K,p)
    np.testing.assert_allclose(C,K@K.T,atol=2e-14,rtol=2e-14)
    assert np.trace(C)==pytest.approx(23.99763523078023,abs=1e-11)
    fractions=leak_trace_fractions(K,p)
    assert sum(fractions.values())==pytest.approx(1.)
    assert fractions[6]+fractions[7]==pytest.approx(0.548704516491934,abs=1e-12)


def test_direct_matrix_covariance_vs_shell_sum(K):
    p={l:float(l-5) for l in ELLS}
    d=np.concatenate([np.full(2*l+1,p[l]) for l in ELLS])
    exact=(K*d[None,:])@K.T
    np.testing.assert_allclose(exact,independent_power_covariance(K,p),atol=2e-13,rtol=2e-14)


def test_covariance_monte_carlo_oracle(K):
    rng=np.random.default_rng(6082)
    C=independent_power_covariance(K,{l:1.0 for l in ELLS})
    # Monte Carlo across *independent manufactured harmonic vectors*, not Planck sky draws.
    n=24000
    a=rng.standard_normal((253,n))
    x=K@a
    est=(x@x.T)/n
    assert np.linalg.norm(est-C)/np.linalg.norm(C)<0.035


def test_exact_ellipsoid_saturation(K):
    r={l:float(np.sqrt(2*l+1)) for l in ELLS}
    ans=sharp_ellipsoid_bound(K,r)
    assert ans['sharp_bound']>0
    assert ans['ellipsoid_norm_of_witness']==pytest.approx(1,rel=2e-13)
    assert ans['achieved_leakage']==pytest.approx(ans['sharp_bound'],rel=2e-13)
    # independent masked response C^T C and leading spectral singular value
    R=np.concatenate([np.full(2*l+1,r[l]) for l in ELLS])
    assert ans['sharp_bound']==pytest.approx(np.linalg.norm(K*R[None,:],2),rel=2e-13)


def test_ellipsoid_known_simple_analytic():
    k=np.zeros((32,253),float)
    k[0,shell_slice(6).start]=3.0;k[1,shell_slice(7).start]=4.0
    r={l:0. for l in ELLS};r[6]=2.;r[7]=3.
    ans=sharp_ellipsoid_bound(k,r)
    assert ans['sharp_bound']==pytest.approx(12.)
    assert ans['achieved_leakage']==pytest.approx(12.)
    assert np.linalg.norm(ans['witness'][shell_slice(6)])<1e-12


def test_within_shell_rotation_covariance_invariant(K):
    rng=np.random.default_rng(277)
    kp=K.copy()
    for l in ELLS:
        sl=shell_slice(l);n=2*l+1
        q,_=np.linalg.qr(rng.normal(size=(n,n)))
        kp[:,sl]=K[:,sl]@q
    p={l:42./(l*(l+1)) for l in ELLS}
    np.testing.assert_allclose(independent_power_covariance(kp,p),independent_power_covariance(K,p),atol=1e-14,rtol=2e-14)


def test_correlated_toy_psd_fixed_marginals(K):
    p=default_templates()['RED_Cl_PROP_1_OVER_ELL_ELLPLUS1_NORMALIZED_AT_ELL6']
    C0=independent_power_covariance(K,p)
    np.testing.assert_allclose(shared_mode_correlated_covariance(K,p,0),C0,atol=1e-14)
    for rho in (.15,.5,1.):
        C=shared_mode_correlated_covariance(K,p,rho)
        assert np.linalg.eigvalsh(C)[0]>-1e-12
        assert np.sqrt(max(np.linalg.eigvalsh(C)))<=correlation_agnostic_bound(K,p)*(1+1e-12)


def test_corr_toy_explicit_monte_carlo(K):
    p={l:1. for l in ELLS};rho=.45;N=24000
    rng=np.random.default_rng(812)
    shared=rng.normal(size=(33,N))
    samples=[]
    for l in ELLS:
        xi=rng.normal(size=(2*l+1,N))
        samples.append(np.sqrt(rho)*shared[:2*l+1]+np.sqrt(1-rho)*xi)
    output=K@np.concatenate(samples,axis=0)
    sample_cov=output@output.T/N
    exact=shared_mode_correlated_covariance(K,p,rho)
    assert np.linalg.norm(sample_cov-exact)/np.linalg.norm(exact)<0.055


def test_zero_power_and_strict_input_checks(K):
    zero={l:0 for l in ELLS}
    assert np.array_equal(independent_power_covariance(K,zero),np.zeros((32,32)))
    assert sharp_ellipsoid_bound(K,zero)['sharp_bound']==0
    p={l:1. for l in ELLS}
    for bad in ({l:1. for l in range(6,16)}, {**p,6:float('nan')},{**p,8:float('inf')},{**p,9:-1.},{**p,10:True}):
        with pytest.raises(EnvelopeInputError):independent_power_covariance(K,bad)
    with pytest.raises(EnvelopeInputError):shared_mode_correlated_covariance(K,p,1.1)
    with pytest.raises(EnvelopeInputError):shared_mode_correlated_covariance(K,p,float('nan'))
    with pytest.raises(EnvelopeInputError):independent_power_covariance(K[:4],p)


def test_ellipsoid_not_necessarily_independent_gaussian(K):
    p=default_templates()['WHITE_UNIT_VARIANCE_EXPLICIT']
    C=independent_power_covariance(K,p)
    ellipsoid=sharp_ellipsoid_bound(K,{l:float(np.sqrt(2*l+1)) for l in ELLS})
    assert np.trace(C)==pytest.approx(23.99763523078023,abs=1e-10)
    assert np.max(np.linalg.eigvalsh(ellipsoid['gram']))==pytest.approx(ellipsoid['sharp_bound']**2)
    assert ellipsoid['sharp_bound']>=np.linalg.norm(K,2)


def test_source_fallback_to_existing_checkout_without_binary_duplication(tmp_path):
    """Simulate exact existing-repo path, no new repo checkout is created."""
    stage=tmp_path/'htt_base/docs/research_program/theory_obs_application_20261015/loop11_smica_power_envelope_20261016'
    stage.mkdir(parents=True)
    path=tmp_path/'htt_base/docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz'
    path.parent.mkdir(parents=True)
    path.write_bytes(locate_source(HERE).read_bytes())
    assert locate_source(stage)==path
    assert source_operator(locate_source(stage)).shape==(32,253)
    with pytest.raises(EnvelopeInputError):
        locate_source(tmp_path/'unknown/subdir')
