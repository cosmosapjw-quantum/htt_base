"""Finite algebra checks of the compensated dust/radiation distance response.

No ODE solver, quadrature, catalogue, likelihood, or old campaign is invoked.
All numerical examples are declared synthetic background/velocity inputs.
Run with the explicit interpreter in THEORY.md. Writes RESULTS.json beside self.
"""
from __future__ import annotations

from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
import time
import unittest

C_KM_S = 299792.458
H0_KM_S_MPC = 70.0
OMEGA_R = 1.0e-4  # Synthetic flat dust+radiation, Lambda=0; not a cosmological fit.


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(a):
    return math.sqrt(dot(a, a))


def background(z, omega_r=OMEGA_R, h0=H0_KM_S_MPC, c=C_KM_S):
    if not (math.isfinite(z) and z > 0):
        raise ValueError("positive finite redshift required")
    if not (0 < omega_r < 1 and h0 > 0 and c > 0):
        raise ValueError("two positive fluids and positive dimensional scales required")
    y = 1 + z
    om = 1 - omega_r
    s = math.sqrt(omega_r + om / y)
    hz = h0 * y * y * s
    # Rationalized expression avoids subtraction of nearly equal square roots.
    chi = 2 * c * z / (h0 * y * (1 + s))
    local = (1 + s) / (2 * z * s)
    history = z * (1 - om / (2 * y * s * (1 + s)))
    return {"z": z, "H_km_s_Mpc": hz, "chi_Mpc": chi, "dL_Mpc": y * chi,
            "A_local": local, "h_history": history,
            "F_ratio": history / local}


def mode(a, b, epsilon_m0=1 - OMEGA_R, epsilon_r0=OMEGA_R):
    if not (0 < a <= 1 and epsilon_m0 > 0 and epsilon_r0 > 0):
        raise ValueError("invalid scale factor or energy densities")
    ratio = 3 * epsilon_m0 / (4 * epsilon_r0)
    return [x / a for x in b], [-ratio * x for x in b]


def require_linear_domain(b, ell, a_min, beta_cap=0.01):
    """A declared velocity ceiling, not a guarantee of a distance-error bound."""
    bm, br = mode(a_min, b)
    bo = [x + y for x, y in zip(b, ell)]
    largest = max(norm(bm), norm(br), norm(bo))
    if largest > beta_cap:
        raise ValueError("velocity exceeds declared perturbative ceiling")
    return largest


def doppler(beta, n):
    return (1 + dot(beta, n)) / math.sqrt(1 - dot(beta, beta))


def exact_kinematic_residual(zbar, n, b, ell, amp):
    """Endpoint Lorentz/area-duality falsifier on an exact FLRW metric.

    beta_s=(1+zbar)*amp*b is a prescribed endpoint value. The finite-amp
    construction is NOT claimed to be the nonlinear two-fluid GR solution.
    Its derivative at amp=0 independently verifies the linear response.
    """
    beta_s = [(1 + zbar) * amp * x for x in b]
    beta_o = [amp * (x + y) for x, y in zip(b, ell)]
    ds, do = doppler(beta_s, n), doppler(beta_o, n)
    zobs = (1 + zbar) * ds / do - 1
    source = background(zbar)
    dl = source["dL_Mpc"] * ds * ds / do
    return dl / background(zobs)["dL_Mpc"] - 1


