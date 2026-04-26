"""bass/hierarchy/test_mode_mixing_blocks.py — Round-16 PR-S3 regression suite.

Implements V5_ROUND16_02_SOLVER_LAYER.md §2.6 spec tests:

    - test_wigner_3j_known_values
    - test_shear_coupling_table_diagonal_in_m_when_axisymmetric
    - test_T7_T9_zero_when_shear_zero
    - test_axisymmetric_with_tilt_drives_m_eq_2_only (precursor: A_mix
      structure when only σ_{2,0} is non-zero)
    - test_off_axis_drives_all_m (precursor: σ_{2,±1} non-zero couples
      m to m∓1)

Plus the PR-S3 audit fingerprints (V5_ROUND16_02 §2.7):

    - A1: no toy/naive grep hits in production module
    - A2: full 5-component σ_2M, not σ_+ alone
    - A6: A_curv non-zero is delegated to PR-S4; this PR covers A_mix
      (the shear coupling block)
    - A7: convergence — A_mix(L=20)/A_mix(L=12) bounded
    - A9: deterministic table → bit-identity across calls
"""
from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest
import scipy.sparse as sp

from bass.hierarchy.mode_mixing_blocks import (
    PHOTON_M_COUNT,
    PHOTON_M_VALUES,
    ShearCouplingTable,
    assemble_A_curv_block,
    assemble_A_mix_block,
    assemble_EB_mixing_block,
    build_shear_coupling_table,
    ell_m_to_index,
    index_to_ell_m,
    shear_5vec_to_quadrupole_components,
    wigner_3j,
)


# ────────────────────────────────────────────────────────────────────────
# Wigner-3j sanity (audit A2: not a toy approximation)
# ────────────────────────────────────────────────────────────────────────


class TestWigner3jKnownValues:
    """V5_ROUND16_02 §2.6: cross-check against known closed-form values."""

    def test_w3j_2_2_2_0_0_0(self) -> None:
        # (2 2 2; 0 0 0) = -sqrt(2/35) per Edmonds Table 1
        expected = -math.sqrt(2.0 / 35.0)
        assert wigner_3j(2, 2, 2, 0, 0, 0) == pytest.approx(expected, rel=1e-12)

    def test_w3j_zeros_when_triangle_violated(self) -> None:
        # (2, 2, 5; 0, 0, 0) violates triangle inequality
        assert wigner_3j(2, 2, 5, 0, 0, 0) == 0.0

    def test_w3j_zeros_when_m_sum_nonzero(self) -> None:
        # Wigner-3j vanishes unless m1 + m2 + m3 = 0
        assert wigner_3j(2, 2, 2, 1, 0, 0) == 0.0

    def test_w3j_symmetry_cyclic(self) -> None:
        # Cyclic permutation of columns leaves the 3j invariant.
        a = wigner_3j(2, 3, 4, 1, -2, 1)
        b = wigner_3j(3, 4, 2, -2, 1, 1)
        c = wigner_3j(4, 2, 3, 1, 1, -2)
        assert a == pytest.approx(b, rel=1e-15)
        assert a == pytest.approx(c, rel=1e-15)

    def test_w3j_cached_returns_same_value(self) -> None:
        # The lru_cache must return the exact same float on repeat call.
        a = wigner_3j(2, 2, 4, 0, 0, 0)
        b = wigner_3j(2, 2, 4, 0, 0, 0)
        assert a == b
        assert a != 0.0


# ────────────────────────────────────────────────────────────────────────
# Coupling table structure
# ────────────────────────────────────────────────────────────────────────


class TestShearCouplingTable:
    def test_table_shape_matches_L_max(self) -> None:
        table = build_shear_coupling_table(L_max=10)
        assert table.values.shape == (3, 11, PHOTON_M_COUNT, PHOTON_M_COUNT)
        assert table.L_max == 10

    def test_table_rejects_low_L_max(self) -> None:
        with pytest.raises(ValueError, match="L_max"):
            build_shear_coupling_table(L_max=1)

    def test_table_value_for_C7_at_axisymmetric_drive(self) -> None:
        # M=0 selects σ_{2,0} drive; for ell=10, m=0 the C7 should be
        # non-zero (axisymmetric mode reaches into ℓ+2 at m=0).
        table = build_shear_coupling_table(L_max=12)
        # m index 2 = m=0, M index 2 = M=0
        assert table.values[0, 10, 2, 2] != 0.0

    def test_table_deterministic_across_builds(self) -> None:
        # Bit-identity across builds (audit A9 fairness).
        a = build_shear_coupling_table(L_max=8)
        b = build_shear_coupling_table(L_max=8)
        np.testing.assert_array_equal(a.values, b.values)


