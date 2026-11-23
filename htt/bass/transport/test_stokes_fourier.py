import unittest

import numpy as np
from scipy.linalg import expm

from bass.collision.test_coherency import dense_collision, sky_grid
from bass.transport.stokes_fourier import FourierStokesPropagator


def fourier_convergence():
    _, _, n, w, u, v = sky_grid(3)
    k = np.array([.33, -.47, .21])  # Mpc^{-1}; deliberately oblique to grid
    distance = 3.1  # Mpc
    t = 2.4
    solver = FourierStokesPropagator(n, w.ravel(), k, u, v)
    C = dense_collision(n, w.ravel(), u, v)
    diag = -1j*distance*np.repeat(n@k, 4)
    rng = np.random.default_rng(458)
    sky = rng.normal(size=(len(n),4)) + 1j*rng.normal(size=(len(n),4))
    source = .2*(rng.normal(size=sky.shape) + 1j*rng.normal(size=sky.shape))
    K = np.zeros((sky.size+1,sky.size+1),complex)
    K[:-1, :-1] = t*C + np.diag(diag)
    K[:-1, -1] = source.ravel()
    exact = (expm(K) @ np.r_[sky.ravel(),1.])[:-1].reshape(sky.shape)
    errors = []
    implicit = []
    for count in (1,2,4,8,16,32):
        actual = solver.advance(sky,distance,t,substeps=count,source_increment=source,method="strang")
        joint = solver.advance(sky,distance,t,substeps=count,source_increment=source)
        implicit.append({"substeps":count,"max_abs_error":float(np.max(abs(joint-exact)))})
        errors.append({"substeps": count, "max_abs_error": float(np.max(abs(actual-exact)))})
    # Nonuniformity of the splitting error in the tight-coupling limit.
    monopole = np.zeros_like(sky)
    monopole[:,0] = 1.
    thick = 1e3
    true_thick = (expm(thick*C+np.diag(diag)) @ monopole.ravel()).reshape(sky.shape)
    stiff = []
    stiff_implicit = []
    for count in (1,8,64,256,1024):
        y = solver.advance(monopole,distance,thick,substeps=count,method="strang")
        joint = solver.advance(monopole,distance,thick,substeps=count)
        stiff_implicit.append({"substeps":count,"max_abs_error":float(np.max(abs(joint-true_thick)))})
        stiff.append({"substeps":count,"max_abs_error":float(np.max(abs(y-true_thick)))})
    return {"n_directions":len(n),"k_per_mpc":k.tolist(),"delta_chi_mpc":distance,
            "delta_tau":t,"strang_complex_affine_errors":errors,"sdirk2_complex_affine_errors":implicit,
            "delta_tau_thick":thick,"strang_monopole_thick_errors":stiff,"sdirk2_monopole_thick_errors":stiff_implicit}


