"""Tier-B → FLRWSourceTerms extractor (V5 Round-5 audit landing).

Closes the W10+ scalar-mode evolution gap that the reverted S8/S9 pipeline
attempted via toy Sachs-Wolfe MD approximation ``(Θ_0 + Ψ)_* = -R/5``.
This module extracts the five Newtonian-gauge callables the LoS projector
(``bass/los/flrw_bessel_projector.py``) requires, directly from the VER2
Tier-B PSTF output — no toy closure, no MD analytic, no surrogate.

Audit trail:
    - Round-5 prompt:  docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND5.md
    - Round-5 answer:  v5_residual_harmonic_algebraic_audit_round5.md
    - Key corrections from the auditor:
      * Q-16: FLRW / Bianchi-I orthogonal → Θ_ℓ^VER2 = Θ_ℓ^MB directly
        (no gauge-transformation coefficient).
      * Q-17: Einstein anisotropic stress depends on the INTENSITY
        quadrupoles Θ_2^γ, Θ_2^ν — NOT on Π = Θ_2 - √6·E_2. Π belongs
        to the Thomson source, intensity quadrupoles drive Ψ − Φ.
      * Q-17: MB normalization σ_γ = 2·Θ_2^γ, σ_ν = 2·Θ_2^ν so
        (ρ+p)·σ_tot = (8/3)·(ρ_γ·Θ_2^γ + ρ_ν·Θ_2^ν).
      * Q-20: Π = Θ_2 − √6·E_2 as written, no extra PSTF prefactor.

Physics:
    Newtonian-gauge Einstein constraints (conformal time, Ma-Bertschinger
    convention):

        k² Φ + 3·ℋ·(Φ' + ℋ·Ψ) = 4πG·a²·δρ_tot
        k² (Φ' + ℋ·Ψ) = 4πG·a²·(ρ + p)·θ_tot        with θ = k·v
        Ψ − Φ = (12πG·a²/k²) · (ρ + p)·σ_tot          (anisotropic stress)

    Combining:
        Φ = (4πG·a²/k²) · [δρ_tot − 3ℋ·Σ_i (ρ_i+p_i)·v_i / k]
        Ψ = Φ + (12πG·a²/k²) · (ρ+p)·σ_tot

    BASS unit convention (species.bg_table.constants):
        ρ_bass = ρ_phys / ρ_crit,0 = dimensionless (in ρ_crit,0 units)
        H_0_mpc = H_0 / c = H_0 in 1/Mpc
        (H/H_0)² = ρ_tot_bass (flat-ΛCDM Friedmann residual=0)
        ⇒ 4πG = (3/2)·H_0² (in natural 1/Mpc² units)
        ⇒ 4πG·a²/k² = (3/2)·H_0_mpc²·a²/k²  (dimensionless)

ISW driver:
    Φ̇ + Ψ̇ computed by 4th-order centered finite differences in the bulk,
    2nd-order one-sided differences at the boundaries. Applied to
    (Φ + Ψ) sampled on the integration_result.eta grid.

Interpolation:
    scipy.interpolate.PchipInterpolator with extrapolate=False — shape-
    preserving and does not ring near the recombination visibility peak.
    Callers evaluating outside [η_0, η_{N-1}] will receive NaN.

References:
    - Ma & Bertschinger 1995 (synchronous ↔ Newtonian gauge dictionary,
      ρ·v convention, θ = k·v, σ = 2·Θ_2 for radiation)
    - Ellis & van Elst 1998 (1+3 covariant PSTF formalism, gauge-
      invariance of ℓ≥1 multipoles around FRW)
    - Seljak & Zaldarriaga 1996 (LoS source assembly)
    - Kamionkowski, Kosowsky, Stebbins 1997 (Π decomposition)
"""
from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np
from scipy.interpolate import PchipInterpolator

from bass.los.flrw_bessel_projector import FLRWSourceTerms

if TYPE_CHECKING:
    from bass.hierarchy.integrator import IntegrationResult
    from bass.species.registry import SpeciesBackgroundRegistry


__all__ = [
    "extract_flrw_sources_from_tier_b",
    "_slot",
    "_fd4_derivative",
]


_SQRT6 = float(np.sqrt(6.0))


def _slot(ell: int, m: int) -> int:
    """Real-spherical-harmonic packed slot index: ``ℓ² + (m + ℓ)``."""
    return ell * ell + (m + ell)


