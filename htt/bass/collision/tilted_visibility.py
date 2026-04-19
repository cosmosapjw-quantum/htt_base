"""bass/collision/tilted_visibility.py (LB-4, Layer A) — lowell §11.3
direction-resolved visibility wrapper.

Composes (i) the scalar HyRec-based Thomson rate
``Γ_T(η) = a n_e x_e σ_T`` from ``bass.species.baryon.BaryonBackground``
with (ii) a **non-perturbative** Lorentz-boost factor

    B(η, e) = cosh β_e(η) + sinh β_e(η) (ê · v̂_e(η))
            ≡ γ_e(η) (1 + v_e(η) · ê)                  (exact)

to produce the direction-resolved

    Γ̃_T(η, e) = Γ_T(η) × B(η, e)                         [Mpc⁻¹]
    κ̃(η, e)   = ∫_η^{η_0} Γ̃_T(η', e) dη'                 [dimensionless]
    g̃(η, e)   = Γ̃_T(η, e) × exp(−κ̃(η, e))               [Mpc⁻¹]

**No ``1 + v_e · e`` linearisation anywhere** (Layer A hard constraint):
the code uses ``γ × (1 + v_e · ê)`` which is the *exact* rearrangement
of ``cosh β + sinh β (ê·v̂_e)``; both forms agree to machine precision
at every β and the identity is enforced by test TV-04.

Scope
-----
Layer A provides *scalar* direction-resolved Γ̃_T, κ̃, g̃ for LoS and
visibility-weighted-source machinery; it does **not** modify the PSTF
collision kernel itself. Layer B (LB-4b) boosts the full PSTF Thomson
source ``K_{A_ℓ}`` and stays deferred until the tilted species registry
(LB-1b) is in place.

FLRW-reduction invariant: constructed with ``v_e = lambda η: zeros(3)``
the wrapper satisfies ``Γ̃_T(η, e) == Γ_T(η)`` and ``g̃(η, e) == g(η)``
for every direction ``e``. Enforced by test TV-01.

References
----------
- lowell §11.3 (direction-resolved visibility formulas).
- lowell §4 (frame split: transport in ``n^a``, collision / visibility
  in ``u_e^a``).
- Ellis, Maartens, MacCallum §4.2 – §4.3 (1+3 decomposition).
- Pontzen-Challinor 2007 (non-perturbative tilt parametrisation).
- ``docs/lowell_bianchi/00_conventions.md §2``, ``§4``.
- ``docs/lowell_bianchi/04_thomson_collision_spec.md §8.1``.
- Companion Y-Block module ``bass.tilt.species_tilt``.
"""
from __future__ import annotations

from typing import Callable, Union

import numpy as np

from bass.species.baryon import BaryonBackground


__all__ = [
    "TiltedVisibility",
    "scalar_visibility",
]


_Number = Union[float, np.floating]


def _as_scalar_float(x) -> float:
    """Coerce a 0-d ndarray / python scalar / numpy scalar to ``float``."""
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim != 0:
        raise ValueError(
            f"expected scalar, got shape {arr.shape}"
        )
    return float(arr)


