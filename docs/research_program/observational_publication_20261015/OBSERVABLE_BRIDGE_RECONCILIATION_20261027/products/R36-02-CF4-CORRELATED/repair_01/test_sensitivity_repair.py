"""Regression for the R36-02 SAME02 matched-radius cache summary."""
from __future__ import annotations

import json

import numpy as np

import run_sensitivity as repair


def test_distinct_radius_identity_subset():
    full = np.zeros((108, 108))
    for ir, scale in enumerate((1., 2., 4.)):
        sl = slice(36*ir, 36*(ir+1))
        full[sl, sl] = np.eye(36)*scale
    rows = repair.matched_radius_summary(full, full.copy())
    assert [row['trace'] for row in rows] == [36., 72., 144.]
    assert [row['trace_ratio_to_full_sample'] for row in rows] == [1., 1., 1.]
    assert [row['frobenius_relative_to_full_sample'] for row in rows] == [0., 0., 0.]


def test_all_twelve_retained_matched_radius_summaries():
    repair.source_cache_check()
    full, subsets = repair.cache_matrices()
    fixed = json.loads((repair.HERE/'SENSITIVITY.json').read_text())
    old = json.loads((repair.BASE/'SENSITIVITY.json').read_text())
    assert set(subsets) == set(fixed['results']) == set(repair.CASES)
    for name in repair.CASES:
        actual = fixed['results'][name]['bands_sum_blocks']
        assert len(actual) == 3
        for ir, row in enumerate(actual):
            sl = slice(36*ir, 36*(ir+1))
            sub = subsets[name][sl, sl]
            matched = full[sl, sl]
            np.testing.assert_allclose(row['trace_ratio_to_full_sample'],
                np.trace(sub)/np.trace(matched), rtol=0, atol=1e-14)
            np.testing.assert_allclose(row['frobenius_relative_to_full_sample'],
                np.linalg.norm(sub-matched)/np.linalg.norm(matched), rtol=0, atol=1e-14)
            assert row['trace'] == old['results'][name]['bands_sum_blocks'][ir]['trace']
            assert row['rank_1e_10'] == old['results'][name]['bands_sum_blocks'][ir]['rank_1e_10']
            if ir == 0:
                assert row == old['results'][name]['bands_sum_blocks'][ir]
    fp20 = fixed['results']['exclude_FP']['bands_sum_blocks'][2]
    np.testing.assert_allclose(fp20['trace_ratio_to_full_sample'],
        1.1710463175169397, rtol=0, atol=1e-13)
    np.testing.assert_allclose(fp20['frobenius_relative_to_full_sample'],
        .35610037450194054, rtol=0, atol=1e-13)


def test_non_summary_results_unchanged():
    old = json.loads((repair.BASE/'RESULT.json').read_text())
    new = json.loads((repair.HERE/'RESULT.json').read_text())
    assert new.pop('repair')['retained_covariances_unchanged'] is True
    assert new.pop('footprint_method_sensitivity') == 'SENSITIVITY.json'
    assert old.pop('footprint_method_sensitivity') == 'SENSITIVITY.json'
    assert new == old
    assert repair.sha256(repair.BASE/'ARTIFACT_MANIFEST.json') == repair.BASE_CANDIDATE
