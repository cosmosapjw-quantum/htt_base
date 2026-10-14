"""Finite linear-algebra tests for Gaia fixed-cohort sensitivity consumer."""
import hashlib
import importlib.util
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
SPEC = importlib.util.spec_from_file_location('gaia_bias', ROOT / 'scripts/run_reboot_gaia_bias_sensitivity.py')
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def fixture():
    ra = np.array([0., 90., 210.])
    dec = np.array([0., 15., 45.])
    x = mod.design(ra, dec)
    y = np.array([[.01, -.02], [.04, .005], [-.01, .03]])
    c = np.array([[[.04, .006], [.006, .09]],
                  [[.16, -.02], [-.02, .25]],
                  [[.06, .01], [.01, .13]]])
    return x, y, c


def dense_blocks(c):
    n = len(c)
    out = np.zeros((2*n, 2*n))
    for i in range(n):
        out[2*i:2*i+2, 2*i:2*i+2] = c[i]
    return out


def test_dense_three_source_geometry_and_attainment():
    x, y, c = fixture()
    assert np.linalg.matrix_rank(x.reshape(-1, 6)) == 6
    assert np.linalg.cond(x.reshape(-1, 6)) == pytest.approx(2.502, rel=.01)
    fit = mod.influence(x, y, c)
    bigc = dense_blocks(c)
    bigq = np.linalg.inv(bigc)
    xx = x.reshape(-1, 6)
    dense_m = np.linalg.solve(xx.T @ bigq @ xx, xx.T @ bigq)
    np.testing.assert_allclose(fit['M'].reshape(6, -1), dense_m, rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(fit['V'], dense_m @ bigc @ dense_m.T, rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(fit['V'], fit['K'] @ fit['K'].T, rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(fit['M'].reshape(6, -1) @ xx, np.eye(6), atol=1e-12)
    assert mod.verify_support_attainment(fit, rho=2.3, box_mas=.017) < 1e-12
    sigma, ell, box = mod.support(fit, rho=(0, 1.7), box_microas=(0, 13))
    np.testing.assert_allclose(ell[1], 1.7*sigma)
    np.testing.assert_allclose(box[1], .013*np.abs(dense_m).sum(axis=1))


def test_precision_physical_scale_and_units():
    x, y, c = fixture()
    fit = mod.influence(x, y, c)
    for alpha in (.25, 4.):
        altered = mod.influence(x, y, c, precision_scale=alpha)
        np.testing.assert_allclose(altered['M'], fit['M'], rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose(altered['V'], fit['V'], rtol=1e-10, atol=1e-12)
    for s in (2., 4.):
        altered = mod.influence(x, y, s*s*c)
        np.testing.assert_allclose(altered['M'], fit['M'], rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose(altered['V'], s*s*fit['V'], rtol=1e-10, atol=1e-12)
        s0, e0, b0 = mod.support(fit)
        ss, es, bs = mod.support(altered)
        np.testing.assert_allclose(ss, s*s0)
        np.testing.assert_allclose(es, s*e0)
        np.testing.assert_allclose(bs, b0)
    micro = mod.influence(x, y*1000, c*1e6)
    np.testing.assert_allclose(micro['M'], fit['M'], rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(micro['V'], fit['V']*1e6, rtol=1e-10, atol=1e-8)
    s0, e0, b0 = mod.support(fit)
    sm, em, bm = mod.support(micro, box_microas=tuple(1000*b for b in mod.BOX_MICROAS))
    np.testing.assert_allclose(sm, 1000*s0)
    np.testing.assert_allclose(em, 1000*e0)
    np.testing.assert_allclose(bm, 1000*b0)


def test_frozen_baseline_source_parity():
    ids, x, y, c, saved, path = mod.load_frozen()
    fit = mod.influence(x, y, c)
    assert len(ids) == 4756
    assert hashlib.sha256((mod.SOURCE/'qualified_rows.npz').read_bytes()).hexdigest() == mod.EXPECTED_NPZ_SHA256
    np.testing.assert_allclose(fit['coefficients'], saved['full_fit']['coefficients_mas_yr'], atol=1e-12, rtol=0)
    assert mod.relative_error(fit['V'], saved['full_fit']['covariance_mas2_yr2']) < 1e-10
    assert mod.verify_support_attainment(fit) < 1e-12


@pytest.mark.parametrize('field', ['x', 'y', 'c'])
def test_reject_complex_or_nonfinite(field):
    x, y, c = fixture()
    data = {'x': x.copy(), 'y': y.copy(), 'c': c.copy()}
    data[field] = data[field].astype(complex)
    data[field].flat[0] += 1j
    with pytest.raises(ValueError):
        mod.influence(**data)
    data = {'x': x.copy(), 'y': y.copy(), 'c': c.copy()}
    data[field].flat[0] = np.nan
    with pytest.raises(ValueError):
        mod.influence(**data)


def test_reject_nonsymmetric_or_non_spd_and_bad_scale():
    x, y, c = fixture()
    bad = c.copy(); bad[0, 0, 1] += .01
    with pytest.raises(ValueError): mod.influence(x, y, bad)
    bad = c.copy(); bad[0, 0, 0] = -1
    with pytest.raises(np.linalg.LinAlgError): mod.influence(x, y, bad)
    with pytest.raises(ValueError): mod.influence(x, y, c, precision_scale=0)


def test_archived_r1_three_source_prototype_parity():
    source = mod.verify_r1_identity()
    r1 = types.ModuleType('archived_r1_observational_linear_core')
    sys.modules[r1.__name__] = r1
    exec(compile(source, mod.R1_MEMBER, 'exec'), r1.__dict__)
    x, y, c = fixture()
    xx = x.reshape(-1, 6)
    bigc = dense_blocks(c)  # six by six fixture only
    bigq = np.linalg.inv(bigc)
    fit = mod.influence(x, y, c)
    prototype = r1.fixed_design_gls(xx, bigc)
    np.testing.assert_allclose(prototype.matrix, fit['M'].reshape(6, -1), rtol=1e-10, atol=1e-12)
    np.testing.assert_allclose(prototype.covariance, fit['V'], rtol=1e-10, atol=1e-12)
    for alpha in (.25, 4.):
        weighted_m, weighted_v = r1.weighted_linear_map(xx, alpha*bigq, bigc)
        np.testing.assert_allclose(weighted_m, fit['M'].reshape(6, -1), rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose(weighted_v, fit['V'], rtol=1e-10, atol=1e-12)
    l = np.linalg.cholesky(bigc)
    for j in range(6):
        row = fit['M'].reshape(6, -1)[j]
        assert r1.box_bias(row, np.full(6, .013)) == pytest.approx(.013*np.abs(row).sum(), rel=1e-12)
        assert r1.ellipsoid_bias(row, l, 1.7) == pytest.approx(1.7*np.sqrt(fit['V'][j, j]), rel=1e-12)


def test_zero_budget_witnesses_and_whitened_norm():
    x, y, c = fixture()
    fit = mod.influence(x, y, c)
    zero = mod.verify_support_attainment(fit, rho=0., box_mas=0., diagnostics=True)
    assert zero == {'ellipsoid_shift_max_abs_mas_year': 0.,
                    'whitened_norm_max_abs': 0.,
                    'box_shift_max_abs_mas_year': 0.}
    positive = mod.verify_support_attainment(fit, rho=2.3, box_mas=.017, diagnostics=True)
    assert positive['whitened_norm_max_abs'] < 1e-12
    assert positive['ellipsoid_shift_max_abs_mas_year'] < 1e-12
    assert positive['box_shift_max_abs_mas_year'] < 1e-12
