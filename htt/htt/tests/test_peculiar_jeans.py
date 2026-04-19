"""Tests for peculiar_jeans fix (A1) and bridge quantities."""
import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent.parent)
for _p in [_root, _root + "/htt", _root + "/bass"]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import math
import numpy as np
import pytest
from htt.core.tilted_flrw import peculiar_jeans, q_matter, Delta_q


class TestPeculiarJeansFix:
    """Tests that peculiar_jeans handles q ≤ 0 (accelerating universe)."""

    beta_CF4 = 1.334e-3
    q0_true = -0.5271  # flat ΛCDM with Ω_m = 0.3153

    def test_accelerating_universe_returns_inf(self):
        """q < 0 → λ_J = ∞ (no gravitational Jeans instability)."""
        lJ, ratio = peculiar_jeans(self.beta_CF4, self.q0_true)
        assert lJ == float('inf')
        assert ratio == float('inf')

    def test_q_zero_returns_inf(self):
        """q = 0 exact → λ_J = ∞."""
        lJ, ratio = peculiar_jeans(self.beta_CF4, 0.0)
        assert lJ == float('inf')
        assert ratio == float('inf')

    def test_no_ValueError_at_negative_q(self):
        """Must NOT raise ValueError for q < 0 (the bug we fixed)."""
        # This is the exact call that used to crash
        lJ, ratio = peculiar_jeans(self.beta_CF4, -0.5271)
        assert math.isinf(lJ)

    def test_positive_q_still_works(self):
        """q > 0 → finite λ_J (unchanged from old behavior)."""
        lJ, ratio = peculiar_jeans(self.beta_CF4, 0.5)
        assert 0 < lJ < 1e6  # finite, reasonable
        assert 0 < ratio < 1

    def test_eds_q_half(self):
        """Einstein-de Sitter: q = 0.5 gives known result."""
        lJ, ratio = peculiar_jeans(self.beta_CF4, 0.5)
        # λ_J = λ_H × (β/(9×0.5))^{1/3} = 4452 × (1.334e-3/4.5)^{1/3}
        expected_ratio = (self.beta_CF4 / 4.5) ** (1.0 / 3.0)
        assert abs(ratio - expected_ratio) / expected_ratio < 1e-10

    def test_q_matter_helper(self):
        """q_matter() = ½Ω_m ≈ 0.158."""
        qm = q_matter()
        assert abs(qm - 0.15765) < 0.001

    def test_q_matter_custom_Om(self):
        """q_matter(Ω_m=0.3) = 0.15."""
        assert q_matter(Om=0.3) == 0.15

    def test_q_matter_positive(self):
        """q_matter is always positive (matter decelerates)."""
        for Om in [0.01, 0.1, 0.3, 0.5, 1.0]:
            assert q_matter(Om=Om) > 0

    def test_lambda_J_with_q_matter(self):
        """Using q_matter gives a finite, physically meaningful λ_J."""
        qm = q_matter()
        lJ, ratio = peculiar_jeans(self.beta_CF4, qm)
        assert 100 < lJ < 2000  # should be ~300-600 Mpc
        assert 0 < ratio < 0.5

    def test_monotonic_in_q(self):
        """λ_J decreases as q increases (stronger deceleration → shorter Jeans)."""
        results = []
        for q in [0.01, 0.1, 0.5, 1.0]:
            lJ, _ = peculiar_jeans(self.beta_CF4, q)
            results.append(lJ)
        for i in range(len(results) - 1):
            assert results[i] > results[i + 1]

    def test_monotonic_in_beta(self):
        """λ_J increases with β (larger tilt → larger Jeans scale)."""
        results = []
        for beta in [1e-4, 1e-3, 1e-2, 1e-1]:
            lJ, _ = peculiar_jeans(beta, 0.5)
            results.append(lJ)
        for i in range(len(results) - 1):
            assert results[i] < results[i + 1]


class TestDeltaQWithBridgeQuantities:
    """Tests that bridge quantities are computable at CF4 parameters."""

    beta_CF4 = 1.334e-3

    def test_Delta_q_positive(self):
        """Δq > 0: tilt makes the universe appear to decelerate MORE."""
        dq = Delta_q(self.beta_CF4, 200.0)
        assert dq > 0

    def test_Delta_q_decreases_with_distance(self):
        """Δq ∝ 1/d³: tilt effect weakens with survey depth."""
        dq_40 = Delta_q(self.beta_CF4, 40.0)
        dq_200 = Delta_q(self.beta_CF4, 200.0)
        dq_1000 = Delta_q(self.beta_CF4, 1000.0)
        assert dq_40 > dq_200 > dq_1000

    def test_Delta_q_at_200_Mpc(self):
        """Δq ≈ 1.6 at d = 200 Mpc (from pipeline results)."""
        dq = Delta_q(self.beta_CF4, 200.0)
        assert 1.0 < dq < 2.5
