"""Analytic fixtures and domain failures; no catalogue or science admission."""
import unittest
import numpy as np
from numpy.testing import assert_allclose
from common.r7_contracts import NumericalUnresolved
from common.relativistic_kinematics import (
    METRIC, four_velocity, lorentz_boost, relative_motion, intercept_velocity,
    hubble_tensor_lift, clock_normal, perfect_fluid_normal_projection,
    flux_to_beta, tilt_interval, endpoint_boost, inverse_temperature_boost,
    homogeneous_scalar_curvature, homogeneous_connection,
    homogeneous_codazzi_flux, invariant_eigenframe_structure,
    unit_timelike, kinematics_from_velocity_jet, hamiltonian_orbit_curvature,
    ideal_position_drift_moment,
)
from common.typefree_physical_budgets import StressBudgetContext, stress_gap_budget, weak_response_budget


class LocalGeometryTests(unittest.TestCase):
    def test_boost_metric_inverse_and_distinct_motion_pairs(self):
        beta = np.array([.2, -.1, .05]); l = lorentz_boost(beta)
        assert_allclose(l.T@METRIC@l, METRIC, atol=1e-14)
        assert_allclose(l@lorentz_boost(-beta), np.eye(4), atol=1e-14)
        assert_allclose(l[:, 0], four_velocity(beta))
        u, n = four_velocity(beta), four_velocity([0, 0, 0])
        self.assertAlmostEqual(relative_motion(u, n, first="U", second="N").beta_magnitude, np.linalg.norm(beta))
        self.assertEqual(relative_motion(u, u, first="U", second="O").first, "U")
        assert_allclose(intercept_velocity(u[0], u[1:]), u)
        with self.assertRaises(ValueError):
            intercept_velocity(1, [.1, 0, 0])

    def test_hubble_lift_recovers_boosted_anisotropic_gradient(self):
        beta = [.2, -.1, .05]; l = lorentz_boost(beta); inv = lorentz_boost(-np.array(beta))
        source_b = np.diag([0., 2., 3., 4.])
        b = inv.T@source_b@inv
        h0 = b[0, 0]+np.trace(b[1:, 1:])/3
        h1 = -2*b[0, 1:]
        q = b[1:, 1:]-np.eye(3)*np.trace(b[1:, 1:])/3
        lift = hubble_tensor_lift(h0, h1, q, geodesic=True)
        assert_allclose(lift.source_u, l[:, 0], atol=1e-13)
        assert_allclose(lift.symmetric_gradient, b, atol=1e-13)
        # Timelike eigenvalue also has a spacelike eigenvector: no unique U.
        with self.assertRaises(NumericalUnresolved):
            hubble_tensor_lift(2., [0, 0, 0], np.diag([-2., 0., 2.]), geodesic=True)
        with self.assertRaises(ValueError):
            hubble_tensor_lift(3., [0, 0, 0], np.zeros((3, 3)), geodesic=False)

    def test_clock_and_flux(self):
        n = clock_normal([-2., .2, 0, 0])
        self.assertAlmostEqual(n@METRIC@n, -1.)
        with self.assertRaises(ValueError):
            clock_normal([0, 1, 0, 0])
        beta = np.array([.2, .3, -.1]); e, j, s = perfect_fluid_normal_projection(4., 1., beta)
        self.assertAlmostEqual(flux_to_beta(np.linalg.norm(j), 5.), np.linalg.norm(beta))
        self.assertAlmostEqual(e, 5/(1-beta@beta)-1)
        assert_allclose(s, np.eye(3)+5*np.outer(beta, beta)/(1-beta@beta))
        low, high = tilt_interval(np.linalg.norm(j)*.9, np.linalg.norm(j)*1.1, 4., 6.)
        self.assertLess(low, np.linalg.norm(beta)); self.assertGreater(high, np.linalg.norm(beta))
        with self.assertRaises(ValueError):
            flux_to_beta(1, 0)

    def test_endpoint_optical_invariant_and_temperature(self):
        z, da, dl, d = endpoint_boost(.3, 10., 16.9, [1, 0, 0], [.2, 0, 0])
        self.assertAlmostEqual((1+z)*da, 13.)
        self.assertAlmostEqual(dl/da, (1+z)**2)
        beta = np.array([.2, .1, 0]); gamma = four_velocity(beta)[0]
        t, recovered = inverse_temperature_boost(gamma/2.7, -gamma*beta/2.7)
        self.assertAlmostEqual(t, 2.7); assert_allclose(recovered, beta)

    def test_homogeneous_geometry_without_a_type_selection(self):
        self.assertEqual(homogeneous_scalar_curvature(np.eye(3), np.zeros(3)), 1.5)
        self.assertEqual(homogeneous_scalar_curvature(np.diag([1, 1, 5]), np.zeros(3)), -2.5)
        self.assertEqual(homogeneous_scalar_curvature(np.zeros((3, 3)), [1, 0, 0]), -6.)
        with self.assertRaises(ValueError):
            homogeneous_scalar_curvature(np.eye(3), [1, 0, 0])
        # SU(2) orthonormal frame; Koszul gives Gamma=C/2.
        c = np.zeros((3, 3, 3))
        for k, i, j in [(0, 1, 2), (1, 2, 0), (2, 0, 1)]:
            c[k, i, j] = 1.; c[k, j, i] = -1.
        g = homogeneous_connection(c)
        assert_allclose(g, c/2)
        assert_allclose(homogeneous_codazzi_flux(c, np.eye(3), kappa=1), 0.)
        lam = np.array([1., 2., 4.]); dt = np.zeros((3, 3, 3))
        for k in range(3):
            for i in range(3):
                for j in range(3):
                    dt[k, i, j] = (lam[i]-lam[j])*g[j, k, i]
        assert_allclose(invariant_eigenframe_structure(lam, dt, invariant_on_homogeneous_neighborhood=True), c)
        with self.assertRaises(NumericalUnresolved):
            invariant_eigenframe_structure([1, 1, 2], dt, invariant_on_homogeneous_neighborhood=True)

    def test_velocity_jet_all_sectors_and_lorentz_covariance(self):
        u = np.array([1., 0, 0, 0]); d = np.zeros((4, 4))
        d[0, 1:] = [.2, -.1, .3]
        d[1:, 1:] = [[2, .4, 0], [-.4, 3, 0], [0, 0, 4]]
        result = kinematics_from_velocity_jet(u, d, speed_of_light=2, congruence="U", frame="rest tetrad")
        self.assertEqual(result.expansion, 18.)
        assert_allclose(result.shear_covariant[1:, 1:], np.diag([-2, 0, 2]))
        self.assertAlmostEqual(result.vorticity_covariant[1, 2], .8)
        assert_allclose(result.acceleration_covariant[1:], [.8, -.4, 1.2])
        beta = np.array([.2, -.1, .03]); inv = lorentz_boost(-beta)
        boosted = kinematics_from_velocity_jet(four_velocity(beta), inv.T@d@inv, speed_of_light=2, congruence="U", frame="boosted tetrad")
        self.assertAlmostEqual(boosted.expansion, result.expansion)
        assert_allclose(boosted.shear_covariant, inv.T@result.shear_covariant@inv, atol=1e-14)
        assert_allclose(boosted.vorticity_covariant, inv.T@result.vorticity_covariant@inv, atol=1e-14)
        assert_allclose(boosted.acceleration_covariant, inv.T@result.acceleration_covariant, atol=1e-14)
        d[0, 0] = 1
        with self.assertRaises(ValueError):
            kinematics_from_velocity_jet(u, d, speed_of_light=2, congruence="U", frame="rest tetrad")

    def test_hamiltonian_and_drift_coefficients(self):
        # Flat FLRW constraint: 2*kappa*E=2*theta^2/(3*c^2).
        self.assertAlmostEqual(hamiltonian_orbit_curvature(energy_density_normal=3, cosmological_constant=0, theta_normal=6, shear_full_contraction=0, kappa=1, speed_of_light=2), 0.)
        s = np.diag([1., 2., -3.]); w = np.array([[0, .3, 0], [-.3, 0, .1], [0, -.1, 0]])
        recovered_s, recovered_w = ideal_position_drift_moment(s/5+w/3, ideal_full_sky_calibrated_geodesic=True)
        assert_allclose(recovered_s, s); assert_allclose(recovered_w, w)

    def test_causal_type_and_nonrepresentable_outputs_fail(self):
        with self.assertRaises(ValueError):
            unit_timelike([1, 1, 0, 0], tolerance=2)
        with np.errstate(over="ignore", invalid="ignore"):
            with self.assertRaises(NumericalUnresolved):
                homogeneous_scalar_curvature(1e200*np.eye(3), [0, 0, 0])
            with self.assertRaises(NumericalUnresolved):
                perfect_fluid_normal_projection(1e308, 0, [.9, 0, 0])
            with self.assertRaises(NumericalUnresolved):
                inverse_temperature_boost(1e-308, [-.9e-308, 0, 0])
            with self.assertRaises(NumericalUnresolved):
                ideal_position_drift_moment(np.diag([1e308, -1e308, 0]), ideal_full_sky_calibrated_geodesic=True)


