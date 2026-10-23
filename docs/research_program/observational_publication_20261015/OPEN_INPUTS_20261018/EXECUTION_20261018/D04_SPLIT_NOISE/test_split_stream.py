import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('split_stream', Path(__file__).with_name('split_stream.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_contrast_order_and_common_mode():
    a = np.arange(480, dtype=float).reshape(5, 96)
    expected = np.stack([(a[1]-a[2])/2, (a[3]-a[4])/2,
                         a[0]-(a[1]+a[2])/2, a[0]-(a[3]+a[4])/2])
    np.testing.assert_array_equal(m.contrasts(a), expected)
    np.testing.assert_allclose(m.contrasts(a+12345), expected)


@pytest.mark.parametrize('a', [np.ones((4, 96)), np.full((5, 96), np.nan)])
def test_no_missing_fill(a):
    with pytest.raises(ValueError): m.contrasts(a)


def test_wrong_source_layout():
    from types import SimpleNamespace
    with pytest.raises(ValueError):
        m.validate_hdu(SimpleNamespace(header={'NSIDE': 64}))


def test_actual_compact_cache_and_operator_reproduce():
    import json
    import healpy as hp
    result = json.loads(Path(__file__).with_name('RESULT.json').read_text())
    with np.load(result['external_coarse_cache']['path'], allow_pickle=False) as z:
        maps, st, sp = z['selected_IQU_K_CMB'], z['T_mask'], z['P_mask']
    _, scalar = m.old.pixel_fit_geometry()
    theta, phi = hp.pix2ang(64, np.arange(49152))
    spin = m.old.block_design(theta, phi, 2, 5)
    ot, _ = m.old.linear_projector(scalar, st)
    op, _ = m.old.linear_projector(spin, np.r_[sp, sp])
    direct = np.array([np.r_[(ot@a[0, st])[4:], op@np.r_[a[1, sp], a[2, sp]]] for a in maps])
    with np.load(Path(__file__).with_name('COEFFICIENTS.npz'), allow_pickle=False) as z:
        np.testing.assert_allclose(direct, z['coefficients_K_CMB'][1:], atol=1e-20, rtol=2e-12)
        np.testing.assert_array_equal(z['contrasts_K_CMB'], m.contrasts(z['coefficients_K_CMB']))
        with np.load(m.OLD/'results/PILOT_COEFFICIENTS.npz', allow_pickle=False) as p:
            np.testing.assert_array_equal(z['coefficients_K_CMB'][0], p['component_coefficients_K_CMB'][0, 1])
    assert st.sum() == 26846 and sp.sum() == 30021


def test_one_tuple_not_null_and_fixed_chart():
    import json
    r = json.loads(Path(__file__).with_name('RESULT.json').read_text())
    assert r['null_mock_status'] == 'ONE_NOMINAL_ID_NOT_ENSEMBLE'
    assert r['physical_covariance'] == 'UNKNOWN' and r['inference'] is None
    assert r['L03_original_acceptance'] == 'HOLD'
    assert len(r['source_files']) == 4 and len(r['fixed_L02_morphology']) == 9
    assert r['fixed_weights_intake']['additional_beam_applied'] is False
    assert r['original_chart']['sha256'] == '900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459'
