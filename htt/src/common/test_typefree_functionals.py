import unittest
from dataclasses import replace

import numpy as np

from common.anchor_geometry import (AnchorBodySpec, AnchorGeometryKind, AnchorBlockSpec,
                                    PolytopeHalfspace)
from common.typefree_functionals import (FunctionalSpec, FunctionalRecord, RelativeAnchor,
    evaluate_paired_anchor, support_utilization, anchor_support, FiniteJointSource,
    finite_joint_pushforward, strict_exceedance, ratio_value, UndefinedValue)


def spec(labels=("x", "y")):
    return FunctionalSpec("test.vector.v1", labels, (len(labels),), 1, "polar", "orthonormal",
                          "rate", "frame", "epoch", "finite-test-domain", "raw", "exact", "supplied")


def ellipsoid(q=((.25, 0), (0, 1)), labels=("x", "y")):
    return AnchorBodySpec("body", AnchorGeometryKind.ELLIPSOID, labels, "frame", "raw",
                          "exact", "supplied", "supplied-test-body", quadratic_form=q)


class PairedFunctionalTests(unittest.TestCase):
    def test_existing_quadratic_semantics_signed_margin_and_anisotropic_support(self):
        body = ellipsoid()
        rec = FunctionalRecord("one", spec(), [2, 0], [0, 0], body)
        self.assertEqual(evaluate_paired_anchor(rec).gauge, 1)
        beyond = FunctionalRecord("two", spec(), [4, 0], [0, 0], body)
        self.assertEqual(evaluate_paired_anchor(beyond).gauge, 2)
        self.assertEqual(evaluate_paired_anchor(beyond).margin, -1)
        vertical = FunctionalRecord("three", spec(), [0, 2], [0, 0], body)
        self.assertEqual(support_utilization(rec, [1, 0]).value, 1)
        self.assertEqual(support_utilization(vertical, [0, 1]).value, 2)
        opposite = replace(rec, values=np.array([-2., 0.]))
        self.assertEqual(support_utilization(opposite, [1, 0]).value, -1)

    def test_relative_span_zero_span_and_immutable_copies(self):
        small = ellipsoid(((1.,),), ("relative_x",))
        embedding = np.array([[1.], [0.]])
        relative = RelativeAnchor("relative", ("x", "y"), "frame", "raw", "exact",
                                  "supplied", embedding, small)
        embedding[0, 0] = 4
        self.assertEqual(relative.embedding[0, 0], 1)
        with self.assertRaises(ValueError):
            relative.embedding.setflags(write=True)
        rec = FunctionalRecord("one", spec(), [0, 1], [0, 0], relative)
        self.assertEqual(evaluate_paired_anchor(rec).status, "OUTSIDE_RELATIVE_SPAN")
        inside = replace(rec, values=np.array([.5, 0.]))
        self.assertEqual(evaluate_paired_anchor(inside).gauge, .5)
        self.assertEqual(support_utilization(inside, [0, 1]).status, "ZERO_SUPPORT_DIRECTION")
        zero = replace(relative, body=None, embedding=np.empty((2, 0)))
        origin = replace(rec, values=np.zeros(2), anchor=zero)
        result = evaluate_paired_anchor(origin)
        self.assertEqual((result.gauge, result.member, result.status), (0, True, "NO_DIRECTIONS"))
        self.assertEqual(support_utilization(origin, [1, 0]).status, "NO_DIRECTIONS")
        self.assertEqual(evaluate_paired_anchor(replace(rec, anchor=zero)).status, "OUTSIDE_RELATIVE_SPAN")

    def test_product_and_exact_polytope_support(self):
        product = AnchorBodySpec("product", AnchorGeometryKind.PRODUCT_BLOCK_BALL,
            ("x", "y"), "frame", "raw", "exact", "supplied", "test",
            blocks=(AnchorBlockSpec("x", (0,), 2), AnchorBlockSpec("y", (1,), 1)))
        self.assertEqual(anchor_support(product, [1, 1]), 3)
        poly = AnchorBodySpec("box", AnchorGeometryKind.POLYTOPE, ("x", "y"),
            "frame", "raw", "exact", "supplied", "test",
            halfspaces=tuple(PolytopeHalfspace(n, b) for n, b in
                [((1, 0), 2), ((-1, 0), 2), ((0, 1), 1), ((0, -1), 1)]))
        self.assertEqual(anchor_support(poly, [1, 1]), 3)

    def test_missing_and_definition_channel_mismatch_remain_explicit(self):
        rec = FunctionalRecord("one", spec(), [1, 2], [0, 0])
        self.assertEqual(evaluate_paired_anchor(rec).status, "MISSING_ANCHOR")
        self.assertEqual(evaluate_paired_anchor(replace(rec, anchor=ellipsoid(),
            spec=replace(spec(), frame="another"))).status, "CHANNEL_MISMATCH")
        with self.assertRaises(ValueError):
            FunctionalRecord("one", spec(), [1, np.nan], [0, 0])
        with self.assertRaises(ValueError):
            FunctionalRecord("one", spec(), [1, 2], None)

    def test_same_marginals_different_joint_pairing_and_permutation(self):
        one = spec(("value",))
        def image(pairs):
            rows = tuple(FunctionalRecord(str(i), one, [n], [d]) for i, (n, d) in enumerate(pairs))
            source = FiniteJointSource("joint", rows, "EMPIRICAL", "original")
            return finite_joint_pushforward(source, lambda r: ratio_value(r.values, r.reference),
                                             definition_id="ratio.v1", target_domain_id="ratio-with-undefined")
        comonotone = image([(1, 1), (2, 2)])
        opposite = image([(1, 2), (2, 1)])
        self.assertEqual(strict_exceedance(comonotone, 1).lower, 0)
        self.assertEqual(strict_exceedance(opposite, 1).lower, .5)
        self.assertEqual(strict_exceedance(image([(2, 1), (1, 2)]), 1).lower, .5)
        self.assertEqual(np.mean([a.value.item() for a in opposite.atoms]), 1.25)

    def test_undefined_mass_is_not_renormalized_and_nan_never_ok(self):
        one = spec(("value",))
        source = FiniteJointSource("joint", (
            FunctionalRecord("a", one, [1], [1]),
            FunctionalRecord("b", one, [1], [0])), "POSTERIOR", "original", (.25, .75))
        image = finite_joint_pushforward(source, lambda r: ratio_value(r.values, r.reference),
                                         definition_id="ratio.v1", target_domain_id="unconditional-with-undefined")
        self.assertEqual(image.undefined_mass, .75)
        result = strict_exceedance(image, 0)
        self.assertEqual((result.lower, result.upper, result.undefined_mass), (.25, 1, .75))
        self.assertEqual(strict_exceedance(image, 1).lower, 0)
        self.assertIsInstance(ratio_value(np.nan, 1), UndefinedValue)
        nan = finite_joint_pushforward(source, lambda r: np.nan,
                                      definition_id="bad", target_domain_id="original")
        self.assertEqual(nan.undefined_mass, 1)
        self.assertIsInstance(ratio_value(1, -1, positive_denominator=True), UndefinedValue)

    def test_empty_set_and_vector_scalarization(self):
        empty = FiniteJointSource("set", (), "FINITE_SET", "empty")
        image = finite_joint_pushforward(empty, lambda r: r.values,
                                        definition_id="identity", target_domain_id="empty-image")
        self.assertEqual(image.status, "EMPTY_SET")
        with self.assertRaises(TypeError):
            strict_exceedance(image, 0)
        with self.assertRaises(ValueError):
            FiniteJointSource("empty-law", (), "EMPIRICAL", "empty")
        source = FiniteJointSource("joint", (FunctionalRecord("a", spec(), [1, 2], [0, 0]),),
                                   "NULL", "finite")
        image = finite_joint_pushforward(source, lambda r: r.values,
                                         definition_id="vector", target_domain_id="finite")
        with self.assertRaises(ValueError):
            strict_exceedance(image, 1)
        self.assertEqual(strict_exceedance(image, 1, scalarization=lambda x: x[0],
                         scalarization_id="first-coordinate").lower, 0)


if __name__ == "__main__":
    unittest.main()
