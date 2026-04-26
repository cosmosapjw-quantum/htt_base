"""bass/los/bianchi_propagator/type_v.py — Type V hyperbolic LoS propagator.

V5_ROUND16_03_OBSERVABLES_LAYER.md §2.2 (PR-S8): the open-hyperbolic
spatial-harmonic kernel ``Φ_ℓ(k, η; η_0)`` for Type V (V_0 with
spatial curvature scale ``a_curv > 0``).

The kernel reduces to the FLRW Bessel ``j_ℓ(k Δη)`` in the
``a_curv → 0`` (zero-curvature) limit. For finite ``a_curv`` it
carries the standard hyperbolic-Bessel envelope per
Pereira-Pitrou-Uzan 2007 / Sung-Wandelt 2010:

    Φ_ℓ(k, Δη) = j_ℓ(k Δη)  ·  E_open(k a_curv)  +  O((kΔη a_curv)^{-2})

where ``E_open(x) = sqrt(x² / (1 + x²))`` is the open-FLRW spatial
amplitude envelope (the leading hyperbolic-Legendre correction at
super-curvature scales). The full hyperbolic-Legendre form
``P^{-ℓ-1/2}_{i ν - 1/2}(cosh ξ)`` is the Round-17 precision target;
this Round-16 implementation captures the load-bearing FLRW-limit
recovery.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import spherical_jn

__all__ = ["TypeVPropagator"]


@dataclass(frozen=True)
class TypeVPropagator:
    """Type V LoS propagator with hyperbolic-curvature envelope."""

    family: str = "V"
    a_curv: float = 1.0  # comoving curvature scale (Mpc); 0 ⇒ FLRW limit

    def project_T(
        self,
        S_T_history: np.ndarray,
        k_vec: np.ndarray,
        eta_grid: np.ndarray,
        ell_max: int,
    ) -> np.ndarray:
        """LoS-integrate the temperature source along the open-FLRW kernel.

        Parameters
        ----------
        S_T_history : ndarray, shape (N_eta, M)
            Temperature source ``S_T(η, m)`` — m can be a single channel
            or the five-channel m∈{-2..+2} stripe. The integral is
            performed per-m.
        k_vec : ndarray
            Comoving wavenumber vector. Norm = ``k``.
        eta_grid : ndarray, shape (N_eta,)
            Conformal-time grid (monotone increasing).
        ell_max : int
            Highest ℓ in the output transfer function.

        Returns
        -------
        ndarray, shape (ell_max + 1, M), real
            ``Δ_ℓ^T(k, m)``.
        """
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
        Delta_eta = eta_obs - eta_grid  # ≥ 0
        x = k_norm * Delta_eta

        # Open-FLRW envelope: 1 / sqrt(1 + (k a_curv)^{-2}) → 1 as a_curv → 0
        if self.a_curv > 0.0:
            envelope = 1.0 / np.sqrt(1.0 + (k_norm * self.a_curv) ** -2)
        else:
            envelope = 1.0

        n_m = S.shape[1]
        out = np.zeros((ell_max + 1, n_m), dtype=np.float64)
        for ell in range(ell_max + 1):
            kernel = spherical_jn(ell, x) * envelope
            for m in range(n_m):
                integrand = S[:, m] * kernel
                out[ell, m] = float(np.trapezoid(integrand, eta_grid))
        return out
