"""Fast synthetic tests of the R108 fixed-design wrapper of the R106 Gaia estimator (no data files)."""
import healpy as hp
import numpy as np

from scripts.r69.gaia_e2_b2 import templates
from scripts.r103 import gaia_frame_curvature as g
from scripts.r106 import gaia_null_refit as r106
from scripts.r108 import gaia_estimator as est


def _synthetic(n=6000, seed=3):
    rng = np.random.default_rng(seed)
    ra = rng.uniform(0, 2 * np.pi, n)
    dec = np.arcsin(rng.uniform(-1, 1, n))
    e1, e2 = rng.uniform(0.3, 1.2, n), rng.uniform(0.3, 1.2, n)
    rho = rng.uniform(-0.6, 0.6, n)
    shell = rng.integers(0, 4, n)
    patch = hp.ang2pix(2, np.pi / 2 - dec, ra)
    return rng, ra, dec, e1, e2, rho, shell, patch


def test_fast_rhs_matches_group_normal_and_whitening():
    rng, ra, dec, e1, e2, rho, shell, patch = _synthetic()
    y = rng.normal(size=(len(ra), 2))
    X, Y = r106.whiten(ra, dec, y, e1, e2, rho)
    L = est.cholesky_factors(e1, e2, rho)
    assert np.allclose(est.whiten_field(L, y), Y, rtol=1e-13, atol=1e-13)
    _, s = r106.group_normal(X, Y, shell, patch)
    key = shell * est.NPATCH + patch
    assert np.max(np.abs(est.rhs(X, Y, key) - s)) < 1e-10 * np.max(np.abs(s))


def test_catalogue_noise_whitens_to_identity():
    _, _, _, e1, e2, rho, _, _ = _synthetic(50)
    l00, l10, l11 = est.cholesky_factors(e1, e2, rho)
    for i in range(50):
        C = np.array([[e1[i] ** 2, rho[i] * e1[i] * e2[i]], [rho[i] * e1[i] * e2[i], e2[i] ** 2]])
        Lt = np.array([[l00[i], l10[i]], [0.0, l11[i]]])
        assert np.allclose(Lt @ C @ Lt.T, np.eye(2), atol=1e-12)


def test_constant_frame_is_annihilated_by_curvature_rows():
    rng, ra, dec, e1, e2, rho, shell, patch = _synthetic(8000, 4)
    X, _ = r106.whiten(ra, dec, np.zeros((len(ra), 2)), e1, e2, rho)
    L = est.cholesky_factors(e1, e2, rho)
    key = shell * est.NPATCH + patch
    f, _ = r106.group_normal(X, np.zeros((len(ra), 2)), shell, patch)
    w = g.curvature_rows([0.6, 1.17, 1.76, 2.46])
    noise = rng.normal(size=(len(ra), 2))
    _, B = templates(ra, dec)
    frame = np.einsum("nkj,j->nk", B, rng.normal(0, 10, 16)) / 1000.0
    s0 = est.rhs(X, est.whiten_field(L, noise), key)
    s1 = est.rhs(X, est.whiten_field(L, noise + frame), key)
    keep = np.arange(est.NPATCH)
    c0, c1 = r106.curvature(f, s0, w, keep), r106.curvature(f, s1, w, keep)
    assert np.max(np.abs(c1 - c0)) < 1e-8 * max(1.0, np.max(np.abs(c0)))
    st = est.stats(f, s0, w)
    assert set(st) == {"all48", "excl_selected__EB"} and len(st["excl_selected__EB"]["pair"]) == 2


def test_provenance_hashes_the_main_script(tmp_path, monkeypatch):
    import sys
    import types

    from scripts.r108.common import sha256_file

    script = tmp_path / "fake_main_script.py"
    script.write_text("print('x')\n")
    fake = types.ModuleType("__main__")
    fake.__file__ = str(script)
    monkeypatch.setitem(sys.modules, "__main__", fake)
    pv = est.provenance()
    assert pv["main_script"]["sha256"] == sha256_file(script)
    assert pv["module_sha256"][pv["main_script"]["path"]] == sha256_file(script)
    del fake.__file__
    assert est.main_script_identity()["sha256"] is None
