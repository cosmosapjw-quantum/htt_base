"""Small deterministic mathematical tests; usable with unittest or pytest."""
import unittest
import numpy as np
from htt.htt.infer.r61_box_comparison import (
    BoxExtremaNumericalError, quadratic_box_range, mixed_invariant_box_range,
)


def stf_basis():
    s2, s6 = 1/np.sqrt(2), 1/np.sqrt(6)
    return np.array([np.diag([s2, -s2, 0]), np.diag([s6, s6, -2*s6]),
                     [[0, s2, 0], [s2, 0, 0], [0, 0, 0]],
                     [[0, 0, s2], [0, 0, 0], [s2, 0, 0]],
                     [[0, 0, 0], [0, 0, s2], [0, s2, 0]]])


class TestQuadraticBox(unittest.TestCase):
    def check_range(self, Q, lo, hi, expected):
        r = quadratic_box_range(Q, lo, hi)
        np.testing.assert_allclose([r['minimum'], r['maximum']], expected, atol=2e-12, rtol=0)
        for name in ('minimum_witness', 'maximum_witness'):
            w = r[name]
            x = np.array(w['x'])
            self.assertTrue(np.all(x >= lo) and np.all(x <= hi))
            self.assertAlmostEqual(float(x@np.asarray(Q)@x), w['value'], places=12)
        self.assertEqual(r['diagnostics']['faces_enumerated'], 3**len(lo))
        return r

    def test_nonzero_box_center(self):
        self.check_range(np.eye(2), np.array([1., -3.]), np.array([2., -1.]), [2., 13.])

    def test_indefinite_three_dimensions(self):
        self.check_range(np.diag([1., -2., 3.]), np.array([-2., -1., -.5]),
                         np.array([1., 3., 2.]), [-18., 16.])

    def test_psd_flat_directions(self):
        r = self.check_range(np.diag([1., 0., 0.]), np.array([-2., -3., .4]),
                             np.array([3., 5., .8]), [0., 9.])
        self.assertGreater(r['diagnostics']['singular_consistent_lp_feasible'], 0)

    def test_singular_stationary_affine_set_requires_feasible_lp(self):
        # The minimum-norm stationary point (0,0) is outside this box; the
        # stationary affine line x+y=0 intersects it and must not be dropped.
        r = self.check_range(np.ones((2, 2)), np.array([1., -4.]),
                             np.array([3., -2.]), [0., 9.])
        self.assertGreater(r['diagnostics']['singular_consistent_lp_feasible'], 0)

    def test_singular_inconsistent_face_has_no_stationary_point(self):
        r = self.check_range(np.array([[0., 1.], [1., 0.]]), np.array([1., 1.]),
                             np.array([2., 2.]), [2., 8.])
        self.assertGreater(r['diagnostics']['singular_inconsistent_faces'], 0)

    def test_analytic_one_dimension(self):
        self.check_range(np.array([[2.]]), np.array([1.]), np.array([3.]), [2., 18.])
        self.check_range(np.array([[-2.]]), np.array([-2.]), np.array([1.]), [-8., 0.])
        self.check_range(np.array([[0.]]), np.array([2.]), np.array([3.]), [0., 0.])

    def test_collapsed_interval(self):
        self.check_range(np.array([[2., 1.], [1., -1.]]), np.array([1., -2.]),
                         np.array([1., 3.]), [-6., 3.])

    def test_ambiguous_near_singular_mode_is_explicit_error(self):
        with self.assertRaises(BoxExtremaNumericalError):
            quadratic_box_range(np.diag([1., 1e-13]), [-1., -1.], [1., 1.])

    def test_actual_mixed_box_one_active_beta_coordinate(self):
        E = stf_basis()
        lo = np.array([.5, 0, 0, 0, 0.])
        hi = np.array([1., 0, 0, 0, 0.])
        rho = .01
        r = mixed_invariant_box_range([1., 0., 0.], [2., 0., 0.], lo, hi, E, rho=rho)
        a = np.sqrt(5)*rho
        expected = [.5/np.sqrt(2)-a, 4*(1/np.sqrt(2)+a)]
        np.testing.assert_allclose(r['range'], expected, atol=2e-12, rtol=0)
        self.assertEqual(r['diagnostics']['kappa_corners'], 32)
        self.assertEqual(r['diagnostics']['quadratic_box_calls'], 64)
        self.assertEqual(r['diagnostics']['faces_enumerated'], 64*27)
        for key in ('minimum_witness', 'maximum_witness'):
            w = r[key]
            self.assertLess(w['reconstruction_abs_error'], 2e-12)
            self.assertAlmostEqual(w['calibration_fullsky_rms'], rho, places=14)

    def test_invalid_inputs(self):
        for Q, lo, hi in ((np.eye(2), [1], [2]), (np.eye(2), [1, 2], [0, 3]),
                          (np.array([[1., 1.], [0., 1.]]), [0, 0], [1, 1])):
            with self.assertRaises(ValueError):
                quadratic_box_range(Q, lo, hi)


if __name__ == '__main__':
    unittest.main()
