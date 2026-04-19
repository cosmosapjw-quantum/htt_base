"""
Test suite: tsc/diagnostics/entropy_invariants.py  (Week 4 Day 5 Part 2)
=========================================================================

Test classes (5):
  1. TestEntropyOverNumber         — s/n formula + sign / statistics checks
  2. TestEntropyOverEnergy         — s/ρ formula + complementary checks
  3. TestGramAdmissibility         — eigenvalue bounds on Gram matrices
  4. TestMBEtaIndependence         — I_n ratios for MB are η-independent
  5. TestValidation                — error paths

Target: ~22 tests.
"""
from __future__ import annotations

import math
import numpy as np
import pytest

from tsc.charts.laguerre_basis import xi_moment
from tsc.diagnostics.entropy_invariants import (
    ADMISSIBILITY_THRESHOLD,
    GramAdmissibility,
    MBIndependenceResult,
    entropy_over_number,
    entropy_over_energy,
    gram_admissibility,
    verify_mb_eta_independence,
)


# ============================================================================
# Test Class 1 - Entropy over number
# ============================================================================

class TestEntropyOverNumber:
    """s/n = I_3/I_2 + 1 - η."""

    def test_MB_at_eta_zero_is_four(self):
        # I_3/I_2 = 6/2 = 3, +1 = 4
        assert entropy_over_number(0, 0.0) == pytest.approx(4.0, abs=1e-14)

    def test_BE_at_eta_zero_matches_moment_formula(self):
        expected = xi_moment(3, +1, 0.0) / xi_moment(2, +1, 0.0) + 1.0
        assert entropy_over_number(+1, 0.0) == pytest.approx(expected, rel=1e-14)

    def test_FD_at_eta_zero_matches_moment_formula(self):
        expected = xi_moment(3, -1, 0.0) / xi_moment(2, -1, 0.0) + 1.0
        assert entropy_over_number(-1, 0.0) == pytest.approx(expected, rel=1e-14)

    def test_MB_eta_shift_follows_minus_eta(self):
        # For MB, I_3/I_2 is η-independent, so s/n = 4 - η
        assert entropy_over_number(0, -1.0) == pytest.approx(5.0, abs=1e-12)
        assert entropy_over_number(0, -2.0) == pytest.approx(6.0, abs=1e-12)

    def test_rejects_invalid_xi(self):
        with pytest.raises(ValueError, match="xi"):
            entropy_over_number(2, 0.0)

    def test_rejects_positive_eta_for_BE(self):
        with pytest.raises(ValueError, match="BE"):
            entropy_over_number(+1, 0.5)

    def test_FD_allows_positive_eta(self):
        # FD is defined for any real η
        val = entropy_over_number(-1, 0.5)
        assert math.isfinite(val)


# ============================================================================
# Test Class 2 - Entropy over energy
# ============================================================================

class TestEntropyOverEnergy:
    """s/ρ = 1 + (1 - η) · I_2/I_3."""

    def test_MB_at_eta_zero(self):
        # MB: I_2/I_3 = 2/6 = 1/3; s/ρ = 1 + 1/3 = 4/3
        assert entropy_over_energy(0, 0.0) == pytest.approx(
            4.0 / 3.0, abs=1e-14,
        )

    def test_BE_at_eta_zero_matches_moments(self):
        I2 = xi_moment(2, +1, 0.0)
        I3 = xi_moment(3, +1, 0.0)
        expected = 1.0 + I2 / I3
        assert entropy_over_energy(+1, 0.0) == pytest.approx(expected, rel=1e-14)

    def test_eta_shift_reduces_entropy_over_energy(self):
        # For MB, s/ρ(η) = 1 - η/3 + 1/3
        # η=1: 1 - 1/3 + 1/3 = 1
        # η=0: 4/3
        val_0 = entropy_over_energy(0, 0.0)
        val_1 = entropy_over_energy(0, 1.0)
        assert val_0 > val_1

    def test_rejects_invalid_xi(self):
        with pytest.raises(ValueError, match="xi"):
            entropy_over_energy(+2, 0.0)


# ============================================================================
# Test Class 3 - Gram admissibility
# ============================================================================

