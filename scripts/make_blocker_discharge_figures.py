#!/usr/bin/env python3
"""REV-R128: figures for the real-data blocker discharges (K1/K5/K6).

A single three-panel measurement figure computed from the committed discharge
JSONs (`docs/generated/k{1,5,6}_*.json`):

  K1  per-statistic local + global look-elsewhere p on the real Planck map
      (isotropic LambdaCDM null; E2E-systematics null still blocked).
  K5  CF4 bulk-flow coverage: measurement-only under-covers; cosmic-variance-
      inclusive coverage is nominal (~0.68).
  K6  CF4 WF-field vorticity is << shear at every radius (curl-suppressed
      reconstruction -> structural no-go), estimator validated by injection.

OBSSTAT model-independent descriptors; no Bianchi family, geometry,
anisotropy-evidence, or native-solver claim. Deterministic content-addressed
sidecars (no git state); --check compares them byte-for-byte.
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
GEN = REPO_ROOT / "docs/generated"
FIG_DIR = REPO_ROOT / "figures" / "current"
STEM = "fig_blocker_discharges"


def _config_hash(payload: dict) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _source() -> dict:
    k1 = json.loads((GEN / "k1_global_maxscan.json").read_text())
    k5 = json.loads((GEN / "k5_cf4_release_coverage.json").read_text())
    k6 = json.loads((GEN / "k6_cf4_curl_posterior.json").read_text())
    return {
        "k1_local_p": k1["smica"]["local_p"],
        "k1_global_p_smica": k1["smica"]["global_p"],
        "k1_global_p_commander": k1["commander"]["global_p"],
        "k5_cov_meas": k5["coverage"]["measurement_noise_only"]["amplitude_coverage"],
        "k5_cov_cv": k5["coverage"]["cosmic_variance_inclusive"]["amplitude_coverage"],
        "k5_amp": k5["measured_bulk"]["amplitude_kms"],
        "k5_err_total": k5["coverage"]["total_amplitude_error_kms"],
        "k6_radii": [int(r[1:]) for r in sorted(k6["per_radius"], key=lambda s: int(s[1:]))],
        "k6_vort": [k6["per_radius"][k]["wf_mean_vorticity_amplitude"]
                    for k in sorted(k6["per_radius"], key=lambda s: int(s[1:]))],
        "k6_shear": [k6["per_radius"][k]["wf_mean_shear_amplitude"]
                     for k in sorted(k6["per_radius"], key=lambda s: int(s[1:]))],
        "k6_ratio_max": k6["vorticity_over_shear_ratio_max"],
    }


def _manifest(source: dict) -> dict:
    return {
        "artifact_id": f"bass.measurement.{STEM}",
        "artifact_path": f"figures/current/{STEM}.png",
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "transfer_source": "mixed_none_and_cf4_wf_proxy",
        "sky_support_status": "real_planck_pr3_and_cf4_release",
        "null_mock_status": "real_data_with_lambdacdm_null_and_release_matched_mocks",
        "covariance_status": "release_matched_mocks_k5_lower_bound_k6",
        "family_identification": False,
        "native_solver_result": False,
        "source_json_path": f"figures/current/{STEM}.source.json",
        "generating_command": "python scripts/make_blocker_discharge_figures.py",
        "config_hash": _config_hash(source),
        "created_by": "scripts/make_blocker_discharge_figures.py",
        "schema_version": "bass.blocker_discharge_figure.v1",
        "caption_policy": [
            "must_state_model_independent_descriptor",
            "must_not_use_for_family_identification_or_family_selection",
            "must_state_no_native_low_ell_solver_output",
            "must_state_k1_e2e_null_still_blocked",
        ],
        "caveats": [
            "K1 null is isotropic LambdaCDM, not FFP10/NPIPE end-to-end; E2E-systematics calibration remains blocked.",
            "K6 is a structural no-go: the CF4 WF reconstruction is curl-suppressed; recovered vorticity is reconstruction-conditioned, not physical.",
            "K5 cosmic-variance coverage is conditional on the fiducial LambdaCDM per-component prior.",
            "Model-independent OBSSTAT descriptors; no Bianchi family-ID or geometry detection.",
        ],
        "promotion_blockers": [
            "native_solver_validation_absent",
            "k1_e2e_systematics_null_absent",
            "family_identification_blocked_pre_native_atlas",
        ],
        "publication_gates": {
            "bianchi_evidence_claim": "fail_model_independent_descriptor_only",
            "family_identification_claim": "fail_blocked_pre_native_atlas",
        },
        "title": "Real-data blocker discharges (K1/K5/K6)",
        "source": source,
    }


def _render(s: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    blue, green, red, grey = "#2563eb", "#16a34a", "#dc2626", "#64748b"
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12.4, 3.9))

    # K1: per-statistic local p + global p
    keys = list(s["k1_local_p"])
    short = {"s_one_half": "S$_{1/2}$", "parity_even_over_odd_ratio": "parity ratio",
             "parity_asymmetry": "parity asym", "planarity_mean": "planarity",
             "qo_axis_alignment_deg": "QO align", "axis_to_cmb_dipole_deg": "dipole align"}
    vals = [s["k1_local_p"][k] for k in keys]
    ax1.barh(range(len(keys)), vals, color=blue, alpha=0.8)
    ax1.set_yticks(range(len(keys))); ax1.set_yticklabels([short.get(k, k) for k in keys], fontsize=8)
    ax1.axvline(s["k1_global_p_smica"], color=red, ls="--",
                label=f"global p={s['k1_global_p_smica']:.3f}")
    ax1.axvline(0.05, color=grey, ls=":", lw=1)
    ax1.set_xlabel("local p (isotropic $\\Lambda$CDM null)")
    ax1.set_title("K1: real Planck SMICA low-$\\ell$ morphology\nlook-elsewhere global p (E2E null still blocked)", fontsize=9)
    ax1.legend(fontsize=8, loc="lower right")

    # K5: coverage bars
    ax2.bar(["measurement\nonly", "cosmic-variance\ninclusive"],
            [s["k5_cov_meas"], s["k5_cov_cv"]], color=[red, green], alpha=0.85)
    ax2.axhline(0.68, color=grey, ls="--", label="nominal 0.68")
    ax2.set_ylim(0, 1); ax2.set_ylabel("bulk-flow amplitude coverage")
    ax2.set_title(f"K5: CF4 |B|={s['k5_amp']:.0f}$\\pm${s['k5_err_total']:.0f} km/s\nrelease-matched mock coverage", fontsize=9)
    ax2.legend(fontsize=8)

    # K6: vorticity vs shear per radius
    r = s["k6_radii"]
    ax3.plot(r, s["k6_shear"], marker="o", color=blue, label="shear |$\\sigma$|")
    ax3.plot(r, s["k6_vort"], marker="s", color=red, label="vorticity |$\\omega$|")
    ax3.set_yscale("log"); ax3.set_xlabel("analysis radius [Mpc]")
    ax3.set_ylabel("amplitude [km/s/Mpc]")
    ax3.set_title(f"K6: CF4 WF field curl-suppressed\n|$\\omega$|/|$\\sigma$|$\\leq${s['k6_ratio_max']:.3f} (structural no-go)", fontsize=9)
    ax3.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(FIG_DIR / f"{STEM}.png", dpi=140)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    source = _source()
    exp_src = json.dumps(source, indent=2, sort_keys=True) + "\n"
    exp_man = json.dumps(_manifest(source), indent=2, sort_keys=True) + "\n"
    if args.check:
        stale = []
        for path, content in ((FIG_DIR / f"{STEM}.source.json", exp_src),
                              (FIG_DIR / f"{STEM}.manifest.json", exp_man)):
            if (path.read_text() if path.exists() else None) != content:
                stale.append(path.relative_to(REPO_ROOT).as_posix())
        if stale:
            print("stale blocker-discharge figure sidecars:", *stale, sep="\n  - ")
            return 1
        print("blocker-discharge figure sidecars up to date")
        return 0
    _render(source)
    (FIG_DIR / f"{STEM}.source.json").write_text(exp_src)
    (FIG_DIR / f"{STEM}.manifest.json").write_text(exp_man)
    print(f"wrote figures/current/{STEM}.png (+ source.json, manifest.json)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
