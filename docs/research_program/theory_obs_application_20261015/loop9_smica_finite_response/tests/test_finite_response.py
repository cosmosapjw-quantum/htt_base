"""Numerical falsifiers for the finite selected-pixel harmonic operator."""
from __future__ import annotations

import sys
from pathlib import Path

import healpy as hp
import numpy as np
import pytest
from scipy.linalg import lstsq

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "htt"))
sys.path.insert(0, str(ROOT / "htt/src"))

from finite_response import fit_response, fit_vector, injection_checks
from obsstat.r7_cmb_product_response import real_design


@pytest.fixture(scope="module")
def geometry():
    nside = 16
    directions = np.column_stack(hp.pix2vec(nside, np.arange(hp.nside2npix(nside))))
    y = real_design(directions, ell_max=16)
    selected = np.ones(len(y), dtype=bool)
    selected[::5] = False
    return directions, y, selected


def test_real_harmonic_order_sign_and_full_sky_normalization(geometry):
    n, y, _ = geometry
    c = np.sqrt(3 / (4 * np.pi))
    np.testing.assert_allclose(y[:, 0], 1 / np.sqrt(4 * np.pi), atol=1e-14)
    np.testing.assert_allclose(y[:, 1], c * n[:, 2], atol=1e-14)
    np.testing.assert_allclose(y[:, 2], -c * n[:, 0], atol=1e-14)
    np.testing.assert_allclose(y[:, 3], -c * n[:, 1], atol=1e-14)
    # Equal-area HEALPix sum approximates continuum orthonormality.
    gram = y[:, :36].T @ y[:, :36] * (4 * np.pi / len(y))
    assert np.max(abs(gram - np.eye(36))) < 4e-3


def test_unit_and_random_injection_match_independent_lstsq(geometry):
    _, y, selected = geometry
    r = fit_response(y, selected, 5)
    assert r["K_full_fit"].shape == (36, 253)
    assert r["K_ell23"].shape == (12, 253)
    assert r["K_ell2to5"].shape == (32, 253)
    checks = injection_checks(r, seed=1729)
    assert checks["bound_holds"]
    rng = np.random.default_rng(10)
    a = rng.normal(size=253)
    predicted = r["K_full_fit"] @ a
    independently = lstsq(r["low_design"], r["high_design"] @ a,
                          check_finite=False)[0]
    np.testing.assert_allclose(predicted, independently, rtol=0, atol=2e-12)
    assert np.linalg.norm(predicted) <= np.linalg.norm(r["K_full_fit"], 2) * np.linalg.norm(a) * (1+1e-12)


def test_fitted_high_shell_is_removed_but_unfitted_shell_leaks(geometry):
    _, y, selected = geometry
    r = fit_response(y, selected, 8)
    # Included ell6..8 modes are recovered in their own rows, while their
    # leakage into the retained ell2..5 rows is numerical zero.
    np.testing.assert_allclose(r["K_full_fit"][36:81, :81-36], np.eye(45), atol=1e-11)
    assert np.max(abs(r["K_ell2to5"][:, :81-36])) < 1e-11
    assert np.linalg.norm(r["K_ell2to5"][:, 81-36:]) > 1e-4
    assert r["condition"] < 1e6


def test_seed_and_selection_are_deterministic(geometry):
    _, y, selected = geometry
    a = fit_response(y, selected, 5)
    b = fit_response(y, selected.copy(), 5)
    np.testing.assert_array_equal(a["K_full_fit"], b["K_full_fit"])
    assert injection_checks(a, 7) == injection_checks(b, 7)


def test_invalid_design_or_pixel_values_fail_closed(geometry):
    _, y, selected = geometry
    with pytest.raises(ValueError):
        fit_response(y[:, :36], selected)
    broken = y.copy(); broken[0, 0] = np.nan
    selected[0] = True
    with pytest.raises(ValueError):
        fit_response(broken, selected)
    selected[0] = False
    r = fit_response(y, selected)
    with pytest.raises(ValueError):
        fit_vector(r, np.zeros(r["n_selected"] - 1))
