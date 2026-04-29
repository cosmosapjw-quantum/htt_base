"""Per-k line-of-sight (LoS) η-grid builder for the FLRW transfer projector.

Round-15 P0 D-1 fix
-------------------
Decouples the LoS quadrature grid from the IMEX integrator output grid.
The integrator returns η on a 64-point uniform-linear grid spanning
~[261, 14147] Mpc (Δη ≈ 220 Mpc). That spacing is fatal to the LoS
quadrature for two independent reasons:

1. Visibility undersampling: the recombination visibility g(η) has FWHM
   ≈ 19 Mpc; with Δη = 220 Mpc only a single grid point lies inside
   the visibility peak, so the SW/polter contribution is captured at
   essentially one η-sample.

2. Bessel aliasing: the kernel j_ℓ[k(η_0 − η)] oscillates with period
   2π/k. For sub-horizon modes (k ~ 0.05/Mpc) this is ~125 Mpc, well
   below 220 Mpc, so the trapezoidal integral aliases the oscillation
   and produces 10-100× over-amplification or sign flips.

Round-15 §10 decisive test (`scripts/v5_round15_decisive_los_test.py`)
fed *perfect* CAMB Newtonian-gauge T_source through the existing 64-point
grid + projector and observed: 0/12 cells within 5%, 4/12 sign-flipped,
median |ratio| 8.30, max |ratio| 3687 — confirming the LoS grid (not the
source extractor) is the dominant defect ("Case D" classification).

This module produces a composite, per-k grid:

    Zone 1 — recombination-refined window
        [eta_init, recomb_eta + 5·recomb_fwhm]
        with Δη = recomb_fwhm / n_per_recomb_fwhm  (default ≈ 2.4 Mpc)
        captures the visibility peak with ~8 samples per FWHM.

    Zone 2 — k-adapted oscillation band
        [zone1_end, eta_today]
        with Δη = (2π / k) / n_per_oscillation     (default ≥ Nyquist×4)
        Nyquist-resolves the Bessel kernel.

A maximum-Δη ceiling caps the oscillation step for very-low k where the
"period" exceeds the full history (otherwise zone 2 would degenerate to
two points).  A maximum-total-points cap protects against pathological
high-k explosions while keeping zone 1 fully sampled.

Source callables (PchipInterpolator with extrapolate=False) are
evaluated on the new grid; the caller MUST pass `eta_init` ≥ the
integrator's η[0] so PCHIP does not return NaN. The recommended pattern
is `eta_init = float(integration_result.eta[0])`.
"""
from __future__ import annotations

import numpy as np

__all__ = ["build_los_grid"]


