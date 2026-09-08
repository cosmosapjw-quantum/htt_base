import numpy as np
import pytest
from htt.infer.r7_high_source import (cancellation_cost,HighSourcePolicy,profile_high_source,gaussian_fisher)

def test_center_radius_and_pairwise_overlap_are_different():
    result=cancellation_cost([[1.]],[[1.]],[2.],0.)
    assert result.cost==4.
    assert not result.cost<=1.**2
    assert result.cost<=4*1.**2
    outside=cancellation_cost([[1.],[0.]],[[1.]],[0.,1.],0.)
    assert not outside.in_range and np.isinf(outside.cost)
    np.testing.assert_equal(outside.range_witness,[0.,1.])

def test_four_experiments_have_different_laws():
    base=dict(coverage_target="fixed theta with named nuisance law",law_id="fixture")
    h0=profile_high_source([2.],[[1.]],[[1.]],[[1.]],HighSourcePolicy("UNRESTRICTED",**base),[0.])
    assert h0.degrees_of_freedom==0 and h0.quadratic==0 and h0.null_directions.shape==(1,1)
    h1=profile_high_source([2.],[[1.]],[[1.]],[[1.]],HighSourcePolicy("ELLIPSOID",S=np.eye(1),radius=1.,**base),[0.])
    assert abs(h1.quadratic-1)<1e-12
    h2=profile_high_source([2.],[[1.]],[[1.]],[[1.]],HighSourcePolicy("GAUSSIAN",S=np.eye(1),**base),[0.])
    assert h2.quadratic==2. and h2.covariance[0,0]==2. and np.isfinite(h2.loglik)
    h3=profile_high_source([2.],[[1.]],[[0.]],[[1.]],HighSourcePolicy("JOINT_MEASURED",joint_z=np.array([1.]),
        joint_B=np.array([[0.]]),joint_covariance=np.ones((2,2)),**base),[1.])
    assert h3.degrees_of_freedom==1 and np.isfinite(h3.loglik)
    impossible=profile_high_source([2.],[[1.]],[[0.]],[[1.]],HighSourcePolicy("JOINT_MEASURED",joint_z=np.array([1.]),
        joint_B=np.array([[0.]]),joint_covariance=np.ones((2,2)),**base),[0.])
    assert impossible.loglik==-np.inf

def test_positive_sky_profile_remains_an_inner_optimization():
    policy=HighSourcePolicy("ELLIPSOID","conditional","x",np.eye(1),1.,np.eye(1),np.array([.2]),law_id="positive")
    # Explicitly supply h0 rather than the deliberately malformed scalar below.
    from dataclasses import replace
    policy=replace(policy,h0=np.zeros(1))
    result=profile_high_source([-2.],[[1.]],[[1.]],[[1.]],policy,[0.])
    assert result.objective_lower_bound is None
    assert result.numeric_status=="OUTER_PROFILE_UNRESOLVED_POSITIVE_SKY"

def test_covariance_fisher_term_survives_zero_mean_response():
    np.testing.assert_allclose(gaussian_fisher([[0.]],[[2.]],[[[2.]]]),[[.5]])
