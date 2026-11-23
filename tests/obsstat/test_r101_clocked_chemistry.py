"""Physics and numerical tests of the fixed-efold, prescribed-network contract."""

from dataclasses import replace
import unittest

import numpy as np
from numpy.testing import assert_allclose
from scipy.integrate import quad, solve_ivp

from bass.recombination.clocked_chemistry import ChemistryTangent, evolve_clocked_chemistry
from bass.recombination.reionization import (
    C_LIGHT, SEC_PER_MPC, SIGMA_T, CosmologyForRecombination, compute_tau_dot_conformal_Mpc,
)


def generator(ion, feed, escape):
    """Neutral -> ionized -> delayed intermediate -> neutral, per proper second."""
    return np.array([[-ion, 0.0, escape], [ion, -feed, 0.0], [0.0, feed, -escape]])


def problem():
    return dict(
        N_edges=np.array([-0.6, -0.18, 0.0]),
        initial_population=np.array([0.22, 0.65, 0.13]),
        electron_yield=np.array([0.02, 1.10, 0.12]),
        proper_generators_s=np.array([generator(0.16, 2.1, 2.1), generator(1.8, 0.09, 0.15)]),
        hubble_normal_s=np.array([0.85, 1.06]),
        beta=np.array([[0.4, -0.1, 0.05], [-0.15, 0.3, 0.1]]),
        photon_direction=np.array([[0.6, 0.8, 0.0], [0.0, 0.8, 0.6]]),
        comoving_hydrogen_m3=1.2e19,
    )


def perturbation():
    return ChemistryTangent(
        proper_generators_s=np.array([generator(-0.07, 0.2, -0.2), generator(0.12, -0.01, 0.06)]),
        initial_population=np.array([-0.02, 0.03, -0.01]),
        electron_yield=np.array([0.03, -0.1, 0.01]),
        hubble_normal_s=np.array([0.16, -0.11]),
        beta=np.array([[0.06, 0.04, -0.02], [0.01, -0.05, 0.09]]),
        photon_direction=np.array([[-0.08, 0.06, 0.03], [0.05, -0.06, 0.08]]),
        comoving_hydrogen_m3=-7.4e17,
    )


def shifted(data, tangent, h):
    perturbed = dict(data)
    for field in vars(tangent):
        derivative = getattr(tangent, field)
        if derivative is not None:
            perturbed[field] = data[field] + h * derivative
    rays = perturbed["photon_direction"]
    perturbed["photon_direction"] = rays / np.linalg.norm(rays, axis=-1, keepdims=True)
    return perturbed


def proper_time_reference(data):
    """Direct nonlinear-in-time opacity RHS, independently integrated in tau_b."""
    p = data["initial_population"].copy()
    nodes = [p]
    depths = []
    for j, (left, right) in enumerate(zip(data["N_edges"][:-1], data["N_edges"][1:])):
        H = data["hubble_normal_s"][j]
        beta = data["beta"][j]
        gamma = (1.0 - beta @ beta) ** -0.5
        n = data["photon_direction"][j]
        k = p.size

        def rhs(tau, state):
            N = left + gamma * H * tau
            n_rest = data["comoving_hydrogen_m3"] / (gamma * np.exp(3.0 * N))
            xe = data["electron_yield"] @ state[:k]
            # dt_normal/dtau_b=Gamma for homogeneous fields, -u.k/E_n=Gamma(1-beta.n)
            proper_opacity = SIGMA_T * C_LIGHT * n_rest * xe * gamma**2 * (1 - beta @ n)
            return np.r_[data["proper_generators_s"][j] @ state[:k], proper_opacity]

        span = (0, (right - left) / (gamma * H))
        ivp = solve_ivp(rhs, span, np.r_[p, 0.0], method="DOP853", rtol=2e-13, atol=1e-14)
        if not ivp.success:
            raise RuntimeError(ivp.message)
        p = ivp.y[:k, -1]
        depths.append(ivp.y[-1, -1])
        nodes.append(p)
    return np.array(nodes), np.array(depths)


