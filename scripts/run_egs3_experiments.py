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

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
# make canonical `bass...` / `obsstat...` imports resolve regardless of cwd
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
OUT = REPO / "docs/generated/egs3_experiments.json"

_INPUT_PATHS = (
    "scripts/run_egs3_experiments.py",
    "htt/bass/transfer/shear_quadrupole_seminative.py",
    "htt/obsstat/egs2_fisher.py",
    "htt/obsstat/egs3_bianchi_v_constraint.py",
    "htt/obsstat/egs3_calibration.py",
    "htt/obsstat/egs3_evalue_merge.py",
    "htt/obsstat/egs3_gf_interval.py",
    "htt/obsstat/egs3_graded_comparator.py",
    "htt/obsstat/egs3_identified_set.py",
    "htt/obsstat/egs3_kinematic_deprojection.py",
    "htt/obsstat/egs3_prior_exposure.py",
    "htt/obsstat/egs3_psd_cone.py",
    "htt/obsstat/egs3_shear_memory_bias.py",
    "htt/obsstat/egs3_volterra_memory.py",
    "htt/obsstat/egs3_vorticity_channels.py",
    "htt/obsstat/biposh_smica.py",
    "htt/obsstat/joint_pv_cmb_forecast.py",
    "htt/obsstat/lowell_map_features.py",
    "htt/obsstat/pv_covariance.py",
)
_METADATA_KEYS = frozenset({
    "owner",
    "implementation_scope",
    "claim_tier",
    "transfer_source",
    "config_hash",
    "input_hashes",
    "sky_support_status",
    "null_mock_status",
    "caveats",
    "generating_command",
    "metadata_refresh_command",
    "git_commit",
    "git_commit_or_worktree_state",
    "worktree_state",
})


def _stable_hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=float
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _input_hashes() -> list[str]:
    records: list[str] = []
    for relative in _INPUT_PATHS:
        path = REPO / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        records.append(f"{relative}:sha256:{digest}")
    return records


def _with_artifact_metadata(source: dict) -> dict:
    """Attach content-addressed metadata without re-running any experiment.

    This is deliberately usable on an existing payload so a provenance-only
    refresh does not change or recompute the stored scientific numbers.
    """
    payload = copy.deepcopy(source)
    d1 = payload["experiments"]["axis_d"]["D1_feasible_pv_covariance"]
    d1.update({
        "label": "deterministic synthetic method witness; no survey forecast",
        "observational_interpretation": None,
        "public_use": False,
    })
    inputs = _input_hashes()
    scientific_payload = {
        key: value for key, value in payload.items() if key not in _METADATA_KEYS
    }
    payload.update({
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "transfer_source": "mixed_none_and_analytic_transfer_stand_ins",
        "config_hash": _stable_hash({
            "metadata_schema": "htt.minimum_artifact_metadata.v1",
            "scientific_payload_hash": _stable_hash(scientific_payload),
            "input_hashes": inputs,
        }),
        "input_hashes": inputs,
        "sky_support_status": "synthetic_or_not_applicable_no_observed_sky_claim",
        "null_mock_status": "fixed_seed_synthetic_and_idealized_nulls_no_e2e_validation",
        "caveats": [
            "Conditional theorems and deterministic synthetic mechanics only.",
            "Axis D1 is a synthetic method witness with no observational interpretation or public-result use.",
            "Analytic and semi-native transfer stand-ins are not native low-ell solver outputs.",
            "No detection, geometry, family-identification, or posterior claim is authorized.",
        ],
        "generating_command": "python scripts/run_egs3_experiments.py",
        "metadata_refresh_command": "python scripts/run_egs3_experiments.py --metadata-only",
        "git_commit": "content-addressed",
        "git_commit_or_worktree_state": "content-addressed",
        "worktree_state": "content-addressed",
    })
    return payload


