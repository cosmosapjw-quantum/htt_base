import importlib.util
from pathlib import Path
import unittest
import numpy as np

PATH=Path(__file__).resolve().parents[2]/'scripts/solver_free_observation_bounds.py'
SPEC=importlib.util.spec_from_file_location('sf_bounds',PATH)
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)


class ObservationBoundsTests(unittest.TestCase):
    def test_bin_derivatives_and_tail(self):
        t=np.array([-.2,.1,.7]);h=1e-5
        k,d,dd=m.gaussian_bin(t,-.1,.4,.2)
        plus=m.gaussian_bin(t+h,-.1,.4,.2);minus=m.gaussian_bin(t-h,-.1,.4,.2)
        np.testing.assert_allclose((plus[0]-minus[0])/(2*h),d,atol=1e-8)
        np.testing.assert_allclose((plus[1]-minus[1])/(2*h),dd,atol=1e-7)
        self.assertGreater(m.gaussian_bin(-10,0,1,1)[0],0)

    def test_normalization_and_zero_mass(self):
        r=m.selected_response([.5,.5],[2,2],[0,0],[.3,.5],[.2,-.1])
        self.assertAlmostEqual(r['response'],0)
        self.assertNotEqual(r['numerator_only'],0)
        with self.assertRaises(ValueError):m.selected_response([1],[1],[0],[0],[0])

    def test_rank_bounds_attained_and_ties(self):
        x=np.array([1.,2.,3.]);r=m.rank_interval(2,x,.2,.3)
        lo=m.rank_interval(2.2,np.maximum(0,x-.3))['p_min']
        hi=m.rank_interval(1.8,x+.3)['p_min']
        self.assertEqual((r['p_min'],r['p_max']),(lo,hi))
        self.assertEqual(m.rank_interval(2,[2])['p_min'],1.)

    def test_underdetermined_rank_and_adversary(self):
        self.assertEqual(m.robust_information([[1,0,0],[0,1,0]],0)['sigma_min'],0)
        r=m.robust_information(np.diag([2,1,.5]),.1,.2)
        self.assertAlmostEqual(r['information_min_lower'],.16/1.2)
        self.assertFalse(m.robust_information(np.diag([2,1,.5]),.5)['robust_full_column_rank'])

    def test_invalid_inputs(self):
        for args in [(0,0,1,0),(0,1,0,1),(np.nan,0,1,1),(1j,0,1,1)]:
            with self.assertRaises(ValueError):m.gaussian_bin(*args)
        with self.assertRaises(ValueError):m.rank_interval(1,[1],-1)


if __name__=='__main__':unittest.main()
