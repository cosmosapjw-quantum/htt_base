from __future__ import annotations

import inspect

import pytest

from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry


@pytest.mark.skip(reason="pending FB-9.3 implementation — skeleton only")
def test_fb93_registry_massive_neutrino_skeleton_contract() -> None:
    signature = inspect.signature(SpeciesBackgroundRegistry.from_planck2018)
    assert signature.parameters["Sigma_mnu"].default == 0.0
    doc = SpeciesBackgroundRegistry.from_planck2018.__doc__ or ""
    assert "byte-identical" in doc
    assert SpeciesLabel.NEUTRINO.name == "NEUTRINO"