class TestFourierStokes(unittest.TestCase):
    def test_joint_dense_exponential_and_refinement(self):
        result = fourier_convergence()
        errs = [r["max_abs_error"] for r in result["strang_complex_affine_errors"]]
        self.assertTrue(all(3.9 < a/b < 4.1 for a,b in zip(errs[2:-1],errs[3:])))
        self.assertLess(errs[-1], 3e-4)
        thick = [r["max_abs_error"] for r in result["strang_monopole_thick_errors"]]
        self.assertLess(thick[-1], .001)
        self.assertGreater(thick[0], .05)
        joint = [r["max_abs_error"] for r in result["sdirk2_complex_affine_errors"]]
        stiff_joint = [r["max_abs_error"] for r in result["sdirk2_monopole_thick_errors"]]
        self.assertTrue(all(3.7 < a/b < 4.3 for a,b in zip(joint[2:-1],joint[3:])))
        self.assertLess(stiff_joint[0], 1e-4)
        self.assertLess(stiff_joint[-1], 1e-7)

    def test_shifted_moment_solve_against_independent_dense_matrix(self):
        _, _, n, w, u, v = sky_grid(3)
        solver = FourierStokesPropagator(n,w.ravel(),[.3, .1, -.2],u,v)
        C = dense_collision(n,w.ravel(),u,v)
        rng = np.random.default_rng(81)
        rhs = rng.normal(size=(len(n),4)) + 1j*rng.normal(size=(len(n),4))
        diagonal = rng.uniform(.8,1.2,len(n)) + .3j*rng.normal(size=len(n))
        for depth in (0., .2, 10., 1e4):
            matrix = np.diag(np.repeat(diagonal,4))-depth*C
            exact = np.linalg.solve(matrix,rhs.ravel())
            out = solver.collision.factor_shifted_collision(diagonal,depth)(rhs)
            np.testing.assert_allclose(out.ravel(),exact,atol=2e-12,rtol=2e-12)

    def test_conserved_trace_in_stiff_implicit_stage(self):
        _, _, n, w, u, v = sky_grid(3)
        solver = FourierStokesPropagator(n,w.ravel(),[.5,-.2,.4],u,v)
        monopole = np.zeros((len(n),4))
        monopole[:,0] = 1.
        for s in (1e8, 1e14, 1e17, 1e100):
            updated = solver.collision.factor_shifted_collision(np.ones(len(n)), s)(monopole)
            np.testing.assert_allclose(updated,monopole,atol=4e-14,rtol=0.)

    def test_implicit_map_continuous_through_both_axes(self):
        _, _, n, w, u, v = sky_grid(3)
        solver = FourierStokesPropagator(n,w.ravel(),[.5,-.2,.4],u,v)
        rng = np.random.default_rng(49)
        s = rng.normal(size=(len(n),4)) + 1j*rng.normal(size=(len(n),4))
        for distance,t,near_d,near_t in ((5.,0.,5.,1e-14),(0.,5.,1e-14,5.)):
            y = solver.advance(s,distance,t)
            near = solver.advance(s,near_d,near_t)
            np.testing.assert_allclose(y,near,atol=6e-14,rtol=0.)
            exact = solver.advance(s,distance,t,method="strang")
            a = np.max(abs(solver.advance(s,distance,t,substeps=16)-exact))
            b = np.max(abs(solver.advance(s,distance,t,substeps=32)-exact))
            self.assertGreater(a/b,3.8)
            self.assertLess(a/b,4.3)

    def test_exact_free_phase_and_opposite_wavevector_reality(self):
        _, _, n, w, u, v = sky_grid(4)
        k = np.array([0., 0., .4])
        solver = FourierStokesPropagator(n,w.ravel(),k,u,v)
        opposite = FourierStokesPropagator(n,w.ravel(),-k,u,v)
        rng = np.random.default_rng(87)
        sky = rng.normal(size=(len(n),4)) + 1j*rng.normal(size=(len(n),4))
        source = .3j*sky
        distance = 2.3
        phase = -1j*distance*(n@k)[:,None]
        expected = np.exp(phase)*sky + np.expm1(phase)/phase*source
        np.testing.assert_allclose(solver.advance(sky,distance,0.,source_increment=source,method="strang"), expected, atol=2e-14)
        for t in (0., .7, 500.):
            p = solver.advance(sky,distance,t,substeps=8,source_increment=source)
            m = opposite.advance(sky.conj(),distance,t,substeps=8,source_increment=source.conj())
            np.testing.assert_allclose(p.conj(),m,atol=3e-14)
        expected = (solver.collision.advance_with_source(sky.real,1.2,source.real)
                    + 1j*solver.collision.advance_with_source(sky.imag,1.2,source.imag))
        np.testing.assert_allclose(solver.advance(sky,0,1.2,source_increment=source,method="strang"),expected,atol=3e-14)
        with self.assertRaises(ValueError):
            solver.advance(sky,1.,np.ones(len(n)))


if __name__ == "__main__":
    unittest.main()
