from __future__ import annotations

import numpy as np
import pytest

from bass.recombination import (
    build_tilted_visibility_source,
    build_visibility_history_contract,
)
from bass.hierarchy.frame_contracts import PhotonDirectionConvention
from bass.recombination.recombination_ingest import make_synthetic_tanh_table
from bass.recombination.reionization import (
    CosmologyForRecombination,
    ReionizationParameters,
)
from bass.species.background_table import build_flrw_background_table
from bass.species.baryon import BaryonBackground
from bass.species.constants import default_constants


def _test_cosmology() -> CosmologyForRecombination:
    return CosmologyForRecombination(
        h=0.6736,
        T_cmb=2.7255,
        Omega_b=0.0493,
        Y_He=0.245,
        Omega_m=0.315,
        Omega_r=9.2e-5,
        Omega_Lambda=0.684908,
    )


def _build_baryon(contract) -> BaryonBackground:
    bg = build_flrw_background_table()
    c = default_constants()
    return BaryonBackground(bg, c.Omega_b_0, contract.interp, recombination_warning_policy="ignore")


def test_scalar_history_contract_keeps_electron_frame_visibility() -> None:
    table = make_synthetic_tanh_table()
    contract = build_visibility_history_contract(table)
    assert contract.frame_metadata.visibility_frame == "electron_frame"
    assert contract.history_metadata.reionization_mode == "disabled"
    assert contract.normalization_status.visibility_nonnegative is True
    assert contract.normalization_status.kappa_monotone_increasing_in_z is True
    assert contract.normalization_status.optical_depth_decreases_toward_observer is True
    assert contract.normalization_status.min_visibility >= 0.0
    assert contract.events is not None
    assert contract.events.z_last_scattering > 0.0
    assert contract.interp.query_visibility(np.array([1100.0])).shape == (1,)


def test_reionization_contract_marks_tanh_mode_and_detects_event() -> None:
    table = make_synthetic_tanh_table(z_min=30.0, z_max=3000.0)
    contract = build_visibility_history_contract(
        table,
        include_reionization=True,
        reionization_params=ReionizationParameters(include_HeII=False),
        cosmology=_test_cosmology(),
    )
    assert contract.history_metadata.reionization_mode == "tanh"
    assert contract.table.metadata["reionization"] == "tanh"
    assert contract.events is not None
    assert contract.events.reionization_detected is True
    assert contract.events.tau_reion > 0.0


def test_tilted_visibility_reduces_to_scalar_when_tilt_vanishes() -> None:
    contract = build_visibility_history_contract(make_synthetic_tanh_table())
    baryon = _build_baryon(contract)
    source = build_tilted_visibility_source(
        contract,
        baryon=baryon,
        v_e=lambda eta: np.zeros(3, dtype=np.float64),
    )
    eta = 0.5 * baryon._bg.eta_today  # noqa: SLF001
    directions = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 1.0, 1.0]) / np.sqrt(3.0),
    ]
    scalar_gamma = float(baryon.tau_dot(eta))
    scalar_visibility = float(baryon.visibility(eta))
    for direction in directions:
        assert source.Gamma_T(eta, direction) == pytest.approx(scalar_gamma, rel=1.0e-12)
        assert source.g(eta, direction) == pytest.approx(scalar_visibility, rel=5.0e-4)


def test_tilted_visibility_has_forward_back_asymmetry() -> None:
    contract = build_visibility_history_contract(make_synthetic_tanh_table())
    baryon = _build_baryon(contract)
    source = build_tilted_visibility_source(
        contract,
        baryon=baryon,
        v_e=lambda eta: np.array([0.0, 0.0, 0.3], dtype=np.float64),
        direction_convention=PhotonDirectionConvention.PROPAGATION,
    )
    eta = 0.5 * baryon._bg.eta_today  # noqa: SLF001
    gamma_forward = source.Gamma_T(eta, np.array([0.0, 0.0, 1.0]))
    gamma_side = source.Gamma_T(eta, np.array([1.0, 0.0, 0.0]))
    gamma_back = source.Gamma_T(eta, np.array([0.0, 0.0, -1.0]))
    assert gamma_back > gamma_side > gamma_forward


def test_reionization_changes_low_z_visibility_source() -> None:
    table = make_synthetic_tanh_table(z_min=30.0, z_max=3000.0)
    no_reion_contract = build_visibility_history_contract(table)
    with_reion_contract = build_visibility_history_contract(
        table,
        include_reionization=True,
        reionization_params=ReionizationParameters(include_HeII=False),
        cosmology=_test_cosmology(),
    )
    baryon_no_reion = _build_baryon(no_reion_contract)
    baryon_with_reion = _build_baryon(with_reion_contract)
    source_no_reion = build_tilted_visibility_source(
        no_reion_contract,
        baryon=baryon_no_reion,
        v_e=lambda eta: np.zeros(3, dtype=np.float64),
    )
    source_with_reion = build_tilted_visibility_source(
        with_reion_contract,
        baryon=baryon_with_reion,
        v_e=lambda eta: np.zeros(3, dtype=np.float64),
    )
    eta_low_z = baryon_no_reion._bg.eta_at_a(1.0 / 9.0)  # noqa: SLF001
    direction = np.array([0.0, 0.0, 1.0], dtype=np.float64)
    assert source_with_reion.g(eta_low_z, direction) > source_no_reion.g(eta_low_z, direction)
