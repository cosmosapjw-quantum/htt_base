from __future__ import annotations

import inspect

import pytest

from bass.species.massive_neutrino import phase_space_grid


@pytest.mark.skip(reason="pending FB-9.1 implementation — skeleton only")
def test_fb91_phase_space_grid_skeleton_contract() -> None:
    signature = inspect.signature(phase_space_grid)
    assert signature.parameters["mass_eV"].default is inspect._empty
    assert signature.parameters["N_q"].default == 15
    doc = phase_space_grid.__doc__ or ""
    assert "byte-identical" in doc
