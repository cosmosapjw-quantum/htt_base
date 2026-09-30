"""Deterministic, catalogue-free endpoint law and F6 regression checks."""
from dataclasses import replace
import math
import unittest

import numpy as np

from htt.infer.endpoint_cosmography import (
    COEFFICIENT_NAMES, DistanceTreatment, EndpointInferenceUnavailable,
    EndpointObservations, EndpointRankUnresolved, FiniteDistanceRemainder,
    GaussianStateLaw, RemainderKind, compare_gaussian_state_laws,
    endpoint_design, endpoint_log_likelihood, fit_endpoint_cosmography,
)


def fixture(count=72):
    index = np.arange(count, dtype=float)
    nz = 1 - 2 * (index + .5) / count
    azimuth = index * math.pi * (3 - math.sqrt(5))
    directions = np.column_stack((np.sqrt(1 - nz*nz) * np.cos(azimuth),
                                  np.sqrt(1 - nz*nz) * np.sin(azimuth), nz))
    distance = 10 + ((17 * index) % 91)
    intercept = np.array([1.04, .08, -.04, .02])
    h0 = 70.
    h1 = np.array([4., -3., 2.])
    q = np.array([[3., 1., -.5], [1., -2., .7], [-.5, .7, -1.]])
    # Construct the synthetic observable from the physical contraction, not
    # the implementation's design helper.
    one_plus_z = (intercept[0] + directions @ intercept[1:]
                  + distance / 299792.458 * (h0 + directions @ h1
                    + np.einsum("ni,ij,nj->n", directions, q, directions)))
    coefficients = np.r_[intercept, h0, h1, q[0, 0], q[1, 1], q[0, 1], q[0, 2], q[1, 2]]
    v, w = np.cos(index / 7), np.sin(index / 5)
    covariance = 1e-8 * (np.diag(1 + index / count) + .3*np.outer(v, v) + .2*np.outer(w, w))
    ids = tuple(f"synthetic:{i}" for i in range(count))
    observations = EndpointObservations(
        row_ids=ids, directions=directions, redshift=one_plus_z - 1,
        area_distance_mpc=distance, covariance=covariance,
        covariance_row_ids=ids, support_mask=np.ones(count, dtype=bool),
        source_congruence="synthetic common smooth material U",
        observer_frame="synthetic observer O", redshift_frame="synthetic observer O",
        direction_frame="synthetic orthonormal right-handed Cartesian basis",
        redshift_correction_source="NATIVE_OBSERVER_NO_CORRECTION",
        distance_treatment=DistanceTreatment.FIXED_INDEPENDENT_AREA_DISTANCE,
        distance_source="synthetic independent exact d_A in Mpc",
        selection_source="fixed synthetic design; outcome independent",
        covariance_source="declared synthetic known joint Gaussian covariance",
        remainder=FiniteDistanceRemainder(RemainderKind.EXACT_ZERO_ASSUMED, "synthetic truncated relation"),
    )
    return observations, coefficients


def subset(observations, order):
    order = np.asarray(order)
    ids = tuple(observations.row_ids[i] for i in order)
    bounds = observations.remainder.absolute_bounds
    remainder = (observations.remainder if bounds is None else
                 replace(observations.remainder, absolute_bounds=bounds[order]))
    return replace(
        observations, row_ids=ids, covariance_row_ids=ids,
        directions=observations.directions[order], redshift=observations.redshift[order],
        area_distance_mpc=observations.area_distance_mpc[order],
        covariance=observations.covariance[np.ix_(order, order)],
        support_mask=observations.support_mask[order], remainder=remainder,
    )


