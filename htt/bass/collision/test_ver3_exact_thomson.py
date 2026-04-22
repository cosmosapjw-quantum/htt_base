from __future__ import annotations

import math

import numpy as np
import pytest

from bass.collision import (
    ElectronFrameThomsonContext,
    SourceTerms,
    exact_thomson_gate_bundle,
    exact_thomson_source,
)
from bass.collision.polarization import zero_polarization_hierarchy
from bass.hierarchy.pstf_tensor import PSTFTensor, PSTFHierarchyState, zero_hierarchy
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import TiltedSpeciesBackground


def _tower_with_monopole(value: float, *, L: int = 3) -> PSTFHierarchyState:
    state = zero_hierarchy(L)
    state.tensors[0] = PSTFTensor(ell=0, components=np.array([value], dtype=np.float64))
    return state


def _tower_with_quadrupole(value: float, *, L: int = 3) -> PSTFHierarchyState:
    state = zero_hierarchy(L)
    state.tensors[2] = PSTFTensor(ell=2, components=np.array([0.0, 0.0, value, 0.0, 0.0]))
    return state


@pytest.fixture(scope="module")
def registry() -> SpeciesBackgroundRegistry:
    return SpeciesBackgroundRegistry.from_planck2018(recombination_warning_policy="ignore")


def test_exact_thomson_source_preserves_isotropic_null_limit() -> None:
    source = exact_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=zero_hierarchy(3),
        polarization_state=zero_polarization_hierarchy(3),
        v_b_real_sph=np.zeros(3),
        Gamma_T=4.0,
    )
    assert source.scalar_monopole_input == pytest.approx(0.0)
    assert source.directional_temperature_norm == pytest.approx(0.0)
    assert source.polarization_quadrupole_norm == pytest.approx(0.0)
    assert np.allclose(source.projected.temperature.as_flat(), 0.0)
    assert np.allclose(source.projected.polarization_E.E.as_flat(), 0.0)
    assert np.allclose(source.projected.polarization_B.as_flat(), 0.0)


def test_exact_thomson_source_keeps_monopole_and_directional_inputs_separate() -> None:
    monopole_only = exact_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=_tower_with_monopole(5.0),
        polarization_state=zero_polarization_hierarchy(3),
        v_b_real_sph=np.zeros(3),
        Gamma_T=2.0,
    )
    quadrupole_only = exact_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=_tower_with_quadrupole(1.2),
        polarization_state=zero_polarization_hierarchy(3),
        v_b_real_sph=np.zeros(3),
        Gamma_T=5.0,
    )
    assert monopole_only.scalar_monopole_input == pytest.approx(5.0)
    assert monopole_only.directional_temperature_norm == pytest.approx(0.0)
    assert np.allclose(monopole_only.projected.temperature.as_flat(), 0.0)
    assert quadrupole_only.scalar_monopole_input == pytest.approx(0.0)
    assert quadrupole_only.directional_temperature_norm > 0.0
    assert quadrupole_only.projected.temperature.tensors[2].components[2] == pytest.approx(
        -(9.0 / 10.0) * 5.0 * 1.2
    )
    assert quadrupole_only.projected.polarization_E.E.tensors[2].components[2] == pytest.approx(
        -(3.0 / (5.0 * math.sqrt(6.0))) * 5.0 * 1.2
    )


def test_exact_thomson_source_reports_tilt_modulated_effective_opacity(
    registry: SpeciesBackgroundRegistry,
) -> None:
    tilted_electron = TiltedSpeciesBackground(
        base=registry[SpeciesLabel.BARYON],
        beta=0.2,
        v_hat_e=(0.0, 0.0, 1.0),
    )
    source = exact_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=zero_hierarchy(3),
        polarization_state=zero_polarization_hierarchy(3),
        v_b_real_sph=np.zeros(3),
        Gamma_T=3.0,
        direction=np.array([0.0, 0.0, 1.0], dtype=np.float64),
        tilted_electron=tilted_electron,
    )
    assert source.effective_opacity == pytest.approx(
        3.0 * tilted_electron.gamma * (1.0 - tilted_electron.beta)
    )
    assert source.opacity_contract == "electron_frame_tilt_modulated"


def test_exact_thomson_gate_bundle_preserves_split_metadata() -> None:
    source = exact_thomson_source(
        ElectronFrameThomsonContext(),
        temperature_state=_tower_with_quadrupole(1.2),
        polarization_state=zero_polarization_hierarchy(3),
        v_b_real_sph=np.zeros(3),
        Gamma_T=5.0,
    )
    bundle = exact_thomson_gate_bundle(source, family="I")
    assert bundle.gate_name == "exact_thomson_gate"
    assert bundle.passed is True
    assert bundle.metadata["source_split"] == "scalar_monopole_vs_directional_tensor"


def test_directional_exact_thomson_source_contract_keeps_isotropic_null_mode() -> None:
    source = exact_thomson_source(
        np.array([0.0, 0.0, 1.0]),
        np.array([2.0, 2.0, 2.0]),
        2.0,
        np.zeros(3),
        0.0,
        0.0,
        {"Gamma_T": 4.0},
    )
    assert isinstance(source, SourceTerms)
    np.testing.assert_allclose(source.dI_dir, 0.0)
    np.testing.assert_allclose(source.dP_dir, 0.0)
    assert source.effective_opacity == pytest.approx(4.0)


def test_directional_exact_thomson_source_uses_tilt_modulated_effective_rate() -> None:
    source = exact_thomson_source(
        np.array([0.0, 0.0, 1.0]),
        np.array([0.0, 0.0, 0.0]),
        1.0,
        np.zeros(3),
        0.5,
        0.25,
        {"Gamma_T": 3.0, "gamma_e": 1.25, "v_dot_direction": 0.2},
    )
    assert source.effective_opacity == pytest.approx(3.0 * 1.25 * (1.0 - 0.2))
    np.testing.assert_allclose(source.dI_dir, source.effective_opacity * 1.5)
