"""EGS3 revisionary-redesign gates: the PSD-cone-valued sector comparator.

P1 bit-identical trace reconstruction (gating regression for the redesign);
P2 admissible set = PSD cone (fail-closed + convex);
P3 identifiability = reachable eigendirections, blind sector = structural null;
P4 two-sided bracket = convex cone-shell membership excluding the FLRW vertex.
"""
import unittest
import numpy as np

from htt.obsstat.egs3_psd_cone import (
    sector_matrix, sectors_from_matrix, xc_from_matrix, admissibility,
    eigen_identifiability, cone_shell_membership, bracket_shell_from_a2a3,
    convex_combination_is_admissible, SECTOR_SIGNATURE,
)
from htt.obsstat.egs3_graded_comparator import graded_comparator, COMPARATOR_SIGNS


class P1TraceReconstructionTests(unittest.TestCase):
    def test_xc_from_matrix_is_bit_identical_to_graded(self):
        for g in [(2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7),
                  (1.0, 1.0, 0.0, 0.0),          # cancellation case
                  (3.7, 0.0, 0.5, 0.25)]:
            M = sector_matrix(g)
            gc = graded_comparator(*g) if min(g[:3]) >= 0 else None
            # trace identity reproduces <c, g> exactly (not just close)
            self.assertTrue(np.array_equal(xc_from_matrix(M), float(COMPARATOR_SIGNS @ np.asarray(g))))
            if gc is not None:
                self.assertTrue(np.array_equal(xc_from_matrix(M), gc.x_C))

    def test_signature_is_the_comparator_sign_vector(self):
        self.assertTrue(np.array_equal(np.diag(SECTOR_SIGNATURE), COMPARATOR_SIGNS))

    def test_spectrum_equals_sectors(self):
        g = (2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7)
        self.assertTrue(np.allclose(sectors_from_matrix(sector_matrix(g)), g))


class P2AdmissibleConeTests(unittest.TestCase):
    def test_psd_is_admissible_and_fail_closed_on_negative_sector(self):
        self.assertTrue(admissibility(sector_matrix((2e-6, 1e-6, 5e-7, 3e-7))).is_admissible)
        bad = admissibility(sector_matrix((2e-6, -1e-6, 0.0, 0.0)))
        self.assertFalse(bad.is_admissible)
        self.assertEqual(bad.negative_sectors, ("W2",))

    def test_admissible_set_is_a_convex_cone(self):
        M1 = sector_matrix((2e-6, 1e-6, 5e-7, 3e-7))
        M2 = sector_matrix((1e-6, 1e-6, 1e-6, 1e-6))
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            self.assertTrue(convex_combination_is_admissible(M1, M2, t))


class P3EigenIdentifiabilityTests(unittest.TestCase):
    def test_reachable_eigendirections_are_rank_two_with_named_null(self):
        ei = eigen_identifiability(sector_matrix((2e-6, 1.5e-6, 8e-7, 3e-7)))
        self.assertEqual(ei.reachable_rank, 2)
        self.assertEqual(set(ei.reachable_sectors), {"Sigma2", "Omega_tilt"})
        self.assertEqual(set(ei.null_sectors), {"W2", "Omega_k"})

    def test_blind_sector_is_a_structural_null_of_the_measurement_map(self):
        # the W^2, Omega_k invariants are annihilated by M |-> P_R M P_R, and the
        # reachable invariants are recovered exactly.
        ei = eigen_identifiability(sector_matrix((2e-6, 9.9e-6, 8e-7, 9.9e-6)))
        self.assertEqual(ei.null_residual, 0.0)          # blind sector killed exactly
        self.assertTrue(ei.reachable_recovers_sectors)   # reachable kept exactly


class P4ConeShellBracketTests(unittest.TestCase):
    def test_bracket_is_a_convex_shell_excluding_the_flrw_vertex(self):
        s_lo, s_hi = bracket_shell_from_a2a3(5.0, 3.0)
        self.assertGreater(s_lo, 0.0)                    # lower bound is strictly positive
        cs = cone_shell_membership(sector_matrix((4.0, 0.0, 0.0, 0.0)), s_lo, s_hi)
        self.assertTrue(cs.in_shell)
        self.assertTrue(cs.excludes_vertex)
        # the shear-free vertex (lambda_Sigma = 0) is NOT in the shell
        vtx = cone_shell_membership(sector_matrix((0.0, 0.0, 0.0, 0.0)), s_lo, s_hi)
        self.assertFalse(vtx.in_shell)


