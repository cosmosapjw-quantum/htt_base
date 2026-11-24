"""R108 S6: the harmonic kernel of the R105 masked ell=2 fit equals the direct pixel fit.

Synthetic Nside 16 sky, random mask, R105 design() columns: the kernel prediction
(map2alm iter=0 / map2alm_spin of masked columns, conjugate inner products over all m)
must reproduce the direct normal-equation fit of a band-limited T, Q, U field.
"""

from __future__ import annotations

import healpy as hp
import numpy as np
import pytest

from scripts.r105.commander_transfer import design
from scripts.r108.commander_splits import SPLITS, _HttpsOnly, products
from scripts.r108.s6_b03_templates import coefficients, orientations


def test_kernel_prediction_matches_direct_masked_fit():
    ns, lmax = 16, 24
    npix = hp.nside2npix(ns)
    rng = np.random.default_rng(7)
    mask_t = (rng.random(npix) > 0.3).astype(float)
    mask_p = (rng.random(npix) > 0.4).astype(float)
    response = np.array([0.97, 0.95])
    S, P = design(*hp.pix2ang(ns, np.arange(npix)), response)
    gT = S.T @ (S * mask_t[:, None])
    gP = P.conj().T @ (P * mask_p[:, None])
    kT = np.array([hp.map2alm(S[:, c] * mask_t, lmax=lmax, iter=0) for c in range(9)])
    kP = np.array([np.stack(hp.map2alm_spin([(P[:, c] * mask_p).real.copy(), (P[:, c] * mask_p).imag.copy()], 2,
                                            lmax=lmax)) for c in range(5)])
    np.random.seed(11)
    cl = 1.0 / (np.arange(lmax + 1) + 1.0) ** 2
    alms = hp.synalm([cl, cl, cl, 0 * cl, 0 * cl, 0 * cl], lmax=lmax, new=True)
    t, q, u = hp.alm2map(alms, ns, lmax=lmax, pol=True)
    cp = np.linalg.solve(gP, P.conj().T @ (mask_p * (q + 1j * u)))
    direct = np.stack([np.linalg.solve(gT, S.T @ (mask_t * t))[4:], cp.real, cp.imag])
    pred = coefficients(alms, kT, kP, gT, gP, npix)
    assert np.max(np.abs(pred - direct)) <= 1e-10 * np.max(np.abs(direct))


def test_orientation_basis_and_split_product_names():
    from urllib.request import Request

    eul = orientations()
    assert eul.shape == (48 * 8, 3)
    names = [p["id"] for p in products(2)]
    assert len(names) == 4 + 2 * 4 and len(set(names)) == len(names)
    assert "dx12_v3_commander_noise_hm1_mc_00001_raw.fits" in names
    assert all(p["url"].startswith("https://pla.esac.esa.int/") for p in products(1))
    assert SPLITS == (("hm1", "hm2"), ("oe1", "oe2"))
    with pytest.raises(ValueError, match="non-https"):
        _HttpsOnly().redirect_request(Request("https://pla.esac.esa.int/x"), None, 302, "Found", {}, "http://x")
