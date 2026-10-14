import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('reboot_id', Path(__file__).parents[1]/'scripts/analyze_reboot_identifiability.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_exact_profile_information_and_units():
    b=np.ones((3,1)); g=np.arange(3.)[:,None]; c=np.diag([1.,4.,9.])
    expected=np.array([[26/49]])
    assert np.allclose(mod.information(g,b,c),expected,rtol=1e-13,atol=1e-14)
    # Consistent observable-unit conversion must preserve information.
    assert np.allclose(mod.information(g*1000,b*1000,c*1e6),expected,rtol=1e-13)
    assert np.allclose(mod.information(g+100*b,b,c),expected,rtol=1e-12)
    assert np.allclose(mod.information(g,1e-12*b,c),expected,rtol=1e-13)
    assert np.allclose(mod.information(g,np.zeros_like(b),c),g.T@np.linalg.solve(c,g),rtol=1e-13)


def test_response_null_and_degeneracy():
    r=mod.laboratory()
    assert [c['rank'] for c in r['cases']]==[0,3,0]
    first,last=r['near_degeneracy'][0],r['near_degeneracy'][-1]
    assert first['minimum_singular_value']/last['minimum_singular_value']==pytest.approx(1e-5,rel=1e-9)
    assert r['null_status']=='NO_OBSERVED_HYPOTHESIS_TEST'


@pytest.mark.parametrize('cov',[np.array([[1.,2.],[0.,1.]]),np.array([[1.,0.],[0.,-1.]])])
def test_reject_wrong_covariance(cov):
    with pytest.raises((ValueError,np.linalg.LinAlgError)):
        mod.information(np.ones((2,1)),np.ones((2,1)),cov)
