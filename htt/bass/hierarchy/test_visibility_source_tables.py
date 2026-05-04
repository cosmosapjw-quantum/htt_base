from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from bass.background import get_family_spec
from bass.hierarchy import assemble_source_vector, build_hierarchy_layout, flatten, zero_hierarchy
from bass.hierarchy.ver2_native_integrator import (
    _neutrino_anisotropic_stress_temperature_rhs,
    _resolved_doppler_source,
    _resolved_polarization_source,
    _resolved_temperature_visibility_source,
    _resolved_visibility_g,
    _resolved_visibility_source_components,
    _scalar_kappa_from_contract,
    _scalar_visibility_g_from_contract,
)
from bass.los import build_backend


class _FakeBoostedVisibility:
    def __init__(self, *, g_value: float, kappa_value: float, boost_value: float) -> None:
        self.g_value = float(g_value)
        self.kappa_value = float(kappa_value)
        self.boost_value = float(boost_value)
        self.visibility = self
        self.g_calls = 0
        self.kappa_calls = 0
        self.boost_calls = 0

    def g(self, eta: float, direction: np.ndarray) -> float:
        self.g_calls += 1
        np.testing.assert_allclose(direction, np.array([1.0, 0.0, 0.0]))
        return self.g_value

    def kappa(self, eta: float, direction: np.ndarray) -> float:
        self.kappa_calls += 1
        np.testing.assert_allclose(direction, np.array([1.0, 0.0, 0.0]))
        return self.kappa_value

    def boost_factor(self, eta: float, direction: np.ndarray) -> float:
        self.boost_calls += 1
        np.testing.assert_allclose(direction, np.array([1.0, 0.0, 0.0]))
        return self.boost_value


class _FakeScalarInterp:
    def __init__(self) -> None:
        self.table = SimpleNamespace(z_min=0.0, z_max=3000.0)
        self.queries: list[float] = []
        self.kappa_queries: list[float] = []

    def query_visibility(self, z: float) -> float:
        self.queries.append(float(z))
        return 0.5 + 1.0e-4 * float(z)

    def query_kappa(self, z: float) -> float:
        self.kappa_queries.append(float(z))
        return 0.25 + 1.0e-5 * float(z)


class _FakeBackgroundTable:
    def __init__(self, a: float) -> None:
        self.a = float(a)

    def interp_a(self, eta: float) -> float:
        return self.a


def test_source_table_visibility_uses_electron_frame_visibility_g() -> None:
    source = _FakeBoostedVisibility(g_value=0.125, kappa_value=7.0, boost_value=3.0)
    cfg = SimpleNamespace(gamma_T_override=None)

    visibility = _resolved_visibility_g(
        eta=42.0,
        direction=np.array([1.0, 0.0, 0.0]),
        visibility_source=source,
        config=cfg,
    )

    assert visibility == pytest.approx(0.125)
    assert source.g_calls == 1
    assert source.kappa_calls == 0
    assert source.boost_calls == 0


def test_native_neutrino_metric_source_uses_only_quadrupole_stress() -> None:
    neutrino = zero_hierarchy(3)
    neutrino.tensors[2].components[:] = np.arange(1.0, 6.0)
    neutrino.tensors[3].components[:] = 10.0
    background = SimpleNamespace(a_val=0.5, Theta=6.0)

    rhs = _neutrino_anisotropic_stress_temperature_rhs(
        neutrino,
        background=background,
        R_nu=0.25,
    )

    expected_coeff = 0.5 * (6.0 / 3.0) * 0.25 * (2.0 / 5.0)
    np.testing.assert_allclose(rhs[:4], 0.0, atol=1.0e-15)
    np.testing.assert_allclose(rhs[4:9], expected_coeff * np.arange(1.0, 6.0))
    np.testing.assert_allclose(rhs[9:], 0.0, atol=1.0e-15)


def test_source_table_visibility_override_keeps_gamma_exp_minus_kappa_form() -> None:
    source = _FakeBoostedVisibility(g_value=0.125, kappa_value=0.25, boost_value=1.5)
    cfg = SimpleNamespace(gamma_T_override=lambda eta: 2.0)

    visibility = _resolved_visibility_g(
        eta=42.0,
        direction=np.array([1.0, 0.0, 0.0]),
        visibility_source=source,
        config=cfg,
    )

    assert visibility == pytest.approx(2.0 * 1.5 * np.exp(-0.25))
    assert source.g_calls == 0
    assert source.kappa_calls == 1
    assert source.boost_calls == 1


def test_source_table_visibility_fails_closed_on_nonfinite_values() -> None:
    source = _FakeBoostedVisibility(g_value=float("nan"), kappa_value=0.0, boost_value=1.0)
    cfg = SimpleNamespace(gamma_T_override=None)

    with pytest.raises(RuntimeError, match="electron-frame visibility"):
        _resolved_visibility_g(
            eta=42.0,
            direction=np.array([1.0, 0.0, 0.0]),
            visibility_source=source,
            config=cfg,
        )


def test_scalar_visibility_contract_uses_z_of_eta_without_edge_clipping() -> None:
    interp = _FakeScalarInterp()
    source = SimpleNamespace(contract=SimpleNamespace(interp=interp))

    visibility = _scalar_visibility_g_from_contract(
        eta=12.0,
        bg_table=_FakeBackgroundTable(a=1.0 / 1101.0),
        visibility_source=source,
    )

    assert visibility == pytest.approx(0.5 + 0.11)
    assert len(interp.queries) == 1
    assert interp.queries[0] == pytest.approx(1100.0)


