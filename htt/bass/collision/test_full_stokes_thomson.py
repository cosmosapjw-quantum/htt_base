from __future__ import annotations

import numpy as np
import pytest

from bass.collision import (
    build_full_stokes_mueller_kernel,
    build_full_stokes_temperature_kernel,
    exact_thomson_gate_bundle,
    full_stokes_mueller_collision,
    full_stokes_temperature_collision,
    full_stokes_thomson_source,
    rotate_screen_basis,
    rotate_stokes_samples,
)
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import TiltedSpeciesBackground
from bass.collision.polarization import zero_polarization_hierarchy
from bass.collision.thomson_pstf import ThomsonPSTFCollisionOperator
from bass.hierarchy.ver2_native_integrator import (
    _EProjectedCollision,
    _BProjectedCollision,
    _ProjectedCollisionAux,
    _TemperatureProjectedCollision,
)
from bass.hierarchy.pstf_radiation import (
    RadiationPSTFState,
    TruncationMetadata,
    project_from_angular_samples,
    reconstruct_on_sphere,
)
from bass.hierarchy.pstf_tensor import PSTFTensor, zero_hierarchy


def _octahedral_grid() -> tuple[np.ndarray, np.ndarray]:
    directions = np.array(
        [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
        ],
        dtype=np.float64,
    )
    weights = np.full(6, 4.0 * np.pi / 6.0, dtype=np.float64)
    return directions, weights


def _tensor_product_sphere_rule(L: int) -> tuple[np.ndarray, np.ndarray]:
    mu, mu_weights = np.polynomial.legendre.leggauss(2 * int(L) + 3)
    n_phi = 4 * int(L) + 5
    phi = np.linspace(0.0, 2.0 * np.pi, n_phi, endpoint=False, dtype=np.float64)
    directions: list[list[float]] = []
    weights: list[float] = []
    for mu_i, w_i in zip(mu, mu_weights):
        sin_theta = float(np.sqrt(max(0.0, 1.0 - float(mu_i) * float(mu_i))))
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


@pytest.fixture(scope="module")
def registry() -> SpeciesBackgroundRegistry:
    return SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")


def test_full_stokes_thomson_preserves_isotropic_unpolarized_null_collision() -> None:
    directions, weights = _octahedral_grid()
    source = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=np.full(6, 2.5),
        Q=np.zeros(6),
        U=np.zeros(6),
        Gamma_T=7.0,
    )
    np.testing.assert_allclose(source.source_I, 2.5, atol=1.0e-14)
    np.testing.assert_allclose(source.source_Q, 0.0, atol=1.0e-14)
    np.testing.assert_allclose(source.source_U, 0.0, atol=1.0e-14)
    np.testing.assert_allclose(source.collision_I, 0.0, atol=1.0e-13)
    np.testing.assert_allclose(source.collision_Q, 0.0, atol=1.0e-13)
    np.testing.assert_allclose(source.collision_U, 0.0, atol=1.0e-13)


def test_full_stokes_thomson_recovers_90_degree_rayleigh_polarization() -> None:
    directions = np.array(
        [
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 0.0],
        ],
        dtype=np.float64,
    )
    weights = np.array([0.0, 1.0], dtype=np.float64)
    source = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=np.array([0.0, 1.0], dtype=np.float64),
        Q=np.zeros(2),
        U=np.zeros(2),
        Gamma_T=1.0,
        basis_u=np.array(
            [
                [1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        ),
        basis_v=np.array(
            [
                [0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0],
            ],
            dtype=np.float64,
        ),
    )
    assert source.source_I[0] > 0.0
    assert abs(source.source_Q[0] / source.source_I[0]) == pytest.approx(1.0)
    assert source.source_U[0] == pytest.approx(0.0, abs=1.0e-14)


def test_full_stokes_thomson_uses_directional_tilt_opacity(
    registry: SpeciesBackgroundRegistry,
) -> None:
    directions, weights = _octahedral_grid()
    tilted_electron = TiltedSpeciesBackground(
        base=registry[SpeciesLabel.BARYON],
        beta=0.2,
        v_hat_e=(0.0, 0.0, 1.0),
    )
    source = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=np.ones(6),
        Q=np.zeros(6),
        U=np.zeros(6),
        Gamma_T=3.0,
        tilted_electron=tilted_electron,
    )
    plus_z = 4
    minus_z = 5
    assert source.effective_opacity[plus_z] == pytest.approx(
        3.0 * tilted_electron.gamma * (1.0 - tilted_electron.beta)
    )
    assert source.effective_opacity[minus_z] == pytest.approx(
        3.0 * tilted_electron.gamma * (1.0 + tilted_electron.beta)
    )


