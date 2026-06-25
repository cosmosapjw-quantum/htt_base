#!/usr/bin/env python3
"""LR-06D: CF4 hierarchical bulk-flow likelihood on the full group release.

Consumes the parsed CF4-full group catalog
(`workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz`, VizieR J/ApJ/944/94 table4)
and computes the minimum-variance bulk flow B (amplitude + Galactic apex) in
depth windows, with a fitted intrinsic dispersion sigma_star, a forward-mock
coverage calibration, and a sky/row-coverage gate.

Claim boundary (per the ticket): no global-tilt claim from CF4 distance data
alone; this is a kinematic descriptor with selection + observer-frame caveats.
Diagnostic-only OBSSTAT result.
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

from obsstat.bulkflow_mle import (  # noqa: E402
    estimate_bulk_flow, velocity_error, fit_sigma_star, forward_mock_coverage,
)

CAT = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
DEPTHS = [60.0, 100.0, 150.0, 200.0, 300.0]
REPORT_JSON = REPO_ROOT / "docs/generated/cf4_bulkflow_likelihood_report.json"
REPORT_MD = REPO_ROOT / "docs/generated/cf4_bulkflow_likelihood_report.md"
FIG = REPO_ROOT / "figures/observed_current/fig_observed_cf4_bulkflow_likelihood.png"


def _git_state() -> str:
    try:
        c = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, text=True).strip()
        d = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True).stdout.strip()
        return f"{c}+dirty" if d else c
    except Exception:
        return "unknown"


def _sg_cart_to_galactic(vec: np.ndarray) -> tuple[float, float]:
    from astropy.coordinates import SkyCoord, CartesianRepresentation
    import astropy.units as u
    rep = CartesianRepresentation(vec[0] * u.one, vec[1] * u.one, vec[2] * u.one)
    g = SkyCoord(rep, frame="supergalactic").galactic
    return float(g.l.deg), float(g.b.deg)


def _sky_fraction(n_unit: np.ndarray, nside: int = 4) -> float:
    try:
        import healpy as hp
        pix = hp.vec2pix(nside, n_unit[:, 0], n_unit[:, 1], n_unit[:, 2])
        return float(len(np.unique(pix)) / hp.nside2npix(nside))
    except Exception:
        return float("nan")


def build_report(*, generating_command: str) -> dict:
    data = np.load(CAT)
    sgx, sgy, sgz = data["SGX"], data["SGY"], data["SGZ"]
    dist, vpec, e_dm, v3k = data["Dist"], data["Vpec"], data["e_DMzp"], data["V3k"]
    pos = np.column_stack([sgx, sgy, sgz]).astype(float)
    r = np.linalg.norm(pos, axis=1)
    good = np.isfinite(r) & (r > 1.0) & np.isfinite(vpec) & np.isfinite(e_dm) & np.isfinite(dist)
    pos, r, dist, vpec, e_dm, v3k = pos[good], r[good], dist[good], vpec[good], e_dm[good], v3k[good]
    n_unit = pos / r[:, None]
    sigma_meas = velocity_error(e_dm, v3k)

    rows = []
    for dmax in DEPTHS:
        m = dist <= dmax
        if m.sum() < 50:
            rows.append({"depth_mpc": dmax, "status": "BLOCKED_INSUFFICIENT_GROUPS", "n_groups": int(m.sum())})
            continue
        nu, vp, sm = n_unit[m], vpec[m], sigma_meas[m]
        ss = fit_sigma_star(nu, vp, sm)
        bf = estimate_bulk_flow(nu, vp, sm, sigma_star=ss)
        gl, gb = _sg_cart_to_galactic(bf.vector)
        cov = forward_mock_coverage(nu, sm, bf.vector, ss, n_mock=300, seed=7)
        rows.append({
            "depth_mpc": dmax, "status": "OK", "n_groups": int(m.sum()),
            "sky_fraction_nside4": round(_sky_fraction(nu), 3),
            "sigma_star_kms": round(ss, 1),
            "bulk_amplitude_kms": round(bf.amplitude, 1),
            "bulk_amplitude_error_kms": round(bf.amplitude_error, 1),
            "apex_galactic_l_deg": round(gl, 1), "apex_galactic_b_deg": round(gb, 1),
            "forward_mock_coverage_1sigma": round(cov["one_sigma_coverage"], 3),
            "forward_mock_recovered_kms": round(cov["recovered_mean_kms"], 1),
        })
    return {
        "artifact_id": "obsstat.cf4_bulkflow_likelihood",
        "owner": "OBSSTAT", "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only", "transfer_source": "none",
        "sky_support_status": "cf4_full_group_catalog", "ticket": "LR-06D",
        "null_mock_status": "forward_mock_coverage_calibrated",
        "generating_command": generating_command,
        "git_commit_or_worktree_state": _git_state(),
        "input_hashes": [f"workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz:sha256:"
                         f"{hashlib.sha256(CAT.read_bytes()).hexdigest()}"],
        "release": "Cosmicflows-4 (Tully+ 2023) VizieR J/ApJ/944/94 table4",
        "n_groups_total": int(good.sum()),
        "depth_windows": rows,
        "observer_frame_note": "peculiar velocities use the catalog ramp Vpec (V3k cosmological frame "
                               "for the error scaling); a full Vh/Vls/V3k frame ablation is a follow-up.",
        "caveats": [
            "Minimum-variance bulk flow on the CF4 group peculiar velocities; diagnostic-only.",
            "sigma_star is fitted to reduced chi^2 ~ 1; covariance is the inverse Fisher matrix.",
            "Forward-mock coverage uses the real geometry + errors with the recovered B as the injected truth.",
            "No global-tilt or Bianchi-geometry claim is made from CF4 distances alone.",
            "Selection and Malmquist/inhomogeneous-sampling biases are not fully forward-modelled here.",
        ],
    }


def render_md(r: dict) -> str:
    lines = [
        "# CF4 Bulk-Flow Likelihood on the Full Group Release (LR-06D)",
        "",
        f"owner: {r['owner']} · claim_tier: {r['claim_tier']} · ticket: {r['ticket']}",
        f"release: {r['release']} · {r['n_groups_total']} usable groups",
        "",
        "| depth [Mpc] | N | sky frac | sigma_star | |B| [km/s] | apex (l,b) | mock coverage |",
        "| --- | ---: | ---: | ---: | --- | --- | ---: |",
    ]
    for row in r["depth_windows"]:
        if row["status"] != "OK":
            lines.append(f"| {row['depth_mpc']:.0f} | {row['n_groups']} | {row['status']} | | | | |")
            continue
        lines.append(
            f"| {row['depth_mpc']:.0f} | {row['n_groups']} | {row['sky_fraction_nside4']:.2f} | "
            f"{row['sigma_star_kms']:.0f} | {row['bulk_amplitude_kms']:.0f} +/- {row['bulk_amplitude_error_kms']:.0f} | "
            f"({row['apex_galactic_l_deg']:.0f}, {row['apex_galactic_b_deg']:.0f}) | "
            f"{row['forward_mock_coverage_1sigma']:.2f} |")
    lines += ["", f"Observer-frame note: {r['observer_frame_note']}", "", "## Caveats", "",
              *[f"- {c}" for c in r["caveats"]], ""]
    return "\n".join(lines)


def _figure_manifest(r: dict) -> dict:
    w = _git_state()
    return {
        "artifact_id": "obsstat.cf4_bulkflow_likelihood.figure",
        "artifact_path": f"figures/observed_current/{FIG.name}",
        "owner": "OBSSTAT", "implementation_scope": "obsstat",
        "claim_tier": "diagnostic_only", "production_status": "diagnostic_only",
        "artifact_mode": "paper_appendix_conditioned", "allowed_use": "paper_appendix",
        "transfer_source": "none", "sky_support_status": "cf4_full_group_catalog",
        "null_mock_status": "forward_mock_coverage_calibrated",
        "family_identification": False, "native_solver_result": False,
        "ticket": "LR-06D", "generating_command": "python scripts/make_cf4_bulkflow_likelihood.py",
        "git_commit_or_worktree_state": w, "git_commit": w.split("+")[0], "code_version": w,
        "schema_version": "obsstat.cf4_bulkflow_likelihood_figure.v1",
        "caveats": r["caveats"], "input_hashes": r["input_hashes"],
    }


def _write_figure(r: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ok = [x for x in r["depth_windows"] if x["status"] == "OK"]
    d = [x["depth_mpc"] for x in ok]
    amp = [x["bulk_amplitude_kms"] for x in ok]
    err = [x["bulk_amplitude_error_kms"] for x in ok]
    fig, ax = plt.subplots(figsize=(5.6, 4.0))
    ax.errorbar(d, amp, yerr=err, fmt="o-", color="#2563eb", capsize=3)
    ax.set_xlabel("depth window d < R [Mpc]"); ax.set_ylabel("bulk flow |B| [km/s]")
    ax.set_title("LR-06D: CF4 group bulk flow vs depth\n(minimum-variance, sigma_star-fitted)")
    fig.tight_layout(); FIG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG, dpi=140); plt.close(fig)
    FIG.with_suffix(".manifest.json").write_text(json.dumps(_figure_manifest(r), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if not CAT.exists():
        print("BLOCKED_MISSING_FULL_RELEASE_BINDING: run dl_pipeline stage cf4_full first")
        return 1
    report = build_report(generating_command="python scripts/make_cf4_bulkflow_likelihood.py")
    if args.check:
        ok = REPORT_JSON.exists()
        print("up to date" if ok else "stale"); return 0 if ok else 1
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    _write_figure(report)
    print(f"wrote {REPORT_JSON.relative_to(REPO_ROOT)} / figure")
    for row in report["depth_windows"]:
        if row["status"] == "OK":
            print(f"  d<{row['depth_mpc']:.0f}: |B|={row['bulk_amplitude_kms']:.0f}+/-{row['bulk_amplitude_error_kms']:.0f} "
                  f"km/s @({row['apex_galactic_l_deg']:.0f},{row['apex_galactic_b_deg']:.0f}) cov={row['forward_mock_coverage_1sigma']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