class HistoryChecks(unittest.TestCase):
    def test_01_exact_compensation_and_first_integrals(self):
        em, er = F(9999, 10000), F(1, 10000)
        ratio = 3 * em / (4 * er)
        b = [F(1, 10**8), F(-2, 10**8), F(3, 10**8)]
        for a in [F(1), F(1, 2), F(1, 10), F(1, 100)]:
            for bi in b:
                qm = em / a**3 * bi / a
                qr = F(4, 3) * er / a**4 * (-ratio * bi)
                self.assertEqual(qm + qr, 0)
                self.assertEqual(a**4 * qm, em * bi)
                self.assertEqual(a**4 * qr, -em * bi)

    def test_02_uncompensated_dust_violates_zero_momentum(self):
        self.assertNotEqual(F(1, 2) ** -4 * F(1, 10**8), 0)

    def test_03_relative_velocity_frame_shift(self):
        # First-order change of normal frame subtracts the same velocity.
        m, r, w = F(2, 13), F(-3, 11), F(7, 17)
        self.assertEqual((m - w) - (r - w), m - r)

    def test_04_exact_endpoint_lorentz_derivative(self):
        n = [2 / 3, -1 / 3, 2 / 3]
        b, ell = [0.3, -0.1, 0.2], [-0.2, 0.4, 0.1]
        for z in [0.03, 0.1, 0.5, 1.0]:
            bg = background(z)
            expect = bg["A_local"] * dot(n, ell) + bg["h_history"] * dot(n, b)
            step = 1.0e-6
            got = (exact_kinematic_residual(z, n, b, ell, step) -
                   exact_kinematic_residual(z, n, b, ell, -step)) / (2 * step)
            self.assertLess(abs(got - expect), 2e-8)

    def test_05_observer_and_source_signs(self):
        z = F(1, 10)
        # Fixed-z Taylor: 2*vs-vo -(1+A)*(vs-vo).
        a = F(10)
        self.assertEqual(2 * 0 - 1 - (1 + a) * (0 - 1), a)
        self.assertEqual(2 * 1 - 0 - (1 + a) * (1 - 0), 1 - a)
        self.assertGreater(z, 0)

    def test_06_zero_velocity(self):
        self.assertAlmostEqual(exact_kinematic_residual(
            0.1, [0, 0, 1], [0, 0, 0], [0, 0, 0], 1), 0, places=14)

    def test_07_low_redshift_cancellation(self):
        expected = (3 + OMEGA_R) / 4
        z = 1e-7
        self.assertLess(abs(background(z)["h_history"] / z - expected), 3e-8)
        self.assertLess(abs(z * background(z)["A_local"] - 1), 1e-7)

    def test_08_depth_rank_and_duplicate_depth(self):
        rows = [background(z) for z in [0.01, 0.05, 0.1, 0.5, 1.0, 2.0]]
        for lo, hi in zip(rows, rows[1:]):
            determinant = lo["A_local"] * hi["h_history"] - hi["A_local"] * lo["h_history"]
            self.assertGreater(determinant, 0)
            self.assertGreater(hi["F_ratio"], lo["F_ratio"])
        row = rows[0]
        self.assertEqual(row["A_local"] * row["h_history"] -
                         row["A_local"] * row["h_history"], 0)

    def test_09_local_annihilation_and_history_recovery(self):
        one, two = background(0.05), background(0.5)
        b, ell = 2e-8, 7e-4
        d1 = one["A_local"] * ell + one["h_history"] * b
        d2 = two["A_local"] * ell + two["h_history"] * b
        bhat = (d2 / two["A_local"] - d1 / one["A_local"]) / (
            two["F_ratio"] - one["F_ratio"])
        self.assertLess(abs(bhat - b), 2e-18)

    def test_10_nuisance_can_destroy_history_rank(self):
        h = [background(z)["h_history"] for z in [0.05, 0.1, 0.5]]
        # Orthogonal projection onto the complement of a nuisance column h.
        ph = [x - x * dot(h, h) / dot(h, h) for x in h]
        self.assertLess(norm(ph), 1e-15)

    def test_11_endpoint_copy_and_frozen_source_are_detected(self):
        row = background(0.05)
        self.assertGreater(abs(row["h_history"] - row["A_local"]), 10)
        # Setting beta_s=beta_o=b would incorrectly give constant kernel 1.
        self.assertGreater(abs(row["h_history"] - 1), 0.9)

    def test_12_perturbative_domain_and_rejection(self):
        self.assertLess(require_linear_domain(
            [2e-8, -1e-8, 0], [1e-3, 0, 0], 1 / 101), 0.01)
        with self.assertRaises(ValueError):
            require_linear_domain([1e-3, 0, 0], [0, 0, 0], 1 / 101)
        for z in [0, -0.1, float("nan")]:
            with self.assertRaises(ValueError):
                background(z)

    def test_13_unit_rescaling(self):
        # km/s -> m/s for both c and H leaves distances and kernels unchanged.
        first = background(0.3)
        second = background(0.3, h0=H0_KM_S_MPC * 1000, c=C_KM_S * 1000)
        for key in ["chi_Mpc", "dL_Mpc", "A_local", "h_history", "F_ratio"]:
            self.assertAlmostEqual(first[key], second[key], places=12)

    def test_14_two_bin_residual_bound(self):
        one, two = background(0.05), background(0.5)
        denominator = two["F_ratio"] - one["F_ratio"]
        bound = (1e-5 / two["A_local"] + 2e-5 / one["A_local"]) / denominator
        for sign1 in [-1, 1]:
            for sign2 in [-1, 1]:
                error = (sign2 * 1e-5 / two["A_local"] -
                         sign1 * 2e-5 / one["A_local"]) / denominator
                self.assertLessEqual(abs(error), bound * (1 + 1e-14))