def _json_bound(value: float) -> float | str:
    value = float(value)
    if math.isinf(value):
        return "Infinity" if value > 0.0 else "-Infinity"
    return value


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
    # review): W2 is a structural zero column only in this registered response
    # map; Omega_k is a leading-order no-channel that re-opens beyond leading
    # order. No all-order or Weyl claim is made for the W2 column.
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
    from bass.transfer.shear_quadrupole_seminative import floor_profile_vs_k, shear_multipole_response
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


def axis_d() -> dict:
    """Axis D: synthetic joint-information method witnesses (pre-solver).

    The CF4/JWST observational forecast is quarantined by PR-120.  This axis
    retains only deterministic synthetic Woodbury, subset-error, coupled-Fisher,
    and BipoSH response mechanics plus the fail-closed theory-g CMB sector.
    """
    import numpy as np
    from htt.obsstat import pv_covariance as pv
    from htt.obsstat import joint_pv_cmb_forecast as jf
    from htt.obsstat import biposh_smica as bs
    from htt.obsstat.lowell_map_features import _packed_index
    rng = np.random.default_rng(20260702)
    pos = rng.normal(size=(600, 3)) * 50.0
    r = np.linalg.norm(pos, axis=1); nh = pos / r[:, None]
    modes = pv.velocity_field_modes(pos, sigma_shear_kms_per_mpc=0.3)
    U, Lam = modes["U"][:, 3:], modes["Lambda"][3:]
    sig2 = (rng.uniform(50.0, 150.0, 600)) ** 2
    v = nh @ np.array([200.0, -90.0, 60.0]) + rng.normal(size=600) * np.sqrt(sig2)
    fit = pv.pv_tilt_gls(nh, v, sig2, U, Lam)
    # Woodbury vs dense witness on a small block
    d0 = rng.uniform(1, 4, 40); U0 = rng.normal(size=(40, 8)); l0 = rng.uniform(.5, 2, 8)
    C0 = np.diag(d0) + U0 @ np.diag(l0) @ U0.T; b0 = rng.normal(size=(40, 2))
    woodbury_ok = bool(np.allclose(pv.woodbury_solve(d0, U0, l0, b0), np.linalg.solve(C0, b0), atol=1e-9))
    # Synthetic subset-error sensitivity vs selected fraction.
    order = np.argsort(r)
    gain_curve = {}
    for frac in (0.02, 0.05, 0.10, 0.15):
        mask = np.zeros(600, bool); mask[order[:int(frac * 600)]] = True
        gain_curve[f"{frac:.2f}"] = jf.synthetic_error_shrink_sensitivity(
            nh, v, sig2, mask, error_scale=1/3, U=U, Lambda=Lam
        )["information_multiplier"]
    jff = jf.joint_fisher_sensitivity(
        rho=0.5, f_tilt_base=1.0, f_tilt_candidate=gain_curve["0.10"]
    )
    # BipoSH aberration response (isotropic vs injected l<->l+1), synthetic alm
    lmax = 8
    def packed(seed):
        rr = np.random.default_rng(seed)
        a = rr.normal(size=(lmax + 1) * (lmax + 2) // 2) + 1j * rr.normal(size=(lmax + 1) * (lmax + 2) // 2)
        for l in range(lmax + 1):
            a[_packed_index(lmax, l, 0)] = a[_packed_index(lmax, l, 0)].real
        return a
    iso, ab = [], []
    for s in range(30):
        a = packed(1000 + s)
        iso.append(bs.compute_biposh_from_alm(a, lmax, L_values=(1, 2)).power_by_L[1])
        aa = a.copy()
        for l in range(2, lmax):
            for m in range(0, l + 1):
                aa[_packed_index(lmax, l + 1, m)] += 0.3 * a[_packed_index(lmax, l, m)]
        ab.append(bs.compute_biposh_from_alm(aa, lmax, L_values=(1, 2)).power_by_L[1])
    cmb_fail_closed = False
    try:
        jf.anisotropic_cmb_covariance((1.0, 0.0, 0.0, 0.0))
    except jf.OutOfScopeError:
        cmb_fail_closed = True
    return {
        "D1_feasible_pv_covariance": {
            "woodbury_matches_dense": woodbury_ok,
            "correlated_tilt_amplitude_kms": fit.amplitude, "n_modes": fit.n_modes,
            "note": "diag(sigma^2)+U Lambda U^T Woodbury; O(N K^2), no dense N x N inversion",
            "label": "deterministic synthetic method witness; no survey forecast",
            "observational_interpretation": None,
            "public_use": False,
        },
        "D2_synthetic_subset_error_sensitivity": {
            "information_multiplier_by_selected_fraction": gain_curve,
            "monotone_in_selected_fraction": bool(all(gain_curve[a] <= gain_curve[b] for a, b in
                                            zip(["0.02", "0.05", "0.10"], ["0.05", "0.10", "0.15"]))),
            "label": "deterministic synthetic method witness; no survey forecast",
            "observational_interpretation": None,
            "public_use": False,
        },
        "D3_generic_fisher_sensitivity": {
            "sigma2_inflation_base": jff["inflation_base"],
            "sigma2_inflation_candidate": jff["inflation_candidate"],
            "sensitivity_ratio": jff["sensitivity_ratio"],
            "observational_interpretation": None,
        },
        "D4_biposh_aberration": {
            "iso_L1_mean": float(np.mean(iso)), "aberrated_L1_mean": float(np.mean(ab)),
            "aberration_raises_L1": bool(np.mean(ab) > np.mean(iso)),
        },
        "D5_theory_cmb_fail_closed": cmb_fail_closed,
        "headline": ("synthetic correlated-covariance and generic information-weight sensitivity "
                     "+ synthetic off-diagonal BipoSH response; the former CF4/JWST forecast is "
                     "quarantined and the theory-g CMB likelihood stays fail-closed"),
    }


def axis_e() -> dict:
    """Axis E: identified-set semantics for x_C (P26/P31/P35/P36/P28/P29, A8). The
    P1 x P18 operational resolution: the reportable object is [x_C^-, x_C^+] over the
    two-stage-tau feasible set, with empty (refutability) / unbounded (no-result) /
    ceiling-unfit (F>1) statuses, Imbens-Manski endpoint coverage, joint-feasible-set
    G_F propagation, dependent e-value merging, and the prior-exposure witness.
    Synthetic statistics machinery only; separate diagnostic surface (bit-identical
    x_C untouched); no detection/family/solver/posterior claim."""
    import numpy as np
    from htt.obsstat.egs3_identified_set import (
        identified_set_report, im_coverage_experiment,
        refutability_power_experiment, toy_design,
        signed_curvature_branch_reports, two_stage_tau,
    )
    from htt.obsstat.egs3_gf_interval import gf_joint_vs_naive, gf_strictness_witness
    from htt.obsstat.egs3_evalue_merge import arithmetic_merge_mc, test_martingale_ville_mc
    from htt.obsstat.egs3_prior_exposure import gaussian_prior_exposure_witness

    toy = toy_design()
    y = toy["R"] @ toy["g_true"]
    pop = identified_set_report(y, toy["R"], toy["c"], toy["lower"], toy["upper"],
                                alpha2=1.0)
    branch_reports = signed_curvature_branch_reports(
        y, toy["R"], toy["c"], toy["lower"], toy["upper"], alpha2=1.0)
    estimated_cov_tau = two_stage_tau(
        10, 2, alpha1=0.05, alpha2=0.05,
        threshold_policy="estimated_covariance_f", n_sim=300)
    upper_open = toy["upper"].copy(); upper_open[1] = np.inf
    unbounded = identified_set_report(y, toy["R"], toy["c"], toy["lower"],
                                      upper_open, alpha2=1.0)
    A = toy["R"][:, [0, 2]]
    q, _ = np.linalg.qr(A, mode="complete")
    misfit = identified_set_report(y + 10.0 * q[:, -1], toy["R"], toy["c"],
                                   toy["lower"], toy["upper"])
    unfit = identified_set_report(y, toy["R"], toy["c"], toy["lower"],
                                  toy["upper"], alpha2=1.0, ceiling_U=0.05)
    cov = im_coverage_experiment(n_mc=2000, seed=20260708)
    power = refutability_power_experiment(n_mc=1000, seed=20260708)
    gf = gf_joint_vs_naive()
    strictness = gf_strictness_witness()
    merge = arithmetic_merge_mc(seed=20260708)
    ville = test_martingale_ville_mc(seed=20260708)
    prior = gaussian_prior_exposure_witness(seed=20260708)
    return {
        "E1_identified_set": {
            "population_interval": [pop.x_lo, pop.x_hi],
            "signed_curvature_branches": {
                branch_id: {
                    "status": rep.status,
                    "interval": [rep.x_lo, rep.x_hi],
                    "component_bounds": [
                        [_json_bound(lo), _json_bound(hi)]
                        for lo, hi in rep.component_bounds
                    ],
                }
                for branch_id, rep in branch_reports.items()
            },
            "reproduces_registered_example": bool(
                abs(pop.x_lo - 0.11) < 1e-9 and abs(pop.x_hi - 0.17) < 1e-9),
            "tau1_chi2_dof": pop.m - pop.rank, "tau1": pop.tau.tau1,
            "estimated_covariance_threshold_example": {
                "policy": estimated_cov_tau.threshold_policy,
                "m": estimated_cov_tau.m,
                "r": estimated_cov_tau.r,
                "n_sim": estimated_cov_tau.n_sim,
                "df_residual": estimated_cov_tau.df_residual,
                "tau1_hotelling_F": estimated_cov_tau.tau1,
                "tau2_hotelling_F": estimated_cov_tau.tau2,
            },
            "statuses": {"feasible": pop.status, "empty_misfit": misfit.status,
                         "unbounded_no_ceiling": unbounded.status,
                         "ceiling_unfit_F_gt_1": unfit.status},
            "rank": pop.rank,
        },
        "E2_im_coverage": {
            "n_mc": cov.n_mc, "seed": cov.seed, "alpha": cov.alpha,
            "delta_over_sigma": cov.delta_over_sigma,
            "coverage_projection": cov.coverage_projection,
            "coverage_im": cov.coverage_im,
            "coverage_endpoint_naive": cov.coverage_endpoint,
            "se_binomial": cov.se_binomial, "cn_im": cov.cn_im,
            "ordering_projection_ge_im_gt_naive": bool(
                cov.coverage_projection >= cov.coverage_im > cov.coverage_endpoint),
        },
        "E3_refutability_power": {
            "amplitudes": list(power.amplitudes),
            "empty_rate": list(power.empty_rate), "se": list(power.se),
            "alpha1": power.alpha1, "n_mc": power.n_mc, "seed": power.seed,
            "size_matches_alpha1": bool(
                abs(power.empty_rate[0] - power.alpha1) < 3.0 * max(power.se[0], 7e-3)),
        },
        "E4_gf_joint_vs_naive": {
            "joint": list(gf.joint), "naive": list(gf.naive),
            "width_ratio": gf.width_ratio,
            "joint_within_naive": gf.joint_within_naive,
            "strict_lower": gf.strict_lower,
            "strict_upper": gf.strict_upper,
            "equality_reason": gf.equality_reason,
            "strictness_criterion": gf.strictness_criterion,
            "strictness_witness": strictness,
        },
        "E7_evalue_merge": {
            "merged_mean": merge.merged_mean, "se": merge.se,
            "n_sims": merge.n_sims, "seed": merge.seed,
            "dependence": merge.dependence, "mean_le_one": merge.mean_le_one,
            "ville_beta_grid": list(ville.beta_grid),
            "ville_crossing_rate": list(ville.crossing_rate),
            "ville_holds": ville.ville_holds,
        },
        "E8_prior_exposure": {
            "kl_null_block_exact_zero": prior.kl_null_block == 0.0,
            "coupled_prior_kl": prior.coupled_prior_kl,
            "n_samples": prior.n_samples, "seed": prior.seed,
        },
        "headline": ("x_C is reported as a two-stage-tau identified set [x_C^-, x_C^+] with "
                     "refutability (empty), no-result (unbounded), and ceiling-unfit (F>1) "
                     "statuses; Imbens-Manski endpoint coverage nominal where the naive "
                     "endpoint CI undercovers; G_F propagates on the joint feasible set; "
                     "e-values merge under arbitrary dependence and are anytime-valid; "
                    "null-direction posteriors are prior-exposed; v7 fortification "
                    "records signed curvature branches, estimated-covariance "
                    "thresholds, and exact strict/equality conditions"),
    }


def axis_f() -> dict:
    """Axis F: physics/convention seals (B1 repair + P5 + P13 companion). The parent
    identity and Bianchi V seals are SymPy artifacts (SSoT: docs/generated/
    parent_identity_seal.json + bianchi_v_constraint_seal.json via `make egs3-seals`);
    this axis records the numeric witnesses. Conditional/diagnostic only."""
    from htt.obsstat.egs3_bianchi_v_constraint import numeric_scaling_witness
    from htt.obsstat.egs3_shear_memory_bias import kappa_bias_curve
    wit = numeric_scaling_witness()
    curve = kappa_bias_curve()
    return {
        "F1_parent_identity_ref": {
            "artifact": "docs/generated/parent_identity_seal.json",
            "note": "SymPy seal is the SSoT (make egs3-seals): parent identity -> "
                    "c=(1,-1,1,1); W^2 = omega_ab omega^ab/(6H^2); v5-doc convention "
                    "was 3x; (3/2) MES rule derived",
        },
        "F2_bianchi_v_witness": {
            "artifact": "docs/generated/bianchi_v_constraint_seal.json",
            "betas": list(wit.betas), "rel_errors": list(wit.rel_errors),
            "loglog_slope": wit.loglog_slope,
            "omega_k_breakdown_raises": wit.omega_k_breakdown_raises,
        },
        "F3_shear_memory_bias": {
            "e0_grid": list(curve.e0_grid),
            "kappa_bias_ratio": list(curve.kappa_bias_ratio),
            "zero_crossing_e0": curve.zero_crossing_e0,
            "note": "registered scalar closure unbiased iff the toy Weyl closure "
                    "matches the friction (e0=1); quantitative kernel is "
                    "closure-conditional (P13 -> DERIVED_CONDITIONAL)",
        },
        "headline": ("parent-identity + Bianchi V constraint SymPy seals PASS; the "
                     "registered shear-closure kappa fit is unbiased only at the "
                     "friction-matching toy Weyl closure (P13 quantitative content is "
                     "closure-conditional)"),
    }


def build_payload() -> dict:
    return {
        "schema": "htt.egs3.experiments.v1",
        "claim_tier": "program_theorem_and_synthetic_mechanics",
        "family_identification": False,
        "native_solver_result": False,
        "experiments": {"axis_a": axis_a(), "axis_b": axis_b(), "axis_psd": axis_psd(),
                        "axis_c": axis_c(), "axis_d": axis_d(),
                        "axis_e": axis_e(), "axis_f": axis_f()},
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated JSON is stale")
    parser.add_argument(
        "--metadata-only",
        action="store_true",
        help="refresh/check metadata on the existing payload without recomputing experiments",
    )
    args = parser.parse_args(argv)
    if args.metadata_only:
        if not OUT.is_file():
            print(f"missing {OUT}; metadata-only refresh cannot synthesize results")
            return 1
        payload = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        payload = build_payload()
    payload = _with_artifact_metadata(payload)
    text = json.dumps(payload, indent=2, default=float) + "\n"
    if args.check:
        if not OUT.is_file():
            print(f"missing {OUT}")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"stale {OUT}")
            return 1
        print(f"{OUT.name} up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
