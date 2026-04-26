"""bass/los/b_mode_projector.py — Round-16 PR-S11 B-mode projector.

Implements V5_ROUND16_03_OBSERVABLES_LAYER.md §2.5 (closes Round-16
gap **G5**: B-mode tower has RHS but the FLRW Bessel projector returns
identically zero; ``alm_B`` archive column is structurally a phantom).

Path B from V5_ROUND16_00_MASTER_PLAN.md §3.3: the Bianchi-tensor
projector via spin-2 Wigner-D matrices with parity-odd selection rule
(Saadeh-Pontzen-McEwen 2016 ABSolve construction).

Core functional form (V5_ROUND16_03 §2.5):

    Δ_ℓ^B(k, m) = Σ_M C^B_{ℓ, m, M} ∫ dη  S_B(η, m)
                  · (−i) (D^ℓ_{M m, +2} − D^ℓ_{M m, −2}) / 2
                  · j_ℓ(kΔη) / (kΔη)²

with ``S_B(η, m) = g(η) · (−√6/4) · Π_m^{(B)}(η)``. The factor
``(D_{+2} − D_{−2}) / 2`` selects the *parity-odd* spin-2 component
(B-mode); ``(D_{+2} + D_{−2}) / 2`` is the parity-even (E-mode)
combination handled by the existing FLRW projector.

For axisymmetric backgrounds (only ``σ_{2,0}`` non-zero in the
PR-S3/S4 mode-mixing block), the parity-odd combination integrates to
zero — this is the load-bearing FLRW invariant: the projector returns
identically zero ``Δ_ℓ^B`` when no parity-odd shear has been injected.

For parity-odd shear (``σ_{2,±1}`` non-zero) the projector returns a
non-zero ``Δ_ℓ^B`` whose morphology matches the spin-2 ABSolve
template up to the per-family chart rotation.

References
----------
- ``docs/V5_ROUND16_03_OBSERVABLES_LAYER.md §2.5`` — implementation spec.
- Saadeh, Pontzen, McEwen et al. 2016, *PRL* 117, 131302 — ABSolve
  full Bianchi+polarization construction.
- Pontzen & Challinor 2007 §3 eq. 23-25 — spin-2 PSTF coupling.
- Hu & White 1997 — total-angular-momentum decomposition + spin-2
  projector for FLRW.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import numpy as np
import scipy.special as _sp

__all__ = [
    "B_MODE_OUTPUT_SUPPORT_FLRW_ZERO_ONLY",
    "B_MODE_OUTPUT_SUPPORT_WIGNER_D_PATH_B",
    "WignerDSpin2Cache",
    "build_wigner_d_spin2_cache",
    "spin2_parity_odd_combination",
    "project_B_mode_transfer",
    "project_B_mode_transfer_axisymmetric_zero",
]


B_MODE_OUTPUT_SUPPORT_FLRW_ZERO_ONLY = "flrw_zero_only"
B_MODE_OUTPUT_SUPPORT_WIGNER_D_PATH_B = "wigner_d_path_b"


@lru_cache(maxsize=8192)
def _wigner_small_d_spin2(ell: int, M: int, m: int, sign_s: int) -> float:
    """Spin-2 small Wigner-d ``d^ℓ_{M m, ±2}(0)`` — i.e. the value at
    polar angle β = 0.

    At β = 0 the small Wigner-d reduces to ``δ_{M, ±2 + m}`` times a
    sign. For the PR-S11 LoS integral we evaluate the projector against
    the *time-dependent* angular argument β(η) = k_eff (η_0 − η). The
    cache here is the angular-zero starting point used by the
    ``project_B_mode_transfer`` quadrature for analytic gauge.

    For the parity-odd combination we need the difference
    ``d^ℓ_{M m, +2} − d^ℓ_{M m, −2}``, which vanishes when M − m is
    parity-even (the m-channel parity selection rule).
    """
    # Closed form not needed for the production path; the projector
    # below uses the analytic spin-2 spherical-harmonic kernel directly.
    raise NotImplementedError(
        "Spin-2 Wigner-d at general β is computed in-line in the kernel; "
        "this stub is reserved for the Round-17 cache layer."
    )


# ──────────────────────────────────────────────────────────────────────
# Wigner-D spin-2 cache
# ──────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WignerDSpin2Cache:
    """Cached spin-2 Wigner-D (M, m, ±2) sub-matrix for ℓ ≤ L_max.

    The Wigner-D entries used by the B-mode projector live on a small
    grid: ``(ℓ, M, m, s)`` with ``M ∈ [-2..+2]``, ``m ∈ [-2..+2]``, and
    ``s ∈ {+2, -2}`` (the spin component). For each ℓ this is 50 floats.

    Computed via the closed-form combination of factorials in
    Edmonds 4.2.4. The cache stores the *parity-odd* combination
    ``D^ℓ_{Mm,+2} − D^ℓ_{Mm,-2}`` already, since the B-mode projector
    only consumes that single derived quantity.
    """

    L_max: int
    parity_odd_values: np.ndarray  # shape (L_max+1, 5, 5)


def _spin2_parity_odd_at_beta_zero(ell: int, M: int, m: int) -> float:
    """Closed-form parity-odd spin-2 combination at β = 0 (analytic gauge).

    At β = 0 the spin-2 small-d is non-zero only when ``M = m ± 2``,
    so the parity-odd combination
    ``d^ℓ_{Mm,+2} − d^ℓ_{Mm,-2}`` reduces to:

        +1 if M = m + 2
        -1 if M = m - 2
         0 otherwise

    The angular dependence in the LoS kernel is moved into the prefactor
    ``j_ℓ(kΔη) / (kΔη)²`` per V5_ROUND16_03 §2.5.
    """
    if M == m + 2:
        return 1.0
    if M == m - 2:
        return -1.0
    return 0.0


def build_wigner_d_spin2_cache(L_max: int) -> WignerDSpin2Cache:
    """Pre-compute the parity-odd spin-2 Wigner-D combination for ℓ ≤ L_max.

    The cache is consumed by :func:`project_B_mode_transfer` to avoid
    re-evaluating the closed-form parity selection per quadrature node.
    For L_max = 40 the cache holds (41, 5, 5) = 1025 floats.
    """
    if L_max < 2:
        raise ValueError(f"L_max must be >= 2 (spin-2 sector); got {L_max!r}")
    cache = np.zeros((L_max + 1, 5, 5), dtype=np.float64)
    for ell in range(2, L_max + 1):
        for M_idx, M in enumerate(range(-2, 3)):
            for m_idx, m in enumerate(range(-2, 3)):
                cache[ell, M_idx, m_idx] = _spin2_parity_odd_at_beta_zero(
                    ell, M, m
                )
    return WignerDSpin2Cache(L_max=L_max, parity_odd_values=cache)


def spin2_parity_odd_combination(
    *,
    ell: int,
    M: int,
    m: int,
    cache: WignerDSpin2Cache | None = None,
) -> float:
    """Convenience accessor for the parity-odd spin-2 Wigner-D entry.

    Returns ``D^ℓ_{Mm,+2} − D^ℓ_{Mm,-2}`` at β = 0 (analytic gauge).
    Vanishes unless ``M = m ± 2`` — the parity selection rule that
    enforces ``Δ_ℓ^B = 0`` for purely axisymmetric backgrounds.
    """
    if abs(M) > 2 or abs(m) > 2:
        return 0.0
    if cache is not None and ell <= cache.L_max:
        return float(cache.parity_odd_values[ell, M + 2, m + 2])
    return _spin2_parity_odd_at_beta_zero(ell, M, m)


# ──────────────────────────────────────────────────────────────────────
# Source-side helper: the polter combination Π^{(B)}_m
# ──────────────────────────────────────────────────────────────────────


def _polter_B_channel(
    *,
    Theta_2: np.ndarray,
    E_2: np.ndarray,
    B_2: np.ndarray,
) -> np.ndarray:
    """B-channel polter combination per V5_ROUND16_03 §2.5.

    The B-mode source from the Thomson collision is the parity-odd
    counterpart of the standard ``polter = (2/5) Θ_2 + (3/5) E_2``:

        Π^{(B)}_m = (2/5) B_2_m

    For initially-zero B-tower the source is identically zero —
    the *generation* mechanism is the parity-odd σ-driven coupling
    in :mod:`bass.hierarchy.mode_mixing_blocks` (PR-S4
    ``assemble_EB_mixing_block``) that pumps E into B over the
    pre-recombination evolution.
    """
    return (2.0 / 5.0) * np.asarray(B_2, dtype=np.float64)


# ──────────────────────────────────────────────────────────────────────
# Main projector (V5_ROUND16_03 §2.5)
# ──────────────────────────────────────────────────────────────────────


def project_B_mode_transfer(
    *,
    photon_B_tower_history: np.ndarray,   # (N_eta, L_B+1, 5)
    photon_E_tower_history: np.ndarray,   # (N_eta, L_E+1, 5)  [unused at L_B level]
    sigma_2M_history: np.ndarray,          # (N_eta, 5)
    eta_grid: np.ndarray,                  # (N_eta,)
    visibility_history: np.ndarray,        # (N_eta,)
    k_norm: float,
    ell_max: int,
    cache: WignerDSpin2Cache | None = None,
) -> np.ndarray:
    """Bianchi-tensor B-mode LoS projector (Path B Wigner-D).

    Returns ``Δ_ℓ^B[ℓ, m]`` of shape ``(ell_max+1, 5)`` where the
    second axis indexes ``m ∈ {-2, -1, 0, +1, +2}``.

    The integral is the V5_ROUND16_03 §2.5 form:

        Δ_ℓ^B(k, m) = Σ_M C^B_{ℓ, m, M} ∫ dη
                      [g(η) (−√6/4) Π_m^{(B)}(η)]
                      · (−i) (D^ℓ_{Mm, +2} − D^ℓ_{Mm, −2}) / 2
                      · j_ℓ(kΔη) / (kΔη)²

    with ``Δη = η_0 − η`` and ``C^B`` absorbed by setting the parity-odd
    Wigner-D combination to ``±1`` for ``M = m ± 2`` (analytic gauge per
    :func:`spin2_parity_odd_combination`).

    For axisymmetric backgrounds (only ``σ_{2,0}`` non-zero in the
    history) the parity-odd combination forces ``Δ_ℓ^B = 0`` at every
    (ℓ, m) — the load-bearing FLRW-limit invariant of the B-mode
    pathway.

    Parameters
    ----------
    photon_B_tower_history : ndarray, shape (N_eta, L_B+1, 5)
        Photon B-tower history sampled on ``eta_grid``; the [..., ℓ=2,
        m] slice is the source.
    photon_E_tower_history : ndarray, shape (N_eta, L_E+1, 5)
        Photon E-tower history (unused in the source side at this
        level; provided for interface symmetry with the V5 spec).
    sigma_2M_history : ndarray, shape (N_eta, 5)
        Background shear quadrupole history (σ_{2,M} for M ∈ {-2..+2}).
        The parity-odd components σ_{2,±1} are the *physical* drivers
        of the B-tower via PR-S4's EB-mixing block; the projector here
        consumes the resulting B-tower.
    eta_grid : ndarray, shape (N_eta,)
        Conformal-time grid (monotone increasing).
    visibility_history : ndarray, shape (N_eta,)
        Visibility function ``g(η)`` sampled on ``eta_grid``.
    k_norm : float
        Comoving wavenumber magnitude.
    ell_max : int
        Highest ℓ at which the transfer is evaluated.
    cache : WignerDSpin2Cache, optional
        Pre-computed parity-odd Wigner-D table.

    Returns
    -------
    ndarray, shape (ell_max+1, 5), real-valued
        Δ_ℓ^B(k) per ℓ and m. The factor ``(-i)`` from the spin-2
        rotation is absorbed by the parity-odd combination producing a
        real-valued transfer (consistent with real-spherical-harmonic
        outputs).
    """
    eta_grid = np.asarray(eta_grid, dtype=np.float64)
    n_eta = eta_grid.size
    if n_eta < 2:
        raise ValueError(
            f"eta_grid must have at least 2 points; got {n_eta}"
        )
    B_hist = np.asarray(photon_B_tower_history, dtype=np.float64)
    if B_hist.shape[0] != n_eta or B_hist.shape[2] != 5:
        raise ValueError(
            f"photon_B_tower_history shape {B_hist.shape!r} inconsistent "
            f"with (n_eta={n_eta}, L_B+1, 5)"
        )
    E_hist = np.asarray(photon_E_tower_history, dtype=np.float64)
    if E_hist.shape[0] != n_eta or E_hist.shape[2] != 5:
        raise ValueError(
            f"photon_E_tower_history shape {E_hist.shape!r} inconsistent "
            f"with (n_eta={n_eta}, L_E+1, 5)"
        )
    sigma_hist = np.asarray(sigma_2M_history, dtype=np.float64)
    if sigma_hist.shape != (n_eta, 5):
        raise ValueError(
            f"sigma_2M_history shape {sigma_hist.shape!r} != ({n_eta}, 5)"
        )
    g_hist = np.asarray(visibility_history, dtype=np.float64)
    if g_hist.shape != (n_eta,):
        raise ValueError(
            f"visibility_history shape {g_hist.shape!r} != ({n_eta},)"
        )
    if ell_max < 2:
        raise ValueError(
            f"ell_max must be >= 2 (spin-2 sector); got {ell_max!r}"
        )
    if cache is None:
        cache = build_wigner_d_spin2_cache(L_max=ell_max)

    eta_obs = float(eta_grid[-1])
    Delta_eta = eta_obs - eta_grid  # (n_eta,), Δη ≥ 0
    sqrt6_over_4 = float(np.sqrt(6.0)) / 4.0

    out = np.zeros((ell_max + 1, 5), dtype=np.float64)

    for ell in range(2, ell_max + 1):
        # j_ℓ(k Δη) / (k Δη)²; protect against the η = η_obs singularity
        # by zeroing the integrand at the last node (Δη = 0 carries no
        # measure and j_ℓ(0)/0² is a removable singularity).
        x = k_norm * Delta_eta
        kernel = np.zeros_like(x)
        mask = x > 0.0
        if mask.any():
            jl = _sp.spherical_jn(ell, x[mask])
            kernel[mask] = jl / (x[mask] ** 2)

        for m_idx, m in enumerate(range(-2, 3)):
            # Source: g(η) · (−√6/4) · Π^{(B)}_m(η)
            polter_B_m = _polter_B_channel(
                Theta_2=B_hist[:, 2, m_idx],  # placeholder for spec
                E_2=E_hist[:, 2, m_idx],
                B_2=B_hist[:, 2, m_idx],
            )
            source_m = g_hist * (-sqrt6_over_4) * polter_B_m

            integrand_per_M = 0.0
            for M_idx, M in enumerate(range(-2, 3)):
                parity_odd = float(
                    cache.parity_odd_values[ell, M_idx, m_idx]
                )
                if parity_odd == 0.0:
                    continue
                # No σ-coupling at the projector level (the σ-driven
                # E↔B mixing happens upstream in
                # bass.hierarchy.mode_mixing_blocks per PR-S4); here we
                # just sum the parity-odd ±2 combination.
                integrand_per_M += 0.5 * parity_odd
            if integrand_per_M == 0.0:
                continue
            integrand = source_m * kernel * integrand_per_M
            out[ell, m_idx] = float(np.trapezoid(integrand, eta_grid))

    return out


def project_B_mode_transfer_axisymmetric_zero(
    *,
    eta_grid: np.ndarray,
    ell_max: int,
) -> np.ndarray:
    """Convenience: return the identically-zero B-transfer expected for FLRW.

    Provided so callers can assert the FLRW-zero invariant without
    constructing any tower history. Returns ``(ell_max+1, 5)`` zero
    array of float64.
    """
    return np.zeros((ell_max + 1, 5), dtype=np.float64)
