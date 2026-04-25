"""Tests for the per-k LoS η-grid builder (Round-15 P0 D-1 fix)."""
from __future__ import annotations

import numpy as np
import pytest

from bass.los.los_grid_builder import build_los_grid


# ----------------------------------------------------------------------
# Input validation
# ----------------------------------------------------------------------


@pytest.mark.parametrize("bad_k", [0.0, -1.0e-3, np.inf, np.nan])
def test_rejects_non_positive_or_non_finite_k(bad_k: float) -> None:
    with pytest.raises(ValueError, match="k must be positive finite"):
        build_los_grid(bad_k, eta_today=14147.0, eta_init=261.0)


@pytest.mark.parametrize("bad_eta_today", [0.0, -1.0, np.inf, np.nan])
def test_rejects_non_positive_or_non_finite_eta_today(bad_eta_today: float) -> None:
    with pytest.raises(ValueError, match="eta_today must be positive finite"):
        build_los_grid(1.0e-2, eta_today=bad_eta_today, eta_init=261.0)


def test_rejects_non_finite_eta_init() -> None:
    with pytest.raises(ValueError, match="eta_init must be finite"):
        build_los_grid(1.0e-2, eta_today=14147.0, eta_init=np.nan)


def test_rejects_eta_init_ge_eta_today() -> None:
    with pytest.raises(ValueError, match="eta_init .* must be < eta_today"):
        build_los_grid(1.0e-2, eta_today=14147.0, eta_init=14147.0)


def test_rejects_n_per_oscillation_below_nyquist() -> None:
    with pytest.raises(ValueError, match="n_per_oscillation must be >= 2"):
        build_los_grid(
            1.0e-2, eta_today=14147.0, eta_init=261.0, n_per_oscillation=1,
        )


def test_rejects_n_per_recomb_fwhm_too_small() -> None:
    with pytest.raises(ValueError, match="n_per_recomb_fwhm must be >= 2"):
        build_los_grid(
            1.0e-2, eta_today=14147.0, eta_init=261.0, n_per_recomb_fwhm=1,
        )


def test_rejects_non_positive_recomb_fwhm() -> None:
    with pytest.raises(ValueError, match="recomb_fwhm must be positive"):
        build_los_grid(1.0e-2, eta_today=14147.0, eta_init=261.0, recomb_fwhm=0.0)


# ----------------------------------------------------------------------
# Grid geometry
# ----------------------------------------------------------------------


@pytest.mark.parametrize("k", [1.0e-4, 1.0e-3, 1.0e-2, 5.0e-2, 1.0e-1])
def test_grid_endpoints_match_inputs(k: float) -> None:
    eta_init = 261.0
    eta_today = 14147.0
    grid = build_los_grid(k, eta_today=eta_today, eta_init=eta_init)
    assert grid[0] == pytest.approx(eta_init, abs=1e-12)
    assert grid[-1] == pytest.approx(eta_today, abs=1e-9)


@pytest.mark.parametrize("k", [1.0e-4, 1.0e-3, 1.0e-2, 5.0e-2, 1.0e-1])
def test_grid_strictly_monotone_increasing(k: float) -> None:
    grid = build_los_grid(k, eta_today=14147.0, eta_init=261.0)
    diffs = np.diff(grid)
    assert np.all(diffs > 0.0), (
        f"non-monotone at k={k}: min diff = {diffs.min():.3e}"
    )


def test_recombination_zone_resolves_visibility_fwhm() -> None:
    """Zone 1 must place at least n_per_recomb_fwhm samples inside the FWHM."""
    grid = build_los_grid(
        1.0e-2, eta_today=14147.0, eta_init=261.0,
        recomb_eta=281.0, recomb_fwhm=19.0, n_per_recomb_fwhm=8,
    )
    # FWHM window: [281 - 9.5, 281 + 9.5]
    fwhm_lo, fwhm_hi = 271.5, 290.5
    in_fwhm = grid[(grid >= fwhm_lo) & (grid <= fwhm_hi)]
    assert in_fwhm.size >= 7, (
        f"zone 1 placed only {in_fwhm.size} samples inside the FWHM "
        f"(want ≥ 7); spacing breakdown:"
        f"\n  first 10 grid pts = {grid[:10]}"
    )


def test_oscillation_zone_resolves_bessel_period_at_high_k() -> None:
    """At k=0.05, the Bessel period 2π/k ≈ 125.7 Mpc must be Nyquist-resolved
    in zone 2."""
    k = 0.05
    grid = build_los_grid(
        k, eta_today=14147.0, eta_init=261.0,
        n_per_oscillation=8,
    )
    # Grab samples in the deep late-time band away from zone 1.
    late = grid[grid > 1000.0]
    deta_late = np.median(np.diff(late))
    period = 2.0 * np.pi / k
    assert deta_late <= period / 4.0, (
        f"late-time spacing {deta_late:.3f} Mpc exceeds Nyquist for "
        f"period {period:.3f} Mpc"
    )


def test_low_k_does_not_explode_grid_size() -> None:
    """For k where 2π/k > eta_today, the oscillation step should be bounded
    by max_oscillation_step_mpc — not collapse to two points."""
    grid = build_los_grid(
        1.0e-5, eta_today=14147.0, eta_init=261.0,
        max_oscillation_step_mpc=200.0,
    )
    late = grid[grid > 1000.0]
    deta_late = np.median(np.diff(late))
    assert deta_late <= 200.0 + 1.0
    assert grid.size > 50  # sane lower bound


def test_high_k_capped_by_max_total_points() -> None:
    """Very high k must not produce a grid larger than max_total_points."""
    grid = build_los_grid(
        1.0,
        eta_today=14147.0, eta_init=261.0,
        max_total_points=2000,
    )
    assert grid.size <= 2000


def test_grid_dtype_is_float64() -> None:
    grid = build_los_grid(1.0e-2, eta_today=14147.0, eta_init=261.0)
    assert grid.dtype == np.float64


def test_recombination_window_is_better_resolved_than_uniform_64() -> None:
    """Round-15 P0 acceptance: the new grid must place strictly more samples
    inside the visibility FWHM than the legacy 64-pt uniform-linear grid."""
    eta_init, eta_today = 261.0, 14147.0
    new = build_los_grid(1.0e-2, eta_today=eta_today, eta_init=eta_init)
    legacy = np.linspace(eta_init, eta_today, 64)
    fwhm_lo, fwhm_hi = 271.5, 290.5
    n_new = int(np.sum((new >= fwhm_lo) & (new <= fwhm_hi)))
    n_legacy = int(np.sum((legacy >= fwhm_lo) & (legacy <= fwhm_hi)))
    assert n_new > n_legacy, (
        f"new grid puts {n_new} pts in FWHM vs legacy {n_legacy}; "
        f"D-1 fix did not refine recombination zone"
    )


def test_recomb_window_truncates_when_eta_today_in_zone() -> None:
    """If eta_today lies inside the recombination window the result is just
    zone 1 (single zone), without raising."""
    grid = build_los_grid(
        1.0e-2, eta_today=320.0, eta_init=261.0,
        recomb_eta=281.0, recomb_fwhm=19.0,
    )
    assert grid[0] == pytest.approx(261.0, abs=1e-12)
    assert grid[-1] == pytest.approx(320.0, abs=1e-9)
    assert np.all(np.diff(grid) > 0)
