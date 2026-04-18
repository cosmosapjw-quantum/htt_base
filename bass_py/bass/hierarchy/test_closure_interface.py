"""Tests for ``bass.hierarchy.closure_interface``.

LB-2a ships only ``HardCutClosure``; LB-3 will add FreeStreaming /
PowerLaw / TCA strategies. These tests pin the Protocol contract and
the closure semantics at tower-boundary queries.

Reference: ``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §6``.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy import (
    ClosureStrategy,
    HardCutClosure,
    PSTFTensor,
    zero_hierarchy,
    zero_pstf,
)


def test_hardcut_conforms_to_protocol() -> None:
    closure = HardCutClosure()
    assert isinstance(closure, ClosureStrategy)


def test_hardcut_returns_zero_above_L() -> None:
    state = zero_hierarchy(L=2)
    closure = HardCutClosure()
    # Within-tower query returns a copy of the state tensor.
    for ell in range(3):
        t = closure.get_closure(state, ell)
        assert isinstance(t, PSTFTensor)
        assert t.ell == ell
        assert t.allclose(zero_pstf(ell))
    # Above-L queries return zero tensors of the requested rank.
    for ell in (3, 4, 5):
        t = closure.get_closure(state, ell)
        assert t.ell == ell
        assert t.allclose(zero_pstf(ell))


def test_hardcut_within_tower_returns_copy() -> None:
    """Modifying the returned PSTF should not mutate the state."""
    state = zero_hierarchy(L=3)
    state.tensors[2].components[0] = 7.0
    closure = HardCutClosure()
    t = closure.get_closure(state, 2)
    t.components[0] = -99.0
    assert state.tensors[2].components[0] == 7.0


def test_hardcut_above_L_returns_zero() -> None:
    state = zero_hierarchy(L=4)
    state.tensors[3].components[:] = 1.0
    closure = HardCutClosure()
    t = closure.get_closure(state, 5)
    assert np.all(t.components == 0.0)


def test_hardcut_negative_ell_raises() -> None:
    state = zero_hierarchy(L=2)
    closure = HardCutClosure()
    with pytest.raises(ValueError):
        closure.get_closure(state, -1)
