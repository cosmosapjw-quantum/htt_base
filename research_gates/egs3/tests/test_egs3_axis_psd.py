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


if __name__ == "__main__":
    unittest.main()
