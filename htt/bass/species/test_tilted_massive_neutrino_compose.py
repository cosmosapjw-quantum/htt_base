from __future__ import annotations

import pytest

from bass.species.background_table import build_flrw_background_table
from bass.species.massive_neutrino import MassiveNeutrinoBackground
from bass.species.tilted import TiltedSpeciesBackground


@pytest.mark.skip(reason="pending FB-9.5 implementation — skeleton only")
def test_fb95_tilted_massive_neutrino_compose_skeleton() -> None:
    bg_table = build_flrw_background_table(n_eta=32)
    base = MassiveNeutrinoBackground(bg_table, mass_eV=0.04, N_q=15)
    tilted = TiltedSpeciesBackground(base=base, beta=0.0)
    assert isinstance(base, MassiveNeutrinoBackground)
    assert isinstance(tilted, TiltedSpeciesBackground)
