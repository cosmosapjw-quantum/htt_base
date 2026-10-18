"""Tests for basis-invariant weakest-direction information certificates."""
import numpy as np
import pytest
from obsstat.cf4_q_information_budget import information_budget, Cf4QInformationError


def test_simple_budget_has_correct_feasible_deficit():
    raw=np.eye(3)
    kept=np.diag([.12,.01,.6])
    x=information_budget(raw,kept,minimum_retained_fraction=.05)
    np.testing.assert_allclose(x['relative_information_eigenvalues'],[.01,.12,.6],rtol=0,atol=1e-12)
    assert x['weakest_relative_information']==pytest.approx(.01)
    assert x['normalized_minimum_added_information_trace']==pytest.approx(.04)
    assert x['proposed_reference_lift_satisfies_floor'] is True


def test_invariant_to_arbitrary_invertible_parameter_change():
    rng=np.random.default_rng(22)
    A=rng.normal(size=(3,3))
    raw=np.diag([5.,2.,7.])
    kept=np.diag([.05,.2,1.4])
    x=information_budget(raw,kept,minimum_retained_fraction=.08)
    y=information_budget(A.T@raw@A,A.T@kept@A,minimum_retained_fraction=.08)
    np.testing.assert_allclose(x['relative_information_eigenvalues'],
                               y['relative_information_eigenvalues'],rtol=1e-10,atol=1e-10)


def test_rejects_non_psd_retention_or_singular_raw():
    with pytest.raises(Cf4QInformationError):
        information_budget(np.diag([1,1,0]),np.eye(3),minimum_retained_fraction=.05)
    with pytest.raises(Cf4QInformationError):
        information_budget(np.eye(3),2*np.eye(3),minimum_retained_fraction=.05)


def test_all_information_lost_requires_full_target_floor():
    x=information_budget(np.eye(3),np.zeros((3,3)),minimum_retained_fraction=.07)
    assert x['normalized_minimum_added_information_trace']==pytest.approx(.21)
    assert x['minimum_new_orthogonal_amplitude_ratio']==pytest.approx(np.sqrt(.07))


def test_complex_gram_rejected_not_silently_dropped():
    with pytest.raises(Cf4QInformationError):
        information_budget(np.eye(3,dtype=complex),.2*np.eye(3),minimum_retained_fraction=.05)
