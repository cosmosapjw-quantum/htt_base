"""bass/species/tilted.py (FB-3.1) — Tilted species-background wrapper.

Species-level overlay that carries a non-perturbative tilt boost
``(β, v̂_e)`` on top of an orthogonal ``SpeciesBackground`` (photon /
neutrino / baryon / CDM / Λ). The wrapper exposes the tilt-projected
``(ρ̃, p̃, v^a)`` surface required by the Phase FB-3 hierarchy-coupling
rotation (FB-3.2+), while **preserving the orthogonal β=0 path
bit-for-bit** so that all LB-1 … FB-2 regression anchors keep holding
byte-for-byte.

Convention (prompt SSOT — FB-3 handoff from AUDIT_PHASE_FB2 §FB-3 preview)::

    u^a(total) = γ (u_0^a + v^a),     v^a = β v̂_e^a,
    γ = (1 − β²)^{−1/2},              |v̂_e| = 1,    0 ≤ β < 1.

The tilt-projected thermodynamic surface for one species in the
``n^a`` frame is (King & Ellis 1973 §2-§3; Ellis-Maartens-MacCallum
2012 §5.4 eqs 5.12-5.14):

    ρ̃   =  γ² (ρ + p) − p,
    p̃   =  p + (1/3) γ² (ρ + p) β²,
    q̃^a =  γ² (ρ + p) v^a        [deferred to FB-3.2 consumers],
    π̃^ab =  γ² (ρ + p) v^⟨a v^b⟩ [deferred to FB-3.2 consumers].

FB-3.1 scope
------------
This rotation is **abstraction only**:

- Expose ``rho_tilde(eta)``, ``p_tilde(eta)``, ``v_vector(eta)`` plus
  the ``gamma`` / ``gamma_sq`` properties — enough surface for
  ``TiltedSpeciesBackground`` to be *consumed* by the hierarchy driver.
- β=0 path returns the base-species values **by short-circuit** so
  that no finite-precision cancellation can disturb the LB-1 byte
  anchor. This is the single non-negotiable invariant of FB-3.1.

Non-goals (explicitly deferred)
-------------------------------
- Boltzmann hierarchy wire-up (``hierarchy_rhs_photon`` tilt vectors):
  FB-3.2.
- Non-perturbative boost kernel on PSTF moments (Wigner-D /
  direction-resolved projection): FB-3.2 / FB-5.2.
- Thomson kernel full Lorentz (Layer B): FB-4.

References
----------
- King & Ellis 1973, *CMP* 31, 209 (tilted-fluid kinematic split).
- Ellis, Maartens & MacCallum 2012, *Relativistic Cosmology* §5.4
  (tilted perfect fluid, eqs 5.12-5.14).
- ``docs/lowell_bianchi/lowell_bianchi_solver_reference.md §7``
  (tilt SSOT).
- ``docs/lowell_bianchi/00_conventions.md §2`` (frame-split rule +
  ``v̂_e`` default — FB02-F1 resolved here).
- Companion ``bass.tilt.species_tilt`` (Y-Block full
  ``(μ, q, p_iso, π)`` decomposition; FB-3.1 consumes the same
  algebra, scoped to the LB-1 species surface).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Union

import numpy as np

from bass.species.base import (
    SpeciesBackground, _as_1d, _squeeze_if_scalar,
)


__all__ = [
    "TiltedSpeciesBackground",
    "V_HAT_E_DEFAULT",
    "V_HAT_NORM_TOL",
    # FB-3.5 β-gate reparametrisation
    "assert_tilt_admissible",
    "rapidity_to_velocity",
    "velocity_to_rapidity",
]


_Number = Union[float, np.ndarray]


# ──────────────────────────────────────────────────────────────────────
# Convention SSOT — ``v̂_e`` default (FB02-F1 resolution, 00_conventions §2)
# ──────────────────────────────────────────────────────────────────────

V_HAT_E_DEFAULT: Tuple[float, float, float] = (1.0, 0.0, 0.0)
"""Default tilt direction — spatial unit vector aligned with the first
tetrad axis ``e_1``.

