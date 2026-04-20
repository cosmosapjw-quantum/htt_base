from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.base import SpeciesLabel
from bass.species.massive_neutrino import MassiveNeutrinoBackground
from bass.species.neutrino import NeutrinoBackground


_REPO_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_ROOT = _REPO_ROOT / "data" / "class_massive_neutrino_fixtures"


@pytest.fixture(scope="module")
def bg_table():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def massless_reference(bg_table):
    c = bg_table.constants
    return NeutrinoBackground(bg_table, c.Omega_nu_0, N_eff=c.N_eff)


@pytest.mark.parametrize("a", [1e-6, 1e-4, 1e-2, 0.1, 1.0])
def test_fb92_massless_limit_is_byte_identical_to_lb1(
    bg_table,
    massless_reference,
    a: float,
) -> None:
    eta = bg_table.eta_at_a(a)
    massive = MassiveNeutrinoBackground(bg_table, mass_eV=0.0, N_q=15)
    assert massive.label is SpeciesLabel.NEUTRINO
    assert massive.rho_rest(eta) == massless_reference.rho_rest(eta)
    assert massive.p_rest(eta) == massless_reference.p_rest(eta)
    assert massive.dot_rho(eta) == massless_reference.dot_rho(eta)


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
def test_fb92_temperature_tracks_inverse_scale_factor(bg_table, mass_eV: float) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    eta = np.array([bg_table.eta_at_a(a) for a in (1e-4, 1e-2, 0.1, 1.0)])
    temperature = np.asarray(nu.temperature(eta))
    a = np.asarray(bg_table.interp_a(eta))
    assert np.allclose(temperature * a, temperature[0] * a[0], rtol=1e-12)


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
def test_fb92_rho_p_are_positive_and_w_is_bounded(bg_table, mass_eV: float) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    eta = np.array([bg_table.eta_at_a(a) for a in np.geomspace(1e-4, 1.0, 9)])
    rho = np.asarray(nu.rho_rest(eta))
    p = np.asarray(nu.p_rest(eta))
    w = p / rho
    assert np.all(rho > 0.0)
    assert np.all(p > 0.0)
    assert np.all(w >= 0.0)
    assert np.all(w <= (1.0 / 3.0) + 1e-12)


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
def test_fb92_pressure_never_exceeds_radiation_limit(bg_table, mass_eV: float) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    eta = np.array([bg_table.eta_at_a(a) for a in np.geomspace(1e-4, 1.0, 9)])
    rho = np.asarray(nu.rho_rest(eta))
    p = np.asarray(nu.p_rest(eta))
    assert np.all(p <= rho / 3.0 + 1e-15)


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
def test_fb92_w_is_monotone_decreasing(bg_table, mass_eV: float) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    eta = np.array([bg_table.eta_at_a(a) for a in np.geomspace(1e-4, 1.0, 80)])
    w = np.asarray(nu.w(eta))
    assert np.all(np.diff(w) <= 2e-4)


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
def test_fb92_w_crosses_one_sixth_near_a_nr(bg_table, mass_eV: float) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    a_nr = nu.nr_transition_scale_factor()
    eta_nr = bg_table.eta_at_a(a_nr)
    assert nu.w(eta_nr) == pytest.approx(1.0 / 6.0, abs=0.03)


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
def test_fb92_free_streaming_velocity_is_physical(bg_table, mass_eV: float) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    eta = np.array([bg_table.eta_at_a(a) for a in np.geomspace(1e-4, 1.0, 9)])
    velocity = np.asarray(nu.free_streaming_velocity(eta))
    assert np.all(velocity > 0.0)
    assert np.all(velocity <= 1.0 + 1e-12)
    assert np.all(np.diff(velocity) <= 1e-5)


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
def test_fb92_dot_rho_satisfies_collisionless_continuity(bg_table, mass_eV: float) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    eta = np.array([bg_table.eta_at_a(a) for a in np.geomspace(1e-4, 1.0, 7)])
    theta = np.asarray(bg_table.interp_Theta(eta))
    rho = np.asarray(nu.rho_rest(eta))
    p = np.asarray(nu.p_rest(eta))
    dot_rho = np.asarray(nu.dot_rho(eta))
    expected = -theta * (rho + p)
    assert np.allclose(dot_rho, expected, rtol=1e-12, atol=0.0)


@pytest.mark.parametrize(
    ("mass_lo", "mass_hi"),
    [(0.02, 0.04), (0.04, 0.08), (0.02, 0.08)],
)
def test_fb92_today_density_increases_with_mass(
    bg_table,
    mass_lo: float,
    mass_hi: float,
) -> None:
    lo = MassiveNeutrinoBackground(bg_table, mass_eV=mass_lo, N_q=15)
    hi = MassiveNeutrinoBackground(bg_table, mass_eV=mass_hi, N_q=15)
    eta_today = bg_table.eta_today
    assert hi.rho_rest(eta_today) > lo.rho_rest(eta_today)
    assert hi.p_rest(eta_today) < lo.p_rest(eta_today)


@pytest.mark.parametrize("sigma_mnu", [0.06, 0.12, 0.24])
def test_fb92_class_fixture_matches_rho_and_p(bg_table, sigma_mnu: float) -> None:
    path = _FIXTURE_ROOT / f"{sigma_mnu:.2f}.npz"
    with np.load(path, allow_pickle=False) as data:
        nu = MassiveNeutrinoBackground(
            bg_table,
            mass_eV=float(data["mass_eV"]),
            N_q=15,
        )
        eta = np.asarray(data["eta"], dtype=np.float64)
        rho_ref = np.asarray(data["rho"], dtype=np.float64)
        p_ref = np.asarray(data["p"], dtype=np.float64)
        rho = np.asarray(nu.rho_rest(eta))
        p = np.asarray(nu.p_rest(eta))
        assert np.allclose(rho, rho_ref, rtol=1e-4, atol=0.0)
        assert np.allclose(p, p_ref, rtol=1e-4, atol=0.0)
        assert np.allclose(p / rho, np.asarray(data["w"]), rtol=1e-4, atol=0.0)


@pytest.mark.parametrize("sigma_mnu", [0.06, 0.12, 0.24])
def test_fb92_class_fixture_carries_provenance_header(sigma_mnu: float) -> None:
    path = _FIXTURE_ROOT / f"{sigma_mnu:.2f}.npz"
    with np.load(path, allow_pickle=False) as data:
        assert "provenance_header" in data.files
        assert "class_version" in data.files
        assert "precision_settings" in data.files
        assert "generator_script_sha256" in data.files
        header = str(data["provenance_header"].item())
        assert "CLASS" in header
        assert "precision" in header.lower()
        assert len(str(data["generator_script_sha256"].item())) == 64


def test_fb92_negative_mass_raises(bg_table) -> None:
    with pytest.raises(ValueError):
        MassiveNeutrinoBackground(bg_table, mass_eV=-0.01, N_q=15)


def test_fb92_invalid_quadrature_size_raises(bg_table) -> None:
    with pytest.raises(ValueError):
        MassiveNeutrinoBackground(bg_table, mass_eV=0.04, N_q=0)
