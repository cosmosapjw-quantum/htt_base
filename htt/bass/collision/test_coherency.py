import unittest

import numpy as np
from scipy.linalg import expm
from scipy.sparse import bmat, csc_matrix
from scipy.sparse.linalg import expm_multiply

from bass.collision.coherency import ThomsonCoherencyPropagator
from bass.collision.electron_frame import (
    _scatter_one_stokes_component, build_full_stokes_mueller_kernel,
    full_stokes_mueller_collision, full_stokes_thomson_source,
)
from bass.transport.general_bianchi_transfer import (
    _spherical_screen_basis, gl_sphere_grid, map_from_scalar_alm, qu_from_spin2_alm,
)
from scripts.r101.coherency_history import alm_from_stokes, evolve_cells
from scripts.r97.bianchi_coupled_m_transport import _build_diag_stream_and_thomson, _mode_index_table


def sky_grid(size):
    th, ph, grid, weights = gl_sphere_grid(size)
    n = grid.reshape(-1, 3)
    u, v = _spherical_screen_basis(n)
    return th, ph, n, weights, u, v


def dense_collision(n, w, u, v):
    # Existing scattering-plane Mueller integral on I,Q,U and the independent
    # Jones determinant det(B_out^T B_in)=n_out.n_in on Stokes V.
    mueller = build_full_stokes_mueller_kernel(directions=n, weights=w, basis_u=u, basis_v=v)
    gain = np.zeros((len(n), 4, len(n), 4))
    gain[:, :3, :, :3] = mueller.source_matrix.transpose(2, 0, 3, 1)
    gain[:, 3, :, 3] = 3/(8*np.pi) * (n @ n.T) * w
    return gain.reshape(4*len(n), -1) - np.eye(4*len(n))


def seeded_harmonics(ell_max, rng):
    modes = {}
    for channel, ell_min in (("I", 0), ("E", 2), ("B", 2), ("V", 0)):
        alm = {}
        for ell in range(ell_min, ell_max+1):
            alm[ell, 0] = rng.normal()
            for m in range(1, ell+1):
                alm[ell, m] = rng.normal() + 1j*rng.normal()
                alm[ell, -m] = (-1)**m * alm[ell, m].conjugate()
        modes[channel] = alm
    return modes


def synthesize(alm, theta, phi):
    I, V = (map_from_scalar_alm(alm[ch], theta, phi) for ch in ("I", "V"))
    Q, U = qu_from_spin2_alm(alm["E"], alm["B"], theta, phi)
    return np.stack((I, Q, U, V), axis=-1).reshape(-1, 4)


def r100_affine_comparison(ell_max=6, n_theta=10, t=3.2):
    th, ph, n, w, u, v = sky_grid(n_theta)
    op = ThomsonCoherencyPropagator(n, w.ravel(), u, v)
    rng = np.random.default_rng(42)
    initial = seeded_harmonics(ell_max, rng)
    forcing = seeded_harmonics(ell_max, rng)
    s0, f = (synthesize(mapping, th, ph) for mapping in (initial, forcing))
    after = alm_from_stokes(op.advance_with_source(s0, t, f), th, ph, w, ell_max)
    m_values = tuple(range(-ell_max, ell_max+1))
    idx, size = _mode_index_table(ell_max, m_values)
    _, K = _build_diag_stream_and_thomson(ell_max, m_values, idx, size, 0.)
    y, source = np.empty(size, complex), np.empty((size, 1), complex)
    for ch, code in (("I", "T"), ("E", "E"), ("B", "B")):
        for lm, slot in idx[code].items():
            y[slot], source[slot, 0] = initial[ch][lm], forcing[ch][lm]
    augmented = bmat([[t*K, csc_matrix(source)], [None, csc_matrix((1, 1))]], format="csc")
    result = expm_multiply(augmented, np.r_[y, 1.])[:-1]
    errors = {}
    for ch, code in (("I", "T"), ("E", "E"), ("B", "B")):
        errors[ch] = float(max(abs(result[k]-after[ch][lm]) for lm,k in idx[code].items()))
    v_errors = []
    for (ell,m), a in initial["V"].items():
        x = t*(.5 if ell == 1 else 1.)
        phi1 = -np.expm1(-x)/x if x else 1.
        exact = np.exp(-x)*a + phi1*forcing["V"][ell,m]
        v_errors.append(abs(after["V"][ell,m] - exact))
    errors["V"] = float(max(v_errors))
    return errors, sum(len(alm) for alm in after.values())


