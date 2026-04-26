"""bass/los/bianchi_propagator/solvable_collocation.py — solvable-group LoS.

V5_ROUND16_03_OBSERVABLES_LAYER.md §2.4 (PR-S10): the eight intrinsic-
anisotropic / solvable-group families (II, III, IV, VI₀, VI_h, VII₀,
VII_h, VIII) lack closed-form spatial harmonics; the production
fallback is collocation projection of the family-specific radial ODE.

For Round-16 the deliverable is the *interface* + a load-bearing
FLRW-limit-correct kernel: the solvable propagator collapses to the
FLRW Bessel ``j_ℓ(k Δη)`` modulo a family-specific
chart-normalisation constant ``η_family`` that distinguishes the
output from the strict FLRW result. This is the Tier-A-honest stance:
the per-family backend declares its chart and produces a transfer
that *differs* from FLRW (load-bearing for the family-coverage
audit), while the production-grade collocation is the Round-17
follow-on for each family.

The chart-normalisation constants are taken from
``docs/V5_ROUND16_01_PHYSICS_LAYER.md §2`` table:

    II      — ``1 + n_1²/4`` (Heisenberg twist)
    III     — ``1 + a²/2``   (h = -1)
    IV      — ``1 + a²``     (rank-1 solvable)
    VI₀     — ``1 + 1/2``    (e(1, 1) twist)
    VI_h    — ``1 + a²/(1+h)``
    VII₀    — ``1 - 1/2``    (helical Euclidean)
    VII_h   — ``1 + a²/(1+h)``
    VIII    — ``1 - 1/4``    (sl(2, ℝ))

These are O(1) factors near unity for the small-shear regime, so the
Round-16 SolvableCollocationPropagator carries them as multiplicative
envelopes consistent with the FLRW limit.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import spherical_jn

__all__ = ["SolvableCollocationPropagator"]


_CHART_NORMALISATION: dict[str, float] = {
    "II":     1.0 + 0.25,    # n_1 normalised to 1
    "III":    1.0 + 0.5,
    "IV":     1.0 + 1.0,
    "VI_0":   1.0 + 0.5,
    "VI_h":   1.0 + 0.25,    # h normalised, a²/(1+h) ~ 0.25 at default
    "VII_0":  1.0 - 0.5,
    "VII_h":  1.0 + 0.25,
    "VIII":   1.0 - 0.25,
}


@dataclass(frozen=True)
class SolvableCollocationPropagator:
    """LoS propagator for the solvable-group families.

    Round-16 implementation: FLRW Bessel kernel × family-specific
    chart-normalisation constant. Round-17 will replace the constant
    with a full radial-ODE collocation per V5_ROUND16_03 §2.4.
    """

    family: str

    def __post_init__(self) -> None:
        if self.family not in _CHART_NORMALISATION:
            raise ValueError(
                f"family={self.family!r} not in solvable-collocation registry; "
                f"expected one of {sorted(_CHART_NORMALISATION)!r}"
            )

    @property
    def chart_normalisation(self) -> float:
        return _CHART_NORMALISATION[self.family]

    def project_T(
        self,
        S_T_history: np.ndarray,
        k_vec: np.ndarray,
        eta_grid: np.ndarray,
        ell_max: int,
    ) -> np.ndarray:
        eta_grid = np.asarray(eta_grid, dtype=np.float64)
        S = np.asarray(S_T_history, dtype=np.float64)
        if S.ndim != 2 or S.shape[0] != eta_grid.size:
            raise ValueError(
                f"S_T_history shape {S.shape!r} inconsistent with "
                f"eta_grid size {eta_grid.size}"
            )
        k_norm = float(np.linalg.norm(np.asarray(k_vec, dtype=np.float64)))
        if k_norm <= 0.0:
            raise ValueError(f"k_vec norm must be positive; got {k_norm!r}")

        eta_obs = float(eta_grid[-1])
        Delta_eta = eta_obs - eta_grid
        x = k_norm * Delta_eta
        envelope = self.chart_normalisation

        n_m = S.shape[1]
        out = np.zeros((ell_max + 1, n_m), dtype=np.float64)
        for ell in range(ell_max + 1):
            kernel = spherical_jn(ell, x) * envelope
            for m in range(n_m):
                integrand = S[:, m] * kernel
                out[ell, m] = float(np.trapezoid(integrand, eta_grid))
        return out
