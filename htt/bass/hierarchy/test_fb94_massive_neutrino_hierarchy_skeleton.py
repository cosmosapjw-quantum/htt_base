from __future__ import annotations

import inspect

import pytest

from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_neutrino


@pytest.mark.skip(reason="pending FB-9.4 implementation — skeleton only")
def test_fb94_massive_neutrino_hierarchy_skeleton_contract() -> None:
    signature = inspect.signature(hierarchy_rhs_neutrino)
    assert "neutrino_background" in signature.parameters
    assert signature.parameters["neutrino_background"].default is None
    doc = hierarchy_rhs_neutrino.__doc__ or ""
    assert "byte-identical" in doc
