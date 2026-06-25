"""PR07-003 gate: RK4 / DOP853 / Radau cross-check + branch guards."""
import unittest
import numpy as np

from bass.background.bi_continuation import SpeciesPrimitive, BIState, integrate, dust_flrw_exact
from bass.background.bi_continuation.verification import integrate_solve_ivp


class IntegratorTests(unittest.TestCase):
    def test_dop853_and_radau_against_exact_dust(self):
        H0 = 0.8
        state = BIState(1.0, H0, np.zeros((3, 3)), (SpeciesPrimitive(3 * H0 * H0, 0.0, np.zeros(3)),))
        t = np.linspace(0.0, 0.4, 101)
        a_exact, H_exact = dust_flrw_exact(t, H0)
        for method in ('DOP853', 'Radau'):
            hist = integrate_solve_ivp(state, t, method=method, rtol=1e-11, atol=1e-13)
            self.assertLess(max(abs(x.a - y) for x, y in zip(hist, a_exact)), 1e-9)
            self.assertLess(max(abs(x.H - y) for x, y in zip(hist, H_exact)), 1e-9)

    def test_rk4_step_convergence(self):
        H0 = 0.8
        state = BIState(1.0, H0, np.zeros((3, 3)), (SpeciesPrimitive(3 * H0 * H0, 0.0, np.zeros(3)),))
        errors = []
        steps = []
        for n in (51, 101, 201):
            t = np.linspace(0, 0.4, n)
            h = integrate(state, t)[-1]
            ae, He = dust_flrw_exact(np.array([0.4]), H0)
            errors.append(abs(h.a - ae[0]) + abs(h.H - He[0]))
            steps.append(n - 1)
        # fourth-order RK4: halving the step should drop the error by ~16x.
        slope1 = np.log2(errors[0] / errors[1])
        slope2 = np.log2(errors[1] / errors[2])
        self.assertTrue(3.6 <= slope1 <= 4.4, slope1)
        self.assertTrue(3.6 <= slope2 <= 4.4, slope2)


class BranchGuardTests(unittest.TestCase):
    def test_expanding_branch_guard(self):
        with self.assertRaisesRegex(ValueError, 'H>0'):
            BIState(1.0, -0.1, np.zeros((3, 3)), (SpeciesPrimitive(0.03, 0.0, np.zeros(3)),))


if __name__ == '__main__':
    unittest.main()
