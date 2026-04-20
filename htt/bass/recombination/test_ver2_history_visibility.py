from __future__ import annotations

import numpy as np

from bass.recombination import (
    build_tilted_visibility_source_stub,
    build_visibility_history_contract,
)
from bass.recombination.recombination_ingest import make_synthetic_tanh_table
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


def test_scalar_history_contract_keeps_electron_frame_visibility() -> None:
    table = make_synthetic_tanh_table()
    contract = build_visibility_history_contract(table)
    assert contract.frame_metadata.visibility_frame == "electron_frame"
    assert contract.history_metadata.reionization_mode == "disabled"
    assert contract.interp.query_visibility(np.array([1100.0])).shape == (1,)


def test_reionization_contract_marks_tanh_mode() -> None:
    table = make_synthetic_tanh_table(z_min=30.0, z_max=3000.0)
    contract = build_visibility_history_contract(
        table,
        include_reionization=True,
        reionization_params=ReionizationParameters(include_HeII=False),
        cosmology=_test_cosmology(),
    )
    assert contract.history_metadata.reionization_mode == "tanh"
    assert contract.table.metadata["reionization"] == "tanh"


def test_tilted_visibility_stub_reduces_to_scalar_at_zero_tilt() -> None:
    contract = build_visibility_history_contract(make_synthetic_tanh_table())
    stub = build_tilted_visibility_source_stub(contract, tilt_active=False)
    assert stub.source_ready is False
    assert stub.reduces_to_scalar_when_tilt_zero is True
    assert stub.tilt_active is False
