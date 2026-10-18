from pathlib import Path
import importlib.util
import sys

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('shoes_ladder_local',Path(__file__).with_name('ladder.py'))
ladder = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ladder
spec.loader.exec_module(ladder)


@pytest.fixture(scope='module')
def actual():
    return ladder.load_actual()[:3]


def test_orientation_rejection(actual):
    L,y,C = actual
    with pytest.raises(ValueError,match='orientation'):
        ladder.validate_layout(L.T,y,C,ladder.named_intervals())


def test_all_named_actual_intervals_and_constraints(actual):
    L,y,C = actual
    witness = ladder.validate_layout(L,y,C,ladder.named_intervals())
    assert witness['all_37_named_supports_exact']
    assert witness['constraint_selectors_zero_based'] == [38,38,43,44,45,41,37,39]


def test_wrong_named_interval_rejected(actual):
    L,y,C = actual
    mapping = ladder.named_intervals()
    mapping['M101'],mapping['M1337'] = mapping['M1337'],mapping['M101']
    with pytest.raises(ValueError,match='named Table 3 interval mismatch'):
        ladder.validate_layout(L,y,C,mapping)


def test_actual_dummy_variance_not_sigma(actual):
    C = actual[2]
    ladder.validate_dummy(C)
    assert np.isclose(np.sqrt(C[3210,3210]),np.sqrt(1e-9))
    mutated = C.copy()
    mutated[3210,3210] = np.sqrt(C[3210,3210])
    with pytest.raises(ValueError,match='variance'):
        ladder.validate_dummy(mutated)
    mutated[3210,3210] = C[3210,3210]
    mutated[3210,0] = 1e-12
    with pytest.raises(ValueError,match='offdiagonal'):
        ladder.validate_dummy(mutated)


def test_qr_svd_with_correlated_covariance_and_column_scaling():
    rng = np.random.default_rng(312)
    A = rng.normal(size=(23,4))*np.array([1e-3,1,4,1e3])
    T = rng.normal(size=(23,23))
    C = T@T.T+np.eye(23)
    y = A@np.array([3.,2.,-1.,.5])+rng.normal(size=23)*.01
    q,V,qsvd,checks = ladder.solve_gls(A,y,C)
    # Separate normal-equation oracle is safe only in this small fixture.
    expected = np.linalg.solve(A.T@np.linalg.solve(C,A),A.T@np.linalg.solve(C,y))
    np.testing.assert_allclose(q,expected,rtol=1e-9,atol=1e-9)
    np.testing.assert_allclose(q,qsvd,rtol=1e-8,atol=1e-8)
    np.testing.assert_allclose(V@ (A.T@np.linalg.solve(C,A)),np.eye(4),rtol=1e-7,atol=1e-7)
    assert checks['rank'] == 4


def test_common_host_offset_invariance():
    rng = np.random.default_rng(52)
    R = rng.normal(size=(37,37))
    V = R@R.T+.2*np.eye(37)
    q = rng.normal(size=37)+32
    centered,cov,eigenvalues,rank,checks = ladder.project_hosts(q,V)
    shifted,cov2,*_ = ladder.project_hosts(q+8.,V)
    np.testing.assert_allclose(centered,shifted,atol=1e-12)
    np.testing.assert_array_equal(cov,cov2)
    assert rank == 36
    assert abs(eigenvalues[0]) < 1e-10


def test_actual_saved_covariance_and_reproduction():
    path = Path(__file__).with_name('HOST_COVARIANCE.npz')
    with np.load(path) as bundle:
        assert bundle['q'].shape == (47,)
        assert bundle['covariance'].shape == (47,47)
        assert bundle['host_names'].tolist() == ladder.HOSTS
        np.testing.assert_allclose(bundle['q'],bundle['q_svd'],rtol=1e-8,atol=1e-10)
        assert np.linalg.matrix_rank(bundle['centered_host_covariance']) == 36

