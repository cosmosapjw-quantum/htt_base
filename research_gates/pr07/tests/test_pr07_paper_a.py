"""PR07-004 gate: PAPER-A proof closure (real htt.departure module)."""
import unittest
import numpy as np

from htt.departure.paper_a_closure import (
    numerical_rank,
    duplicate_block_audit,
    radial_vorticity_response,
    single_shell_dipole_design,
    temporal_tensor_design,
    boost_composition_audit,
    first_jet_counterexample,
)


class PaperATests(unittest.TestCase):
    def test_duplicate_rank_hypothesis(self):
        A = np.array([[1., 2.], [3., 5.], [2., -1.]])
        r = duplicate_block_audit(A)
        self.assertEqual(r['rank_A'], 2)
        self.assertEqual(r['rank_AA'], 2)
        # full column rank here, so the null space equals the (x,-x) line.
        self.assertTrue(r['nullspace_equals_x_minus_x'])

    def test_duplicate_rank_not_full_column_rank(self):
        # rank-deficient block: equality of null space with (x,-x) must NOT hold.
        A = np.array([[1., 2., 3.], [2., 4., 6.]])
        r = duplicate_block_audit(A)
        self.assertEqual(r['rank_AA'], r['rank_A'])
        self.assertFalse(r['nullspace_equals_x_minus_x'])

    def test_radial_vorticity_no_go(self):
        rng = np.random.default_rng(4)
        n = rng.normal(size=(100, 3)); d = rng.uniform(10, 200, size=100)
        R = radial_vorticity_response(n, d)
        self.assertEqual(numerical_rank(R), 0)
        self.assertLess(np.max(np.abs(R)), 1e-12)

    def test_single_shell_degeneracy_and_broad_depth_recovery(self):
        rng = np.random.default_rng(5)
        n = rng.normal(size=(200, 3))
        shell = single_shell_dipole_design(n, np.full(200, 80.0))
        broad = single_shell_dipole_design(n, np.exp(rng.uniform(np.log(20), np.log(200), size=200)))
        self.assertEqual(numerical_rank(shell), 3)
        self.assertEqual(numerical_rank(broad), 6)

    def test_temporal_tensor_rank(self):
        T = np.array([[1., 0., 0.], [0.4, 1., 0.], [0.2, 0.5, 1.]])
        self.assertEqual(numerical_rank(temporal_tensor_design(T)), 15)

    def test_boost_and_first_jet_split(self):
        b = boost_composition_audit(np.array([0.2, 0, 0]), np.array([0, 0.15, 0]))
        self.assertLess(b['lorentz_error'], 1e-12)
        self.assertGreater(b['nonadditivity_norm'], 1e-4)
        j = first_jet_counterexample(0.2)
        self.assertTrue(j['same_pointwise_velocity'])
        self.assertTrue(j['different_first_jet'])


if __name__ == '__main__':
    unittest.main()