class EndpointCosmographyTests(unittest.TestCase):
    def test_free_intercept_and_all_slope_coefficients_recover(self):
        observations, truth = fixture()
        result = fit_endpoint_cosmography(observations)
        np.testing.assert_allclose(result.coefficients, truth, rtol=0, atol=2e-10)
        self.assertEqual(result.design_rank, 13)
        self.assertEqual(result.coefficient_names, COEFFICIENT_NAMES)
        self.assertEqual(result.observer_frame, observations.observer_frame)
        self.assertEqual(result.source_congruence, observations.source_congruence)
        self.assertEqual(result.coefficient_identification_status, "IDENTIFIED_WITHIN_EXACT_TRUNCATED_CONDITIONAL_MODEL")
        self.assertEqual(result.empirical_coverage_status, "NOT_CALIBRATED")
        self.assertEqual(result.normal_tilt_status, "UNAVAILABLE_NO_GEOMETRIC_NORMAL")
        # The arbitrary statistical intercept is not silently projected to a
        # unit physical four-velocity, even if it is inconsistent with one.
        self.assertGreater(abs(result.coefficients[0]**2 - result.coefficients[1:4] @ result.coefficients[1:4] - 1), .01)
        forced = endpoint_design(observations.directions, observations.area_distance_mpc)[:, 4:]
        chol = np.linalg.cholesky(observations.covariance)
        wrong, *_ = np.linalg.lstsq(np.linalg.solve(chol, forced),
                                    np.linalg.solve(chol, observations.redshift), rcond=None)
        self.assertGreater(np.linalg.norm(wrong - truth[4:]), 1.)

    def test_dense_gls_and_noise_covariance_match_independent_oracle(self):
        observations, _ = fixture()
        perturbation = 2e-4*np.cos(np.arange(len(observations.row_ids)) / 3)
        observations = replace(observations, redshift=observations.redshift + perturbation)
        result = fit_endpoint_cosmography(observations)
        design = endpoint_design(observations.directions, observations.area_distance_mpc)
        precision_design = np.linalg.solve(observations.covariance, design)
        normal = design.T @ precision_design
        expected_covariance = np.linalg.inv(normal)
        expected_coefficients = np.linalg.solve(normal, precision_design.T @ (1 + observations.redshift))
        np.testing.assert_allclose(result.coefficients, expected_coefficients, rtol=0, atol=3e-9)
        np.testing.assert_allclose(result.coefficient_covariance, expected_covariance, rtol=2e-10, atol=1e-14)
        self.assertGreater(np.max(abs(result.coefficient_covariance[:4, 4:])), 1e-8)
        diagonal = fit_endpoint_cosmography(replace(observations, covariance=np.diag(np.diag(observations.covariance))))
        self.assertGreater(np.linalg.norm(diagonal.coefficients - result.coefficients), 1e-3)
        residual = 1 + observations.redshift - design @ result.coefficients
        expected_ll = -.5*(residual @ np.linalg.solve(observations.covariance, residual)
                          + np.linalg.slogdet(observations.covariance)[1]
                          + len(residual)*math.log(2*math.pi))
        self.assertAlmostEqual(endpoint_log_likelihood(observations, result.coefficients), expected_ll, places=8)

    def test_mask_and_permutation_preserve_full_marginal_covariance(self):
        observations, truth = fixture()
        mask = np.arange(len(observations.row_ids)) % 4 != 0
        masked = replace(observations, support_mask=mask)
        fit_mask = fit_endpoint_cosmography(masked)
        selected = subset(observations, np.flatnonzero(mask))
        fit_selected = fit_endpoint_cosmography(selected)
        np.testing.assert_allclose(fit_mask.coefficient_covariance, fit_selected.coefficient_covariance, rtol=1e-13, atol=1e-16)
        self.assertEqual(fit_mask.selected_row_ids, selected.row_ids)
        order = np.arange(len(observations.row_ids))[::-1]
        reordered = subset(masked, order)
        fit_reordered = fit_endpoint_cosmography(reordered)
        np.testing.assert_allclose(fit_reordered.coefficients, truth, rtol=0, atol=3e-10)
        np.testing.assert_allclose(fit_reordered.coefficient_covariance, fit_mask.coefficient_covariance, rtol=2e-11, atol=1e-14)
        self.assertAlmostEqual(endpoint_log_likelihood(masked, truth), endpoint_log_likelihood(reordered, truth), places=9)
        with self.assertRaisesRegex(ValueError, "row order"):
            replace(observations, covariance_row_ids=observations.covariance_row_ids[::-1])

    def test_one_distance_shell_and_inadequate_support_fail_closed(self):
        observations, _ = fixture()
        with self.assertRaises(EndpointRankUnresolved):
            fit_endpoint_cosmography(replace(observations, area_distance_mpc=np.full(len(observations.row_ids), 50.)))
        with self.assertRaises(EndpointRankUnresolved):
            fit_endpoint_cosmography(subset(observations, np.arange(12)))
        with self.assertRaises(EndpointRankUnresolved):
            fit_endpoint_cosmography(observations, max_condition=1.)

    def test_finite_remainder_is_bias_not_noise_and_unknown_is_unavailable(self):
        observations, _ = fixture()
        bounds = np.full(len(observations.row_ids), 3e-5)
        remainder_spec = FiniteDistanceRemainder(RemainderKind.BOUNDED_DETERMINISTIC, "synthetic uniform bound", bounds)
        bounded = replace(observations, remainder=remainder_spec)
        result = fit_endpoint_cosmography(bounded)
        self.assertEqual(result.coefficient_identification_status, "BOUNDED_REMAINDER_SET_NO_POINT_IDENTIFICATION")
        nominal = fit_endpoint_cosmography(observations)
        np.testing.assert_array_equal(result.coefficient_covariance, nominal.coefficient_covariance)
        self.assertTrue(np.all(result.deterministic_bias_bound > 0))
        r = bounds * np.cos(np.arange(len(bounds)))
        displaced = fit_endpoint_cosmography(replace(bounded, redshift=bounded.redshift + r))
        self.assertTrue(np.all(abs(displaced.coefficients - result.coefficients) <= result.deterministic_bias_bound + 1e-10))
        self.assertTrue(np.isfinite(endpoint_log_likelihood(bounded, result.coefficients, remainder=r)))
        with self.assertRaisesRegex(EndpointInferenceUnavailable, "explicitly"):
            endpoint_log_likelihood(bounded, result.coefficients)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            endpoint_log_likelihood(bounded, result.coefficients, remainder=2*bounds)
        unknown = replace(observations, remainder=FiniteDistanceRemainder(RemainderKind.UNKNOWN, "not supplied"))
        with self.assertRaisesRegex(EndpointInferenceUnavailable, "unknown finite-distance"):
            fit_endpoint_cosmography(unknown)
        with self.assertRaisesRegex(EndpointInferenceUnavailable, "distance-error"):
            fit_endpoint_cosmography(replace(observations, distance_treatment=DistanceTreatment.ERROR_INTEGRATION_UNAVAILABLE))

    def test_invalid_frames_nan_shapes_and_covariance(self):
        observations, _ = fixture()
        invalid = [
            {"observer_frame": "unknown"}, {"redshift_frame": "different corrected frame"},
            {"redshift_correction_source": ""}, {"direction_convention": "PHOTON_PROPAGATION_DIRECTION"},
            {"direction_frame": ""}, {"distance_source": "unknown"},
            {"directions": observations.directions * 2},
            {"redshift": np.full(len(observations.row_ids), np.nan)},
            {"covariance": np.zeros_like(observations.covariance)},
            {"covariance": -observations.covariance},
            {"support_mask": np.ones(len(observations.row_ids), dtype=int)},
        ]
        for change in invalid:
            with self.subTest(field=next(iter(change))):
                with self.assertRaises((ValueError, TypeError)):
                    replace(observations, **change)
        self.assertFalse(observations.redshift.flags.writeable)
        self.assertFalse(observations.covariance.flags.writeable)


