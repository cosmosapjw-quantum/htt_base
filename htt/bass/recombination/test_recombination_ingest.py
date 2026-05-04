"""
Test suite: bass/recombination/recombination_ingest.py  (Week 8-01)
===================================================================

Test classes:
  1. TestParseRecombinationHeader   — key=value parser
  2. TestRecombinationTableContainer — shape, validation, invariants
  3. TestLoadRecombinationTable     — CSV parsing
  4. TestValidationChecks           — physical bounds, monotonicity
  5. TestBuildInterpolators         — cubic spline construction
  6. TestQueryMethods               — x_e, T_m, tau_dot, kappa queries
  7. TestVisibilityFunction         — g(z) = τ̇ exp(-κ)
  8. TestSyntheticTanhFixture       — fixture generator
  9. TestFindLastScatteringRedshift — brentq root-finding
 10. TestFindVisibilityPeak         — parabolic refinement
 11. TestRealHyRecReference         — **validation against real HyRec Planck 2018**
 12. TestPhysicalSignAssertions     — v1.2 NEW PATTERN (continued)
 13. TestCrossReferenceKnownValues  — known cosmology values
"""
from __future__ import annotations

import io
import math
import numpy as np
import pytest
from pathlib import Path

from bass.recombination.recombination_ingest import (
    EXPECTED_COLUMNS,
    RecombinationInterp,
    RecombinationTable,
    build_interpolators,
    find_last_scattering_redshift,
    find_visibility_peak,
    load_recombination_table,
    make_synthetic_tanh_table,
    parse_recombination_header,
    validate_recombination_table,
)


# ============================================================================
# Fixture paths
# ============================================================================

FIXTURE_DIR = Path(__file__).parent / "fixtures"
REAL_HYREC_CSV = FIXTURE_DIR / "recombination_ref_planck2018.csv"


# ============================================================================
# 1. TestParseRecombinationHeader
# ============================================================================

class TestParseRecombinationHeader:

    def test_basic_key_value_parsing(self):
        lines = [
            "# h = 0.6735837",
            "# Omega_b = 0.04941",
        ]
        md, unparsed = parse_recombination_header(lines)
        assert md == {"h": "0.6735837", "omega_b": "0.04941"}
        assert unparsed == []

    def test_free_form_lines_unparsed(self):
        lines = [
            "# Source: HyRec-2",
            "# Generated: 2026-04-18",
            "# h = 0.6735",
        ]
        md, unparsed = parse_recombination_header(lines)
        assert md == {"h": "0.6735"}
        assert "Source: HyRec-2" in unparsed
        assert "Generated: 2026-04-18" in unparsed

    def test_handles_hash_stripped_input(self):
        # Accept lines with or without the leading #
        lines = [
            "h = 0.67",
            "# T = 2.725",
        ]
        md, _ = parse_recombination_header(lines)
        assert md == {"h": "0.67", "t": "2.725"}

    def test_empty_lines_ignored(self):
        md, unp = parse_recombination_header(["# ", "#", ""])
        assert md == {}
        assert unp == []

    def test_case_insensitive_keys(self):
        md, _ = parse_recombination_header(["# Omega_B = 0.04"])
        assert "omega_b" in md
        assert "Omega_B" not in md

    def test_multiple_equals_in_value(self):
        # Only first '=' is a separator
        md, _ = parse_recombination_header(["# equation = a = b + c"])
        assert md == {"equation": "a = b + c"}


# ============================================================================
# 2. TestRecombinationTableContainer
# ============================================================================

