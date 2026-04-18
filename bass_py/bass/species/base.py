"""bass/species/base.py (LB-1) — ABC + shared types for species backgrounds.

Defines the canonical ordering, the rest-frame snapshot container, and
the ``SpeciesBackground`` abstract base class. The concrete photon /
neutrino / baryon / CDM / Λ classes inherit from this.

Reference: ``docs/lowell_bianchi/01_species_background_spec.md §2.2``.
Convention: ``docs/lowell_bianchi/00_conventions.md §§6, 7``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union

import numpy as np

_Number = Union[float, np.ndarray]


class SpeciesLabel(Enum):
    """Canonical species ordering (00_conventions.md §6).

    The iteration order γ → ν → b → c → Λ is fixed and relied upon by
    ``SpeciesBackgroundRegistry`` and by downstream multi-species
    solvers (LB-5).
    """
    PHOTON = "\u03B3"    # γ
    NEUTRINO = "\u03BD"  # ν
    BARYON = "b"
    CDM = "c"
    LAMBDA = "\u039B"    # Λ


# The canonical iteration order used by registries and summations.
CANONICAL_ORDER: tuple[SpeciesLabel, ...] = (
    SpeciesLabel.PHOTON,
    SpeciesLabel.NEUTRINO,
    SpeciesLabel.BARYON,
    SpeciesLabel.CDM,
    SpeciesLabel.LAMBDA,
)


@dataclass(frozen=True)
class SpeciesSnapshot:
    """Rest-frame thermodynamic state of one species at one η.

    For LB-1 all species are analytic (photon / neutrino / CDM / Λ) or
    table-backed (baryon); the snapshot captures only macroscopic
    quantities. LB-2 and later add moments of the distribution
    function.

    Attributes
    ----------
    eta : conformal time [Mpc]
    a   : scale factor at ``eta``
    rho : rest-frame energy density [ρ_crit,0 units]
    p   : rest-frame pressure [ρ_crit,0 units]
    T   : temperature [K], or ``None`` if undefined (Λ, CDM)
    w   : equation-of-state p/ρ (defined as 0 when ρ = 0)

    Reference: Ellis §5.1 (perfect fluid); Kolb §3.3.
    """
    eta: float
    a: float
    rho: float
    p: float
    T: Optional[float]
    w: float


def _as_1d(x: _Number) -> tuple[np.ndarray, bool]:
    """Coerce input to 1-D float array; return (array, was_scalar)."""
    arr = np.asarray(x, dtype=np.float64)
    scalar = arr.ndim == 0
    return np.atleast_1d(arr), scalar


def _squeeze_if_scalar(result: np.ndarray, was_scalar: bool) -> _Number:
    """Return a Python float if the original input was scalar."""
    if was_scalar:
        return float(result[0])
    return result


class SpeciesBackground(ABC):
    """Background energy density and pressure for one species.

    All public query methods accept either a Python scalar or a NumPy
    array of conformal times η [Mpc]. Scalar input → scalar output;
    array input → array output with matching shape.

    Out-of-range queries (η outside the shared FLRW-table domain) must
    raise ``ValueError`` rather than silently extrapolating — this is
    enforced at the table layer.

    Reference: Ellis §5.1-5.3 (stress-energy, continuity);
    ``01_species_background_spec.md §2.2``.
    """

    # Class-level attribute set by each concrete subclass.
    label: SpeciesLabel

    # --- Required interface ------------------------------------------------

    @abstractmethod
    def rho_rest(self, eta: _Number) -> _Number:
        """Rest-frame energy density ρ_X(η) in ρ_crit,0 units.

        Reference: Ellis eq (5.1.1) — ρ = T_ab u^a u^b for u^a = n^a at
        orthogonal background.
        """

    @abstractmethod
    def p_rest(self, eta: _Number) -> _Number:
        """Rest-frame pressure p_X(η) in ρ_crit,0 units.

        Reference: Ellis eq (5.1.2) — p = (1/3) T_ab h^ab.
        """

    @abstractmethod
    def dot_rho(self, eta: _Number) -> _Number:
        """Proper-time derivative ρ̇_X = u^a ∇_a ρ_X from continuity.

        At the orthogonal background (no spatial gradients, no species
        bulk velocity) the covariant continuity equation reduces to

            ρ̇_s + Θ (ρ_s + p_s) = C_s            (Ellis §5.3)

        For species with no monopole collision term this becomes

            ρ̇_s = −Θ (1 + w_s) ρ_s.

        Units: [ρ_crit,0 × Mpc⁻¹]. Returned in the natural-units system
        where Θ = 3𝓗/a = 3 H/c has dimension Mpc⁻¹.

        Reference: Ellis eq (5.3.7); ``00_conventions.md §3``.
        """

    @abstractmethod
    def _a_of_eta(self, eta: _Number) -> _Number:
        """Scale factor a(η) from the shared FLRW background table.

        This is a private helper used by ``snapshot`` and by the
        analytic closed forms in concrete subclasses. All concrete
        classes share the same background table so the result is
        identical across species for the same η.
        """

    # --- Default implementations -------------------------------------------

    def w(self, eta: _Number) -> _Number:
        """Equation-of-state parameter w_X = p_X / ρ_X.

        Defined as 0 where ρ = 0, to avoid 0/0 at species that can
        vanish asymptotically (physically only relevant for the
        cosmological constant at a=0, where ρ remains finite).

        Reference: Ellis §5.1.
        """
        arr_eta, scalar = _as_1d(eta)
        rho = np.asarray(self.rho_rest(arr_eta), dtype=np.float64)
        p = np.asarray(self.p_rest(arr_eta), dtype=np.float64)
        out = np.zeros_like(rho)
        mask = rho > 0.0
        out[mask] = p[mask] / rho[mask]
        return _squeeze_if_scalar(out, scalar)

    def temperature(self, eta: _Number) -> Optional[_Number]:
        """Temperature T_X(η) [K], or ``None`` if undefined.

        Λ and CDM return ``None`` unconditionally; photon and neutrino
        override to return a T ∝ 1/a; baryon delegates to HyRec.
        """
        return None

    def snapshot(self, eta: float) -> SpeciesSnapshot:
        """Convenience one-η container with (a, ρ, p, T, w)."""
        rho = float(np.asarray(self.rho_rest(np.atleast_1d(eta)))[0])
        p = float(np.asarray(self.p_rest(np.atleast_1d(eta)))[0])
        w = p / rho if rho > 0 else 0.0
        T_out = self.temperature(np.atleast_1d(eta))
        if T_out is None:
            T_val: Optional[float] = None
        else:
            T_val = float(np.asarray(T_out)[0])
        return SpeciesSnapshot(
            eta=float(eta),
            a=float(np.asarray(self._a_of_eta(np.atleast_1d(eta)))[0]),
            rho=rho, p=p, T=T_val, w=w,
        )