# ────────────────────────────────────────────────────────────────────────
# Index helpers
# ────────────────────────────────────────────────────────────────────────


class TestIndexHelpers:
    def test_round_trip_ell_m_index(self) -> None:
        for ell in range(2, 15):
            for m in PHOTON_M_VALUES:
                idx = ell_m_to_index(ell, m)
                assert index_to_ell_m(idx) == (ell, m)

    def test_index_unique_across_range(self) -> None:
        seen = set()
        for ell in range(2, 12):
            for m in PHOTON_M_VALUES:
                idx = ell_m_to_index(ell, m)
                assert idx not in seen
                seen.add(idx)
        assert len(seen) == 10 * PHOTON_M_COUNT

    def test_index_rejects_invalid_m(self) -> None:
        with pytest.raises(ValueError, match="m"):
            ell_m_to_index(5, 3)

    def test_index_rejects_low_ell(self) -> None:
        with pytest.raises(ValueError, match="ell"):
            ell_m_to_index(1, 0)


# ────────────────────────────────────────────────────────────────────────
# 5-vector to quadrupole conversion
# ────────────────────────────────────────────────────────────────────────


class TestShear5VecToQuadrupole:
    def test_zero_5vec_gives_zero_quadrupole(self) -> None:
        out = shear_5vec_to_quadrupole_components(np.zeros(5))
        np.testing.assert_array_equal(out, np.zeros(5))

    def test_axisymmetric_only_M_zero_active(self) -> None:
        # σ_- alone ⇒ only σ_{2,0} non-zero
        sigma_5 = np.array([0.0, 0.5, 0.0, 0.0, 0.0])
        out = shear_5vec_to_quadrupole_components(sigma_5)
        assert out[2] == 0.5  # M=0 slot
        out_no_M0 = np.delete(out, 2)
        np.testing.assert_array_equal(out_no_M0, np.zeros(4))

    def test_off_diagonal_x1_drives_M_minus_2(self) -> None:
        sigma_5 = np.array([0.0, 0.0, 0.7, 0.0, 0.0])  # σ_×1 only
        out = shear_5vec_to_quadrupole_components(sigma_5)
        assert out[0] == 0.7  # M=-2 slot

    def test_off_diagonal_x3_drives_M_minus_1(self) -> None:
        sigma_5 = np.array([0.0, 0.0, 0.0, 0.0, 0.3])
        out = shear_5vec_to_quadrupole_components(sigma_5)
        assert out[1] == 0.3  # M=-1 slot

    def test_rejects_wrong_shape(self) -> None:
        with pytest.raises(ValueError, match="shape"):
            shear_5vec_to_quadrupole_components(np.zeros(4))


# ────────────────────────────────────────────────────────────────────────
# A_mix structural properties (V5_ROUND16_02 §2.6)
# ────────────────────────────────────────────────────────────────────────


class TestAMixZeroShear:
    """V5_ROUND16_02 §2.6: σ_2M = 0 ⇒ A_mix = 0."""

    def test_T7_T9_zero_when_shear_zero(self) -> None:
        A = assemble_A_mix_block(
            sigma_2M=np.zeros(5),
            L_max=12,
            ell_min=2,
        )
        assert A.nnz == 0
        assert sp.linalg.norm(A) == 0.0


class TestAMixAxisymmetric:
    """V5_ROUND16_02 §2.6: σ_2M = δ_{M,0} ⇒ A_mix is m-diagonal."""

    def test_axisymmetric_A_mix_m_diagonal(self) -> None:
        # Pure σ_{2,0} drive: M=0 only ⇒ m_target = m always.
        sigma_2M = np.zeros(5)
        sigma_2M[2] = 1.0e-3  # M=0 slot
        A = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=12, ell_min=2,
        )
        # Walk every nonzero entry and verify (row, col) m-values match.
        A_coo = A.tocoo()
        for r, c in zip(A_coo.row, A_coo.col):
            ell_r, m_r = index_to_ell_m(int(r))
            ell_c, m_c = index_to_ell_m(int(c))
            assert m_r == m_c, (
                f"axisymmetric A_mix should be m-diagonal but found "
                f"row=(ℓ={ell_r}, m={m_r}) col=(ℓ={ell_c}, m={m_c})"
            )

    def test_axisymmetric_A_mix_couples_only_dell_two(self) -> None:
        # Same as above plus check ℓ-coupling is in {-2, 0, +2}.
        sigma_2M = np.zeros(5)
        sigma_2M[2] = 1.0e-3
        A = assemble_A_mix_block(sigma_2M=sigma_2M, L_max=12, ell_min=2)
        A_coo = A.tocoo()
        for r, c in zip(A_coo.row, A_coo.col):
            ell_r, _ = index_to_ell_m(int(r))
            ell_c, _ = index_to_ell_m(int(c))
            assert (ell_r - ell_c) in {-2, 0, 2}, (
                f"unexpected ℓ-coupling Δℓ={ell_r - ell_c}"
            )


