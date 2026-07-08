"""EGS3 Axis F gates: physics/convention seals (B1 repair, P5, P13 companion).

F1 parent-identity SymPy seal: the Gauss constraint forces c = (+1,-1,+1,+1) and
   W^2 = omega_ab omega^ab/(6 H^2); the v5-document convention omega_a omega^a/H^2
   is exactly 3x the registered value; the (3/2) MES conversion rule is DERIVED;
   the MES epsilon coefficients equal the code-side registered constants
   (provenance comparison, not a rederivation);
F2 Bianchi V constraint seal: the momentum constraint reproduces the conditional
   P5 formula symbolically; the exact-rapidity correction is (4/3) beta^2; the
   numeric relative error scales as beta^2; Omega_K <= 0 raises (P5 domain);
F3 shear-memory kernel bias: fitting the registered scalar closure on exact
   linearized-1+3 trajectories is unbiased exactly at the friction-matching toy
   Weyl closure e0 = 1 and increasingly biased away from it (the quantitative
   content of the P13 DERIVED_CONDITIONAL demotion);
F4 (CoVe adversarial) the seal conclusions survive parameter sweeps; the on-disk
   seal artifacts are PASS; no family/geometry keys appear in the seals.

Diagnostic-only; no detection, family/geometry (the Bianchi V label is the
CONDITION of a legacy-recovery statement), native-solver, or posterior claim.
"""
import json
import unittest
from fractions import Fraction
from pathlib import Path

import numpy as np

from htt.obsstat import egs3_parent_identity as pid
from htt.obsstat.egs3_parent_identity import (
    parent_identity_seal, derive_parent_identity, w2_convention_table,
    three_halves_rule, MES_EPSILON_COEFFICIENTS, COMPARATOR_SIGN_VECTOR,
)
from htt.obsstat.egs3_bianchi_v_constraint import (
    bianchi_v_seal, symbolic_p5_formula, exact_tilt_correction_series,
    numeric_scaling_witness, p5_leading_sigma_plus_sq, exact_rapidity_sigma_plus_sq,
)
from htt.obsstat.egs3_shear_memory_bias import (
    kappa_bias_curve, exact_linearized_shear, registered_law_shear,
    fit_registered_kappa,
)

REPO = Path(__file__).resolve().parents[3]
GENERATED = REPO / "docs" / "generated"


class F1ParentIdentitySealTests(unittest.TestCase):
    def test_seal_passes(self):
        seal = parent_identity_seal()
        self.assertEqual(seal["status"], "PASS")

    def test_comparator_signs_derived_not_postulated(self):
        parent = derive_parent_identity()
        self.assertTrue(parent["identity_ok"])
        self.assertEqual(tuple(parent["c_derived"]), COMPARATOR_SIGN_VECTOR)
        self.assertEqual(tuple(parent["c_derived"]), (1, -1, 1, 1))

    def test_w2_mismatch_factor_is_exactly_three(self):
        w2 = w2_convention_table()
        self.assertTrue(w2["tensor_equals_twice_vector"])
        self.assertEqual(w2["mismatch_factor"], 3)

    def test_three_halves_rule_derived(self):
        rule = three_halves_rule()
        self.assertTrue(rule["factor_is_three_halves"])

    def test_mes_coefficients_match_code_registered_constants(self):
        # provenance comparison against the code-side SSoT (not a rederivation)
        from htt.tsc.admissibility.three_bound_hierarchy import COEFFS
        code = {name: tuple(coeffs) for name, coeffs in COEFFS.items()}
        registered = {
            "B_sigma": MES_EPSILON_COEFFICIENTS["B_sigma"],
            "B_omega": MES_EPSILON_COEFFICIENTS["B_omega"],
        }
        for name, fracs in registered.items():
            key = {"B_sigma": "sigma", "B_omega": "omega"}[name]
            match = [k for k in code if key in k.lower()]
            self.assertTrue(match, f"no code coefficient set matching {name}")
            self.assertEqual(tuple(Fraction(f) for f in code[match[0]]),
                             tuple(fracs))


