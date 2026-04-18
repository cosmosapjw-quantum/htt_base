"""bass/hierarchy/closure_interface.py (LB-2a) — Closure strategy hook.

Defines the ``ClosureStrategy`` Protocol and the ``HardCutClosure``
baseline used to terminate the multipole tower at ``ℓ = L_max``. The
driver (LB-2b ``hierarchy_rhs``) calls ``closure.get_closure`` to
obtain values of ``Π_{L+1}`` and ``Π_{L+2}`` that enter T3 and T7.

LB-3 will add ``FreeStreamingClosure``, ``PowerLawClosure`` and
``TCAClosure`` (wrapping the existing W6-04 quadrupole closure in
``bass.closure.quadrupole_tca``).

References
----------
- ``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §6``.
- ``docs/lowell_bianchi/03_closure_truncation_spec.md`` (LB-3 spec).
- Ma-Bertschinger 1995 §6 (truncation schemes for Boltzmann hierarchy).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np

from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
    zero_pstf,
)


__all__ = [
    "ClosureStrategy",
    "HardCutClosure",
]


@runtime_checkable
class ClosureStrategy(Protocol):
    """Pluggable tower-closure interface.

    The driver calls ``get_closure(state, ell_requested)`` whenever it
    needs ``Π_ℓ`` for ``ell_requested`` beyond the tower's top
    multipole. Strategies must return a valid ``PSTFTensor`` of the
    requested rank; raising is acceptable only if the rank is not
    supported by the strategy.
    """

    def get_closure(
        self, state: PSTFHierarchyState, ell_requested: int
    ) -> PSTFTensor: ...


@dataclass(frozen=True)
class HardCutClosure:
    """Π_ℓ = 0 for all ``ell > state.L`` — the simplest viable closure.

    Crude but unconditionally stable: the hierarchy RHS terms T3 and T7
    that reference ``Π_{L+1}`` / ``Π_{L+2}`` receive exact zeros at
    every step. This is the baseline strategy shipped with LB-2a; LB-3
    provides physics-motivated alternatives (free-streaming recursion,
    power-law extrapolation, TCA).

    Reference: Ma-Bertschinger 1995 §6 (hard-cut truncation caveats);
    02_multipole_hierarchy_spec.md §6 (LB-2 default).
    """

    def get_closure(
        self, state: PSTFHierarchyState, ell_requested: int
    ) -> PSTFTensor:
        """Return an all-zero PSTFTensor of the requested rank."""
        if ell_requested < 0:
            raise ValueError(
                f"ell_requested must be non-negative, got {ell_requested}"
            )
        if ell_requested <= state.L:
            # Within-tower queries: return the actual tensor (defensive
            # copy to keep the closure side-effect-free on the state).
            return state.tensors[ell_requested].copy()
        return zero_pstf(ell_requested)


# Silence unused-import warning on np — downstream closure strategies
# (LB-3) will need it directly.
_ = np
