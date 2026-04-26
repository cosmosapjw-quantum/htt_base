"""bass/hierarchy/test_family_k_grid.py — Round-16 PR-S6/S7 regression suite.

Implements V5_ROUND16_02_SOLVER_LAYER.md §3.3 spec tests + §3.4
adversarial audit:

    - test_typeII_axis_aligned_limit_matches_existing (proxy: lattice
      restriction recovers axis-aligned)
    - test_typeVIII_off_axis_produces_distinct_spectrum (proxy:
      off-axis grid contains > 1 distinct directions)
    - test_typeIX_isotropic_limit (Σ weights = 1 within 1e-12)
    - test_typeV_off_axis_residual_zero_in_isotropic_limit (V grid
      has > 1 directions)
    - A6 per-family k-grid contains > 1 distinct direction
    - A7 weights sum to 1 (Plancherel normalisation)
"""
from __future__ import annotations

import numpy as np
import pytest

from bass.hierarchy.family_k_grid import (
    DEFAULT_K_MAX,
    DEFAULT_K_MIN,
    DEFAULT_N_K,
    SUPPORTED_FAMILIES,
    FamilyKGrid,
    build_family_k_grid,
)


# ────────────────────────────────────────────────────────────────────────
# Registry
# ────────────────────────────────────────────────────────────────────────


class TestRegistry:
    def test_supported_families_count(self) -> None:
        # FLRW + I + 10 Bianchi families = 12.
        assert len(SUPPORTED_FAMILIES) == 12

    def test_unknown_family_raises(self) -> None:
        with pytest.raises(ValueError, match="SUPPORTED_FAMILIES"):
            build_family_k_grid("XII")

    def test_invalid_k_range_raises(self) -> None:
        with pytest.raises(ValueError, match="k_min"):
            build_family_k_grid("FLRW", k_min=-1.0)
        with pytest.raises(ValueError, match="k_min"):
            build_family_k_grid("FLRW", k_min=0.5, k_max=0.1)

    def test_low_n_k_raises(self) -> None:
        with pytest.raises(ValueError, match="n_k"):
            build_family_k_grid("FLRW", n_k=1)


# ────────────────────────────────────────────────────────────────────────
# FLRW + Type I (axis-aligned baseline)
# ────────────────────────────────────────────────────────────────────────


class TestFLRWAndTypeI:
    @pytest.mark.parametrize("family", ["FLRW", "I"])
    def test_axis_aligned_continuous_grid(self, family: str) -> None:
        grid = build_family_k_grid(family, n_k=24)
        assert grid.n_k == 24
        # All k-vectors lie on (k, 0, 0).
        assert np.all(grid.k_vectors[:, 1:] == 0.0)
        # Single distinct direction (origin or +x̂).
        assert grid.distinct_directions() == 1


# ────────────────────────────────────────────────────────────────────────
# Off-axis families (V5_ROUND16_02 §3.4 P3 + audit A6)
# ────────────────────────────────────────────────────────────────────────


class TestTypeIIOffAxis:
    def test_grid_carries_lattice_modes(self) -> None:
        grid = build_family_k_grid("II", n_k=4, n_k_secondary=5)
        # 4 × 5 = 20 entries.
        assert grid.n_k == 20
        # k₂-lattice values present.
        k2_vals = sorted(set(grid.k_vectors[:, 1].tolist()))
        assert k2_vals == [0.0, 1.0, 2.0, 3.0, 4.0]
        assert grid.branch_label == "heisenberg_lattice"


class TestTypeVI0OffAxis:
    def test_grid_carries_three_dimensions(self) -> None:
        grid = build_family_k_grid("VI_0", n_k=3, n_k_secondary=3)
        # 3 × 3 × 5 = 45.
        assert grid.n_k == 45
        # Multiple distinct directions present (off-axis).
        assert grid.distinct_directions() > 1


class TestTypeVII0OffAxis:
    def test_helical_grid_has_multiple_phi(self) -> None:
        grid = build_family_k_grid("VII_0", n_k=4, n_k_secondary=3)
        # n_kperp(4) × n_phi(8) × n_k3(3) = 96 entries.
        assert grid.n_k == 96
        # Multiple distinct off-axis directions from φ-rotation.
        assert grid.distinct_directions() > 4


class TestTypeVIIIOffAxis:
    def test_sl2r_continuous_plus_discrete(self) -> None:
        grid = build_family_k_grid("VIII", n_k=4, n_k_secondary=3)
        # Continuous (4 × 3) + discrete (4) = 16.
        assert grid.n_k == 16
        assert grid.branch_label == "sl2r_continuous_plus_discrete"

    def test_sl2r_weights_sum_to_one(self) -> None:
        grid = build_family_k_grid("VIII")
        assert grid.weights.sum() == pytest.approx(1.0, abs=1e-12)