Matches ``BianchiCosmology.v_hat_e`` (FB-0.2 SSOT) and the PSTF
m-basis alignment rule (``00_conventions §5.4``: m=0 along the
Σ_+ eigenvector). Any consumer that needs the canonical default
(the FB-3.2 hierarchy driver, LB-4 Layer-A visibility, FB-4
Thomson Layer-B boost) MUST import this constant rather than
re-literal-ing ``(1, 0, 0)`` so that the FB02-F1 cross-reference
stays single-sourced.
"""

V_HAT_NORM_TOL: float = 1e-10
"""Unit-norm tolerance on ``|v̂_e|² − 1``. Tight because the caller
supplies a literal unit vector; drift past this threshold is a user
error (not integrator noise)."""


# ──────────────────────────────────────────────────────────────────────
# FB-3.5 — β-gate reparametrisation helpers
#
# Parent-plan decision D4 = (a) nominates rapidity as the
# decision-level SSOT for tilt parameters. FB-3.1 / FB-3.2 / FB-3.3 /
# FB-3.4 shipped the velocity storage (``self.beta = |v|``) which is
# the byte-identical regression anchor for every prior test; migrating
# the *internal* storage to rapidity would break that anchor because
# ``tanh(atanh(β))`` is not bitwise identical to ``β`` in float64.
# FB-3.5 therefore closes the reparametrisation carry via two
# complementary moves:
#
# 1. Expose a ``.rapidity`` derived property on
#    ``TiltedSpeciesBackground`` and a matching ``from_rapidity``
#    classmethod, so downstream modules (FB-8 `ObserverBoost`, the
#    FB-11 inference driver) can consume the rapidity surface
#    directly without crossing the velocity ↔ rapidity boundary
#    themselves.
# 2. Publish a single shared admissibility gate
#    ``assert_tilt_admissible(β, v̂_e)`` that every tilt consumer (the
#    species-level wrapper here, the FB-8 ``ObserverBoost``, the
#    FB-11 priors module) calls to validate a ``(β, v̂_e)`` pair
#    eagerly. The gate's guarantees are identical to the
#    ``__post_init__`` guards in the wrapper; centralising them
#    prevents drift between the three surfaces.
# ──────────────────────────────────────────────────────────────────────


def velocity_to_rapidity(beta: float) -> float:
    """Return ``atanh(β)`` for ``β ∈ [0, 1)``.

    ``β = 0`` returns exactly ``0.0`` (no numpy round-off). Raises
    ``ValueError`` for any value outside the admissible domain —
    uses the same guard set as
    :func:`assert_tilt_admissible`.
    """
    b = float(beta)
    if not np.isfinite(b):
        raise ValueError(f"beta must be finite; got beta={beta!r}")
    if b < 0.0:
        raise ValueError(
            f"beta must be non-negative; got beta={b!r}. Sign of the "
            f"boost lives in v̂_e, not in β."
        )
    if b >= 1.0:
        raise ValueError(
            f"beta must satisfy 0 ≤ β < 1 (superluminal guard); "
            f"got beta={b!r}."
        )
    if b == 0.0:
        return 0.0
    return float(np.arctanh(b))


def rapidity_to_velocity(rapidity: float) -> float:
    """Return ``tanh(η)`` for ``η ≥ 0``.

    ``η = 0`` returns exactly ``0.0``. Raises ``ValueError`` for
    negative or non-finite input.
    """
    r = float(rapidity)
    if not np.isfinite(r):
        raise ValueError(f"rapidity must be finite; got rapidity={rapidity!r}")
    if r < 0.0:
        raise ValueError(
            f"rapidity must be non-negative; got rapidity={r!r}. Sign "
            f"of the boost lives in v̂_e, not in rapidity."
        )
    if r == 0.0:
        return 0.0
    return float(np.tanh(r))


def assert_tilt_admissible(
    beta: float,
    v_hat_e: Tuple[float, float, float],
    *,
    tol: float = V_HAT_NORM_TOL,
) -> None:
    """Single SSOT admissibility gate for every tilt ``(β, v̂_e)`` pair.

    Raises ``ValueError`` on any of the following:

    - ``β`` is non-finite,
    - ``β`` is negative,
    - ``β ≥ 1`` (superluminal),
    - ``v_hat_e`` is not a length-3 tuple / iterable,
    - ``|v̂_e|² − 1`` exceeds ``tol``.

    Silently returns ``None`` on admissible input. Centralises the
    FB-3.1 ``__post_init__`` guards so that FB-8 ``ObserverBoost``
    and the FB-11 priors module can reuse the identical check
    without copy-paste.
    """
    b = float(beta)
    if not np.isfinite(b):
        raise ValueError(f"beta must be finite; got beta={beta!r}")
    if b < 0.0:
        raise ValueError(
            f"beta must be non-negative; got beta={b!r}. Sign of the "
            f"boost lives in v̂_e, not in β."
        )
    if b >= 1.0:
        raise ValueError(
            f"beta must satisfy 0 ≤ β < 1 (superluminal guard); "
            f"got beta={b!r}. See 00_conventions §2."
        )
    v_raw = tuple(float(x) for x in v_hat_e)
    if len(v_raw) != 3:
        raise ValueError(
            f"v_hat_e must have exactly three components; got "
            f"{len(v_raw)} from input {v_hat_e!r}"
        )
    norm_sq = v_raw[0] ** 2 + v_raw[1] ** 2 + v_raw[2] ** 2
    if abs(norm_sq - 1.0) > tol:
        raise ValueError(
            f"v_hat_e must be a unit vector (|v̂_e|² = 1); got "
            f"|v̂_e|² = {norm_sq!r} (tolerance {tol:.1e}). "
            f"See 00_conventions §2 for the v̂_e SSOT."
        )


# ──────────────────────────────────────────────────────────────────────
# Wrapper
# ──────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TiltedSpeciesBackground:
    """Tilt-projected overlay of a ``SpeciesBackground`` (FB-3.1).

    Wraps an orthogonal species-background instance ``base`` with a
    non-perturbative boost ``(β, v̂_e)`` and exposes the tilt-projected
    ``(ρ̃, p̃, v^a)`` surface consumed by the FB-3.2 hierarchy driver
    and the FB-4 Thomson Layer-B kernel.

    At ``beta == 0.0`` every method **short-circuits to the base** so
    the orthogonal path (LB-1 … FB-2) is preserved bit-for-bit. This
    is the sole non-negotiable invariant of this rotation.

    Parameters
    ----------
    base : SpeciesBackground
        Orthogonal rest-frame species background (photon / neutrino /
        baryon / CDM / Λ). Only the public ``rho_rest`` / ``p_rest``
        surface is consumed; no private attribute is touched, so any
        future ``SpeciesBackground`` subclass (e.g. massive-ν post-FB)
        is supported without modification.
    beta : float, default ``0.0``
        Boost velocity magnitude between the species rest-frame and
        the Bianchi ``n^a`` frame, ``|v| = β``. Must satisfy
        ``0.0 ≤ β < 1.0``; ``β ≥ 1`` raises ``ValueError``. The β=0
        default preserves the orthogonal path.
    v_hat_e : tuple of three floats, default ``V_HAT_E_DEFAULT``
        Spatial unit vector in the ``n^a``-frame tetrad basis that
        defines the boost direction. Must satisfy ``|v̂_e|² = 1``
        within ``V_HAT_NORM_TOL``. The default ``(1, 0, 0)`` matches
        ``BianchiCosmology.v_hat_e`` (FB-0.2) and
        ``00_conventions §2`` (FB02-F1 cross-reference).

    Raises
    ------
    ValueError
        If ``beta`` is negative, ``beta ≥ 1`` (superluminal), the
        ``v_hat_e`` tuple is not length-3, or ``|v̂_e|² ≠ 1`` beyond
        the tolerance. All guards are raised eagerly in
        ``__post_init__`` — there is no silent renormalisation.

    Notes
    -----
    Bit-identity on the β=0 path is enforced by explicit
    short-circuit (``if self.beta == 0.0: return ...``). This avoids
    floating-point cancellation in the algebraic form
    ``γ²(ρ+p) − p`` which would otherwise perturb the LB-1 byte
    anchor on the last bit.

    The β > 0 methods evaluate the King-Ellis 1973 §3 /
    Ellis-Maartens-MacCallum §5.4 equations exactly (no small-β
    linearisation anywhere).

    References
    ----------
    - King & Ellis 1973, *CMP* 31, 209 §3.
    - EMM 2012 §5.4 eqs (5.12)-(5.14).
    - lowell §7 tilt SSOT.
    - ``00_conventions §2``.
    """

    base: SpeciesBackground
    beta: float = 0.0
    v_hat_e: Tuple[float, float, float] = V_HAT_E_DEFAULT

    def __post_init__(self) -> None:
        # FB-3.5 — route validation through the shared admissibility
        # gate so the guard set is single-sourced. Error messages are
        # identical to the FB-3.1 in-place guards (byte regression on
        # the test_T09..T12 match patterns); the only structural change
        # is that the gate function can now be re-used by FB-8 /
        # FB-11 consumers without copy-paste.
        assert_tilt_admissible(self.beta, self.v_hat_e, tol=V_HAT_NORM_TOL)
        # Normalise stored values to float / tuple-of-float so downstream
        # dataclass-frozen access sees canonical types.
        object.__setattr__(self, "beta", float(self.beta))
        object.__setattr__(
            self, "v_hat_e", tuple(float(x) for x in self.v_hat_e),
        )

    # ─────────────────────────────────────────────────────────────
    # Kinematic scalars
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def from_rapidity(
        cls,
        base: SpeciesBackground,
        rapidity: float,
        v_hat_e: Tuple[float, float, float] = V_HAT_E_DEFAULT,
    ) -> "TiltedSpeciesBackground":
        """Construct from rapidity (FB-3.5 reparametrisation surface).

        Parent-plan D4 = (a) pins rapidity as the decision-level SSOT
        for tilt parameters. Callers that already have the rapidity
        (``FB-8 ObserverBoost``, ``FB-11 priors``, ``TiltedVisibility``)
        should use this factory rather than composing
        ``tanh(rapidity)`` in their own code — that keeps the
        velocity ↔ rapidity conversion single-sourced via
        :func:`rapidity_to_velocity`.
        """
        beta = rapidity_to_velocity(float(rapidity))
        return cls(base=base, beta=beta, v_hat_e=v_hat_e)

    @property
    def rapidity(self) -> float:
        """Boost rapidity ``η = atanh(β)``.

        Returns exactly ``0.0`` at ``β = 0`` (no ``atanh`` round-off).
        Delegates to :func:`velocity_to_rapidity` so the conversion
        formula is single-sourced.
        """
        return velocity_to_rapidity(self.beta)

    @property
    def gamma(self) -> float:
        """Lorentz factor ``γ = (1 − β²)^{−1/2}``.

        At ``β = 0`` returns exactly ``1.0`` (no ``√1`` round-off).
        """
        if self.beta == 0.0:
            return 1.0
        return 1.0 / np.sqrt(1.0 - self.beta * self.beta)

    @property
    def gamma_sq(self) -> float:
        """``γ² = 1 / (1 − β²)``.

        At ``β = 0`` returns exactly ``1.0``. Used by ``rho_tilde`` /
        ``p_tilde`` so the divisor is never noisy.
        """
        if self.beta == 0.0:
            return 1.0
        return 1.0 / (1.0 - self.beta * self.beta)

    @property
    def v_magnitude(self) -> float:
        """Tilt-velocity magnitude ``|v| = β`` (velocity convention)."""
        return self.beta

    # ─────────────────────────────────────────────────────────────
    # Tilt-projected thermodynamics (EMM 2012 §5.4)
    # ─────────────────────────────────────────────────────────────

    def rho_tilde(self, eta: _Number) -> _Number:
        """``n^a``-frame energy density ``ρ̃ = γ² (ρ + p) − p``.

        Ellis-Maartens-MacCallum 2012 §5.4 eq (5.12). At ``β = 0``
        short-circuits to ``base.rho_rest(eta)`` to preserve
        bit-identity with the orthogonal path.
        """
        if self.beta == 0.0:
            return self.base.rho_rest(eta)
        rho = np.asarray(self.base.rho_rest(eta), dtype=np.float64)
        p = np.asarray(self.base.p_rest(eta), dtype=np.float64)
        return self.gamma_sq * (rho + p) - p

    def p_tilde(self, eta: _Number) -> _Number:
        """``n^a``-frame isotropic pressure
        ``p̃ = p + (1/3) γ² (ρ + p) β²``.

        Ellis-Maartens-MacCallum 2012 §5.4 eq (5.13). At ``β = 0``
        short-circuits to ``base.p_rest(eta)``. This is not the full
        anisotropic ``π̃_ab`` — the trace-free part is deferred to
        FB-3.2 consumers that need it.
        """
        if self.beta == 0.0:
            return self.base.p_rest(eta)
        rho = np.asarray(self.base.rho_rest(eta), dtype=np.float64)
        p = np.asarray(self.base.p_rest(eta), dtype=np.float64)
        return p + (1.0 / 3.0) * self.gamma_sq * (rho + p) * self.beta * self.beta

    def v_vector(self, eta: _Number) -> np.ndarray:
        """Tilt 3-velocity ``v^a(η) = β v̂_e`` broadcast over ``eta``.

        For scalar ``eta`` returns shape ``(3,)``; for length-``N``
        array returns shape ``(N, 3)``. At ``β = 0`` returns a
        zero-valued array of the appropriate shape (bit-identical to
        ``zeros(3)`` / ``zeros((N, 3))``) — ``v̂_e`` is discarded on
        the orthogonal path so callers need not worry about its value.

        Reference: King & Ellis 1973 §2 (tilted 3-velocity).
        """
        arr_eta, scalar = _as_1d(eta)
        if self.beta == 0.0:
            out = np.zeros((arr_eta.size, 3), dtype=np.float64)
        else:
            v_spatial = self.beta * np.asarray(self.v_hat_e, dtype=np.float64)
            out = np.broadcast_to(
                v_spatial[np.newaxis, :], (arr_eta.size, 3),
            ).copy()
        if scalar:
            return out[0]
        return out