class F2BianchiVConstraintTests(unittest.TestCase):
    def test_seal_passes(self):
        seal = bianchi_v_seal()
        self.assertEqual(seal["status"], "PASS")
        self.assertIn("constraint-algebra", seal["scope"])

    def test_symbolic_identity(self):
        self.assertTrue(symbolic_p5_formula()["identity_ok"])

    def test_exact_rapidity_correction_is_four_thirds_beta_sq(self):
        self.assertTrue(
            exact_tilt_correction_series()["coefficient_is_four_thirds"])

    def test_numeric_slope_is_two(self):
        wit = numeric_scaling_witness()
        self.assertLess(abs(wit.loglog_slope - 2.0), 0.05)

    def test_omega_k_domain_raises(self):
        with self.assertRaises(ValueError):
            p5_leading_sigma_plus_sq(1e-3, A=0.0, w=0.0, Omega_m=0.6)
        with self.assertRaises(ValueError):
            exact_rapidity_sigma_plus_sq(1e-3, A=0.0, w=0.0, Omega_m=0.6)


class F3ShearMemoryBiasTests(unittest.TestCase):
    def test_unbiased_exactly_at_friction_matching_closure(self):
        curve = kappa_bias_curve()
        idx = curve.e0_grid.index(1.0)
        self.assertLess(abs(curve.kappa_bias_ratio[idx]), 1e-9)
        self.assertEqual(curve.zero_crossing_e0, 1.0)

    def test_bias_grows_away_from_e0_one(self):
        curve = kappa_bias_curve()
        biases = dict(zip(curve.e0_grid, curve.kappa_bias_ratio))
        self.assertGreater(biases[0.0], biases[0.5])
        self.assertGreater(biases[0.5], 0.0)
        self.assertLess(biases[1.5], 0.0)
        self.assertLess(biases[2.0], biases[1.5])

    def test_trajectories_differ_under_same_history_for_e0_not_one(self):
        z = np.linspace(0.0, 3.0, 121)
        exact = exact_linearized_shear(z, e0=0.0, kappa=1.0)
        registered = registered_law_shear(z, kappa_hat=0.5)
        self.assertGreater(float(np.max(np.abs(exact - registered))), 1e-6)
        # ... and coincide exactly at e0 = 1 with kappa_hat = kappa/2
        exact_match = exact_linearized_shear(z, e0=1.0, kappa=1.0)
        registered_match = registered_law_shear(z, kappa_hat=0.5)
        self.assertLess(float(np.max(np.abs(exact_match - registered_match))), 1e-12)

    def test_zero_history_is_unidentified(self):
        z = np.linspace(0.0, 3.0, 11)
        with self.assertRaises(ValueError):
            fit_registered_kappa(np.zeros(11), np.zeros(11), np.zeros(11))


class F4CoVeAdversarialTests(unittest.TestCase):
    def test_bias_zero_crossing_robust_to_history_parameters(self):
        for pi0, z0, H in [(1e-3, 1.0, 1.0), (5e-4, 0.5, 1.3), (2e-3, 2.0, 0.7)]:
            curve = kappa_bias_curve(pi0=pi0, z0=z0, H=H)
            idx = curve.e0_grid.index(1.0)
            self.assertLess(abs(curve.kappa_bias_ratio[idx]), 1e-9)

    def test_bianchi_slope_robust_to_background_parameters(self):
        for A, w, Om in [(0.5, 0.0, 0.6), (0.3, 1.0 / 3.0, 0.4), (0.8, 0.0, 0.9)]:
            wit = numeric_scaling_witness(A=A, w=w, Omega_m=Om)
            self.assertLess(abs(wit.loglog_slope - 2.0), 0.05)

    def test_seal_artifacts_on_disk_pass(self):
        for name in ("parent_identity_seal.json", "bianchi_v_constraint_seal.json"):
            path = GENERATED / name
            if not path.exists():
                self.skipTest(f"{name} absent -- run `make egs3-seals` first")
            payload = json.loads(path.read_text())
            self.assertEqual(payload["status"], "PASS")
            self.assertIn("claim_boundary", payload)

    def test_seals_carry_no_family_or_geometry_keys(self):
        for seal in (parent_identity_seal(), bianchi_v_seal()):
            flat = json.dumps(seal).lower()
            self.assertNotIn("family_detected", flat)
            self.assertNotIn("geometry_claim", flat)
            self.assertNotIn("detected", flat)            # no affirmative detection
            self.assertIn("claim_boundary", seal)

    def test_module_adds_no_registered_statistic(self):
        names = set(dir(pid))
        self.assertNotIn("channel_response_design", names)
        self.assertNotIn("_RESPONSE_SUPPORT", names)


if __name__ == "__main__":
    unittest.main()
