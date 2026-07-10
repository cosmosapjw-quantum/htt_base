"""EGS3 Axis G gates (v9 follow-on, REV-R181): KE-FRAME/KE-CONSTR/KE-OBS.

Items 1-7 of the registered ten-item King-Ellis rotating-congruence
rederivation program (t3_king_ellis.yaml, from review R1 3.4):

G-KE-1  congruence definitions + exact kinematic decomposition for the
        slice normal AND the tilted congruence; Frobenius omega[n] = 0 and
        aligned-tilt omega[u] = 0 exact; kinematic scalars x-independent
        (group invariance);
G-KE-2  KE-OBS exact vorticity classification: the closed form
        omega_ab omega^ab = (S^2 sin^2 phi/2)(S cos phi (H1-H2)
        - cosh(b) c/a1)^2 verified symbolically; the type-I oblique
        CORRECTION finding (NOT identically irrotational at Omega_k = 0);
        the leading-order slaving reduction;
G-KE-3  contracted Gauss identity DERIVED (coefficients from exact
        rational-point linear systems, gamma = -2/3, alpha = beta = 1)
        and verified identically on five configurations including two
        rotating ones;
G-KE-4  tilted-fluid matter decomposition in both frames (n-frame
        cosh/sinh closed forms; u-frame trivial exactly);
G-KE-5  u-frame momentum-constraint components exist (matter side exactly
        zero) -- the constraint surface for the dynamics phase;
G-KE-6  type-V structure constants: commutators, Jacobi, n^{ab} = 0;
G-KE-7  seal PASS + Wolfram second-engine seal PASS with exact rational
        cross-engine anchor equality;
G-KE-CoVe  x_C bit-identity three-route anchor + forbidden-string guard +
        the T3 lower-endpoint withdrawal stays asserted in scope.
"""
import json
from pathlib import Path
import unittest

import numpy as np

from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_king_ellis_frame import (
    congruence_definitions,
    frame_kinematics,
    gauss_identity,
    ke_obs_vorticity_theorem,
    king_ellis_frame_seal,
    matter_frames,
    momentum_constraint,
    structure_constants,
)
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix

REPO = Path(__file__).resolve().parents[3]
_SEAL = king_ellis_frame_seal()   # heavy symbolics cached once per process


class GKE1KinematicsAndFrobenius(unittest.TestCase):
    def test_definitions_and_frobenius(self):
        defs = congruence_definitions()
        self.assertIn("group-invariant", defs["tilted"])
        obs = ke_obs_vorticity_theorem()
        self.assertTrue(obs["frobenius_normal_zero"])
        self.assertTrue(obs["aligned_zero_bianchi_v"])

    def test_scalars_group_invariant(self):
        for tilt in ("normal", "aligned", "transverse"):
            self.assertTrue(
                frame_kinematics("bianchi_v", tilt)["x_independent"], tilt)


class GKE2VorticityClassification(unittest.TestCase):
    def test_closed_form_and_correction_finding(self):
        obs = ke_obs_vorticity_theorem()
        self.assertTrue(obs["closed_form_verified"])
        self.assertTrue(obs["type_i_oblique_form_verified"])
        # the CORRECTION finding: Omega_k = 0 is NOT identically
        # irrotational for oblique group-invariant tilt
        self.assertTrue(obs["type_i_not_identically_irrotational"])
        self.assertTrue(obs["transverse_v_reduction"])
        self.assertTrue(obs["type_v_cancellation_surface_exists"])
        self.assertTrue(obs["slaving_leading_order_verified"])


class GKE3GaussIdentityDerived(unittest.TestCase):
    def test_coefficients_and_symbolic_residuals(self):
        g = gauss_identity()
        self.assertEqual((g["gamma"], g["alpha"], g["beta"]),
                         ("-2/3", "1", "1"))
        self.assertTrue(all(g["checks"].values()),
                        [k for k, v in g["checks"].items() if not v])
        self.assertIn("non_integrability_note", g)


class GKE4MatterFrames(unittest.TestCase):
    def test_both_frame_decompositions_exact(self):
        m = matter_frames()
        self.assertTrue(all(m["checks"].values()))


class GKE5MomentumConstraint(unittest.TestCase):
    def test_uframe_components_and_matter_side(self):
        mc = momentum_constraint()
        self.assertTrue(mc["matter_side_zero_exact"])
        self.assertTrue(mc["aligned"])     # nonzero geometric components
        self.assertTrue(mc["transverse"])


class GKE6StructureConstants(unittest.TestCase):
    def test_type_v_algebra(self):
        s = structure_constants()
        self.assertTrue(s["commutators_match_type_v"])
        self.assertTrue(s["jacobi"])
        self.assertTrue(s["n_ab_zero"])


class GKE7SealAndCrossEngine(unittest.TestCase):
    def test_seal_pass_scope_and_items(self):
        self.assertEqual(_SEAL["status"], "PASS")
        self.assertEqual(_SEAL["theorem_id"], "KE-FRAME/KE-CONSTR/KE-OBS")
        self.assertIn("1-7", _SEAL["items_discharged"])
        self.assertIn("withdrawal for the slice-normal", " ".join(
            _SEAL["scope_not_claimed"].split()))

    def test_wolfram_second_engine_anchor_equality(self):
        path = REPO / "docs/generated/king_ellis_frame_wolfram_seal.json"
        self.assertTrue(path.exists(), "wolfram seal missing (run "
                        "scripts/run_egs3_v9_seals.py)")
        wseal = json.loads(path.read_text())
        if wseal.get("status", "").startswith("BLOCKED"):
            self.skipTest(f"registered blocker: {wseal['status']}")
        self.assertEqual(wseal["status"], "PASS")
        self.assertTrue(wseal["checks"]["cross_engine_anchor_match_sympy"])
        self.assertEqual(wseal["anchors"],
                         _SEAL["rational_point_anchor"]["values"])


class GKECoVeAdversarialGuard(unittest.TestCase):
    FORBIDDEN_STRINGS = ("posterior", "detection", "native solver",
                         "family assignment")

    def test_x_c_anchor_bit_identical(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        inline = 0.12 - 0.0 + 0.03 + 0.0
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_graded, inline))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_module_docstring_forbidden_strings_and_withdrawal(self):
        import htt.obsstat.egs3_king_ellis_frame as mod
        doc = (mod.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc)
        # the T3 lower-endpoint withdrawal must remain asserted
        self.assertIn("withdrawal", doc)