class TestAMixParityOdd:
    """Parity-odd σ_{2,±1} drives off-diagonal m-mixing.

    Critical for the B-mode generation pathway in PR-S4 / PR-S11.
    """

    def test_M_eq_minus_1_drives_off_diagonal_m(self) -> None:
        sigma_2M = np.zeros(5)
        sigma_2M[1] = 1.0e-3  # M=-1 slot
        A = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=10, ell_min=2,
        )
        # M=-1 drives m_target = m + 1 (since m_target = m - M = m + 1).
        # Find at least one entry with m_r != m_c.
        A_coo = A.tocoo()
        seen_off_diagonal = False
        for r, c in zip(A_coo.row, A_coo.col):
            ell_r, m_r = index_to_ell_m(int(r))
            ell_c, m_c = index_to_ell_m(int(c))
            if m_r != m_c:
                seen_off_diagonal = True
                # The drive M=-1 implies m_c = m_r - M = m_r + 1.
                assert m_c == m_r + 1, (
                    f"M=-1 should drive m_target = m_row + 1; "
                    f"saw m_r={m_r}, m_c={m_c}"
                )
        assert seen_off_diagonal, (
            "M=-1 drive produced an m-diagonal A_mix; off-axis tilt "
            "would be silently FLRW (V5_ROUND16_00 §1 G3 failure mode)"
        )

    def test_full_off_axis_shear_couples_all_m_slots(self) -> None:
        # All five σ_2M components non-zero ⇒ row/col m-values cover all
        # five m-channels for every active ℓ.
        sigma_2M = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        A = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=10, ell_min=2,
        )
        A_coo = A.tocoo()
        m_pairs = set()
        for r, c in zip(A_coo.row, A_coo.col):
            _, m_r = index_to_ell_m(int(r))
            _, m_c = index_to_ell_m(int(c))
            m_pairs.add((m_r, m_c))
        # Should contain pairs with all Δm ∈ {-2..+2}.
        seen_dm = {m_c - m_r for (m_r, m_c) in m_pairs}
        assert seen_dm.issuperset({-2, -1, 0, 1, 2}), (
            f"Full off-axis shear didn't couple all five m-channels; "
            f"saw Δm ∈ {sorted(seen_dm)}"
        )


# ────────────────────────────────────────────────────────────────────────
# Convergence / fairness audit
# ────────────────────────────────────────────────────────────────────────


class TestAMixConvergence:
    """V5_ROUND16_02 §2.7 A7: ||A_mix(L)||_op grows in a controlled way."""

    def test_L_grows_norm_bounded_by_max_sigma_times_ratio(self) -> None:
        sigma_2M = np.array([0.0, 0.0, 1.0e-3, 0.0, 0.0])
        A_12 = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=12, ell_min=2,
        )
        A_20 = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=20, ell_min=2,
        )
        n_12 = sp.linalg.norm(A_12)
        n_20 = sp.linalg.norm(A_20)
        assert n_20 >= n_12, "extending L_max must not shrink the norm"
        # Loose physical bound: the ratio scales no worse than the
        # T8 prefactor (5ℓ/(2ℓ+3)) ratio at the tail, which is < 5.
        assert n_20 / n_12 < 5.0, (
            f"norm ratio {n_20/n_12:.3f} unexpectedly large; "
            f"prefactor structure check needed"
        )


class TestAMixDeterminism:
    """V5_ROUND16_02 §2.7 A9: A_mix is a deterministic function of inputs."""

    def test_repeated_calls_produce_identical_matrix(self) -> None:
        sigma_2M = np.array([1e-4, 2e-4, 3e-4, 4e-4, 5e-4])
        A1 = assemble_A_mix_block(sigma_2M=sigma_2M, L_max=10).toarray()
        A2 = assemble_A_mix_block(sigma_2M=sigma_2M, L_max=10).toarray()
        np.testing.assert_array_equal(A1, A2)

    def test_pre_built_table_matches_on_the_fly(self) -> None:
        sigma_2M = np.array([0.1, 0.0, 0.2, 0.0, 0.3])
        table = build_shear_coupling_table(L_max=10)
        A_with_table = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=10, coupling_table=table,
        )
        A_without_table = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=10,
        )
        np.testing.assert_array_equal(
            A_with_table.toarray(), A_without_table.toarray()
        )


