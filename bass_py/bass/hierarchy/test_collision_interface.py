"""Tests for ``bass.hierarchy.collision_interface``.

LB-2a ships only ``ZeroCollisionOperator``; LB-4 will add the full
Thomson PSTF-native operator with E-mode polarization coupling.

Reference: ``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §7``;
``docs/lowell_bianchi/04_thomson_collision_spec.md``.
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy import (
    CollisionOperator,
    PSTFTensor,
    ZeroCollisionOperator,
    zero_hierarchy,
    zero_pstf,
)


def test_zero_collision_conforms_to_protocol() -> None:
    assert isinstance(ZeroCollisionOperator(), CollisionOperator)


def test_zero_collision_returns_zero_at_every_ell() -> None:
    op = ZeroCollisionOperator()
    state = zero_hierarchy(L=4)
    for ell in range(7):
        K = op.evaluate(ell, state)
        assert isinstance(K, PSTFTensor)
        assert K.ell == ell
        assert np.all(K.components == 0.0)


def test_zero_collision_ignores_aux() -> None:
    """Passing arbitrary aux state must not change the zero output."""
    op = ZeroCollisionOperator()
    state = zero_hierarchy(L=2)
    aux_payload = {"tau_dot": 123.0, "v_b": np.array([1.0, 2.0, 3.0])}
    K = op.evaluate(1, state, aux=aux_payload)
    assert K.allclose(zero_pstf(1))


def test_zero_collision_negative_ell_raises() -> None:
    op = ZeroCollisionOperator()
    state = zero_hierarchy(L=0)
    with pytest.raises(ValueError):
        op.evaluate(-2, state)
