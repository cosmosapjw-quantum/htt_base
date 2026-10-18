"""Actual SH0ES 2022 compact matrix representation: exact GLS and gauge tests."""
import numpy as np
import pytest
from obsstat.htt_shoes_matrix_bridge import (
    Sh0esMatrixError, whitened_linear_gls,
    conditional_template_information, assert_cross_catalogue_source_map,
)


def test_whitened_gls_equals_dense_for_correlated_gaussian():
    rng=np.random.default_rng(28)
    n,p=30,5
    A=rng.normal(size=(n,p))
    beta=rng.normal(size=p)
    x=rng.normal(size=(n,n))
    C=x@x.T+np.eye(n)
    y=A@beta+rng.normal(size=n)
    out=whitened_linear_gls(y,A,C)
    ci=np.linalg.inv(C)
    reference=np.linalg.solve(A.T@ci@A,A.T@ci@y)
    np.testing.assert_allclose(out['estimate'],reference,atol=1e-12)
    np.testing.assert_allclose(out['estimate_covariance'],
        np.linalg.inv(A.T@ci@A),rtol=1e-12,atol=1e-12)
    assert out['normal_equation_gradient_relative'] < 1e-12


def test_reparametrization_invariance_and_exact_template_gauge():
    rng=np.random.default_rng(198)
    A=rng.normal(size=(80,5))
    W=rng.normal(size=(5,5))
    W+=np.eye(5)
    U=rng.normal(size=(80,80))
    C=U@U.T+5*np.eye(80)
    y=rng.normal(size=80)
    b=whitened_linear_gls(y,A,C)
    c=whitened_linear_gls(y,A@W,C)
    np.testing.assert_allclose(A@b['estimate'],A@W@c['estimate'],atol=1e-10,rtol=0)
    p=conditional_template_information(A[:,0],A,C)
    assert p['retained_information_fraction']<1e-10
    some=rng.normal(size=80)
    q=conditional_template_information(some,A,C)
    assert q['retained_information_fraction']>0


def test_template_information_cannot_exceed_fixed_mean_information():
    rng=np.random.default_rng(63)
    A=rng.normal(size=(36,5))
    C=np.diag(rng.uniform(.2,4,36))
    template=rng.normal(size=36)
    x=conditional_template_information(template,A,C)
    assert 0<=x['retained_information_fraction']<=1
    assert x['conditioned_fisher_information']<=x['raw_fisher_information']+1e-12


def test_cross_catalogue_source_map_must_be_observed_not_guessed():
    rng=np.random.default_rng(36)
    cov=np.eye(5)
    with pytest.raises(Sh0esMatrixError):
        assert_cross_catalogue_source_map(None,cov,n_cf4=4)
    with pytest.raises(Sh0esMatrixError):
        assert_cross_catalogue_source_map(np.ones((4,6)),cov,n_cf4=4)
    a=assert_cross_catalogue_source_map(np.eye(5)[:4],cov,n_cf4=4)
    np.testing.assert_allclose(a,np.eye(4))


def test_no_silent_complex_or_bad_source_covariance():
    with pytest.raises(Sh0esMatrixError):
        whitened_linear_gls(np.ones(20),np.ones((20,2)),1j*np.eye(20))
    with pytest.raises(Sh0esMatrixError):
        whitened_linear_gls(np.ones(20),np.ones((20,2)),-np.eye(20))


def test_shared_ladder_anchor_must_not_be_double_counted():
    from obsstat.htt_shoes_matrix_bridge import joint_shared_anchor_covariance
    k=.4**2
    s=.2**2
    block=joint_shared_anchor_covariance(
        np.array([[s]]),np.array([[s]]),
        np.ones((1,1)),np.ones((1,1)),np.array([[k]]))
    np.testing.assert_allclose(block,np.array([[k+s,k],[k,k+s]]))
    actual=np.ones(2)@block@np.ones(2)/4
    naive=(k+s)/2
    assert actual==pytest.approx(k+s/2)
    assert actual-naive==pytest.approx(k/2)


def test_separate_anchors_have_zero_crosscovariance():
    from obsstat.htt_shoes_matrix_bridge import joint_shared_anchor_covariance
    prior=np.diag([.2,.4])
    a=np.array([[1.,0.],[1.,0.]])
    b=np.array([[0.,1.]])
    full=joint_shared_anchor_covariance(.3*np.eye(2),np.eye(1),a,b,prior)
    np.testing.assert_allclose(full[:2,2:],0,atol=1e-14)


def test_joint_anchor_covariance_rejects_unphysical_indefinite_prior():
    from obsstat.htt_shoes_matrix_bridge import joint_shared_anchor_covariance
    with pytest.raises(Sh0esMatrixError):
        joint_shared_anchor_covariance(np.eye(1),np.eye(1),np.ones((1,2)),
                                       np.ones((1,2)),np.diag([1.,-1.]))
