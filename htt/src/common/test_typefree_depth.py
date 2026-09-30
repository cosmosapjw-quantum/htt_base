import unittest
from dataclasses import replace

import numpy as np

from common.depth_path import DepthRepresentation
from common.typefree_functionals import FunctionalSpec, FunctionalRecord
from common.typefree_depth import signed_depth_transport
from common.r7_contracts import NumericalUnresolved


def record(label, values, *, frame="same", latent="joint", definition="signed-vector.v1"):
    labels = tuple(f"{label}:{i}" for i in range(len(values)))
    spec = FunctionalSpec(definition, labels, (len(values),), 1, "polar", "orthonormal",
                          "rate", frame, label, "path", "raw", "exact", "supplied")
    return FunctionalRecord(latent, spec, values, np.zeros(len(values)))


class SignedDepthTests(unittest.TestCase):
    def test_ambiguous_covariance_never_emits_negative_variance(self):
        rows = (record("a", [1]), record("b", [1]))
        rep = DepthRepresentation((1, 1), (np.eye(1),), ("a:0", "b:0"), "identity")
        for small in (-1e-15, 1e-15):
            with self.assertRaises(NumericalUnresolved):
                signed_depth_transport(rows, rep, transport_definition_id="identity.v1", covariance=np.diag([small, 1]))

    def test_sign_reversal_and_complete_joint_covariance(self):
        records = (record("a", [1]), record("b", [-1]))
        rep = DepthRepresentation((1, 1), (np.eye(1),), ("a:0", "b:0"), "identity")
        result = signed_depth_transport(records, rep, transport_definition_id="identity.v1",
                                         covariance=[[1, .8], [.8, 1]])
        np.testing.assert_array_equal(result.contrasts, [-2])
        self.assertEqual(result.signed_coherence, (-1,))
        np.testing.assert_allclose(result.contrast_covariance, [[.4]])
        np.testing.assert_array_equal(rep.restore(result.initial_and_contrasts), [1, -1])
        self.assertFalse(result.independent_likelihood)

    def test_missing_cross_blocks_and_fitted_transport(self):
        records = (record("a", [1]), record("b", [1]))
        rep = DepthRepresentation((1, 1), (np.eye(1),), ("a:0", "b:0"), "identity")
        missing = signed_depth_transport(records, rep, transport_definition_id="identity.v1",
                                          covariance_blocks={(0, 0): [[1]], (1, 1): [[1]]})
        self.assertIsNone(missing.contrast_covariance)
        self.assertEqual(missing.covariance_status, "COVARIANCE_UNAVAILABLE")
        fitted = replace(rep, transport_policy="FITTED_REQUIRES_JOINT_LAW")
        self.assertEqual(signed_depth_transport(records, fitted, transport_definition_id="fitted.v1",
                                               covariance=np.eye(2)).status, "SCENARIO_ONLY")

    def test_coordinate_permutation_with_map_and_covariance(self):
        rows = (record("a", [1, 2]), record("b", [3, 1]))
        k = np.diag([2., 1.])
        rep = DepthRepresentation((2, 2), (k,), ("a:0", "a:1", "b:0", "b:1"), "fixed")
        cov = np.array([[2, .2, .5, 0], [.2, 1, 0, .1], [.5, 0, 3, .3], [0, .1, .3, 2]])
        first = signed_depth_transport(rows, rep, transport_definition_id="fixed.v1", covariance=cov)
        perm = np.array([[0., 1.], [1., 0.]])
        joint = np.zeros((4, 4)); joint[:2, :2] = perm; joint[2:, 2:] = perm
        changed = tuple(replace(r, spec=replace(r.spec, coordinate_labels=r.spec.coordinate_labels[::-1]),
                                values=r.values[::-1], reference=r.reference[::-1]) for r in rows)
        rep2 = DepthRepresentation((2, 2), (perm@k@perm.T,),
                                   ("a:1", "a:0", "b:1", "b:0"), "permuted")
        second = signed_depth_transport(changed, rep2, transport_definition_id="fixed.v1",
                                          covariance=joint@cov@joint.T)
        np.testing.assert_allclose(second.contrasts, perm@first.contrasts)
        np.testing.assert_allclose(second.contrast_covariance, perm@first.contrast_covariance@perm.T)
        self.assertEqual(second.signed_coherence, first.signed_coherence)

    def test_zero_norm_and_explicit_frame_and_latent_binding(self):
        rows = (record("a", [0]), record("b", [1], frame="other"))
        rep = DepthRepresentation((1, 1), (np.eye(1),), ("a:0", "b:0"), "frame-map")
        with self.assertRaises(ValueError):
            signed_depth_transport(rows, rep, transport_definition_id="frame-map.v1")
        result = signed_depth_transport(rows, rep, transport_definition_id="frame-map.v1",
                                         frame_transports=(("same", "other"),))
        self.assertEqual(result.signed_coherence, (None,))
        with self.assertRaises(ValueError):
            signed_depth_transport((rows[0], replace(rows[1], latent_id="independent")), rep,
                                     transport_definition_id="frame-map.v1")

    def test_large_finite_coherence_does_not_overflow_the_norm(self):
        rows = (record("a", [1e200]), record("b", [1e200]))
        rep = DepthRepresentation((1, 1), (np.eye(1),), ("a:0", "b:0"), "identity")
        result = signed_depth_transport(rows, rep, transport_definition_id="identity.v1")
        self.assertEqual(result.signed_coherence, (1,))


if __name__ == "__main__":
    unittest.main()
