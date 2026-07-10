#!/usr/bin/env python3
"""REV-R126: figures for the EGS2 + EGS3 extension theorems and the PSD-cone
revisionary redesign, computed from the canonical repo modules.

Eight diagnostic-only program-theorem figures (synthetic / analytic illustration
of the Wolfram- and gate-verified identities; no observed data, no native
low-ell solver, no Bianchi family or geometry identification):

  egs3_a1_graded_rank      graded comparator response design + rank-2 reachable
                           (Sigma2, Omega_tilt) vs joint-null (W2, Omega_k).
  egs3_a3_evalue           Pi e-value calibration: empirical false-exceedance
                           rate stays under the Markov beta bound.
  egs2_nt2a1_fisher_floor  genuine multi-multipole Fisher-CR floor dropping
                           strictly below the single-l sqrt(2/5)=0.632.
  egs3_b1_floor_profile    the floor as a PROFILE in the shear scale k: it
                           saturates at 0.632 for super-horizon shear and drops
                           below only at finite k (sharpens NT2-A1).
  egs3_b2_volterra         depth gap as a Volterra functional of the tilt stress
                           with an exponential memory kernel exp(-3 int H).
  egs3_b3_vorticity        radial peculiar velocities are vorticity-blind
                           (n.Omega.n=0); the transverse channel re-opens it.
  egs2_nt2b1_bracket       two-sided shear/F bracket excluding zero (lower bound
                           is the strong new content).
  egs3_psd_cone            PSD-cone redesign: reachable eigen-directions (rank 2)
                           + the convex cone-shell bracket excluding the FLRW
                           vertex; x_C = tr(C M) is bit-identical.

Each figure ships a deterministic source.json (plotted values) + a gated
manifest; --check compares those sidecars byte-for-byte. Manifests are
content-addressed only (no git state) so --check is stable across commits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = REPO_ROOT / "figures" / "current"

# canonical modules (import lazily inside _sources so --help works without deps)


def _config_hash(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _manifest(stem: str, theorem_id: str, title: str, source: dict) -> dict:
    return {
        "artifact_id": f"bass.theorem.{stem}",
        "artifact_path": f"figures/current/{stem}.png",
        "owner": "BASS",
        "implementation_scope": "bass_py",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "synthetic_only",
        "covariance_status": "synthetic_only",
        "family_identification": False,
        "native_solver_result": False,
        "theorem_id": theorem_id,
        "theorem_title": title,
        "source_json_path": f"figures/current/{stem}.source.json",
        "statistics_definitions": {"program": "egs2_egs3_extension", "theorem_id": theorem_id},
        "generating_command": "python scripts/make_egs2_egs3_theorem_figures.py",
        "config_hash": _config_hash(source),
        "created_by": "scripts/make_egs2_egs3_theorem_figures.py",
        "schema_version": "bass.egs2_egs3_theorem_figure.v1",
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_not_use_for_family_identification_or_family_selection",
            "must_state_no_native_low_ell_solver_output",
        ],
        "caveats": [
            "Analytic/synthetic theorem illustration; not observed data.",
            "Conditional theorem; structural/limit statement, not a detection.",
            "No native low-ell solver output or morphology atlas is used.",
            "No Bianchi family-ID or geometry-detection claim is made.",
        ],
        "failed_gates": [
            "native_low_ell_solver_not_available",
            "family_morphology_atlas_not_available",
            "observational_closure_not_bound",
        ],
        "passed_gates": [
            "gate_test_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "promotion_blockers": [
            "native_solver_validation_absent",
            "native_morphology_atlas_absent",
            "family_identification_blocked_pre_native_atlas",
        ],
        "publication_gates": {
            "bianchi_evidence_claim": "fail_program_theorem_only",
            "family_identification_claim": "fail_blocked_pre_native_atlas",
        },
        "required_gates": [
            "gate_test_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "title": title,
        "source": source,
    }


def _sources() -> dict[str, dict]:
    from htt.obsstat.egs3_graded_comparator import (
        channel_response_design, identifiable_rank, CHANNELS, SECTORS,
    )
    from htt.obsstat.egs3_calibration import evalue_markov_calibration
    from htt.obsstat.egs2_fisher import fisher_floor, single_ell_sampling_dispersion
    from htt.bass.transfer.shear_quadrupole_seminative import (
        floor_profile_vs_k, shear_multipole_response,
    )
    from htt.obsstat.egs3_volterra_memory import volterra_shear
    from htt.obsstat.egs3_vorticity_channels import radial_response, transverse_response
    from htt.obsstat.egs2_shear_bracket import filling_bracket
    from htt.obsstat.egs3_psd_cone import (
        sector_matrix, xc_from_matrix, eigen_identifiability,
        cone_shell_membership, bracket_shell_from_a2a3,
    )
    from htt.obsstat.egs3_graded_comparator import graded_comparator

    # --- A1 graded rank --------------------------------------------------
    D = channel_response_design()
    rk = identifiable_rank()
    a1 = {
        "theorem_id": "EGS3-A1",
        "channels": list(CHANNELS),
        "sectors": list(SECTORS),
        "response_design": D.tolist(),
        "rank": rk.rank,
        "reachable_sectors": list(rk.reachable_sectors),
        "null_sectors": list(rk.null_sectors),
    }

    # --- A3 Pi e-value calibration --------------------------------------
    cal = evalue_markov_calibration(n_sims=40000, threshold=1.5, seed=71)
    a3 = {
        "theorem_id": "EGS3-A3",
        "beta_grid": list(cal.beta_grid),
        "empirical_false_rate": list(cal.empirical_false_rate),
        "null_mean_evalue": cal.null_mean_evalue,
        "markov_holds": cal.markov_holds,
        "n_sims": cal.n_sims,
    }

    # --- NT2-A1 genuine multi-multipole Fisher floor --------------------
    lmaxes = list(range(2, 41))
    floors = [fisher_floor(L, 1.0) for L in lmaxes]
    a1_floor = {
        "theorem_id": "NT2-A1",
        "lmax": lmaxes,
        "fisher_floor": floors,
        "single_ell_l2_dispersion": single_ell_sampling_dispersion(2, 1.0),
    }

    # --- B1 floor profile vs k ------------------------------------------
    kvals = np.logspace(-5.3, -3.0, 24)
    prof = floor_profile_vs_k(kvals.tolist(), lmax=40)
    kchi = [prof[k]["k_chi_star"] for k in sorted(prof)]
    floor_k = [prof[k]["floor"] for k in sorted(prof)]
    resp = shear_multipole_response(k=7.0e-5, lmax=20)
    b1 = {
        "theorem_id": "EGS3-B1",
        "k_chi_star": kchi,
        "floor": floor_k,
        "saturation_floor": single_ell_sampling_dispersion(2, 1.0),
        "r_ell_l": list(resp.ell),
        "r_ell": [resp.r_ell[l] for l in resp.ell],
    }

    # --- B2 Volterra depth memory ---------------------------------------
    z = np.linspace(0.0, 1.0, 41)
    H = 3.0
    pi_of_z = 1.0e-3 * (1.0 + 2.0 * z)        # depth-growing tilt stress
    sig = volterra_shear(lambda zz: 1.0e-3 * (1.0 + 2.0 * zz), z, H=H, sigma0=1.0e-3)
    kernel = np.exp(-3.0 * H * z)              # exponential memory kernel
    b2 = {
        "theorem_id": "EGS3-B2",
        "z": z.tolist(),
        "pi_of_z": pi_of_z.tolist(),
        "shear_volterra": sig.tolist(),
        "memory_kernel": kernel.tolist(),
        "H": H,
    }

    # --- B3 vorticity radial-blind vs transverse re-opening -------------
    rng = np.random.default_rng(91)
    n_hat = np.array([0.0, 0.0, 1.0])
    m_hat = np.array([1.0, 0.0, 0.0])         # transverse to n_hat
    omegas = rng.normal(0.0, 1.0, size=(400, 3))
    radial = [radial_response(o, n_hat) for o in omegas]
    transverse = [transverse_response(o, n_hat, m_hat) for o in omegas]
    b3 = {
        "theorem_id": "EGS3-B3",
        "radial_response": radial,
        "transverse_response": transverse,
        "radial_max_abs": float(np.max(np.abs(radial))),
        "transverse_max_abs": float(np.max(np.abs(transverse))),
    }

    # --- NT2-B1 two-sided shear/F bracket -------------------------------
    a2_grid = np.linspace(0.5, 6.0, 23)
    r_ratio = 0.5                              # a3/a2 fixed in the H3 regime
    f_lo, f_hi = [], []
    for a2 in a2_grid:
        fb = filling_bracket(float(a2), float(r_ratio * a2))
        f_lo.append(fb.F_lo)
        f_hi.append(fb.F_hi)
    nt2b1 = {
        "theorem_id": "NT2-B1",
        "a2": a2_grid.tolist(),
        "a3_over_a2": r_ratio,
        "F_lo": f_lo,
        "F_hi": f_hi,
        "excludes_zero": bool(filling_bracket(2.0, 1.0).excludes_zero),
    }

    # --- PSD-cone redesign ----------------------------------------------
    g = (2.0e-6, 1.5e-6, 8.0e-7, 3.0e-7)
    M = sector_matrix(g)
    ei = eigen_identifiability(M)
    s_lo, s_hi = bracket_shell_from_a2a3(5.0, 3.0)
    cs = cone_shell_membership(sector_matrix((4.0, 0.0, 0.0, 0.0)), s_lo, s_hi)
    psd = {
        "theorem_id": "EGS3-PSD",
        "sectors": list(SECTORS),
        "spectrum": list(g),
        "x_C_trace": xc_from_matrix(M),
        "x_C_graded": graded_comparator(*g).x_C,
        "bit_identical": bool(np.array_equal(xc_from_matrix(M), graded_comparator(*g).x_C)),
        "reachable_rank": ei.reachable_rank,
        "reachable_sectors": list(ei.reachable_sectors),
        "null_sectors": list(ei.null_sectors),
        "shell_s_lo": s_lo,
        "shell_s_hi": s_hi,
        "shell_lambda_sigma": cs.lambda_sigma,
        "shell_in": cs.in_shell,
        "excludes_vertex": cs.excludes_vertex,
    }

    # --- C kinematic deprojection of the observer-boost quadrupole ------
    from htt.obsstat.egs3_kinematic_deprojection import (
        injection_recovery_experiment, covariance_inflation,
    )
    betas = [2.0e-4, 5.0e-4, 1.0e-3, 1.5e-3, 2.0e-3, 2.5e-3, 3.0e-3]
    fpr_naive, fpr_deproj = [], []
    for bta in betas:
        rr = injection_recovery_experiment(beta=bta, sigma2_true=0.0, alpha=1.0,
                                           kappa_tilt=3.0, sigma_quad=1.0e-6, sigma_dip=3.0e-4,
                                           n_mock=4000, seed=20260701)
        fpr_naive.append(rr["fpr_naive"]); fpr_deproj.append(rr["fpr_deprojected"])
    # covariance inflation 1/(1-r^2) vs the boost-tilt response coupling rho = kappa_tilt*beta
    rho_grid = list(np.linspace(0.0, 0.9, 19))
    inflation = [covariance_inflation(rho, kappa_tilt=1.0, alpha=1.0) for rho in rho_grid]
    c = {
        "theorem_id": "EGS3-C",
        "beta": betas,
        "fpr_naive": fpr_naive,
        "fpr_deprojected": fpr_deproj,
        "nominal_fpr": 0.05,
        "rho": rho_grid,
        "covariance_inflation": inflation,
    }

    # --- D BASS-Extended joint PV+CMB forecast + BipoSH ------------------
    from htt.obsstat import pv_covariance as pv_cov
    from htt.obsstat import joint_pv_cmb_forecast as jfc
    from htt.obsstat import biposh_smica as bsm
    from htt.obsstat.lowell_map_features import _packed_index
    rng = np.random.default_rng(20260702)
    pos = rng.normal(size=(600, 3)) * 50.0
    rad = np.linalg.norm(pos, axis=1); nh = pos / rad[:, None]
    mo = pv_cov.velocity_field_modes(pos, sigma_shear_kms_per_mpc=0.3)
    Uc, Lc = mo["U"][:, 3:], mo["Lambda"][3:]
    sig2 = (rng.uniform(50.0, 150.0, 600)) ** 2
    vv = nh @ np.array([200.0, -90.0, 60.0]) + rng.normal(size=600) * np.sqrt(sig2)
    order = np.argsort(rad)
    fracs = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20]
    gains = []
    for fr in fracs:
        mask = np.zeros(600, bool); mask[order[:int(fr * 600)]] = True
        gains.append(jfc.jwst_anchor_forecast(nh, vv, sig2, mask, jwst_shrink=1 / 3, U=Uc, Lambda=Lc)["precision_gain"])
    f_grid = list(np.linspace(1.0, 20.0, 20))
    infl = [jfc.joint_fisher_forecast(rho=0.6, f_omega_tilt_jwst=f)["inflation_jwst"] for f in f_grid]
    # BipoSH L=1 aberration mechanism: isotropic vs injected l<->l+1
    lmax = 8
    def _packed(seed):
        rr = np.random.default_rng(seed)
        a = rr.normal(size=(lmax + 1) * (lmax + 2) // 2) + 1j * rr.normal(size=(lmax + 1) * (lmax + 2) // 2)
        for l in range(lmax + 1):
            a[_packed_index(lmax, l, 0)] = a[_packed_index(lmax, l, 0)].real
        return a
    iso_L1, ab_L1 = [], []
    for s in range(60):
        a = _packed(2000 + s)
        iso_L1.append(bsm.compute_biposh_from_alm(a, lmax, L_values=(1,)).power_by_L[1])
        aa = a.copy()
        for l in range(2, lmax):
            for m in range(0, l + 1):
                aa[_packed_index(lmax, l + 1, m)] += 0.3 * a[_packed_index(lmax, l, m)]
        ab_L1.append(bsm.compute_biposh_from_alm(aa, lmax, L_values=(1,)).power_by_L[1])
    dfig = {"theorem_id": "EGS3-D", "anchor_fraction": fracs, "precision_gain": gains,
            "f_grid": f_grid, "inflation": infl, "rho": 0.6}
    dbip = {"theorem_id": "EGS3-D", "iso_L1": iso_L1, "aberrated_L1": ab_L1, "coupling_eps": 0.3}

    # --- E identified-set semantics: IM coverage + refutability power ----
    from htt.obsstat.egs3_identified_set import (
        im_coverage_experiment, refutability_power_experiment,
    )
    dos_grid = [0.1, 0.25, 0.5, 1.0, 2.0]
    cov_proj, cov_im, cov_end = [], [], []
    for dos in dos_grid:
        cv = im_coverage_experiment(n_mc=2000, seed=20260708, delta_over_sigma=dos)
        cov_proj.append(cv.coverage_projection)
        cov_im.append(cv.coverage_im)
        cov_end.append(cv.coverage_endpoint)
    e_im = {
        "theorem_id": "EGS3-E2",
        "delta_over_sigma": dos_grid,
        "coverage_projection": cov_proj,
        "coverage_im": cov_im,
        "coverage_endpoint_naive": cov_end,
        "nominal": 0.95,
        "n_mc": 2000,
        "seed": 20260708,
        "small_delta_endpoint_limit": 0.90,       # 1 - 2 alpha at delta -> 0
    }
    pw = refutability_power_experiment(n_mc=1000, seed=20260708)
    e_pow = {
        "theorem_id": "EGS3-E3",
        "amplitudes": list(pw.amplitudes),
        "empty_rate": list(pw.empty_rate),
        "se": list(pw.se),
        "alpha1": pw.alpha1,
        "n_mc": pw.n_mc,
        "seed": pw.seed,
    }

    # --- F shear-memory kernel bias ---------------------------------------
    from htt.obsstat.egs3_shear_memory_bias import kappa_bias_curve
    smb = kappa_bias_curve(e0_grid=tuple(np.linspace(0.0, 2.0, 21)))
    f_smb = {
        "theorem_id": "EGS3-F3",
        "e0_grid": list(smb.e0_grid),
        "kappa_bias_ratio": list(smb.kappa_bias_ratio),
        "zero_crossing_e0": smb.zero_crossing_e0,
        "pi0": smb.pi0, "z0": smb.z0, "H": smb.H, "n_nodes": smb.n_nodes,
    }

    # --- U1/U2 unification: beta-channel correspondence + fingerprint ceilings
    import sympy as _sp
    from htt.obsstat.egs3_teff_unification import (
        BETA_CF4, fingerprint_ceilings as _fpc)
    from htt.teff.representative import two_temperature_ratio as _ttr

    _s = _sp.Symbol("s", positive=True)
    _t = _sp.Symbol("t", positive=True)
    _R3t = _sp.lambdify(_t, _ttr(3)[0].subs(_ttr(3)[1],
                                            _sp.sqrt(_t / (2 + _t))), "numpy")
    _R5t = _sp.lambdify(_t, _ttr(5)[0].subs(_ttr(5)[1],
                                            _sp.sqrt(_t / (2 + _t))), "numpy")
    t_grid = [round(x, 10) for x in np.linspace(1e-6, 0.5, 120)]
    _ceil = _fpc()
    u1 = {
        "theorem_id": "EGS3-U1",
        "t_grid": t_grid,
        "R3_of_t": [round(float(_R3t(x)), 12) for x in t_grid],
        "R5_of_t": [round(float(_R5t(x)), 12) for x in t_grid],
        "tangent_R3": [round(1.0 - 0.75 * x, 12) for x in t_grid],
        "tangent_R5": [round(1.0 + 1.25 * x, 12) for x in t_grid],
        "t_cf4": round(2.0 * float(np.sinh(BETA_CF4)) ** 2, 15),
        "leading_coeffs": ["-3/4", "+5/4"],
    }
    _R3s = _sp.lambdify(_s, _ttr(3)[0].subs(_ttr(3)[1], _s), "numpy")
    _R5s = _sp.lambdify(_s, _ttr(5)[0].subs(_ttr(5)[1], _s), "numpy")
    s_grid = [round(x, 10) for x in np.logspace(-4, np.log10(0.95), 100)]
    u2 = {
        "theorem_id": "EGS3-U2",
        "s_grid": s_grid,
        "dev_R3": [round(float(1.0 - _R3s(x)), 15) for x in s_grid],
        "dev_R5": [round(float(_R5s(x) - 1.0), 15) for x in s_grid],
        "env_R3": [round(1.5 * x * x, 15) for x in s_grid],
        "env_R5": [round(2.5 * x * x, 15) for x in s_grid],
        "eps1": _ceil["eps1_registered"],
        "ceiling_R3": _ceil["ceiling_R3_float"],
        "ceiling_R5": _ceil["ceiling_R5_float"],
        "s_cf4": _ceil["cf4_containment"]["s_cf4_tanh"],
        "fp_cf4": _ceil["cf4_containment"]["fingerprint_3half_s2"],
    }
    # --- U4 statistical closure (from the deterministic seal artifact)
    _seal = json.loads((REPO_ROOT / "docs/generated/teff_statistical_seal.json")
                       .read_text())
    _cov = _seal["im_fingerprint_coverage"]
    _hot = _seal["hotelling_fingerprint_calibration"]
    u4 = {
        "theorem_id": "EGS3-U4",
        "coverage_rows": _cov["rows"],
        "nominal": _cov["nominal"],
        "floor": round(_cov["nominal"] - _cov["binomial_3sigma_tol"], 6),
        "identified_interval_R3": _cov["identified_interval_R3"],
        "size_naive": _hot["empirical_size_naive_chi2"],
        "size_hotelling": _hot["empirical_size_hotelling_F"],
        "alpha": _hot["alpha"],
        "n_sim_cov": _hot["n_sim_cov"],
    }

    return {"a1": a1, "a3": a3, "a1_floor": a1_floor, "b1": b1, "b2": b2,
            "b3": b3, "nt2b1": nt2b1, "psd": psd, "c": c, "d": dfig, "dbip": dbip,
            "e_im": e_im, "e_pow": e_pow, "f_smb": f_smb,
            "u1": u1, "u2": u2, "u4": u4}


def _render(src: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    blue, green, red, orange, grey = "#2563eb", "#16a34a", "#dc2626", "#ea580c", "#64748b"

    # A1 graded rank: response design heatmap + reachable/null labels
    a1 = src["a1"]
    D = np.array(a1["response_design"])
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    im = ax.imshow(D, cmap="Blues", aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(4)); ax.set_xticklabels(a1["sectors"], rotation=20, fontsize=8)
    ax.set_yticks(range(len(a1["channels"]))); ax.set_yticklabels(a1["channels"], fontsize=8)
    # colour the sector tick labels: green = reachable, red = joint null
    for tick, s in zip(ax.get_xticklabels(), a1["sectors"]):
        tick.set_color(green if s in a1["reachable_sectors"] else red)
    ax.set_title(f"EGS3-A1: graded comparator response, rank {a1['rank']}\n"
                 f"green reachable {{Σ²,Ω_tilt}}; red joint null {{W²,Ω_k}}")
    fig.colorbar(im, ax=ax, shrink=0.8, label="leading-EGS response")
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_egs3_a1_graded_rank.png", dpi=140); plt.close(fig)

    # A3 e-value calibration
    a3 = src["a3"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    b = np.array(a3["beta_grid"]); r = np.array(a3["empirical_false_rate"])
    ax.plot(b, b, color=grey, ls="--", label="Markov bound  P(E≥1/β)≤β")
    ax.plot(b, r, marker="o", color=blue, label="empirical false-exceedance")
    ax.fill_between(b, r, b, where=(b >= r), color=green, alpha=0.15, label="conservative margin")
    ax.set_xlabel("β"); ax.set_ylabel("false-exceedance rate")
    ax.set_title(f"EGS3-A3: Π is a calibrated e-value\nnull mean E={a3['null_mean_evalue']:.3f}; bound holds")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_a3_evalue_calibration.png", dpi=140); plt.close(fig)

    # NT2-A1 genuine Fisher floor
    af = src["a1_floor"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(af["lmax"], af["fisher_floor"], marker="o", ms=3, color=blue, label="multi-ℓ Fisher–CR floor")
    ax.axhline(af["single_ell_l2_dispersion"], color=red, ls="--",
               label=f"single-ℓ √(2/5)={af['single_ell_l2_dispersion']:.3f}")
    ax.set_xlabel("ℓ_max in the estimator"); ax.set_ylabel("fractional floor σ(F)/F")
    ax.set_title("NT2-A1: genuine multi-multipole floor\nstrictly below the single-ℓ dispersion")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs2_nt2a1_fisher_floor.png", dpi=140); plt.close(fig)

    # B1 floor profile vs k (+ r_ell inset)
    b1 = src["b1"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.semilogx(b1["k_chi_star"], b1["floor"], marker="o", ms=3, color=blue)
    ax.axhline(b1["saturation_floor"], color=red, ls="--",
               label=f"super-horizon saturation √(2/5)={b1['saturation_floor']:.3f}")
    ax.set_xlabel("k·χ⋆ (shear mode scale)"); ax.set_ylabel("fractional floor σ(F)/F")
    ax.set_title("EGS3-B1: the floor is a k-PROFILE\nsaturates at 0.632; drops below only at finite k")
    ax.legend(fontsize=8)
    ins = ax.inset_axes([0.55, 0.48, 0.4, 0.4])
    ins.plot(b1["r_ell_l"], b1["r_ell"], marker=".", color=green)
    ins.set_title("r_ℓ decay (k=7e-5)", fontsize=7); ins.tick_params(labelsize=6)
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_egs3_b1_floor_profile.png", dpi=140); plt.close(fig)

    # B2 Volterra depth memory
    b2 = src["b2"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(b2["z"], b2["shear_volterra"], color=blue, lw=2, label="shear σ(z)  (Volterra of Π)")
    ax.plot(b2["z"], b2["pi_of_z"], color=orange, lw=1.5, ls="-.", label="tilt stress Π(z)")
    ax2 = ax.twinx()
    ax2.plot(b2["z"], b2["memory_kernel"], color=grey, ls="--", label="memory kernel e^{-3∫H}")
    ax2.set_ylabel("kernel", color=grey)
    ax.set_xlabel("depth z"); ax.set_ylabel("σ(z), Π(z)")
    ax.set_title("EGS3-B2: depth gap is a Volterra memory of Π\nexponential kernel e^{-3∫H}")
    ax.legend(fontsize=7, loc="upper right"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_b2_volterra.png", dpi=140); plt.close(fig)

    # B3 vorticity radial-blind vs transverse
    b3 = src["b3"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.hist(b3["radial_response"], bins=30, color=red, alpha=0.7, label="radial  n·Ω·n ≡ 0 (blind)")
    ax.hist(b3["transverse_response"], bins=30, color=green, alpha=0.5, label="transverse  n·Ω·m ≠ 0 (re-opens)")
    ax.axvline(0.0, color=grey, ls="--")
    ax.set_xlabel("vorticity channel response"); ax.set_ylabel("count")
    ax.set_title("EGS3-B3: vorticity re-opening\nradial blind; transverse channel breaks the no-go")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_b3_vorticity.png", dpi=140); plt.close(fig)

    # NT2-B1 two-sided bracket
    nb = src["nt2b1"]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    # log-y: the MES upper bound is quadratic in a2 and would otherwise crush the
    # load-bearing lower bound (the strong new content) onto the axis.
    ax.fill_between(nb["a2"], nb["F_lo"], nb["F_hi"], color=blue, alpha=0.2, label="admissible F_shear band")
    ax.semilogy(nb["a2"], nb["F_lo"], color=green, lw=2, label="lower bound > 0 (excludes 0)")
    ax.semilogy(nb["a2"], nb["F_hi"], color=red, lw=2, label="upper bound (MES)")
    ax.set_xlabel("CMB quadrupole a₂"); ax.set_ylabel("F_shear (log)")
    ax.set_title("NT2-B1: two-sided shear/F bracket\nlower bound is strictly positive — zero is excluded")
    ax.legend(fontsize=8, loc="lower right"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs2_nt2b1_bracket.png", dpi=140); plt.close(fig)

    # PSD-cone redesign schematic
    ps = src["psd"]
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.2, 3.6))
    # null-KIND distinction (2026-07 review P2): W2 is a genuine structural
    # null (red); Omega_k is a leading-order no-channel that re-opens beyond
    # leading order (amber) -- not the same kind of null.
    amber_nc = "#e08a00"
    cols = []
    for s in ps["sectors"]:
        if s in ps["reachable_sectors"]:
            cols.append(green)
        elif s == "W2":
            cols.append(red)
        else:
            cols.append(amber_nc)
    axa.bar(range(4), ps["spectrum"], color=cols)
    axa.set_xticks(range(4)); axa.set_xticklabels(ps["sectors"], rotation=20, fontsize=8)
    axa.set_ylabel("labelled eigenvalue (sector)")
    axa.set_title(f"M=diag(g), moment block ⪰0, rank {ps['reachable_rank']} reachable\n"
                  f"green=reachable, red=structural null,\norange=leading-order no-channel",
                  fontsize=9)
    # cone-shell on the lambda_Sigma = Sigma^2 axis (log-x: the squared bracket
    # spans ~4 decades after the 2026-07 units repair)
    axb.axvspan(ps["shell_s_lo"], ps["shell_s_hi"], color=blue, alpha=0.18, label="cone-shell")
    axb.axvline(ps["shell_lambda_sigma"], color=green, lw=2, label="observed λ_Σ = Σ²")
    axb.axvline(ps["shell_s_lo"], color=red, lw=2,
                label="s_lo>0: FLRW vertex λ_Σ=0 excluded")
    axb.set_xscale("log")
    axb.set_xlim(ps["shell_s_lo"] * 0.2, ps["shell_s_hi"] * 3.0); axb.set_yticks([])
    axb.set_xlabel("shear eigenvalue λ_Σ = Σ² (log)")
    axb.set_title("convex cone-shell bracket (Σ² units)\ns_lo>0 excludes the vertex")
    axb.legend(fontsize=7)
    fig.suptitle(f"EGS3 PSD-cone redesign: x_C=tr(C M) bit-identical = {ps['bit_identical']}", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_egs3_psd_cone.png", dpi=140); plt.close(fig)

    # C kinematic deprojection: FPR (naive vs deprojected) + covariance inflation
    cc = src["c"]
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.4, 3.6))
    axa.plot(cc["beta"], cc["fpr_naive"], marker="o", color=red, label="naive Σ² (reads all quad. power as shear)")
    axa.plot(cc["beta"], cc["fpr_deprojected"], marker="s", color=green, label="deprojected Σ̃² (boost-immune)")
    axa.axhline(cc["nominal_fpr"], color=grey, ls="--", label=f"nominal {cc['nominal_fpr']:.2f}")
    axa.set_xlabel("boost β"); axa.set_ylabel("false-positive rate (pure bulk-flow sky)")
    axa.set_ylim(-0.03, 1.03)
    axa.set_title("EGS3-C4: boost→shear false positive\nkilled by the kinematic deprojection")
    axa.legend(fontsize=7, loc="center right")
    axb.plot(cc["rho"], cc["covariance_inflation"], color=blue, lw=2)
    axb.axhline(1.0, color=grey, ls="--", label="no coupling (β→0)")
    axb.set_xlabel("boost–tilt response coupling ρ = √α·κ_T·β")
    axb.set_ylabel("Σ² covariance inflation  1/(1−r²)")
    axb.set_title("EGS3-C2: coupled-Fisher inflation\n→ 1 as β → 0")
    axb.legend(fontsize=7, loc="upper left")
    fig.suptitle("EGS3-C: kinematic deprojection makes the low-ℓ shear reading boost-immune "
                 "(estimator property; Σ² stays partial)", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_egs3_c_deprojection.png", dpi=140); plt.close(fig)

    # D BASS-Extended joint forecast: JWST Omega_tilt gain + Sigma^2 inflation reduction
    dd = src["d"]
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.4, 3.6))
    axa.plot([100 * f for f in dd["anchor_fraction"]], dd["precision_gain"], marker="o", color=blue)
    axa.axhline(1.0, color=grey, ls="--", label="no gain")
    axa.set_xlabel("JWST-anchored fraction of groups (%)")
    axa.set_ylabel("Ω_tilt precision gain (feasible Woodbury GLS)")
    axa.set_title("EGS3-D1: PV Ω_tilt precision vs JWST anchors\n(survey-design forecast)")
    axa.legend(fontsize=7)
    axb.plot(dd["f_grid"], dd["inflation"], color=green, lw=2)
    axb.axhline(1.0, color=grey, ls="--", label="no coupling")
    axb.set_xlabel("PV/JWST Ω_tilt prior precision  f")
    axb.set_ylabel("Σ² covariance inflation  1/(1−r²)")
    axb.set_title("EGS3-D2: prior breaks the Σ²–Ω_tilt degeneracy\n(inflation ↓ as prior ↑; ρ=0.6)")
    axb.legend(fontsize=7)
    fig.suptitle("EGS3-D: joint PV+CMB forecast — a PV Ω_tilt prior removes the observer-boost "
                 "Σ² leakage (forecast; Σ² stays partial; theory-g CMB fail-closed)", fontsize=7.5)
    fig.tight_layout(); fig.savefig(FIG_DIR / "fig_egs3_d_joint_forecast.png", dpi=140); plt.close(fig)

    # D BipoSH L=1 aberration channel (mechanism): isotropic vs injected l<->l+1
    db = src["dbip"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.hist(db["iso_L1"], bins=18, color=grey, alpha=0.7, label="isotropic (SI null)")
    ax.hist(db["aberrated_L1"], bins=18, color=red, alpha=0.5, label=f"+ l↔l+1 aberration (ε={db['coupling_eps']})")
    ax.set_xlabel("L=1 BipoSH power  D¹  (boost/aberration channel)")
    ax.set_ylabel("count")
    ax.set_title("EGS3-D3: the L=1 BipoSH channel responds to an\nobserver-boost aberration "
                 "(measured on real SMICA, k1_biposh_smica)")
    ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_d_biposh.png", dpi=140); plt.close(fig)

    # E2 Imbens-Manski vs projection vs naive endpoint coverage
    ei = src["e_im"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.plot(ei["delta_over_sigma"], ei["coverage_projection"], marker="o", color=blue,
            label="projection z(1−α/2)  (set CI, conservative)")
    ax.plot(ei["delta_over_sigma"], ei["coverage_im"], marker="s", color=green,
            label="Imbens–Manski C_N  (parameter CI, nominal)")
    ax.plot(ei["delta_over_sigma"], ei["coverage_endpoint_naive"], marker="^", color=red,
            label="naive endpoint z(1−α)  (undercovers)")
    ax.axhline(ei["nominal"], color=grey, ls="--", label=f"nominal {ei['nominal']:.2f}")
    ax.axhline(ei["small_delta_endpoint_limit"], color=red, ls=":", lw=1,
               label="naive Δ→0 limit 1−2α")
    ax.set_xlabel("interval width / endpoint s.e.  (Δ/σ)")
    ax.set_ylabel("MC coverage of a boundary point")
    ax.set_ylim(0.87, 1.0)
    ax.set_title(f"EGS3-E2 (P35): identified-set endpoint coverage\nN={ei['n_mc']}/point, seed {ei['seed']}")
    ax.legend(fontsize=7, loc="lower right"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_e_im_coverage.png", dpi=140); plt.close(fig)

    # E3 refutability power curve
    ep = src["e_pow"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.errorbar(ep["amplitudes"], ep["empty_rate"], yerr=[3 * s for s in ep["se"]],
                marker="o", color=blue, capsize=3, label="empty-set rate (±3 SE)")
    ax.axhline(ep["alpha1"], color=grey, ls="--", label=f"size α₁={ep['alpha1']:.2f}")
    ax.axhline(1.0, color=green, ls=":", lw=1)
    ax.set_xlabel("orthogonal misfit injection amplitude a")
    ax.set_ylabel("P(G(y) = ∅)  = specification-test power")
    ax.set_ylim(-0.03, 1.05)
    ax.set_title(f"EGS3-E3 (M2′): the empty feasible set is REFUTABILITY\nsize α₁ at a=0, "
                 f"power → 1 (N={ep['n_mc']}, seed {ep['seed']})")
    ax.legend(fontsize=8, loc="center right"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_e_refutability_power.png", dpi=140); plt.close(fig)

    # F3 shear-memory kernel kappa-inference bias
    fs = src["f_smb"]
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    ax.plot(fs["e0_grid"], fs["kappa_bias_ratio"], marker="o", ms=3, color=blue,
            label="κ̂/(κ/2) − 1  (registered-law fit on exact-law trajectories)")
    ax.axhline(0.0, color=grey, ls="--")
    ax.axvline(fs["zero_crossing_e0"], color=green, ls=":",
               label=f"friction-matching closure e₀={fs['zero_crossing_e0']:.0f} (unbiased)")
    ax.set_xlabel("toy Weyl-closure coefficient e₀  (E = e₀ H σ)")
    ax.set_ylabel("κ inference bias")
    ax.set_title("EGS3-F3 (P13): the scalar-closure κ is closure-conditional\n"
                 "unbiased only at the friction-matching e₀=1")
    ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_f_shear_memory_bias.png", dpi=140); plt.close(fig)

    # U1 beta-channel correspondence: R3/R5 on the comparator tilt coordinate
    u1 = src["u1"]
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.plot(u1["t_grid"], u1["R3_of_t"], color=blue, lw=2,
            label="R₃(t) exact (antipodal reduction)")
    ax.plot(u1["t_grid"], u1["R5_of_t"], color=green, lw=2, label="R₅(t) exact")
    ax.plot(u1["t_grid"], u1["tangent_R3"], color=blue, ls="--", lw=1,
            label="1 − (3/4)t")
    ax.plot(u1["t_grid"], u1["tangent_R5"], color=green, ls="--", lw=1,
            label="1 + (5/4)t")
    ax.axhline(1.0, color=grey, lw=0.8)
    ax.axvline(u1["t_cf4"], color=red, ls=":",
               label="t at the CF4 bulk-flow rapidity")
    ax.set_xlabel("t = Ω_tilt / ((1+w) Ω_m)   (comparator tilt coordinate)")
    ax.set_ylabel("two-temperature moment ratio")
    ax.set_title("EGS3-U1: one rapidity, two channels\nTeff ratios as exact "
                 "functions of the comparator tilt sector")
    ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_u1_beta_channel.png", dpi=140); plt.close(fig)

    # U2 fingerprint ceilings: proved envelopes + MES eps1 ceiling + CF4 point
    u2 = src["u2"]
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.loglog(u2["s_grid"], u2["dev_R3"], color=blue, lw=2, label="1 − R₃(s)")
    ax.loglog(u2["s_grid"], u2["env_R3"], color=blue, ls="--", lw=1,
              label="(3/2) s² envelope (proved)")
    ax.loglog(u2["s_grid"], u2["dev_R5"], color=green, lw=2, label="R₅(s) − 1")
    ax.loglog(u2["s_grid"], u2["env_R5"], color=green, ls="--", lw=1,
              label="(5/2) s² envelope (proved)")
    ax.axvline(u2["eps1"], color=red, ls=":", label="registered MES ε₁")
    ax.plot([u2["s_cf4"]], [u2["fp_cf4"]], marker="*", ms=11, color=orange,
            ls="none", label="CF4 rapidity (deterministic row)")
    ax.set_xlabel("two-temperature mixing s")
    ax.set_ylabel("fingerprint deviation")
    ax.set_title("EGS3-U2: MES-registry ceilings on the Teff fingerprints\n"
                 "deviations bounded by the proved quadratic envelopes")
    ax.legend(fontsize=7, loc="upper left"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_u2_fingerprint_ceilings.png", dpi=140)
    plt.close(fig)

    # U4 statistical closure: IM coverage bars + Hotelling calibration
    u4 = src["u4"]
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(7.6, 3.8))
    labels = list(u4["coverage_rows"].keys())
    covs = [u4["coverage_rows"][k]["coverage"] for k in labels]
    axa.bar(range(len(labels)), covs, color=blue)
    axa.axhline(u4["nominal"], color=green, ls="--", label="nominal 1−α")
    axa.axhline(u4["floor"], color=red, ls=":", label="binomial 3σ floor")
    axa.set_xticks(range(len(labels)))
    axa.set_xticklabels([l.replace("_", "\n") for l in labels], fontsize=7)
    axa.set_ylim(0.88, 1.0); axa.set_ylabel("empirical IM coverage")
    axa.set_title("IM coverage on the identified\nfingerprint interval "
                  f"[{u4['identified_interval_R3'][0]:.4f}, 1]", fontsize=9)
    axa.legend(fontsize=7, loc="lower right")
    axb.bar([0, 1], [u4["size_naive"], u4["size_hotelling"]],
            color=[red, green])
    axb.axhline(u4["alpha"], color=grey, ls="--", label="nominal α")
    axb.set_xticks([0, 1])
    axb.set_xticklabels([f"naive χ²\n(n_sim={u4['n_sim_cov']} est. cov)",
                         "Hotelling/F"], fontsize=8)
    axb.set_ylabel("empirical size")
    axb.set_title("T4′ on the joint fingerprint:\nestimated covariance needs "
                  "the F correction", fontsize=9)
    axb.legend(fontsize=7)
    fig.suptitle("EGS3-U4: the EGS3 statistical machinery closed over the "
                 "Teff fingerprint lane (display mixings, disclosed)",
                 fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_egs3_u4_teff_im_coverage.png", dpi=140)
    plt.close(fig)


_SPECS = [
    ("fig_egs3_a1_graded_rank", "EGS3-A1", "Graded comparator identifiability rank", "a1"),
    ("fig_egs3_a3_evalue_calibration", "EGS3-A3", "Pi e-value Markov calibration", "a3"),
    ("fig_egs2_nt2a1_fisher_floor", "NT2-A1", "Genuine multi-multipole Fisher-CR floor", "a1_floor"),
    ("fig_egs3_b1_floor_profile", "EGS3-B1", "Semi-native floor profile in the shear scale k", "b1"),
    ("fig_egs3_b2_volterra", "EGS3-B2", "Volterra depth-memory of the tilt stress", "b2"),
    ("fig_egs3_b3_vorticity", "EGS3-B3", "Vorticity re-opening: radial blind, transverse channel", "b3"),
    ("fig_egs2_nt2b1_bracket", "NT2-B1", "Two-sided shear/F bracket excluding zero", "nt2b1"),
    ("fig_egs3_psd_cone", "EGS3-PSD", "PSD-cone comparator redesign", "psd"),
    ("fig_egs3_c_deprojection", "EGS3-C", "Kinematic deprojection of the observer-boost quadrupole", "c"),
    ("fig_egs3_d_joint_forecast", "EGS3-D", "BASS-Extended joint PV+CMB information forecast", "d"),
    ("fig_egs3_d_biposh", "EGS3-D", "SMICA BipoSH L=1 boost-aberration channel", "dbip"),
    ("fig_egs3_e_im_coverage", "EGS3-E2", "Imbens-Manski vs projection interval coverage", "e_im"),
    ("fig_egs3_e_refutability_power", "EGS3-E3", "Refutability (empty-set) power curve", "e_pow"),
    ("fig_egs3_f_shear_memory_bias", "EGS3-F3", "Shear-memory kernel kappa-inference bias", "f_smb"),
    ("fig_egs3_u1_beta_channel", "EGS3-U1", "Beta-channel correspondence: Teff ratios on the comparator tilt coordinate", "u1"),
    ("fig_egs3_u2_fingerprint_ceilings", "EGS3-U2", "MES-registry ceilings on the Teff fingerprints", "u2"),
    ("fig_egs3_u4_teff_im_coverage", "EGS3-U4", "Statistical closure over the Teff fingerprint lane", "u4"),
]


def _sidecar_payloads(src: dict) -> dict[str, tuple[str, str]]:
    out = {}
    for stem, tid, title, key in _SPECS:
        source = src[key]
        out[stem] = (
            json.dumps(source, indent=2, sort_keys=True) + "\n",
            json.dumps(_manifest(stem, tid, title, source), indent=2, sort_keys=True) + "\n",
        )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    src = _sources()
    payloads = _sidecar_payloads(src)
    if args.check:
        stale = []
        for stem, (exp_src, exp_man) in payloads.items():
            for path, content in ((FIG_DIR / f"{stem}.source.json", exp_src),
                                  (FIG_DIR / f"{stem}.manifest.json", exp_man)):
                if (path.read_text(encoding="utf-8") if path.exists() else None) != content:
                    stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale EGS2/EGS3 theorem figure sidecars:", *stale, sep="\n  - ")
            return 1
        print("EGS2/EGS3 theorem figure sidecars up to date")
        return 0
    _render(src)
    for stem, (exp_src, exp_man) in payloads.items():
        (FIG_DIR / f"{stem}.source.json").write_text(exp_src, encoding="utf-8")
        (FIG_DIR / f"{stem}.manifest.json").write_text(exp_man, encoding="utf-8")
        print(f"wrote figures/current/{stem}.png (+ source.json, manifest.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