def test_full_stokes_thomson_gate_opens_tilted_authority_path(
    registry: SpeciesBackgroundRegistry,
) -> None:
    directions, weights = _octahedral_grid()
    tilted_electron = TiltedSpeciesBackground(
        base=registry[SpeciesLabel.BARYON],
        beta=0.15,
        v_hat_e=(0.0, 0.0, 1.0),
    )
    source = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=np.ones(6),
        Q=np.zeros(6),
        U=np.zeros(6),
        Gamma_T=2.0,
        tilted_electron=tilted_electron,
    )
    bundle = exact_thomson_gate_bundle(source, family="I", branch="tilted")
    assert bundle.passed is True
    assert bundle.known_limit_checks["full_tilted_stokes_authority"] is True
    assert bundle.known_limit_checks["screen_basis_orthonormal"] is True
    assert bundle.known_limit_checks["angular_quadrature_weights_normalized"] is True
    assert bundle.metadata["operator_scope"] == "full_electron_frame_stokes"
    assert bundle.metadata["angular_grid_size"] == 6


def test_full_stokes_thomson_gate_blocks_tilted_branch_without_directional_opacity() -> None:
    directions, weights = _octahedral_grid()
    source = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=np.ones(6),
        Q=np.zeros(6),
        U=np.zeros(6),
        Gamma_T=2.0,
    )
    bundle = exact_thomson_gate_bundle(source, family="I", branch="tilted")
    assert bundle.passed is False
    assert bundle.known_limit_checks["full_tilted_stokes_authority"] is True
    assert bundle.known_limit_checks["tilted_branch_requires_directional_opacity"] is False


def test_full_stokes_thomson_is_linear_in_incoming_stokes_fields() -> None:
    directions, weights = _octahedral_grid()
    first = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=np.linspace(0.2, 1.2, 6),
        Q=np.linspace(-0.1, 0.2, 6),
        U=np.linspace(0.05, -0.15, 6),
        Gamma_T=1.0,
    )
    second = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=np.linspace(1.0, 0.4, 6),
        Q=np.linspace(0.3, -0.2, 6),
        U=np.linspace(-0.08, 0.12, 6),
        Gamma_T=1.0,
    )
    combined = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=np.linspace(0.2, 1.2, 6) + np.linspace(1.0, 0.4, 6),
        Q=np.linspace(-0.1, 0.2, 6) + np.linspace(0.3, -0.2, 6),
        U=np.linspace(0.05, -0.15, 6) + np.linspace(-0.08, 0.12, 6),
        Gamma_T=1.0,
    )
    np.testing.assert_allclose(combined.source_I, first.source_I + second.source_I)
    np.testing.assert_allclose(combined.source_Q, first.source_Q + second.source_Q)
    np.testing.assert_allclose(
        combined.source_U,
        first.source_U + second.source_U,
        atol=1.0e-15,
    )


def test_full_stokes_thomson_conserves_angle_integrated_intensity_without_tilt() -> None:
    directions, weights = _tensor_product_sphere_rule(4)
    x = directions[:, 0]
    y = directions[:, 1]
    z = directions[:, 2]
    source = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=1.0 + 0.2 * x + 0.1 * (3.0 * z * z - 1.0),
        Q=0.05 * (x * x - y * y),
        U=0.03 * x * y,
        Gamma_T=2.0,
    )

    np.testing.assert_allclose(
        float(np.dot(weights, source.collision_I)),
        0.0,
        atol=2.0e-13,
    )


def test_full_stokes_intensity_projection_matches_pstf_thomson_quadrupole_operator() -> None:
    L = 4
    gamma_t = 5.0
    directions, weights = _tensor_product_sphere_rule(L)
    temperature_state = zero_hierarchy(L)
    quadrupole = np.array([0.3, -0.2, 1.0, 0.4, -0.5], dtype=np.float64)
    temperature_state.tensors[2] = PSTFTensor(ell=2, components=quadrupole)
    polarization_state = zero_polarization_hierarchy(L)
    radiation_state = RadiationPSTFState(
        I=temperature_state,
        E=polarization_state,
        B=zero_hierarchy(L),
        truncation=TruncationMetadata(L=L, allow_L2_override=True),
    )
    intensity = reconstruct_on_sphere(radiation_state, directions)["I"]
    angular = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=intensity,
        Q=np.zeros_like(intensity),
        U=np.zeros_like(intensity),
        Gamma_T=gamma_t,
    )
    projected_collision = project_from_angular_samples(
        {"I": angular.collision_I},
        directions,
        weights,
        L=L,
        truncation=TruncationMetadata(L=L, allow_L2_override=True),
    )
    pstf_collision = ThomsonPSTFCollisionOperator().evaluate_tower(
        temperature_state,
        polarization_state,
        np.zeros(3),
        gamma_t,
    )
    np.testing.assert_allclose(
        projected_collision.I.as_flat(),
        pstf_collision.as_flat(),
        atol=8.0e-14,
    )