class TestGramAdmissibility:
    """Eigenvalue bounds on Gram matrices."""

    def test_identity_is_admissible(self):
        G = np.eye(3)
        res = gram_admissibility(G)
        assert res.lambda_min == pytest.approx(1.0, abs=1e-14)
        assert res.lambda_max == pytest.approx(1.0, abs=1e-14)
        assert res.kappa == pytest.approx(1.0, abs=1e-14)
        assert res.is_admissible is True

    def test_positive_definite_admissible(self):
        # [[2,1],[1,2]] has eigenvalues 1, 3
        G = np.array([[2.0, 1.0], [1.0, 2.0]])
        res = gram_admissibility(G)
        assert res.lambda_min == pytest.approx(1.0, abs=1e-12)
        assert res.lambda_max == pytest.approx(3.0, abs=1e-12)
        assert res.kappa == pytest.approx(3.0, abs=1e-12)
        assert res.is_admissible is True

    def test_singular_not_admissible(self):
        # Rank-1 matrix has a zero eigenvalue
        G = np.array([[1.0, 1.0], [1.0, 1.0]])
        res = gram_admissibility(G)
        assert res.lambda_min < ADMISSIBILITY_THRESHOLD
        assert res.is_admissible is False

    def test_negative_definite_not_admissible(self):
        G = np.array([[-1.0, 0.0], [0.0, -2.0]])
        res = gram_admissibility(G)
        assert res.lambda_min < 0
        assert res.is_admissible is False

    def test_symmetrizes_before_eig(self):
        # Asymmetric input — should still succeed (symmetrized internally)
        G = np.array([[2.0, 1.5], [0.5, 2.0]])
        res = gram_admissibility(G)
        # Symmetrized: [[2.0, 1.0], [1.0, 2.0]] → eigenvalues {1, 3}
        assert res.lambda_min == pytest.approx(1.0, abs=1e-12)
        assert res.lambda_max == pytest.approx(3.0, abs=1e-12)

    def test_rejects_non_square(self):
        with pytest.raises(ValueError, match="square"):
            gram_admissibility(np.ones((2, 3)))

    def test_returns_frozen_dataclass(self):
        G = np.eye(2)
        res = gram_admissibility(G)
        assert isinstance(res, GramAdmissibility)
        with pytest.raises(Exception):
            res.lambda_min = 99.0


# ============================================================================
# Test Class 4 - MB η-independence
# ============================================================================

class TestMBEtaIndependence:
    """I_n₁/I_n₂ for MB is η-independent because I_n(MB, η) = e^η n!."""

    def test_pair_3_2_is_three_at_all_eta(self):
        result = verify_mb_eta_independence(
            n_pairs=[(3, 2)],
            eta_values=[-3.0, -1.0, 0.0, 1.0, 2.0],
            tolerance=1e-12,
        )
        assert result.all_within_tolerance
        # All ratios should equal 3
        for r in result.observed_ratios[0, :]:
            assert r == pytest.approx(3.0, rel=1e-12)

    def test_pair_4_3_is_four_at_all_eta(self):
        result = verify_mb_eta_independence(
            n_pairs=[(4, 3)],
            eta_values=[-2.0, 0.0, 3.0],
            tolerance=1e-12,
        )
        assert result.all_within_tolerance
        for r in result.observed_ratios[0, :]:
            assert r == pytest.approx(4.0, rel=1e-12)

    def test_multiple_pairs_independence(self):
        result = verify_mb_eta_independence(
            n_pairs=[(3, 2), (4, 3), (4, 2), (5, 2)],
            eta_values=[-5.0, -2.0, -1.0, 0.0, 1.0, 2.0, 5.0],
            tolerance=1e-10,
        )
        assert result.all_within_tolerance
        assert result.max_deviation_across_eta < 1e-10

    def test_max_deviation_is_near_machine_precision(self):
        result = verify_mb_eta_independence(
            n_pairs=[(3, 2), (4, 3)],
            eta_values=[-2.0, -1.0, 0.0, 1.0, 2.0],
            tolerance=1e-12,
        )
        assert result.max_deviation_across_eta < 1e-13

    def test_rejects_empty_n_pairs(self):
        with pytest.raises(ValueError, match="n_pairs"):
            verify_mb_eta_independence(n_pairs=[], eta_values=[0.0])

    def test_rejects_empty_eta_values(self):
        with pytest.raises(ValueError, match="eta_values"):
            verify_mb_eta_independence(n_pairs=[(3, 2)], eta_values=[])

    def test_returns_frozen_dataclass(self):
        result = verify_mb_eta_independence(
            n_pairs=[(3, 2)], eta_values=[0.0],
        )
        assert isinstance(result, MBIndependenceResult)
        with pytest.raises(Exception):
            result.all_within_tolerance = False


# ============================================================================
# Test Class 5 - Validation and error paths
# ============================================================================

class TestValidation:
    def test_entropy_over_number_rejects_xi_two(self):
        with pytest.raises(ValueError, match="xi"):
            entropy_over_number(2, 0.0)

    def test_entropy_over_energy_rejects_xi_minus_two(self):
        with pytest.raises(ValueError, match="xi"):
            entropy_over_energy(-2, 0.0)