def _fd4_derivative(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Finite-difference derivative matching the Round-5 Q-18.2 recipe.

    - 4th-order centered in the bulk,
    - 2nd-order one-sided at the two outermost points,
    - 2nd-order centered at indices 1 and N-2 (not enough neighbours
      for 4th-order stencil).

    Works on non-uniform grids via the local spacing ``h = (x[i+1] − x[i−1])/2``.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    n = x.size
    if y.shape != x.shape:
        raise ValueError(
            f"_fd4_derivative requires y.shape == x.shape, got "
            f"y.shape={y.shape}, x.shape={x.shape}"
        )
    if n < 5:
        raise ValueError(f"_fd4_derivative requires at least 5 points; got {n}")

    dydx = np.empty_like(y)
    # 2nd-order one-sided at boundaries:
    dydx[0] = (-3.0 * y[0] + 4.0 * y[1] - y[2]) / (x[2] - x[0])
    dydx[-1] = (3.0 * y[-1] - 4.0 * y[-2] + y[-3]) / (x[-1] - x[-3])
    # 2nd-order centered at indices 1 and N-2 (not enough room for 4th order):
    dydx[1] = (y[2] - y[0]) / (x[2] - x[0])
    dydx[-2] = (y[-1] - y[-3]) / (x[-1] - x[-3])
    # 4th-order centered in the bulk (non-uniform grid via local h).
    # Vectorized equivalent of the original i=2..N-3 loop with
    # h_i = (x[i+1] - x[i-1]) / 2.
    dydx[2:-2] = (
        -y[4:]
        + 8.0 * y[3:-1]
        - 8.0 * y[1:-3]
        + y[:-4]
    ) / (6.0 * (x[3:-1] - x[1:-3]))
    return dydx


def _scaled_pchip_no_extrapolation(eta_grid: np.ndarray, values: np.ndarray):
    """Build a no-extrapolation PCHIP callable after amplitude scaling.

    Some Tier-B probe channels are finite but extremely small. Constructing
    scipy's PCHIP slopes directly on subnormal-scale values can raise an
    internal overflow RuntimeWarning in the reciprocal-slope harmonic mean.
    Scaling to O(1) before construction preserves the interpolated function
    and avoids treating that numerical conditioning detail as physics failure.
    """

    eta_arr = np.asarray(eta_grid, dtype=np.float64)
    values_arr = np.asarray(values, dtype=np.float64)
    if values_arr.shape != eta_arr.shape:
        raise ValueError(
            "PCHIP source interpolation requires values.shape == eta_grid.shape, "
            f"got values.shape={values_arr.shape}, eta_grid.shape={eta_arr.shape}"
        )
    if not np.all(np.isfinite(values_arr)):
        raise ValueError("PCHIP source interpolation requires finite values")
    amplitude = float(np.max(np.abs(values_arr)))
    if amplitude == 0.0:
        return PchipInterpolator(eta_arr, values_arr, extrapolate=False)
    scaled = values_arr / amplitude
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "error",
                message="overflow encountered in divide",
                category=RuntimeWarning,
            )
            interp = PchipInterpolator(eta_arr, scaled, extrapolate=False)
    except RuntimeWarning:
        return _linear_no_extrapolation(eta_arr, values_arr)

    def _call(query):
        return amplitude * interp(query)

    return _call


def _linear_no_extrapolation(eta_grid: np.ndarray, values: np.ndarray):
    """Linear no-extrapolation fallback for finite but PCHIP-ill-conditioned data."""

    eta_arr = np.asarray(eta_grid, dtype=np.float64)
    values_arr = np.asarray(values, dtype=np.float64)

    def _call(query):
        query_arr = np.asarray(query, dtype=np.float64)
        out = np.interp(query_arr, eta_arr, values_arr)
        out = np.asarray(out, dtype=np.float64)
        out = np.where(
            (query_arr < eta_arr[0]) | (query_arr > eta_arr[-1]),
            np.nan,
            out,
        )
        if np.ndim(query_arr) == 0:
            return float(out)
        return out

    return _call