def test_cached_temperature_kernel_matches_full_stokes_temperature_channel(
    registry: SpeciesBackgroundRegistry,
) -> None:
    directions, weights = _tensor_product_sphere_rule(3)
    tilted_electron = TiltedSpeciesBackground(
        base=registry[SpeciesLabel.BARYON],
        beta=0.12,
        v_hat_e=(1.0 / np.sqrt(2.0), 0.0, 1.0 / np.sqrt(2.0)),
    )
    I = 1.0 + 0.1 * directions[:, 0] + 0.05 * directions[:, 2] ** 2
    Q = 0.02 * (directions[:, 0] ** 2 - directions[:, 1] ** 2)
    U = 0.03 * directions[:, 0] * directions[:, 1]
    full = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=I,
        Q=Q,
        U=U,
        Gamma_T=3.0,
        tilted_electron=tilted_electron,
    )
    kernel = build_full_stokes_temperature_kernel(
        directions=directions,
        weights=weights,
    )
    cached = full_stokes_temperature_collision(
        kernel=kernel,
        I=I,
        Q=Q,
        U=U,
        Gamma_T=3.0,
        tilted_electron=tilted_electron,
    )

    np.testing.assert_allclose(cached.source_I, full.source_I, atol=1.0e-13)
    np.testing.assert_allclose(cached.collision_I, full.collision_I, atol=1.0e-13)
    np.testing.assert_allclose(cached.effective_opacity, full.effective_opacity)


def test_cached_mueller_kernel_matches_full_stokes_all_channels(
    registry: SpeciesBackgroundRegistry,
) -> None:
    directions, weights = _tensor_product_sphere_rule(3)
    tilted_electron = TiltedSpeciesBackground(
        base=registry[SpeciesLabel.BARYON],
        beta=0.08,
        v_hat_e=(0.0, 1.0 / np.sqrt(2.0), 1.0 / np.sqrt(2.0)),
    )
    I = 1.0 + 0.07 * directions[:, 0] + 0.04 * directions[:, 2] ** 2
    Q = 0.03 * (directions[:, 0] ** 2 - directions[:, 1] ** 2)
    U = -0.025 * directions[:, 1] * directions[:, 2]
    full = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=I,
        Q=Q,
        U=U,
        Gamma_T=2.5,
        tilted_electron=tilted_electron,
    )
    kernel = build_full_stokes_mueller_kernel(
        directions=directions,
        weights=weights,
    )
    cached = full_stokes_mueller_collision(
        kernel=kernel,
        I=I,
        Q=Q,
        U=U,
        Gamma_T=2.5,
        tilted_electron=tilted_electron,
    )

    np.testing.assert_allclose(cached.source_I, full.source_I, atol=1.0e-13)
    np.testing.assert_allclose(cached.source_Q, full.source_Q, atol=1.0e-13)
    np.testing.assert_allclose(cached.source_U, full.source_U, atol=1.0e-13)
    np.testing.assert_allclose(cached.collision_I, full.collision_I, atol=1.0e-13)
    np.testing.assert_allclose(cached.collision_Q, full.collision_Q, atol=1.0e-13)
    np.testing.assert_allclose(cached.collision_U, full.collision_U, atol=1.0e-13)


