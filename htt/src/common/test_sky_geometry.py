"""COMMON-A tests — sky_geometry (INDEPENDENT_TRACKS_PLAN §2.6)."""
from __future__ import annotations

import math
import numpy as np
import pytest

from common.sky_geometry import (
    angular_separation_matrix,
    galactic_plane_mask,
    lb_to_unitvec,
    normalize_weights,
    spherical_mean,
    unitvec_to_lb,
)


# ---------------------------------------------------------------------------
# §1 — lb ↔ unitvec roundtrip
# ---------------------------------------------------------------------------

class TestLbUnitvecRoundtrip:
    def test_roundtrip_preserves_lb(self):
        l = np.array([0.0, 90.0, 180.0, 270.0, 359.9])
        b = np.array([0.0, 45.0, -30.0, 10.0, -80.0])
        vec = lb_to_unitvec(l, b)
        l2, b2 = unitvec_to_lb(vec)
        np.testing.assert_allclose(l, l2, atol=1e-10)
        np.testing.assert_allclose(b, b2, atol=1e-10)

    def test_unitvec_has_unit_norm(self):
        l = np.array([10.0, 200.0, 350.0])
        b = np.array([5.0, -70.0, 88.0])
        vec = lb_to_unitvec(l, b)
        np.testing.assert_allclose(np.linalg.norm(vec, axis=-1), 1.0, atol=1e-14)

    def test_wrap_longitude(self):
        """l=360° → 0° after roundtrip."""
        l = np.array([360.0])
        b = np.array([0.0])
        vec = lb_to_unitvec(l, b)
        l2, _ = unitvec_to_lb(vec)
        assert abs(l2[0] - 0.0) < 1e-9 or abs(l2[0] - 360.0) < 1e-9


# ---------------------------------------------------------------------------
# §2 — spherical_mean vs naive mean
# ---------------------------------------------------------------------------

class TestSphericalMean:
    def test_spherical_mean_vs_naive_mean_divergence(self):
        """Extreme longitudes: naive mean gives ~180°, spherical gives ~0°/360°."""
        l = np.array([0.0, 359.0, 1.0, 358.0])
        b = np.array([0.0, 0.0, 0.0, 0.0])
        naive = float(np.mean(l))         # ~ 179.5
        sph = spherical_mean(l, b)
        assert abs(naive - 179.5) < 0.1
        # Spherical mean should be near 0° / 360° (equator, longitude cluster)
        sph_l = sph["l_deg"]
        dist_to_zero = min(sph_l, 360.0 - sph_l)
        assert dist_to_zero < 1.0, f"spherical l_deg={sph_l} not near 0/360"
        assert sph["resultant_R"] > 0.99

    def test_mean_of_aligned_points_is_unit_R(self):
        l = np.array([30.0, 30.0, 30.0])
        b = np.array([15.0, 15.0, 15.0])
        r = spherical_mean(l, b)
        assert math.isclose(r["resultant_R"], 1.0, abs_tol=1e-12)
        assert math.isclose(r["l_deg"], 30.0, abs_tol=1e-10)
        assert math.isclose(r["b_deg"], 15.0, abs_tol=1e-10)

    def test_antipodal_points_cancel(self):
        l = np.array([0.0, 180.0])
        b = np.array([0.0, 0.0])
        r = spherical_mean(l, b)
        assert r["resultant_R"] < 1e-12
        assert math.isnan(r["l_deg"])

    def test_weighted_mean_respects_weight(self):
        l = np.array([0.0, 90.0])
        b = np.array([0.0, 0.0])
        r_eq = spherical_mean(l, b, np.array([1.0, 1.0]))
        r_heavy_zero = spherical_mean(l, b, np.array([10.0, 1.0]))
        # With w = (1,1) the mean sits at 45°; with w = (10,1) closer to 0°.
        assert r_heavy_zero["l_deg"] < r_eq["l_deg"]

    def test_mismatched_weight_shape_raises(self):
        with pytest.raises(ValueError, match="shape"):
            spherical_mean(
                np.array([0.0, 90.0]), np.array([0.0, 0.0]), np.array([1.0])
            )

    def test_nonpositive_weight_sum_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            spherical_mean(
                np.array([0.0, 1.0]), np.array([0.0, 0.0]),
                np.array([1.0, -1.0]),
            )


# ---------------------------------------------------------------------------
# §3 — angular_separation_matrix
# ---------------------------------------------------------------------------

class TestAngularSeparation:
    def test_self_separation_is_zero(self):
        l = np.array([30.0, 120.0, 250.0])
        b = np.array([10.0, -40.0, 60.0])
        M = angular_separation_matrix(l, b)
        # arccos(1 − ε) ≈ √(2ε); for double precision this is ~2e-6 deg.
        np.testing.assert_allclose(np.diag(M), 0.0, atol=1e-4)

    def test_symmetry(self):
        l = np.array([0.0, 90.0, 180.0])
        b = np.array([0.0, 0.0, 0.0])
        M = angular_separation_matrix(l, b)
        np.testing.assert_allclose(M, M.T, atol=1e-12)

    def test_equatorial_right_angle(self):
        l = np.array([0.0, 90.0])
        b = np.array([0.0, 0.0])
        M = angular_separation_matrix(l, b)
        assert math.isclose(M[0, 1], 90.0, abs_tol=1e-10)


# ---------------------------------------------------------------------------
# §4 — galactic_plane_mask
# ---------------------------------------------------------------------------

class TestGalacticPlaneMask:
    def test_mask_keeps_high_latitude(self):
        b = np.array([5.0, 25.0, -30.0, -5.0])
        mask = galactic_plane_mask(b, 20.0)
        np.testing.assert_array_equal(mask, [False, True, True, False])

    def test_boundary_is_inclusive(self):
        """|b| = half_angle should be kept (≥, not >)."""
        b = np.array([20.0, -20.0])
        mask = galactic_plane_mask(b, 20.0)
        np.testing.assert_array_equal(mask, [True, True])


# ---------------------------------------------------------------------------
# §5 — normalize_weights (production fallback gate)
# ---------------------------------------------------------------------------

class TestNormalizeWeights:
    def test_native_path(self):
        w, status = normalize_weights(np.array([1.0, 2.0, 1.0]))
        assert status == "native_weights"
        assert math.isclose(w.sum(), 1.0, rel_tol=1e-14)

    def test_all_zero_rejects_in_production(self):
        with pytest.raises(ValueError, match="forbidden"):
            normalize_weights(np.zeros(5), allow_uniform_fallback=False)

    def test_all_zero_allowed_in_diagnostic(self):
        w, status = normalize_weights(np.zeros(4), allow_uniform_fallback=True)
        assert status == "uniform_fallback_diagnostic_only"
        np.testing.assert_allclose(w, 0.25)

    def test_negative_weight_sum_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            normalize_weights(np.array([1.0, -2.0]))

    def test_mixed_sign_positive_sum_rejected(self):
        with pytest.raises(ValueError, match="non-negative"):
            normalize_weights(np.array([2.0, -1.0]))

    def test_nonfinite_weight_rejected(self):
        with pytest.raises(ValueError, match="finite"):
            normalize_weights(np.array([1.0, np.nan]))
