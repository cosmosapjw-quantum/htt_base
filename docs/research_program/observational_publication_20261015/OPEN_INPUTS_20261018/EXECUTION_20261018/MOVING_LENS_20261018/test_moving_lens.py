"""Narrow falsifiers for the fixed moving-lens source contract."""
import math
import json
from pathlib import Path
from statistics import NormalDist
import unittest
from unittest.mock import patch

from moving_lens import (build_result, compression_falsifier, contrast_interval,
                         extract_source, physical_interval)


class MovingLensTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = extract_source()

    def test_table_source_rows_and_columns(self):
        rows = self.source['individual_extended_combined']
        self.assertEqual([(rows[f'{nu} GHz']['center'], rows[f'{nu} GHz']['sd'])
                          for nu in ['90', '150', '220']],
                         [(.93, .36), (1.14, .32), (3.08, 1.29)])
        self.assertEqual([rows[f'{nu} GHz']['source_row_id'] for nu in ['90', '150', '220']],
                         ['S5.T1.2.8', 'S5.T1.2.12', 'S5.T1.2.16'])
        self.assertTrue(all(rows[f'{nu} GHz']['source_column_1based'] == 7
                            for nu in ['90', '150', '220']))
        nulls = self.source['difference_extended_combined']
        self.assertEqual([nulls[key]['center'] for key in ['150{-}90', '220{-}90', '220{-}150']],
                         [.12, 2.17, 2.02])
        self.assertTrue(all(nulls[key]['source_column_1based'] == 8
                            for key in ['150{-}90', '220{-}90', '220{-}150']))

    def test_vi1_fixed_mask_bin_and_amplitudes(self):
        vi = self.source['vi1']
        self.assertEqual((vi['act150']['center'], vi['act150']['sd']), (1.06, .27))
        self.assertEqual((vi['cib353_to150']['center'], vi['cib353_to150']['sd']), (-.07, .14))
        self.assertEqual((vi['cib545_to150']['center'], vi['cib545_to150']['sd']), (-.01, .10))
        self.assertEqual(vi['conclusion_cib545_to150']['center'], 0.)
        paragraph = self.source['selected_source_extracts']['S6.SS1.p4']
        self.assertIn('GAL060', paragraph)
        self.assertIn(r'\Delta\ell=500', paragraph)
        self.assertIn(r'2000\leq\ell\leq 5000', paragraph)

    def test_source_compression_counterexample_exceeds_all_rounding(self):
        result = compression_falsifier(self.source)
        for row, expected in zip(result, [-.09, .02, .08]):
            self.assertAlmostEqual(row['residual'], expected, places=13)
            self.assertGreater(abs(row['residual']), 3 * .005)
            self.assertTrue(row['shared_scalar_filter_falsified'])

    def test_bonferroni_alpha_allocation(self):
        a, b = self.source['vi1']['act150'], self.source['vi1']['cib545_to150']
        for alpha in [.01, .05, .1]:
            result = contrast_interval(a, b, alpha=alpha)
            marginal_failure = 2 * (1 - NormalDist().cdf(result['q']))
            self.assertAlmostEqual(marginal_failure, alpha/2, places=14)
            self.assertAlmostEqual(2*marginal_failure, alpha, places=14)
            self.assertAlmostEqual(result['interval'][1]-result['center'],
                                   result['q']*(a['sd']+b['sd']), places=14)

    def test_rounding_encloses_all_center_sd_corners(self):
        a, b = self.source['vi1']['act150'], self.source['vi1']['cib545_to150']
        out = contrast_interval(a, b, rounding_step=.01)['interval']
        for ca in [-.005, .005]:
            for cb in [-.005, .005]:
                corner = contrast_interval(dict(center=a['center']+ca, sd=a['sd']+.005),
                                           dict(center=b['center']+cb, sd=b['sd']+.005))['interval']
                self.assertLessEqual(out[0], corner[0]+1e-14)
                self.assertGreaterEqual(out[1], corner[1]-1e-14)

    def test_source_variant_union_contains_both_versions(self):
        result = build_result(self.source)
        union = result['source_variant_union']
        for key in ['outward_rounding_envelope', 'conclusion_variant_envelope']:
            inner = result[key]['interval']
            self.assertLessEqual(union[0], inner[0])
            self.assertGreaterEqual(union[1], inner[1])
        self.assertAlmostEqual(union[0], .1982669635101204, places=13)
        self.assertAlmostEqual(union[1], 1.9317330364898797, places=13)

    def test_monotone_hypothetical_delta_expansion(self):
        previous = [.2, 1.9]
        for delta in [0., .1, .2, .5, 1.]:
            current = physical_interval([.2, 1.9], delta)['interval']
            self.assertLessEqual(current[0], previous[0])
            self.assertGreaterEqual(current[1], previous[1])
            self.assertAlmostEqual(current[1]-current[0], 1.7+2*delta)
            previous = current

    def test_missing_delta_remains_unbounded(self):
        result = physical_interval([.2, 1.9])
        self.assertEqual(result['status'], 'UNBOUNDED')
        self.assertIsNone(result['interval'])
        self.assertEqual(result['endpoints'], ['-infinity', '+infinity'])
        with self.assertRaises(ValueError):
            physical_interval([.2, 1.9], math.nan)

    def test_reject_independence_assumption(self):
        a = self.source['vi1']['act150']
        b = self.source['vi1']['cib545_to150']
        with self.assertRaisesRegex(ValueError, 'Independence is unsupported'):
            contrast_interval(a, b, dependence='independent')

    def test_advanced_head_does_not_change_historical_result(self):
        historical = json.loads((Path(__file__).parent / 'RESULT.json').read_text())
        with patch('moving_lens.subprocess.check_output', return_value='f'*40+'\n') as git:
            reproduced = build_result(self.source)
        git.assert_not_called()
        self.assertEqual(reproduced, historical)
        self.assertEqual(reproduced['git_base_head'],
                         'ad27f4cb5f84dfaccc322e53f2810ad29dc72276')

    def test_requested_runtime_erratum_has_no_scientific_field_changes(self):
        initial = json.loads((Path(__file__).parent / 'RESULT_INITIAL.json').read_text())
        corrected = json.loads((Path(__file__).parent / 'RESULT.json').read_text())
        self.assertEqual(initial['runtime']['requested_model'], 'gpt-6-sol')
        self.assertEqual(corrected['runtime']['requested_model'], 'gpt-6.1-sol')
        initial['runtime']['requested_model'] = corrected['runtime']['requested_model']
        self.assertEqual(initial, corrected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