def build_los_grid(
    k: float,
    eta_today: float,
    eta_init: float,
    *,
    n_per_oscillation: int = 8,
    recomb_eta: float = 281.0,
    recomb_fwhm: float = 19.0,
    n_per_recomb_fwhm: int = 8,
    sparse_late_isw: bool = True,
    max_total_points: int = 8000,
    max_oscillation_step_mpc: float = 200.0,
) -> np.ndarray:
    """Composite η-grid for LoS quadrature at a single wavenumber.

    Parameters
    ----------
    k : float
        Comoving wavenumber, 1/Mpc. Must be positive finite.
    eta_today : float
        Conformal time at the observer, Mpc. Sets the upper grid bound.
    eta_init : float
        Earliest η in the grid (lower bound). MUST satisfy
        ``eta_init >= integration_result.eta[0]`` so that source
        PchipInterpolators (with ``extrapolate=False``) evaluate to
        finite values at the grid endpoints.
    n_per_oscillation : int, default 8
        Samples per Bessel oscillation period 2π/k. Eight gives a
        comfortable margin above the Nyquist limit of 2 for trapezoidal
        quadrature.
    recomb_eta : float, default 281.0
        Approximate η at the recombination visibility peak, Mpc.
    recomb_fwhm : float, default 19.0
        Approximate FWHM of the recombination visibility, Mpc.
    n_per_recomb_fwhm : int, default 8
        Samples per visibility FWHM in zone 1.
    sparse_late_isw : bool, default True
        Reserved for future late-ISW grid relaxation. Currently has no
        effect — the k-adapted spacing in zone 2 already Nyquist-samples
        the Bessel kernel across the full late-time history, which is
        also what the late-ISW driver needs.
    max_total_points : int, default 8000
        Hard cap on the returned grid size. If exceeded, zone 2 is
        downsampled while zone 1 is preserved fully. Eight thousand is
        roughly 100× the 64-point baseline and still affordable for the
        scipy.special.spherical_jn evaluation cost in the projector.
    max_oscillation_step_mpc : float, default 200.0
        Upper bound on Δη in zone 2. For very low k (period larger than
        the entire history) this prevents zone 2 collapsing to two
        endpoints. 200 Mpc places ≥ 70 samples across a 14000 Mpc late
        history, which is ample for the smooth ISW driver.

    Returns
    -------
    eta_grid : ndarray, shape (N,)
        Strictly monotone increasing. ``eta_grid[0] == eta_init``,
        ``eta_grid[-1] == eta_today`` (to floating precision).

    Raises
    ------
    ValueError
        If inputs are non-finite, non-positive where positivity is
        required, or geometrically inconsistent
        (``eta_init >= eta_today``).
    """
    if not (np.isfinite(k) and k > 0.0):
        raise ValueError(f"k must be positive finite; got {k!r}")
    if not (np.isfinite(eta_today) and eta_today > 0.0):
        raise ValueError(f"eta_today must be positive finite; got {eta_today!r}")
    if not np.isfinite(eta_init):
        raise ValueError(f"eta_init must be finite; got {eta_init!r}")
    if eta_init >= eta_today:
        raise ValueError(
            f"eta_init ({eta_init}) must be < eta_today ({eta_today})"
        )
    if n_per_oscillation < 2:
        raise ValueError(
            f"n_per_oscillation must be >= 2 (Nyquist); got {n_per_oscillation}"
        )
    if n_per_recomb_fwhm < 2:
        raise ValueError(
            f"n_per_recomb_fwhm must be >= 2; got {n_per_recomb_fwhm}"
        )
    if recomb_fwhm <= 0.0:
        raise ValueError(f"recomb_fwhm must be positive; got {recomb_fwhm}")
    if max_total_points < 16:
        raise ValueError(
            f"max_total_points must be >= 16; got {max_total_points}"
        )
    if max_oscillation_step_mpc <= 0.0:
        raise ValueError(
            f"max_oscillation_step_mpc must be positive; "
            f"got {max_oscillation_step_mpc}"
        )

    # Zone 1 — recombination-refined window.
    deta_recomb = recomb_fwhm / float(n_per_recomb_fwhm)
    recomb_window_end = recomb_eta + 5.0 * recomb_fwhm
    zone1_end = min(recomb_window_end, eta_today)
    zone1_end = max(zone1_end, eta_init + deta_recomb)  # ensure non-empty
    n_zone1 = max(2, int(np.ceil((zone1_end - eta_init) / deta_recomb)) + 1)
    zone1 = np.linspace(eta_init, zone1_end, n_zone1)

    # If the recomb window already reaches eta_today, we are done.
    if zone1[-1] >= eta_today - 1.0e-12:
        zone1[-1] = eta_today
        return zone1.astype(np.float64, copy=False)

    # Zone 2 — k-adapted oscillation band.
    period = 2.0 * np.pi / k
    deta_osc = period / float(n_per_oscillation)
    deta_osc = min(deta_osc, max_oscillation_step_mpc)
    n_zone2 = max(2, int(np.ceil((eta_today - zone1[-1]) / deta_osc)) + 1)
    zone2 = np.linspace(zone1[-1], eta_today, n_zone2)

    # Concatenate without repeating the shared boundary point.
    grid = np.concatenate([zone1, zone2[1:]])

    # Cap to max_total_points: preserve zone 1, downsample zone 2.
    if grid.size > max_total_points:
        budget_zone2 = max_total_points - n_zone1 + 1
        if budget_zone2 < 2:
            budget_zone2 = 2
        zone2_capped = np.linspace(zone1[-1], eta_today, budget_zone2)
        grid = np.concatenate([zone1, zone2_capped[1:]])

    # `sparse_late_isw` reserved for a future refinement; currently a no-op.
    _ = sparse_late_isw

    return grid.astype(np.float64, copy=False)
