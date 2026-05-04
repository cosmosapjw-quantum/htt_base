from __future__ import annotations

import math

import numpy as np
import pytest

from bass.collision import (
    ElectronFrameThomsonContext,
    electron_frame_rate_factor,
    project_thomson_source,
)
from bass.collision.tilted_eb_mixing import evaluate_tilted_polarization_eb_collision
from bass.collision.tilted_thomson_layer_b import evaluate_tilted_thomson_pstf_collision
from bass.collision._tilted_layer_b_common import apply_axisymmetric_boost_to_tower
from bass.collision.polarization import zero_polarization_hierarchy
from bass.species.base import SpeciesBackground, SpeciesLabel, _as_1d, _squeeze_if_scalar
from bass.species.tilted import TiltedSpeciesBackground
from bass.hierarchy.pstf_tensor import PSTFTensor, PSTFHierarchyState, zero_hierarchy


def _tower_with_quadrupole(value: float, *, L: int = 3) -> PSTFHierarchyState:
    state = zero_hierarchy(L)
    state.tensors[2] = PSTFTensor(ell=2, components=np.array([0.0, 0.0, value, 0.0, 0.0]))
    return state


class _DummySpecies(SpeciesBackground):
    label = SpeciesLabel.BARYON

    def rho_rest(self, eta):
        arr, scalar = _as_1d(eta)
        return _squeeze_if_scalar(np.ones_like(arr), scalar)

    def p_rest(self, eta):
        arr, scalar = _as_1d(eta)
        return _squeeze_if_scalar(np.zeros_like(arr), scalar)

    def dot_rho(self, eta):
        arr, scalar = _as_1d(eta)
        return _squeeze_if_scalar(np.zeros_like(arr), scalar)

    def _a_of_eta(self, eta):
        arr, scalar = _as_1d(eta)
        return _squeeze_if_scalar(np.ones_like(arr), scalar)


def _tilted_species(beta: float, v_hat_e: tuple[float, float, float]) -> TiltedSpeciesBackground:
    return TiltedSpeciesBackground(
        base=_DummySpecies(),
        beta=beta,
        v_hat_e=v_hat_e,
    )


def test_electron_frame_rate_factor_uses_propagation_convention() -> None:
    rate = electron_frame_rate_factor(
        gamma_e=1.25,
        v_dot_direction=0.2,
        convention=ElectronFrameThomsonContext().direction_convention,
    )
    assert rate.factor == pytest.approx(1.25 * 0.8)


def test_electron_frame_rate_factor_uses_sky_convention() -> None:
    from bass.hierarchy import PhotonDirectionConvention

    rate = electron_frame_rate_factor(
        gamma_e=1.25,
        v_dot_direction=0.2,
        convention=PhotonDirectionConvention.SKY,
    )
    assert rate.factor == pytest.approx(1.25 * 1.2)


def test_context_blocks_non_linear_scope() -> None:
    with pytest.raises(ValueError, match="classical linear Thomson"):
        ElectronFrameThomsonContext(operator_scope="nonlinear")


def test_projected_thomson_source_preserves_isotropic_null_mode() -> None:
    source = project_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=zero_hierarchy(3),
        polarization_state=zero_polarization_hierarchy(3),
        v_b_real_sph=np.zeros(3),
        Gamma_T=4.0,
    )
    assert source.source_ready is True
    assert source.effective_rate.factor == pytest.approx(1.0)
    assert np.allclose(source.temperature.as_flat(), 0.0)
    assert np.allclose(source.polarization_E.E.as_flat(), 0.0)
    assert np.allclose(source.polarization_B.as_flat(), 0.0)


def test_projected_thomson_source_is_linear() -> None:
    t1 = _tower_with_quadrupole(2.0)
    t2 = _tower_with_quadrupole(-0.5)
    e1 = zero_polarization_hierarchy(3)
    e2 = zero_polarization_hierarchy(3)
    combo_t = PSTFHierarchyState(
        L=3,
        tensors=[a + 2.0 * b for a, b in zip(t1.tensors, t2.tensors)],
    )
    combo_e = zero_polarization_hierarchy(3)
    s1 = project_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=t1,
        polarization_state=e1,
        v_b_real_sph=np.zeros(3),
        Gamma_T=3.0,
    )
    s2 = project_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=t2,
        polarization_state=e2,
        v_b_real_sph=np.zeros(3),
        Gamma_T=3.0,
    )
    s_combo = project_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=combo_t,
        polarization_state=combo_e,
        v_b_real_sph=np.zeros(3),
        Gamma_T=3.0,
    )
    assert np.allclose(
        s_combo.temperature.as_flat(),
        s1.temperature.as_flat() + 2.0 * s2.temperature.as_flat(),
    )
    assert np.allclose(
        s_combo.polarization_E.E.as_flat(),
        s1.polarization_E.E.as_flat() + 2.0 * s2.polarization_E.E.as_flat(),
    )


