from __future__ import annotations

import numpy as np
import pytest

from bass.recombination import (
    build_visibility_history_contract,
    homogeneous_reionization_history,
    opacity_from_physical_inputs,
    optical_depth,
    visibility_history_gate_bundle,
    visibility_function,
)
from bass.recombination.recombination_ingest import build_interpolators, make_synthetic_tanh_table
from bass.recombination.reionization import (
    CosmologyForRecombination,
    ReionizationParameters,
)


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


def test_opacity_and_optical_depth_wrappers_match_contract_tables() -> None:
    table = make_synthetic_tanh_table()
    cosmo = _test_cosmology()
    tau_dot = opacity_from_physical_inputs(z=table.z, x_e=table.x_e, cosmology=cosmo)
    kappa = optical_depth(z=table.z, tau_dot_Mpc=tau_dot, cosmology=cosmo)
    assert tau_dot.shape == table.z.shape
    assert kappa.shape == table.z.shape
    assert np.all(tau_dot >= 0.0)
    assert np.all(np.diff(kappa) >= -1.0e-12)
    assert kappa[0] == pytest.approx(0.0, abs=1.0e-15)


def test_visibility_function_is_nonnegative_for_monotone_scalar_history() -> None:
    table = make_synthetic_tanh_table()
    interp = build_interpolators(table)
    visibility = visibility_function(tau_dot_Mpc=table.tau_dot, kappa=table.kappa)
    assert np.all(visibility >= 0.0)
    np.testing.assert_allclose(
        visibility,
        interp.query_visibility(table.z),
        rtol=1.0e-10,
        atol=1.0e-12,
    )


def test_homogeneous_reionization_history_opens_tanh_contract() -> None:
    table = make_synthetic_tanh_table(z_min=30.0, z_max=3000.0)
    contract = homogeneous_reionization_history(
        table,
        reionization_params=ReionizationParameters(include_HeII=False),
        cosmology=_test_cosmology(),
    )
    assert contract.history_metadata.reionization_mode == "tanh"
    assert contract.history_metadata.homogeneous_reionization_only is True
    assert contract.events is not None
    assert contract.events.reionization_detected is True


def test_reionization_adapter_preserves_monotonic_visibility_metadata() -> None:
    table = make_synthetic_tanh_table(z_min=30.0, z_max=3000.0)
    contract = homogeneous_reionization_history(
        table,
        reionization_params=ReionizationParameters(include_HeII=False),
        cosmology=_test_cosmology(),
    )
    assert contract.normalization_status.visibility_nonnegative is True
    assert contract.normalization_status.kappa_monotone_increasing_in_z is True
    assert contract.normalization_status.optical_depth_decreases_toward_observer is True


def test_visibility_history_gate_bundle_uses_normalization_checks() -> None:
    table = make_synthetic_tanh_table(z_min=30.0, z_max=3000.0)
    contract = homogeneous_reionization_history(
        table,
        reionization_params=ReionizationParameters(include_HeII=False),
        cosmology=_test_cosmology(),
    )
    bundle = visibility_history_gate_bundle(contract, family="V")
    assert bundle.gate_name == "visibility_history_gate"
    assert bundle.passed is True
    assert bundle.metadata["reionization_mode"] == "tanh"
