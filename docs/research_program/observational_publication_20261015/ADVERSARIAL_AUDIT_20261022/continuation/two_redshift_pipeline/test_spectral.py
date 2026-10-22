import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec=importlib.util.spec_from_file_location('a22_spectral',Path(__file__).with_name('spectral.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_finite_refit_and_transport_negative_controls():
    case=m.run_case(.08,np.eye(3)[0])
    assert case['checks']['amplitude_mag'] < 1e-8
    assert min(case['negative_controls'].values()) > 1e-3
    assert np.ptp(case['raw_band_kappa_mag']) > .001


def test_blueshift_and_domain():
    assert m.run_case(.02,np.eye(3)[0])['zHEL_transformed'] < 0
    with pytest.raises(ValueError):m.flux(0,500,-1,m.P0)
    with pytest.raises(ValueError):m.spectrum(0,249,.35,.08)
    with pytest.raises(ValueError):m.doppler([1,0,0],[1,0,0])


def test_radial_bound_and_collinear_limit():
    b=.1; q=np.linspace(-b,b,31);r=m.radial_ratio(b,q)
    assert np.min(r) >= 1-1e-15
    assert np.max(r) <= 1/np.sqrt(1-b*b)+1e-15
    np.testing.assert_allclose(m.radial_ratio(b,np.array([-b,b])),1,rtol=1e-15,atol=0)


def test_no_boost_identity():
    assert m.doppler(np.eye(3)[0],np.zeros(3)) == 1
    assert m.radial_ratio(0,0) == 1
