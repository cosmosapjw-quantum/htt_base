from __future__ import annotations

import numpy as np
import pytest

from bass.background.bianchi_types import (
    type_i_constants,
    type_iv_constants,
    type_v_constants,
    type_vii0_constants,
    type_viih_constants,
    type_ix_constants,
)
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator

ETA_GRID = np.linspace(40.0, 420.0, 129)
K_GRID = np.array([0.05, 0.08, 0.12], dtype=float)
ELL_MAX = 8


def _visibility(eta: float) -> float:
    return float(np.exp(-0.5 * ((eta - 220.0) / 35.0) ** 2))


def _direct_source_builder(
    *, amplitude: float = 1.0, anisotropy: float = 0.2, b_mode: float = 0.0
):
    def _builder(eta: float, k: float) -> dict[str, float]:
        envelope = np.exp(-0.5 * ((eta - 210.0) / 40.0) ** 2)
        return {
            "temperature": amplitude * envelope * (1.0 + 0.1 * k),
            "temperature_anisotropy": anisotropy * envelope,
            "polarization": 0.35 * amplitude * envelope,
            "b_mode": b_mode * envelope,
        }

    return _builder


def _component_source_builder(*, amplitude: float = 1.0):
    def _builder(eta: float, k: float) -> dict[str, float]:
        window = np.exp(-0.5 * ((eta - 225.0) / 45.0) ** 2)
        return {
            "theta_0": amplitude * window,
            "psi": 0.2 * amplitude * window,
            "pi": 0.1 * amplitude * np.exp(-0.5 * ((eta - 215.0) / 50.0) ** 2),
            "phi_dot_plus_psi_dot": 0.03 * amplitude * np.cos(0.7 * k) * window,
            "v_b": 0.01 * amplitude * np.sin(eta / 60.0),
            "kappa": 2.0e-3 * (eta - ETA_GRID[0]),
        }

    return _builder


def _build_bundle(structure, **kwargs):
    return build_lowell_line_of_sight_propagator(
        structure,
        eta_grid_mpc=kwargs.pop("eta_grid_mpc", ETA_GRID),
        k_grid_mpc=kwargs.pop("k_grid_mpc", K_GRID),
        ell_max=kwargs.pop("ell_max", ELL_MAX),
        visibility_fn=kwargs.pop("visibility_fn", _visibility),
        source_builder=kwargs.pop("source_builder", _direct_source_builder()),
        limber_eta_sp_sign=kwargs.pop("limber_eta_sp_sign", "integrator"),
    )


def test_fb71_lowell_los_contract_is_callable() -> None:
    assert callable(build_lowell_line_of_sight_propagator)


def test_fb71_rejects_negative_ell_max() -> None:
    with pytest.raises(ValueError, match="ell_max"):
        _build_bundle(type_i_constants(), ell_max=-1)


def test_fb71_rejects_nonmonotone_eta_grid() -> None:
    with pytest.raises(ValueError, match="eta_grid_mpc"):
        _build_bundle(type_i_constants(), eta_grid_mpc=np.array([1.0, 2.0, 2.0]))


def test_fb71_rejects_nonpositive_k_grid() -> None:
    with pytest.raises(ValueError, match="k_grid_mpc"):
        _build_bundle(type_i_constants(), k_grid_mpc=np.array([0.05, 0.0, 0.2]))


@pytest.mark.parametrize(
    "structure",
    [
        type_i_constants(),
        type_v_constants(a_twist=1.0e-6),
        type_viih_constants(),
        type_ix_constants(),
    ],
)
def test_fb71_returns_expected_transfer_shapes(structure) -> None:
    bundle = _build_bundle(structure)
    assert bundle["transfer_T"].shape == (K_GRID.size, ELL_MAX + 1, 3)
    assert bundle["transfer_E"].shape == (K_GRID.size, ELL_MAX + 1, 3)
    assert bundle["transfer_B"].shape == (K_GRID.size, ELL_MAX + 1, 3)
    assert bundle["propagator_matrix"].shape == (K_GRID.size, ELL_MAX + 1, 3, 3)


@pytest.mark.parametrize("ell_index", [0, 2, 5, 8])
def test_fb71_limber_eta_sp_matches_integrator_sign(ell_index: int) -> None:
    bundle = _build_bundle(type_vii0_constants(n1=1.0e-6, n3=1.0e-6))
    eta_0 = float(bundle["eta_0_mpc"])
    expected = eta_0 - (ell_index + 0.5) / K_GRID[0]
    assert bundle["limber_eta_sp_mpc"][0, ell_index] == pytest.approx(expected)


