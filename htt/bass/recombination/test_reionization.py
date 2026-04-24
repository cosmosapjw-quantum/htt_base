"""
Test suite: bass/recombination/reionization.py  (Week 8-02)
============================================================

Test classes:
  1. TestCosmologyForRecombination   — container invariants, derived fields
  2. TestCosmologyFromMetadata       — metadata extraction
  3. TestReionizationParameters      — container, defaults, validation
  4. TestYAndDeltaY                  — y(z), Δy conversion helpers
  5. TestTanhReionizationXe          — tanh formula, asymptotic limits
  6. TestHeIIReionization            — optional HeII toggle
  7. TestComputeTauDotConformal      — τ̇ formula
  8. TestComputeKappaFromTauDot      — κ trapezoidal integration
  9. TestExtendTableWithReionization — full extension pipeline
 10. TestComputeReionizationTau      — **Planck τ ≈ 0.054 validation**
 11. TestPhysicalSignAssertions      — v1.2 pattern (continued)
 12. TestPlanck2018Consistency       — **production reference validation**
 13. TestAsymptoticLimitHelper       — diagnostics helper
"""
from __future__ import annotations

import math
import numpy as np
import pytest
from pathlib import Path

from bass.recombination.recombination_ingest import (
    RecombinationTable,
    load_recombination_table,
    validate_recombination_table,
)
from bass.recombination.reionization import (
    CosmologyForRecombination,
    H_100,
    ReionizationParameters,
    SEC_PER_MPC,
    compute_kappa_from_tau_dot,
    compute_reionization_tau,
    compute_tau_dot_conformal_Mpc,
    cosmology_from_metadata,
    extend_table_with_reionization,
    tanh_reionization_xe,
    xe_asymptotic_limits,
)


# ============================================================================
# Fixtures
# ============================================================================

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_HYREC_CSV = FIXTURE_DIR / "recombination_ref_planck2018.csv"


# Planck 2018-like cosmology for tests
def _planck_cosmology() -> CosmologyForRecombination:
    return CosmologyForRecombination(
        h=0.6735837,
        T_cmb=2.72548,
        Omega_b=0.04941,
        Y_He=0.245,
        Omega_m=0.313841,
        Omega_r=9.220339e-05,
        Omega_Lambda=0.686067,
    )


# ============================================================================
# 1. TestCosmologyForRecombination
# ============================================================================

class TestCosmologyForRecombination:

    def test_basic_construction(self):
        c = _planck_cosmology()
        assert abs(c.h - 0.6735837) < 1e-10
        assert abs(c.T_cmb - 2.72548) < 1e-10

    def test_H_0_SI(self):
        c = _planck_cosmology()
        expected = 0.6735837 * H_100
        assert abs(c.H_0_SI - expected) < 1e-20

    def test_f_He_derived(self):
        # f_He = Y_He / (4(1-Y_He)) = 0.245 / (4 × 0.755) ≈ 0.0811
        c = _planck_cosmology()
        expected = 0.245 / (4.0 * (1.0 - 0.245))
        assert abs(c.f_He - expected) < 1e-10
        assert 0.08 < c.f_He < 0.09

    def test_n_H_today(self):
        c = _planck_cosmology()
        # Expected n_H(0) ≈ 0.19 m⁻³ for Planck 2018 (well-known value)
        assert 0.18 < c.n_H_today < 0.20

    def test_H_of_z_monotonic(self):
        c = _planck_cosmology()
        z = np.linspace(0.0, 10.0, 20)
        H = c.H_of_z(z)
        assert np.all(np.diff(H) > 0)  # H(z) increases with z

    def test_H_of_z_matches_H0_at_z0(self):
        c = _planck_cosmology()
        H0_computed = c.H_of_z(0.0)
        # sqrt() precision limit is ~machine_eps × H_0 ≈ 1e-23 for H_0 ~ 1e-18
        assert abs(H0_computed - c.H_0_SI) < 1e-22

    def test_rejects_invalid_h(self):
        with pytest.raises(ValueError, match="h"):
            CosmologyForRecombination(
                h=-0.5, T_cmb=2.7, Omega_b=0.05, Y_He=0.25,
                Omega_m=0.3, Omega_r=1e-4, Omega_Lambda=0.7,
            )


# ============================================================================
# 2. TestCosmologyFromMetadata
# ============================================================================