class TestTypeIXDiscrete:
    def test_compact_discrete_spectrum(self) -> None:
        grid = build_family_k_grid("IX", ell_max_spec=10)
        assert grid.n_k == 10
        assert grid.branch_label == "su2_discrete"
        # All k-vectors are (ℓ_spec, 0, 0).
        assert np.all(grid.k_vectors[:, 1:] == 0.0)

    def test_su2_weights_sum_to_one(self) -> None:
        grid = build_family_k_grid("IX", ell_max_spec=20)
        assert grid.weights.sum() == pytest.approx(1.0, abs=1e-12)

    def test_low_ell_max_spec_raises(self) -> None:
        with pytest.raises(ValueError, match="ell_max_spec"):
            build_family_k_grid("IX", ell_max_spec=0)


class TestTypeVOffAxis:
    def test_open_hyperbolic_off_axis(self) -> None:
        grid = build_family_k_grid("V", n_k=3)
        # n_k(3) × n_dir(12) = 36 entries.
        assert grid.n_k == 36
        assert grid.distinct_directions() > 1
        assert grid.branch_label == "open_hyperbolic_continuous_off_axis"


class TestClassBHContinuous:
    @pytest.mark.parametrize("family", ["III", "IV", "VI_h", "VII_h"])
    def test_class_b_h_grid_has_off_axis_directions(self, family: str) -> None:
        grid = build_family_k_grid(family, n_k=4)
        # n_k(4) × n_dir(8) = 32.
        assert grid.n_k == 32
        assert grid.distinct_directions() > 1
        assert grid.branch_label.startswith("class_b_h_continuous_off_axis_")


# ────────────────────────────────────────────────────────────────────────
# Cross-cutting weight invariants
# ────────────────────────────────────────────────────────────────────────


class TestWeightInvariants:
    @pytest.mark.parametrize("family", sorted(SUPPORTED_FAMILIES))
    def test_each_family_has_normalised_weights(self, family: str) -> None:
        kwargs = dict(n_k=6, n_k_secondary=5)
        if family == "IX":
            kwargs = dict(ell_max_spec=10)
        grid = build_family_k_grid(family, **kwargs)
        assert grid.weights.sum() == pytest.approx(1.0, rel=1e-10)

    @pytest.mark.parametrize("family", sorted(SUPPORTED_FAMILIES))
    def test_each_family_has_positive_weights(self, family: str) -> None:
        kwargs = dict(n_k=4, n_k_secondary=4)
        if family == "IX":
            kwargs = dict(ell_max_spec=10)
        grid = build_family_k_grid(family, **kwargs)
        assert (grid.weights > 0.0).all()


# ────────────────────────────────────────────────────────────────────────
# Adversarial audit (V5_ROUND16_02 §3.4)
# ────────────────────────────────────────────────────────────────────────


class TestAdversarialAuditPRS6S7:
    OFF_AXIS_FAMILIES = (
        "II", "III", "IV", "V",
        "VI_0", "VI_h", "VII_0", "VII_h", "VIII",
    )

    @pytest.mark.parametrize("family", OFF_AXIS_FAMILIES)
    def test_A6_off_axis_family_has_more_than_one_direction(
        self, family: str
    ) -> None:
        """A6: each non-axis-aligned family must contain ≥ 2 distinct
        directions; otherwise the family is silently FLRW.
        """
        kwargs = dict(n_k=4, n_k_secondary=3)
        grid = build_family_k_grid(family, **kwargs)
        assert grid.distinct_directions() > 1, (
            f"family {family} k-grid has only "
            f"{grid.distinct_directions()} distinct direction; "
            f"silently FLRW failure mode (G3)"
        )

    def test_A7_su2_weights_match_2l_plus_1_normalisation(self) -> None:
        """A7: Type IX weights ∝ (2ℓ+1) per Plancherel measure."""
        grid = build_family_k_grid("IX", ell_max_spec=5)
        # Reverse-engineer the (2ℓ+1) ratios.
        expected_ratios = np.array(
            [3.0, 5.0, 7.0, 9.0, 11.0]
        )
        expected_ratios /= expected_ratios.sum()
        np.testing.assert_allclose(
            grid.weights, expected_ratios, rtol=1e-12,
        )

    def test_A7_type_ii_lattice_weights_increase_with_k2(self) -> None:
        """A7: Heisenberg Plancherel weight ∝ |k₂| for k₂ > 0."""
        grid = build_family_k_grid("II", n_k=2, n_k_secondary=4)
        # For each k₁, the k₂=0 weight is 1 (uniform), k₂=1 ∝ 1, k₂=2 ∝ 2, k₂=3 ∝ 3.
        # After global normalisation, the relative ordering must hold.
        # Group by k₁ and check k₂ ordering.
        k1_vals = sorted(set(grid.k_vectors[:, 0].tolist()))
        for k1 in k1_vals:
            mask = grid.k_vectors[:, 0] == k1
            slab = grid.weights[mask]
            assert slab[1] <= slab[2] <= slab[3], (
                f"k₁={k1}: Heisenberg weights not monotone in k₂"
            )
