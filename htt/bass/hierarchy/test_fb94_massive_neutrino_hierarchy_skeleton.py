from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy import HardCutClosure, ZeroCollisionOperator, hierarchy_total_size
from bass.hierarchy.hierarchy_rhs import (
    hierarchy_rhs_photon,
    hierarchy_rhs_neutrino,
    zero_nabla_operator,
)
from bass.species.background_table import build_flrw_background_table
from bass.species.base import SpeciesLabel
from bass.species.massive_neutrino import MassiveNeutrinoBackground
from bass.species.registry import SpeciesBackgroundRegistry


def _toy_nabla_operator(tensor: np.ndarray, kind: str = "gradient") -> np.ndarray:
    arr = np.asarray(tensor)
    dtype = np.complex128 if np.iscomplexobj(arr) else np.float64
    scale = float(np.sum(np.real(arr))) + 0.125
    if kind == "gradient":
        return np.full((3,) * (arr.ndim + 1), scale, dtype=dtype)
    if kind == "divergence":
        if arr.ndim == 0:
            raise ValueError("divergence of rank-0 tensor is undefined")
        if arr.ndim == 1:
            return np.array(scale, dtype=dtype)
        return np.full((3,) * (arr.ndim - 1), scale, dtype=dtype)
    raise ValueError(kind)


def _leading_order_power_suppression(k: float, k_fs: float, f_nu: float) -> float:
    x = float(k / k_fs)
    return -8.0 * f_nu * (x * x) / (1.0 + x * x)


def _capture_hierarchy_rhs_outputs(
    *,
    eta: float,
    state: np.ndarray,
    bg_table,
    neutrino_background=None,
) -> dict[str, np.ndarray]:
    kwargs = {
        "eta": eta,
        "y_flat": state,
        "L_max": 3,
        "bg_table": bg_table,
        "tetrad_state": None,
        "closure": HardCutClosure(),
        "nabla_operator": _toy_nabla_operator,
    }
    return {
        "photon": hierarchy_rhs_photon(
            collision=ZeroCollisionOperator(),
            **kwargs,
        ),
        "neutrino": hierarchy_rhs_neutrino(
            neutrino_background=neutrino_background,
            **kwargs,
        ),
    }


@pytest.fixture(scope="module")
def bg_table():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def seeded_state() -> np.ndarray:
    rng = np.random.default_rng(20260420)
    return rng.normal(size=hierarchy_total_size(3)) * 1e-3


@pytest.mark.parametrize("a", [1e-4, 1e-2, 0.1, 1.0])
@pytest.mark.parametrize("with_registry_object", [False, True])
def test_fb94_sigma_mnu_zero_hierarchy_rhs_is_byte_identical(
    bg_table,
    seeded_state: np.ndarray,
    a: float,
    with_registry_object: bool,
) -> None:
    eta = bg_table.eta_at_a(a)
    reg = SpeciesBackgroundRegistry.from_planck2018(
        bg_table=bg_table,
        Sigma_mnu=0.0,
    )
    neutrino_background = (
        reg[SpeciesLabel.NEUTRINO] if with_registry_object else None
    )
    dy_default = hierarchy_rhs_neutrino(
        eta,
        seeded_state,
        L_max=3,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
    )
    dy_zero = hierarchy_rhs_neutrino(
        eta,
        seeded_state,
        L_max=3,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        neutrino_background=neutrino_background,
    )
    assert np.array_equal(dy_default, dy_zero)