def test_projected_thomson_source_recovers_standard_quadrupole_response() -> None:
    temperature = _tower_with_quadrupole(1.2)
    source = project_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=temperature,
        polarization_state=zero_polarization_hierarchy(3),
        v_b_real_sph=np.zeros(3),
        Gamma_T=5.0,
    )
    expected = -(3.0 / (5.0 * math.sqrt(6.0))) * 5.0 * 1.2
    assert source.polarization_E.E.tensors[2].components[2] == pytest.approx(expected)
    assert source.temperature.tensors[2].components[2] == pytest.approx(-(9.0 / 10.0) * 5.0 * 1.2)


def test_projected_tilted_thomson_source_matches_per_ell_layer_b_helpers() -> None:
    temperature = zero_hierarchy(4)
    temperature.tensors[2].components[:] = [0.05, -0.02, 0.4, 0.11, -0.06]
    temperature.tensors[3].components[:] = np.linspace(-0.4, 0.4, 7)
    temperature.tensors[4].components[:] = np.linspace(0.3, -0.3, 9)
    polarization = zero_polarization_hierarchy(4)
    polarization.tensors[2].components[:] = [0.02, -0.03, 0.15, 0.04, -0.01]
    polarization.tensors[3].components[:] = np.linspace(0.25, -0.25, 7)
    polarization.tensors[4].components[:] = np.linspace(-0.2, 0.2, 9)
    b_state = zero_hierarchy(4)
    b_state.tensors[2].components[:] = [-0.01, 0.03, -0.02, 0.04, -0.05]
    b_state.tensors[3].components[:] = np.linspace(0.12, -0.12, 7)
    b_state.tensors[4].components[:] = np.linspace(-0.08, 0.08, 9)
    tilt = _tilted_species(0.1, (0.0, 1.0, 0.0))
    source = project_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=temperature,
        polarization_state=polarization,
        v_b_real_sph=np.array([0.0, 0.03, -0.02], dtype=np.float64),
        Gamma_T=2.1,
        direction=np.array([0.0, 1.0, 0.0], dtype=np.float64),
        tilted_electron=tilt,
        b_state=b_state,
    )
    effective_gamma = 2.1 * source.effective_rate.factor
    boosted_temperature = apply_axisymmetric_boost_to_tower(
        temperature,
        beta=tilt.beta,
        v_hat_e=tilt.v_hat_e,
    )
    pi_2_e_frame = np.asarray(boosted_temperature.tensors[2].components, dtype=np.float64)
    for ell in range(temperature.L + 1):
        expected_t = evaluate_tilted_thomson_pstf_collision(
            ell=ell,
            temperature_state=temperature,
            polarization_state=polarization,
            eta=0.0,
            v_b_real_sph=np.array([0.0, 0.03, -0.02], dtype=np.float64),
            Gamma_T=effective_gamma,
            tilted_electron=tilt,
        )
        expected_e, expected_b = evaluate_tilted_polarization_eb_collision(
            ell=ell,
            e_state=polarization,
            eta=0.0,
            Pi_2_packed=pi_2_e_frame,
            Gamma_T=effective_gamma,
            b_state=b_state,
            tilted_electron=tilt,
        )
        np.testing.assert_allclose(source.temperature.tensors[ell].components, expected_t.components)
        np.testing.assert_allclose(source.polarization_E.E.tensors[ell].components, expected_e.components)
        np.testing.assert_allclose(source.polarization_B.tensors[ell].components, expected_b.components)


def test_tilted_e_source_uses_electron_frame_temperature_quadrupole() -> None:
    temperature = zero_hierarchy(4)
    temperature.tensors[3].components[3] = 1.0
    polarization = zero_polarization_hierarchy(4)
    tilt = _tilted_species(0.2, (0.0, 0.0, 1.0))

    source = project_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=temperature,
        polarization_state=polarization,
        v_b_real_sph=np.zeros(3),
        Gamma_T=1.0,
        direction=np.array([0.0, 0.0, 1.0], dtype=np.float64),
        tilted_electron=tilt,
    )

    boosted_temperature = apply_axisymmetric_boost_to_tower(
        temperature,
        beta=tilt.beta,
        v_hat_e=tilt.v_hat_e,
    )
    assert not np.allclose(
        boosted_temperature.tensors[2].components,
        temperature.tensors[2].components,
    )
    assert np.linalg.norm(source.polarization_E.E.tensors[2].components) > 0.0
