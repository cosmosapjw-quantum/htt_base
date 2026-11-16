"""R54-L03 count-dipole helpers (htt/htt/htt/infer/r54_counts.py): R54-EQ-32 body, Poisson dipole fit, gate MG-L04.

MG-L04  the mask identity of data and mocks: a different latitude cut must change the hash.
"""
from __future__ import annotations

import math

import healpy as hp
import numpy as np
import pytest

from htt.htt.infer import r54_counts as ct


def test_growth_factor_limits():
    d = ct.growth_factor(np.array([0.0, 1.0, 50.0]), 0.3153)
    assert d[0] == pytest.approx(1.0) and 0.55 < d[1] < 0.65
    assert d[2] * 51.0 == pytest.approx(ct.growth_factor(np.array([60.0]), 0.3153)[0] * 61.0, rel=2e-2)   # D ~ a in matter domination
    with pytest.raises(ValueError):
        ct.growth_factor(np.array([-0.1]), 0.3)


def test_ho_nz_is_normalised_and_eq32_variance_scales_with_bias_squared():
    z = np.linspace(0.0, 8.0, 4001)
    assert np.trapezoid(ct.ho_nz(z, 0.79, 1.18), z) == pytest.approx(1.0, rel=1e-3)   # trapezoid error at the z^alpha cusp
    k = np.geomspace(1e-4, 0.5, 300)
    pk = 2.0e4 * (k / 0.02) / (1.0 + (k / 0.02) ** 2.5)
    nz = ct.ho_nz(z, 0.79, 1.18)
    c1 = ct.dipole_clustering_cl1(k, pk, z, nz, lambda zz: np.full_like(zz, 1.0), 0.3153, 67.36)
    c2 = ct.dipole_clustering_cl1(k, pk, z, nz, lambda zz: np.full_like(zz, 2.0), 0.3153, 67.36)
    assert c1 > 0 and c2 == pytest.approx(4.0 * c1, rel=1e-12)
    assert ct.dipole_axis_variance(c1) == pytest.approx(3.0 * c1 / (4.0 * math.pi))
    c_cut = ct.dipole_clustering_cl1(k, pk, z, nz, lambda zz: np.full_like(zz, 1.0), 0.3153, 67.36, z_min=0.03)
    assert c_cut != c1


def test_poisson_dipole_fit_recovers_an_injected_dipole():
    ns = 16
    pv = np.array(hp.pix2vec(ns, np.arange(hp.nside2npix(ns)))).T
    d_true = np.array([0.02, -0.01, 0.03])
    rng = np.random.default_rng(20261116)
    expect = np.where(np.abs(pv[:, 2]) > 0.2, 1.0, 0.0)
    counts = rng.poisson(5000.0 * expect * (1.0 + pv @ d_true)).astype(float)
    fit = ct.poisson_dipole_fit(counts, expect, pv)
    sd = np.sqrt(np.diag(fit["cov_D"]))
    assert np.all(np.abs(fit["D_icrs"] - d_true) < 4.0 * sd) and np.all(sd < 0.003)


def test_mg_l04_mask_hash_distinguishes_latitude_cuts():
    ns = 32
    b = 90.0 - np.degrees(hp.pix2ang(ns, np.arange(hp.nside2npix(ns)))[0])
    assert ct.mask_hash(np.abs(b) > 30.0) == ct.mask_hash(np.abs(b) > 30.0)
    assert ct.mask_hash(np.abs(b) > 30.0) != ct.mask_hash(np.abs(b) > 20.0)
