from __future__ import annotations

import numpy as np
import pytest

from bass.collision import rotate_screen_basis, rotate_stokes_samples
from bass.collision.polarization import PolarizationHierarchyState
from bass.hierarchy import (
    PSTFHierarchyState,
    PSTFTensor,
    build_spin2_projection_kernel,
    project_spin2_qu_to_eb,
    project_spin2_qu_to_eb_with_kernel,
    reconstruct_spin2_qu_from_eb,
    reconstruct_spin2_qu_from_eb_with_kernel,
    spherical_screen_basis,
    spin_weighted_spherical_harmonic,
    zero_hierarchy,
    zero_pstf,
)


def _spin2_sphere_rule(L: int) -> tuple[np.ndarray, np.ndarray]:
    mu, mu_weights = np.polynomial.legendre.leggauss(3 * L + 5)
    n_phi = 6 * L + 7
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False)
    directions = []
    weights = []
    for mu_i, w_i in zip(mu, mu_weights):
        sin_theta = float(np.sqrt(max(0.0, 1.0 - mu_i * mu_i)))
        for phi_j in phi:
            directions.append(
                [
                    sin_theta * float(np.cos(phi_j)),
                    sin_theta * float(np.sin(phi_j)),
                    float(mu_i),
                ]
            )
            weights.append(float(w_i) * (2.0 * np.pi / float(n_phi)))
    return np.asarray(directions, dtype=np.float64), np.asarray(weights, dtype=np.float64)


