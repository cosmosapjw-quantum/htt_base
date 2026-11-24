"""R108 radio lane: collect the headline numbers of THEORY_C1.json, P_OF_C1_THEORY.json and RACS_DIPOLE.json into SUMMARY.json.

Purpose: one small index for the lead, every number copied from a lane result JSON (path given next to it), plus the SHA-256
of each result file, of the RACS download receipts and of the large derived files kept under ~/Downloads/htt_r108/radio/.
Inputs: the three result JSONs and V3_DIAGNOSTIC.json (SHA-256 recorded), ~/Downloads/htt_r108/radio/RECEIPTS.jsonl (D11 strip
    lines; pre-existing-input lines are counted separately).
Claim class: every p copied here is CONDITIONAL (claim_class block; p_conditional fields; RACS contrast p keep RACS_DIPOLE's
    claim label). The V3 low-l systematic and the margins with it are copied from THEORY_C1.json, not recomputed.
Units: C1 dimensionless; dipoles dimensionless; bytes.
Usage (repo root): python3 -m scripts.r108.radio_summary --dir docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/RADIO
No randomness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RADIO_DL = Path.home() / "Downloads/htt_r108/radio"


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    a = ap.parse_args(argv)
    d = Path(a.dir)
    th_p, pc_p, rc_p, v3_p = d / "THEORY_C1.json", d / "P_OF_C1_THEORY.json", d / "RACS_DIPOLE.json", d / "V3_DIAGNOSTIC.json"
    th, pc, rc, v3d = (json.loads(p.read_text()) for p in (th_p, pc_p, rc_p, v3_p))
    allrec = [json.loads(x) for x in (RADIO_DL / "RECEIPTS.jsonl").read_text().splitlines() if x.strip()]
    rec = [r for r in allrec if r.get("id") == "D11"]
    pre = [r for r in allrec if r.get("id") != "D11"]
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    out = dict(schema="htt.r108.radio.summary/2", node="SQ-RADIO", git_head=head,
               command=" ".join([sys.executable, "-m", "scripts.r108.radio_summary", *(argv or sys.argv[1:])]),
               result_files={p.name: dict(path=str(p), sha256=sha256(p), bytes=p.stat().st_size)
                             for p in sorted(d.glob("*.json")) if p.name != "SUMMARY.json"},
               downloads=dict(receipts=str(RADIO_DL / "RECEIPTS.jsonl"), receipts_sha256=sha256(RADIO_DL / "RECEIPTS.jsonl"),
                              strips=len(rec), rows=sum(r["rows"] for r in rec), bytes=sum(r["bytes"] for r in rec),
                              service=rec[0]["service"], table_query_example=rec[0]["query"],
                              job_ids=[r["job_id"] for r in rec], derived_cache=rc["catalogue"]["cache"],
                              non_download_receipt_lines=[{k: r.get(k) for k in ("id", "name", "path", "sha256", "bytes", "status")}
                                                          for r in pre]))
    out["claim_class"] = dict(
        label="CONDITIONAL", calibrated_p=None,
        p_of_C1=pc["claim_class"],
        racs_contrast_p=rc["claim_labels"]["contrast"],
        statement=("every p in this file is CONDITIONAL: p_of_C1 p values are conditional on the R106 EMPIRICAL_DIFF_SELECTION "
                   "family shape and on C1 (the C1 = 0 mocks do not reproduce overdispersion); the RACS/NVSS contrast p are "
                   "Poisson-sandwich / jackknife-Gaussian and uncalibrated; none is a calibrated significance; no physical "
                   "attribution, no family identification"))
    # theory
    env = th["envelope"]
    out["theory_C1"] = dict(source=str(th_p), validation=dict(
        V1_max_abs_rel_err=max(abs(r["rel_err"]) for r in th["V1_powerlaw_identity"]["results"]),
        V2_max_abs_rel_diff_limber=max(abs(r["rel_diff"]) for r in th["V2_limber_high_ell"]),
        V3_max_abs_rel_density_vs_camb=max(abs(r["density"]["rel"]) for r in th["V3_camb_number_counts"]["results"]),
        V3_max_abs_rel_density_rsd_vs_camb=max(abs(r["density_rsd"]["rel"]) for r in th["V3_camb_number_counts"]["results"]),
        V3_max_abs_rel_density_magnification_vs_camb=max(abs(r["density_magnification_x0p5"]["rel"]) for r in th["V3_camb_number_counts"]["results"]),
        V3_max_abs_camb_GR_terms_rel_l2_10=max(abs(r["camb_all_terms_over_density_rsd_lensing_x1"]) for r in th["V3_camb_number_counts"]["results"]),
        V4_max_abs_rel_convergence=max(abs(r["rel_to_production"]) for r in th["V4_convergence"]),
        camb_sigma8_0=th["camb_sigma8_0"]),
        per_bracket={k: dict(linear=v["linear"]["C1_density"], hmcode2020=v["hmcode2020"]["C1_density"],
                             tf7_growth_form=v["linear_TF7_growth_form_C1"], primary=v["primary"],
                             rsd_rel=v["linear"]["max_rel_change_rsd"],
                             magnification_rel_abs_alpha_le_0p6=v["linear"]["max_rel_change_magnification_abs_alpha_le_0p6"],
                             z_lt_0p1_only=v["linear_C1_z_lt_0p1_only"], z_ge_0p1_only=v["linear_C1_z_ge_0p1_only"])
                     for k, v in th["C1_l1"].items()},
        envelope=env, shot_noise=th["shot_noise_R65_NVSS"], forms_for_R106=th["C1_forms_for_R106"])
    # V3 low-l difference: copied from THEORY_C1.json (power law of |rel| over l = 2..10 per window, extrapolated to l = 1,
    # carried as a one-sided systematic factor); the gap label comes from V3_DIAGNOSTIC.json (integrator and CAMB variations)
    v3s = th["V3_low_l_systematic"]
    out["theory_C1"]["V3_low_l_systematic"] = dict(
        v3s, source=f"{th_p} V3_low_l_systematic", gap_status=v3d["gap_status"],
        gap_status_source=f"{v3_p} gap_status",
        integrator_variant_max_rel_spread=max(v3d["max_rel_spread_over_variants"].values()),
        camb_accuracy_variation=v3d["camb_accuracy_variation"],
        applied_to=("THEORY_C1 envelope.<pv>.with_V3_low_l_systematic, C1_forms_for_R106 *_x_V3_factor_up / *_and_V3_factor_up, "
                    "P_OF_C1_THEORY points labelled 'x V3 low-l systematic', p_of_C1_margins *_x_V3"))
    sn = th["shot_noise_R65_NVSS"]
    mag = {}
    for sel in ("integrated", "peak"):
        x = sn[f"integral_count_slope_x_20_40mJy_{sel}"]
        am = 2 * (x - 1)
        mag[sel] = dict(x=x, alpha_mu=am, rel_change_per_bracket={
            k: (v["linear"]["C_dk"] * 2 * am + am * am * v["linear"]["C_kk"]) / v["linear"]["C1_density"] for k, v in th["C1_l1"].items()})
    out["theory_C1"]["magnification_at_measured_NVSS_x"] = mag
    v3e = env["linear"]["with_V3_low_l_systematic"]
    out["p_of_C1_margins"] = {fam: dict(crossing_0p05=c, over_count_field_max=c / env["linear"]["extended_max"],
                                        over_differential_pair_max=c / env["linear"]["differential_pair_max"]["C1"],
                                        over_minkowski_4max=c / env["linear"]["differential_triangle_bound_4max"],
                                        over_count_field_max_x_V3=c / v3e["extended_max"],
                                        over_differential_pair_max_x_V3=c / v3e["differential_pair_max"],
                                        over_minkowski_4max_x_V3=c / v3e["differential_triangle_bound_4max"],
                                        V3_factor_up=v3e["factor_up"])
                              for fam, c in pc["crossings_r106_0p05"].items()}
    out["p_of_C1_margins_note"] = ("crossing_0p05 = C1 at which the conditional p of the EMPIRICAL_DIFF family reaches 0.05 (R106); "
                                   "margins are crossing / theory C1 (linear P(k)), without and with the V3 low-l systematic "
                                   "factor (x_V3: theory C1 x factor_up, so the margin is divided by factor_up)")
    out["p_of_C1"] = dict(source=str(pc_p), claim_class=pc["claim_class"], classification=pc["classification"],
                          reproduction_passed={k: v["passed"] for k, v in pc["reproduction"].items()},
                          r106_crossings_0p05=pc["crossings_r106_0p05"], dipole_t_self=pc["summary_dipole_t_self"])
    blocks = {}
    for k in ("nvss_full_R65_mask", "nvss_on_overlap_pixels", "racs_full_mask_alpha0p75", "racs_overlap_with_R65_NVSS_mask",
              "racs_full_mask_alpha0p75_cut_x1p5"):
        b = rc[k]
        cd = b["count_dipole_integrated_selection"]["mono_dipole"]
        dd = b["differential_offdiag_dipole"]["mono_dipole"]
        c = b["contrast_R65_estimator"]["dipole"]
        blocks[k] = dict(pixels=b["retained_pixels"], contrast_delta_xy=c["delta_integrated_minus_peak_xy"], wald_t_self=c["wald_t_self"],
                         p_claim_class=rc["claim_labels"]["contrast"],
                         poisson_p_uncalibrated=c["poisson_chi2_2dof_p"],
                         jackknife=b.get("jackknife_nside4_p2", {}).get("wald_jk"),
                         jackknife_p_uncalibrated=b.get("jackknife_nside4_p2", {}).get("gaussian_chi2_2dof_p"),
                         df=b["offdiag_fraction_contrast"]["df"], required_offdiag_dipole=b["required_offdiag_dipole_for_contrast"],
                         count_dipole_amplitude=cd["amplitude"], count_dipole_radec=cd["direction_radec_deg"],
                         count_dipole_over_kinematic=cd["ratio_amplitude_to_kinematic"], count_C1_raw=cd["C1_raw"],
                         count_C1_residual_debiased_pearson=cd["C1_residual_debiased_pearson"],
                         diff_C1_transverse_raw=dd["C1_transverse_raw"], diff_C1_transverse_debiased_pearson=dd["C1_transverse_debiased_pearson"],
                         diff_C1_transverse_interval_68=dd["C1_transverse_raw_one_realisation_interval_68"],
                         shot_noise=b["shot_noise_integrated_selection"])
    out["racs_d11"] = dict(source=str(rc_p), mask=rc["mask_racs"], overlap=rc["mask_overlap"], assumptions=rc["assumptions"],
                           nvss_replay=rc["nvss_r65_replay"], blocks=blocks)
    (d / "SUMMARY.json").write_text(json.dumps(out, indent=1, default=float) + "\n")
    print("wrote", d / "SUMMARY.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
