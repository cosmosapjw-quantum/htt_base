"""Small independent normalization and perturbation falsifiers for OBS-04."""
import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('obs04', Path(__file__).resolve().parents[2]/'scripts/obs04_cmb_common_response.py')
obs04 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obs04)


def test_full_sphere_normalization_and_rotation():
    q = np.array([[2.,1.,-.4],[1.,-3.,.2],[-.4,.2,1.]])
    assert obs04.sphere_mean_square(q) == pytest.approx(2*np.sum(q*q)/15, abs=1e-13)
    rotation, _ = np.linalg.qr(np.random.default_rng(42).normal(size=(3,3)))
    assert obs04.sphere_mean_square(rotation@q@rotation.T) == pytest.approx(obs04.sphere_mean_square(q), abs=1e-13)


def test_declared_envelopes_contain_stf_perturbations_and_degeneracy():
    rng = np.random.default_rng(4)
    for q in (np.diag([-2.,1.,1.]), np.zeros((3,3))):
        s = obs04.sensitivity(q, [0,1,3,5])
        for j, radius in enumerate(s['declared_e_Q_uK']):
            for _ in range(20):
                perturb = rng.normal(size=(3,3)); perturb=(perturb+perturb.T)/2
                perturb -= np.eye(3)*np.trace(perturb)/3
                perturb *= radius/max(np.linalg.norm(perturb), 1e-300)
                eigenvalues=np.linalg.eigvalsh(q+perturb)
                assert np.all(eigenvalues >= np.asarray(s['eigenvalue_lower_uK'])[j]-1e-13)
                assert np.all(eigenvalues <= np.asarray(s['eigenvalue_upper_uK'])[j]+1e-13)
                assert s['frobenius_lower_uK'][j]-1e-13 <= np.linalg.norm(q+perturb) <= s['frobenius_upper_uK'][j]+1e-13


@pytest.mark.parametrize('q', [np.eye(3), np.ones((3,2)), np.diag([np.nan,0,0]), [[0,1,0],[0,0,0],[0,0,0]]])
def test_invalid_stf_rejected(q):
    with pytest.raises(ValueError): obs04.sensitivity(q, [1])


@pytest.mark.parametrize('grid', [[],[-1],[float('inf')],[float('nan')],[[1]]])
def test_invalid_radius_rejected(grid):
    with pytest.raises(ValueError): obs04.sensitivity(np.zeros((3,3)), grid)


def test_common_bias_cancellation_and_response_mismatch_survives():
    sky=np.array([2.,-3.]); common_bias=np.array([100.,100.])
    a=np.eye(2); b=2*np.eye(2)
    first=a@sky+common_bias; second=a@sky+common_bias
    np.testing.assert_array_equal(second-first, np.zeros(2))
    assert np.linalg.norm(first-a@sky)>100
    np.testing.assert_array_equal((b@sky+common_bias)-first, (b-a)@sky)