def _theta_phi(directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    theta = np.arccos(np.clip(directions[:, 2], -1.0, 1.0))
    phi = np.mod(np.arctan2(directions[:, 1], directions[:, 0]), 2.0 * np.pi)
    return theta, phi


def _random_spin2_tower(L: int, *, seed: int) -> PSTFHierarchyState:
    rng = np.random.default_rng(seed)
    tensors = [zero_pstf(0), zero_pstf(1)]
    for ell in range(2, L + 1):
        tensors.append(PSTFTensor(ell=ell, components=rng.normal(size=2 * ell + 1)))
    return PSTFHierarchyState(L=L, tensors=tensors)


def _assert_towers_close(
    actual: PSTFHierarchyState,
    expected: PSTFHierarchyState,
    *,
    atol: float = 3.0e-11,
) -> None:
    np.testing.assert_allclose(actual.as_flat(), expected.as_flat(), rtol=0.0, atol=atol)


def test_spin_weighted_harmonics_are_orthonormal_on_solver_quadrature() -> None:
    L = 5
    directions, weights = _spin2_sphere_rule(L)
    theta, phi = _theta_phi(directions)
    for spin in (-2, 2):
        columns = []
        for ell in range(2, L + 1):
            for m in range(-ell, ell + 1):
                columns.append(spin_weighted_spherical_harmonic(ell, m, spin, theta, phi))
        basis = np.stack(columns, axis=1)
        gram = basis.conj().T @ (weights[:, None] * basis)
        np.testing.assert_allclose(gram, np.eye(gram.shape[0]), rtol=0.0, atol=8.0e-14)


def test_spin2_projection_roundtrips_bandlimited_eb_content() -> None:
    L = 5
    directions, weights = _spin2_sphere_rule(L)
    e_tower = _random_spin2_tower(L, seed=13)
    b_tower = _random_spin2_tower(L, seed=17)
    samples = reconstruct_spin2_qu_from_eb(
        PolarizationHierarchyState(E=e_tower),
        b_tower,
        directions,
    )
    recovered = project_spin2_qu_to_eb(
        samples["Q"],
        samples["U"],
        directions,
        weights,
        L=L,
    )
    _assert_towers_close(recovered.E.E, e_tower)
    _assert_towers_close(recovered.B, b_tower)
    assert recovered.metadata.basis_contract == "spherical_screen_basis_spin2_harmonic"


def test_spin2_projection_keeps_pure_e_from_leaking_into_b() -> None:
    L = 4
    directions, weights = _spin2_sphere_rule(L)
    e_tower = _random_spin2_tower(L, seed=23)
    b_tower = zero_hierarchy(L)
    samples = reconstruct_spin2_qu_from_eb(
        PolarizationHierarchyState(E=e_tower),
        b_tower,
        directions,
    )
    recovered = project_spin2_qu_to_eb(
        samples["Q"],
        samples["U"],
        directions,
        weights,
        L=L,
    )
    assert np.linalg.norm(recovered.E.E.as_flat()) > 1.0e-3
    _assert_towers_close(recovered.E.E, e_tower)
    np.testing.assert_allclose(recovered.B.as_flat(), 0.0, rtol=0.0, atol=2.0e-11)


def test_spin2_projection_is_covariant_under_screen_basis_rotation() -> None:
    L = 4
    directions, weights = _spin2_sphere_rule(L)
    e_tower = _random_spin2_tower(L, seed=31)
    b_tower = _random_spin2_tower(L, seed=37)
    basis_u, basis_v = spherical_screen_basis(directions)
    samples = reconstruct_spin2_qu_from_eb(
        PolarizationHierarchyState(E=e_tower),
        b_tower,
        directions,
        basis_u=basis_u,
        basis_v=basis_v,
    )
    rotated_u, rotated_v = rotate_screen_basis(directions, basis_u, basis_v, 0.41)
    rotated_q, rotated_u_samples = rotate_stokes_samples(
        samples["Q"],
        samples["U"],
        basis_u,
        basis_v,
        rotated_u,
        rotated_v,
    )
    recovered = project_spin2_qu_to_eb(
        rotated_q,
        rotated_u_samples,
        directions,
        weights,
        L=L,
        basis_u=rotated_u,
        basis_v=rotated_v,
    )
    _assert_towers_close(recovered.E.E, e_tower)
    _assert_towers_close(recovered.B, b_tower)


def test_cached_spin2_projection_kernel_preserves_uncached_physics() -> None:
    L = 4
    directions, weights = _spin2_sphere_rule(L)
    basis_u, basis_v = spherical_screen_basis(directions)
    rotated_u, rotated_v = rotate_screen_basis(directions, basis_u, basis_v, 0.29)
    e_tower = _random_spin2_tower(L, seed=41)
    b_tower = _random_spin2_tower(L, seed=43)
    uncached_samples = reconstruct_spin2_qu_from_eb(
        PolarizationHierarchyState(E=e_tower),
        b_tower,
        directions,
        basis_u=rotated_u,
        basis_v=rotated_v,
    )
    uncached_projection = project_spin2_qu_to_eb(
        uncached_samples["Q"],
        uncached_samples["U"],
        directions,
        weights,
        L=L,
        basis_u=rotated_u,
        basis_v=rotated_v,
    )

    kernel = build_spin2_projection_kernel(
        directions,
        weights,
        L=L,
        basis_u=rotated_u,
        basis_v=rotated_v,
    )
    cached_samples = reconstruct_spin2_qu_from_eb_with_kernel(
        PolarizationHierarchyState(E=e_tower),
        b_tower,
        kernel,
    )
    cached_projection = project_spin2_qu_to_eb_with_kernel(
        cached_samples["Q"],
        cached_samples["U"],
        kernel,
    )

    np.testing.assert_allclose(
        cached_samples["Q"],
        uncached_samples["Q"],
        rtol=0.0,
        atol=1.0e-13,
    )
    np.testing.assert_allclose(
        cached_samples["U"],
        uncached_samples["U"],
        rtol=0.0,
        atol=1.0e-13,
    )
    _assert_towers_close(cached_projection.E.E, uncached_projection.E.E)
    _assert_towers_close(cached_projection.B, uncached_projection.B)


def test_spin2_projection_rejects_scalar_quadrature_drift() -> None:
    L = 3
    directions, weights = _spin2_sphere_rule(L)
    broken = weights.copy()
    broken[0] *= 1.02
    broken *= (4.0 * np.pi) / float(np.sum(broken))
    samples = {
        "Q": np.zeros(directions.shape[0], dtype=np.float64),
        "U": np.zeros(directions.shape[0], dtype=np.float64),
    }
    with pytest.raises(ValueError, match="spin-2 harmonic orthonormality"):
        project_spin2_qu_to_eb(samples["Q"], samples["U"], directions, broken, L=L)
