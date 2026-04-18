"""bass/hierarchy/collision_interface.py (LB-2a) — Collision source hook.

Defines the ``CollisionOperator`` Protocol that the driver (LB-2b
``hierarchy_rhs``) calls to obtain the source ``K_{A_ℓ}`` at each ℓ,
and provides ``ZeroCollisionOperator`` for collisionless species
(neutrinos after decoupling, or photons in a Γ_T = 0 diagnostic
scenario).

LB-4 will deliver ``ThomsonCollisionOperator`` with full PSTF-native
coupling to the E-mode polarization hierarchy.

References
----------
- Ellis, Maartens, MacCallum §5.5 — Thomson scattering tensor.
- Kolb-Turner §5.1 — Boltzmann equation and collision terms.
- ``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §7``.
- ``docs/lowell_bianchi/04_thomson_collision_spec.md`` (LB-4 spec).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

import numpy as np

from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor, zero_pstf


__all__ = [
    "CollisionOperator",
    "ZeroCollisionOperator",
]


@runtime_checkable
class CollisionOperator(Protocol):
    """Pluggable collision-source interface.

    At every η the driver calls ``evaluate(ell, state, aux)`` to obtain
    ``K_{A_ℓ}`` in PSTF-packed form. Operators may consume ancillary
    state (``aux``) such as baryon velocity, E-mode polarization
    components, and the differential optical depth ``τ̇``.
    """

    def evaluate(
        self,
        ell: int,
        state: PSTFHierarchyState,
        aux: Optional[object] = None,
    ) -> PSTFTensor: ...


@dataclass(frozen=True)
class ZeroCollisionOperator:
    """``K_{A_ℓ} = 0`` for all ℓ — collisionless transport.

    Use for neutrinos (after decoupling) and for diagnostic Γ_T = 0
    photon scenarios used to validate the dissipative-free hierarchy.

    Reference: 02_multipole_hierarchy_spec.md §1.2 (neutrino collision
    source); Kolb-Turner §5.1.
    """

    def evaluate(
        self,
        ell: int,
        state: PSTFHierarchyState,
        aux: Optional[object] = None,
    ) -> PSTFTensor:
        if ell < 0:
            raise ValueError(f"ell must be non-negative, got {ell}")
        return zero_pstf(ell)


# Silence unused-import warning.
_ = np
