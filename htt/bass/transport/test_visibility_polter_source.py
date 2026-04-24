"""Tests for bass.transport.visibility_polter_source (Week 8-03).

Coverage plan:
- Config dataclass
- Three Π paths (PSTF, subleading, TCA-solve) + closed form (Path D)
- Four-path genuine cross-check at general sources (machine precision)
- Visibility-weighted Π (PSTF and CAMB)
- Peak and integral diagnostics
- Physical sign assertions (v1.2 pattern)
- η(z) light utility
- Scope guards
- Reionization-extended g behavior

Fixture tiers (R0 / R2 separation)
----------------------------------
R0 = synthetic fixture: NON-PHYSICAL shape (κ ∝ ∫τ̇ with artificial
    10⁻² scale factor, not c/((1+z)H)). Its peak is at z ≈ 1361, NOT
    at real recombination. Used for algebra / linearity / broadcast /
    self-consistency checks only. Physics-range asserts are forbidden
    on this tier.

R2 = HyRec-derived scalar history (bass/recombination/fixtures/
    recombination_ref_planck2018.csv): physical visibility, peak at
    z ≈ 1088.8, z*(κ=1) ≈ 1089.9 within Planck 2018 ref 1089.95±0.27.
    Used for physics-range assertions (peak location, optical-depth
    normalization, reion bump cross-check).

The R1 semi-physical rung (calibrated tanh x_e + proper H(z) geometry)
is already absorbed by the W8-01 loader + W8-02 extender working on
the HyRec CSV, so no separate R1 fixture is maintained.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from bass.closure.quadrupole_tca import combined_source_pi, polter_camb
from bass.recombination.recombination_ingest import (
    build_interpolators,
    load_recombination_table,
    make_synthetic_tanh_table,
)
from bass.recombination.reionization import (
    CosmologyForRecombination,
    ReionizationParameters,
    extend_table_with_reionization,
)
from bass.runtime.canonical_decision import (
    CanonicalBlockError,
    CanonicalDecision,
    make_canonical_decision,
)
from tsc.diagnostics.tangency import compute_D_diagnostic, TangentKind
from bass.transport.visibility_polter_source import (
    C_IN_MPC_PER_S,
    OutOfScopeError,
    VisibilityPolterConfig,
    assert_gpi_peak_near_last_scattering,
    assert_pi_sign_matches_theta2_at_subleading,
    assert_visibility_positive,
    conformal_lookback_at_z,
    conformal_time_at_z,
    doppler_source,
    four_path_pi_residual_general,
    full_los_integral,
    g_weighted_pi_on_grid,
    g_weighted_pi_pstf,
    g_weighted_polter_camb,
    gpi_integral_trap_in_z,
    gpi_peak_in_z,
    isw_source,
    pi_closed_form_from_sources,
    pi_from_tca_sources,
    pi_pstf,
    pi_subleading_limit,
    polter_camb_at,
    three_way_pi_residual_at_subleading,
)


SQRT6 = np.sqrt(6.0)


# ============================================================================
# Canonical decision helpers (mirror of bass/closure/test_quadrupole_tca.py)
# ============================================================================

def _on_manifold_G(x):
    return np.asarray(x, dtype=float)


def _allowing_decision() -> CanonicalDecision:
    """Factory-built allowing decision for W3-gated call sites.

    Direct construction of `CanonicalDecision` is NOT a sanctioned
    path per `CANONICAL_DECISION_DESIGN.md` §2; all callers route
    through `make_canonical_decision`. This helper mirrors the
    pattern in `bass/closure/test_quadrupole_tca.py` to keep tests
    consistent with the W3 discipline.
    """
    tang = compute_D_diagnostic(
        G_field=_on_manifold_G, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    return make_canonical_decision(
        beta_result=(True, {
            "beta": 1.36e-3, "beta_max": 8.62e-3, "slack": 7.26e-3,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )


def _blocking_decision() -> CanonicalDecision:
    """Factory-built blocking decision (beta gate fails)."""
    tang = compute_D_diagnostic(
        G_field=_on_manifold_G, kind=TangentKind.ONE_FIELD, xi=0, eta=0.0,
    )
    return make_canonical_decision(
        beta_result=(False, {
            "beta": 0.5, "beta_max": 8.62e-3, "slack": -0.491,
            "eta_u_dot": 0.16, "safety_factor": 0.5, "epsilon_1": 0.02,
        }),
        sigma_result=(True, {
            "sigma_sq": 1e-5, "floor": 1e-6, "log_margin_decades": 1.0,
        }),
        tangency_result=tang,
    )


# ============================================================================
# R0 — Synthetic fixtures (self-consistency tier)
# ============================================================================

@pytest.fixture
def synthetic_interp():
    """R0 fixture: non-physical tanh shape. Peak at z ≈ 1361, NOT 1089.

    Usage restriction: algebra / linearity / broadcast / sign /
    self-consistency only. Physics-range asserts forbidden.
    """
    table = make_synthetic_tanh_table(
        z_min=1.0, z_max=3000.0, n_points=600,
        z_transition=1089.0, transition_width=100.0,
    )
    return build_interpolators(table)


@pytest.fixture
def config_pstf(synthetic_interp):
    return VisibilityPolterConfig(recomb_interp=synthetic_interp)


@pytest.fixture
def config_camb(synthetic_interp):
    return VisibilityPolterConfig(
        recomb_interp=synthetic_interp, use_camb_polter=True,
    )


@pytest.fixture
def planck_cosmology():
    return CosmologyForRecombination(
        h=0.6766, T_cmb=2.72548, Omega_b=0.0493, Y_He=0.245,
        Omega_m=0.3111, Omega_r=9.237e-5, Omega_Lambda=0.6889,
    )


@pytest.fixture
def reion_params():
    return ReionizationParameters(
        z_reion_H=7.67, delta_z_H=0.5,
        z_reion_HeII=3.5, delta_z_HeII=0.5, include_HeII=True,
    )


@pytest.fixture
def reion_extended_interp(synthetic_interp, reion_params, planck_cosmology):
    """R0 + W8-02 reion extension. Still R0 shape in recomb range."""
    extended_table = extend_table_with_reionization(
        synthetic_interp.table, reion_params,
        cosmology=planck_cosmology,
    )
    return build_interpolators(extended_table)


# ============================================================================
# R2 — Real HyRec-derived fixture (physics-calibrated tier)
# ============================================================================

_REAL_CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "recombination"
    / "fixtures"
    / "recombination_ref_planck2018.csv"
)


@pytest.fixture(scope="module")
def real_recombination_interp():
    """R2 fixture: HyRec-2 scalar history, Planck 2018-like cosmology.

    Module-scope cached — CSV parse + spline build happens once per
    test module. Produces a physically-calibrated visibility with
    peak at z ≈ 1088.8 and z*(κ=1) ≈ 1089.9.
    """
    if not _REAL_CSV_PATH.exists():
        pytest.skip(f"real HyRec CSV not staged at {_REAL_CSV_PATH}")
    table = load_recombination_table(_REAL_CSV_PATH)
    return build_interpolators(table)


@pytest.fixture(scope="module")
def real_config_pstf(real_recombination_interp):
    return VisibilityPolterConfig(recomb_interp=real_recombination_interp)


# ============================================================================
# 1. Config dataclass
# ============================================================================

class TestVisibilityPolterConfig:
    def test_frozen(self, config_pstf):
        with pytest.raises((AttributeError, Exception)):
            config_pstf.use_camb_polter = True

    def test_default_pstf_mode(self, config_pstf):
        assert config_pstf.use_camb_polter is False
        assert config_pstf.is_camb_mode is False

    def test_camb_mode_flag(self, config_camb):
        assert config_camb.use_camb_polter is True
        assert config_camb.is_camb_mode is True

    def test_rejects_non_bool_flag(self, synthetic_interp):
        with pytest.raises(TypeError):
            VisibilityPolterConfig(
                recomb_interp=synthetic_interp,
                use_camb_polter="yes",  # type: ignore[arg-type]
            )

    def test_rejects_nonfinite_normalization(self, synthetic_interp):
        with pytest.raises(ValueError):
            VisibilityPolterConfig(
                recomb_interp=synthetic_interp,
                polter_camb_normalization=float("inf"),
            )


# ============================================================================
# 2. Π path A — PSTF from (Θ_2, E_2)
# ============================================================================

class TestPiPSTF:
    def test_zero_inputs(self):
        assert pi_pstf(0.0, 0.0) == 0.0

    def test_matches_combined_source_pi(self):
        for theta, E in [(1.0, 0.0), (0.0, 1.0), (2.5, -0.7), (-1e-9, 3e-10)]:
            assert pi_pstf(theta, E) == combined_source_pi(theta, E)

    def test_linearity_in_theta(self):
        # Π is linear in Θ_2 at fixed E_2
        pi_a = pi_pstf(1.0, 0.5)
        pi_b = pi_pstf(3.0, 0.5)
        # Π(3, 0.5) - Π(1, 0.5) = 3 - 1 = 2 (linear in theta)
        np.testing.assert_allclose(pi_b - pi_a, 2.0, rtol=1e-14)


# ============================================================================
# 3. Π path B — subleading limit (5/2) Θ_2
# ============================================================================

class TestPiSubleadingLimit:
    def test_formula(self):
        for theta in [1.0, -3.7, 1e-9, -5e-12]:
            np.testing.assert_allclose(
                pi_subleading_limit(theta), 2.5 * theta, rtol=1e-14,
            )

    def test_sign_matches_theta2(self):
        assert pi_subleading_limit(1.0) > 0
        assert pi_subleading_limit(-1.0) < 0
        assert pi_subleading_limit(0.0) == 0.0

    def test_rejects_nonfinite(self):
        with pytest.raises(ValueError):
            pi_subleading_limit(float("nan"))


# ============================================================================
# 4. Π path D — closed form from sources
# ============================================================================

class TestPiClosedForm:
    def test_general_formula_reduces_at_subleading(self):
        # At S_E = 0, Π = (10 / (3 Γ_T)) S_T
        for S_T, gT in [(1.0, 1.0), (2.5, 0.3), (-1e-9, 2e-6)]:
            expected = (10.0 / (3.0 * gT)) * S_T
            actual = pi_closed_form_from_sources(S_T, 0.0, gT)
            np.testing.assert_allclose(actual, expected, rtol=1e-14)

    def test_pure_E_source_gives_minus_sqrt6_E2(self):
        # At Θ_2 = 0: S_T = (√6/10) Γ_T E_2, S_E = (2/5) Γ_T E_2
        # Closed form should give Π = -√6 E_2
        for E_2, gT in [(1.0, 1.0), (-0.5, 0.3), (3e-9, 2e-6)]:
            S_T = (SQRT6 / 10.0) * gT * E_2
            S_E = (2.0 / 5.0) * gT * E_2
            expected = -SQRT6 * E_2
            actual = pi_closed_form_from_sources(S_T, S_E, gT)
            np.testing.assert_allclose(actual, expected, rtol=1e-13)

    def test_rejects_nonpositive_gamma(self):
        with pytest.raises(ValueError):
            pi_closed_form_from_sources(1.0, 0.0, 0.0)
        with pytest.raises(ValueError):
            pi_closed_form_from_sources(1.0, 0.0, -0.1)


# ============================================================================
# 5. Π path C — TCA solve then combine
# ============================================================================

class TestPiFromTCASources:
    def test_matches_closed_form_at_general(self):
        d = _allowing_decision()
        for S_T, S_E, gT in [
            (1.0, 0.3, 1.0), (-2.5, 0.7, 0.5),
            (1e-9, -1e-10, 1e-6), (3e3, 2e2, 5.0),
        ]:
            pi_solve = pi_from_tca_sources(S_T, S_E, gT, decision=d)
            pi_closed = pi_closed_form_from_sources(S_T, S_E, gT)
            np.testing.assert_allclose(
                pi_solve, pi_closed, rtol=1e-12, atol=1e-15,
            )

    def test_zero_sources_give_zero_pi(self):
        d = _allowing_decision()
        assert pi_from_tca_sources(0.0, 0.0, 1.0, decision=d) == 0.0


# ============================================================================
# 6. Visibility-weighted Π (PSTF)
# ============================================================================

class TestGWeightedPiPSTF:
    def test_scalar_input(self, config_pstf):
        z = 1089.0
        theta_2, E_2 = 1.0, -0.5
        val = g_weighted_pi_pstf(z, theta_2, E_2, config_pstf)
        g = config_pstf.recomb_interp.query_visibility(z)
        pi = combined_source_pi(theta_2, E_2)
        np.testing.assert_allclose(val, g * pi, rtol=1e-14)

    def test_array_input(self, config_pstf):
        z_grid = np.linspace(900.0, 1300.0, 40)
        theta_arr = np.ones_like(z_grid) * 2.0
        E_arr = np.zeros_like(z_grid)
        result = g_weighted_pi_pstf(z_grid, theta_arr, E_arr, config_pstf)
        assert result.shape == z_grid.shape
        # Π = Θ_2 when E_2=0 ⇒ g·Π = 2·g
        g_vals = config_pstf.recomb_interp.query_visibility(z_grid)
        np.testing.assert_allclose(result, 2.0 * g_vals, rtol=1e-13)

    def test_zero_multipoles_give_zero(self, config_pstf):
        z_grid = np.linspace(900.0, 1300.0, 20)
        zeros = np.zeros_like(z_grid)
        result = g_weighted_pi_pstf(z_grid, zeros, zeros, config_pstf)
        np.testing.assert_array_equal(result, 0.0)

    def test_sign_tracks_pi(self, config_pstf):
        z = 1089.0
        # Θ_2 > 0, E_2 = 0 ⇒ Π > 0, g > 0 ⇒ product > 0
        pos = g_weighted_pi_pstf(z, 1.0, 0.0, config_pstf)
        neg = g_weighted_pi_pstf(z, -1.0, 0.0, config_pstf)
        assert pos > 0
        assert neg < 0

    def test_peak_in_synthetic_matches_analytic_root(self, config_pstf):
        """R0 self-consistency only. The synthetic fixture is NON-PHYSICAL;
        its peak is NOT at real recombination. The peak location follows
        from the fixture's own construction:

            d ln τ̇ / dz  =  dκ / dz
            2/(1+z_peak) ≈ 10⁻² · τ̇(z_peak)   (z >> z_transition ⇒ x_e→1)

        which places the synthetic peak near z ≈ 1361. This test asserts
        that the numeric peak the module finds agrees with the analytic
        root of the synthetic definition. For a physical peak near
        z ≈ 1089, see `TestRealRecombinationPhysics` (R2 tier).
        """
        z_peak, _ = gpi_peak_in_z(
            theta_2_of_z=lambda z: np.ones_like(z),
            E_2_of_z=lambda z: np.zeros_like(z),
            config=config_pstf,
            z_search_lo=500.0, z_search_hi=2500.0, n_samples=4000,
        )
        # Verify the analytic root of the synthetic profile
        # (lhs ~ rhs within ~5% due to x_e < 1 tail)
        interp = config_pstf.recomb_interp
        lhs = 2.0 / (1.0 + z_peak)
        rhs = 1.0e-2 * float(interp.query_tau_dot(z_peak))
        assert abs(lhs - rhs) / max(lhs, rhs) < 0.1, (lhs, rhs, z_peak)
        # Numeric synthetic peak location; bounded above z_transition=1089
        assert z_peak > 1089.0
        # And below 2×z_transition (sanity, prevents runaway)
        assert z_peak < 2180.0


# ============================================================================
# 7. CAMB polter co-evaluation
# ============================================================================

class TestCAMBPolterCoexistence:
    def test_polter_camb_re_export(self):
        for pig, E in [(1.0, 0.0), (0.0, 1.0), (2.5, -0.7)]:
            assert polter_camb_at(pig, E) == polter_camb(pig, E)

    def test_g_weighted_polter_camb_formula(self, config_camb):
        z = 1089.0
        pig, E_2 = 5.0, -1.0
        val = g_weighted_polter_camb(z, pig, E_2, config_camb)
        expected_polter = pig / 10.0 + 9.0 * E_2 / 15.0
        g = config_camb.recomb_interp.query_visibility(z)
        np.testing.assert_allclose(val, g * expected_polter, rtol=1e-14)

    def test_mode_switch_changes_output(self, config_pstf, config_camb):
        # Given same (pig ≡ Θ_2, E_2), PSTF and CAMB give different weights
        z_grid = np.array([1089.0])
        theta_arr = np.array([3.0])
        E_arr = np.array([1.0])
        pstf = g_weighted_pi_on_grid(
            z_grid, lambda z: theta_arr, lambda z: E_arr, config_pstf,
        )
        camb = g_weighted_pi_on_grid(
            z_grid, lambda z: theta_arr, lambda z: E_arr, config_camb,
        )
        # Should differ unless pig/10 + 9E/15 == Θ − √6 E coincidentally;
        # with these values the PSTF = 3 − √6 ≈ 0.551, CAMB = 3/10 + 9/15 = 0.9
        assert not np.isclose(pstf[0], camb[0], rtol=1e-3)


# ============================================================================
# 8. g·Π on grid with callables
# ============================================================================

class TestGPiOnGrid:
    def test_callable_inputs(self, config_pstf):
        z_grid = np.linspace(800.0, 1400.0, 50)
        result = g_weighted_pi_on_grid(
            z_grid,
            lambda z: np.full_like(z, 1.5),
            lambda z: np.zeros_like(z),
            config_pstf,
        )
        assert result.shape == z_grid.shape
        assert np.all(result > 0)

    def test_shape_mismatch_raises(self, config_pstf):
        z_grid = np.linspace(800.0, 1400.0, 10)
        with pytest.raises(ValueError):
            g_weighted_pi_on_grid(
                z_grid,
                lambda z: np.array([1.0]),  # wrong shape
                lambda z: np.zeros_like(z),
                config_pstf,
            )

    def test_camb_mode_through_on_grid(self, config_camb):
        z_grid = np.linspace(900.0, 1200.0, 30)
        result = g_weighted_pi_on_grid(
            z_grid,
            lambda z: np.full_like(z, 10.0),
            lambda z: np.full_like(z, 0.0),
            config_camb,
        )
        # CAMB polter with pig=10, E_2=0 → 10/10 = 1.0
        g_vals = config_camb.recomb_interp.query_visibility(z_grid)
        np.testing.assert_allclose(result, g_vals, rtol=1e-13)


# ============================================================================
# 9. Peak diagnostics
# ============================================================================

class TestGPiPeak:
    def test_constant_profile_peaks_at_g_peak(self, config_pstf):
        from bass.recombination.recombination_ingest import find_visibility_peak
        z_g_peak, _ = find_visibility_peak(config_pstf.recomb_interp)
        z_gpi_peak, _ = gpi_peak_in_z(
            theta_2_of_z=lambda z: np.ones_like(z),
            E_2_of_z=lambda z: np.zeros_like(z),
            config=config_pstf,
        )
        # For constant Π, gpi peak ≈ g peak within grid resolution
        assert abs(z_gpi_peak - z_g_peak) < 5.0

    def test_varying_profile_shifts_peak(self, config_pstf):
        # Profile that grows linearly with z biases the peak higher
        z_peak_flat, _ = gpi_peak_in_z(
            theta_2_of_z=lambda z: np.ones_like(z),
            E_2_of_z=lambda z: np.zeros_like(z),
            config=config_pstf,
        )
        z_peak_rising, _ = gpi_peak_in_z(
            theta_2_of_z=lambda z: z / 1000.0,  # rising with z
            E_2_of_z=lambda z: np.zeros_like(z),
            config=config_pstf,
        )
        assert z_peak_rising >= z_peak_flat  # peak cannot move lower

    def test_invalid_search_range(self, config_pstf):
        with pytest.raises(ValueError):
            gpi_peak_in_z(
                theta_2_of_z=lambda z: np.ones_like(z),
                E_2_of_z=lambda z: np.zeros_like(z),
                config=config_pstf,
                z_search_lo=1500.0, z_search_hi=1400.0,
            )


# ============================================================================
# 10. Trapezoidal integral in z-space
# ============================================================================

class TestGPiIntegral:
    def test_sign_preservation(self, config_pstf):
        z_grid = np.linspace(800.0, 1400.0, 400)
        theta_vals = np.ones_like(z_grid)
        E_vals = np.zeros_like(z_grid)
        val = gpi_integral_trap_in_z(z_grid, theta_vals, E_vals, config_pstf)
        assert val > 0
        # Flipping sign of Θ_2 flips the integral
        val_neg = gpi_integral_trap_in_z(
            z_grid, -theta_vals, E_vals, config_pstf,
        )
        np.testing.assert_allclose(val_neg, -val, rtol=1e-13)

    def test_shape_validation(self, config_pstf):
        z = np.linspace(800.0, 1400.0, 10)
        with pytest.raises(ValueError):
            gpi_integral_trap_in_z(z, np.ones(9), np.zeros(10), config_pstf)
        with pytest.raises(ValueError):
            gpi_integral_trap_in_z(
                np.array([1.0]), np.array([1.0]), np.array([0.0]),
                config_pstf,
            )

    def test_constant_profile_matches_trap_of_g(self, config_pstf):
        # ∫ g · 1 dz = ∫ g dz (since Π = 1 when Θ_2=1, E_2=0)
        z_grid = np.linspace(500.0, 2000.0, 1000)
        theta_vals = np.ones_like(z_grid)
        E_vals = np.zeros_like(z_grid)
        gpi_integral = gpi_integral_trap_in_z(
            z_grid, theta_vals, E_vals, config_pstf,
        )
        g_vals = config_pstf.recomb_interp.query_visibility(z_grid)
        direct_integral = np.trapezoid(g_vals, z_grid)
        np.testing.assert_allclose(
            gpi_integral, direct_integral, rtol=1e-13,
        )


# ============================================================================
# 11. Three-way cross-check at subleading (sanity)
# ============================================================================

class TestThreeWayAtSubleading:
    def test_residual_zero_at_various_theta(self):
        d = _allowing_decision()
        for theta, gT in [
            (1.0, 1.0), (-3.7e-9, 2.5e-6),
            (1e-12, 1e-14), (2.5, 0.5),
        ]:
            res = three_way_pi_residual_at_subleading(theta, gT, d)
            assert res["residual_max"] < 1e-14, res

    def test_sign_matches_theta(self):
        d = _allowing_decision()
        res_pos = three_way_pi_residual_at_subleading(1.0, 1.0, d)
        res_neg = three_way_pi_residual_at_subleading(-1.0, 1.0, d)
        assert res_pos["pi_A"] > 0
        assert res_neg["pi_A"] < 0

    def test_rejects_nonpositive_gamma(self):
        d = _allowing_decision()
        with pytest.raises(ValueError):
            three_way_pi_residual_at_subleading(1.0, 0.0, d)


# ============================================================================
# 12. Four-path genuine cross-check (general sources)
# ============================================================================

class TestFourPathCrossCheck:
    """The genuine cross-check: different numerical routes, same answer."""

    def test_machine_precision_at_unit_scale(self):
        d = _allowing_decision()
        for S_T, S_E, gT in [
            (1.0, 0.3, 1.0), (2.5, -0.7, 1.0),
            (0.1, 0.9, 2.0), (-1.5, 0.2, 0.5),
        ]:
            res = four_path_pi_residual_general(S_T, S_E, gT, d)
            # Relative to |Π|, residual must be at machine precision
            rel = res["residual_max"] / max(abs(res["pi_A"]), 1e-300)
            assert rel < 1e-13, res

    def test_machine_precision_at_physical_scale(self):
        d = _allowing_decision()
        # Realistic magnitudes from W7-02 packet (Θ_2 ~ 1e-9)
        for S_T, S_E, gT in [
            (1e-9 * 4.2e-6, 0.0, 4.2e-6),
            (3e-12 * 2e-5, -1e-13 * 2e-5, 2e-5),
            (-2.5e-9 * 1.5, 3.7e-11 * 1.5, 1.5),
        ]:
            res = four_path_pi_residual_general(S_T, S_E, gT, d)
            rel = res["residual_max"] / max(abs(res["pi_A"]), 1e-300)
            assert rel < 1e-12, res

    def test_extreme_magnitudes(self):
        d = _allowing_decision()
        # Large magnitudes accumulate ULPs more visibly but still machine-prec
        res = four_path_pi_residual_general(1e15, 1e13, 1e3, d)
        rel = res["residual_max"] / abs(res["pi_A"])
        assert rel < 1e-13, res

    def test_rejects_nonpositive_gamma(self):
        d = _allowing_decision()
        with pytest.raises(ValueError):
            four_path_pi_residual_general(1.0, 0.0, 0.0, d)


# ============================================================================
# 13. Physical sign assertions (v1.2 pattern)
# ============================================================================

class TestPhysicalSignAssertions:
    def test_visibility_positive_passes_on_synthetic(self, config_pstf):
        # Should not raise
        assert_visibility_positive(config_pstf, n_samples=200)

    def test_visibility_positive_raises_on_broken_interp(
        self, synthetic_interp,
    ):
        """A spline overshoot into negative territory must trigger the
        assertion. We force a strong negative entry (-1.0) so that the
        cubic-spline undershoot is deep enough to survive any sample
        grid alignment."""
        broken_table = make_synthetic_tanh_table(
            z_min=1.0, z_max=3000.0, n_points=100,
        )
        broken_table.tau_dot[50] = -1.0
        broken_interp = build_interpolators(broken_table)
        broken_config = VisibilityPolterConfig(recomb_interp=broken_interp)
        with pytest.raises(AssertionError):
            assert_visibility_positive(
                broken_config, n_samples=500, atol=1.0e-6,
            )

    def test_pi_sign_at_subleading(self):
        # Valid: Π sign tracks Θ_2
        assert_pi_sign_matches_theta2_at_subleading(1.0)
        assert_pi_sign_matches_theta2_at_subleading(-3.7e-9)
        assert_pi_sign_matches_theta2_at_subleading(0.0)  # early return

    def test_gpi_peak_assertion_on_synthetic_relaxed(self, config_pstf):
        """R0 sanity: with a wide tolerance, the physics-centred
        assertion still passes on the synthetic fixture because the
        synthetic peak (z ≈ 1361) falls within a ±300 tolerance window
        around z_expected=1089. This is a LOOSENED check; physics-
        range assertions use the R2 fixture."""
        assert_gpi_peak_near_last_scattering(
            config_pstf, z_expected=1089.0, z_tolerance=300.0,
        )

    def test_gpi_peak_assertion_fails_on_shifted(self, config_pstf):
        # Demand peak at 500 with small tolerance — must fail
        with pytest.raises(AssertionError):
            assert_gpi_peak_near_last_scattering(
                config_pstf, z_expected=500.0, z_tolerance=50.0,
            )


# ============================================================================
# 14. η(z) light utility (flat ΛCDM)
# ============================================================================

class TestEtaOfZLight:
    def test_lookback_at_zero_is_zero(self, planck_cosmology):
        eta_lb = conformal_lookback_at_z(0.0, planck_cosmology)
        assert eta_lb == 0.0 or abs(eta_lb) < 1e-10

    def test_conformal_time_today_positive_and_realistic(
        self, planck_cosmology,
    ):
        # Planck 2018 value ~14.2 Gpc comoving horizon
        eta_today = conformal_time_at_z(0.0, planck_cosmology, z_upper=1.0e4)
        # Sanity: 10 Gpc < η(0) < 20 Gpc = 10000..20000 Mpc
        assert 10_000.0 < eta_today < 20_000.0

    def test_lookback_monotone_in_z(self, planck_cosmology):
        z_vals = [0.1, 1.0, 10.0, 100.0, 1000.0]
        lookbacks = [
            conformal_lookback_at_z(z, planck_cosmology) for z in z_vals
        ]
        for i in range(len(lookbacks) - 1):
            assert lookbacks[i] < lookbacks[i + 1], (i, lookbacks)

    def test_rejects_z_above_upper(self, planck_cosmology):
        with pytest.raises(ValueError):
            conformal_time_at_z(1e5, planck_cosmology, z_upper=1e4)
        with pytest.raises(ValueError):
            conformal_lookback_at_z(-1.0, planck_cosmology)


# ============================================================================
# 15. Scope guards (deferred features)
# ============================================================================

class TestScopeGuards:
    def test_full_los_raises_scope(self):
        with pytest.raises(OutOfScopeError):
            full_los_integral()

    def test_isw_source_raises_scope(self):
        with pytest.raises(OutOfScopeError):
            isw_source()

    def test_doppler_source_raises_scope(self):
        with pytest.raises(OutOfScopeError):
            doppler_source()


# ============================================================================
# 16. Reionization behavior in g·Π
# ============================================================================

class TestReionizationFoldedIntoG:
    def test_reion_extended_g_has_low_z_bump(self, reion_extended_interp):
        # Without reion, g ≈ 0 at z~7; with reion there is a bump
        z_reion = np.linspace(3.0, 15.0, 100)
        g_reion = reion_extended_interp.query_visibility(z_reion)
        # Non-zero, positive, has a local maximum in range
        assert np.any(g_reion > 0)
        # Visibility bump magnitude: order τ̇_reion / Mpc ~ 1e-4
        assert np.max(g_reion) > 1e-7

    def test_gpi_near_recomb_largely_unchanged_by_reion_r2(
        self, real_recombination_interp, reion_params, planck_cosmology,
    ):
        """Reion-extended real fixture: g(z≈1089) is suppressed by
        e^{-τ_reion} ≈ 0.947 (Planck 2018 τ_reion = 0.054).

        Cross-fixture note. The equivalent synthetic+reion hybrid is
        arithmetically inconsistent: synthetic κ uses a non-physical
        10⁻² scale factor while the reion extender integrates with
        c/((1+z)H). Mixing the two double-counts. The physics check
        therefore uses the R2 fixture exclusively.
        """
        # Baseline config from real fixture
        config_noreion = VisibilityPolterConfig(
            recomb_interp=real_recombination_interp,
        )
        # Extend with reion on real fixture (self-consistent)
        ext_table = extend_table_with_reionization(
            real_recombination_interp.table, reion_params,
            cosmology=planck_cosmology,
        )
        ext_interp = build_interpolators(ext_table)
        config_reion = VisibilityPolterConfig(recomb_interp=ext_interp)

        z = 1089.0
        val_no = g_weighted_pi_pstf(z, 1.0, 0.0, config_noreion)
        val_yes = g_weighted_pi_pstf(z, 1.0, 0.0, config_reion)
        assert val_no > 0 and val_yes > 0
        # Reion suppression factor ≈ e^{-τ_reion} ≈ 0.947
        ratio = val_yes / val_no
        assert 0.85 < ratio < 1.0, ratio


# ============================================================================
# 17. R2 real-physics recombination checks (HyRec-2 CSV fixture)
# ============================================================================

class TestRealRecombinationPhysics:
    """Physics-calibrated tier. z_peak and z_*(κ=1) are the observable
    tests; agreement with Planck 2018 is the spec."""

    def test_real_visibility_positive(self, real_config_pstf):
        assert_visibility_positive(real_config_pstf, n_samples=500)

    def test_real_g_peak_at_last_scattering(self, real_recombination_interp):
        """Peak of g(z) must sit in z ∈ (1080, 1100), matching Planck 2018
        z_* = 1089.95 ± 0.27 within narrow tolerance."""
        from bass.recombination.recombination_ingest import (
            find_visibility_peak,
        )
        z_peak, _ = find_visibility_peak(
            real_recombination_interp,
            z_search_lo=800.0, z_search_hi=1400.0, n_samples=4000,
        )
        assert 1080.0 < z_peak < 1100.0, z_peak

    def test_real_z_star_matches_planck_within_1pct(
        self, real_recombination_interp,
    ):
        """z_*(κ=1) must land in the Planck 2018 1σ band when measured
        on the CSV-backed scalar history."""
        from bass.recombination.recombination_ingest import (
            find_last_scattering_redshift,
        )
        z_star = find_last_scattering_redshift(
            real_recombination_interp, target_kappa=1.0,
        )
        # Planck 2018: z_* = 1089.95 ± 0.27
        assert 1089.0 < z_star < 1091.0, z_star

    def test_real_gpi_peak_tracks_g_peak_for_constant_profile(
        self, real_config_pstf,
    ):
        """With constant (Θ_2=1, E_2=0), g·Π peak must coincide with
        the g peak (up to grid resolution)."""
        from bass.recombination.recombination_ingest import (
            find_visibility_peak,
        )
        z_g_peak, _ = find_visibility_peak(
            real_config_pstf.recomb_interp,
            z_search_lo=800.0, z_search_hi=1400.0, n_samples=4000,
        )
        z_gpi_peak, _ = gpi_peak_in_z(
            theta_2_of_z=lambda z: np.ones_like(z),
            E_2_of_z=lambda z: np.zeros_like(z),
            config=real_config_pstf,
            z_search_lo=800.0, z_search_hi=1400.0, n_samples=4000,
        )
        assert abs(z_gpi_peak - z_g_peak) < 1.0, (z_gpi_peak, z_g_peak)

    def test_real_gpi_peak_assertion_passes(self, real_config_pstf):
        """The module-level physics assertion must pass on the R2
        fixture with a tight tolerance (50)."""
        assert_gpi_peak_near_last_scattering(
            real_config_pstf, z_expected=1089.0, z_tolerance=50.0,
        )

    def test_real_gpi_sign_at_peak(self, real_config_pstf):
        z_star = 1089.0
        # Positive Θ_2 with E_2=0: g·Π > 0 (since Π=Θ_2 and g>0)
        pos = g_weighted_pi_pstf(z_star, 1.0, 0.0, real_config_pstf)
        neg = g_weighted_pi_pstf(z_star, -1.0, 0.0, real_config_pstf)
        assert pos > 0
        assert neg < 0
        np.testing.assert_allclose(pos, -neg, rtol=1e-13)

    def test_real_gpi_integral_positive(self, real_config_pstf):
        """∫ g·Π dz over the recombination window with constant Θ_2=1
        must be positive and of order (g_peak × width)."""
        z_grid = np.linspace(900.0, 1300.0, 500)
        theta_vals = np.ones_like(z_grid)
        E_vals = np.zeros_like(z_grid)
        val = gpi_integral_trap_in_z(
            z_grid, theta_vals, E_vals, real_config_pstf,
        )
        assert val > 0
        # Plausibility: width ~100 × g_peak ~ 2e-2 gives ~ few×1e0
        assert 0.1 < val < 100.0, val

    def test_real_gpi_peak_shifts_with_reion(
        self, real_recombination_interp, planck_cosmology, reion_params,
    ):
        """Adding reionization does not shift the recombination-era
        peak by more than 10 (z* moves ≲ 5 per handoff §3.1)."""
        from bass.recombination.recombination_ingest import (
            find_visibility_peak,
        )
        # Baseline (no reion)
        z_peak_0, _ = find_visibility_peak(
            real_recombination_interp,
            z_search_lo=800.0, z_search_hi=1400.0, n_samples=4000,
        )
        # Extend with reion
        extended = extend_table_with_reionization(
            real_recombination_interp.table, reion_params,
            cosmology=planck_cosmology,
        )
        extended_interp = build_interpolators(extended)
        z_peak_reion, _ = find_visibility_peak(
            extended_interp,
            z_search_lo=800.0, z_search_hi=1400.0, n_samples=4000,
        )
        # Shift must be modest (<10, handoff reports ~5)
        assert abs(z_peak_reion - z_peak_0) < 10.0


# ============================================================================
# 17. Runtime gating smoke test (W3 surface)
# ============================================================================

class TestW3Surface:
    def test_explicit_decision_accepted(self):
        d = _allowing_decision()
        pi = pi_from_tca_sources(1.0, 0.0, 1.0, decision=d)
        np.testing.assert_allclose(pi, 10.0 / 3.0, rtol=1e-13)

    def test_two_allowing_decisions_give_same_result(self):
        # Factory-built allowing decisions are deterministic
        d1 = _allowing_decision()
        d2 = _allowing_decision()
        pi1 = pi_from_tca_sources(1.0, 0.0, 1.0, decision=d1)
        pi2 = pi_from_tca_sources(1.0, 0.0, 1.0, decision=d2)
        np.testing.assert_allclose(pi1, pi2, rtol=1e-15)

    def test_blocking_decision_raises(self):
        d = _blocking_decision()
        with pytest.raises(CanonicalBlockError):
            pi_from_tca_sources(1.0, 0.0, 1.0, decision=d)