class TestCosmologyFromMetadata:

    def test_basic_extraction(self):
        md = {
            "h": "0.6735837",
            "t_cmb": "2.72548 K",  # with unit suffix
            "omega_b": "0.04941",
            "y_he": "0.245",
            "omega_m_total": "0.313841",
            "omega_r_total": "9.22e-5",
            "omega_lambda": "0.686067",
        }
        c = cosmology_from_metadata(md)
        assert abs(c.h - 0.6735837) < 1e-10
        assert abs(c.T_cmb - 2.72548) < 1e-10  # unit suffix stripped
        assert abs(c.Omega_b - 0.04941) < 1e-10

    def test_missing_key_raises(self):
        md = {
            "h": "0.67",  # missing others
        }
        with pytest.raises(KeyError, match="missing required keys"):
            cosmology_from_metadata(md)

    def test_bad_value_raises(self):
        md = {
            "h": "not_a_number",
            "t_cmb": "2.72548",
            "omega_b": "0.04941",
            "y_he": "0.245",
            "omega_m_total": "0.3",
            "omega_r_total": "1e-4",
            "omega_lambda": "0.7",
        }
        with pytest.raises(ValueError, match="not parseable"):
            cosmology_from_metadata(md)


# ============================================================================
# 3. TestReionizationParameters
# ============================================================================

class TestReionizationParameters:

    def test_default_is_planck_2018(self):
        r = ReionizationParameters()
        assert r.z_reion_H == 7.67
        assert r.delta_z_H == 0.5
        assert r.z_reion_HeII == 3.5
        assert r.delta_z_HeII == 0.5
        assert r.include_HeII is True

    def test_rejects_negative_z_reion(self):
        with pytest.raises(ValueError, match="z_reion_H"):
            ReionizationParameters(z_reion_H=-1.0)

    def test_rejects_zero_delta_z(self):
        with pytest.raises(ValueError, match="delta_z_H"):
            ReionizationParameters(delta_z_H=0.0)

    def test_HeII_validation_only_when_enabled(self):
        # When include_HeII=False, z_reion_HeII can be anything
        r = ReionizationParameters(
            z_reion_HeII=-1.0, include_HeII=False,
        )
        assert r.z_reion_HeII == -1.0

    def test_HeII_validated_when_enabled(self):
        with pytest.raises(ValueError, match="z_reion_HeII"):
            ReionizationParameters(
                z_reion_HeII=-1.0, include_HeII=True,
            )


# ============================================================================
# 5. TestTanhReionizationXe
# ============================================================================

class TestTanhReionizationXe:

    def test_high_z_limit_zero(self):
        # At z >> z_reion_H, x_e_rei → 0 (no reionization yet)
        r = ReionizationParameters()
        f_He = 0.0811
        x_e = tanh_reionization_xe(100.0, r, f_He)
        assert abs(x_e) < 1e-50  # tanh saturates

    def test_low_z_limit_full(self):
        # At z = 0 (after both reionizations), x_e_rei → 1 + 2 f_He
        # Residual ~O(1e-6) because z=0 is not infinitely far below
        # z_rei_HeII = 3.5 — tanh has not fully saturated.
        r = ReionizationParameters()
        f_He = 0.0811
        x_e = tanh_reionization_xe(0.0, r, f_He)
        expected = 1.0 + 2.0 * f_He
        assert abs(x_e - expected) < 1e-4

    def test_between_reionizations(self):
        # At 3.5 < z < 7.67, only H+HeI done: x_e_rei → 1 + f_He
        r = ReionizationParameters()
        f_He = 0.0811
        x_e = tanh_reionization_xe(5.5, r, f_He)
        expected = 1.0 + f_He
        # Allow some tolerance because 5.5 is near the HeII transition edge
        assert abs(x_e - expected) < 0.05

    def test_midpoint_is_half_amplitude(self):
        # At z = z_reion_H exactly, x_e_rei ≈ (1 + f_He)/2
        # (because tanh(0) = 0 at the midpoint of the H bump)
        r = ReionizationParameters(include_HeII=False)
        f_He = 0.0811
        x_e = tanh_reionization_xe(r.z_reion_H, r, f_He)
        expected = 0.5 * (1.0 + f_He)
        assert abs(x_e - expected) < 1e-10

    def test_scalar_input_returns_scalar(self):
        r = ReionizationParameters()
        x_e = tanh_reionization_xe(5.0, r, 0.08)
        assert isinstance(x_e, float)

    def test_array_input_returns_array(self):
        r = ReionizationParameters()
        z = np.array([0.0, 5.0, 10.0, 100.0])
        x_e = tanh_reionization_xe(z, r, 0.08)
        assert isinstance(x_e, np.ndarray)
        assert x_e.shape == (4,)

    def test_monotonic_in_z(self):
        # x_e_rei is monotonically DECREASING in z (more reionized at low z)
        r = ReionizationParameters()
        z = np.linspace(0.0, 20.0, 200)
        x_e = tanh_reionization_xe(z, r, 0.08)
        assert np.all(np.diff(x_e) <= 1e-14)