class TestThomsonCoherency(unittest.TestCase):
    def test_direct_and_cached_native_iqu_endpoints(self):
        _, _, n, w, u, v = sky_grid(3)
        s = np.random.default_rng(753).normal(size=(len(n), 4))
        grid = dict(directions=n, weights=w.ravel(), basis_u=u, basis_v=v)
        fields = dict(I=s[:, 0], Q=s[:, 1], U=s[:, 2], Gamma_T=3.)
        target = 3*ThomsonCoherencyPropagator(n, w.ravel(), u, v).collision(s)[:, :3]
        for result in (full_stokes_thomson_source(**grid, **fields),
                full_stokes_mueller_collision(kernel=build_full_stokes_mueller_kernel(**grid), **fields)):
            actual = np.column_stack((result.collision_I, result.collision_Q, result.collision_U))
            np.testing.assert_allclose(actual, target, rtol=0., atol=3e-14)

    def test_oriented_scattering_against_jones_including_collinear(self):
        outgoing = np.array([0., 0., 1.])
        u_out, v_out = np.eye(3)[:2]
        s = np.array([1., .31, -.42])
        density = .5*np.array([[s[0]+s[1], s[2]], [s[2], s[0]-s[1]]])
        for angle in (0., 1e-11, .31, np.pi/2, np.pi-1e-11, np.pi):
            incoming = np.array([np.sin(angle), 0., np.cos(angle)])
            u = np.array([np.cos(angle), 0., -np.sin(angle)])
            v = np.cross(incoming, u)
            u_in, v_in = np.cos(.64)*u + np.sin(.64)*v, np.cos(.64)*v - np.sin(.64)*u
            J = np.array([u_out, v_out]) @ np.array([u_in, v_in]).T
            d = J @ density @ J.T
            expected = 2*np.array([d.trace(), d[0,0]-d[1,1], 2*d[0,1]])
            actual = _scatter_one_stokes_component(incoming_value=s, incoming=incoming,
                  outgoing=outgoing, incoming_u=u_in, incoming_v=v_in, outgoing_u=u_out, outgoing_v=v_out)
            np.testing.assert_allclose(actual, expected, atol=2e-14, rtol=0)

    def test_near_parallel_generic_ray_jones_limit(self):
        n = np.array([1., 2., 3.])/np.sqrt(14.)
        u = np.array([.3, -1., .6])
        u -= (n @ u)*n
        u /= np.linalg.norm(u)
        v = np.cross(n, u)
        for angle in (1e-14, np.pi-1e-14):
            no = n*np.cos(angle) + u*np.sin(angle)
            uo = u*np.cos(angle) - n*np.sin(angle)
            vo = np.cross(no, uo)
            stokes = np.array([1., .31, -.42])
            M = np.array([uo, vo]) @ np.array([u, v]).T
            d = M @ np.array([[1.31, -.42], [-.42, .69]]) @ M.T
            exact = np.array([d.trace(), d[0,0]-d[1,1], 2*d[0,1]])
            actual = _scatter_one_stokes_component(incoming_value=stokes, incoming=n, outgoing=no,
                        incoming_u=u, incoming_v=v, outgoing_u=uo, outgoing_v=vo)
            np.testing.assert_allclose(actual, exact, atol=2e-14, rtol=0)

    def test_dense_generator_and_source_exponential(self):
        _, _, n, w, u, v = sky_grid(3)
        op = ThomsonCoherencyPropagator(n, w.ravel(), u, v)
        C = dense_collision(n, w.ravel(), u, v)
        rng = np.random.default_rng(96)
        s = rng.normal(size=(len(n), 4))
        f = rng.normal(size=s.shape)
        np.testing.assert_allclose(op.collision(s).ravel(), C @ s.ravel(), atol=2e-14)
        for t in (0., 1e-12, 5e-4, 0.05, 5., 50.):
            block = np.zeros((C.shape[0]+1, C.shape[1]+1))
            block[:-1, :-1] = t*C
            block[:-1, -1] = f.ravel()
            exact = (expm(block) @ np.r_[s.ravel(),1.])[:-1]
            np.testing.assert_allclose(op.advance_with_source(s, t, f).ravel(), exact, atol=3e-13, rtol=2e-13)

    def test_all_m_affine_r100_quadrupole_and_circular(self):
        errors, count = r100_affine_comparison()
        self.assertEqual(count, 188)
        self.assertLess(max(errors.values()), 3e-12)

    def test_stiff_limit_semigroup_and_realizability(self):
        _, _, n, w, u, v = sky_grid(6)
        op = ThomsonCoherencyPropagator(n, w.ravel(), u, v)
        rng = np.random.default_rng(7)
        s = rng.normal(size=(len(n), 4))
        s[:, 0] = np.linalg.norm(s[:, 1:], axis=1)  # 100% polarized at each direction
        for t in (1e-8, .2, 20., 1e6):
            result = op.advance(s, t)
            self.assertGreaterEqual(np.min(result[:, 0]-np.linalg.norm(result[:, 1:],axis=1)), -2e-14)
            self.assertAlmostEqual(w.ravel() @ (result-s)[:, 0], 0., places=12)
            np.testing.assert_allclose(op.advance(op.advance(s, t*.4), t*.6), result, atol=2e-14)
        np.testing.assert_allclose(result[:, 0], (w.ravel() @ s[:, 0])/(4*np.pi), atol=1e-14)
        np.testing.assert_allclose(result[:, 1:], 0., atol=1e-14)
        f = np.zeros_like(s)
        f[:, 0] = n @ np.array([.2, -.1, .7])
        # Source equals t times the baryon dipole. Deep tight coupling tracks that dipole.
        np.testing.assert_allclose(op.advance_with_source(s*0, 1e6, 1e6*f), f, atol=8e-11)
        np.testing.assert_allclose(op.advance_with_source(s, 0, f), s+f, atol=0)

    def test_rotated_screens_and_rotated_tetrad(self):
        _, _, n, w, u, v = sky_grid(5)
        rng = np.random.default_rng(28)
        s = rng.normal(size=(len(n), 4))
        op = ThomsonCoherencyPropagator(n, w.ravel(), u, v)
        psi = rng.uniform(-np.pi, np.pi, len(n))
        c, sn = np.cos(psi)[:, None], np.sin(psi)[:, None]
        ur, vr = c*u+sn*v, c*v-sn*u
        def rotate(sky):
            out = sky.copy()
            out[:, 1] = np.cos(2*psi)*sky[:, 1] + np.sin(2*psi)*sky[:, 2]
            out[:, 2] = -np.sin(2*psi)*sky[:, 1] + np.cos(2*psi)*sky[:, 2]
            return out
        R, _ = np.linalg.qr(rng.normal(size=(3, 3)))
        R[:, 0] *= np.linalg.det(R)
        rotated = ThomsonCoherencyPropagator(n@R, w.ravel(), ur@R, vr@R)
        np.testing.assert_allclose(rotated.advance(rotate(s), 4.), rotate(op.advance(s, 4.)), atol=2e-14)

    def test_validation_and_tangent(self):
        _, _, n, w, u, v = sky_grid(4)
        op = ThomsonCoherencyPropagator(n, w.ravel(), u, v)
        with self.assertRaisesRegex(ValueError, "degree-four"):
            ThomsonCoherencyPropagator(np.vstack((np.eye(3), -np.eye(3))), np.full(6, 4*np.pi/6))
        with self.assertRaisesRegex(ValueError, "right-handed"):
            ThomsonCoherencyPropagator(n, w.ravel(), u, -v)
        s = np.random.default_rng(86).normal(size=(len(n), 4))
        for x in (-.1, np.nan, np.inf, np.ones(len(n))):
            with self.assertRaises(ValueError):
                op.advance(s, x)
        with self.assertRaises(ValueError):
            op.advance(s.astype(complex), 1.)
        with self.assertRaises(ValueError):
            evolve_cells(op, s, [-.1, .4])
        q, dq, eps = .7, .13, 1e-5
        deriv = (op.advance(s, q+dq*eps)-op.advance(s, q-dq*eps))/(2*eps)
        np.testing.assert_allclose(deriv, dq*op.collision(op.advance(s,q)), atol=3e-11)


if __name__ == "__main__":
    unittest.main()