class ClockedChemistryTest(unittest.TestCase):
    def test_independent_proper_time_evolution(self):
        data = problem()
        history = evolve_clocked_chemistry(**data)
        nodes, depths = proper_time_reference(data)
        assert_allclose(history.population, nodes, rtol=2e-12, atol=1e-13)
        assert_allclose(history.delta_optical_depth, depths, rtol=3e-12, atol=1e-14)
        assert_allclose(history.population.sum(axis=1), 1.0, atol=2e-14)
        self.assertGreaterEqual(history.population.min(), 0.0)
        self.assertAlmostEqual(history.optical_depth_to_observer[-1], 0.0)
        assert_allclose(np.diff(history.optical_depth_to_observer), -depths, rtol=3e-12)
        assert_allclose(np.sum(history.visibility_bin_probability),
                        -np.expm1(-np.sum(depths)), rtol=3e-12)

    def test_hyrec_table_unit_bridge_in_flrw(self):
        cosmo = CosmologyForRecombination(h=0.67, T_cmb=2.725, Omega_b=0.049,
                                          Y_He=0.245, Omega_m=0.31, Omega_r=9e-5,
                                          Omega_Lambda=0.68991)
        H = float(cosmo.H_of_z(1060.0))
        edges = np.array([-7.03, -7.01, -6.95])
        xe = 0.63
        history = evolve_clocked_chemistry(edges, [1.0], [xe], [[0.0]], H,
                                           [0, 0, 0], [1, 0, 0], cosmo.n_H_today)
        def existing_rate(N):
            tau_dot = compute_tau_dot_conformal_Mpc(np.expm1(-N), xe, cosmo)
            return float(tau_dot * np.exp(-N) / (H * SEC_PER_MPC))
        reference = [quad(existing_rate, a, b)[0] for a, b in zip(edges[:-1], edges[1:])]
        assert_allclose(history.delta_optical_depth, reference, rtol=2e-14)

    def test_delayed_rec_then_reionization(self):
        # Repeated-rate two-stage branch with finite line probability b.
        feed = 2.0
        b = 0.3
        Q = np.array([[-feed, 0, 0, 0], [b*feed, -feed, 0, 0],
                      [(1-b)*feed, 0, 0, 0], [0, feed, 0, 0]], dtype=float)
        late = np.zeros_like(Q)
        late[0, 3] = 1.3
        late[3, 3] = -1.3
        history = evolve_clocked_chemistry([0.0, 0.5, 0.8], [1,0,0,0], [1,0,0,0],
                                           [Q, late], 1, [0,0,0], [0,0,1], 1e18)
        t = 0.5
        survived = np.exp(-feed*t)
        escaped = b*(1 - survived*(1 + feed*t))
        expected = np.array([survived, b*feed*t*survived, (1-b)*(1-survived), escaped])
        assert_allclose(history.population[1], expected, rtol=5e-15)
        self.assertAlmostEqual(history.x_e[-1], survived + escaped*(-np.expm1(-0.3*1.3)))
        self.assertGreater(history.x_e[-1], history.x_e[1])

    def test_complete_fixed_grid_tangent(self):
        data, tangent = problem(), perturbation()
        history = evolve_clocked_chemistry(**data, tangent=tangent)
        h = 2e-5
        plus = evolve_clocked_chemistry(**shifted(data, tangent, h))
        minus = evolve_clocked_chemistry(**shifted(data, tangent, -h))
        for field in vars(history.tangent):
            with self.subTest(field=field):
                finite_difference = (getattr(plus, field) - getattr(minus, field)) / (2*h)
                assert_allclose(getattr(history.tangent, field), finite_difference,
                                rtol=2e-8, atol=8e-12)
        assert_allclose(history.tangent.population.sum(axis=1), 0.0, atol=2e-15)
        assert_allclose(history.tangent.visibility_bin_probability.sum(),
                        np.exp(-history.optical_depth_to_observer[0])
                        * history.tangent.optical_depth_to_observer[0], rtol=2e-14)

    def test_nil_electron_limit_and_optically_thin_bin(self):
        data = problem()
        history = evolve_clocked_chemistry(**(data | {"electron_yield": np.zeros(3)}),
                                           tangent=ChemistryTangent(electron_yield=np.ones(3)))
        assert_allclose(history.delta_optical_depth, 0.0)
        assert_allclose(history.visibility_bin_probability, 0.0)
        self.assertTrue(np.all(history.tangent.delta_optical_depth > 0))
        h = evolve_clocked_chemistry(**(data | {"comoving_hydrogen_m3": 1e-6}))
        self.assertGreater(h.delta_optical_depth.min(), 0.0)
        assert_allclose(h.visibility_bin_probability, h.delta_optical_depth, rtol=3e-15, atol=0)

    def test_clock_scaling_and_tilt_separation(self):
        data = problem()
        scaled = {key: data[key]*7.0 for key in
                  ("proper_generators_s", "hubble_normal_s", "comoving_hydrogen_m3")}
        base = evolve_clocked_chemistry(**data)
        changed = evolve_clocked_chemistry(**(data | scaled))
        assert_allclose(changed.population, base.population, atol=2e-14)
        assert_allclose(changed.delta_optical_depth, base.delta_optical_depth, atol=2e-14)
        # At fixed normal density anchor a transverse boost slows chemistry,
        # while fixing the electron yield removes its direct transverse opacity response.
        prob = data | {"beta": [0.0, 0.0, 0.7], "photon_direction": [1.0, 0.0, 0.0],
                       "electron_yield": [1.,1.,1.]}
        transverse = evolve_clocked_chemistry(**prob)
        zero = evolve_clocked_chemistry(**(prob | {"beta": [0.0,0.0,0.0]}))
        self.assertGreater(np.linalg.norm(transverse.population - zero.population), 1e-3)
        assert_allclose(transverse.delta_optical_depth, zero.delta_optical_depth, rtol=1e-14)

    def test_piecewise_time_order_and_refinement(self):
        data = problem()
        refined = data | {"N_edges": np.array([-0.6,-0.39,-0.18,-0.09,0.0])}
        for key in ("hubble_normal_s", "proper_generators_s", "beta", "photon_direction"):
            refined[key] = np.repeat(data[key], 2, axis=0)
        a, b = evolve_clocked_chemistry(**data), evolve_clocked_chemistry(**refined)
        assert_allclose(a.population, b.population[::2], rtol=5e-15)
        assert_allclose(a.delta_optical_depth, b.delta_optical_depth.reshape(2,2).sum(axis=1),
                        rtol=5e-15)
        flipped = evolve_clocked_chemistry(**(data | {"proper_generators_s":
                                                       data["proper_generators_s"][::-1]}))
        self.assertGreater(np.linalg.norm(flipped.population[-1] - a.population[-1]), 1e-2)

    def test_stiff_two_state_reward_and_log_rate_derivative(self):
        # Closed form remains well-conditioned at 10^15 transitions per efold.
        a, b, x0 = 3.0e14, 7.0e14, 0.2
        total = a + b
        xe_eq, dxe_eq = a / total, a*b / total**2
        q = np.array([[-a, b], [a, -b]])
        dq = np.array([[-a, 0.], [a, 0.]])
        scale = SIGMA_T * C_LIGHT * 1e19
        hist = evolve_clocked_chemistry([0.,1.], [1.-x0,x0], [0.,1.], q, 1.0,
                                        [0,0,0], [1,0,0], 1e19,
                                        tangent=ChemistryTangent(proper_generators_s=dq))
        phi3 = -np.expm1(-3.) / 3.
        phi_fast = 1. / (3. + total)  # exp[-(3+total)] underflows at this rate.
        reference = xe_eq * phi3 + (x0 - xe_eq) * phi_fast
        dreference = dxe_eq * (phi3 - phi_fast) - (x0-xe_eq) * a * phi_fast**2
        assert_allclose(hist.x_e[-1], xe_eq, rtol=2e-13)
        assert_allclose(hist.delta_optical_depth[0], scale*reference, rtol=2e-13)
        assert_allclose(hist.tangent.x_e[-1], dxe_eq, rtol=2e-13)
        assert_allclose(hist.tangent.delta_optical_depth[0], scale*dreference, rtol=2e-13)
        assert_allclose(hist.population.sum(axis=1), 1.0, atol=5e-15, rtol=0)

    def test_midpoint_freeze_converges_for_smooth_driving(self):
        x0 = np.array([0.2, 0.65, 0.15])
        charge, ray = np.array([0.,1.,0.]), np.array([0.6,0.8,0.])
        anchor = 1.0e19

        def coefficients(N):
            H = 0.7 + 0.15*np.cos(2*N)
            v = np.array([0.2*np.sin(N), 0.12*np.cos(2*N), 0.1])
            q = generator(0.5 + 0.4*np.sin(2*N), 1.3 - 0.5*N, 1.2 + 0.6*N*N)
            return q, H, v

        def rhs(N, state):
            q, H, v = coefficients(N)
            p = state[:-1]
            op = SIGMA_T*C_LIGHT*anchor*np.exp(-3*N)*(1-v@ray)*(charge@p)/H
            return np.r_[(q@p)*np.sqrt(1-v@v)/H, op]

        ref = solve_ivp(rhs, (-0.8,0.0), np.r_[x0, 0.], method="DOP853",
                        atol=1e-14, rtol=2e-13)
        self.assertTrue(ref.success)
        errors = []
        for m in (8,16,32):
            edges = np.linspace(-0.8,0.0,m+1)
            q, H, v = zip(*(coefficients(x) for x in 0.5*(edges[:-1] + edges[1:])))
            result = evolve_clocked_chemistry(edges, x0, charge, q, H, v, ray, anchor)
            errors.append(np.abs(np.r_[result.population[-1], result.optical_depth_to_observer[0]]
                                 - ref.y[:, -1]).max())
        ratios = np.array(errors[:-1]) / errors[1:]
        self.assertTrue(np.all((ratios > 3.8) & (ratios < 4.2)), ratios)

    def test_domain_and_tangent_guards(self):
        data = problem()
        invalids = [dict(N_edges=[0., 0., 1.]), dict(N_edges=[0., 1., 0.5]),
                    dict(hubble_normal_s=0.0), dict(beta=[1.,0.,0.]),
                    dict(hubble_normal_s=np.nan), dict(photon_direction=[0.,0.,0.]),
                    dict(electron_yield=[1.,0.,-0.1]), dict(comoving_hydrogen_m3=0),
                    dict(initial_population=[0.5,0.5,0.5]), dict(beta=[1j,0,0]),
                    dict(proper_generators_s=generator(0.5,-0.4,0.6)),
                    dict(proper_generators_s=1e-25*np.eye(3)),
                    dict(tangent=ChemistryTangent(initial_population=[0.1,0.,0.])),
                    dict(tangent=ChemistryTangent(proper_generators_s=1e-28*np.eye(3))),
                    dict(tangent=ChemistryTangent(photon_direction=data["photon_direction"])),
                    dict(tangent=replace(perturbation(), hubble_normal_s=[1.,np.inf]))]
        for change in invalids:
            with self.subTest(field=next(iter(change))), self.assertRaises(ValueError):
                evolve_clocked_chemistry(**(data | change))


if __name__ == "__main__":
    unittest.main()
