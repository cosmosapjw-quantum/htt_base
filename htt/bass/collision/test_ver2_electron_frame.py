from __future__ import annotations

import math

import numpy as np
import pytest

from bass.collision import (
    ElectronFrameThomsonContext,
    electron_frame_rate_factor,
    project_thomson_source,
)
from bass.collision.polarization import zero_polarization_hierarchy
from bass.hierarchy.pstf_tensor import PSTFTensor, PSTFHierarchyState, zero_hierarchy


def _tower_with_quadrupole(value: float, *, L: int = 3) -> PSTFHierarchyState:
    state = zero_hierarchy(L)
    state.tensors[2] = PSTFTensor(ell=2, components=np.array([0.0, 0.0, value, 0.0, 0.0]))
    return state


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
