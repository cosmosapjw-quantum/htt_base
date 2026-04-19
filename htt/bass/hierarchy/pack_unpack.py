"""bass/hierarchy/pack_unpack.py (LB-5) — combined state vector utilities.

Pack/unpack the combined integrator state ``Y(η)`` that ``LowellBianchiIntegrator``
hands to ``scipy.integrate.solve_ivp``. The layout is **fixed** at spec §2.1
and reproduced here as the single source of truth; see
``docs/lowell_bianchi/05_integrator_spec.md §2`` for the table.

Packing order (for default ``L_max = 6``)::

    index 0                 — a(η)                         (scale factor)
    index 1..2              — Σ_+(η), Σ_−(η)               (tetrad shear)
    index 3..(3+T_tot)      — photon temperature tower     (ℓ = 0..L_max)
    index (3+T_tot)..+E_tot — photon E-mode tower          (ℓ = 0..L_max,
                                                            ℓ<2 kept as
                                                            zero-padding)
    last 4 indices          — neutrino reduced 4-scalars:
                              Δ_ν, q_ν, π_ν, G_3            (spec §2.1)

where ``T_tot = hierarchy_total_size(L_max) = (L_max + 1)²`` and
``E_tot`` also equals ``(L_max + 1)²`` — the E-mode tower is stored
with the same flat layout as the temperature tower and the ``ℓ < 2``
slots are held at zero by construction (see
``04_thomson_collision_spec.md §5`` for why those slots exist).

The layout is deliberately **dense and regular**: all slicing logic
flows through the ``slice_*`` helpers below so a future layout change
needs only this file + the tests.

References
----------
- ``docs/lowell_bianchi/05_integrator_spec.md §1, §2`` (fixed index
  table and total-size formula).
- ``docs/lowell_bianchi/02_multipole_hierarchy_spec.md §2.5, §9.3``
  (``PSTFHierarchyState`` flat layout — reused slot-by-slot).
- Ma-Bertschinger 1995 §4 (combined state vector in the FLRW
  Boltzmann system); Ellis §6.1 (conservation laws).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from bass.collision.polarization import PolarizationHierarchyState
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    hierarchy_total_size,
    pack_hierarchy,
    unpack_hierarchy,
    zero_hierarchy,
)


__all__ = [
    "BACKGROUND_SIZE",
    "NEUTRINO_REDUCED_SIZE",
    "CombinedState",
    "combined_total_size",
    "slice_a",
    "slice_sigma_pm",
    "slice_photon_T",
    "slice_photon_E",
    "slice_neutrino_reduced",
    "pack_combined_state",
    "unpack_combined_state",
]


# ════════════════════════════════════════════════════════════════════
#   Size constants
# ════════════════════════════════════════════════════════════════════

BACKGROUND_SIZE: int = 3
"""(a, Σ_+, Σ_−) — three scalars at the head of the state vector."""

NEUTRINO_REDUCED_SIZE: int = 4
"""(Δ_ν, q_ν, π_ν, G_3) — four scalars at the tail of the state vector
(lowell §9.3 "low-ℓ retained set"; spec §1 and §2.1)."""


def combined_total_size(L_max: int) -> int:
    """Total number of scalars in the packed combined state vector.

    ``3 + (L_max+1)² + (L_max+1)² + 4`` — background, temperature tower,
    E-mode tower, reduced neutrino block. See
    ``05_integrator_spec.md §1.1`` for the breakdown.
    """
    if L_max < 0:
        raise ValueError(f"L_max must be non-negative, got {L_max}")
    T_tot = hierarchy_total_size(L_max)
    E_tot = hierarchy_total_size(L_max)
    return BACKGROUND_SIZE + T_tot + E_tot + NEUTRINO_REDUCED_SIZE


# ════════════════════════════════════════════════════════════════════
#   Slice accessors (spec §2.2)
# ════════════════════════════════════════════════════════════════════

def slice_a(L_max: int) -> slice:
    """Index slice for the scale factor ``a(η)`` (one scalar)."""
    _ = L_max  # signature parity with other slicers
    return slice(0, 1)


def slice_sigma_pm(L_max: int) -> slice:
    """Index slice for ``(Σ_+, Σ_−)`` (two scalars at indices 1, 2)."""
    _ = L_max
    return slice(1, 3)


def slice_photon_T(L_max: int) -> slice:
    """Index slice for the photon temperature tower ``Π_0..Π_{L_max}``."""
    start = BACKGROUND_SIZE
    return slice(start, start + hierarchy_total_size(L_max))


def slice_photon_E(L_max: int) -> slice:
    """Index slice for the photon E-mode tower ``E_0..E_{L_max}``.

    ``ℓ < 2`` slots are stored as zero-padding (see
    ``04_thomson_collision_spec.md §5`` — ``PolarizationHierarchyState``
    requires ``L ≥ 2`` and keeps ℓ=0,1 as zero tensors for layout parity).
    """
    start = BACKGROUND_SIZE + hierarchy_total_size(L_max)
    return slice(start, start + hierarchy_total_size(L_max))


def slice_neutrino_reduced(L_max: int) -> slice:
    """Index slice for the 4-scalar neutrino reduced fluid block."""
    start = (
        BACKGROUND_SIZE
        + hierarchy_total_size(L_max)
        + hierarchy_total_size(L_max)
    )
    return slice(start, start + NEUTRINO_REDUCED_SIZE)


# ════════════════════════════════════════════════════════════════════
#   Combined state dataclass
# ════════════════════════════════════════════════════════════════════

@dataclass
class CombinedState:
    """Structured view of the unpacked combined state at one η.

    Attributes
    ----------
    a : float
        Scale factor ``a(η)``.
    Sigma_plus, Sigma_minus : float
        Axisymmetric tetrad shear amplitudes. For FLRW both are zero.
    photon_T : PSTFHierarchyState
        Photon temperature multipole tower ``{Π_0, …, Π_{L_max}}``.
    photon_E : PolarizationHierarchyState
        Photon E-mode multipole tower; ``L ≥ 2``.
    neutrino_reduced : ndarray of shape (4,)
        Reduced neutrino fluid moments (Δ_ν, q_ν, π_ν, G_3) — see
        ``neutrino_reduced.py`` for the exact definitions (spec §3, §12).

    Reference: 05_integrator_spec.md §1.2.
    """

    a: float
    Sigma_plus: float
    Sigma_minus: float
    photon_T: PSTFHierarchyState
    photon_E: PolarizationHierarchyState
    neutrino_reduced: np.ndarray

    @property
    def L_max(self) -> int:
        return self.photon_T.L


# ════════════════════════════════════════════════════════════════════
#   Pack / unpack
# ════════════════════════════════════════════════════════════════════

def pack_combined_state(
    *,
    a: float,
    Sigma_plus: float,
    Sigma_minus: float,
    photon_T: PSTFHierarchyState,
    photon_E: PolarizationHierarchyState,
    neutrino_reduced: np.ndarray,
    L_max: int,
) -> np.ndarray:
    """Pack a structured state into the flat layout consumed by ``solve_ivp``.

    Every field is validated against ``L_max`` before copying; the
    output is a fresh contiguous float64 array of length
    ``combined_total_size(L_max)``.

    Reference: 05_integrator_spec.md §2.1.
    """
    if L_max < 0:
        raise ValueError(f"L_max must be non-negative, got {L_max}")
    if photon_T.L != L_max:
        raise ValueError(
            f"photon_T.L={photon_T.L} != L_max={L_max}"
        )
    if photon_E.L != L_max:
        raise ValueError(
            f"photon_E.L={photon_E.L} != L_max={L_max}"
        )
    nu = np.asarray(neutrino_reduced, dtype=np.float64)
    if nu.shape != (NEUTRINO_REDUCED_SIZE,):
        raise ValueError(
            f"neutrino_reduced shape {nu.shape} != "
            f"({NEUTRINO_REDUCED_SIZE},)"
        )

    total = combined_total_size(L_max)
    out = np.empty(total, dtype=np.float64)
    out[slice_a(L_max)] = float(a)
    out[slice_sigma_pm(L_max)] = [float(Sigma_plus), float(Sigma_minus)]
    out[slice_photon_T(L_max)] = pack_hierarchy(photon_T)
    out[slice_photon_E(L_max)] = pack_hierarchy(photon_E.E)
    out[slice_neutrino_reduced(L_max)] = nu
    return out


def unpack_combined_state(
    y: np.ndarray, L_max: int,
) -> CombinedState:
    """Inverse of ``pack_combined_state``.

    Round-trips bit-identically (test I-01 pins ``atol = 1e-14``).

    Reference: 05_integrator_spec.md §2.1.
    """
    if L_max < 0:
        raise ValueError(f"L_max must be non-negative, got {L_max}")
    arr = np.asarray(y, dtype=np.float64)
    expected = combined_total_size(L_max)
    if arr.shape != (expected,):
        raise ValueError(
            f"y shape {arr.shape} != ({expected},) for L_max={L_max}"
        )
    a = float(arr[slice_a(L_max)][0])
    sigma = arr[slice_sigma_pm(L_max)]
    photon_T = unpack_hierarchy(arr[slice_photon_T(L_max)], L_max)
    photon_E = PolarizationHierarchyState(
        E=unpack_hierarchy(arr[slice_photon_E(L_max)], L_max),
    )
    neutrino_reduced = arr[slice_neutrino_reduced(L_max)].copy()
    return CombinedState(
        a=a,
        Sigma_plus=float(sigma[0]),
        Sigma_minus=float(sigma[1]),
        photon_T=photon_T,
        photon_E=photon_E,
        neutrino_reduced=neutrino_reduced,
    )


# Silence unused-import warning — ``zero_hierarchy`` is re-exported for
# downstream IC constructors that want the symbol from the same module.
_ = zero_hierarchy
_ = Tuple