class TiltedVisibility:
    """Direction-resolved optical-depth / visibility wrapper (lowell §11.3).

    Composes the scalar HyRec-based ``Γ_T(η)`` supplied by a
    ``BaryonBackground`` with a non-perturbative Lorentz-boost factor
    ``B(η, e)`` computed from a user-supplied ``v_e(η)`` callable.
    At ``v_e ≡ 0`` every direction-resolved quantity reduces to its
    scalar baryon-background analogue (TV-01).

    Parameters
    ----------
    baryon : BaryonBackground
        Supplies ``tau_dot(η) = Γ_T(η)`` and the shared FLRW η-grid.
        Must satisfy the LB-1 contract (``tau_dot``, ``visibility``,
        ``_bg`` attribute exposing the ``FLRWBackgroundTable``).
    v_e : Callable[[float], (3,) ndarray]
        Normal-frame tetrad components of the electron 3-velocity.
        ``v_e(η)`` must return a real ``(3,)`` array with
        ``|v_e| < 1``; superluminal tilts raise ``ValueError``.
    beta_from_v : bool, default True
        Kept for API parity with spec §9.4. Internal storage is always
        the 3-velocity ``v_e``; the rapidity ``β_e = atanh|v_e|`` and
        ``γ_e = cosh β_e`` are derived non-perturbatively via
        ``1/sqrt(1 − |v_e|²)``. When ``False`` the flag is accepted as
        documentation that the caller has already performed the
        β-parametrisation externally; the numerical path is identical.

    Raises
    ------
    TypeError
        If ``baryon`` is not a ``BaryonBackground`` or ``v_e`` is not
        callable.

    Reference: lowell §11.3; 00_conventions.md §4;
    04_thomson_collision_spec.md §8.1, §9.4.
    """

    def __init__(
        self,
        baryon: BaryonBackground,
        v_e: Callable[[float], np.ndarray],
        *,
        beta_from_v: bool = True,
    ) -> None:
        if not isinstance(baryon, BaryonBackground):
            raise TypeError(
                f"baryon must be a BaryonBackground, got "
                f"{type(baryon).__name__}"
            )
        if not callable(v_e):
            raise TypeError(
                f"v_e must be callable (η -> (3,) ndarray), got "
                f"{type(v_e).__name__}"
            )
        self._baryon = baryon
        self._v_e_func = v_e
        self._beta_from_v = bool(beta_from_v)

        # Shared FLRW η-grid (monotonically increasing to η_0).
        self._eta_grid = np.asarray(baryon._bg.eta, dtype=np.float64).copy()
        if self._eta_grid.ndim != 1 or self._eta_grid.size < 2:
            raise ValueError(
                "BaryonBackground.bg.eta must be a 1-D grid with ≥ 2 points"
            )
        # Evaluate τ̇(η) on the grid with graceful zero-fallback for
        # grid points outside the recombination table's z-range.  The
        # FLRW table typically extends to pre-recombination z ≈ 10⁸
        # while the HyRec fixture starts at z = 8000; we set τ̇ = 0
        # there as a Layer A simplification (this predates any photon
        # decoupling physics so the integrated κ̃ contribution is
        # negligible compared to the recombination peak).
        tau_dot_grid = np.zeros_like(self._eta_grid)
        for i, eta_i in enumerate(self._eta_grid):
            try:
                tau_dot_grid[i] = float(baryon.tau_dot(float(eta_i)))
            except ValueError:
                tau_dot_grid[i] = 0.0
        self._tau_dot_grid = tau_dot_grid

    # --- internal helpers -----------------------------------------------

    def _v_at(self, eta: _Number) -> np.ndarray:
        """Return ``v_e(η)`` as a validated (3,) float64 array."""
        v = np.asarray(self._v_e_func(float(eta)), dtype=np.float64)
        if v.shape != (3,):
            raise ValueError(
                f"v_e(η={eta}) returned shape {v.shape}; expected (3,)"
            )
        v_sq = float(np.dot(v, v))
        if v_sq >= 1.0 or not np.isfinite(v_sq):
            raise ValueError(
                f"|v_e(η={eta})|² = {v_sq:.6f} ≥ 1: superluminal / "
                f"non-finite tilt"
            )
        return v

    @staticmethod
    def _validate_direction(e: np.ndarray) -> np.ndarray:
        """Normalise a direction vector and validate finiteness."""
        arr = np.asarray(e, dtype=np.float64)
        if arr.shape != (3,):
            raise ValueError(
                f"direction e must have shape (3,), got {arr.shape}"
            )
        if not np.all(np.isfinite(arr)):
            raise ValueError(
                f"direction e must be finite, got {arr}"
            )
        norm = float(np.linalg.norm(arr))
        if norm == 0.0:
            raise ValueError("direction e has zero length")
        return arr / norm

    # --- §11.3 direction-resolved scalars --------------------------------

    def gamma_e(self, eta: _Number) -> float:
        """``γ_e(η) = cosh β_e(η) = 1 / √(1 − |v_e|²)``.

        Reduces to ``1`` when ``v_e ≡ 0``.

        Reference: lowell §11.3 eq (11.3.1); Ellis §4.2.
        """
        v = self._v_at(eta)
        return 1.0 / float(np.sqrt(1.0 - float(np.dot(v, v))))

    def boost_factor(self, eta: _Number, e: np.ndarray) -> float:
        """``B(η, e) = cosh β_e + sinh β_e (ê · v̂_e)`` (exact).

        Implemented as the algebraically-equivalent
        ``γ_e (1 + v_e · ê)`` to avoid division by ``|v_e|`` at
        ``v_e = 0``. Both forms agree to machine precision; the
        identity is documented in the module header and enforced by
        TV-04 / TV-08.

        Reference: lowell §11.3 eq (11.3.1); spec §8.1.
        """
        v = self._v_at(eta)
        e_hat = self._validate_direction(e)
        v_sq = float(np.dot(v, v))
        gamma = 1.0 / float(np.sqrt(1.0 - v_sq))
        # γ (1 + v·ê) ≡ cosh β + sinh β (ê·v̂) — no linear truncation.
        return gamma * (1.0 + float(np.dot(v, e_hat)))

    def Gamma_T(self, eta: _Number, e: np.ndarray) -> float:
        """``Γ̃_T(η, e) = Γ_T(η) × B(η, e)`` [Mpc⁻¹].

        Scalar ``Γ_T(η)`` is delegated to ``baryon.tau_dot`` (LB-1 HyRec
        fixture); the direction dependence is injected only through
        ``B(η, e)``.  Returns ``0`` when ``η`` maps to a redshift outside
        the recombination-table domain (matches the grid-cache
        fallback in ``__init__``).

        Reference: lowell §11.3 eq (11.3.1).
        """
        try:
            tau_dot = _as_scalar_float(self._baryon.tau_dot(float(eta)))
        except ValueError:
            tau_dot = 0.0
        return tau_dot * self.boost_factor(eta, e)

    def kappa(self, eta: _Number, e: np.ndarray) -> float:
        """``κ̃(η, e) = ∫_η^{η_0} Γ̃_T(η', e) dη'``.

        Numerical line integral on the shared FLRW η-grid using
        ``np.trapezoid``. For time-varying ``v_e(η)`` the integrand is
        evaluated grid-point-by-grid-point; for constant ``v_e`` this
        collapses to ``B × κ(η)`` via a single multiplication but
        that shortcut is **not** taken here — it would complicate the
        ``v_e(η) ≡ 0`` / ``v_e(η) ≠ 0`` dispatch and is not needed at
        LB-4 scope.

        The lower limit ``eta`` is inserted at the front of the
        sub-grid (with a linearly-interpolated integrand) so the result
        respects the requested starting point even when it falls
        between grid points.

        Reference: lowell §11.3 eq (11.3.2); Ma-Bertschinger 1995 eq (70).
        """
        eta_f = float(eta)
        e_hat = self._validate_direction(e)

        eta_grid = self._eta_grid
        eta_today = float(eta_grid[-1])
        if eta_f >= eta_today:
            return 0.0
        if eta_f < float(eta_grid[0]):
            raise ValueError(
                f"eta={eta_f} below FLRW grid minimum "
                f"{float(eta_grid[0])}"
            )

        # Per-grid-point boost factor evaluated via self.boost_factor,
        # which re-derives γ / v at every η via self._v_at (independent
        # evaluation of v_e(η) per point — time-varying v_e honoured).
        idx_lo = int(np.searchsorted(eta_grid, eta_f, side="right"))
        # eta_sub covers [eta, η_grid[idx_lo], …, η_today].
        n_sub = 1 + (eta_grid.size - idx_lo)
        eta_sub = np.empty(n_sub, dtype=np.float64)
        gtilde_sub = np.empty(n_sub, dtype=np.float64)
        eta_sub[0] = eta_f
        gtilde_sub[0] = self.Gamma_T(eta_f, e_hat)
        for j, k in enumerate(range(idx_lo, eta_grid.size), start=1):
            eta_k = float(eta_grid[k])
            eta_sub[j] = eta_k
            # Reuse the cached tau_dot grid to skip the query.
            tau_dot_k = float(self._tau_dot_grid[k])
            v = self._v_at(eta_k)
            v_sq = float(np.dot(v, v))
            gamma = 1.0 / float(np.sqrt(1.0 - v_sq))
            boost_k = gamma * (1.0 + float(np.dot(v, e_hat)))
            gtilde_sub[j] = tau_dot_k * boost_k

        return float(np.trapezoid(gtilde_sub, eta_sub))

    def g(self, eta: _Number, e: np.ndarray) -> float:
        """``g̃(η, e) = Γ̃_T(η, e) × exp(−κ̃(η, e))`` [Mpc⁻¹].

        Reduces to ``baryon.visibility(η)`` when ``v_e ≡ 0``.

        Reference: lowell §11.3 eq (11.3.3); Baumann §3.10.
        """
        return self.Gamma_T(eta, e) * float(np.exp(-self.kappa(eta, e)))


# ════════════════════════════════════════════════════════════════════
#   Convenience wrapper: purely-scalar visibility (Γ_T, κ, g)
# ════════════════════════════════════════════════════════════════════

def scalar_visibility(
    baryon: BaryonBackground, eta: _Number,
) -> tuple[float, float, float]:
    """Return ``(Γ_T, κ, g)`` at η from the baryon background.

    Thin convenience around ``baryon.tau_dot``, ``baryon.kappa``,
    ``baryon.visibility`` used to cross-check ``TiltedVisibility`` in
    its FLRW limit (TV-01).

    Reference: spec §9.4; Ma-Bertschinger 1995 eq (70).
    """
    gamma = _as_scalar_float(baryon.tau_dot(float(eta)))
    kap = _as_scalar_float(baryon.kappa(float(eta)))
    g = _as_scalar_float(baryon.visibility(float(eta)))
    return gamma, kap, g
