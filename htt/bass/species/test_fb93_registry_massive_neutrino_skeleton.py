from __future__ import annotations

import inspect

import numpy as np
import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.base import CANONICAL_ORDER, SpeciesLabel
from bass.species.massive_neutrino import MassiveNeutrinoBackground
from bass.species.neutrino import NeutrinoBackground
from bass.species.registry import SpeciesBackgroundRegistry


@pytest.fixture(scope="module")
def bg_table():
    return build_flrw_background_table()


@pytest.fixture(scope="module")
def registry_default(bg_table):
    return SpeciesBackgroundRegistry.from_planck2018(bg_table=bg_table)


@pytest.fixture(scope="module")
def registry_zero(bg_table):
    return SpeciesBackgroundRegistry.from_planck2018(
        bg_table=bg_table,
        Sigma_mnu=0.0,
    )


@pytest.mark.parametrize("label", CANONICAL_ORDER)
@pytest.mark.parametrize("a", [1e-5, 1e-3, 0.1, 1.0])
def test_fb93_sigma_mnu_zero_registry_is_byte_identical(
    registry_default,
    registry_zero,
    label: SpeciesLabel,
    a: float,
) -> None:
    eta = registry_default.bg_table.eta_at_a(a)
    base = registry_default[label]
    zero = registry_zero[label]
    assert type(base) is type(zero)
    assert np.array_equal(
        np.asarray(base.rho_rest(eta)),
        np.asarray(zero.rho_rest(eta)),
    )
    assert np.array_equal(
        np.asarray(base.p_rest(eta)),
        np.asarray(zero.p_rest(eta)),
    )


def test_fb93_signature_keeps_keyword_default() -> None:
    signature = inspect.signature(SpeciesBackgroundRegistry.from_planck2018)
    assert signature.parameters["Sigma_mnu"].default == 0.0


def test_fb93_zero_mass_registry_keeps_lb1_neutrino_type(registry_zero) -> None:
    assert isinstance(registry_zero[SpeciesLabel.NEUTRINO], NeutrinoBackground)
    assert not isinstance(
        registry_zero[SpeciesLabel.NEUTRINO],
        MassiveNeutrinoBackground,
    )


@pytest.mark.parametrize("sigma_mnu", [0.06, 0.12, 0.24])
def test_fb93_positive_sigma_mnu_uses_massive_neutrino_slot(
    bg_table,
    sigma_mnu: float,
) -> None:
    registry = SpeciesBackgroundRegistry.from_planck2018(
        bg_table=bg_table,
        Sigma_mnu=sigma_mnu,
    )
    neutrino = registry[SpeciesLabel.NEUTRINO]
    assert isinstance(neutrino, MassiveNeutrinoBackground)
    assert neutrino.mass_eV == pytest.approx(sigma_mnu / 3.0, rel=0.0, abs=0.0)


@pytest.mark.parametrize("label", [SpeciesLabel.PHOTON, SpeciesLabel.BARYON, SpeciesLabel.CDM, SpeciesLabel.LAMBDA])
@pytest.mark.parametrize("sigma_mnu", [0.06, 0.12, 0.24])
def test_fb93_positive_sigma_mnu_does_not_mutate_other_species(
    bg_table,
    registry_default,
    label: SpeciesLabel,
    sigma_mnu: float,
) -> None:
    registry = SpeciesBackgroundRegistry.from_planck2018(
        bg_table=bg_table,
        Sigma_mnu=sigma_mnu,
    )
    eta = bg_table.eta_at_a(0.2)
    assert np.array_equal(
        np.asarray(registry[label].rho_rest(eta)),
        np.asarray(registry_default[label].rho_rest(eta)),
    )
    assert np.array_equal(
        np.asarray(registry[label].p_rest(eta)),
        np.asarray(registry_default[label].p_rest(eta)),
    )


@pytest.mark.parametrize("sigma_mnu", [0.06, 0.12, 0.24])
def test_fb93_positive_sigma_mnu_changes_neutrino_density_today(
    bg_table,
    registry_default,
    sigma_mnu: float,
) -> None:
    registry = SpeciesBackgroundRegistry.from_planck2018(
        bg_table=bg_table,
        Sigma_mnu=sigma_mnu,
    )
    eta_today = bg_table.eta_today
    assert (
        registry[SpeciesLabel.NEUTRINO].rho_rest(eta_today)
        > registry_default[SpeciesLabel.NEUTRINO].rho_rest(eta_today)
    )


def test_fb93_negative_sigma_mnu_raises(bg_table) -> None:
    with pytest.raises(ValueError):
        SpeciesBackgroundRegistry.from_planck2018(
            bg_table=bg_table,
            Sigma_mnu=-0.01,
        )
