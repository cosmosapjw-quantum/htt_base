from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import ALL_BIANCHI_TYPES, all_bianchi_algebras, build_bianchi_algebra
from bass.background.geometry import (
    build_geometry,
    connection_from_commutators,
    covariant_derivative_rank2_homogeneous,
    curl_pstf2,
    div_pstf2,
    spatial_ricci_from_compact_formula,
    spatial_ricci_from_connection,
)
from bass.background.initial_conditions import _ORTHONORMAL_PSTF_BASIS, _codazzi_operator_matrix


ALL_LABELS = ["FLRW", *ALL_BIANCHI_TYPES]


@pytest.mark.parametrize("label", ALL_LABELS)
def test_ver2_algebra_builds_for_every_type(label):
    algebra = build_bianchi_algebra(label)
    assert algebra.type_name == label
    assert algebra.C.shape == (3, 3, 3)
    assert algebra.antisymmetry_residual_norm < 1e-12
    assert algebra.jacobi_residual_norm < 1e-12


def test_ver2_registry_covers_flrw_plus_eleven_types():
    registry = all_bianchi_algebras()
    assert set(registry) == set(ALL_LABELS)


@pytest.mark.parametrize("label", ["III", "IV", "V", "VI_h", "VII_h"])
def test_class_b_algebra_uses_ver2_canonical_axis(label):
    algebra = build_bianchi_algebra(label)
    assert algebra.class_label == "B"
    assert algebra.axis_permutation == (1, 0, 2)
    assert algebra.a[0] > 0.0
    assert algebra.a[1] == pytest.approx(0.0)
    assert algebra.n[0, 0] == pytest.approx(0.0)


@pytest.mark.parametrize("label", ["FLRW", "I", "II", "VI_0", "VII_0", "VIII", "IX"])
def test_class_a_algebra_keeps_identity_axis_metadata(label):
    algebra = build_bianchi_algebra(label)
    assert algebra.class_label == "A"
    assert algebra.axis_permutation == (0, 1, 2)
    assert np.allclose(algebra.a, 0.0)


@pytest.mark.parametrize("label", ALL_LABELS)
def test_geometry_torsion_relation_matches_commutator_tensor(label):
    geometry = build_geometry(build_bianchi_algebra(label))
    assert geometry.torsion_residual_norm < 1e-12


def test_flrw_geometry_is_exactly_flat():
    geometry = build_geometry(build_bianchi_algebra("FLRW"))
    assert np.allclose(geometry.Gamma, 0.0)
    assert np.allclose(geometry.ricci_tensor, 0.0)
    assert geometry.ricci_scalar == pytest.approx(0.0)
    assert np.allclose(geometry.ricci_pstf, 0.0)


def test_type_ix_isotropic_geometry_has_zero_pstf_ricci():
    geometry = build_geometry(build_bianchi_algebra("IX", n=1.0e-2))
    assert np.allclose(geometry.ricci_pstf, 0.0, atol=1e-15)
    assert np.allclose(geometry.compact_ricci_pstf, 0.0, atol=1e-15)


@pytest.mark.parametrize("label", ["I", "V", "IX"])
def test_dual_route_curvature_matches_for_named_ver3_branches(label):
    geometry = build_geometry(build_bianchi_algebra(label))
    assert geometry.dual_route_status == "AVAILABLE"
    assert geometry.dual_route_curvature_residual_norm < 1.0e-12
    np.testing.assert_allclose(geometry.ricci_tensor, geometry.compact_ricci_tensor)


def test_type_v_connection_route_is_isotropic_open_curvature():
    geometry = build_geometry(build_bianchi_algebra("V"))
    expected = -(2.0e-4) * np.eye(3, dtype=np.float64)
    np.testing.assert_allclose(geometry.ricci_tensor, expected, atol=1.0e-15)
    assert geometry.ricci_scalar == pytest.approx(-6.0e-4)
    assert np.allclose(geometry.ricci_pstf, 0.0, atol=1.0e-15)