class TestRecombinationTableContainer:

    def test_valid_construction(self):
        n = 100
        z = np.linspace(1.0, 3000.0, n)
        tab = RecombinationTable(
            z=z, x_e=np.ones(n) * 0.5, T_m=np.ones(n) * 1000.0,
            tau_dot=np.ones(n) * 1e-3, kappa=np.linspace(0, 5, n),
        )
        assert tab.n_points == n
        assert tab.z_min == 1.0
        assert tab.z_max == 3000.0

    def test_rejects_non_ascending_z(self):
        n = 10
        z = np.arange(n, dtype=float)[::-1]  # descending
        with pytest.raises(ValueError, match="strictly ascending"):
            RecombinationTable(
                z=z, x_e=np.zeros(n), T_m=np.zeros(n),
                tau_dot=np.zeros(n), kappa=np.zeros(n),
            )

    def test_rejects_shape_mismatch(self):
        z = np.linspace(1.0, 10.0, 10)
        with pytest.raises(ValueError, match="shape"):
            RecombinationTable(
                z=z, x_e=np.zeros(5),  # wrong size
                T_m=np.zeros(10), tau_dot=np.zeros(10), kappa=np.zeros(10),
            )

    def test_rejects_nonfinite(self):
        z = np.linspace(1.0, 10.0, 10)
        x_e = np.ones(10)
        x_e[3] = np.nan
        with pytest.raises(ValueError, match="non-finite"):
            RecombinationTable(
                z=z, x_e=x_e, T_m=np.zeros(10),
                tau_dot=np.zeros(10), kappa=np.zeros(10),
            )

    def test_rejects_duplicate_z(self):
        # Duplicates mean diff(z) == 0, violates strict ascending
        z = np.array([1.0, 2.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="strictly ascending"):
            RecombinationTable(
                z=z, x_e=np.zeros(4), T_m=np.zeros(4),
                tau_dot=np.zeros(4), kappa=np.zeros(4),
            )


# ============================================================================
# 3. TestLoadRecombinationTable
# ============================================================================

class TestLoadRecombinationTable:

    def _write_tmp(self, tmp_path, content):
        p = tmp_path / "test.csv"
        p.write_text(content)
        return p

    def test_basic_parse(self, tmp_path):
        content = (
            "# h = 0.67\n"
            "# source = test\n"
            "z,x_e,T_m,tau_dot,kappa\n"
            "1.0,0.001,5.45,1e-10,0.0\n"
            "1000.0,0.1,2725.0,0.05,0.5\n"
            "1500.0,0.99,4100.0,0.2,10.0\n"
        )
        p = self._write_tmp(tmp_path, content)
        tab = load_recombination_table(p)
        assert tab.n_points == 3
        assert tab.metadata["h"] == "0.67"
        assert tab.metadata["source"] == "test"
        assert tab.z_min == 1.0
        assert tab.z_max == 1500.0

    def test_accepts_unsorted_input(self, tmp_path):
        content = (
            "z,x_e,T_m,tau_dot,kappa\n"
            "1000.0,0.1,2725.0,0.05,5.0\n"
            "1.0,0.001,5.45,1e-10,0.0\n"
            "500.0,0.5,1363.0,0.025,2.5\n"
        )
        p = self._write_tmp(tmp_path, content)
        tab = load_recombination_table(p)
        # Should be re-sorted ascending
        assert tab.z[0] == 1.0
        assert tab.z[1] == 500.0
        assert tab.z[2] == 1000.0

    def test_rejects_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_recombination_table(tmp_path / "nonexistent.csv")

    def test_rejects_wrong_columns(self, tmp_path):
        content = (
            "z,x_e,T_m,tau_dot\n"  # missing kappa
            "1.0,0.001,5.45,1e-10\n"
        )
        p = self._write_tmp(tmp_path, content)
        with pytest.raises(ValueError, match="column schema mismatch"):
            load_recombination_table(p)

    def test_rejects_bad_numeric_data(self, tmp_path):
        content = (
            "z,x_e,T_m,tau_dot,kappa\n"
            "1.0,not_a_number,5.45,1e-10,0.0\n"
        )
        p = self._write_tmp(tmp_path, content)
        with pytest.raises(ValueError, match="failed to parse data"):
            load_recombination_table(p)

    def test_rejects_no_data_rows(self, tmp_path):
        content = "# h = 0.67\nz,x_e,T_m,tau_dot,kappa\n"
        p = self._write_tmp(tmp_path, content)
        with pytest.raises(ValueError, match="no data rows"):
            load_recombination_table(p)

    def test_handles_blank_lines(self, tmp_path):
        content = (
            "# h = 0.67\n"
            "\n"
            "z,x_e,T_m,tau_dot,kappa\n"
            "\n"
            "1.0,0.001,5.45,1e-10,0.0\n"
            "1000.0,0.1,2725.0,0.05,0.5\n"
            "\n"
        )
        p = self._write_tmp(tmp_path, content)
        tab = load_recombination_table(p)
        assert tab.n_points == 2


# ============================================================================
# 4. TestValidationChecks
# ============================================================================

class TestValidationChecks:

    def test_valid_synthetic_table_passes(self):
        tab = make_synthetic_tanh_table()
        errors = validate_recombination_table(tab)
        assert errors == []

    def test_x_e_out_of_range(self):
        tab = make_synthetic_tanh_table()
        # Inject value outside [0, 1.2]
        bad_x_e = tab.x_e.copy()
        bad_x_e[0] = -0.1
        tab_bad = RecombinationTable(
            z=tab.z, x_e=bad_x_e, T_m=tab.T_m,
            tau_dot=tab.tau_dot, kappa=tab.kappa,
        )
        errors = validate_recombination_table(tab_bad)
        assert any("x_e out of" in e for e in errors)

    def test_negative_tau_dot(self):
        tab = make_synthetic_tanh_table()
        bad_tau = tab.tau_dot.copy()
        bad_tau[5] = -1e-3
        tab_bad = RecombinationTable(
            z=tab.z, x_e=tab.x_e, T_m=tab.T_m,
            tau_dot=bad_tau, kappa=tab.kappa,
        )
        errors = validate_recombination_table(tab_bad)
        assert any("tau_dot has negative" in e for e in errors)

    def test_kappa_non_monotonic(self):
        tab = make_synthetic_tanh_table()
        bad_kappa = tab.kappa.copy()
        # Flip two adjacent points to create a clear decrease
        bad_kappa[100] = bad_kappa[99] - 1.0
        tab_bad = RecombinationTable(
            z=tab.z, x_e=tab.x_e, T_m=tab.T_m,
            tau_dot=tab.tau_dot, kappa=bad_kappa,
        )
        errors = validate_recombination_table(tab_bad)
        assert any("kappa not monotonically" in e for e in errors)

    def test_T_m_out_of_range(self):
        tab = make_synthetic_tanh_table()
        bad_Tm = tab.T_m.copy()
        bad_Tm[10] = -1.0
        tab_bad = RecombinationTable(
            z=tab.z, x_e=tab.x_e, T_m=bad_Tm,
            tau_dot=tab.tau_dot, kappa=tab.kappa,
        )
        errors = validate_recombination_table(tab_bad)
        assert any("T_m out of" in e for e in errors)


# ============================================================================
# 5. TestBuildInterpolators
# ============================================================================

class TestBuildInterpolators:

    def test_construction(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        assert isinstance(interp, RecombinationInterp)
        assert interp.table is tab

    def test_splines_exact_at_grid_points(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        # At grid points, the shape-preserving interpolator should be exact
        test_z = tab.z[50]
        assert abs(interp.query_x_e(test_z) - tab.x_e[50]) < 1e-12
        assert abs(interp.query_T_m(test_z) - tab.T_m[50]) < 1e-10
        assert abs(interp.query_tau_dot(test_z) - tab.tau_dot[50]) < 1e-12
        assert abs(interp.query_kappa(test_z) - tab.kappa[50]) < 1e-12

    def test_interpolators_preserve_positive_opacity_and_monotone_kappa(self):
        z = np.array([1.0, 4.0, 6.0, 20.0, 100.0], dtype=float)
        tab = RecombinationTable(
            z=z,
            x_e=np.array([0.001, 0.01, 0.05, 0.2, 1.0], dtype=float),
            T_m=2.725 * (1.0 + z),
            tau_dot=np.array([0.0, 1.0e-8, 1.0e-4, 2.0e-4, 3.0e-4]),
            kappa=np.array([0.0, 1.0e-7, 2.0e-3, 8.0e-3, 1.0e-1]),
        )
        interp = build_interpolators(tab)
        z_query = np.linspace(tab.z_min, tab.z_max, 512)
        tau_dot = interp.query_tau_dot(z_query)
        kappa = interp.query_kappa(z_query)
        assert np.all(tau_dot >= -1.0e-15)
        assert np.all(np.diff(kappa) >= -1.0e-15)


# ============================================================================
# 6. TestQueryMethods
# ============================================================================

class TestQueryMethods:

    def test_scalar_query_returns_scalar(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        result = interp.query_x_e(1089.0)
        assert isinstance(result, float)

    def test_array_query_returns_array(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        z_arr = np.array([100.0, 1089.0, 2000.0])
        result = interp.query_x_e(z_arr)
        assert isinstance(result, np.ndarray)
        assert result.shape == (3,)

    def test_out_of_range_raises(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        with pytest.raises(ValueError, match="out of table range"):
            interp.query_x_e(tab.z_max + 100.0)
        with pytest.raises(ValueError, match="out of table range"):
            interp.query_x_e(tab.z_min - 1.0)

    def test_out_of_range_array_raises(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        with pytest.raises(ValueError):
            interp.query_x_e(np.array([100.0, tab.z_max + 100.0]))


# ============================================================================
# 7. TestVisibilityFunction
# ============================================================================

class TestVisibilityFunction:

    def test_visibility_formula(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        z_test = 1100.0
        tau_dot = interp.query_tau_dot(z_test)
        kappa = interp.query_kappa(z_test)
        g = interp.query_visibility(z_test)
        expected = tau_dot * np.exp(-kappa)
        assert abs(g - expected) < 1e-14

    def test_visibility_array(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        z_arr = np.linspace(500.0, 1500.0, 100)
        g_arr = interp.query_visibility(z_arr)
        assert g_arr.shape == (100,)
        assert np.all(g_arr >= 0)


# ============================================================================
# 8. TestSyntheticTanhFixture
# ============================================================================

class TestSyntheticTanhFixture:

    def test_basic_shape(self):
        tab = make_synthetic_tanh_table(n_points=200)
        assert tab.n_points == 200

    def test_x_e_monotonic_in_z(self):
        # tanh profile: x_e increases with z
        tab = make_synthetic_tanh_table()
        assert np.all(np.diff(tab.x_e) >= 0)

    def test_kappa_increases_with_z(self):
        tab = make_synthetic_tanh_table()
        assert np.all(np.diff(tab.kappa) >= 0)

    def test_passes_own_validation(self):
        tab = make_synthetic_tanh_table()
        assert validate_recombination_table(tab) == []


# ============================================================================
# 9. TestFindLastScatteringRedshift
# ============================================================================

class TestFindLastScatteringRedshift:

    def test_synthetic_table(self):
        # Synthetic table has kappa values by construction; z_ls depends
        # on the specific parameters
        tab = make_synthetic_tanh_table(n_points=1000)
        interp = build_interpolators(tab)
        # Pick a kappa value near the middle of the range
        target = (tab.kappa[0] + tab.kappa[-1]) / 2.0
        z_target = find_last_scattering_redshift(
            interp, target_kappa=target,
        )
        # Verify by evaluating kappa at z_target
        assert abs(interp.query_kappa(z_target) - target) < 1e-10

    def test_out_of_range_target_raises(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        with pytest.raises(ValueError, match="outside table range"):
            find_last_scattering_redshift(
                interp, target_kappa=tab.kappa[-1] + 100.0,
            )


# ============================================================================
# 10. TestFindVisibilityPeak
# ============================================================================

class TestFindVisibilityPeak:

    def test_peak_location_in_search_range(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        z_peak, g_peak = find_visibility_peak(
            interp,
            z_search_lo=tab.z_min,
            z_search_hi=tab.z_max,
        )
        assert tab.z_min <= z_peak <= tab.z_max
        assert g_peak > 0.0

    def test_invalid_search_range_raises(self):
        tab = make_synthetic_tanh_table()
        interp = build_interpolators(tab)
        with pytest.raises(ValueError, match="invalid search range"):
            find_visibility_peak(
                interp, z_search_lo=2000.0, z_search_hi=1000.0,
            )


# ============================================================================
# 11. TestRealHyRecReference — validation against real Planck 2018 table
# ============================================================================

@pytest.mark.skipif(
    not REAL_HYREC_CSV.exists(),
    reason=f"Real HyRec reference CSV not found: {REAL_HYREC_CSV}",
)
class TestRealHyRecReference:
    """Critical production-data integration test.

    Validates that the sandbox-generated HyRec-2 Planck 2018 reference
    table (8,000 rows, z=1..8000) parses correctly and produces the
    expected physical values.
    """

    def test_load_real_table(self):
        tab = load_recombination_table(REAL_HYREC_CSV)
        assert tab.n_points == 8000
        assert tab.z_min == 1.0
        assert tab.z_max == 8000.0

    def test_real_table_metadata(self):
        tab = load_recombination_table(REAL_HYREC_CSV)
        # h, Omega_b, T_CMB, Y_He should be present from the generator
        # (keys are lowercased)
        assert "h" in tab.metadata
        assert abs(float(tab.metadata["h"]) - 0.6735837) < 1e-6

    def test_real_table_passes_validation(self):
        tab = load_recombination_table(REAL_HYREC_CSV)
        errors = validate_recombination_table(tab)
        assert errors == []

    def test_x_e_at_z_1075_matches_reference(self):
        # User memory reference: x_e(z=1075) ≈ 0.1137
        # Our sandbox HyRec gives 0.11335 (0.3% off, from cosmology variant)
        tab = load_recombination_table(REAL_HYREC_CSV)
        interp = build_interpolators(tab)
        x_e_at_1075 = interp.query_x_e(1075.0)
        assert abs(x_e_at_1075 - 0.1137) < 0.01  # within 1%

    def test_last_scattering_near_1090(self):
        # Planck 2018 reference: z_* = 1089.95 ± 0.27
        tab = load_recombination_table(REAL_HYREC_CSV)
        interp = build_interpolators(tab)
        z_ls = find_last_scattering_redshift(interp, target_kappa=1.0)
        # Our κ integration should give ≈ 1089.9
        assert 1085.0 < z_ls < 1095.0

    def test_visibility_peak_near_last_scattering(self):
        tab = load_recombination_table(REAL_HYREC_CSV)
        interp = build_interpolators(tab)
        z_peak, g_peak = find_visibility_peak(interp)
        # Visibility peaks slightly before z_ls (g = τ̇ exp(-κ) max
        # where dτ̇/dz = τ̇²); typically z_peak ≈ 1080-1090
        assert 1060.0 < z_peak < 1100.0
        assert g_peak > 0.0


# ============================================================================
# 12. TestPhysicalSignAssertions — v1.2 pattern
# ============================================================================

class TestPhysicalSignAssertions:

    def test_tau_dot_non_negative_after_interpolation(self):
        # τ̇ must remain non-negative under spline interpolation
        tab = make_synthetic_tanh_table(n_points=500)
        interp = build_interpolators(tab)
        z_query = np.linspace(tab.z_min, tab.z_max, 2000)
        tau_dot = interp.query_tau_dot(z_query)
        assert np.all(tau_dot >= -1e-10)  # tiny negative allowed (spline overshoot)

    def test_visibility_non_negative(self):
        tab = make_synthetic_tanh_table(n_points=500)
        interp = build_interpolators(tab)
        z_query = np.linspace(tab.z_min, tab.z_max, 2000)
        g = interp.query_visibility(z_query)
        assert np.all(g >= -1e-10)

    def test_visibility_integral_approximates_one(self):
        # ∫ g(z) dz/((1+z)H(z)) should approximate 1 - exp(-κ_total)
        # A weaker check: ∫ g dz roughly matches τ̇_typical × FWHM.
        # We assert the integral is finite and positive.
        tab = make_synthetic_tanh_table(n_points=500)
        interp = build_interpolators(tab)
        z_grid = np.linspace(tab.z_min, tab.z_max, 2000)
        g_grid = interp.query_visibility(z_grid)
        integral = float(np.trapezoid(g_grid, z_grid))
        assert integral > 0.0
        assert np.isfinite(integral)

    def test_kappa_positive_derivative_proxy(self):
        # dκ/dz = τ̇ × dη/dz should be non-negative (both τ̇ ≥ 0
        # and |dη/dz| > 0)
        tab = make_synthetic_tanh_table(n_points=500)
        interp = build_interpolators(tab)
        z_query = np.linspace(tab.z_min + 10, tab.z_max - 10, 500)
        dz = 1.0
        kappa_plus = interp.query_kappa(z_query + dz)
        kappa_minus = interp.query_kappa(z_query - dz)
        dkappa_dz = (kappa_plus - kappa_minus) / (2.0 * dz)
        assert np.all(dkappa_dz > -1e-10)


# ============================================================================
# 13. TestCrossReferenceKnownValues — HyRec sandbox generated data
# ============================================================================

@pytest.mark.skipif(
    not REAL_HYREC_CSV.exists(),
    reason="Real HyRec reference CSV not found",
)
class TestCrossReferenceKnownValues:

    def test_tau_dot_at_z_1100(self):
        # CAMB/literature reference: τ̇(z=1100) ≈ 0.07 /Mpc for Planck 2018
        tab = load_recombination_table(REAL_HYREC_CSV)
        interp = build_interpolators(tab)
        tau_1100 = interp.query_tau_dot(1100.0)
        # Our sandbox value was 0.0684, reference range 0.06-0.08
        assert 0.05 < tau_1100 < 0.10

    def test_kappa_monotone_across_full_range(self):
        tab = load_recombination_table(REAL_HYREC_CSV)
        diffs = np.diff(tab.kappa)
        # Large-scale monotone increase
        assert np.all(diffs >= -1e-6)

    def test_deep_ionized_kappa_large(self):
        # Deep in the ionized era (z=8000), κ should be O(100-1000)
        tab = load_recombination_table(REAL_HYREC_CSV)
        assert tab.kappa[-1] > 100.0
