import unittest

import numpy as np
from numpy.testing import assert_allclose
from scipy.interpolate import CubicSpline

from bass.recombination.baryon_history import BaryonHistory
from bass.recombination.opacity_history import OpacityHistory
from bass.recombination.tilted_hyrec import channel_expansion_from_tilted_kinematics


class BaryonVisibilityTests(unittest.TestCase):
    def test_class_B_continuity_and_class_A_limit(self):
        N = np.linspace(-2.0, 0.0, 17)
        H = np.full(N.size, 2e-17)
        beta = np.tile([0.2, -0.1, 0.0], (N.size, 1))
        z33 = np.zeros((N.size, 3, 3))
        for a_normalized in ([0.3, 0.0, 0.0], [0.0, 0.0, 0.0]):
            a = H[:, None]*a_normalized
            history = BaryonHistory(N, H, z33, a, z33, beta)
            drift = 2*np.dot(a_normalized, beta[0])
            gamma = 1/np.sqrt(1-beta[0] @ beta[0])
            x = np.linspace(-2.0, 0, 46)
            assert_allclose([history.hydrogen_factor(t) for t in x], np.exp(drift*x), rtol=1e-14)
            assert_allclose([history.theta(t) for t in x], gamma*H[0]*(3-drift), rtol=1e-14, atol=0)
            # Independent current identity: d ln(n_rest)/d tau_b = -Theta_b.
            t, h = -0.6, 0.001
            logn = lambda u: np.log(history.hydrogen_factor(u)) - 3*u - np.log(gamma)
            lhs = gamma*H[0]*(logn(t+h)-logn(t-h))/(2*h)
            assert_allclose(lhs, -history.theta(t), rtol=2e-12, atol=0)

    def test_accelerating_baryon_frame(self):
        N = np.linspace(-1, 0, 17)
        H = np.full(N.size, 1.1e-12)
        vb = np.column_stack((0.2+0.1*N, 0*N, 0*N))
        z33 = np.zeros((N.size, 3, 3))
        history = BaryonHistory(N, H, z33, np.zeros_like(vb), z33, vb)
        for i in (0, 4, 12, 16):
            v = vb[i, 0]
            g = 1/np.sqrt(1-v*v)
            # FLRW with non-comoving congruence: A_x/c = H (gamma*v + gamma^3*v').
            assert_allclose(history.acceleration(N[i]), [H[i]*(g*v+g**3*0.1), 0, 0], rtol=2e-14, atol=1e-26)
            assert_allclose(history.theta(N[i]), H[i]*(3*g+g**3*v*0.1), rtol=2e-14, atol=0)
            assert_allclose(np.trace(history.shear(N[i])), 0, atol=1e-26)

    def test_directional_slab_and_refinement(self):
        N = np.linspace(-2, 0, 11)
        q = np.full_like(N, 0.72)
        for sign in [-1, 1]:
            rate = q[0]*(1-sign*0.2)
            measure = OpacityHistory(N, q, beta=[0.2,0,0], direction=[sign,0,0])
            edges = np.linspace(-1.9, -0.2, 36)
            c = measure.cells(edges)
            assert_allclose(c.delta_tau, rate*np.diff(edges), rtol=3e-14, atol=0)
            assert_allclose(c.visibility_mass, np.diff(np.exp(-rate*(edges[-1]-edges))), atol=3e-16)
            assert_allclose(c.visibility_mass.sum(), -np.expm1(-rate*(edges[-1]-edges[0])), atol=3e-16)
            assert_allclose(measure.cells(edges[::5]).delta_tau, c.delta_tau.reshape(-1,5).sum(axis=1), rtol=2e-14)

    def test_replay_positivity_and_thin_late_cell(self):
        N = np.arange(6.0)
        q = np.array([1e8, 0.0, 0.0, 0.0, 1e-20, 1e-20])
        edges = np.linspace(0,5,101)
        self.assertLess(np.min(CubicSpline(N,q)(edges)), -1.0)
        m = OpacityHistory(N,q)
        cells = m.cells(edges)
        self.assertTrue(np.all(m.rate(edges) >= 0))
        self.assertTrue(np.all(cells.delta_tau >= 0))
        assert_allclose(m.cells([4,5]).delta_tau, [1e-20], rtol=2e-15, atol=0)
        assert_allclose(cells.visibility_mass[-1], np.diff(edges)[-1]*1e-20, rtol=3e-14, atol=0)
        for bad in ([-1,0], [2,1], [0,np.nan]):
            with self.assertRaises(ValueError):
                m.cells(bad)

    def test_sobolev_full_sphere_sign(self):
        H = 1.0e-13
        common = dict(H_n_s=H, v_b=[0,0,0], theta_b_s=3*H,
                      n_H_normal_cm3=1e-5, x_1s=0.9, tr_normal_k=3000)
        # Axial minimum lies at pole which is not a Gauss-Legendre sample.
        with self.assertRaisesRegex(ValueError, "redshift gradient"):
            channel_expansion_from_tilted_kinematics(**common, sigma_b_s=H*np.diag([0.505,0.505,-1.01]))
        # Acceleration introduces an odd directional term, causing a zero despite positive shear-only K.
        with self.assertRaisesRegex(ValueError, "redshift gradient"):
            channel_expansion_from_tilted_kinematics(**common, sigma_b_s=np.zeros((3,3)), acceleration_b_over_c_s=[0,0,1.1*H])
        # Conservative h + lam_min - |A| < 0, but exact minimum is positive (hard case).
        kwargs = dict(common, sigma_b_s=H*np.diag([-.8,.3,.5]))
        r = channel_expansion_from_tilted_kinematics(**kwargs, acceleration_b_over_c_s=[0,0,0.35*H])
        r_flip = channel_expansion_from_tilted_kinematics(**kwargs, acceleration_b_over_c_s=[0,0,-0.35*H])
        assert_allclose(r.lya_escape_expansion_s, r_flip.lya_escape_expansion_s, rtol=2e-13, atol=0)

    def test_sobolev_neutral_response(self):
        H = 3.0e-13
        kwargs = dict(H_n_s=H,v_b=[0,0,0],theta_b_s=3*H,n_H_normal_cm3=8e-6,
                      tr_normal_k=3000, sigma_b_s=H*np.diag([-.35,.1,.25]),
                      acceleration_b_over_c_s=[0, .05*H, 0])
        f, step = 0.6, 1e-4
        def state(x):
            return channel_expansion_from_tilted_kinematics(**kwargs,x_1s=x)
        finite_difference = (state(f+step).lya_escape_expansion_s-state(f-step).lya_escape_expansion_s)/(2*step)
        assert_allclose(state(f).d_lya_escape_d_x1s_s, finite_difference,rtol=1e-7,atol=0)

if __name__ == "__main__":
    unittest.main()