@pytest.mark.parametrize("label", ["V", "IX"])
def test_geometry_scaling_regression_is_quadratic_in_algebra_scale(label):
    algebra = build_bianchi_algebra(label)
    geometry_1 = build_geometry(algebra)
    geometry_2 = build_geometry(build_bianchi_algebra(label, **({"n": 2.0e-2} if label == "IX" else {"a_twist": 2.0e-2})))
    np.testing.assert_allclose(geometry_2.ricci_tensor, 4.0 * geometry_1.ricci_tensor, atol=1.0e-15)
    assert geometry_2.ricci_scalar == pytest.approx(4.0 * geometry_1.ricci_scalar)


def test_type_i_homogeneous_diagonal_sigma_has_zero_divergence_and_curl():
    geometry = build_geometry(build_bianchi_algebra("I"))
    sigma = np.diag([1.0e-3, -5.0e-4, -5.0e-4])
    assert np.allclose(div_pstf2(sigma, geometry.Gamma), 0.0)
    assert np.allclose(curl_pstf2(sigma, geometry.Gamma), 0.0)


@pytest.mark.parametrize("label", ["VII_0", "VIII"])
def test_rank2_covariant_derivative_matches_ver2_sdd_definition(label):
    geometry = build_geometry(build_bianchi_algebra(label))
    sigma = _ORTHONORMAL_PSTF_BASIS[2] + 0.5 * _ORTHONORMAL_PSTF_BASIS[4]
    expected = np.zeros((3, 3, 3), dtype=np.float64)
    for gamma in range(3):
        for alpha in range(3):
            for beta in range(3):
                for mu in range(3):
                    expected[gamma, alpha, beta] -= geometry.Gamma[mu, alpha, gamma] * sigma[mu, beta]
                    expected[gamma, alpha, beta] -= geometry.Gamma[mu, beta, gamma] * sigma[alpha, mu]
    np.testing.assert_allclose(
        covariant_derivative_rank2_homogeneous(sigma, geometry.Gamma),
        expected,
    )


def test_connection_from_commutators_matches_build_geometry_route():
    algebra = build_bianchi_algebra("VIII")
    geometry = build_geometry(algebra)
    np.testing.assert_allclose(connection_from_commutators(algebra.C), geometry.Gamma)


@pytest.mark.parametrize("label", ["II", "V", "VIII"])
def test_explicit_route_helpers_match_build_geometry_bundle(label):
    algebra = build_bianchi_algebra(label)
    geometry = build_geometry(algebra)
    ricci_a, scalar_a, pstf_a = spatial_ricci_from_connection(algebra.C, Gamma=geometry.Gamma)
    ricci_b, scalar_b, pstf_b = spatial_ricci_from_compact_formula(algebra)
    np.testing.assert_allclose(ricci_a, geometry.ricci_tensor)
    assert scalar_a == pytest.approx(geometry.ricci_scalar)
    np.testing.assert_allclose(pstf_a, geometry.ricci_pstf)
    np.testing.assert_allclose(ricci_b, geometry.compact_ricci_tensor)
    assert scalar_b == pytest.approx(geometry.compact_ricci_scalar)
    np.testing.assert_allclose(pstf_b, geometry.compact_ricci_pstf)


@pytest.mark.parametrize("label", ["VII_0", "VIII"])
def test_class_a_helical_and_semisimple_codazzi_operator_is_nontrivial(label):
    geometry = build_geometry(build_bianchi_algebra(label))
    operator = _codazzi_operator_matrix(geometry)
    assert np.linalg.matrix_rank(operator) >= 2


def test_branch_policy_is_explicit_for_type_i_tilt():
    algebra = build_bianchi_algebra("I")
    assert algebra.supports_branch("orthogonal")
    assert algebra.supports_branch("tilted")
    assert algebra.branch_policy.constraint_policy_required == "codazzi_balanced_total_momentum"


def test_branch_policy_is_explicit_for_type_ix_tilt_domain():
    algebra = build_bianchi_algebra("IX")
    assert algebra.supports_branch("orthogonal")
    assert algebra.supports_branch("tilted")
    assert algebra.branch_policy.constraint_policy_required == "config_domain_restricted_tilt"
