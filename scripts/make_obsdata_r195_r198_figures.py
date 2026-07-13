#!/usr/bin/env python3
"""Observed-data analysis figures for the rev-r195..r198 lanes (REV-R198).

Physics/statistics-result figures rendered from the committed analysis cards
(NOT dev-history / claim-gate / limitation-narrative content). Each figure ships
a deterministic source.json (the plotted values, read from the cards) + a gated
manifest; --check compares those sidecars byte-for-byte (content-addressed, no
git state, so stable across commits).

Deck (each from one committed card, diagnostic-only, observed data):
  cf4_mv_bulkflow          MV ideal-window |B|(R) + the literature band
  cf4_reconstruction       |B| across the 7 reconstruction methods
  cf4_mock_significance    |B|_obs vs the in-house LambdaCDM forward-mock null
  cf4_fsigma8_ml           ML -2 dlnL(f sigma_8) profile + CF4/Planck
  cf4_velocity_correlation the Gorski Psi_par/Psi_perp(r) data vs linear theory
  desi_dipole_mock         observed dipole vs the LambdaCDM clustering mock null
  cf4pp_vorticity          WF mean-field curl/div + the CR curl vs corr. length
  act_kappa                per-ell debiased kappa band power + the 95% CL limit

Diagnostic-only kinematic/statistical descriptors; no Bianchi family, geometry,
or observer-frame claim; no native low-ell solver output.
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
FIG_DIR = REPO_ROOT / "figures" / "obsdata_current"
GEN = REPO_ROOT / "docs/generated"

BLUE, GREEN, RED, ORANGE, GREY, PURPLE = (
    "#1f5fa8", "#2c8c3c", "#c02c2c", "#e08a00", "#666666", "#7030a0")


def _card(name: str) -> dict:
    return json.loads((GEN / name).read_text())


def _config_hash(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _manifest(stem: str, title: str, source: dict) -> dict:
    return {
        "artifact_id": f"bass.obsdata.{stem}",
        "artifact_path": f"figures/obsdata_current/{stem}.png",
        "owner": "OBSSTAT",
        "implementation_scope": "htt_obsstat",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "transfer_source": "none",
        "sky_support_status": "directional_descriptor_only",
        "null_mock_status": "real_data_and_in_house_lcdm_mocks",
        "covariance_status": "linear_lcdm_or_analytic",
        "family_identification": False,
        "native_solver_result": False,
        "source_json_path": f"figures/obsdata_current/{stem}.source.json",
        "statistics_definitions": {"program": "obsdata_r195_r198", "figure": stem},
        "generating_command": "python scripts/make_obsdata_r195_r198_figures.py",
        "config_hash": _config_hash(source),
        "created_by": "scripts/make_obsdata_r195_r198_figures.py",
        "schema_version": "bass.obsdata_figure.v1",
        "caption_policy": [
            "must_state_observed_data_diagnostic",
            "must_not_state_family_identification",
            "must_not_state_native_low_ell_solver_output",
            "must_not_state_detection",
        ],
        "caveats": [
            "Observed-data / in-house-mock analysis figure; diagnostic-only.",
            "Kinematic/statistical descriptor; no geometry-detection, no "
            "family-identification, no observer-frame-violation claim.",
            "No native low-ell solver output is used.",
        ],
        "failed_gates": [
            "native_low_ell_solver_not_available",
            "family_morphology_atlas_not_available",
        ],
        "passed_gates": [
            "gate_test_present", "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "title": title,
        "source": source,
    }


# ---------------------------------------------------------------- sources ----
def _sources() -> dict:
    src: dict[str, dict] = {}

    mv = _card("cf4_mv_bulkflow_card.json")
    Rs = [50, 100, 150, 200]
    src["cf4_mv_bulkflow"] = {
        "R": Rs,
        "amp": [mv["bulk_flow_vs_R"][str(r)]["amplitude_kms"] for r in Rs],
        "cv_err": [mv["bulk_flow_vs_R"][str(r)]["cosmic_variance_error_kms"] for r in Rs],
        "watkins": [mv["literature_crosscheck"]["watkins2023_200hmpc_kms"], 36.0, 200],
        "whitford": [mv["literature_crosscheck"]["whitford2023_173mpch_kms"], 108.0, 173],
        "sigma_lo": mv["bulk_flow_vs_R"]["200"]["significance"]["sigma_pk_corrected"],
        "sigma_hi": mv["bulk_flow_vs_R"]["200"]["significance"]["sigma_full_fiducial_pk"],
    }

    rc = _card("cf4_reconstruction_dependence_card.json")
    m = rc["reconstruction_method_comparison"]
    methods = [("Vpds", m["Vpds"]["amplitude_kms"], "direct"),
               ("Vpwf", m["Vpwf"]["amplitude_kms"], "pure-WF"),
               ("Vpec", m["Vpec"]["amplitude_kms"], "ramp/WF")]
    for key, lbl in (("cf4pp_wf_field_affine_bulk", "CF4++ field"),
                     ("carrick2015_2mpp_affine_bulk", "Carrick 2M++"),
                     ("lilow_nn_2mrs_affine_bulk", "LVN-2024 NN"),
                     ("coras_2mrs_affine_bulk", "CORAS 2021")):
        b = rc.get(key)
        if b:
            methods.append((lbl, b["150"]["amplitude_kms"], "field@150"))
    src["cf4_reconstruction"] = {
        "labels": [x[0] for x in methods],
        "amp": [x[1] for x in methods],
        "kind": [x[2] for x in methods],
        "spread": rc["cross_method_spread_incl_field"]["amplitude_spread_kms"],
    }

    mk = _card("cf4_mock_significance_card.json")["bulk_flow_significance_vs_R"]
    src["cf4_mock_significance"] = {
        "R": Rs,
        "obs": [mk[str(r)]["amplitude_obs_kms"] for r in Rs],
        "mock_rms": [mk[str(r)]["mock_amplitude_rms_kms"] for r in Rs],
        "sigma_param": [mk[str(r)]["significance_parametric_mock_sigma"] for r in Rs],
        "floor": [mk[str(r)]["significance_empirical_floor_sigma"] for r in Rs],
        "rho": [mk[str(r)]["cov_ratio_mock_over_analytic_linear"] for r in Rs],
    }

    ml = _card("cf4_velocity_correlation_ml_card.json")
    pk_corr = ml["shape_correction_pk_corr"]
    src["cf4_fsigma8_ml"] = {
        # the profile is stored vs the RAW EH98 f sigma_8; plot it in the SAME
        # shape-corrected (physical) space as f_sigma8_ml + CF4 + Planck
        "grid": [round(g / pk_corr ** 0.5, 4) for g in ml["f_sigma8_grid"]],
        "dchi2": ml["per_variant"]["Vpec"]["profile_minus2dlnL"],
        "fs8": ml["per_variant"]["Vpec"]["f_sigma8_ml"],
        "fs8_err": ml["per_variant"]["Vpec"]["f_sigma8_fisher_error"],
        "fs8_jk": ml["per_variant"]["Vpec"]["f_sigma8_jackknife_error"],
        "cf4": ml["cf4_published_anchor"], "planck": ml["planck_f_sigma8"],
        "fid": ml["fiducial_f_sigma8"],
    }

    vc = _card("cf4_velocity_correlation_card.json")
    src["cf4_velocity_correlation"] = {
        "r": vc["separation_bins_hmpc"],
        "th_par": vc["theory_psi_par_kms2"], "th_perp": vc["theory_psi_perp_kms2"],
        "d_par": vc["per_variant"]["Vpec"]["psi_par_data_kms2"],
        "d_perp": vc["per_variant"]["Vpec"]["psi_perp_data_kms2"],
    }

    dm = _card("desi_dipole_mock_card.json")
    biases = sorted(dm["lcdm_clustering_mock_null"], key=float)
    src["desi_dipole_mock"] = {
        "obs": dm["observed_dipole_amplitude"],
        "bias": [float(b) for b in biases],
        "mock_mean": [dm["lcdm_clustering_mock_null"][b]["mock_dipole_mean"] for b in biases],
        "mock_std": [dm["lcdm_clustering_mock_null"][b]["mock_dipole_std"] for b in biases],
        "pval": [dm["lcdm_clustering_mock_null"][b]["p_value"] for b in biases],
        "shot_sigma_amp": float(np.linalg.norm(dm["shot_noise"]["sigma_per_component"])),
        "sigma_above_shot": dm["shot_noise"]["sigma_above_shot_noise"],
    }

    vt = _card("cf4pp_vorticity_card.json")
    rows = vt["cr_vorticity_distribution_vs_correlation_length"]
    Rk = sorted(rows, key=float)
    src["cf4pp_vorticity"] = {
        "mean_curl": vt["wf_mean_field"]["rms_curl_kms_per_mpc"],
        "mean_div": vt["wf_mean_field"]["rms_div_kms_per_mpc"],
        "ratio": vt["wf_mean_field"]["curl_over_div_ratio"],
        "R": [float(r) for r in Rk],
        "cr_curl": [rows[r]["cr_rms_curl_mean"] for r in Rk],
        "cr_std": [rows[r]["cr_rms_curl_std"] for r in Rk],
    }

    ak = _card("act_kappa_card.json")
    ells = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    src["act_kappa"] = {
        "ell": ells,
        "data": [ak["cl_debiased_data"][str(l)] for l in ells],
        "sim": [ak["cl_debiased_sim_mean"][str(l)] for l in ells],
        "p": ak["p_value_data_vs_isotropic_sims"],
        "ul_ratio": ak["upper_limit_95cl"]["band_power_95ul_over_sim_median"],
        "band_data": ak["band_statistic_data"],
        "band_ul": ak["upper_limit_95cl"]["band_power_95ul"],
    }
    return src


# ---------------------------------------------------------------- render -----
def _render(src: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    d = src["cf4_mv_bulkflow"]
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.errorbar(d["R"], d["amp"], yerr=d["cv_err"], marker="o", color=BLUE, lw=2,
                capsize=3, label="CF4 MV |B|(R)  (± cosmic var.)")
    ax.errorbar(d["watkins"][2], d["watkins"][0], yerr=d["watkins"][1], marker="s",
                color=RED, capsize=3, label="Watkins 2023 (419±36 @200)")
    ax.errorbar(d["whitford"][2], d["whitford"][0], yerr=d["whitford"][1], marker="^",
                color=ORANGE, capsize=3, label="Whitford 2023 (428±108 @173)")
    ax.set_xlabel("Gaussian window scale R  [h⁻¹Mpc]")
    ax.set_ylabel("bulk-flow amplitude |B|  [km/s]")
    ax.set_title("CF4 minimum-variance ideal-window bulk flow\n"
                 f"|B|(200)={d['amp'][-1]:.0f} km/s; ΛCDM tension {d['sigma_lo']:.1f}–{d['sigma_hi']:.1f}σ")
    ax.legend(fontsize=8); ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_obs_cf4_mv_bulkflow.png", dpi=140); plt.close(fig)

    d = src["cf4_reconstruction"]
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    x = np.arange(len(d["labels"]))
    cols = [BLUE if k in ("direct", "pure-WF", "ramp/WF") else GREEN for k in d["kind"]]
    ax.bar(x, d["amp"], color=cols)
    ax.set_xticks(x); ax.set_xticklabels(d["labels"], rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("bulk-flow amplitude |B|  [km/s]")
    ax.set_title("CF4 bulk flow across 7 reconstruction methods\n"
                 f"(spread {d['spread']:.0f} km/s; blue = PV columns, green = field recon.)")
    ax.grid(alpha=0.25, axis="y"); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_obs_cf4_reconstruction_spread.png", dpi=140); plt.close(fig)

    d = src["cf4_mock_significance"]
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(8.0, 3.9))
    axa.errorbar(d["R"], d["mock_rms"], yerr=d["mock_rms"], fmt="none", ecolor=GREY, alpha=0.0)
    axa.fill_between(d["R"], [0]*4, d["mock_rms"], color=BLUE, alpha=0.18,
                     label="ΛCDM mock |B| RMS (in-house)")
    axa.plot(d["R"], d["mock_rms"], color=BLUE, lw=2, marker="s")
    axa.plot(d["R"], d["obs"], color=RED, lw=2, marker="o", label="observed |B|")
    axa.set_xlabel("R  [h⁻¹Mpc]"); axa.set_ylabel("|B|  [km/s]")
    axa.set_title("observed vs the ΛCDM forward-mock null")
    axa.legend(fontsize=8); axa.grid(alpha=0.25)
    axb.plot(d["R"], d["sigma_param"], color=PURPLE, lw=2, marker="o", label="parametric σ")
    axb.plot(d["R"], d["floor"], color=GREEN, lw=2, marker="s", ls="--", label="2000-mock empirical floor")
    axb.set_xlabel("R  [h⁻¹Mpc]"); axb.set_ylabel("ΛCDM tension  [σ]")
    axb.set_title(f"mock-calibrated significance\n(cov ratio mock/analytic ≈ {np.mean(d['rho']):.2f})")
    axb.legend(fontsize=8); axb.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_obs_cf4_mock_significance.png", dpi=140); plt.close(fig)

    d = src["cf4_fsigma8_ml"]
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.plot(d["grid"], d["dchi2"], color=BLUE, lw=2, label="ML profile −2 ΔlnL (Vpec)")
    ax.axhline(1.0, color=GREY, ls=":", lw=1); ax.axhline(4.0, color=GREY, ls=":", lw=1)
    ax.axvline(d["fs8"], color=BLUE, lw=1.5)
    ax.axvspan(d["fs8"]-d["fs8_jk"], d["fs8"]+d["fs8_jk"], color=BLUE, alpha=0.15,
               label=f"fσ₈={d['fs8']:.2f}±{d['fs8_err']:.2f} (jk ±{d['fs8_jk']:.2f})")
    ax.axvline(d["cf4"], color=GREEN, ls="--", label=f"CF4 {d['cf4']:.2f}")
    ax.axvline(d["planck"], color=RED, ls="-.", label=f"Planck {d['planck']:.2f}")
    ax.set_ylim(0, 12); ax.set_xlabel("f σ₈"); ax.set_ylabel("−2 ΔlnL")
    ax.set_title("CF4 velocity-field ML growth rate\n(shape-corrected; injection-MC-validated unbiased)")
    ax.legend(fontsize=8); ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_obs_cf4_fsigma8_ml.png", dpi=140); plt.close(fig)

    d = src["cf4_velocity_correlation"]
    fig, ax = plt.subplots(figsize=(5.6, 4.2))
    ax.plot(d["r"], d["th_par"], color=BLUE, lw=2, label="Ψ∥ linear theory")
    ax.plot(d["r"], d["th_perp"], color=GREEN, lw=2, label="Ψ⊥ linear theory")
    ax.plot(d["r"], d["d_par"], color=BLUE, marker="o", ls="", label="Ψ∥ data (Vpec)")
    ax.plot(d["r"], d["d_perp"], color=GREEN, marker="s", ls="", label="Ψ⊥ data (Vpec)")
    ax.axhline(0.0, color=GREY, lw=0.8)
    ax.set_xlabel("pair separation r  [h⁻¹Mpc]")
    ax.set_ylabel("Ψ(r)  [km²/s²]")
    ax.set_title("CF4 velocity correlation function\n(reconstruction-independent, from LOS pairs)")
    ax.legend(fontsize=8); ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_obs_cf4_velocity_correlation.png", dpi=140); plt.close(fig)

    d = src["desi_dipole_mock"]
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    ax.errorbar(d["bias"], d["mock_mean"], yerr=d["mock_std"], marker="o", color=BLUE,
                lw=2, capsize=3, label="ΛCDM clustering mock |D| (±1σ)")
    ax.axhline(d["obs"], color=RED, lw=2, label=f"observed D={d['obs']:.4f}")
    ax.axhline(d["shot_sigma_amp"], color=GREY, ls="--",
               label=f"shot-noise σ ({d['sigma_above_shot']:.0f}σ below obs)")
    ax.set_xlabel("linear bias b")
    ax.set_ylabel("number-count dipole |D|")
    ax.set_title("DESI BGS dipole vs the ΛCDM clustering mock null\n"
                 f"clustering-dominated; CONSISTENT (p={d['pval'][1]:.2f} @ b={d['bias'][1]:.1f})")
    ax.legend(fontsize=8); ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_obs_desi_dipole_mock.png", dpi=140); plt.close(fig)

    d = src["cf4pp_vorticity"]
    fig, (axa, axb) = plt.subplots(1, 2, figsize=(8.0, 3.9))
    axa.bar([0, 1], [d["mean_div"], d["mean_curl"]], color=[BLUE, RED])
    axa.set_xticks([0, 1]); axa.set_xticklabels(["RMS |div|", "RMS |curl|"])
    axa.set_ylabel("(km/s) / Mpc")
    axa.set_title(f"WF mean field: curl/div = {d['ratio']:.3f}\n(potential flow — curl suppressed)")
    axa.grid(alpha=0.25, axis="y")
    axb.errorbar(d["R"], d["cr_curl"], yerr=d["cr_std"], marker="o", color=PURPLE,
                 lw=2, capsize=3, label="CR RMS|curl|")
    axb.axhline(d["mean_curl"], color=RED, ls="--", label="WF mean-field |curl|")
    axb.set_xlabel("residual correlation length R  [Mpc]")
    axb.set_ylabel("CR RMS |curl|  [(km/s)/Mpc]")
    axb.set_title("CR vorticity vs correlation length\n(definitive ensemble needs WF operator)")
    axb.legend(fontsize=8); axb.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_obs_cf4pp_vorticity.png", dpi=140); plt.close(fig)

    d = src["act_kappa"]
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    ax.plot(d["ell"], d["data"], color=RED, marker="o", lw=2, label="data (mean-field debiased)")
    ax.plot(d["ell"], d["sim"], color=BLUE, marker="s", lw=1.5, ls="--", label="isotropic ΛCDM sim mean")
    ax.set_xlabel("multipole ℓ")
    ax.set_ylabel("debiased κ band power  C_ℓ")
    ax.set_title("ACT DR6 low-ℓ κ isotropy (independent instrument)\n"
                 f"p={d['p']:.2f} CONSISTENT; 95% CL UL {d['ul_ratio']:.2f}× the sim median")
    ax.legend(fontsize=8); ax.grid(alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "fig_obs_act_kappa.png", dpi=140); plt.close(fig)


TITLES = {
    "cf4_mv_bulkflow": "CF4 MV ideal-window bulk flow |B|(R)",
    "cf4_reconstruction": "CF4 bulk flow across 7 reconstruction methods",
    "cf4_mock_significance": "CF4 |B| vs the in-house LambdaCDM forward-mock null",
    "cf4_fsigma8_ml": "CF4 velocity-field ML f sigma_8 profile",
    "cf4_velocity_correlation": "CF4 Gorski velocity correlation function",
    "desi_dipole_mock": "DESI BGS dipole vs the LambdaCDM clustering mock",
    "cf4pp_vorticity": "CF4++ WF vorticity: mean-field suppression + CR",
    "act_kappa": "ACT DR6 low-ell kappa isotropy + 95% CL upper limit",
}
STEM = {
    "cf4_mv_bulkflow": "fig_obs_cf4_mv_bulkflow",
    "cf4_reconstruction": "fig_obs_cf4_reconstruction_spread",
    "cf4_mock_significance": "fig_obs_cf4_mock_significance",
    "cf4_fsigma8_ml": "fig_obs_cf4_fsigma8_ml",
    "cf4_velocity_correlation": "fig_obs_cf4_velocity_correlation",
    "desi_dipole_mock": "fig_obs_desi_dipole_mock",
    "cf4pp_vorticity": "fig_obs_cf4pp_vorticity",
    "act_kappa": "fig_obs_act_kappa",
}


def _sidecar_payloads(src: dict) -> dict:
    out = {}
    for key, data in src.items():
        stem = STEM[key]
        exp_src = json.dumps(data, indent=2, sort_keys=True) + "\n"
        exp_man = json.dumps(_manifest(stem, TITLES[key], data),
                             indent=2, sort_keys=True) + "\n"
        out[stem] = (exp_src, exp_man)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    src = _sources()
    payloads = _sidecar_payloads(src)
    if args.check:
        stale = []
        for stem, (exp_src, exp_man) in payloads.items():
            for path, content in ((FIG_DIR / f"{stem}.source.json", exp_src),
                                  (FIG_DIR / f"{stem}.manifest.json", exp_man)):
                if (path.read_text() if path.exists() else None) != content:
                    stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale obsdata figure sidecars:", *stale, sep="\n  - ")
            return 1
        print("obsdata r195-r198 figure sidecars up to date")
        return 0
    _render(src)
    for stem, (exp_src, exp_man) in payloads.items():
        (FIG_DIR / f"{stem}.source.json").write_text(exp_src)
        (FIG_DIR / f"{stem}.manifest.json").write_text(exp_man)
        print(f"wrote figures/obsdata_current/{stem}.png (+ source.json, manifest.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
