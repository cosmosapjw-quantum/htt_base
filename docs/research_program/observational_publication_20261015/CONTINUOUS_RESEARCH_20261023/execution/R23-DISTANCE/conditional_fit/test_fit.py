"""Narrow source-bound falsifiers for CONDITIONAL_GLS_V1."""
import importlib.util
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('conditional_fit', HERE / 'fit.py')
fitmod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fitmod)


def test_exact_source_cohort_and_unique_missing_groups():
    ledger, rows, groups, counts = fitmod.load_inputs()
    assert len(ledger) == 628 and len(rows) == 274
    assert counts == [[116,269],[21,1],[26,3],[191,1]]
    assert sum(groups[r['pgc']].startswith('UNASSIGNED_PGC:') for r in rows) == 5
    assert len({groups[r['pgc']] for r in rows if groups[r['pgc']].startswith('UNASSIGNED_PGC:')}) == 5


def test_covariance_single_budget_and_rank():
    _, rows, groups, _ = fitmod.load_inputs()
    m = fitmod.make_model(rows,groups)
    assert m['X'].shape == (274,7)
    assert m['G'].shape == (274,269)
    assert m['a'] == .055 and m['b'] == .29
    np.testing.assert_allclose(np.diag(m['V'])-m['b']**2,m['s']**2,rtol=1e-12,atol=1e-14)
    assert np.all(np.diag(m['L']) > 0)
    assert np.all(m['d'] >= .75*m['s']**2-1e-14)


def test_whitened_gaussian_and_intercept_invariance_fixture():
    # A small independent fixture checks the central algebra without refitting
    # the source cohort or rerunning the 4096-draw experiment.
    V = np.array([[.13,.035],[.035,.19]])
    L = np.linalg.cholesky(V)
    z = np.array([.2,-.3])
    w = np.linalg.solve(L,z)
    np.testing.assert_allclose(w@w,z@np.linalg.solve(V,z),rtol=1e-12)
    X = np.column_stack([np.ones(3),[-1.,0.,1.]])
    y = np.array([2.,2.7,4.1])
    beta = np.linalg.lstsq(X,y,rcond=None)[0]
    shifted = np.linalg.lstsq(X,y+1,rcond=None)[0]
    np.testing.assert_allclose(shifted-beta,[1.,0.],atol=1e-12)
