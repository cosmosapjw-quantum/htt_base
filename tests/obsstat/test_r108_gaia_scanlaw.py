"""Fast synthetic tests of scripts/r108/gaia_scanlaw.py (no data files)."""
import healpy as hp
import numpy as np

from scripts.r108 import gaia_scanlaw as S


def test_position_angle_north_east():
    # due north from the equator -> 0, due east -> 90 deg
    assert abs(np.rad2deg(S.position_angle(0.0, 0.0, 0.0, 1e-4))) < 1e-6
    assert abs(np.rad2deg(S.position_angle(0.0, 0.0, 1e-4, 0.0)) - 90.0) < 1e-6


def test_wrap180_is_axial():
    assert np.allclose(S.wrap180([0.0, 180.0, -180.0, 179.0, 91.0]), [0.0, 0.0, 0.0, -1.0, -89.0])


def test_is_step_tolerance():
    assert S.is_step(9_999_999_858)
    assert not S.is_step(20_000_000_000)


def test_design_rows_unit_vectors_and_parallax():
    ra = np.array([0.0, 0.0])
    dec = np.array([0.0, 0.0])
    psi = np.array([0.0, np.pi / 2])  # north, east
    bary = np.array([[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]])  # observer along +y = local East at ra=0
    a = S.design_rows(ra, dec, psi, np.array([1.0, 2.0]), bary)
    assert np.allclose(a[0, :2], [0.0, 1.0]) and np.allclose(a[1, :2], [1.0, 0.0])
    assert abs(a[0, 2]) < 1e-12 and abs(a[1, 2] + 1.0) < 1e-12  # p = -u.b
    assert np.allclose(a[1, 3:], [2.0, 0.0])


def test_count_passes():
    pix = np.array([5, 5, 5, 7, 7, 5, 5])
    obmt = np.array([0, 1, 2, 3, 4, 100, 101]) * S.SAMPLE_NS
    obmt[5:] += 7  # still not consecutive to sample 4
    p = S.count_passes(pix, obmt)
    assert p[5] == 2 and p[7] == 1


def _info(psis, taus):
    psis, taus = np.asarray(psis, float), np.asarray(taus, float)
    a = S.design_rows(np.zeros_like(psis), np.zeros_like(psis), psis, taus, np.zeros((len(psis), 3)))
    a[:, 2] = np.cos(np.arange(len(psis)))  # generic parallax factors keep N invertible
    return a.T @ a


def test_pm_shape_orientation():
    """Scans mostly along psi=45 deg constrain (E+N); the PM error ellipse is elongated along (E-N): rho < 0."""
    rng = np.random.default_rng(1)
    taus = rng.uniform(-1.4, 1.4, 400)
    psis = np.where(rng.random(400) < 0.8, np.pi / 4, -np.pi / 4)
    N = _info(psis, taus)
    flat = N[np.triu_indices(5)][None]
    cov, cond = S.pm_shape(flat)
    rho = cov[0, 0, 1] / np.sqrt(cov[0, 0, 0] * cov[0, 1, 1])
    assert rho < -0.3 and np.isfinite(cond[0])
    psis2 = np.where(rng.random(400) < 0.8, -np.pi / 4, np.pi / 4)
    cov2, _ = S.pm_shape(_info(psis2, taus)[np.triu_indices(5)][None])
    assert cov2[0, 0, 1] > 0


def test_accumulate_and_unpack_roundtrip():
    rng = np.random.default_rng(2)
    a = rng.normal(size=(50, 5))
    pix = np.zeros(50, int)
    r = S.accumulate(1, pix, a, np.ones(50), np.zeros(50))
    assert r["n"][0] == 50 and np.allclose(S.unpack(r["N"])[0], a.T @ a)
    assert len(r["n"]) == hp.nside2npix(1)