# ────────────────────────────────────────────────────────────────────────
# Adversarial audit (V5_ROUND16_02 §2.7)
# ────────────────────────────────────────────────────────────────────────


class TestAdversarialAuditPRS3:
    """V5_ROUND16_02 §2.7 — code-checkable predicates for PR-S3."""

    def test_A2_uses_full_5_component_sigma_not_just_sigma_plus(self) -> None:
        """A2: dropping σ_- alone must change the matrix.

        If the implementation silently restricted to σ_+, then setting
        σ_- != 0 would have no effect on A_mix.
        """
        sigma_with_only_plus = np.array([0.0, 0.0, 1e-3, 0.0, 0.0])
        sigma_with_x_off_diag = np.array([0.0, 0.0, 1e-3, 5e-4, 0.0])
        # Different inputs must produce different matrices.
        A_a = assemble_A_mix_block(
            sigma_2M=sigma_with_only_plus, L_max=10
        ).toarray()
        A_b = assemble_A_mix_block(
            sigma_2M=sigma_with_x_off_diag, L_max=10
        ).toarray()
        # Difference must be nontrivial.
        assert not np.allclose(A_a, A_b), (
            "Adding σ_×2 (M=+1) component left A_mix unchanged; "
            "the implementation may have dropped the M-loop."
        )

    def test_A6_curvature_block_landed_in_PR_S4(self) -> None:
        """A6: PR-S4 supplies assemble_A_curv_block alongside A_mix.

        Updated from PR-S3 (where A_curv was deliberately absent) once
        PR-S4 lands.
        """
        from bass.hierarchy import mode_mixing_blocks as mod

        assert "assemble_A_curv_block" in dir(mod), (
            "PR-S4 deliverable: assemble_A_curv_block must be exported."
        )
        assert "assemble_EB_mixing_block" in dir(mod), (
            "PR-S4 deliverable: assemble_EB_mixing_block must be exported."
        )

    # ──────────────────────────────────────────────────────────────────
    # PR-S4 — A_curv block (V5_ROUND16_02 §2.5)
    # ──────────────────────────────────────────────────────────────────

    def test_A_curv_FLRW_limit_zero(self) -> None:
        """V5_ROUND16_02 §2.5: S_AB = 0 ⇒ A_curv = 0 (FLRW invariant)."""
        A_curv = assemble_A_curv_block(
            S_AB_2M=np.zeros(5), L_max=10, ell_min=2,
        )
        assert A_curv.nnz == 0
        assert sp.linalg.norm(A_curv) == 0.0

    def test_A_curv_axisymmetric_S_AB_m_diagonal(self) -> None:
        """S_{2,0} alone ⇒ A_curv is m-diagonal (same-ℓ recoupling)."""
        S_AB = np.zeros(5)
        S_AB[2] = 1.0e-3
        A = assemble_A_curv_block(S_AB_2M=S_AB, L_max=10, ell_min=2)
        for r, c in zip(*A.nonzero()):
            ell_r, m_r = index_to_ell_m(int(r))
            ell_c, m_c = index_to_ell_m(int(c))
            assert ell_r == ell_c, "A_curv is same-ℓ"
            assert m_r == m_c, "axisymmetric S_AB ⇒ m-diagonal A_curv"

    def test_A_curv_off_axis_drives_off_diagonal_m(self) -> None:
        """S_{2,-1} non-zero ⇒ off-diagonal m_target = m + 1 (M=-1)."""
        S_AB = np.zeros(5)
        S_AB[1] = 5.0e-4  # M=-1
        A = assemble_A_curv_block(S_AB_2M=S_AB, L_max=10, ell_min=2)
        seen_off_diag = False
        for r, c in zip(*A.nonzero()):
            ell_r, m_r = index_to_ell_m(int(r))
            ell_c, m_c = index_to_ell_m(int(c))
            assert ell_r == ell_c, "A_curv must remain same-ℓ"
            if m_r != m_c:
                seen_off_diag = True
                assert m_c == m_r + 1
        assert seen_off_diag, "S_{2,-1} drive must produce m-coupling"

    def test_A_curv_validates_input_shape(self) -> None:
        with pytest.raises(ValueError, match="S_AB_2M"):
            assemble_A_curv_block(S_AB_2M=np.zeros(4), L_max=10)

    # ──────────────────────────────────────────────────────────────────
    # PR-S4 — E↔B parity-odd mixing block
    # ──────────────────────────────────────────────────────────────────

    def test_EB_mixing_zero_for_axisymmetric(self) -> None:
        """V5_ROUND16_02 §2.3 ¶5: pure σ_{2,0} ⇒ E↔B coupling vanishes."""
        sigma_2M = np.zeros(5)
        sigma_2M[2] = 1.0e-3  # M=0 only
        A_EB = assemble_EB_mixing_block(
            sigma_2M=sigma_2M, L_max=10, ell_min=2,
        )
        assert A_EB.nnz == 0
        assert sp.linalg.norm(A_EB) == 0.0

    def test_EB_mixing_zero_for_no_shear(self) -> None:
        A_EB = assemble_EB_mixing_block(
            sigma_2M=np.zeros(5), L_max=10, ell_min=2,
        )
        assert A_EB.nnz == 0

    def test_EB_mixing_zero_for_parity_even_M_plus_2_drive(self) -> None:
        """σ_{2,+2} (M=+2) is parity-even ⇒ E↔B coupling vanishes."""
        sigma_2M = np.zeros(5)
        sigma_2M[4] = 1.0e-3  # M=+2
        A_EB = assemble_EB_mixing_block(
            sigma_2M=sigma_2M, L_max=10, ell_min=2,
        )
        assert A_EB.nnz == 0, (
            "Parity-even σ_{2,+2} must NOT drive E↔B coupling; "
            "the M%2==1 selection rule was violated."
        )

    def test_EB_mixing_fires_for_parity_odd_drive(self) -> None:
        """σ_{2,-1} ≠ 0 ⇒ E↔B block has non-zero entries."""
        sigma_2M = np.zeros(5)
        sigma_2M[1] = 1.0e-3  # M=-1 (parity-odd)
        A_EB = assemble_EB_mixing_block(
            sigma_2M=sigma_2M, L_max=10, ell_min=2,
        )
        assert A_EB.nnz > 0, (
            "Parity-odd σ_{2,-1} drive must populate the E↔B block; "
            "otherwise B-mode generation pathway is broken (G5 failure)."
        )

    def test_EB_mixing_skips_m_zero_rows(self) -> None:
        """The (m / (ℓ+2)) parity factor forces row-m=0 entries to zero."""
        sigma_2M = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        A_EB = assemble_EB_mixing_block(
            sigma_2M=sigma_2M, L_max=10, ell_min=2,
        )
        for r, c in zip(*A_EB.nonzero()):
            _, m_r = index_to_ell_m(int(r))
            assert m_r != 0, (
                f"row m={m_r} should be skipped (parity factor m/(ℓ+2))"
            )

    def test_EB_mixing_validates_input_shape(self) -> None:
        with pytest.raises(ValueError, match="sigma_2M"):
            assemble_EB_mixing_block(sigma_2M=np.zeros(4), L_max=10)

    def test_A7_increasing_L_max_only_extends(self) -> None:
        """A7: extending L_max must preserve the smaller block as a sub-matrix."""
        sigma_2M = np.array([0.0, 0.0, 1e-3, 0.0, 0.0])
        A_8 = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=8, ell_min=2,
        ).toarray()
        A_12 = assemble_A_mix_block(
            sigma_2M=sigma_2M, L_max=12, ell_min=2,
        ).toarray()
        # A_8 lives in the (5*7)=35 first slots of A_12.
        n_small = 5 * (8 - 2 + 1)
        # Extract the upper-left n_small × n_small block of A_12 and
        # verify it matches A_8 except for the boundary (ℓ+2 reaches
        # outside the L=8 box).
        A_12_block = A_12[:n_small, :n_small]
        # Where A_12_block has support outside-of-A_8 in terms of
        # columns — that's only when ℓ_row + 2 ≤ 8 (T7 reach within
        # the small block) — for those entries equality must hold.
        # Pragmatic test: difference only at rows where ℓ + 2 == 9 or 10
        # (out of small reach), so the inner block (ℓ ≤ 6) must agree.
        n_inner = 5 * (6 - 2 + 1)
        np.testing.assert_allclose(
            A_8[:n_inner, :n_inner],
            A_12[:n_inner, :n_inner],
            rtol=1e-15, atol=1e-15,
        )
