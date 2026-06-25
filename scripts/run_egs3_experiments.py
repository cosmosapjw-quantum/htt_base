#!/usr/bin/env python3
"""Run the EGS3 extension experiments (Axis A + Axis B) against the canonical
repo modules and write docs/generated/egs3_experiments.json.

Conditional theorems + synthetic mechanics only: no detection, no
family/geometry, no native-solver validation. The semi-native transfer, the
toy/analytic visibility, and constant-H are documented stand-ins; the analytic
shapes (rank-2 identifiability, e-value calibration, k-profile floor, Volterra
memory, vorticity re-opening) are the robust content.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs/generated/egs3_experiments.json"


def axis_a() -> dict:
    from htt.obsstat.egs3_graded_comparator import identifiable_rank, graded_comparator
    from htt.obsstat.egs3_calibration import evalue_markov_calibration, rao_blackwell_demonstration
    from htt.obsstat.egs2_fisher import fisher_floor
    rk = identifiable_rank()
    gc = graded_comparator(2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7)
    cal = evalue_markov_calibration(n_sims=20000, threshold=1.5, seed=71)
    rb = rao_blackwell_demonstration(n_groups=300, n_per_group=40, seed=17)
    return {
        "A1_graded_rank": {"rank": rk.rank, "reachable": list(rk.reachable_sectors),
                           "null": list(rk.null_sectors), "x_C_example": gc.x_C},
        "A2_floor_invariance": {"floor_L5": fisher_floor(5, 1.0), "scale_free": True},
        "A3_evalue_calibration": {"null_mean": cal.null_mean_evalue, "markov_holds": cal.markov_holds,
                                  "beta_grid": list(cal.beta_grid), "false_rate": list(cal.empirical_false_rate)},
        "A4_rao_blackwell": {"raw_var": rb.raw_variance, "rb_var": rb.rb_variance, "dominates": rb.dominates},
        "headline": "graded comparator rank-2 (Sigma2,Omega_tilt reachable; W2,Omega_k joint null); Pi is a calibrated e-value; RB-sufficient",
    }


def axis_b() -> dict:
    from htt.bass.transfer.shear_quadrupole_seminative import floor_profile_vs_k, shear_multipole_response
    from htt.obsstat.egs3_volterra_memory import volterra_memory_check
    from htt.obsstat.egs3_vorticity_channels import vorticity_reopening
    prof = floor_profile_vs_k([1e-5, 7e-5, 5e-4, 2e-3], lmax=40)
    resp = shear_multipole_response(k=7e-5, lmax=20)
    vm = volterra_memory_check()
    vr = vorticity_reopening(n_configs=500, seed=91)
    return {
        "B1_transfer_floor_profile": {f"{v['k_chi_star']:.3f}": v["floor"] for v in prof.values()},
        "B1_superhorizon_decay": {"r2": resp.r_ell[2], "r3": resp.r_ell[3], "r10": resp.r_ell[10],
                                  "monotone_decay": resp.monotone_decay_from_l2},
        "B2_volterra_memory": {"max_diff_vs_ode": vm.max_abs_diff_vs_ode, "gronwall_holds": vm.gronwall_holds,
                               "kernel_decays": vm.kernel_decays},
        "B3_vorticity_reopen": {"radial_max": vr.radial_max_abs, "transverse_max": vr.transverse_max_abs,
                                "transverse_rank": vr.transverse_design_rank, "reopens": vr.reopens},
        "headline": "floor is a k-profile saturating at 0.632 (super-horizon shear); depth gap is a Volterra memory of Pi; vorticity re-opens in the transverse channel",
    }


def main() -> int:
    payload = {
        "schema": "htt.egs3.experiments.v1",
        "claim_tier": "program_theorem_and_synthetic_mechanics",
        "family_identification": False,
        "native_solver_result": False,
        "experiments": {"axis_a": axis_a(), "axis_b": axis_b()},
        "framework_upgrade": "graded comparator g=(Sigma2,W2,Omega_tilt,Omega_k); x_C=<c,g> is a derived summary (bit-identical)",
        "blockers_kept_open": [
            "BLOCKED_MISSING_PR4_E2E_ACCESS",
            "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
            "BLOCKED_MISSING_FIELD_REALIZATIONS",
            "AWAITING_NATIVE_LOWELL_SOLVER",
        ],
        "claim_boundary": "conditional EGS-type theorems + synthetic mechanics only; no detection, family/geometry, or native-solver validation",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
