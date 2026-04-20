from __future__ import annotations

import numpy as np
import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.massive_neutrino import MassiveNeutrinoBackground
from bass.species.tilted import TiltedSpeciesBackground


@pytest.fixture(scope="module")
def bg_table():
    return build_flrw_background_table()


@pytest.mark.parametrize("mass_eV", [0.02, 0.04, 0.08])
@pytest.mark.parametrize("a", [1e-4, 1e-2, 1.0])
def test_fb95_beta_zero_is_byte_identical_to_massive_rest_frame(
    bg_table,
    mass_eV: float,
    a: float,
) -> None:
    eta = bg_table.eta_at_a(a)
    base = MassiveNeutrinoBackground(bg_table, mass_eV=mass_eV, N_q=15)
    tilted = TiltedSpeciesBackground(base=base, beta=0.0)
    assert np.array_equal(
        np.asarray(tilted.rho_tilde(eta)),
        np.asarray(base.rho_rest(eta)),
    )
    assert np.array_equal(
        np.asarray(tilted.p_tilde(eta)),
        np.asarray(base.p_rest(eta)),
    )
    assert np.array_equal(
        np.asarray(tilted.v_vector(eta)),
        np.zeros(3, dtype=np.float64),
    )


@pytest.mark.parametrize("beta", [0.1, 0.3])
@pytest.mark.parametrize("a", [1e-3, 1e-1, 1.0])
def test_fb95_tilted_thermodynamics_follow_emm_formulas(
    bg_table,
    beta: float,
    a: float,
) -> None:
    eta = bg_table.eta_at_a(a)
    base = MassiveNeutrinoBackground(bg_table, mass_eV=0.04, N_q=15)
    tilted = TiltedSpeciesBackground(base=base, beta=beta)
    rho = float(base.rho_rest(eta))
    p = float(base.p_rest(eta))
    gamma_sq = tilted.gamma_sq
    expected_rho = gamma_sq * (rho + p) - p
    expected_p = p + (gamma_sq * (rho + p) * beta * beta) / 3.0
    assert tilted.rho_tilde(eta) == pytest.approx(expected_rho, rel=1e-12)
    assert tilted.p_tilde(eta) == pytest.approx(expected_p, rel=1e-12)


@pytest.mark.parametrize("beta", [0.1, 0.3])
@pytest.mark.parametrize("a", [1e-3, 1e-1, 1.0])
def test_fb95_tilt_velocity_is_mass_independent(
    bg_table,
    beta: float,
    a: float,
) -> None:
    eta = bg_table.eta_at_a(a)
    light = TiltedSpeciesBackground(
        base=MassiveNeutrinoBackground(bg_table, mass_eV=0.02, N_q=15),
        beta=beta,
    )
    heavy = TiltedSpeciesBackground(
        base=MassiveNeutrinoBackground(bg_table, mass_eV=0.08, N_q=15),
        beta=beta,
    )
    assert np.array_equal(
        np.asarray(light.v_vector(eta)),
        np.asarray(heavy.v_vector(eta)),
    )
