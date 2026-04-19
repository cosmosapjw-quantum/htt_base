"""COMMON-B tests — healpix_selection (INDEPENDENT_TRACKS_PLAN §3.1)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from common.healpix_selection import (
    build_angular_completeness,
    build_occupancy_map,
    build_zoa_mask,
    compute_selection_weights,
    lb_to_pix,
    nside_to_npix,
    pixel_centers,
    pixel_solid_angle,
    posterior_density_map,
)
from common.sky_geometry import normalize_weights


def _isotropic_catalogue(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    cos_b = rng.uniform(-1.0, 1.0, size=n)
    b = np.rad2deg(np.arcsin(cos_b))
    l = rng.uniform(0.0, 360.0, size=n)
    return l, b


# ---------------------------------------------------------------------------
# §1 — pixelization primitives
# ---------------------------------------------------------------------------

class TestPixelizationPrimitives:
    def test_npix_formula(self):
        for nside in (1, 2, 4, 8, 16, 32, 64):
            assert nside_to_npix(nside) == 2 * nside * nside

    def test_rejects_non_power_of_two(self):
        with pytest.raises(ValueError, match="power of two"):
            nside_to_npix(3)

    def test_rejects_nonpositive_nside(self):
        with pytest.raises(ValueError, match="power of two"):
            nside_to_npix(0)

    def test_centers_cover_full_sphere(self):
        l, b = pixel_centers(8)
        assert l.shape == b.shape == (nside_to_npix(8),)
        assert l.min() >= 0.0 and l.max() < 360.0
        assert b.min() >= -90.0 and b.max() <= 90.0

    def test_pixel_solid_angle_sums_to_sphere(self):
        nside = 16
        omega = pixel_solid_angle(nside)
        np.testing.assert_allclose(
            omega * nside_to_npix(nside), 4.0 * math.pi, rtol=1e-12
        )

    def test_lb_to_pix_roundtrip_into_valid_range(self):
        rng = np.random.default_rng(0)
        l, b = _isotropic_catalogue(rng, 500)
        pix = lb_to_pix(l, b, nside=16)
        assert pix.shape == (500,)
        assert pix.min() >= 0
        assert pix.max() < nside_to_npix(16)


# ---------------------------------------------------------------------------
# §2 — ZoA mask
# ---------------------------------------------------------------------------

class TestBuildZoAMask:
    def test_mask_excludes_galactic_plane(self):
        mask = build_zoa_mask(None, None, bcut_deg=10.0, nside=16)
        _, b_centers = pixel_centers(16)
        # Pixels with |b_center| < 10 should be False, ≥ 10 True.
        np.testing.assert_array_equal(mask, np.abs(b_centers) >= 10.0)

    def test_zero_bcut_keeps_all(self):
        mask = build_zoa_mask(None, None, bcut_deg=0.0, nside=8)
        assert mask.all()

    def test_90_bcut_drops_all(self):
        mask = build_zoa_mask(None, None, bcut_deg=90.0, nside=8)
        assert not mask.any()

    def test_invalid_bcut_raises(self):
        with pytest.raises(ValueError, match="bcut_deg"):
            build_zoa_mask(None, None, bcut_deg=-1.0, nside=8)
        with pytest.raises(ValueError, match="bcut_deg"):
            build_zoa_mask(None, None, bcut_deg=91.0, nside=8)

    def test_shape_mismatch_rejected(self):
        with pytest.raises(ValueError, match="shape"):
            build_zoa_mask(
                np.array([0.0, 1.0]), np.array([0.0]), bcut_deg=10.0, nside=8
            )


# ---------------------------------------------------------------------------
# §3 — Occupancy + completeness
# ---------------------------------------------------------------------------

class TestOccupancyAndCompleteness:
    def test_occupancy_sum_equals_n_sources(self):
        rng = np.random.default_rng(1)
        l, b = _isotropic_catalogue(rng, 2000)
        occ = build_occupancy_map(l, b, nside=16)
        assert occ.sum() == 2000
        assert occ.shape == (nside_to_npix(16),)

    def test_completeness_max_one(self):
        rng = np.random.default_rng(2)
        l, b = _isotropic_catalogue(rng, 500)
        cmap = build_angular_completeness(l, b, nside=16, smooth_sigma_pix=1.0)
        assert cmap.shape == (nside_to_npix(16),)
        assert 0.0 <= cmap.min() <= cmap.max()
        assert math.isclose(cmap.max(), 1.0, abs_tol=1e-12)

    def test_completeness_smoother_than_raw(self):
        rng = np.random.default_rng(3)
        l, b = _isotropic_catalogue(rng, 300)
        occ = build_occupancy_map(l, b, nside=16).astype(float)
        raw_var = float(occ.var())
        smooth = build_angular_completeness(l, b, nside=16, smooth_sigma_pix=2.0)
        smooth_scaled = smooth * float(occ.max()) if occ.max() > 0 else smooth
        assert float(smooth_scaled.var()) < raw_var

    def test_empty_catalogue_returns_zero_map(self):
        l = np.array([], dtype=float)
        b = np.array([], dtype=float)
        cmap = build_angular_completeness(l, b, nside=8, smooth_sigma_pix=1.0)
        assert cmap.shape == (nside_to_npix(8),)
        np.testing.assert_array_equal(cmap, np.zeros_like(cmap))


# ---------------------------------------------------------------------------
# §4 — Selection weights
# ---------------------------------------------------------------------------

class TestComputeSelectionWeights:
    def test_masked_source_has_zero_weight(self):
        rng = np.random.default_rng(4)
        l, b = _isotropic_catalogue(rng, 200)
        nside = 16
        mask = build_zoa_mask(l, b, bcut_deg=15.0, nside=nside)
        cmap = build_angular_completeness(l, b, nside=nside)
        w = compute_selection_weights(l, b, mask, cmap)
        pix = lb_to_pix(l, b, nside)
        inside = mask[pix]
        assert np.all(w[~inside] == 0.0)
        assert np.all(w[inside] > 0.0)

    def test_inverse_completeness_scaling(self):
        # A single source in a sparse pixel should get a larger weight than
        # a source in a dense pixel.
        l_dense = np.full(50, 30.0)
        b_dense = np.full(50, 30.0)
        l_sparse = np.array([150.0])
        b_sparse = np.array([60.0])
        l = np.concatenate([l_dense, l_sparse])
        b = np.concatenate([b_dense, b_sparse])
        nside = 16
        mask = np.ones(nside_to_npix(nside), dtype=bool)
        cmap = build_angular_completeness(l, b, nside=nside, smooth_sigma_pix=0.5)
        w = compute_selection_weights(l, b, mask, cmap)
        assert w[-1] > w[0], "sparse-pixel source should outweigh dense-pixel source"

    def test_rejects_shape_mismatch(self):
        nside = 8
        mask = np.ones(nside_to_npix(nside), dtype=bool)
        cmap = np.ones(nside_to_npix(nside) + 1)
        with pytest.raises(ValueError, match="C_pix"):
            compute_selection_weights(
                np.array([0.0]), np.array([0.0]), mask, cmap
            )

    def test_rejects_nonpositive_eps(self):
        nside = 8
        mask = np.ones(nside_to_npix(nside), dtype=bool)
        cmap = np.ones(nside_to_npix(nside))
        with pytest.raises(ValueError, match="eps"):
            compute_selection_weights(
                np.array([0.0]), np.array([0.0]), mask, cmap, eps=0.0
            )


# ---------------------------------------------------------------------------
# §5 — Posterior density
# ---------------------------------------------------------------------------

class TestPosteriorDensityMap:
    def test_sums_to_one(self):
        rng = np.random.default_rng(5)
        l, b = _isotropic_catalogue(rng, 1000)
        dmap = posterior_density_map(l, b, nside=16)
        assert math.isclose(dmap.sum(), 1.0, rel_tol=1e-12)

    def test_empty_samples_uniform(self):
        dmap = posterior_density_map(
            np.array([], dtype=float), np.array([], dtype=float), nside=4
        )
        n_pix = nside_to_npix(4)
        np.testing.assert_allclose(dmap, np.full(n_pix, 1.0 / n_pix))


# ---------------------------------------------------------------------------
# §6 — REG-01 regression: ladder must not silently fall back to uniform
# ---------------------------------------------------------------------------

class TestZoALadderNoFallbackLeak:
    """REG-01: Mode 0 ZoA ladder must not leak a uniform-fallback into Mode 1/2.

    The ladder scans bcut ∈ [0°, 89°]. When the cut is so aggressive that
    every source in the catalogue falls inside the ZoA, the selection weights
    collapse to all-zero — and :func:`common.sky_geometry.normalize_weights`
    must raise (not silently hand back a uniform distribution) whenever
    ``allow_uniform_fallback=False``. A silent fallback would contaminate
    the Mode 1/Mode 2 downstream with a fictitious "uniform" axis instead
    of surfacing the Mode-0-unresolved cell.
    """

    def _make_equatorial_catalogue(self, n: int = 80) -> tuple[np.ndarray, np.ndarray]:
        """All sources near the galactic equator so high bcut excludes every one."""
        rng = np.random.default_rng(42)
        l = rng.uniform(0.0, 360.0, size=n)
        b = rng.uniform(-5.0, 5.0, size=n)
        return l, b

    def test_ladder_mid_cut_preserves_native_weights(self):
        l, b = self._make_equatorial_catalogue(80)
        nside = 16
        # At mid-cut (3°) the ZoA removes some equatorial sources but leaves
        # the rest with native (non-uniform) selection weights.
        mask = build_zoa_mask(l, b, bcut_deg=3.0, nside=nside)
        cmap = build_angular_completeness(l, b, nside=nside, smooth_sigma_pix=1.0)
        w_raw = compute_selection_weights(l, b, mask, cmap)
        assert (w_raw > 0.0).any()
        w_norm, status = normalize_weights(w_raw, allow_uniform_fallback=False)
        assert status == "native_weights"
        # Native ≠ uniform: the nonzero weights must not all be equal.
        nonzero = w_norm[w_norm > 0.0]
        assert nonzero.size >= 2
        assert float(nonzero.std()) > 0.0, (
            "native selection weights collapsed to a uniform value — "
            "that is the very leak REG-01 guards against"
        )

    def test_ladder_high_cut_raises_when_fallback_forbidden(self):
        l, b = self._make_equatorial_catalogue(80)
        nside = 16
        # Aggressive cut excludes every source → all weights collapse to zero.
        mask = build_zoa_mask(l, b, bcut_deg=60.0, nside=nside)
        cmap = build_angular_completeness(l, b, nside=nside, smooth_sigma_pix=1.0)
        w_raw = compute_selection_weights(l, b, mask, cmap)
        assert np.allclose(w_raw, 0.0), (
            "test precondition: equatorial catalogue must be entirely excluded "
            "by the aggressive cut so that weights collapse to zero"
        )
        # Production path (allow_uniform_fallback=False) MUST raise.
        with pytest.raises(ValueError, match="forbidden"):
            normalize_weights(w_raw, allow_uniform_fallback=False)

    def test_ladder_high_cut_explicit_diagnostic_fallback(self):
        l, b = self._make_equatorial_catalogue(80)
        nside = 16
        mask = build_zoa_mask(l, b, bcut_deg=60.0, nside=nside)
        cmap = build_angular_completeness(l, b, nside=nside, smooth_sigma_pix=1.0)
        w_raw = compute_selection_weights(l, b, mask, cmap)
        # Only when the caller *explicitly* opts into diagnostic mode does the
        # fallback activate — and it is marked with the diagnostic-only status.
        w_norm, status = normalize_weights(w_raw, allow_uniform_fallback=True)
        assert status == "uniform_fallback_diagnostic_only"
        np.testing.assert_allclose(w_norm, 1.0 / w_norm.size)
