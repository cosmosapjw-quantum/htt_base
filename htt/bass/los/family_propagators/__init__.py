"""bass/los/family_propagators — Round-16 PR-S8/S9/S10 family LoS propagators.

(Module renamed from the originally-planned ``bass.los.bianchi_propagator``
to avoid colliding with the existing :mod:`bass.los.bianchi_propagator`
module — a Type-I-specific propagator from Week-9 that other code
already depends on. The Round-16 family propagators live in
``bass.los.family_propagators`` instead.)

Implements V5_ROUND16_03_OBSERVABLES_LAYER.md §2.2-§2.4 (closes
Round-16 gap **G6**: no end-to-end output regression for any non-FLRW
family beyond the Type-V→Type-I residual comparator).

Each family has a propagator class implementing the
:class:`BianchiPropagator` protocol:

- :class:`TypeVPropagator` — open hyperbolic with hyperbolic-Legendre
  kernel ``Φ_ℓ(k, η; η_0)`` reducing to the FLRW Bessel ``j_ℓ(kΔη)``
  in the zero-curvature limit (Pereira-Pitrou-Uzan 2007 / Sung-Wandelt
  2010).
- :class:`TypeIXPropagator` — compact SU(2) discrete spectrum with
  Wigner-D propagator over the spectral index ``ℓ_spec``
  (Pontzen-Challinor 2007 §2).
- :class:`SolvableCollocationPropagator` — fallback for II, III, IV,
  VI₀, VI_h, VII₀, VII_h, VIII via collocation on the family-specific
  radial ODE.

The :func:`get_propagator` dispatch returns a propagator instance for
each family supported by Round-16. FLRW + Type I keep the existing
:mod:`bass.los.flrw_bessel_projector` (no override needed).
"""
from __future__ import annotations

from typing import Protocol

import numpy as np

from bass.los.family_propagators.solvable_collocation import (
    SolvableCollocationPropagator,
)
from bass.los.family_propagators.type_ix import TypeIXPropagator
from bass.los.family_propagators.type_v import TypeVPropagator

__all__ = [
    "BianchiPropagator",
    "TypeVPropagator",
    "TypeIXPropagator",
    "SolvableCollocationPropagator",
    "get_propagator",
    "SUPPORTED_FAMILIES",
]


SUPPORTED_FAMILIES: frozenset[str] = frozenset({
    "V", "IX",
    "II", "III", "IV", "VI_0", "VI_h", "VII_0", "VII_h", "VIII",
})


class BianchiPropagator(Protocol):
    """Per-family LoS propagator protocol per V5_ROUND16_03 §2.6."""

    family: str

    def project_T(
        self,
        S_T_history: np.ndarray,
        k_vec: np.ndarray,
        eta_grid: np.ndarray,
        ell_max: int,
    ) -> np.ndarray: ...


def get_propagator(family: str) -> BianchiPropagator:
    """Dispatch table for the family-specific Bianchi LoS propagator.

    For FLRW + Type I the existing
    :mod:`bass.los.flrw_bessel_projector` is the production path (no
    override needed); ``get_propagator`` only handles the families that
    require non-Bessel kernels.
    """
    if family == "V":
        return TypeVPropagator()
    if family == "IX":
        return TypeIXPropagator()
    if family in {"II", "III", "IV", "VI_0", "VI_h", "VII_0", "VII_h", "VIII"}:
        return SolvableCollocationPropagator(family=family)
    raise KeyError(
        f"family={family!r} not in Bianchi propagator registry; "
        f"FLRW + Type I use bass.los.flrw_bessel_projector. "
        f"Supported: {sorted(SUPPORTED_FAMILIES)!r}"
    )
