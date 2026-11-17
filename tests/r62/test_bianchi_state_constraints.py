"""R62 slice-constraint regressions; no ODE or Boltzmann evolution required."""
from dataclasses import replace

import numpy as np
import pytest

from bass.background.bianchi_types import build_bianchi_algebra
from bass.background.convention_bridge import (
    build_structure_tensor_with_sign, exact_momentum_divergence,
)
from bass.background.initial_conditions import CodazziProjectionError
from bass.background.tilted_bianchi_state import (
    FAMILY_ADMISSIBILITY_REGISTRY, SpeciesFluidCongruence,
    construct_admissible_tilted_state, momentum_constraint_map,
)
from bass.diagnostics.bianchi_similarity import (
    classify_bianchi_type, tilt_orbit_fingerprint,
)
from common.stf_metric_bridge import stf_matrix_to_orthonormal


def _algebra(family, a, n):
    base = build_bianchi_algebra(family)
    a, n = np.asarray(a, dtype=float), np.asarray(n, dtype=float)
    return replace(base, a=a, n=n, C=build_structure_tensor_with_sign(a, n))


def _dust_for_q(q, rho=10.0):
    q = np.asarray(q, dtype=float)
    assert np.linalg.norm(q) < rho
    beta = q / rho
    return SpeciesFluidCongruence(
        species="cdm", eps_hat=rho * (1.0 - beta @ beta),
        p_hat=0.0, v_vec=beta,
    )


def _rotation():
    axis = np.array([1.0, 2.0, -3.0]) / np.sqrt(14.0)
    x, y, z = axis
    cross = np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])
    angle = 0.73
    return np.eye(3) + np.sin(angle) * cross + (1. - np.cos(angle)) * cross @ cross


def test_nonisotropic_ix_positive_dust_counterexample_is_admitted():
    # H=1, R=4, sigma^2=s^2 => rho=5-s^2; D3=s => q3=-s.
    s = 0.1
    algebra = _algebra("IX", np.zeros(3), np.diag([1., 2., 3.]))
    sigma = np.array([[0., s, 0.], [s, 0., 0.], [0., 0., 0.]])
    source = _dust_for_q([0., 0., -s], rho=5. - s*s)
    state = construct_admissible_tilted_state(
        family="IX", algebra=algebra, H=1., closure="hold_H",
        sigma_ab=sigma, species=[source],
    )
    assert source.eps_hat > 0. and 0. < source.speed < 1.
    assert state.constraints.is_admissible
    assert state.constraints.codazzi_residual_norm < 1e-13
    assert abs(state.constraints.hamiltonian_residual) < 1e-13
    assert momentum_constraint_map(algebra).rank == 3
    # Historical representative value remains valid only for the default n.
    assert FAMILY_ADMISSIBILITY_REGISTRY["IX"].divergence_rank_on_stf5 == 0


@pytest.mark.parametrize("family", ["I", "FLRW", "IX"])
@pytest.mark.parametrize("mode", ["strict", "project_shear_to_codazzi"])
def test_zero_divergence_representatives_still_reject_net_momentum(family, mode):
    with pytest.raises(CodazziProjectionError, match="actual divergence range"):
        construct_admissible_tilted_state(
            family=family, species=[_dust_for_q([0.1, 0., 0.])], codazzi_mode=mode,
        )


