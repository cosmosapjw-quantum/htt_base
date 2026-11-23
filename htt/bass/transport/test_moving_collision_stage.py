"""Angular and stiff-time regressions for the BASS Lie/Stokes moving cell."""
import numpy as np
import unittest
from scipy.linalg import expm
from scipy.special import sph_harm_y

from bass.collision.electron_frame import rotate_stokes_samples
from bass.collision.moving_thomson import MovingFrameThomsonOperator
from bass.transport.general_bianchi_transfer import (
    _spherical_screen_basis, map_from_scalar_alm, qu_from_spin2_alm, spin2_alm_from_qu,
)
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, vector_to_alm_dict
from bass.transport.moving_collision_stage import MovingCollisionStage, initial_radiation_stokes


class TestMovingCollisionStage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.op = GeneralLieStokesOperator(6)

    def test_rest_reduction_and_first_order_outward_dipole(self):
        op = self.op
        zero = MovingCollisionStage(op, np.zeros(3))
        expected_gain = (op.U_rank9 * op.thomson_gains) @ op.U_rank9.T
        np.testing.assert_allclose(zero.left @ zero.right_h, expected_gain, atol=5e-14)
        np.testing.assert_array_equal(zero.emission, np.zeros(op.dim))
        beta = np.array([1., -.5, .8])*1e-9
        moving = MovingCollisionStage(op, beta)
        np.testing.assert_allclose(moving.emission, op.dipole_source_vector(-beta), atol=3e-17)


    def test_high_modes_and_signed_emission_against_rest_quadrature(self):
        op = self.op
        beta = np.array([.21, -.08, .05])
        candidate = MovingCollisionStage(op, beta)
        # Disjoint quadrature construction: begin with a large electron-rest sky,
        # aberrate each ray to the normal sky, and independently analyze its result.
        ang = MovingFrameThomsonOperator(beta, n_theta_rest=28)
        # Antipodal sky chart: (et, -ep, p=-n) is right-handed, so U,V flip.
        n, w = -ang.directions_normal, ang.weights_normal
        et, ep = _spherical_screen_basis(n)
        th, ph = np.arccos(np.clip(n[:, 2], -1, 1)), np.arctan2(n[:, 1], n[:, 0])
        y = np.zeros(op.dim, dtype=complex)
        for ch, ell, m, amp in (("T", 6, 2, .19+.10j), ("E", 5, 1, -.12j),
                                ("B", 6, 3, .04+.06j), ("V", 6, 3, -.07+.05j)):
            y[op.idx[ch][ell,m]] = amp
            y[op.idx[ch][ell,-m]] = (-1)**m * amp.conjugate()
        alm = vector_to_alm_dict(y, op.idx)
        Q, U = qu_from_spin2_alm(alm["E"], alm["B"], th, ph)
        q, u = rotate_stokes_samples(Q, -U, et, -ep, ang.basis_u_normal, ang.basis_v_normal)
        sky = np.column_stack((map_from_scalar_alm(alm["T"], th, ph) + .25, q, u,
                               -map_from_scalar_alm(alm["V"], th, ph)))
        coll = ang.collision_bolometric(sky, clock="conserved_anchor")
        Q, U = rotate_stokes_samples(coll[:,1], coll[:,2], ang.basis_u_normal, ang.basis_v_normal, et, -ep)
        E, B = spin2_alm_from_qu(Q, -U, th, ph, w, op.L)
        reference = np.zeros_like(y)
        for (ell, m), idx in op.idx["T"].items():
            ylm = sph_harm_y(ell, m, th, ph).conj()
            reference[idx] = np.sum(w * coll[:,0] * ylm)
            reference[op.idx["V"][ell,m]] = -np.sum(w * coll[:,3] * ylm)
            if ell >= 2:
                reference[op.idx["E"][ell,m]] = E[ell,m]
                reference[op.idx["B"][ell,m]] = B[ell,m]
        np.testing.assert_allclose(candidate.apply(y) + candidate.emission, reference, atol=7e-12, rtol=1e-10)


    def test_stiff_stage_and_second_order_time_refinement(self):
        op = self.op
        mov = MovingCollisionStage(op, [.13, -.11, .06])
        geom = np.zeros(14)
        # A finite cell with a noncommuting Fourier streaming block.
        k = np.array([.3, .1, -.5])
        base = op.base_operator(geom, k_eff=k)
        K = mov.loss.toarray() + mov.left @ mov.right_h
        dtau, dN = 3., .8
        rng = np.random.default_rng(103)
        y = rng.normal(size=op.dim) + 1j*rng.normal(size=op.dim)
        exact = expm(dN*base.toarray() + dtau*K) @ y
        errors = []
        for substeps in (4, 8, 16):
            pred = op.advance_cell(y, dN, geom, dtau, k_eff=k, substeps=substeps, moving_collision=mov)
            errors.append(np.linalg.norm(pred-exact)/np.linalg.norm(exact))
        assert min(a/b for a,b in zip(errors, errors[1:])) > 3.8, errors
        # One implicit solve at a depth large enough to invalidate a frozen
        # explicit beta-correction. Direct residual includes both gain and loss.
        gh, tau = .25, 4e3
        pred = mov.factor_sdirk_stage(base, gh, tau)(y)
        residual = pred - gh*(base @ pred) - gh*tau*mov.apply(pred) - y
        assert np.linalg.norm(residual)/np.linalg.norm(y) < 1e-11


    def test_boosted_blackbody_matches_fluid_energy_flux_and_pressure(self):
        op = self.op
        from bass.background.general_tilted_evolution import energy_momentum_ratio_from_primitive, primitive_from_energy_momentum_ratio
        from bass.transport.general_lie_stokes import vector_to_stokes_maps
        from bass.transport.coupled_einstein_boltzmann import extract_stf_pi_from_state
        beta = np.array([.24, -.19, .07])
        logE, q_ratio = energy_momentum_ratio_from_primitive(2.8, beta, 1/3)
        _, _, _, stress = primitive_from_energy_momentum_ratio(logE, q_ratio, 1/3)
        state = initial_radiation_stokes(op, beta)
        outward = op._grid[2].reshape(-1, 3)
        w = op._grid[3].ravel()
        theta = vector_to_stokes_maps(state, op.idx, L=op.L, n_gl_theta=op.n_gl_theta)[..., 0].ravel()
        intensity = stress[0,0]*(1+4*theta)/(4*np.pi)
        k = np.column_stack((np.ones(len(w)), -outward))
        recovered = np.einsum("n,ni,nj->ij", w*intensity, k, k)
        np.testing.assert_allclose(recovered, stress, atol=4e-14)
        pi_fluid = stress[1:,1:] - np.eye(3)*np.trace(stress[1:,1:])/3
        np.testing.assert_allclose(extract_stf_pi_from_state(state, stress[0,0], op), pi_fluid, atol=3e-14)

    def test_invalid_velocity(self):
        op = self.op
        for bad in ([1,0,0], [np.nan,0,0]):
            with self.assertRaises(ValueError):
                MovingCollisionStage(op, bad)
