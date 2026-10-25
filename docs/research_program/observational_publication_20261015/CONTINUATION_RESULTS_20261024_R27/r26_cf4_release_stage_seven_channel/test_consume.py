"""Small exact falsifiers for the release-stage conditional model; run after actual ACK."""
from __future__ import annotations

from fractions import Fraction as F
import unittest

import numpy as np

from consume import (WIDTHS, classify, identify_singletons, intersect, difference,
                     midpoint, nominal_map, precision_extreme, _at_total)


def row(pgc=1, methods=None, dmav='', e_dmav='', dmzp='', dmcal='', count_fp=''):
    return {'pgc': pgc, 'line': pgc, 'methods': methods or [('', '')]*6,
            'dmav': dmav, 'e_dmav': e_dmav, 'dmzp': dmzp,
            'dmcal': dmcal, 'count_fp': count_fp}


def singleton(j, pgc, method='35.000', error='.200', av='35.000', zp='34.850'):
    methods = [('', '')]*6
    methods[j] = (method, error)
    return row(pgc, methods, av, error, zp)


class ReleaseStageTest(unittest.TestCase):
    def test_singleton_joint_reduction_and_fixed_reference(self):
        rows = [singleton(j, j+1, av='35.000' if j == 0 else '35.100',
                          zp='34.850' if j == 0 else '34.950') for j in range(6)]
        for width in WIDTHS.values():
            got = identify_singletons(rows, width)
            self.assertEqual(got['status'], 'SINGLETON_JOINT_FEASIBLE')
            self.assertEqual(got['training_count'], 6)
            self.assertEqual(F(got['delta_star'][0]), 0)
            self.assertEqual(F(got['zeta_star']), F('.150'))
            self.assertEqual([F(x) for x in got['delta_star'][1:]], [F('.100')]*5)
            self.assertLessEqual(F(got['Zstar'][0]), F(got['Zstar'][1]))
        bad = rows.copy()
        bad[0] = singleton(0, 1, av='35.100', zp='34.950')
        self.assertEqual(identify_singletons(bad, F(1, 2))['status'],
                         'FIXED_SNIA_REFERENCE_INCOMPATIBLE')

    def test_joint_interval_pairwise_difference_and_empty_global(self):
        # D, H, Z can be individually nonempty while no common (delta,zeta) exists.
        d, h, z = (F(0), F(0)), (F(0), F(0)), (F(1), F(1))
        zstar = intersect(z, (d[0]-h[1], d[1]-h[0]))
        self.assertGreater(zstar[0], zstar[1])
        self.assertEqual(difference((F(2), F(3)), (F(4), F(5))), (F(-3), F(-1)))
        self.assertEqual(midpoint((F(1), F(2))), F(3, 2))
        rows = [singleton(j, j+1) for j in range(5)]
        self.assertEqual(identify_singletons(rows, F(1, 2))['status'], 'NO_SINGLETON_CHANNEL')

    def test_error_interval_rejection(self):
        rows = [singleton(j, j+1) for j in range(6)]
        rows[2] = singleton(2, 3, error='.200', av='35.000', zp='34.850')
        rows[2]['e_dmav'] = '.300'
        result = identify_singletons(rows, F(1, 2))
        self.assertEqual(result['status'], 'SINGLETON_ERROR_INCOMPATIBLE')
        self.assertEqual(result['witness'], 3)

    def test_mixed_joint_mean_error_and_valid_witness(self):
        methods = [('', '')]*6
        methods[0] = ('30.000', '1.0')
        methods[1] = ('32.000', '1.0')
        bad = row(methods=methods, dmav='31.100', e_dmav='.742', dmzp='31.100')
        offsets = (F(0), F(0), F(0), F(0), F(0), F(0))
        got = classify(bad, F(1, 2), offsets, F(0))
        self.assertEqual(got['status'], 'JOINT_MEAN_ERROR_INCOMPATIBLE')
        self.assertGreater(got['possible_mean_interval'][1], F(31))
        good = row(methods=methods, dmav='31.000', e_dmav='.707', dmzp='31.000')
        got = classify(good, F(1, 2), offsets, F(0))
        self.assertEqual(got['status'], 'JOINT_COMPATIBLE')
        q, m = got['witness_q'], got['witness_m']
        self.assertEqual(sum(a*b for a, b in zip(q, m))/sum(q), got['witness_mean'])
        self.assertTrue(got['total_precision_interval'][0] <= sum(q) <= got['total_precision_interval'][1])

    def test_order_invariance_and_direct_channel(self):
        lo, hi, values = [F(1), F(2), F(3)], [F(3), F(4), F(5)], [F(12), F(9), F(15)]
        order = [2, 0, 1]
        self.assertEqual(precision_extreme(lo, hi, values, F(8), F(9), False)[0],
                         precision_extreme([lo[i] for i in order], [hi[i] for i in order],
                                           [values[i] for i in order], F(8), F(9), False)[0])
        self.assertEqual(_at_total([F(1)]*2, [F(3)]*2, [F(0), F(2)], F(3), False)[0], F(2, 3))
        samples = [singleton(j, j+1) for j in range(6)]
        a = identify_singletons(samples, F(1, 2))
        b = identify_singletons(samples[::-1], F(1, 2))
        self.assertEqual(a['delta_star'], b['delta_star'])
        direct = row(dmcal='33.000', dmzp='33.000')
        self.assertEqual(classify(direct, F(1, 2), (F(0),)*6, F(0))['status'],
                         'DIRECT_CALIBRATOR_COMPATIBLE')
        self.assertEqual(nominal_map(direct).tolist(), [0, 0, 0, 0, 0, 0, 1])

    def test_seven_shift_cancels_but_six_only_need_not(self):
        # A direct row has a complete seventh channel.  N contains an intercept.
        A = np.vstack([np.eye(7), np.eye(7)])
        self.assertTrue(np.all(A.sum(axis=1) == 1))
        Q = np.ones((14, 1))/np.sqrt(14.)
        B = np.arange(14., dtype=float).reshape(-1, 1)
        PB = B-Q@(Q.T@B)
        PA = A-Q@(Q.T@A)
        M = np.linalg.solve(PB.T@PB, PB.T@PA)
        np.testing.assert_allclose(M@np.ones(7), 0, atol=1e-12)
        self.assertGreater(abs((M[:, :6]@np.ones(6))[0]), 1e-12)


if __name__ == '__main__':
    unittest.main()
