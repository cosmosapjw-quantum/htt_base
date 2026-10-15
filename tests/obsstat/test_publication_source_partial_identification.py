"""P1 source-matched negative result: no fake physical x/Q posterior."""
import numpy as np
import pytest
from obsstat.publication_source_partial_identification import (
    SourcePartialIdError,source_case_from_planck_temperature_alm,
    strict_tail_probability_identified_set,
)


def test_wolfram_exact_omega_over_sigma_ratio_identity():
    a=np.zeros(32);a[0]=18.;a[5]=20.
    case=source_case_from_planck_temperature_alm(a)
    e2=case["eps2_source_projection"];e3=case["eps3_source_projection"]
    ratio=(196*e2*e2)/(2025*(7*e2+e3)**2)
    assert case["U_omega_over_U_sigma"]==pytest.approx(ratio,rel=1e-14)
    assert case["flat_untilted_counterfactual_Q_outer_interval"]==pytest.approx([-ratio,1.])


def test_unrestricted_signed_curvature_retains_full_unbounded_Q():
    a=np.zeros(32);a[0]=18.;a[5]=20.
    case=source_case_from_planck_temperature_alm(a)
    assert case["full_unknown_curvature_tilt_Q_domain"]=="UNBOUNDED_BOTH_SIDES"
    assert case["physical_posterior"]=="ABSENT"
    assert not case["different_planck_processing_methods_are_new_latent_realizations"]
    for t in (-1000.,0,3,1000):
        assert strict_tail_probability_identified_set(
            t,case["full_unknown_curvature_tilt_Q_domain"])==[0,1]


def test_closed_counterfactual_still_does_not_assume_posterior_weights():
    a=np.zeros(32);a[0]=15.;a[5]=30.
    case=source_case_from_planck_temperature_alm(a)
    domain=case["flat_untilted_counterfactual_Q_outer_interval"]
    assert strict_tail_probability_identified_set(domain[0]-1e-3,domain)==[1,1]
    assert strict_tail_probability_identified_set(0.,domain)==[0,1]
    assert strict_tail_probability_identified_set(domain[1],domain)==[0,0]


def test_zero_anchor_keeps_Q_undefined_without_division():
    a=np.zeros(32)
    case=source_case_from_planck_temperature_alm(a)
    assert case["status"]=="ZERO_SHEAR_ANCHOR_Q_UNDEFINED"
    assert case["flat_untilted_counterfactual_Q_outer_interval"] is None
    assert strict_tail_probability_identified_set(1.,case["flat_untilted_counterfactual_Q_outer_interval"])==[0,1]


def test_bad_branch_and_nonfinite_input_rejected():
    with pytest.raises(SourcePartialIdError):
        source_case_from_planck_temperature_alm(np.ones(32),observer_epsilon1_scenario="measured_dipole")
    with pytest.raises(ValueError):
        source_case_from_planck_temperature_alm(np.full(32,np.nan))
    with pytest.raises(SourcePartialIdError):
        strict_tail_probability_identified_set(float("inf"),[0,1])
    with pytest.raises(SourcePartialIdError):
        strict_tail_probability_identified_set(.2,[2,1])