# ============================================================================
# 6. TestHeIIReionization
# ============================================================================

class TestHeIIReionization:

    def test_HeII_off_gives_smaller_low_z_plateau(self):
        # With HeII off: low-z plateau = 1 + f_He
        # Residual ~O(1e-6) at z=0 (tanh not fully saturated at 3.5 away)
        r_off = ReionizationParameters(include_HeII=False)
        r_on = ReionizationParameters(include_HeII=True)
        f_He = 0.0811
        x_e_off = tanh_reionization_xe(0.0, r_off, f_He)
        x_e_on = tanh_reionization_xe(0.0, r_on, f_He)
        assert x_e_off < x_e_on
        # Difference should equal f_He (HeII contribution at saturation)
        assert abs((x_e_on - x_e_off) - f_He) < 1e-4

    def test_between_bumps_HeII_off_and_on_match(self):
        # Between z_HeII (3.5) and z_H (7.67), only H-bump active.
        # HeII contribution ≈ 0 at z=5.5 regardless of include_HeII flag.
        r_off = ReionizationParameters(include_HeII=False)
        r_on = ReionizationParameters(include_HeII=True)
        f_He = 0.0811
        # At z=6.0 (above HeII midpoint by ~2.5), HeII contribution tiny
        x_e_off = tanh_reionization_xe(6.0, r_off, f_He)
        x_e_on = tanh_reionization_xe(6.0, r_on, f_He)
        # HeII contribution exponentially small at z >> z_rei_HeII
        assert abs(x_e_on - x_e_off) < 0.01

    def test_HeII_midpoint_behavior(self):
        # At z=z_rei_HeII, only HeII bump is at its midpoint;
        # H bump has saturated (fully done)
        r = ReionizationParameters(include_HeII=True)
        f_He = 0.0811
        x_e = tanh_reionization_xe(r.z_reion_HeII, r, f_He)
        # Expected: full H contribution + half HeII
        expected = (1.0 + f_He) + 0.5 * f_He
        assert abs(x_e - expected) < 1e-4


# ============================================================================
# 7. TestComputeTauDotConformal
# ============================================================================

class TestComputeTauDotConformal:

    def test_basic_magnitude_at_z_1100(self):
        # x_e ≈ 0.145 at z=1100, check τ̇ is ~0.07 /Mpc (CAMB reference)
        c = _planck_cosmology()
        z = np.array([1100.0])
        x_e = np.array([0.145])
        tau = compute_tau_dot_conformal_Mpc(z, x_e, c)
        assert 0.05 < tau[0] < 0.10  # CAMB range

    def test_zero_xe_gives_zero_tau(self):
        c = _planck_cosmology()
        z = np.linspace(1.0, 1000.0, 100)
        x_e = np.zeros_like(z)
        tau = compute_tau_dot_conformal_Mpc(z, x_e, c)
        assert np.all(tau == 0.0)

    def test_linearity_in_xe(self):
        c = _planck_cosmology()
        z = np.array([100.0])
        tau1 = compute_tau_dot_conformal_Mpc(z, np.array([1.0]), c)
        tau2 = compute_tau_dot_conformal_Mpc(z, np.array([2.0]), c)
        assert abs(tau2[0] / tau1[0] - 2.0) < 1e-10


# ============================================================================
# 8. TestComputeKappaFromTauDot
# ============================================================================

