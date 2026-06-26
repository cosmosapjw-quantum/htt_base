#!/usr/bin/env python3
"""LR-06F: 3D local-flow affine-gradient posterior from the CF4++ reconstruction.

Loads the local CF4++ supergalactic velocity grid
(`workdir/raw/cf4/CF4pp_mean_std_grids.npz`, 128^3, 1000 Mpc box) and fits the
affine flow v = B + M r in spheres of increasing radius, decomposing M into
bulk B, expansion Theta, shear sigma, and vorticity omega. Reports a
bootstrap spread (lower bound, correlated cells), a boundary-cut (radius) sweep,
and a curl-injection recovery test.

Diagnostic-only OBSSTAT result. Vorticity is reconstruction-conditioned; the
cross-reconstruction comparison is BLOCKED_MISSING_FIELD_REALIZATIONS (only the
CF4++ reconstruction is available locally). No Bianchi/geometry/frame-violation
claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT / "htt", REPO_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from obsstat.affine_flow import fit_affine_flow, bootstrap_affine, curl_injection_recovery  # noqa: E402

GRID = REPO_ROOT / "workdir/raw/cf4/CF4pp_mean_std_grids.npz"
BOX_MPC = 1000.0
RADII = [50.0, 100.0, 150.0, 200.0, 250.0]
REPORT_JSON = REPO_ROOT / "docs/generated/cf4_affine_flow_report.json"
REPORT_MD = REPO_ROOT / "docs/generated/cf4_affine_flow_report.md"
FIG = REPO_ROOT / "figures/observed_current/fig_observed_cf4_affine_flow.png"


def _git_state() -> str:
    try:
        c = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip()
        d = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True).stdout.strip()
        return f"{c}+dirty" if d else c
    except Exception:
        return "unknown"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_field():
    data = np.load(GRID)
    v = np.asarray(data["v_mean_CF4pp"], dtype=float)   # (3,N,N,N)
    n = v.shape[1]
    delta = BOX_MPC / n
    centers = (np.arange(n) + 0.5) * delta - BOX_MPC / 2.0
    gx, gy, gz = np.meshgrid(centers, centers, centers, indexing="ij")
    positions = np.column_stack([gx.ravel(), gy.ravel(), gz.ravel()])
    velocities = np.column_stack([v[0].ravel(), v[1].ravel(), v[2].ravel()])
    return positions, velocities, n, delta


def build_report(*, generating_command: str) -> dict:
    positions, velocities, n, delta = _load_field()
    radius_rows = []
    for r in RADII:
        fit = fit_affine_flow(positions, velocities, radius=r)
        radius_rows.append({
            "radius_mpc": r, "n_cells": fit.n_cells,
            "bulk_amplitude_kms": round(fit.bulk_amplitude, 3),
            "bulk_vector_kms": [round(x, 3) for x in fit.bulk.tolist()],
            "expansion_kms_per_mpc": round(fit.expansion, 5),
            "shear_amplitude_kms_per_mpc": round(fit.shear_amplitude, 5),
            "vorticity_amplitude_kms_per_mpc": round(fit.vorticity_amplitude, 6),
        })
    boot = bootstrap_affine(positions, velocities, radius=150.0, n_boot=300, seed=12345)
    # curl injection at a physically small rate (1 km/s/Mpc about SGZ).
    inj = curl_injection_recovery(positions, velocities, radius=150.0, omega_inject=np.array([0.0, 0.0, 1.0]))
    return {
        "artifact_id": "obsstat.cf4_affine_flow",
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "sky_support_status": "cf4_reconstruction_grid",
        "null_mock_status": "bootstrap_over_correlated_reconstruction_cells",
        "ticket": "LR-06F",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": _git_state(),
        "input_hashes": [f"{GRID.relative_to(REPO_ROOT).as_posix()}:{_sha256(GRID)}"],
        "grid": {"n_per_axis": n, "box_mpc": BOX_MPC, "cell_mpc": round(delta, 4),
                 "frame": "supergalactic_cartesian"},
        "radius_sweep": radius_rows,
        "bootstrap_at_150mpc": boot,
        "curl_injection_recovery": inj,
        "cross_reconstruction": {
            "status": "BLOCKED_MISSING_FIELD_REALIZATIONS",
            "detail": "only the CF4++ reconstruction is available locally; a second independent "
                      "reconstruction is required for the cross-reconstruction comparison.",
        },
        "caveats": [
            "Affine-flow decomposition of a single reconstruction; diagnostic-only.",
            "Vorticity is reconstruction-conditioned: potential/Wiener reconstructions suppress curl "
            "by construction, so a small recovered omega is a reconstruction property, not a detection.",
            "Bootstrap over correlated reconstruction cells is a lower bound on the uncertainty, "
            "not a calibrated covariance.",
            "Expansion Theta is the local divergence of the reconstruction, not a global H0 measurement.",
            "No Bianchi/geometry/cosmological-frame-violation claim.",
        ],
    }


def render_md(r: dict) -> str:
    lines = [
        "# CF4++ Affine Local-Flow Decomposition (LR-06F)",
        "",
        f"owner: {r['owner']} · claim_tier: {r['claim_tier']} · ticket: {r['ticket']}",
        f"grid: {r['grid']['n_per_axis']}^3, box {r['grid']['box_mpc']} Mpc, cell {r['grid']['cell_mpc']} Mpc "
        f"({r['grid']['frame']})",
        "",
        "## Affine fit vs sphere radius",
        "",
        "| R [Mpc] | N cells | bulk |B| [km/s] | expansion Theta [km/s/Mpc] | shear [km/s/Mpc] | vorticity [km/s/Mpc] |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in r["radius_sweep"]:
        lines.append(f"| {row['radius_mpc']:.0f} | {row['n_cells']} | {row['bulk_amplitude_kms']:.1f} | "
                     f"{row['expansion_kms_per_mpc']:.4f} | {row['shear_amplitude_kms_per_mpc']:.4f} | "
                     f"{row['vorticity_amplitude_kms_per_mpc']:.5f} |")
    b = r["bootstrap_at_150mpc"]
    inj = r["curl_injection_recovery"]
    lines += [
        "",
        "## Bootstrap at R=150 Mpc (lower bound, correlated cells)",
        "",
        f"- bulk |B| = {b['bulk_amplitude']['mean']:.1f} +/- {b['bulk_amplitude']['std']:.1f} km/s",
        f"- expansion Theta = {b['expansion']['mean']:.4f} +/- {b['expansion']['std']:.4f} km/s/Mpc",
        f"- shear = {b['shear_amplitude']['mean']:.4f} +/- {b['shear_amplitude']['std']:.4f} km/s/Mpc",
        f"- vorticity = {b['vorticity_amplitude']['mean']:.5f} +/- {b['vorticity_amplitude']['std']:.5f} km/s/Mpc",
        "",
        "## Curl-injection recovery (estimator validation)",
        "",
        f"- injected omega = {inj['omega_injected']} km/s/Mpc",
        f"- recovered omega = {[round(x,4) for x in inj['omega_recovered']]} km/s/Mpc",
        f"- abs error = {inj['abs_error']:.3e}, rel error = {inj['rel_error']:.3e}",
        "",
        f"## Cross-reconstruction: {r['cross_reconstruction']['status']}",
        "",
        r["cross_reconstruction"]["detail"],
        "",
        "## Caveats",
        "",
        *[f"- {c}" for c in r["caveats"]],
        "",
    ]
    return "\n".join(lines)


def _figure_manifest(r: dict) -> dict:
    w = _git_state()
    return {
        "artifact_id": "obsstat.cf4_affine_flow.figure",
        "artifact_path": f"figures/observed_current/{FIG.name}",
        "owner": "OBSSTAT", "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only", "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned", "allowed_use": "paper_appendix",
        "transfer_source": "none", "sky_support_status": "cf4_reconstruction_grid",
        "null_mock_status": "bootstrap_over_correlated_reconstruction_cells",
        "family_identification": False, "native_solver_result": False,
        "ticket": "LR-06F", "generating_command": "python scripts/make_cf4_affine_flow.py",
        "git_commit_or_worktree_state": w, "git_commit": w.split("+")[0], "code_version": w,
        "schema_version": "obsstat.cf4_affine_flow_figure.v1",
        "caption_policy": [
            "must_state_diagnostic_only",
            "must_not_use_for_family_identification_or_family_selection",
            "must_state_no_native_low_ell_solver_output",
        ],
        "promotion_blockers": [
            "native_solver_validation_absent",
            "native_morphology_atlas_absent",
            "family_identification_blocked_pre_native_atlas",
        ],
        "caveats": r["caveats"],
        "input_hashes": r["input_hashes"],
    }


def _write_figure(r: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = r["radius_sweep"]
    R = [x["radius_mpc"] for x in rows]
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.8))
    axs[0].plot(R, [x["bulk_amplitude_kms"] for x in rows], "o-", color="#2563eb")
    axs[0].set_xlabel("sphere radius [Mpc]"); axs[0].set_ylabel("bulk |B| [km/s]")
    axs[0].set_title("LR-06F: CF4++ bulk flow vs radius")
    axs[1].plot(R, [x["shear_amplitude_kms_per_mpc"] for x in rows], "s-", color="#16a34a", label="shear")
    axs[1].plot(R, [x["vorticity_amplitude_kms_per_mpc"] for x in rows], "d--", color="#ea580c", label="vorticity")
    axs[1].plot(R, [abs(x["expansion_kms_per_mpc"]) for x in rows], "^:", color="#7c3aed", label="|expansion|")
    axs[1].set_xlabel("sphere radius [Mpc]"); axs[1].set_ylabel("km/s/Mpc")
    axs[1].set_title("velocity-gradient parts"); axs[1].legend(fontsize=8)
    fig.tight_layout(); FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, dpi=140); plt.close(fig)
    (FIG.with_suffix(".manifest.json")).write_text(json.dumps(_figure_manifest(r), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if not GRID.exists():
        print(f"BLOCKED_MISSING_FIELD_REALIZATIONS: {GRID} not present")
        return 1
    cmd = "python scripts/make_cf4_affine_flow.py"
    report = build_report(generating_command=cmd)
    if args.check:
        ok = REPORT_JSON.exists() and json.loads(REPORT_JSON.read_text())["radius_sweep"][0]["n_cells"] == report["radius_sweep"][0]["n_cells"]
        print("up to date" if ok else "stale")
        return 0 if ok else 1
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    _write_figure(report)
    print(f"wrote {REPORT_JSON.relative_to(REPO_ROOT)} / {REPORT_MD.relative_to(REPO_ROOT)} / {FIG.relative_to(REPO_ROOT)}")
    print(f"bulk@150={report['bootstrap_at_150mpc']['bulk_amplitude']['mean']:.1f} km/s; "
          f"curl-inj rel_err={report['curl_injection_recovery']['rel_error']:.2e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
