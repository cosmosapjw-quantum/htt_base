from __future__ import annotations

import pytest

from bass.species.base import SpeciesLabel
from bass.species.massive_neutrino import MassiveNeutrinoBackground


@pytest.mark.skip(reason="pending FB-9.2 implementation — skeleton only")
def test_fb92_massive_neutrino_background_skeleton_contract() -> None:
    assert MassiveNeutrinoBackground.label is SpeciesLabel.NEUTRINO
    assert hasattr(MassiveNeutrinoBackground, "rho_rest")
    assert hasattr(MassiveNeutrinoBackground, "p_rest")
    doc = MassiveNeutrinoBackground.__doc__ or ""
    assert "byte-identical" in doc