class PhysicalBudgetTests(unittest.TestCase):
    def test_stress_all_kinematic_sectors_and_zero_body(self):
        context = StressBudgetContext("total", "energy_eigenvector", "orthonormal", "t0", "positive 4x3 norm", "analytic fixture")
        budget = stress_gap_budget(derivative_bound=2, spectral_gap_lower=4, speed_of_light=2, context=context)
        x = np.zeros(12); x[0] = np.sqrt(3)
        self.assertAlmostEqual(budget.gauge(x), 1.)
        x[:] = 0; x[-1] = 2
        self.assertAlmostEqual(budget.gauge(x), 1.)
        zero = stress_gap_budget(derivative_bound=0, spectral_gap_lower=4, speed_of_light=2, context=context)
        self.assertEqual(zero.gauge(np.zeros(12)), 0.)
        self.assertEqual(zero.gauge(x), np.inf)

    def test_weak_boundary_and_uncertain_coefficient_error(self):
        args = dict(integral_ws=[5, 6], integral_wprime_m=[3, 4], endpoint_a=[1, 2], endpoint_b=[2, 3], lipschitz_bound=2, variation_integral=3, numerical_error=.1, provenance="exact polynomial integrals")
        result = weak_response_budget(**args, coefficient_error_integral=.5, kinematic_bound=4)
        assert_allclose(result.response, [7, 9]); self.assertAlmostEqual(result.error_radius, 8.1)
        with self.assertRaises(ValueError):
            weak_response_budget(**args, coefficient_error_integral=.5)


if __name__ == "__main__":
    unittest.main()
