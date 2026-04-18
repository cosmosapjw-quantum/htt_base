"""bass/collision/polarization.py (LB-4) — E-mode polarisation PSTF tower.

Provides ``PolarizationHierarchyState``, a lightweight dataclass
wrapping a ``PSTFHierarchyState`` for the E-mode multipole tower, and
the algebraic per-ℓ E-mode Thomson collision source

    K^E_2      = −Γ_T (2/5)   E_2 − Γ_T (3/(5√6)) Π_2
    K^E_{ℓ≥3} = −Γ_T E_ℓ                                        (Thomson damping)

At rank 0 and 1 the E-mode source is identically zero — there is no
scalar/vector E-mode at the PSTF level (E is a rank-2-or-higher PSTF
tensor in the Chandrasekhar / Zaldarriaga-Seljak decomposition).

Storage convention (``PolarizationHierarchyState.E``): identical to the
LB-2a temperature tower — ``(2ℓ+1,)`` real-spherical-harmonic packing
per ℓ; ℓ=0 and ℓ=1 slots are retained as zero tensors so that the tower
shares the same flat layout as the temperature state and plugs into the
LB-2b ``hierarchy_rhs_photon`` driver without special-casing.

B-mode is tracked separately at LB-4c; the LB-4 scope covers E only.

References
----------
- Zaldarriaga & Seljak 1997 (astro-ph/9609170) eq (7), (17) — coupling
  of temperature Π_2 and E-mode E_2 through the Thomson source.
- Ma-Bertschinger 1995 (astro-ph/9506072) eq (64) — E-mode polarisation
  Boltzmann equation.
- Chandrasekhar 1960 *Radiative Transfer* Ch IX — classical Thomson
  kernel derivation.
- Ellis, Maartens, MacCallum *Relativistic Cosmology* §5.5.
- ``docs/lowell_bianchi/04_thomson_collision_spec.md §5``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    PSTFTensor,
    zero_hierarchy,
    zero_pstf,
)


__all__ = [
    "PolarizationHierarchyState",
    "zero_polarization_hierarchy",
    "E_mode_collision_source",
    "E_MODE_ELL2_SELF_COEFF",
    "E_MODE_ELL2_TEMPERATURE_COEFF",
]


# ════════════════════════════════════════════════════════════════════
#   Thomson coefficients for the E-mode collision source
# ════════════════════════════════════════════════════════════════════

E_MODE_ELL2_SELF_COEFF: float = -2.0 / 5.0
"""Self-damping coefficient of E_2 in K^E_2: −(2/5)."""

E_MODE_ELL2_TEMPERATURE_COEFF: float = -3.0 / (5.0 * np.sqrt(6.0))
"""Cross-coupling coefficient of Π_2 in K^E_2: −3/(5√6)."""


# ════════════════════════════════════════════════════════════════════
#   PolarizationHierarchyState
# ════════════════════════════════════════════════════════════════════

@dataclass
class PolarizationHierarchyState:
    """E-mode PSTF multipole tower ``{E_0, E_1, …, E_L}``.

    The underlying storage is a ``PSTFHierarchyState`` (identical
    (2ℓ+1)-packed layout as the temperature tower) so that the same
    ``hierarchy_rhs_photon`` driver and the same ``CollisionOperator``
    protocol handle both temperature and E-mode evolution.

    Attributes
    ----------
    E : PSTFHierarchyState
        Underlying multipole container. ``E.L`` ≥ 2 is required because
        the E-mode polarisation has no ℓ=0 or ℓ=1 content; those slots
        are retained in the tower with zero amplitude as layout padding
        (LB-2b driver symmetry).

    Reference: ``docs/lowell_bianchi/04_thomson_collision_spec.md §5``;
    Zaldarriaga-Seljak 1997 §2.
    """

    E: PSTFHierarchyState

    def __post_init__(self) -> None:
        if not isinstance(self.E, PSTFHierarchyState):
            raise TypeError(
                f"E must be a PSTFHierarchyState, got "
                f"{type(self.E).__name__}"
            )
        if self.E.L < 2:
            raise ValueError(
                f"E-mode tower requires L ≥ 2 (polar rank), got L={self.E.L}"
            )

    @property
    def L(self) -> int:
        """Highest multipole retained — delegates to ``self.E.L``."""
        return self.E.L

    @property
    def tensors(self):
        """Shortcut to ``self.E.tensors`` for CollisionOperator parity."""
        return self.E.tensors

    def copy(self) -> "PolarizationHierarchyState":
        return PolarizationHierarchyState(E=self.E.copy())


def zero_polarization_hierarchy(L: int) -> PolarizationHierarchyState:
    """Factory: all-zero E-mode tower up to depth ``L``.

    ``L ≥ 2`` required.

    Reference: 04_thomson_collision_spec.md §5.
    """
    if L < 2:
        raise ValueError(
            f"zero_polarization_hierarchy requires L ≥ 2, got L={L}"
        )
    return PolarizationHierarchyState(E=zero_hierarchy(L))


# ════════════════════════════════════════════════════════════════════
#   E-mode Thomson collision source (per-ℓ)
# ════════════════════════════════════════════════════════════════════

def E_mode_collision_source(
    ell: int,
    E_state: PolarizationHierarchyState,
    Pi_2_packed: Optional[np.ndarray],
    Gamma_T: float,
) -> PSTFTensor:
    """Per-ℓ E-mode Thomson collision source ``K^E_ell``.

    Formulas (Ma-Bertschinger 1995 eq 64; Zaldarriaga-Seljak 1997
    eq 17; spec §5):

        K^E_0      = 0
        K^E_1      = 0
        K^E_2      = −Γ_T (2/5) E_2 − Γ_T (3/(5√6)) Π_2
        K^E_{ℓ≥3} = −Γ_T E_ℓ

    Parameters
    ----------
    ell : int ≥ 0
        Multipole rank.
    E_state : PolarizationHierarchyState
        Current E-mode tower.
    Pi_2_packed : (5,) ndarray or None
        Packed ``Π_2`` components of the temperature quadrupole in the
        same real-SH basis. Required at ℓ=2; ignored otherwise. ``None``
        at ℓ=2 is an error (signals a missing cross-coupling input).
    Gamma_T : float
        Conformal Thomson rate ``τ̇ = a n_e σ_T`` [Mpc⁻¹]. Must be
        non-negative finite.

    Returns
    -------
    PSTFTensor
        Fresh rank-ℓ PSTFTensor (never aliased into ``E_state``).

    Raises
    ------
    ValueError
        If ``ell < 0``, ``Gamma_T`` is negative / non-finite, ``ell``
        exceeds the E tower, or ``Pi_2_packed`` has wrong shape at ℓ=2.

    Reference: 04_thomson_collision_spec.md §5 (TC-06, TC-07, TC-09).
    """
    if ell < 0:
        raise ValueError(f"ell must be non-negative, got {ell}")
    if not np.isfinite(Gamma_T) or Gamma_T < 0.0:
        raise ValueError(
            f"Gamma_T must be non-negative finite, got {Gamma_T}"
        )

    # No E-mode content at ranks 0 or 1.
    if ell < 2:
        return zero_pstf(ell)

    if ell > E_state.L:
        raise ValueError(
            f"ell={ell} exceeds E-mode tower L={E_state.L}"
        )

    E_ell = E_state.tensors[ell]
    if ell == 2:
        if Pi_2_packed is None:
            raise ValueError(
                "E_mode_collision_source at ell=2 requires Pi_2_packed "
                "(temperature quadrupole cross-coupling term)."
            )
        pi2 = np.asarray(Pi_2_packed, dtype=np.float64)
        expected = (5,)
        if pi2.shape != expected:
            raise ValueError(
                f"Pi_2_packed shape {pi2.shape} != {expected}"
            )
        components = Gamma_T * (
            E_MODE_ELL2_SELF_COEFF * E_ell.components
            + E_MODE_ELL2_TEMPERATURE_COEFF * pi2
        )
        return PSTFTensor(ell=2, components=components)

    # ell >= 3: simple Thomson damping.
    return PSTFTensor(
        ell=ell,
        components=-Gamma_T * E_ell.components,
    )