def test_full_stokes_thomson_is_covariant_under_screen_basis_rotation() -> None:
    directions, weights = _tensor_product_sphere_rule(3)
    reference_kernel = build_full_stokes_mueller_kernel(
        directions=directions,
        weights=weights,
    )
    I = 1.0 + 0.05 * directions[:, 0] - 0.04 * directions[:, 2]
    Q = 0.02 * (directions[:, 0] ** 2 - directions[:, 1] ** 2)
    U = 0.03 * directions[:, 1] * directions[:, 2]
    rotated_u, rotated_v = rotate_screen_basis(
        directions,
        reference_kernel.basis_u,
        reference_kernel.basis_v,
        angle=0.37,
    )
    rotated_Q, rotated_U = rotate_stokes_samples(
        Q,
        U,
        reference_kernel.basis_u,
        reference_kernel.basis_v,
        rotated_u,
        rotated_v,
    )
    reference = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=I,
        Q=Q,
        U=U,
        Gamma_T=2.0,
        basis_u=reference_kernel.basis_u,
        basis_v=reference_kernel.basis_v,
    )
    rotated = full_stokes_thomson_source(
        directions=directions,
        weights=weights,
        I=I,
        Q=rotated_Q,
        U=rotated_U,
        Gamma_T=2.0,
        basis_u=rotated_u,
        basis_v=rotated_v,
    )
    expected_source_Q, expected_source_U = rotate_stokes_samples(
        reference.source_Q,
        reference.source_U,
        reference.basis_u,
        reference.basis_v,
        rotated_u,
        rotated_v,
    )
    expected_collision_Q, expected_collision_U = rotate_stokes_samples(
        reference.collision_Q,
        reference.collision_U,
        reference.basis_u,
        reference.basis_v,
        rotated_u,
        rotated_v,
    )

    np.testing.assert_allclose(rotated.source_I, reference.source_I, atol=1.0e-13)
    np.testing.assert_allclose(rotated.collision_I, reference.collision_I, atol=1.0e-13)
    np.testing.assert_allclose(rotated.source_Q, expected_source_Q, atol=1.0e-13)
    np.testing.assert_allclose(rotated.source_U, expected_source_U, atol=1.0e-13)
    np.testing.assert_allclose(rotated.collision_Q, expected_collision_Q, atol=1.0e-13)
    np.testing.assert_allclose(rotated.collision_U, expected_collision_U, atol=1.0e-13)


def test_tilted_runtime_collision_aux_uses_full_stokes_spin2_qu_rhs(
    registry: SpeciesBackgroundRegistry,
) -> None:
    L = 4
    temperature_state = zero_hierarchy(L)
    temperature_state.tensors[1] = PSTFTensor(
        ell=1,
        components=np.array([0.04, -0.02, 0.03], dtype=np.float64),
    )
    temperature_state.tensors[2] = PSTFTensor(
        ell=2,
        components=np.array([0.2, -0.1, 0.7, 0.05, -0.3], dtype=np.float64),
    )
    polarization_state = zero_polarization_hierarchy(L)
    tilted_electron = TiltedSpeciesBackground(
        base=registry[SpeciesLabel.BARYON],
        beta=0.18,
        v_hat_e=(0.0, 0.0, 1.0),
    )
    common = dict(
        eta=0.0,
        temperature_state=temperature_state,
        polarization_state=polarization_state,
        Gamma_T=4.0,
        direction=np.array([0.0, 0.0, 1.0], dtype=np.float64),
        v_b_real_sph=np.zeros(3, dtype=np.float64),
        b_state=zero_hierarchy(L),
    )
    orthogonal_aux = _ProjectedCollisionAux(
        **common,
        tilted_electron=None,
    )
    tilted_aux = _ProjectedCollisionAux(
        **common,
        tilted_electron=tilted_electron,
    )

    orthogonal_source = orthogonal_aux.get_source()
    tilted_source = tilted_aux.get_source()

    assert orthogonal_source.operator_scope == "linear_classical_thomson_boosted_pstf"
    assert (
        tilted_source.operator_scope
        == "full_stokes_spin2_angular_polarization"
    )
    assert np.linalg.norm(
        tilted_source.temperature.as_flat() - orthogonal_source.temperature.as_flat()
    ) > 1.0e-6
    assert np.linalg.norm(tilted_source.polarization_E.E.as_flat()) > 0.0
    assert np.all(np.isfinite(tilted_source.polarization_B.as_flat()))
    np.testing.assert_allclose(
        _TemperatureProjectedCollision().evaluate(2, temperature_state, tilted_aux).components,
        tilted_source.temperature.tensors[2].components,
        atol=1.0e-14,
    )
    np.testing.assert_allclose(
        _EProjectedCollision().evaluate(2, temperature_state, tilted_aux).components,
        tilted_source.polarization_E.E.tensors[2].components,
        atol=1.0e-14,
    )
    np.testing.assert_allclose(
        _BProjectedCollision().evaluate(2, temperature_state, tilted_aux).components,
        tilted_source.polarization_B.tensors[2].components,
        atol=1.0e-14,
    )
