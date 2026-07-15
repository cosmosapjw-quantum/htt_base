#!/usr/bin/env python3
"""K4: CF4++ reconstruction-functional apex direction and scale versus depth.

REV-R104. The reconstructed CF4++ peculiar-velocity grid (supergalactic
Cartesian positions + velocity vectors) is averaged in radial shells to measure
the bulk-flow apex DIRECTION (Galactic l, b) and amplitude as a function of
depth, with a bootstrap apex dispersion. The manuscript already reports the
scalar radial-velocity-vs-radius profile; the directional apex drift is new.

This is a reconstruction-conditioned systematics descriptor: not HTT evidence, not a
cosmological-frame-violation or tilt claim, not Bianchi family identification.
The C1-K5-MV-F1 finding remains OPEN; the numerical rows are not observed
bulk-flow amplitude or global-tilt measurements. The bootstrap is over
(correlated) reconstruction cells and is a lower bound on
the true direction uncertainty.

Usage:
    venv/bin/python scripts/make_cf4_bulkflow_apex_depth.py [--check]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import astropy.units as u  # noqa: E402
from astropy.coordinates import (  # noqa: E402
    CartesianRepresentation,
    SkyCoord,
    Supergalactic,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
for root in (REPO_ROOT / "htt", REPO_ROOT / "htt" / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.bulkflow_depth import (  # noqa: E402
    angle_between_deg,
    bootstrap_apex_dispersion,
    radial_shell_bulkflow,
)
from common.cf4_p0_quarantine import load_block_record  # noqa: E402

CF4 = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4/query_batch.npz"
OBS_DEFAULTS = REPO_ROOT / "htt/workspace/data/obs_defaults.json"
OUT_JSON = REPO_ROOT / "docs/generated/cf4_bulkflow_apex_depth_report.json"
OUT_MD = REPO_ROOT / "docs/generated/cf4_bulkflow_apex_depth_report.md"
CF4_BLOCK = REPO_ROOT / "docs/generated/cf4_p0_quarantine_block.json"
REMEDIATION_ROOT = REPO_ROOT / "docs/codex_handoff/research_remediation_state.yaml"
FIG_DIR = REPO_ROOT / "figures/observed_current"
FIG = FIG_DIR / "fig_observed_cf4_bulkflow_apex_depth.png"

SHELL_EDGES = [90.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0, 450.0]
N_BOOT = 512
SEED = 20260620


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _git_state() -> tuple[str, str]:
    try:
        short = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
        dirty = subprocess.run(
            ["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown", "unknown"
    return short, (f"{short}+dirty" if dirty else short)


def _sg_unit_to_galactic_lb(vec: np.ndarray) -> tuple[float, float]:
    rep = CartesianRepresentation(float(vec[0]), float(vec[1]), float(vec[2]))
    gal = SkyCoord(rep, frame=Supergalactic).galactic
    return float(gal.l.deg), float(gal.b.deg)


def _galactic_lb_to_sg_unit(l_deg: float, b_deg: float) -> np.ndarray:
    coord = SkyCoord(l=l_deg * u.deg, b=b_deg * u.deg, frame="galactic").supergalactic
    cart = coord.represent_as(CartesianRepresentation)
    vec = np.array([cart.x.value, cart.y.value, cart.z.value], dtype=float)
    return vec / np.linalg.norm(vec)


def build_report(*, generating_command: str, worktree_state: str) -> dict:
    block = load_block_record(REPO_ROOT)
    if block.status != "QUARANTINED_OPEN_FINDINGS":
        raise RuntimeError("CF4 apex diagnostics require the canonical OPEN quarantine block")
    data = np.load(CF4)
    positions = np.c_[data["sgx"], data["sgy"], data["sgz"]].astype(float)
    velocities = np.asarray(data["vxyz_mean"], dtype=float)

    all_bulk = velocities.mean(axis=0)
    all_apex_unit = all_bulk / np.linalg.norm(all_bulk)

    obs_defaults = json.loads(OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    cmb_apex_sg = _galactic_lb_to_sg_unit(cmb["l_deg"], cmb["b_deg"])

    radius = np.linalg.norm(positions, axis=1)
    shells = radial_shell_bulkflow(positions, velocities, SHELL_EDGES)
    rows = []
    for shell in shells:
        mask = (radius >= shell["r_lo"]) & (radius < shell["r_hi"])
        boot = bootstrap_apex_dispersion(velocities[mask], n_boot=N_BOOT, seed=SEED)
        apex_unit = shell["apex_unit"]
        l_deg, b_deg = _sg_unit_to_galactic_lb(apex_unit)
        rows.append(
            {
                "r_lo_mpch": shell["r_lo"],
                "r_hi_mpch": shell["r_hi"],
                "r_mean_mpch": shell["r_mean"],
                "n_cells": shell["n"],
                "bulk_magnitude_kms": shell["bulk_magnitude"],
                "bulk_magnitude_p16_kms": boot["bulk_magnitude_p16"],
                "bulk_magnitude_p84_kms": boot["bulk_magnitude_p84"],
                "apex_galactic_l_deg": l_deg,
                "apex_galactic_b_deg": b_deg,
                "apex_drift_from_full_sample_deg": angle_between_deg(apex_unit, all_apex_unit),
                "apex_angle_to_cmb_dipole_deg": angle_between_deg(apex_unit, cmb_apex_sg),
                "apex_angular_dispersion_deg_median": boot["apex_angular_dispersion_deg_median"],
                "apex_angular_dispersion_deg_p84": boot["apex_angular_dispersion_deg_p84"],
            }
        )

    all_l, all_b = _sg_unit_to_galactic_lb(all_apex_unit)
    config = {"shell_edges_mpch": SHELL_EDGES, "n_boot": N_BOOT, "seed": SEED}
    config_hash = "sha256:" + hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    return {
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "status": "RECONSTRUCTION_CONDITIONED_SYSTEMATICS_DIAGNOSTIC",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "analysis_mode": "reconstruction_conditioned_method_systematics",
        "schema_version": "obsstat.cf4_bulkflow_apex_depth.v1",
        "transfer_source": "external_proxy_cf4_wf_reconstruction",
        "sky_support_status": "cf4_reconstruction_grid",
        "null_mock_status": "bootstrap_over_correlated_reconstruction_cells",
        "config_hash": config_hash,
        "config": config,
        "input_hashes": [_sha256_file(CF4), _sha256_file(REMEDIATION_ROOT)],
        "finding_state": {
            "finding_id": "C1-K5-MV-F1",
            "scientific_status": "OPEN",
            "canonical_source": "docs/generated/cf4_p0_quarantine_block.json",
        },
        "observational_amplitude_claim_allowed": False,
        "global_tilt_claim_allowed": False,
        "cosmological_inference_allowed": False,
        "generating_command": generating_command,
        "git_commit_or_worktree_state": worktree_state,
        "full_sample_bulk_magnitude_kms": float(np.linalg.norm(all_bulk)),
        "full_sample_apex_galactic_lb_deg": [all_l, all_b],
        "cmb_dipole_apex_galactic_lb_deg": [cmb["l_deg"], cmb["b_deg"]],
        "shells": rows,
        "caveats": [
            "numerical rows are functionals of one CF4++ Wiener-filter reconstruction, not observed bulk-flow amplitude measurements",
            "the plotted vectors are volume-averaged reconstruction velocities per shell",
            "bootstrap is over correlated reconstruction cells; a lower bound on the "
            "true direction uncertainty, not a full covariance",
            "no native low-ell solver output or Bianchi family identification",
            "C1-K5-MV-F1 remains OPEN; no global-tilt coordinate or cosmological inference is permitted",
        ],
        "_positions": positions,
        "_velocities": velocities,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# CF4++ Bulk-Flow Apex Versus Depth (REV-R104)",
        "",
        f"owner: {report['owner']}",
        f"implementation_scope: {report['implementation_scope']}",
        f"claim_tier: {report['claim_tier']}",
        f"status: {report['status']}",
        f"allowed_use: {report['allowed_use']}",
        "finding_state: C1-K5-MV-F1 OPEN (canonical PR-120 block)",
        f"transfer_source: {report['transfer_source']}",
        f"null_mock_status: {report['null_mock_status']}",
        f"config_hash: `{report['config_hash']}`",
        "input_hashes:",
        *[f"- {item}" for item in report["input_hashes"]],
        f"generating_command: `{report['generating_command']}`",
        f"git_commit_or_worktree_state: `{report['git_commit_or_worktree_state']}`",
        "",
        f"Full-sample reconstruction functional: {report['full_sample_bulk_magnitude_kms']:.1f} km/s "
        f"toward Galactic (l, b) = "
        f"{report['full_sample_apex_galactic_lb_deg'][0]:.1f}, "
        f"{report['full_sample_apex_galactic_lb_deg'][1]:.1f} deg.",
        "",
        "## Bulk-flow apex by depth shell",
        "",
        "| r [Mpc/h] | N cells | |B| [km/s] | apex l,b [deg] | drift vs full [deg] | angle to CMB apex [deg] |",
        "| --- | --- | --- | --- | --- | --- |",
        *[
            f"| {r['r_lo_mpch']:.0f}-{r['r_hi_mpch']:.0f} | {r['n_cells']} | "
            f"{r['bulk_magnitude_kms']:.0f} (+{r['bulk_magnitude_p84_kms'] - r['bulk_magnitude_kms']:.0f}/"
            f"{r['bulk_magnitude_kms'] - r['bulk_magnitude_p16_kms']:.0f}) | "
            f"{r['apex_galactic_l_deg']:.0f}, {r['apex_galactic_b_deg']:.0f} | "
            f"{r['apex_drift_from_full_sample_deg']:.1f} | {r['apex_angle_to_cmb_dipole_deg']:.1f} |"
            for r in report["shells"]
        ],
        "",
        "## Caveats",
        "",
        *[f"- {item}" for item in report["caveats"]],
        "",
    ]
    return "\n".join(lines)


def _figure_manifest(report: dict) -> dict:
    short, worktree = _git_state()
    return {
        "artifact_id": f"obsstat.observed.{FIG.stem}",
        "artifact_path": FIG.relative_to(REPO_ROOT).as_posix(),
        "artifact_sha256": _sha256_file(FIG),
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned",
        "allowed_use": "paper_appendix",
        "analysis_mode": "reconstruction_conditioned_method_systematics",
        "transfer_source": "external_proxy_cf4_wf_reconstruction",
        "sky_support_status": "cf4_reconstruction_grid",
        "null_mock_status": "bootstrap_over_correlated_reconstruction_cells",
        "config_hash": report["config_hash"],
        "input_hashes": report["input_hashes"],
        "created_by": "scripts/make_cf4_bulkflow_apex_depth.py",
        "generating_command": report["generating_command"],
        "git_commit": short,
        "git_commit_or_worktree_state": worktree,
        "code_version": worktree,
        "schema_version": "obsstat.cf4_bulkflow_apex_figure.v1",
        "finding_state": report["finding_state"],
        "observational_amplitude_claim_allowed": False,
        "global_tilt_claim_allowed": False,
        "cosmological_inference_allowed": False,
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_not_use_for_family_identification_or_family_selection",
            "must_state_no_native_low_ell_solver_output",
        ],
        "caveats": [
            "Reconstruction-conditioned method/systematics diagnostic; numerical values are not observed bulk-flow amplitudes.",
            "No native low-ell solver output or morphology atlas is used.",
            "No Bianchi family-ID or geometry-detection claim is made.",
            "Bootstrap over correlated reconstruction cells; lower bound on uncertainty.",
            "C1-K5-MV-F1 remains OPEN; no global-tilt or cosmological inference is permitted.",
        ],
        "failed_gates": [
            "native_low_ell_solver_not_available",
            "family_morphology_atlas_not_available",
            "full_reconstruction_covariance_not_bound",
        ],
        "passed_gates": [
            "repo_local_observed_data_present",
            "bootstrap_uncertainty_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
        "promotion_blockers": [
            "native_solver_validation_absent",
            "native_morphology_atlas_absent",
            "family_identification_blocked_pre_native_atlas",
            "C1-K5-MV-F1_OPEN",
        ],
        "publication_gates": {
            "bianchi_evidence_claim": "fail_diagnostic_only",
            "frame_violation_claim": "fail_diagnostic_only",
        },
        "required_gates": [
            "repo_local_observed_data_present",
            "manifest_metadata_present",
            "claim_firewall_caption_review",
        ],
    }


def _write_figure(report: dict) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    shells = report["shells"]
    r = [s["r_mean_mpch"] for s in shells]
    mag = [s["bulk_magnitude_kms"] for s in shells]
    lo = [s["bulk_magnitude_kms"] - s["bulk_magnitude_p16_kms"] for s in shells]
    hi = [s["bulk_magnitude_p84_kms"] - s["bulk_magnitude_kms"] for s in shells]
    drift = [s["apex_drift_from_full_sample_deg"] for s in shells]
    to_cmb = [s["apex_angle_to_cmb_dipole_deg"] for s in shells]

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    axes[0].errorbar(r, mag, yerr=[lo, hi], marker="o", color="#2563eb", capsize=3)
    axes[0].set_xlabel("depth r [Mpc/h]")
    axes[0].set_ylabel("bulk flow |B| [km/s]")
    axes[0].set_title("CF4 reconstruction functional vs depth")

    axes[1].plot(r, drift, marker="o", color="#16a34a", label="drift vs full sample")
    axes[1].plot(r, to_cmb, marker="s", color="#dc2626", label="angle to CMB apex")
    axes[1].set_xlabel("depth r [Mpc/h]")
    axes[1].set_ylabel("apex angle [deg]")
    axes[1].set_title("CF4 reconstruction-apex drift")
    axes[1].legend(fontsize=8)

    ls = [s["apex_galactic_l_deg"] for s in shells]
    bs = [s["apex_galactic_b_deg"] for s in shells]
    sc = axes[2].scatter(ls, bs, c=r, cmap="viridis", s=60)
    cl, cb = report["cmb_dipole_apex_galactic_lb_deg"]
    axes[2].scatter([cl], [cb], marker="*", color="k", s=160, label="CMB apex")
    axes[2].set_xlabel("Galactic l [deg]")
    axes[2].set_ylabel("Galactic b [deg]")
    axes[2].set_title("CF4 reconstruction apex (by depth)")
    axes[2].legend(fontsize=8)
    fig.colorbar(sc, ax=axes[2], label="r [Mpc/h]")
    fig.suptitle("CF4++ reconstruction-apex systematics (diagnostic only)", fontsize=12)
    fig.tight_layout()
    fig.savefig(FIG, dpi=140)
    plt.close(fig)

    manifest = _figure_manifest(report)
    FIG.with_suffix("").with_name(FIG.stem + ".manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _public(report: dict) -> dict:
    return {k: v for k, v in report.items() if not k.startswith("_")}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args(argv)
    short, worktree = _git_state()
    report = build_report(
        generating_command="python scripts/make_cf4_bulkflow_apex_depth.py",
        worktree_state=worktree,
    )
    rendered_json = json.dumps(_public(report), indent=2, sort_keys=True) + "\n"
    rendered_md = render_markdown(report)
    if args.check:
        stale = [
            path.relative_to(REPO_ROOT).as_posix()
            for path, content in ((OUT_JSON, rendered_json), (OUT_MD, rendered_md))
            if (path.read_text(encoding="utf-8") if path.exists() else None) != content
        ]
        if stale:
            print("stale CF4 bulk-flow artifacts:", *stale, sep="\n  - ")
            return 1
        print("CF4 bulk-flow apex artifacts up to date")
        return 0
    OUT_JSON.write_text(rendered_json, encoding="utf-8")
    OUT_MD.write_text(rendered_md, encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"wrote {OUT_MD.relative_to(REPO_ROOT)}")
    if not args.no_figures:
        _write_figure(report)
        print(f"wrote {FIG.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
