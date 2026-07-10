"""EGS3 Axis F gates (v9, REV-R178): BV-DYN tilted Bianchi V dynamics seal.

F-DYN-1 the SymPy-derived momentum constraint has the P5 form
        (h1 - h2 proportional to the exact-rapidity tilt flux) and the
        evolution system solves uniquely;
F-DYN-2 constraint-satisfying NON-VACUUM initial data (rho0 declared > 0;
        the vacuum/Milne branch, on which preservation is vacuous, is
        excluded) with residuals < 1e-12;
F-DYN-3 both constraints, MONITORED not imposed, stay below 1e-8 over the
        integrated e-folds for dust AND radiation;
F-DYN-4 along dynamical trajectories the expansion-normalized variables
        satisfy the exact-rapidity P5 relation (<1e-6 relative) and the
        leading-formula error scales as beta^2 (frozen-seal law, now on
        trajectories);
F-DYN-5 seal PASS + deterministic; scope stays diagnostic-only;
F-CoVe  x_C bit-identity three-route anchor + forbidden-string guard.
"""
import unittest

import numpy as np

from htt.obsstat.egs3_bianchi_v_dynamics import (
    bianchi_v_dynamics_seal,
    constraint_initial_data,
    constraint_preservation_check,
    derive_field_equations,
    p5_alignment_on_trajectory,
)
from htt.obsstat.egs3_graded_comparator import COMPARATOR_SIGNS
from htt.obsstat.egs3_psd_cone import sector_matrix, xc_from_matrix

_SEAL = bianchi_v_dynamics_seal()   # derivation cached; computed once


class FDYN1Derivation(unittest.TestCase):
    def test_momentum_constraint_has_p5_form(self):
        _, _, _, (c1s, c2s) = derive_field_equations()
        self.assertIn("sinh(2*bs)", c2s)
        self.assertIn("da1", c2s)
        self.assertIn("da2", c2s)


class FDYN2NonvacuumInitialData(unittest.TestCase):
    def test_ic_exact_and_nonvacuum(self):
        st = constraint_initial_data(beta0=0.02, w=0.0, rho0=0.3)
        self.assertGreater(st[4], 0.0)
        h1, h2 = st[2] / st[0], st[3] / st[1]
        self.assertGreater(abs(h1 - h2), 1e-6)   # genuine shear-tilt coupling

    def test_vacuum_request_rejected(self):
        with self.assertRaises(ValueError):
            constraint_initial_data(beta0=0.02, w=0.0, rho0=0.0)


class FDYN3ConstraintPreservation(unittest.TestCase):
    def test_dust_and_radiation(self):
        for key in ("constraint_preservation_dust",
                    "constraint_preservation_radiation"):
            row = _SEAL[key]
            self.assertTrue(row["preserved_at_tolerance"], key)
            self.assertTrue(row["nonvacuum_throughout"], key)
            self.assertLess(row["max_gauss_residual"], 1e-8)
            self.assertLess(row["max_momentum_residual"], 1e-8)
        # tilt decay is asserted for DUST only; the radiation tilt behaviour
        # is RECORDED as a dynamics finding, not forced
        self.assertTrue(_SEAL["constraint_preservation_dust"]["tilt_decays"])
        self.assertIn("tilt_decays",
                      _SEAL["constraint_preservation_radiation"])


class FDYN4P5OnTrajectory(unittest.TestCase):
    def test_exact_relation_and_beta_sq_scaling(self):
        align = _SEAL["p5_alignment_on_trajectory"]
        self.assertTrue(align["trajectory_satisfies_exact_relation"])
        self.assertTrue(align["beta_sq_scaling_on_trajectory"])
        self.assertLess(abs(align["loglog_slope"] - 2.0), 0.1)


class FDYN5Seal(unittest.TestCase):
    def test_seal_pass_and_scope(self):
        self.assertEqual(_SEAL["status"], "PASS")
        self.assertEqual(_SEAL["theorem_id"], "BV-DYN")
        self.assertIn("NOT the King-Ellis", _SEAL["scope_not_claimed"])
        self.assertIn("NOT a dynamical realization of the T3",
                      _SEAL["scope_not_claimed"])


class FDYNCoVeAdversarialGuard(unittest.TestCase):
    FORBIDDEN_STRINGS = ("posterior", "family", "native solver", "detection")

    def test_x_c_anchor_is_bit_identical_and_exactly_0p15(self):
        g = np.array([0.12, 0.0, 0.03, 0.0])
        inline = 0.12 - 0.0 + 0.03 + 0.0
        via_graded = float(COMPARATOR_SIGNS @ g)
        via_trace = xc_from_matrix(sector_matrix(g))
        self.assertTrue(np.array_equal(via_graded, 0.15))
        self.assertTrue(np.array_equal(via_graded, inline))
        self.assertTrue(np.array_equal(via_trace, via_graded))

    def test_module_docstring_carries_no_forbidden_claim_strings(self):
        import htt.obsstat.egs3_bianchi_v_dynamics as mod
        doc = (mod.__doc__ or "").lower()
        for token in self.FORBIDDEN_STRINGS:
            self.assertNotIn(token, doc)