def test_repeated_ix_momentum_plane_and_shear_kernel_projection():
    algebra = _algebra("IX", np.zeros(3), np.diag([1., 2., 2.]))
    m = momentum_constraint_map(algebra)
    assert m.rank == 2
    assert np.linalg.norm(m.range_projector @ [1., 0., 0.]) < 1e-14
    initial = np.array([[0.2, 0.03, 0.04], [0.03, -0.1, 0.07], [0.04, 0.07, -0.1]])
    state = construct_admissible_tilted_state(
        family="IX", algebra=algebra, sigma_ab=initial,
        species=[_dust_for_q([0., 0.1, -0.2])],
        codazzi_mode="project_shear_to_codazzi",
    )
    assert state.constraints.is_admissible
    # Diagonal shear and sigma23 span the kernel for n2=n3.
    np.testing.assert_allclose(np.diag(state.sigma_ab), np.diag(initial), atol=1e-14)
    assert state.sigma_ab[1, 2] == pytest.approx(initial[1, 2], abs=1e-14)
    s0 = stf_matrix_to_orthonormal(initial, convention="kinematic_response")
    s1 = stf_matrix_to_orthonormal(state.sigma_ab, convention="kinematic_response")
    kernel = np.eye(5) - m.pseudoinverse @ m.matrix
    np.testing.assert_allclose(kernel @ s1, kernel @ s0, atol=1e-13)
    with pytest.raises(CodazziProjectionError, match="rank=2"):
        construct_admissible_tilted_state(
            family="IX", algebra=algebra,
            species=[_dust_for_q([0.1, 0., 0.])],
            codazzi_mode="project_shear_to_codazzi",
        )


def test_exceptional_vi_minus_one_ninth_range_is_state_dependent():
    algebra = _algebra("VI_h", [1., 0., 0.], np.diag([0., 3., -3.]))
    assert classify_bianchi_type(algebra.a, algebra.n).h_parameter == pytest.approx(-1./9.)
    m = momentum_constraint_map(algebra)
    assert m.rank == 2
    # q2+q3=0 at these values, so e2+e3 is excluded.
    np.testing.assert_allclose(m.range_projector @ [0., 1., 1.], 0., atol=1e-14)
    admitted = construct_admissible_tilted_state(
        family="VI_h", algebra=algebra,
        species=[_dust_for_q([0.1, 0.2, -0.2])],
        codazzi_mode="project_shear_to_codazzi",
    )
    assert admitted.constraints.is_admissible
    with pytest.raises(CodazziProjectionError, match="rank=2"):
        construct_admissible_tilted_state(
            family="VI_h", algebra=algebra,
            species=[_dust_for_q([0., 0.1, 0.1])],
            codazzi_mode="project_shear_to_codazzi",
        )


@pytest.mark.parametrize("scale", [1e-18, 1., 1e8])
def test_momentum_rank_is_invariant_under_nonzero_structure_scale(scale):
    algebra = _algebra("IX", np.zeros(3), scale * np.diag([1., 2., 3.]))
    m = momentum_constraint_map(algebra)
    assert m.rank == 3
    np.testing.assert_allclose(m.range_projector, np.eye(3), atol=1e-14)


def test_rotated_operator_and_degenerate_strata_are_covariant():
    rotation = _rotation()
    for diagonal, rank in [([1., 1., 1.], 0), ([1., 2., 2.], 2), ([1., 2., 3.], 3)]:
        n = np.diag(diagonal)
        original = _algebra("IX", np.zeros(3), n)
        rotated = _algebra("IX", np.zeros(3), rotation @ n @ rotation.T)
        m, mr = momentum_constraint_map(original), momentum_constraint_map(rotated)
        assert m.rank == mr.rank == rank
        np.testing.assert_allclose(mr.range_projector, rotation @ m.range_projector @ rotation.T, atol=1e-13)
        sigma = np.array([[.2, .3, -.1], [.3, -.1, .4], [-.1, .4, -.1]])
        np.testing.assert_allclose(
            exact_momentum_divergence(rotation @ sigma @ rotation.T, rotated.a, rotated.n),
            rotation @ exact_momentum_divergence(sigma, original.a, original.n), atol=1e-13,
        )


