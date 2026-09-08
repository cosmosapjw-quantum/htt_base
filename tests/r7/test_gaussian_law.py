import numpy as np
import pytest
from htt.infer.r7_gaussian_law import (
    gaussian_acceptance, condition_gaussian, conditional_mean_derivative,
    calibration_information_gain,
)


def test_singular_support_and_zero_rank():
    bad = gaussian_acceptance([0.,1.], [[1.,0.],[0.,0.]], .05, 0.)
    assert not bad.inside_support and not bad.accepted
    assert gaussian_acceptance([0.,0.], np.zeros((2,2)), .05, 0.).accepted
    assert gaussian_acceptance([0.,0.], np.zeros((2,2)), .05, 0.).threshold == 0


def test_calibration_information_oracle():
    gain = calibration_information_gain([[1.]], [[1.]], [[1.]], [[.25]])
    assert abs(gain.new_information[0,0] - .2) < 1e-10
    assert gain.old_information[0,0] == 0
    zero = calibration_information_gain(np.eye(2), np.array([[1.],[0.]]), [[1.]], [[.25]])
    np.testing.assert_allclose(zero.gain @ [0,1], 0, atol=1e-14)


def test_exact_correlated_measurement():
    c = condition_gaussian([2.], [0.], [[1.]], [[1.]], [[1.]], [3.])
    np.testing.assert_array_equal(c.mean, [5.])
    np.testing.assert_array_equal(c.covariance, [[0.]])
    assert gaussian_acceptance([0.], c.covariance, .05, 0.).accepted
    assert not gaussian_acceptance([1.], c.covariance, .05, 0.).accepted


def test_duplicate_conditioning_and_out_of_support_z():
    c = condition_gaussian([0.], [0.,0.], [[1.]], [[1.,1.]],
                           [[1.,1.],[1.,1.]], [2.,2.])
    np.testing.assert_allclose(c.mean, [2.], atol=1e-14)
    np.testing.assert_allclose(c.covariance, [[0.]], atol=1e-14)
    with pytest.raises(ValueError, match="support"):
        condition_gaussian([0.], [0.,0.], [[1.]], [[1.,1.]],
                           [[1.,1.],[1.,1.]], [2.,3.])


def test_conditional_derivative_includes_varying_gain():
    value = conditional_mean_derivative([2.], [3.], [[4.]], [[5.]], [6.])
    np.testing.assert_array_equal(value, [20.])


@pytest.mark.parametrize('covariance', [ [[1.,.1],[0.,1.]], [[1.,0.],[0.,-1.]],
                                       [[1.,0.],[0.,float('nan')]] ])
def test_invalid_covariance(covariance):
    with pytest.raises(ValueError): gaussian_acceptance([0.,0.], covariance, .05, 0.)


def test_uncertain_rank_is_not_rounded_into_a_pass():
    result = gaussian_acceptance([0.,0.], np.diag([1.,1e-20]), .05, 0.)
    assert result.numeric_status == "NUMERICALLY_UNRESOLVED"
    assert not result.accepted


def test_units_do_not_change_known_gaussian_acceptance():
    for scale in (1e-6, 1., 1e6):
        result = gaussian_acceptance(np.array([1.,2.])*scale,
                                     np.diag([2.,3.])*scale**2,.05,0.)
        assert result.accepted
        assert abs(result.quadratic - (1/2+4/3)) < 1e-12
def test_fixed_residual_inversion_keeps_physical_domain_and_rank():
    from common.r7_contracts import ScopeKey
    from htt.infer.r7_gaussian_law import JointObservationLaw
    from htt.infer.r7_confidence import PhysicalDomain, GaussianAcceptanceRule, invert_acceptance
    scope=ScopeKey("e","l","m",("d",),"K","v","fixed","c")
    law=JointObservationLaw(scope,np.array([0.]),("row",),("theta",),("K",),
        lambda t,e: np.asarray(t),np.eye(1),
        {"source_ids":["fixture"],"selection_law":"fixed","covariance_source":"known",
         "mean_definition":"theta"},"positive",lambda t,e:t[0]>=0)
    domain=PhysicalDomain("positive",("theta",),lambda t,e:True,((0.,np.inf),))
    region=invert_acceptance(law,domain,GaussianAcceptanceRule())
    assert region.contains([1.9])
    assert not region.contains([2.1])
    assert not region.contains([-1.])
    assert region.evaluate([0.]).rank==1
    assert region.coverage_lower==.95


def test_missing_marginal_keeps_fixed_allocation_and_model_union():
    from htt.infer.r7_confidence import PhysicalDomain, PhysicalRegion, combine_regions
    from common.r7_contracts import AcceptanceResult
    domain=PhysicalDomain("real",("theta",),lambda t,e:True)
    region=PhysicalRegion(None,domain,None,
        lambda t,e:AcceptanceResult(True,0,1,1,t[0]<0,"RESOLVED"),.975,"fixture",("scope",))
    combined=combine_regions([region,None],domain,mode="MARGINAL_UNION_BOUND",fixed_alphas=(.025,.025))
    assert combined.coverage_lower==.95
    assert combined.contains([-1.]) and not combined.contains([1.])
    union=combine_regions([region,None],domain,mode="ALTERNATIVE_MODEL_UNION")
    assert union.contains([1.])
    with pytest.raises(ValueError,match="below allocation"):
        combine_regions([region,None],domain,mode="MARGINAL_UNION_BOUND",fixed_alphas=(.01,.04))


def test_schur_cancellation_cannot_create_resolved_tiny_positive_variance():
    result=condition_gaussian([0.],[0.],[[1.+1e-15]],[[1.]],[[1.]],[0.])
    assert result.numeric_status=='NUMERICALLY_UNRESOLVED'


def test_support_tolerance_cannot_thicken_a_singular_density():
    from htt.infer.r7_gaussian_law import gaussian_loglik
    with pytest.raises(ValueError,match='numerical error bound'):
        gaussian_loglik([0.,.5],[[1.,0.],[0.,0.]],1.)
    assert gaussian_loglik([0.,.5],[[1.,0.],[0.,0.]],0.)==-np.inf