class TestComputeKappaFromTauDot:

    def test_zero_tau_dot_zero_kappa(self):
        c = _planck_cosmology()
        z = np.linspace(0.0, 100.0, 50)
        tau_dot = np.zeros_like(z)
        kappa = compute_kappa_from_tau_dot(z, tau_dot, c)
        assert np.all(kappa == 0.0)

    def test_kappa_starts_at_zero(self):
        c = _planck_cosmology()
        z = np.linspace(0.0, 100.0, 50)
        tau_dot = np.ones_like(z) * 0.01
        kappa = compute_kappa_from_tau_dot(z, tau_dot, c)
        assert kappa[0] == 0.0

    def test_kappa_monotonic_for_positive_tau(self):
        c = _planck_cosmology()
        z = np.linspace(0.0, 100.0, 50)
        tau_dot = np.ones_like(z) * 0.01
        kappa = compute_kappa_from_tau_dot(z, tau_dot, c)
        assert np.all(np.diff(kappa) >= 0)


# ============================================================================
# 9. TestExtendTableWithReionization
# ============================================================================

class TestExtendTableWithReionization:

    def _load_real_table(self):
        if not REAL_HYREC_CSV.exists():
            pytest.skip("real HyRec CSV not found")
        return load_recombination_table(REAL_HYREC_CSV)

    def test_returns_valid_extended_table(self):
        tab = self._load_real_table()
        r = ReionizationParameters()
        ext = extend_table_with_reionization(tab, r)
        errors = validate_recombination_table(ext)
        assert errors == []

    def test_extended_z_grid_starts_at_zero(self):
        tab = self._load_real_table()
        r = ReionizationParameters()
        ext = extend_table_with_reionization(tab, r, z_low=0.0)
        assert ext.z_min == 0.0

    def test_xe_plateau_at_low_z(self):
        # At z=0.5 (below z_reion_HeII), x_e should be ~ 1 + 2 f_He
        tab = self._load_real_table()
        c = cosmology_from_metadata(tab.metadata)
        r = ReionizationParameters()
        ext = extend_table_with_reionization(tab, r)
        # Find nearest grid point to z=0.5
        idx = int(np.argmin(np.abs(ext.z - 0.5)))
        # Allow slack: 1.08 to 1.20 range captures x_e_recomb freeze-out
        # (~2e-4) plus full reion
        assert 1.10 < ext.x_e[idx] < 1.20

    def test_xe_high_z_unchanged(self):
        # At z=5000 (deep in recomb era), x_e should be unchanged
        # from the original recomb table (reion contribution ≈ 0)
        tab = self._load_real_table()
        r = ReionizationParameters()
        ext = extend_table_with_reionization(tab, r)
        idx_original = int(np.argmin(np.abs(tab.z - 5000.0)))
        idx_ext = int(np.argmin(np.abs(ext.z - 5000.0)))
        assert abs(
            ext.x_e[idx_ext] - tab.x_e[idx_original]
        ) < 1e-10

    def test_auto_cosmology_extraction_from_metadata(self):
        # No explicit cosmology: function should extract from metadata
        tab = self._load_real_table()
        r = ReionizationParameters()
        ext = extend_table_with_reionization(
            tab, r, cosmology=None,
        )
        # Extended table has annotated metadata
        assert "reionization" in ext.metadata
        assert ext.metadata["reionization"] == "tanh"


# ============================================================================
# 10. TestComputeReionizationTau
# ============================================================================

class TestComputeReionizationTau:
    """Critical validation: τ_reion ≈ 0.054 (Planck 2018 reference)."""

    def _build_planck_table(self):
        if not REAL_HYREC_CSV.exists():
            pytest.skip("real HyRec CSV not found")
        tab = load_recombination_table(REAL_HYREC_CSV)
        r = ReionizationParameters()  # Planck 2018 default
        return extend_table_with_reionization(tab, r)

    def test_tau_reion_matches_planck_2018(self):
        # Planck 2018 reference: τ = 0.054 ± 0.007
        # CAMB default parameterization gives τ ≈ 0.054 with these inputs
        ext = self._build_planck_table()
        tau = compute_reionization_tau(ext, z_high_cutoff=30.0)
        assert 0.045 < tau < 0.065  # within ~1.5σ of Planck central

    def test_tau_is_finite_and_positive(self):
        ext = self._build_planck_table()
        tau = compute_reionization_tau(ext)
        assert tau > 0.0
        assert np.isfinite(tau)

    def test_cutoff_out_of_range_raises(self):
        ext = self._build_planck_table()
        with pytest.raises(ValueError, match="z_high_cutoff"):
            compute_reionization_tau(ext, z_high_cutoff=1e10)
        with pytest.raises(ValueError, match="z_high_cutoff"):
            compute_reionization_tau(ext, z_high_cutoff=-1.0)


