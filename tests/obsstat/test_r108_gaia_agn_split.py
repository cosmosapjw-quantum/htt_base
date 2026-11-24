"""Fast synthetic tests of scripts/r108/gaia_agn_split.py helpers (no data files)."""
import healpy as hp
import numpy as np

from scripts.r103 import gaia_frame_curvature as g
from scripts.r106 import gaia_null_refit as r106
from scripts.r108 import gaia_agn_split as sp


def _halves(seed=9, n=12000):
    rng = np.random.default_rng(seed)
    ra = rng.uniform(0, 2 * np.pi, n)
    dec = np.arcsin(rng.uniform(-1, 1, n))
    e = np.full(n, 0.5)
    y = rng.normal(0, 0.5, (n, 2))
    X, Y = r106.whiten(ra, dec, y, e, e, np.zeros(n))
    shell = rng.integers(0, 4, n)
    patch = hp.ang2pix(2, np.pi / 2 - dec, ra)
    return rng, X, Y, shell, patch


def test_difference_of_identical_halves_is_zero():
    _, X, Y, shell, patch = _halves()
    f, s = r106.group_normal(X, Y, shell, patch)
    w = g.curvature_rows([0.6, 1.17, 1.76, 2.46])
    keep = np.arange(48)
    full, _, _, _ = g.shared_patch_refits(f, s)
    d = (w @ (full - full)).reshape(-1)
    assert np.all(d == 0)
    q, d2 = sp.diff_q(f, s, f, 1.0001 * s, w, keep)
    assert np.isfinite(q["spin6"]) and np.max(np.abs(d2)) > 0


def test_half_stats_blocks_when_a_cell_is_empty():
    _, X, Y, shell, patch = _halves(10, 6000)
    w = g.curvature_rows([0.6, 1.17, 1.76, 2.46])
    m = ~((shell == 0) & (patch == 5))
    st, counts, _, _ = sp.half_stats(X[m], Y[m], shell[m], patch[m], w)
    assert st is None and counts[0, 5] == 0


def test_agn_vs_non_agn_wording_is_by_construction_and_flags_d10():
    m = {"non_agn_in_r106_sample": 0}
    s = sp.agn_vs_non_agn_statement(m, agn_checked=False)
    assert "by construction of the R106 sample" in s and "not checked (D10 blocked)" in s
    assert "every qualified R106 Quaia row is a Gaia-CRF3 / agn_cross_id source" not in s
    assert "checked against D10" in sp.agn_vs_non_agn_statement(m, agn_checked=True)
    assert sp.agn_vs_non_agn_statement({"non_agn_in_r106_sample": 3}, False).startswith("non-AGN rows exist")
