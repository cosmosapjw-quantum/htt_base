"""P6-IR-01 regression source; prepared only, not yet executed.

Exact fixture: A=diag(1,0), E=closed unit ball, J=(0,1), a=1.
Compatibility fixes e_2=z_2; feasible iff z_2**2<=1. If feasible,
theta=(z_1,t), e=(0,z_2) gives arbitrary J theta=t.
This analytic fixture does not validate the full manuscript or a solver.
"""
import unittest
from pathlib import Path


def matvec(matrix, vector):
    return tuple(sum(x*y for x, y in zip(row, vector)) for row in matrix)


def fixture_support(z):
    # Empty-set branch must precede the kernel-visible unbounded branch.
    if z[1]**2 > 1:
        return float("-inf")
    return float("inf")


class FeasibilityRegression(unittest.TestCase):
    A = ((1, 0), (0, 0))
    J = ((0, 1),)

    def test_infeasible_visible_kernel(self):
        self.assertEqual(matvec(self.A, (0, 1)), (0, 0))
        self.assertEqual(matvec(self.J, (0, 1)), (1,))
        z = (0, 2)
        # Every compatible error has e_2=2, so its squared norm is >=4>1.
        self.assertGreater(z[1]**2, 1)
        self.assertEqual(fixture_support(z), float("-inf"))

    def test_feasible_visible_kernel(self):
        z = (0, 0)
        self.assertEqual(fixture_support(z), float("inf"))
        # Any t is allowed analytically; these are exact witness checks only.
        for t in (-10, 0, 10):
            theta = (0, t)
            error = tuple(x-y for x, y in zip(z, matvec(self.A, theta)))
            self.assertLessEqual(sum(x*x for x in error), 1)
            self.assertEqual(matvec(self.J, theta), (t,))

    def test_prepared_sources_carry_domain_and_convention(self):
        root = Path(__file__).resolve().parent / "prepared"
        for relative in ("science/MANUSCRIPT.md", "report/main.tex"):
            text = (root / relative).read_text()
            self.assertIn(r"h_{\varnothing}(a)=-\infty", text)
            self.assertIn(r"If \(\mathcal E_z\ne\varnothing\) and \(J^{\mathsf T}a\)", text)
            self.assertIn(r"choose a feasible \(\theta_0\in\Theta_{\rm lin}(z)\)", text)


if __name__ == "__main__":
    unittest.main()
