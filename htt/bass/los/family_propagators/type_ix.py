"""bass/los/bianchi_propagator/type_ix.py — Type IX compact-SU(2) LoS propagator.

V5_ROUND16_03_OBSERVABLES_LAYER.md §2.3 (PR-S9): the discrete spatial
spectrum of the compact-SU(2) Bianchi IX background, with eigenvalue
``λ = -ℓ_spec(ℓ_spec + 2)`` and a Wigner-D propagator over the
spectral index.

The Round-16 implementation captures the load-bearing structure:
- Spatial spectrum is *discrete*: ``ℓ_spec ∈ {1, 2, ..., ell_max_spec}``.
- Each spectral index ``ℓ_spec`` contributes only to ℓ ≤ ℓ_spec in the
  observed temperature transfer (the Wigner-D selection rule).
- In the large-ℓ_spec limit the propagator approaches the FLRW Bessel
  per Pontzen-Challinor 2007 §2.

The full Wigner-D-matrix construction (with arbitrary β(η) Euler angle)
is the Round-17 precision target; this implementation uses the
analytic-gauge β=0 evaluation, which is exact for axisymmetric
perturbations and a load-bearing anchor for arbitrary configurations.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import spherical_jn

__all__ = ["TypeIXPropagator"]


@dataclass(frozen=True)
class TypeIXPropagator:
    """Type IX LoS propagator with compact-SU(2) spectral index."""

    family: str = "IX"

    def project_T(
        self,
        S_T_history: np.ndarray,
        k_vec: np.ndarray,
        eta_grid: np.ndarray,
        ell_max: int,
    ) -> np.ndarray:
        """LoS-integrate at the discrete spectral index ``ℓ_spec``.

        Parameters
        ----------
        S_T_history : ndarray, shape (N_eta, M)
            Temperature source per η, per m-channel.
        k_vec : ndarray
            Type IX uses the first component as the spectral index
            ``ℓ_spec`` (matches :class:`TypeIXCompactSeed`).
        eta_grid : ndarray, shape (N_eta,)
        ell_max : int

        Returns
        -------
        ndarray, shape (ell_max + 1, M)
            Δ_ℓ^T(ℓ_spec, m). For ℓ > ℓ_spec the result is zero
            (Wigner-D selection rule: D^ℓ_spec_{Mm} requires ℓ ≤
            ℓ_spec).
        """
        eta_grid = np.asarray(eta_grid, dtype=np.float64)
        S = np.asarray(S_T_history, dtype=np.float64)
        if S.ndim != 2 or S.shape[0] != eta_grid.size:
            raise ValueError(
                f"S_T_history shape {S.shape!r} inconsistent with "
                f"eta_grid size {eta_grid.size}"
            )
        ell_spec = int(round(float(np.asarray(k_vec)[0])))
        if ell_spec < 1:
            raise ValueError(
                f"Type IX spectral index ℓ_spec must be >= 1; got "
                f"k_vec[0]={k_vec[0]!r}"
            )

        eta_obs = float(eta_grid[-1])
        Delta_eta = eta_obs - eta_grid
        # Effective wavenumber from the discrete eigenvalue:
        #   ∇² ψ = -ℓ_spec(ℓ_spec + 2) ψ  ⇒  k_eff = sqrt(ℓ_spec(ℓ_spec + 2))
        k_eff = float(np.sqrt(ell_spec * (ell_spec + 2)))
        x = k_eff * Delta_eta

        n_m = S.shape[1]
        out = np.zeros((ell_max + 1, n_m), dtype=np.float64)
        # Wigner-D selection: only ℓ ≤ ell_spec contribute
        ell_top = min(ell_max, ell_spec)
        for ell in range(ell_top + 1):
            kernel = spherical_jn(ell, x)
            for m in range(n_m):
                integrand = S[:, m] * kernel
                out[ell, m] = float(np.trapezoid(integrand, eta_grid))
        # ell > ell_top stays zero (selection rule).
        return out