class P5SignedOmegaKDomainTests(unittest.TestCase):
    """REV-Patch-A: Omega_k_aniso = Omega_k - Omega_k_ref (= -^3R/(6H^2) - ref) is a
    SIGNED comparator coordinate -- negative for closed types / negative
    anisotropic-curvature departures (ComparatorPolicy / departure_contracts, ch03
    Prop x-sign `irrotational_negative`). The moment-cone admissibility must NOT
    reject a background solely for Omega_k < 0, while still fail-closing on a
    negative GENUINE second-moment sector; x_C stays bit-identical."""

    def test_signed_negative_omega_k_is_admissible(self):
        adm = admissibility(sector_matrix((2e-6, 1e-6, 5e-7, -3e-7)))
        self.assertTrue(adm.is_admissible)            # not ejected for Omega_k<0
        self.assertNotIn("Omega_k", adm.negative_sectors)

    def test_negative_genuine_second_moment_still_fails_closed(self):
        for bad, sector in [((2e-6, -1e-6, 0.0, 0.0), "W2"),
                            ((-1e-6, 1e-6, 0.0, 0.0), "Sigma2"),
                            ((1e-6, 1e-6, -1e-6, 0.0), "Omega_tilt")]:
            adm = admissibility(sector_matrix(bad))
            self.assertFalse(adm.is_admissible)
            self.assertIn(sector, adm.negative_sectors)

    def test_xc_bit_identical_with_signed_omega_k(self):
        g = (2e-6, 1e-6, 5e-7, -3e-7)
        self.assertTrue(np.array_equal(
            xc_from_matrix(sector_matrix(g)),
            float(COMPARATOR_SIGNS @ np.asarray(g))))


class P6DiagonalScopeGuardTests(unittest.TestCase):
    """FM3/FM6: the labelled-eigenbasis functions are diagonal-SCOPE. Off-diagonal
    (cross-sector) M is the native-solver superset; it must FAIL CLOSED, not be
    silently mislabelled (M[0,0] is then a Rayleigh quotient, NOT the eigenvalue).
    This replaces the tautological 'diagonal P masks diagonal M' smoke with a real
    boundary test."""

    def _cross(self):
        M = sector_matrix((4.0, 0.0, 1.0, 0.0))
        M[0, 2] = M[2, 0] = 1.5          # genuine Sigma2-Omega_tilt cross term (PSD)
        return M

    def test_offdiagonal_M_is_rejected(self):
        M = self._cross()
        # confirm the adversarial input is genuinely non-diagonal and PSD
        self.assertGreater(abs(M[0, 2]), 0.0)
        self.assertGreaterEqual(np.linalg.eigvalsh(M).min(), -1e-12)
        with self.assertRaises(ValueError):
            sectors_from_matrix(M)
        with self.assertRaises(ValueError):
            eigen_identifiability(M)
        with self.assertRaises(ValueError):
            cone_shell_membership(M, 0.5, 10.0)

    def test_xc_remains_general_for_offdiagonal(self):
        # x_C = tr(C M) is well-defined for ANY M (trace picks the diagonal); the
        # bit-identity is not scope-limited and must NOT raise.
        M = self._cross()
        self.assertEqual(xc_from_matrix(M),
                         float(COMPARATOR_SIGNS @ np.diag(M)))

    def test_diagonal_M_still_passes(self):
        # the in-scope diagonal path is unaffected by the guard
        M = sector_matrix((4.0, 0.0, 1.0, 0.0))
        self.assertEqual(eigen_identifiability(M).reachable_rank, 2)
        self.assertTrue(cone_shell_membership(M, 0.5, 10.0).in_shell)


class P7ReviewRepairTests(unittest.TestCase):
    """2026-07 independent-review repairs (P1 units + P2 null-kind).

    P1: bracket_shell_from_a2a3 must return the SQUARED (Sigma^2-coordinate)
    image of the linear-shear bracket, and a discriminating eigenvalue between
    the squared and linear lower bounds must be IN the shell (the pre-repair
    linear bracket wrongly ejected it).  P2: eigen_identifiability must carry
    the null-KIND distinction (W2 structural vs Omega_k leading-order)."""

    def test_bracket_is_the_square_of_the_linear_bracket(self):
        from htt.obsstat.egs2_shear_bracket import shear_lower, shear_upper
        s_lo, s_hi = bracket_shell_from_a2a3(5.0, 3.0)
        self.assertEqual(s_lo, float(shear_lower(5.0, 3.0)) ** 2)
        self.assertEqual(s_hi, float(shear_upper(5.0)) ** 2)

    def test_discriminating_eigenvalue_between_squared_and_linear_bounds(self):
        from htt.obsstat.egs2_shear_bracket import shear_lower
        lo_lin = float(shear_lower(5.0, 3.0))
        self.assertLess(lo_lin, 1.0)   # squared < linear on (0,1): discriminating
        s_lo, s_hi = bracket_shell_from_a2a3(5.0, 3.0)
        lam = 0.5 * (lo_lin ** 2 + lo_lin)   # strictly between the two bounds
        self.assertGreater(lam, s_lo)
        self.assertLess(lam, lo_lin)         # pre-repair bracket ejected this
        cs = cone_shell_membership(sector_matrix((lam, 0.0, 0.0, 0.0)), s_lo, s_hi)
        self.assertTrue(cs.in_shell)

    def test_null_kinds_distinguish_structural_from_leading_order(self):
        ei = eigen_identifiability(sector_matrix((2e-6, 9.9e-6, 8e-7, 9.9e-6)))
        kinds = dict(zip(ei.null_sectors, ei.null_sector_kinds))
        self.assertEqual(kinds["W2"], "structural_null")
        self.assertEqual(kinds["Omega_k"], "no_channel_leading_order")


if __name__ == "__main__":
    unittest.main()