def test_untilted_type_v_has_exact_shear_kernel_condition():
    # n=0 gives D=-3 sigma a. At a=e1, sigma=diag(0,s,-s) works.
    algebra = _algebra("V", [1., 0., 0.], np.zeros((3, 3)))
    sigma = np.diag([0., 0.2, -0.2])
    state = construct_admissible_tilted_state(
        family="V", algebra=algebra, sigma_ab=sigma,
        species=[_dust_for_q(np.zeros(3))],
    )
    assert momentum_constraint_map(algebra).rank == 3
    assert np.linalg.det(sigma) == 0.
    assert state.constraints.is_admissible
    with pytest.raises(CodazziProjectionError, match="Constraints violated"):
        construct_admissible_tilted_state(
            family="V", algebra=algebra, sigma_ab=np.diag([.1, .1, -.2]),
            species=[_dust_for_q(np.zeros(3))],
        )


@pytest.mark.parametrize("family", ["I", "II", "VI_0", "VII_0", "VIII", "IX"])
def test_same_shear_has_constraint_consistent_class_a_slice_candidates(family):
    # Every canonical Class A n commutes with this same diagonal shear.
    sigma = np.diag([.2, .1, -.3])
    state = construct_admissible_tilted_state(
        family=family, sigma_ab=sigma, species=[_dust_for_q(np.zeros(3))],
    )
    assert state.constraints.is_admissible
    np.testing.assert_allclose(state.sigma_ab, sigma, atol=1e-14)
    np.testing.assert_allclose(state.total_matter.q, 0., atol=1e-14)


def test_requested_family_cannot_hide_a_different_supplied_algebra():
    with pytest.raises(ValueError, match="inconsistent"):
        construct_admissible_tilted_state(
            family="I", algebra=_algebra("IX", np.zeros(3), np.diag([1., 2., 3.])),
            species=[_dust_for_q(np.zeros(3))],
        )


@pytest.mark.parametrize("beta,expected", [([0., 0., 0.], 0), ([.2, 0., 0.], 1), ([.2, .1, 0.], 2), ([.2, .1, .3], 3)])
def test_moment_jacobian_uses_actual_tilt(beta, expected):
    n, a = np.diag([1., 2., 3.]), np.zeros(3)
    fp = tilt_orbit_fingerprint(a, n, beta)
    assert fp.moment_rank == 3
    assert fp.moment_jacobian_rank == expected
    rotation = _rotation()
    rotated = tilt_orbit_fingerprint(a, rotation @ n @ rotation.T, rotation @ beta)
    assert rotated.moment_jacobian_rank == expected


@pytest.mark.parametrize("beta,expected", [([.2, 0., 0.], 1), ([0., .2, .1], 1), ([.2, .2, .1], 2)])
def test_repeated_eigenspaces_have_one_moment_derivative_per_occupied_eigenspace(beta, expected):
    fp = tilt_orbit_fingerprint(np.zeros(3), np.diag([1., 2., 2.]), beta)
    assert fp.moment_rank == 2
    assert fp.moment_jacobian_rank == expected


def test_repeated_eigenspace_azimuth_is_stabilizer_gauge():
    n, a = np.diag([1., 2., 2.]), np.zeros(3)
    beta = np.array([.1, .2, .3])
    angle = 0.8
    stabilizer = np.array([[1., 0., 0.], [0., np.cos(angle), -np.sin(angle)], [0., np.sin(angle), np.cos(angle)]])
    np.testing.assert_allclose(stabilizer @ n @ stabilizer.T, n, atol=1e-14)
    left, right = tilt_orbit_fingerprint(a, n, beta), tilt_orbit_fingerprint(a, n, stabilizer @ beta)
    np.testing.assert_allclose([left.speed_squared, left.p1, left.p2], [right.speed_squared, right.p1, right.p2], atol=1e-14)
    assert left.stabilizer_orbit_dimension == left.continuous_azimuth_degeneracy_dof == 1
    isotropic = tilt_orbit_fingerprint(a, np.eye(3), beta)
    assert isotropic.stabilizer_orbit_dimension == 2
    assert isotropic.moment_jacobian_rank == 1