@pytest.mark.parametrize("a", [1e-4, 1e-2, 0.1, 1.0])
def test_fb94_sigma_mnu_zero_captures_all_hierarchy_rhs_outputs_byte_identically(
    bg_table,
    seeded_state: np.ndarray,
    a: float,
) -> None:
    eta = bg_table.eta_at_a(a)
    reg = SpeciesBackgroundRegistry.from_planck2018(
        bg_table=bg_table,
        Sigma_mnu=0.0,
    )
    baseline = _capture_hierarchy_rhs_outputs(
        eta=eta,
        state=seeded_state,
        bg_table=bg_table,
        neutrino_background=None,
    )
    with_registry = _capture_hierarchy_rhs_outputs(
        eta=eta,
        state=seeded_state,
        bg_table=bg_table,
        neutrino_background=reg[SpeciesLabel.NEUTRINO],
    )
    for key in baseline:
        assert np.array_equal(baseline[key], with_registry[key]), key


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
@pytest.mark.parametrize("a", [1e-2, 0.1, 1.0])
def test_fb94_massive_neutrino_scales_only_free_streaming_terms(
    bg_table,
    seeded_state: np.ndarray,
    mass_eV: float,
    a: float,
) -> None:
    eta = bg_table.eta_at_a(a)
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    dy_zero = hierarchy_rhs_neutrino(
        eta,
        seeded_state,
        L_max=3,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        neutrino_background=nu,
        nabla_operator=zero_nabla_operator,
    )
    dy_massless = hierarchy_rhs_neutrino(
        eta,
        seeded_state,
        L_max=3,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        nabla_operator=_toy_nabla_operator,
    )
    dy_massive = hierarchy_rhs_neutrino(
        eta,
        seeded_state,
        L_max=3,
        bg_table=bg_table,
        tetrad_state=None,
        closure=HardCutClosure(),
        neutrino_background=nu,
        nabla_operator=_toy_nabla_operator,
    )
    modifier = float(nu.free_streaming_modifier(eta))
    expected = dy_zero + modifier * (dy_massless - dy_zero)
    assert np.allclose(dy_massive, expected, rtol=1e-12, atol=1e-15)


@pytest.mark.parametrize("sigma_mnu", [0.06, 0.12, 0.24])
def test_fb94_k_fs_today_matches_literature_scaling_to_ten_percent(
    bg_table,
    sigma_mnu: float,
) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=sigma_mnu / 3.0, N_q=15)
    c = bg_table.constants
    k_fs = float(nu.free_streaming_wavenumber(bg_table.eta_today))
    # The quoted rule-of-thumb is commonly written in h/Mpc. Convert to
    # Mpc^-1 for comparison with the code path here.
    expected = (
        0.0801
        * (nu.mass_eV / 0.1)
        * np.sqrt(c.Omega_m_0 / 0.3)
        * c.h
    )
    assert k_fs == pytest.approx(expected, rel=0.10)


@pytest.mark.parametrize("sigma_mnu", [0.06, 0.12, 0.24])
def test_fb94_large_k_power_suppression_recovers_minus_8f_nu(
    bg_table,
    sigma_mnu: float,
) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=sigma_mnu / 3.0, N_q=15)
    eta_today = bg_table.eta_today
    k_fs = float(nu.free_streaming_wavenumber(eta_today))
    f_nu = float(nu.rho_rest(eta_today) / bg_table.constants.Omega_m_0)
    delta = _leading_order_power_suppression(100.0 * k_fs, k_fs, f_nu)
    assert delta == pytest.approx(-8.0 * f_nu, rel=1e-4)


@pytest.mark.parametrize("sigma_mnu", [0.06, 0.12, 0.24])
def test_fb94_small_k_power_suppression_is_negligible(
    bg_table,
    sigma_mnu: float,
) -> None:
    nu = MassiveNeutrinoBackground(bg_table, mass_eV=sigma_mnu / 3.0, N_q=15)
    eta_today = bg_table.eta_today
    k_fs = float(nu.free_streaming_wavenumber(eta_today))
    f_nu = float(nu.rho_rest(eta_today) / bg_table.constants.Omega_m_0)
    delta = _leading_order_power_suppression(0.01 * k_fs, k_fs, f_nu)
    assert abs(delta) < 1.0e-3 * (8.0 * f_nu)
