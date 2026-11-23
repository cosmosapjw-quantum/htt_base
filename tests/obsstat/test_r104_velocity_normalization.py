"""R104: z=0 km/s velocity fields are transported by g(z)/g(0), and projected along each ray."""
import numpy as np
from numpy.testing import assert_allclose

from scripts.r103 import manticore_cf4_pv as pv


def test_growth_ratio_identity_at_z0_and_dimensionless():
    from scripts.r98 import cf4_p1 as old
    sci, *_ = old._load_r30_and_bridge()
    z = np.array([0.0, 0.05])
    g = sci.background(z, 64)[1]
    ratio = pv.velocity_growth_ratio(g, g[0])
    assert_allclose(ratio[0], 1.0, rtol=0, atol=0)
    assert_allclose(g[0], 35.5247255, rtol=1e-8)
    assert_allclose(ratio[1], 1.00408763, rtol=1e-8)


def test_constant_velocity_projects_to_ray_component():
    mesh = 8
    rng = np.random.default_rng(104)
    n = rng.normal(size=(5, 3))
    n /= np.linalg.norm(n, axis=1)[:, None]
    r = np.linspace(50., 300., 5)
    stencil = pv.mesh_stencil(n, r, mesh_size=mesh, box_mpc=1000.)
    vel = np.array([310., -125., 47.])
    rho = np.full((mesh,) * 3, 2.5)
    field = {"density": rho, **{f"p{i}": rho * vel[i] for i in range(3)}}
    assert_allclose(pv.project_field(field, n, stencil, mesh_size=mesh), n @ vel, rtol=1e-13)