# ============================================================================
# 11. TestPhysicalSignAssertions — v1.2 pattern
# ============================================================================

class TestPhysicalSignAssertions:

    def test_xe_reion_non_negative(self):
        r = ReionizationParameters()
        z = np.linspace(0.0, 50.0, 500)
        x_e = tanh_reionization_xe(z, r, 0.08)
        assert np.all(x_e >= 0.0)

    def test_xe_reion_bounded_above(self):
        # x_e_rei ≤ 1 + 2 f_He (full plateau, both reionizations)
        r = ReionizationParameters()
        f_He = 0.0811
        z = np.linspace(0.0, 50.0, 500)
        x_e = tanh_reionization_xe(z, r, f_He)
        assert np.all(x_e <= 1.0 + 2.0 * f_He + 1e-10)

    def test_tau_reion_positive(self):
        # τ_reion > 0 (always, for any positive x_e_rei)
        if not REAL_HYREC_CSV.exists():
            pytest.skip("real HyRec CSV not found")
        tab = load_recombination_table(REAL_HYREC_CSV)
        r = ReionizationParameters()
        ext = extend_table_with_reionization(tab, r)
        tau = compute_reionization_tau(ext)
        assert tau > 0.0

    def test_larger_z_reion_gives_larger_tau(self):
        # Higher z_reion → more reionization time → larger τ
        if not REAL_HYREC_CSV.exists():
            pytest.skip("real HyRec CSV not found")
        tab = load_recombination_table(REAL_HYREC_CSV)
        r_low = ReionizationParameters(z_reion_H=6.0)
        r_high = ReionizationParameters(z_reion_H=9.0)
        ext_low = extend_table_with_reionization(tab, r_low)
        ext_high = extend_table_with_reionization(tab, r_high)
        tau_low = compute_reionization_tau(ext_low)
        tau_high = compute_reionization_tau(ext_high)
        assert tau_high > tau_low


# ============================================================================
# 12. TestPlanck2018Consistency — production reference
# ============================================================================

@pytest.mark.skipif(
    not REAL_HYREC_CSV.exists(),
    reason="real HyRec CSV not found",
)
class TestPlanck2018Consistency:

    def test_z_star_still_near_1090_with_reionization(self):
        # Adding reionization (τ ≈ 0.054) means κ = 1 is reached slightly
        # EARLIER (lower z) than without reion, because ~5% of optical
        # depth is pre-built at low z. With default z_rei_H=7.67,
        # z_* shifts down by ~5 from 1090 → ≈ 1085.
        from bass.recombination.recombination_ingest import (
            build_interpolators, find_last_scattering_redshift,
        )
        tab = load_recombination_table(REAL_HYREC_CSV)
        r = ReionizationParameters()
        ext = extend_table_with_reionization(tab, r)
        interp = build_interpolators(ext)
        z_star = find_last_scattering_redshift(interp, target_kappa=1.0)
        # Physical range after reion correction
        assert 1082.0 < z_star < 1088.0

    def test_total_kappa_at_z_max_much_larger_than_reion(self):
        # κ(z_max) with reion >> κ_reion, since recombination dominates
        tab = load_recombination_table(REAL_HYREC_CSV)
        r = ReionizationParameters()
        ext = extend_table_with_reionization(tab, r)
        tau_reion = compute_reionization_tau(ext)
        kappa_max = ext.kappa[-1]
        # κ_max should be hundreds (deep ionized era)
        assert kappa_max > 100.0
        # And much larger than τ_reion (~0.054)
        assert kappa_max > 100 * tau_reion


# ============================================================================
# 13. TestAsymptoticLimitHelper
# ============================================================================

class TestAsymptoticLimitHelper:

    def test_limits_with_HeII(self):
        r = ReionizationParameters(include_HeII=True)
        limits = xe_asymptotic_limits(r, f_He=0.0811)
        assert limits["high_z"] == 0.0
        assert abs(limits["between"] - 1.0811) < 1e-10
        assert abs(limits["low_z"] - 1.1622) < 1e-10

    def test_limits_without_HeII(self):
        r = ReionizationParameters(include_HeII=False)
        limits = xe_asymptotic_limits(r, f_He=0.0811)
        # Without HeII, low_z plateau = 1 + f_He
        assert abs(limits["low_z"] - 1.0811) < 1e-10
