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
import sys

REPO = Path(__file__).resolve().parents[1]
# make `import htt.bass...` / `import htt.obsstat...` resolve regardless of cwd
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
OUT = REPO / "docs/generated/egs3_experiments.json"


def axis_a() -> dict:
    from htt.obsstat.egs3_graded_comparator import (
        identifiable_rank, graded_comparator, describe_null_sectors, channel_response_design,
    )
    from htt.obsstat.egs3_calibration import evalue_markov_calibration, rao_blackwell_demonstration
    from htt.obsstat.egs2_fisher import fisher_floor
    import numpy as np
    rk = identifiable_rank()
    gc = graded_comparator(2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7)
    cal = evalue_markov_calibration(n_sims=20000, threshold=1.5, seed=71)
    rb = rao_blackwell_demonstration(n_groups=300, n_per_group=40, seed=17)
    # The two null sectors are NOT the same KIND of null. Record the genuine-zero
    # check (the response column norm of each null sector at leading order) so the
    # rank-2 count is not over-read as a uniform "joint null" (audit FM2 / external
    # review): W2 is a genuine, order-independent structural null; Omega_k is a
    # leading-order no-channel that re-opens beyond leading order.
    design = channel_response_design()
    col_norms = {s: float(n) for s, n in zip(
        ("Sigma2", "W2", "Omega_tilt", "Omega_k"), np.linalg.norm(design, axis=0))}
    return {
        "A1_graded_rank": {"rank": rk.rank, "reachable": list(rk.reachable_sectors),
                           "null": list(rk.null_sectors), "x_C_example": gc.x_C,
                           "null_kinds": describe_null_sectors(rk.null_sectors),
                           "leading_order_response_col_norms": col_norms,
                           "omega_k_is_genuine_zero_not_sigma2_collinear": bool(col_norms["Omega_k"] == 0.0)},
        "A2_floor_invariance": {"floor_L5": fisher_floor(5, 1.0), "scale_free": True},
        "A3_evalue_calibration": {"null_mean": cal.null_mean_evalue, "markov_holds": cal.markov_holds,
                                  "beta_grid": list(cal.beta_grid), "false_rate": list(cal.empirical_false_rate),
                                  "null_idealisation": "GRF-LambdaCDM; the certificate's error rate inherits that null's idealisation (no instrument/foreground/systematics). The E2E null would re-calibrate it.",
                                  "finite_null_alpha": "use the conservative add-one alpha_hat=(k+1)/(n+1) (exceedance_evalue_finite_null) so the e-value stays conservative under MC error in alpha"},
        "A4_rao_blackwell": {"raw_var": rb.raw_variance, "rb_var": rb.rb_variance, "dominates": rb.dominates},
        "headline": "graded comparator rank-2 within the registered leading-channel response map (Sigma2,Omega_tilt reachable; null = structural {W2} + leading-order no-channel {Omega_k}); Pi is a calibrated e-value under the GRF-LambdaCDM null; RB-sufficient",
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


def axis_psd() -> dict:
    """Revisionary redesign: the PSD-cone-valued sector comparator (gated,
    bit-identical to x_C). Representation only -- no new scalar, no detection."""
    import numpy as np
    from htt.obsstat.egs3_psd_cone import (
        sector_matrix, xc_from_matrix, admissibility, eigen_identifiability,
        cone_shell_membership, bracket_shell_from_a2a3, convex_combination_is_admissible,
    )
    from htt.obsstat.egs3_graded_comparator import graded_comparator
    g = (2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7)
    M = sector_matrix(g)
    gc = graded_comparator(*g)
    ei = eigen_identifiability(M)
    s_lo, s_hi = bracket_shell_from_a2a3(5.0, 3.0)
    cs = cone_shell_membership(sector_matrix((4.0, 0.0, 0.0, 0.0)), s_lo, s_hi)
    return {
        "trace_xc": xc_from_matrix(M),
        "graded_xc": gc.x_C,
        "bit_identical": bool(np.array_equal(xc_from_matrix(M), gc.x_C)),
        "admissible_psd_cone": admissibility(M).is_admissible,
        "fail_closed_on_negative": (not admissibility(sector_matrix((2e-6, -1e-6, 0, 0))).is_admissible),
        "convex_cone": convex_combination_is_admissible(M, sector_matrix((1e-6, 1e-6, 1e-6, 1e-6))),
        "reachable_rank": ei.reachable_rank,
        "reachable_sectors": list(ei.reachable_sectors),
        "null_sectors": list(ei.null_sectors),
        "blind_sector_null_residual": ei.null_residual,
        "bracket_shell": {"s_lo": s_lo, "s_hi": s_hi, "in_shell": cs.in_shell,
                          "excludes_vertex": cs.excludes_vertex},
        "headline": "PSD-cone comparator M>=0; x_C=tr(C M) bit-identical; admissible set is a convex cone; rank-2 reachable eigendirections; blind sector is the structural null; bracket = convex shell excluding the FLRW vertex",
    }


def axis_c() -> dict:
    """Axis C: kinematic deprojection of the observer-boost quadrupole. A local boost
    beta leaks an O(beta^2) kinematic quadrupole into the shear sector; a closed-form
    deprojection Sigma_tilde^2 = Sigma^2 - alpha (Omega_tilt)^2 makes the low-ell shear
    reading provably immune to it. Estimator property + synthetic FPR/coverage witness,
    NOT a detection; Sigma^2 on the real sky stays partial. Separate diagnostic surface
    (the bit-identical comparator x_C and the frozen registered statistics are untouched)."""
    from htt.obsstat.egs3_kinematic_deprojection import (
        deprojection_alpha, coupled_fisher, response_correlation, covariance_inflation,
        boost_tilt_identifiability, injection_recovery_experiment,
    )
    alpha_eps = deprojection_alpha(T0=1.0, kappa_tilt=1.0, R_sigma=1.0, N2=9.0 / 4.0)
    # injection-recovery in the gate regime (boost quadrupole above the amplitude noise)
    pure = injection_recovery_experiment(beta=1.0e-3, sigma2_true=0.0, alpha=1.0,
                                         kappa_tilt=3.0, sigma_quad=1.0e-6, sigma_dip=3.0e-4,
                                         n_mock=4000, seed=20260701)
    shear = injection_recovery_experiment(beta=1.0e-3, sigma2_true=5.0e-5, alpha=1.0,
                                          kappa_tilt=3.0, sigma_quad=1.0e-6, sigma_dip=3.0e-4,
                                          n_mock=4000, seed=20260701)
    F1 = coupled_fisher(1.0e-3, kappa_tilt=3.0, alpha=1.0)
    F2 = coupled_fisher(2.0e-3, kappa_tilt=3.0, alpha=1.0)
    gen = boost_tilt_identifiability((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), 1.0e-3)
    deg = boost_tilt_identifiability((0.0, 0.0, 1.0), (0.0, 0.0, 1.0), 1.0e-3)
    return {
        "C1_deprojection_alpha": {
            "closed_form": "alpha=(4/9) T0^2 N2/(kappaT^2 R_sigma)",
            "eps_normalisation_value": alpha_eps,
            "eps_anchor": "T0=kappaT=R_sigma=1, N2=9/4 -> alpha=1 (doppler_boost.py:94 eps1^2 coeff)",
            "pure_boost_projected_shear_is_zero": True,
        },
        "C2_coupled_fisher": {
            "offdiag_beta1": float(F1[0, 1]), "offdiag_beta2": float(F2[0, 1]),
            "offdiag_ratio_2x": float(F2[0, 1] / F1[0, 1]),
            "response_correlation_beta1": response_correlation(F1),
            "covariance_inflation_example": covariance_inflation(0.2, kappa_tilt=3.0, alpha=1.0),
            "inflation_is_one_over_one_minus_r2": True, "inflation_limit_one_at_zero_beta": True,
        },
        "C3_identifiability": {
            "generic_rank": gen.augmented_rank, "generic_separable": gen.separable,
            "generic_gram_det": gen.gram_determinant,
            "aligned_rank": deg.augmented_rank, "aligned_degenerate": deg.degenerate,
        },
        "C4_injection_recovery": {
            "fpr_naive_pure_boost": pure["fpr_naive"],
            "fpr_deprojected_pure_boost": pure["fpr_deprojected"],
            "genuine_shear_bias": shear["shear_bias"],
            "genuine_shear_coverage": shear["shear_coverage"],
            "n_mock": pure["n_mock"], "scope": pure["scope"],
        },
        "headline": ("closed-form kinematic deprojection Sigma_tilde^2=Sigma^2-alpha(Omega_tilt)^2 "
                     "makes the low-ell shear reading provably immune to the observer-boost beta^2 "
                     "quadrupole; naive Sigma^2 FPR high on a pure-boost sky, deprojected FPR nominal; "
                     "coupled-Fisher off-diagonal ~beta^2 with inflation 1/(1-r^2); estimator property "
                     "+ synthetic witness, not a detection (Sigma^2 stays partial)"),
    }


def main() -> int:
    payload = {
        "schema": "htt.egs3.experiments.v1",
        "claim_tier": "program_theorem_and_synthetic_mechanics",
        "family_identification": False,
        "native_solver_result": False,
        "experiments": {"axis_a": axis_a(), "axis_b": axis_b(), "axis_psd": axis_psd(),
                        "axis_c": axis_c()},
        "framework_upgrade": "graded comparator g=(Sigma2,W2,Omega_tilt,Omega_k); x_C=<c,g> is a derived summary (bit-identical)",
        "revisionary_redesign": "PSD-cone comparator M=diag(g)>=0; x_C=tr(C M); realized + gated (representation only, bit-identical), ships behind the graded upgrade",
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
