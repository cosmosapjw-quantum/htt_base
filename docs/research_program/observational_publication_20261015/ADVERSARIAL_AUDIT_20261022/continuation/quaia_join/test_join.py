import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('a22_join', Path(__file__).with_name('join.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_integer_join_beyond_double_precision():
    a = np.array([9007199254740992, 9007199254740993, 9007199254740995], dtype=np.int64)
    dst, src = m.exact_indices(a, a[[2, 0]])
    assert dst.tolist() == [2, 0] and src.tolist() == [0, 1]
    dst, src = m.exact_indices(a, np.array([9007199254740994], dtype=np.int64))
    assert len(dst) == len(src) == 0


def test_invalid_identity_inputs():
    for a in [np.array([1., 2.]), np.array([1, 1]), np.array([2, 1])]:
        with pytest.raises(ValueError):
            m.exact_indices(a, np.array([1]))


def test_icrs_ring_map_geometry():
    import healpy as hp
    ra = np.array([0., 73., 201.])
    dec = np.array([-45., 10., 79.])
    pix = m.selection_pixels(ra, dec)
    assert np.array_equal(pix, hp.ang2pix(64, np.deg2rad(90-dec), np.deg2rad(ra), nest=False))
    assert not np.array_equal(pix, hp.ang2pix(64, ra, dec, lonlat=True, nest=True))


def test_pm_unit_and_positive_covariance():
    sa, sd, rho = .4, .8, -.6
    cov = np.array([[sa*sa, rho*sa*sd], [rho*sa*sd, sd*sd]])
    assert np.linalg.eigvalsh(cov).min() > 0
    np.testing.assert_allclose(cov * 1e6, np.array([[400**2, rho*400*800], [rho*400*800, 800**2]]), atol=0, rtol=1e-15)


def test_supplement_rejects_masked_or_incomplete_covariance():
    import sys
    from astropy.table import Table, MaskedColumn
    sys.modules['join'] = m
    spec = importlib.util.spec_from_file_location('a22_subset', Path(__file__).with_name('supplement.py'))
    s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
    table = Table({'source_id': [11, 12], 'pmra_pmdec_corr': [.1, -.2],
                   'ruwe': [1., 1.1], 'astrometric_params_solved': [31, 95]})
    assert s.validate_subset(table, np.array([11, 12])).tolist() == [11, 12]
    with pytest.raises(ValueError):s.validate_subset(table, np.array([11, 13]))
    table.replace_column('pmra_pmdec_corr', MaskedColumn([.1, -.2], mask=[False, True]))
    with pytest.raises(ValueError):s.validate_subset(table, np.array([11, 12]))


def test_completed_local_subset_survives_uws_outage(tmp_path, monkeypatch):
    import sys
    sys.modules['join'] = m
    spec = importlib.util.spec_from_file_location('a22_subset_offline', Path(__file__).with_name('supplement.py'))
    s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)
    target = tmp_path/'cached.vot';target.write_bytes(b'cached')
    def unavailable(*args, **kwargs):raise ConnectionError('injected UWS outage')
    monkeypatch.setattr(s,'request',unavailable)
    assert s.refresh_status({'phase':'COMPLETED','sha256':'bound'},target,True) is None
    with pytest.raises(ConnectionError):s.refresh_status({'job_url':'unused'},tmp_path/'absent',True)
