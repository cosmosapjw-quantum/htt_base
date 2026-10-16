"""Falsifiers for the source-column layout and conditional finite envelopes."""
from pathlib import Path
import sys

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "src"))
from extended_power_envelope import (ELLS, EnvelopeInputError, shell_slice,
    joined_operator, independent_shell_covariance, sharp_ellipsoid,
    shared_coordinate_toy, cross_shell_agnostic_std_bound, scenario_templates)


@pytest.fixture(scope="module")
def source_matrices():
    repo = HERE.parents[3]
    prior = repo / "docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response/results/response_v1/baseline_response_matrices.npz"
    current = HERE / "results/ell17_32_source_v1/ell17_32_mask_response.npz"
    with np.load(prior, allow_pickle=False) as x, np.load(current, allow_pickle=False) as y:
        old = x["K_ell2to5_32x253"].copy()
        new = y["K_ell2to5_32x800"].copy()
    return old, new, joined_operator(old, new)


def test_exact_shell_partition_and_frozen_old_trace(source_matrices):
    old, new, full = source_matrices
    assert old.shape == (32,253) and new.shape == (32,800)
    assert full.shape == (32,1053)
    assert shell_slice(6) == slice(0,13)
    assert shell_slice(16).stop == 253
    assert shell_slice(17).start == 253
    assert shell_slice(32).stop == 1053
    assert all(shell_slice(ell).stop-shell_slice(ell).start == 2*ell+1 for ell in ELLS)
    np.testing.assert_array_equal(full[:,:253],old)
    np.testing.assert_array_equal(full[:,253:],new)
    assert np.sum(old*old) == pytest.approx(23.99763523078023, abs=1e-11)


def test_direct_diagonal_covariance_and_increment(source_matrices):
    old,new,k = source_matrices
    power = scenario_templates()["RED_ELL6_NORMALIZED_SCENARIO"]
    covariance = independent_shell_covariance(k,power)
    diagonal = np.concatenate([np.full(2*ell+1,power[ell]) for ell in ELLS])
    np.testing.assert_allclose(covariance, (k*diagonal[None,:])@k.T, atol=2e-13, rtol=2e-14)
    assert np.linalg.eigvalsh(covariance)[0] >= -1e-12
    assert np.trace(covariance) > np.sum((old*np.sqrt(diagonal[:253])[None,:])**2)


def test_ellipsoid_is_sharp_and_not_gaussian_quantile(source_matrices):
    _,_,k = source_matrices
    radii = {ell:float(np.sqrt(2*ell+1)) for ell in ELLS}
    answer = sharp_ellipsoid(k,radii)
    assert answer["witness_constraint"] == pytest.approx(1., abs=2e-12)
    assert answer["achieved"] == pytest.approx(answer["bound"], abs=2e-12)
    scale = np.concatenate([np.full(2*ell+1,radii[ell]) for ell in ELLS])
    assert answer["bound"] == pytest.approx(np.linalg.norm(k*scale[None,:],2), rel=2e-13)
    assert answer["bound"] >= np.linalg.norm(k,2)


def test_cross_shell_toy_psd_and_agnostic_bound(source_matrices):
    _,_,k = source_matrices
    power = scenario_templates()["WHITE_UNIT_VARIANCE_SCENARIO"]
    baseline = independent_shell_covariance(k,power)
    np.testing.assert_allclose(shared_coordinate_toy(k,power,0.),baseline,atol=1e-13)
    agnostic = cross_shell_agnostic_std_bound(k,power)
    for rho in (.25,.5,1.):
        covariance = shared_coordinate_toy(k,power,rho)
        eigen = np.linalg.eigvalsh(covariance)
        assert eigen[0] > -1e-12
        assert np.sqrt(eigen[-1]) <= agnostic*(1+1e-12)


def test_zero_and_invalid_inputs_fail_closed(source_matrices):
    old,new,k = source_matrices
    zero = {ell:0. for ell in ELLS}
    assert np.array_equal(independent_shell_covariance(k,zero),np.zeros((32,32)))
    assert sharp_ellipsoid(k,zero)["bound"] == 0.
    with pytest.raises(EnvelopeInputError): joined_operator(old,new[:,:-1])
    with pytest.raises(EnvelopeInputError): shell_slice(33)
    for invalid in ({ell:1. for ell in range(6,32)},
                    {**scenario_templates()["WHITE_UNIT_VARIANCE_SCENARIO"],17:float("nan")},
                    {**scenario_templates()["WHITE_UNIT_VARIANCE_SCENARIO"],18:True},
                    {**scenario_templates()["WHITE_UNIT_VARIANCE_SCENARIO"],19:-1.}):
        with pytest.raises(EnvelopeInputError): independent_shell_covariance(k,invalid)
    with pytest.raises(EnvelopeInputError): shared_coordinate_toy(k,zero,1.1)


def test_tiny_positive_radii_do_not_become_false_zero(source_matrices):
    _,_,k = source_matrices
    for radius in (1e-200, 1e200):
        radii = {ell: radius for ell in ELLS}
        answer = sharp_ellipsoid(k,radii)
        expected = np.linalg.norm(k,2) * radius
        assert answer["bound"] > 0
        assert answer["bound"] == pytest.approx(expected, rel=3e-13, abs=0)
        assert answer["achieved"] == pytest.approx(expected, rel=3e-13, abs=0)
        assert answer["witness_constraint"] == pytest.approx(1., rel=3e-13)
        assert answer["gram_scale"] == radius