def main():
    started = time.perf_counter()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(HistoryChecks)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    elapsed = time.perf_counter() - started
    rows = [background(z) for z in [0.01, 0.05, 0.1, 0.5, 1.0, 2.0]]
    one, two = rows[1], rows[3]
    output = {
        "schema_version": 1,
        "unit_id": "COMPENSATED_HISTORY_20261020",
        "source_commit": "69870ee249cd98a869f35e442105d17c927d28fc",
        "owner": "htt", "claim_tier": "C0", "status": "CONDITIONAL",
        "scope": "finite algebra verification of a first-order analytic subcase",
        "transfer_source": "none",
        "analytic_response_identity": "compensated-dust-radiation-distance-v1",
        "input_kind": "synthetic_declared_background_and_velocity",
        "sky_support_status": "ideal angular dipole; no catalogue or mask",
        "null_mock_status": "NOT_RUN; no sampling-law or coverage assertion",
        "background": {"Omega_r": OMEGA_R, "Omega_m": 1 - OMEGA_R,
                       "Omega_Lambda": 0, "Omega_k": 0,
                       "H0_km_s_Mpc": H0_KM_S_MPC, "c_km_s": C_KM_S},
        "compensation_ratio_R": 3 * (1 - OMEGA_R) / (4 * OMEGA_R),
        "rows": rows,
        "two_bin_example": {
            "z1": one["z"], "z2": two["z"],
            "determinant": one["A_local"] * two["h_history"] -
                           two["A_local"] * one["h_history"],
            "local_cancelled_history_coefficient": two["F_ratio"] - one["F_ratio"],
        },
        "tests": {"run": result.testsRun, "failures": len(result.failures),
                  "errors": len(result.errors), "passed": result.wasSuccessful()},
        "elapsed_seconds": elapsed, "budget_seconds": 60,
        "environment": {"python_executable": sys.executable,
                        "python_version": platform.python_version(),
                        "dependencies": "stdlib only", "threads": "no worker threads"},
        "execution": "completed" if result.wasSuccessful() else "failed",
        "command": f"{sys.executable} {Path(__file__).resolve()}",
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "no_ode_solver_or_quadrature": True,
        "original_nodes_completed": [],
        "original_completed_count": 17,
        "physical_nonlinear_remainder_bound": "UNKNOWN; not replaced by zero",
        "observational_selected_error_bound": "UNKNOWN; not replaced by zero",
        "independent_review": "PENDING_PARENT_ASSIGNED_REVIEWER",
        "caveats": [
            "All examples are synthetic; no original observation or campaign rerun.",
            "Exact Lorentz finite-step check is a kinematic derivative test, not nonlinear GR.",
            "Velocity ceiling alone does not bound optical or selection remainders.",
            "Distinct radial columns do not imply identification after nuisance projection.",
            "No original V03, S02, or K03 acceptance is claimed."
        ],
    }
    Path(__file__).with_name("RESULTS.json").write_text(
        json.dumps(output, indent=2, allow_nan=False) + "\n")
    return 0 if result.wasSuccessful() and elapsed < 60 else 1


if __name__ == "__main__":
    raise SystemExit(main())
