"""Fast synthetic tests for scripts/r108/cf4_2mpp_field.py (grid interpolation and 2M++ grid conventions)."""
import numpy as np
import pytest

from scripts.r108 import cf4_2mpp_field as m


def _linear_field(n, step, centre, A, c):
    i = (np.arange(n) - centre) * step
    X = np.stack(np.meshgrid(i, i, i, indexing="ij"), axis=-1)
    return X @ A.T + c


def test_trilinear_exact_for_linear_field():
    rng = np.random.default_rng(0)
    A, c = rng.normal(size=(3, 3)), rng.normal(size=3)
    g = m.Grid(_linear_field(17, 2.5, 8., A, c), 2.5, 8., 18.)
    x = rng.uniform(-14, 14, (200, 3))
    x = x[np.linalg.norm(x, axis=1) <= 18.]
    v, ok = g.interpolate(x)
    assert ok.all()
    assert np.allclose(v, x @ A.T + c, atol=1e-12)


def test_undefined_outside_rmax_and_nan_corner():
    f = np.ones((9, 9, 9, 3))
    f[6, 4, 4] = np.nan
    g = m.Grid(f, 1., 4., 3.5)
    v, ok = g.interpolate(np.array([[0., 0., 0.], [3.9, 0., 0.], [1.5, 0., 0.], [0., 0., -3.]]))
    assert ok.tolist() == [True, False, False, True]   # r>rmax; corner (6,4,4) is NaN for x=1.5 (cells 5,6)
    assert np.isnan(v[1]).all() and np.isnan(v[2]).all()


def test_twompp_grid_conventions(tmp_path):
    n = 9
    comp = np.zeros((3, n, n, n), np.float32)
    comp[0] += 10.   # vx
    comp[1] += 20.
    comp[2] += 30.
    comp[0, n - 1, 0, 0] = 99.   # marks axis order
    p = tmp_path / "twompp_velocity.npy"
    np.save(p, comp)
    g, meta = m.twompp_grid(p, box_mpch=8., beta_scale=.5, vext=(1., 2., 3.), axis_order="xyz", rmax=4.)
    assert meta["components_first"] and meta["n"] == n and meta["step_mpch"] == pytest.approx(1.)
    assert meta["centre_index"] == pytest.approx(4.)
    assert np.allclose(g.field[4, 4, 4], [6., 12., 18.])
    assert g.field[n - 1, 0, 0, 0] == pytest.approx(.5 * 99 + 1)
    gz, _ = m.twompp_grid(p, box_mpch=8., beta_scale=1., vext=(0., 0., 0.), axis_order="zyx", rmax=4.)
    assert gz.field[0, 0, n - 1, 0] == pytest.approx(99.)


def test_twompp_grid_rejects_bad_shape(tmp_path):
    p = tmp_path / "bad.npy"
    np.save(p, np.zeros((4, 5, 5, 5)))
    with pytest.raises(ValueError):
        m.twompp_grid(p, 8., 1., (0, 0, 0), "xyz", 4.)