@pytest.mark.parametrize("ell_index", [0, 2, 5, 8])
def test_fb71_legacy_negative_branch_matches_old_stationary_phase(ell_index: int) -> None:
    bundle = _build_bundle(
        type_vii0_constants(n1=1.0e-6, n3=1.0e-6),
        limber_eta_sp_sign="legacy_negative",
    )
    expected = (ell_index + 0.5) / K_GRID[0]
    assert bundle["limber_eta_sp_mpc"][0, ell_index] == pytest.approx(expected)


def test_fb71_legacy_and_integrator_limber_proxies_differ() -> None:
    good = _build_bundle(type_viih_constants())
    legacy = _build_bundle(type_viih_constants(), limber_eta_sp_sign="legacy_negative")
    assert not np.allclose(
        good["limber_temperature_proxy"], legacy["limber_temperature_proxy"]
    )


def test_fb71_type_i_b_mode_is_identically_zero() -> None:
    bundle = _build_bundle(type_i_constants(), source_builder=_direct_source_builder(b_mode=1.0))
    np.testing.assert_array_equal(bundle["transfer_B"], 0.0)


def test_fb71_type_i_mode_coupling_is_identity() -> None:
    bundle = _build_bundle(type_i_constants())
    np.testing.assert_allclose(bundle["mode_coupling_matrix"], np.eye(3), atol=0.0)


@pytest.mark.parametrize(
    "structure",
    [type_iv_constants(), type_viih_constants(), type_ix_constants()],
)
def test_fb71_rotating_types_report_nonzero_rotation_strength(structure) -> None:
    bundle = _build_bundle(structure)
    assert float(bundle["rotation_strength"]) > 0.0


@pytest.mark.parametrize(
    "structure",
    [type_v_constants(a_twist=1.0e-6), type_vii0_constants(n1=1.0e-6, n3=1.0e-6)],
)
def test_fb71_near_flrw_limits_keep_rotation_strength_zero(structure) -> None:
    bundle = _build_bundle(structure)
    assert float(bundle["rotation_strength"]) == pytest.approx(0.0, abs=1.0e-18)


@pytest.mark.parametrize(
    "structure",
    [type_i_constants(), type_iv_constants(), type_viih_constants(), type_ix_constants()],
)
def test_fb71_preferred_axis_is_unit_normalised(structure) -> None:
    bundle = _build_bundle(structure)
    assert np.linalg.norm(bundle["preferred_axis"]) == pytest.approx(1.0, rel=1.0e-12)


def test_fb71_zero_visibility_kills_all_transfers() -> None:
    zero_visibility = lambda eta: 0.0
    bundle = _build_bundle(type_viih_constants(), visibility_fn=zero_visibility)
    np.testing.assert_allclose(bundle["transfer_T"], 0.0, atol=1.0e-14)
    np.testing.assert_allclose(bundle["transfer_E"], 0.0, atol=1.0e-14)
    np.testing.assert_allclose(bundle["transfer_B"], 0.0, atol=1.0e-14)


def test_fb71_direct_and_component_sources_are_both_finite() -> None:
    direct = _build_bundle(type_viih_constants(), source_builder=_direct_source_builder())
    component = _build_bundle(
        type_viih_constants(), source_builder=_component_source_builder()
    )
    for key in ("transfer_T", "transfer_E", "transfer_B"):
        assert np.all(np.isfinite(direct[key]))
        assert np.all(np.isfinite(component[key]))


def test_fb71_direct_and_component_paths_do_not_collapse_to_identical_output() -> None:
    direct = _build_bundle(type_viih_constants(), source_builder=_direct_source_builder())
    component = _build_bundle(
        type_viih_constants(), source_builder=_component_source_builder()
    )
    assert not np.allclose(direct["transfer_T"], component["transfer_T"])


def test_fb71_raw_transfers_preserve_pre_mixing_shape() -> None:
    bundle = _build_bundle(type_viih_constants())
    assert bundle["raw_transfer_T"].shape == bundle["transfer_T"].shape
    assert bundle["raw_transfer_E"].shape == bundle["transfer_E"].shape
    assert bundle["raw_transfer_B"].shape == bundle["transfer_B"].shape


def test_fb71_component_builder_uses_visibility_weighting() -> None:
    bundle = _build_bundle(
        type_vii0_constants(n1=1.0e-6, n3=1.0e-6),
        source_builder=_component_source_builder(),
    )
    assert np.max(np.abs(bundle["transfer_T"])) > 0.0
    assert np.max(np.abs(bundle["transfer_E"])) > 0.0