def test_scalar_visibility_contract_defers_early_queries_to_authority_path() -> None:
    interp = _FakeScalarInterp()
    source = SimpleNamespace(contract=SimpleNamespace(interp=interp))

    visibility = _scalar_visibility_g_from_contract(
        eta=12.0,
        bg_table=_FakeBackgroundTable(a=1.0 / 5001.0),
        visibility_source=source,
    )

    assert visibility is None
    assert interp.queries == []


def test_scalar_kappa_contract_defers_early_queries_to_authority_path() -> None:
    interp = _FakeScalarInterp()
    source = SimpleNamespace(contract=SimpleNamespace(interp=interp))

    kappa = _scalar_kappa_from_contract(
        eta=12.0,
        bg_table=_FakeBackgroundTable(a=1.0 / 5001.0),
        visibility_source=source,
    )

    assert kappa is None
    assert interp.kappa_queries == []


def test_doppler_source_is_visibility_times_baryon_velocity() -> None:
    doppler = _resolved_doppler_source(
        visibility_amplitude=0.4,
        baryon_local=np.array([0.1, -0.25, 0.3, 0.4], dtype=np.float64),
    )

    assert doppler == pytest.approx(-0.1)


def test_polarization_source_uses_signed_visibility_weighted_pi_bass() -> None:
    theta = np.zeros(9, dtype=np.float64)
    e_mode = np.zeros(9, dtype=np.float64)
    theta[6] = 0.2
    e_mode[6] = -0.05

    source = _resolved_polarization_source(
        visibility_amplitude=0.4,
        photon_T_flat=theta,
        photon_E_flat=e_mode,
        L_max=2,
    )

    pi_bass = 0.2 - np.sqrt(6.0) * (-0.05)
    assert source == pytest.approx(-np.sqrt(6.0) * 0.4 * pi_bass / 4.0)


def test_polarization_source_keeps_sign_instead_of_abs_e2_surrogate() -> None:
    theta = np.zeros(9, dtype=np.float64)
    e_mode = np.zeros(9, dtype=np.float64)
    e_mode[6] = 0.1

    source = _resolved_polarization_source(
        visibility_amplitude=0.5,
        photon_T_flat=theta,
        photon_E_flat=e_mode,
        L_max=2,
    )

    assert source == pytest.approx(0.75 * 0.1)
    assert source != pytest.approx(abs(e_mode[6]))


def test_temperature_visibility_source_uses_theta0_and_pi_bass() -> None:
    theta = np.zeros(9, dtype=np.float64)
    e_mode = np.zeros(9, dtype=np.float64)
    theta[0] = 0.1
    theta[6] = 0.2
    e_mode[6] = -0.05

    source = _resolved_temperature_visibility_source(
        visibility_amplitude=0.4,
        photon_T_flat=theta,
        photon_E_flat=e_mode,
        L_max=2,
    )

    pi_bass = 0.2 - np.sqrt(6.0) * (-0.05)
    assert source == pytest.approx(0.4 * (0.1 + 0.25 * pi_bass))


def test_visibility_source_components_expose_theta0_and_pi_bass_provenance() -> None:
    theta = np.zeros(9, dtype=np.float64)
    e_mode = np.zeros(9, dtype=np.float64)
    theta[0] = -0.05
    theta[6] = 0.2
    e_mode[6] = 0.03

    components = _resolved_visibility_source_components(
        visibility_amplitude=0.4,
        photon_T_flat=theta,
        photon_E_flat=e_mode,
        L_max=2,
        gravitational_potential=0.01,
    )

    pi_bass = 0.2 - np.sqrt(6.0) * 0.03
    assert components.theta_0_source == pytest.approx(-0.05)
    assert components.pi_bass_source == pytest.approx(pi_bass)
    assert components.temperature_visibility_source == pytest.approx(
        0.4 * (-0.05 + 0.01 + 0.25 * pi_bass)
    )
    assert components.polarization_source == pytest.approx(
        -np.sqrt(6.0) * 0.4 * pi_bass / 4.0
    )


def test_source_vector_uses_temperature_visibility_source_for_monopole() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2, "mode_labels": ("m0",)})
    truncation = {"ell_max": 2, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    tables = {"visibility_amplitude": 1.25, "temperature_visibility_source": 0.33}

    source = assemble_source_vector({}, backend, truncation, tables)

    assert source[flatten(layout, "m0", "ph_I", 0, 0)] == pytest.approx(0.33)


def test_source_vector_has_no_fake_doppler_without_runtime_velocity() -> None:
    backend = build_backend(get_family_spec("I"), truncation={"ell_max": 2, "mode_labels": ("m0",)})
    truncation = {"ell_max": 2, "mode_labels": ("m0",)}
    layout = build_hierarchy_layout(backend, truncation)
    bg = {
        "branch": "orthogonal",
        "opacity_data": {"Gamma_T": 1.0},
        "source_tables": {"visibility_amplitude": 1.25},
    }

    no_doppler = assemble_source_vector(bg, backend, truncation, bg["source_tables"])
    dipole_slot = flatten(layout, "m0", "ph_I", 1, 0)
    assert no_doppler[dipole_slot] == pytest.approx(0.0)

    explicit_tables = {"visibility_amplitude": 1.25, "doppler_source": -0.1}
    explicit_doppler = assemble_source_vector(bg, backend, truncation, explicit_tables)
    assert explicit_doppler[dipole_slot] != pytest.approx(0.0)