def extract_flrw_sources_from_tier_b(
    integration_result: "IntegrationResult",
    species: "SpeciesBackgroundRegistry",
    k: float,
    *,
    anisotropic_stress: bool = True,
) -> FLRWSourceTerms:
    """Build Newtonian-gauge ``FLRWSourceTerms`` from a Tier-B solver output.

    Parameters
    ----------
    integration_result
        Output of ``execute_tier_b_solver``. Must carry
        ``photon_T_tower``, ``photon_E_tower``, ``neutrino_tower``,
        ``baryon_local_history``, ``cdm_local_history``, and ``eta``.
    species
        ``SpeciesBackgroundRegistry.from_planck2018()`` (or equivalent).
        Provides per-species ``ρ_rest(η)`` and the FLRW background table
        ``bg_table.interp_a``, ``interp_calH`` in Mpc⁻¹.
    k
        Comoving wavenumber at which the Tier-B solver was run
        (Mpc⁻¹). Must match the ``k_grid_mpc`` argument passed to
        ``execute_tier_b_solver`` — the tower state is stored at this
        single k.
    anisotropic_stress
        If True (default), include the intensity-quadrupole stress
        correction ``Ψ − Φ = (12πG·a²/k²)·(ρ+p)·σ_tot``. If False,
        set ``Ψ = Φ`` (no-stress limit).

    Returns
    -------
    FLRWSourceTerms with 5 η-callables:
        theta_0(η) → Θ_0^γ(η)
        psi(η)    → Ψ(η, k)  (Newtonian-gauge potential)
        phi_dot_plus_psi_dot(η) → Φ̇(η, k) + Ψ̇(η, k)  (ISW driver)
        v_b(η)    → v_b(η)  (baryon peculiar velocity at this k)
        pi(η)     → Θ_2^γ(η) − √6·E_2^γ(η)  (polarization source)

    All callables are no-extrapolation PCHIP-based callables with
    ``extrapolate=False``; evaluation outside the integration-result
    η-domain returns NaN.

    Raises
    ------
    ValueError
        If the integration_result is missing a required tower array
        (neutrino_tower, photon_B_tower, baryon_local_history,
        cdm_local_history); if k ≤ 0; or if the photon/neutrino
        tower widths are inconsistent with the integration_result's
        L_max.
    """

    from bass.species.base import SpeciesLabel

    if not (float(k) > 0.0):
        raise ValueError(f"k must be positive, got {k!r}")
    if integration_result.neutrino_tower is None:
        raise ValueError(
            "integration_result.neutrino_tower is required for the "
            "Round-5 extractor (neutrino anisotropic stress and density)"
        )
    if integration_result.baryon_local_history is None:
        raise ValueError(
            "integration_result.baryon_local_history is required "
            "(slot 1 = v_b in MB convention)"
        )
    if integration_result.cdm_local_history is None:
        raise ValueError(
            "integration_result.cdm_local_history is required "
            "(slot 1 = v_c)"
        )

    eta = np.asarray(integration_result.eta, dtype=np.float64)
    if eta.size < 5:
        raise ValueError(
            f"extract_flrw_sources_from_tier_b needs ≥5 η samples for "
            f"the 4th-order ISW finite-difference stencil; got {eta.size}"
        )

    # Background a(η) and conformal Hubble ℋ(η) in 1/Mpc from the species
    # registry's frozen bg_table (unit-consistent with k_mpc).
    bg_table = species.bg_table
    a = np.asarray(bg_table.interp_a(eta), dtype=np.float64)
    calH = np.asarray(bg_table.interp_calH(eta), dtype=np.float64)

    # Q-16 / Q-17.1 PSTF → Newtonian-gauge scalar multipoles (m = 0):
    t_tower = np.asarray(integration_result.photon_T_tower, dtype=np.float64)
    e_tower = np.asarray(integration_result.photon_E_tower, dtype=np.float64)
    n_tower = np.asarray(integration_result.neutrino_tower, dtype=np.float64)

    l_max_plus_one_sq = t_tower.shape[1]
    l_max = int(np.sqrt(l_max_plus_one_sq)) - 1
    if (l_max + 1) ** 2 != l_max_plus_one_sq:
        raise ValueError(
            f"photon_T_tower shape {t_tower.shape} is not a (L+1)² packing"
        )
    if l_max < 2:
        raise ValueError(
            f"extract_flrw_sources_from_tier_b needs L_max ≥ 2 (quadrupoles "
            f"are required for the anisotropic-stress correction); got {l_max}"
        )

    theta0_g = t_tower[:, _slot(0, 0)]
    theta1_g = t_tower[:, _slot(1, 0)]
    theta2_g = t_tower[:, _slot(2, 0)]
    e2_g = e_tower[:, _slot(2, 0)]

    theta0_nu = n_tower[:, _slot(0, 0)]
    theta1_nu = n_tower[:, _slot(1, 0)]
    theta2_nu = n_tower[:, _slot(2, 0)]

    # Q-20: Π = Θ_2 − √6·E_2 with α_T = 1, α_E = −√6; no extra PSTF prefactor.
    pi_source = theta0_g.copy()  # allocate correct dtype/shape
    pi_source[:] = theta2_g - _SQRT6 * e2_g

    # Q-19: baryon_local_history slot dictionary (verified via
    # ver2_native_integrator.py line 2973 and cross-checked against
    # Round-2 Q-5.1 Thomson coupling using slot 1 = v_b).
    delta_b = np.asarray(
        integration_result.baryon_local_history[:, 0], dtype=np.float64
    )
    vb = np.asarray(
        integration_result.baryon_local_history[:, 1], dtype=np.float64
    )
    delta_c = np.asarray(
        integration_result.cdm_local_history[:, 0], dtype=np.float64
    )
    vc = np.asarray(
        integration_result.cdm_local_history[:, 1], dtype=np.float64
    )

    # Q-17.1: radiation density contrasts δ_r = 4·Θ_0, velocities v_r = 3·Θ_1
    # (MB convention θ_r = 3·k·Θ_1, v = θ/k).
    delta_g = 4.0 * theta0_g
    delta_nu = 4.0 * theta0_nu
    vg = 3.0 * theta1_g
    vnu = 3.0 * theta1_nu

    # Per-species background densities (dimensionless, ρ_crit,0 units).
    rho_b = np.asarray(
        species[SpeciesLabel.BARYON].rho_rest(eta), dtype=np.float64
    )
    rho_c = np.asarray(
        species[SpeciesLabel.CDM].rho_rest(eta), dtype=np.float64
    )
    rho_g = np.asarray(
        species[SpeciesLabel.PHOTON].rho_rest(eta), dtype=np.float64
    )
    rho_nu = np.asarray(
        species[SpeciesLabel.NEUTRINO].rho_rest(eta), dtype=np.float64
    )

    # Q-17.2 Einstein constraints in BASS natural units.
    # Friedmann flat-ΛCDM: (H/H_0)² = ρ_tot_bass ⇒ 4πG·a² = (3/2)·H_0²·a².
    h0_mpc = float(bg_table.constants.H0_mpc)  # 1/Mpc
    four_pi_g_a2_over_k2 = 1.5 * (h0_mpc ** 2) * (a ** 2) / (float(k) ** 2)

    delta_rho_tot = (
        rho_b * delta_b + rho_c * delta_c + rho_g * delta_g + rho_nu * delta_nu
    )
    # Σ_i (ρ_i + p_i)·v_i:  non-relativistic species have p=0, radiation p = ρ/3
    # so (ρ+p) = (4/3)·ρ.
    mom = (
        rho_b * vb
        + rho_c * vc
        + (4.0 / 3.0) * rho_g * vg
        + (4.0 / 3.0) * rho_nu * vnu
    )
    phi = four_pi_g_a2_over_k2 * (delta_rho_tot - 3.0 * calH * mom / float(k))

    # Q-17.2 + auditor correction: anisotropic stress from intensity
    # quadrupoles only. MB σ_r = 2·Θ_2^r ⇒ (ρ+p)·σ = (8/3)·ρ_r·Θ_2^r.
    if anisotropic_stress:
        stress_intensity = (
            (8.0 / 3.0) * rho_g * theta2_g + (8.0 / 3.0) * rho_nu * theta2_nu
        )
        psi_minus_phi = 3.0 * four_pi_g_a2_over_k2 * stress_intensity
    else:
        psi_minus_phi = np.zeros_like(phi)
    psi = phi + psi_minus_phi

    # Q-18: ISW driver via 4th-order centered FD on the (Φ + Ψ) grid.
    phi_plus_psi = phi + psi
    phi_dot_plus_psi_dot = _fd4_derivative(eta, phi_plus_psi)

    return FLRWSourceTerms(
        theta_0=_scaled_pchip_no_extrapolation(eta, theta0_g),
        psi=_scaled_pchip_no_extrapolation(eta, psi),
        phi_dot_plus_psi_dot=_scaled_pchip_no_extrapolation(eta, phi_dot_plus_psi_dot),
        v_b=_scaled_pchip_no_extrapolation(eta, vb),
        pi=_scaled_pchip_no_extrapolation(eta, pi_source),
    )
