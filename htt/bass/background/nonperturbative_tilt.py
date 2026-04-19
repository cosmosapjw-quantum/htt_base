"""bass/background/nonperturbative_tilt.py — King-Ellis exact tilt RHS.

Migrated from legacy/bass/bass/background/rhs.py (v8.3.0).

Complements ``bass.background.einstein_bianchi`` (conformal-time 10-type
shear solver) by providing the **non-perturbative tilt evolution** that
bass_py's fiducial integrator does not model.  bass_py's einstein_bianchi
carries β as a *static* parameter; this module evolves β(N) via the
exact King-Ellis 1973 formula

    dβ/dN = −(1 − 3 c_s²) · sinh(β) · cosh(β),

and reports the exact tilt energy density

    Ω_tilt = (1 + w) · Ω · sinh² β = [(4/3) Ω_r + Ω_m] · sinh² β.

Together with the tilt-shear coupling source

    (dΣ²/dN)_tilt = [(4/3)² Ω_r + Ω_m] · sinh²β · Σ²,

this closes the reduced-family Bianchi background at arbitrarily large
tilt rapidity — no β² truncation anywhere.

When to use which integrator
----------------------------
- ``bass.background.einstein_bianchi``
    Dispatches over all 10 Bianchi types.  Tracks (a, Σ_+, Σ_-) in
    conformal time with Wainwright-Ellis spatial-curvature sources.
    β held fixed.  Use when the question is **shear dynamics across
    Bianchi types** and β ≲ 0.1 (where static-β is adequate).

- ``nonperturbative_tilt.rhs_bianchi`` (this file)
    Six-variable e-fold ODE y = [Ω_r, Ω_m, Σ², W², β, Ω_k] for the
    reduced tilted families {FLRW_tilt, BI_tilt, BV_tilt, BVII₀_tilt,
    BVIIh_tilt} plus their orthogonal counterparts.  Non-perturbative
    in β.  Use when the tilt rapidity is O(0.1) or larger, or when the
    tilt-shear feedback matters.

External-code policy
--------------------
All the evolution coefficients live in Python below.  Nothing here
calls out to CAMB / CLASS / AniCLASS; the module is a self-contained
truth engine for the reduced-family nonlinear tilt sector.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from bass.background.hooks import HookState

__all__ = [
    'omega_tilt_exact',
    'omega_tilt_exact_vec',
    'rhs_bianchi',
    'rhs_for_family',
    'SUPPORTED_FAMILIES',
    'VORTICITY_FAMILIES',
]


# Families recognised by ``rhs_bianchi``. String labels must include
# 'tilt' to activate tilt-evolution + tilt-shear coupling; else the RHS
# treats the family as orthogonal (β, tilt terms = 0).
SUPPORTED_FAMILIES = frozenset({
    'FLRW_orth', 'FLRW_tilt',
    'BI_orth', 'BI_tilt',
    'BV_orth', 'BV_tilt',
    'BVII0_orth', 'BVII0_tilt',
    'BVIIh_orth', 'BVIIh_tilt',
})

#: Families whose geometry sources a non-zero vorticity W² evolution
#: (otherwise W² ≡ 0 by symmetry).
VORTICITY_FAMILIES = frozenset({
    'BVII0_orth', 'BVII0_tilt', 'BV_tilt', 'BVIIh_tilt',
})

#: Families whose background curvature Ω_k is evolved.
CURVATURE_FAMILIES = frozenset({'BV_orth', 'BV_tilt'})


# ════════════════════════════════════════════════════════════════════
# Exact Ω_tilt
# ════════════════════════════════════════════════════════════════════

def omega_tilt_exact(
    Omega_r: float,
    Omega_m: float,
    beta: float,
    w_eff: float = None,  # type: ignore[assignment]
) -> float:
    """Exact tilt energy density Ω_tilt = (1 + w) · Ω · sinh² β.

    For a radiation-matter mix with per-species w = 1/3, 0:

        (1 + w) · Ω  = (4/3) · Ω_r + Ω_m,

    valid everywhere in the z → ∞ to z = 0 window. The β² linearisation
    misses
      (i) sinh² β vs β² — matters for |β| > 0.1,
      (ii) the Ω_m contribution — dominant after matter-radiation
           equality.

    Parameters
    ----------
    Omega_r, Omega_m : float
        Radiation and matter density parameters.
    beta : float
        Tilt rapidity.
    w_eff : float, optional
        Unused; kept for call-site parity with legacy.

    Returns
    -------
    float
        Ω_tilt ≥ 0.
    """
    if abs(beta) < 1.0e-15:
        return 0.0
    one_plus_w_Omega = (4.0 / 3.0) * Omega_r + Omega_m
    return float(one_plus_w_Omega * np.sinh(beta) ** 2)


def omega_tilt_exact_vec(
    Omega_r: np.ndarray,
    Omega_m: np.ndarray,
    beta: np.ndarray,
) -> np.ndarray:
    """Vectorised ``omega_tilt_exact`` along matching arrays."""
    one_plus_w_Omega = (4.0 / 3.0) * np.asarray(Omega_r) + np.asarray(Omega_m)
    return one_plus_w_Omega * np.sinh(np.asarray(beta)) ** 2


# ════════════════════════════════════════════════════════════════════
# RHS: six-variable e-fold Bianchi background
# ════════════════════════════════════════════════════════════════════

def rhs_bianchi(
    N: float,
    y: np.ndarray,
    family: str,
    hooks: HookState = HookState(),
) -> np.ndarray:
    """dy/dN for y = [Ω_r, Ω_m, Σ², W², β, Ω_k] (NON-PERTURBATIVE).

    Friedmann constraint is enforced implicitly via Ω_Λ:

        Ω_Λ = max(1 − Ω_r − Ω_m − Σ² + W² − Ω_k, 0),

    i.e. the four-variable anisotropic part is evolved independently
    and Ω_Λ absorbs the residual.  Ω_r, Ω_m are *geometry-frame* densities
    that already include the tilt boost; adding Ω_tilt here would
    double-count (Ω_tilt enters only the defect identity, via
    ``omega_tilt_exact``).

    Raychaudhuri deceleration parameter:

        q = (1/2)(1 + 3 w_eff)(Ω_r + Ω_m) − Ω_Λ + 2 Σ² − 2 W²

    Density evolution (adiabatic):

        dΩ_r/dN = −Ω_r · (2 − 2 q)   (w_r = 1/3)
        dΩ_m/dN = −Ω_m · (1 − 2 q)   (w_m = 0)

    Shear evolution:

        dΣ²/dN = −2 (2 − q) Σ²  +  (tilt-shear coupling)

    where the tilt-shear coupling is

        (dΣ²/dN)_tilt = [(4/3)² Ω_r + Ω_m] · sinh² β · Σ²

    (tilted perfect-fluid anisotropic stress at leading Σ² order).

    Vorticity evolution (active only for families in ``VORTICITY_FAMILIES``):

        dW²/dN = −2 (2 − q) W²

    Tilt evolution (active only for tilted families, King-Ellis 1973):

        dβ/dN = −(1 − 3 c_s²) · sinh β · cosh β,   c_s² = w_eff

    Anisotropic curvature (active only for ``CURVATURE_FAMILIES``):

        dΩ_k/dN = −2 (1 − q) Ω_k

    Parameters
    ----------
    N : float
        e-fold time ln a.
    y : ndarray
        State vector [Ω_r, Ω_m, Σ², W², β, Ω_k].
    family : str
        Bianchi family label (must be in ``SUPPORTED_FAMILIES``).
    hooks : HookState
        Thermodynamic hooks for the current era. Currently unused by
        the reduced-family RHS but propagated for interface parity.

    Returns
    -------
    ndarray
        dy/dN with the same shape as ``y``.
    """
    Or, Om, S2, W2, beta, Ok = (float(v) for v in y)

    OL = max(1.0 - Om - Or - S2 + W2 - Ok, 0.0)
    rho_total = max(Or + Om, 1.0e-30)
    w_eff = Or / (3.0 * rho_total)
    q = 0.5 * (1.0 + 3.0 * w_eff) * rho_total - OL + 2.0 * S2 - 2.0 * W2

    dy = np.zeros(6, dtype=np.float64)
    dy[0] = -Or * (2.0 - 2.0 * q)
    dy[1] = -Om * (1.0 - 2.0 * q)

    shear_decay = -2.0 * (2.0 - q) * S2
    tilt_source = 0.0
    if 'tilt' in family and abs(beta) > 1.0e-15:
        # (1 + w_species)² · Ω per species, summed
        one_plus_w_sq_Omega = (4.0 / 3.0) ** 2 * Or + Om
        tilt_source = one_plus_w_sq_Omega * np.sinh(beta) ** 2 * S2
    dy[2] = shear_decay + tilt_source

    if family in VORTICITY_FAMILIES:
        dy[3] = -2.0 * (2.0 - q) * W2
    else:
        dy[3] = 0.0

    if 'tilt' in family:
        cs2 = w_eff  # adiabatic sound speed
        dy[4] = -(1.0 - 3.0 * cs2) * np.sinh(beta) * np.cosh(beta)
    else:
        dy[4] = 0.0

    if family in CURVATURE_FAMILIES:
        dy[5] = -2.0 * (1.0 - q) * Ok
    else:
        dy[5] = 0.0

    return dy


def rhs_for_family(
    family: str,
    hooks: HookState = HookState(),
) -> Callable[[float, np.ndarray], np.ndarray]:
    """Return a solve_ivp-ready closure ``f(N, y)`` for ``family``.

    The closure captures ``family`` and a fixed ``hooks`` snapshot; pass
    it directly to ``scipy.integrate.solve_ivp``.  For era-dependent
    hooks, build a closure that dispatches on z = exp(−N) − 1 externally.
    """
    if family not in SUPPORTED_FAMILIES:
        raise ValueError(
            f"Unsupported family {family!r}. "
            f"Expected one of {sorted(SUPPORTED_FAMILIES)}."
        )

    def f(N: float, y: np.ndarray) -> np.ndarray:
        return rhs_bianchi(N, y, family, hooks)

    return f