class FullLawComparisonTests(unittest.TestCase):
    def law(self, state_id="state A"):
        return GaussianStateLaw(state_id, "declared physical domain", "shared Gaussian response family",
                                "fixed design and calibration", "observer O", "fixed selected rows",
                                ("row 1", "row 2"), np.array([1., 2.]), np.array([[1., .25], [.25, 2.]]))

    def test_mean_and_covariance_are_both_required_for_full_law_equality(self):
        first = self.law()
        identical = replace(first, state_id="state B")
        comparison = compare_gaussian_state_laws(first, identical)
        self.assertTrue(comparison.equal_joint_gaussian_law)
        self.assertEqual(comparison.scope, "TWO_SUPPLIED_STATES_ONLY")
        different_covariance = replace(identical, covariance=identical.covariance + np.eye(2)*1e-12)
        # This is specifically smaller than customary allclose tolerances.
        self.assertTrue(np.allclose(first.covariance, different_covariance.covariance))
        negative = compare_gaussian_state_laws(first, different_covariance)
        self.assertTrue(negative.means_equal)
        self.assertFalse(negative.covariances_equal)
        self.assertFalse(negative.equal_joint_gaussian_law)
        different_mean = replace(identical, mean=identical.mean + np.array([0., 1e-12]))
        self.assertFalse(compare_gaussian_state_laws(first, different_mean).equal_joint_gaussian_law)

    def test_scope_and_order_are_explicit_and_singular_laws_remain_joint(self):
        first = self.law()
        for change in ({"domain_id": "other domain"}, {"shared_sampling_law_id": "other law"},
                       {"conditioning_id": "different calibration"}, {"frame_id": "different frame"},
                       {"measurement_ids": ("row 2", "row 1")}, {"selection_id": "other selection"}):
            with self.subTest(field=next(iter(change))):
                with self.assertRaisesRegex(ValueError, "shared"):
                    compare_gaussian_state_laws(first, replace(first, **change))
        singular = replace(first, covariance=np.diag([1., 0.]))
        self.assertTrue(compare_gaussian_state_laws(singular, replace(singular, state_id="second state")).equal_joint_gaussian_law)


if __name__ == "__main__":
    unittest.main()
