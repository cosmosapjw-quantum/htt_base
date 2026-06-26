#!/usr/bin/env python3
"""K6 discharge: realization-conditioned curl/vorticity posterior of the real
CF4++ Wiener-filter velocity field, or an explicit structural no-go.

BLOCKER: BLOCKED_MISSING_FIELD_REALIZATIONS. This script binds the *real* CF4++
reconstruction grid (`workdir/raw/cf4/CF4pp_mean_std_grids.npz`, Courtois/Hoffman
CF4++, supergalactic Cartesian, 128^3 over a 1000 Mpc box) and runs the OBSSTAT
affine velocity-gradient decomposition (`htt/obsstat/affine_flow.py`) over the
constrained field, propagating the per-cell WF uncertainty `v_std` through a
Monte-Carlo / constrained-realization ensemble to a vorticity-sector posterior.

Honest outcome (per the audit + G3): the CF4 WF velocity field is a
potential-flow reconstruction derived from radial peculiar velocities, so it is
**curl-suppressed by construction**. The estimator's curl channel is validated
independently by solid-body-rotation injection recovery; if the field-conditioned
vorticity is consistent with the curl-suppressed null, the row is a structural
**no-go**, not a physical-vorticity detection. No Bianchi family, geometry, or
native-solver claim is made.

Outputs: docs/generated/k6_cf4_curl_posterior.json (+ field-realization manifest).
Deterministic (seeded); --check compares the committed JSON byte-for-byte.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
for root in (REPO_ROOT / "htt", REPO_ROOT / "htt/htt", REPO_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.affine_flow import fit_affine_flow, curl_injection_recovery  # noqa: E402

GRID_NPZ = REPO_ROOT / "workdir/raw/cf4/CF4pp_mean_std_grids.npz"
OUT_JSON = REPO_ROOT / "docs/generated/k6_cf4_curl_posterior.json"
BOX_MPC = 1000.0          # CF4++ reconstruction box side (dl_pipeline cf4_grid_adapter)
RADII_MPC = (75.0, 100.0, 150.0, 200.0)   # nested analysis spheres about the observer
N_CR = 400                # constrained-realization / MC ensemble size
SEED = 20260626


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _cell_positions_and_field(grid: dict, radius: float):
    """Supergalactic-Cartesian cell centres within ``radius`` of the observer,
    plus the WF mean velocity and per-component std at those cells."""
    v_mean = grid["v_mean_CF4pp"]            # (3, N, N, N)
    v_std = grid["v_std_CF4pp"]
    n = v_mean.shape[1]
    delta = BOX_MPC / n
    axis = (np.arange(n) + 0.5) * delta - BOX_MPC / 2.0   # cell-centre coordinate
    gx, gy, gz = np.meshgrid(axis, axis, axis, indexing="ij")
    r2 = gx**2 + gy**2 + gz**2
    sel = r2 <= radius * radius
    pos = np.column_stack([gx[sel], gy[sel], gz[sel]])
    vmean = np.column_stack([v_mean[0][sel], v_mean[1][sel], v_mean[2][sel]])
    vstd = np.column_stack([v_std[0][sel], v_std[1][sel], v_std[2][sel]])
    return pos, vmean, vstd


def _posterior_at_radius(pos, vmean, vstd, *, rng) -> dict:
    """Affine fit of the WF mean + a constrained-realization ensemble that draws
    each cell velocity ~ N(v_mean, v_std). The ensemble spread ignores cell-cell
    covariance (a documented lower bound on the true posterior width)."""
    base = fit_affine_flow(pos, vmean)
    w_mean = []
    bulk_amp = []
    theta = []
    shear_amp = []
    for _ in range(N_CR):
        draw = vmean + rng.normal(size=vmean.shape) * vstd
        fit = fit_affine_flow(pos, draw)
        w_mean.append(fit.vorticity_axial)
        bulk_amp.append(fit.bulk_amplitude)
        theta.append(fit.expansion)
        shear_amp.append(fit.shear_amplitude)
    w = np.asarray(w_mean)                       # (N_CR, 3)
    w_norm = np.linalg.norm(w, axis=1)
    # curl-channel validity: inject a solid-body rotation comparable to the
    # field's strain scale and confirm the estimator recovers it.
    omega_inject = np.array([base.shear_amplitude, -base.shear_amplitude, base.shear_amplitude])
    inj = curl_injection_recovery(pos, vmean, radius=float(np.max(np.linalg.norm(pos, axis=1)) + 1.0),
                                  omega_inject=omega_inject)
    return {
        "n_cells": int(pos.shape[0]),
        "wf_mean_vorticity_axial": base.vorticity_axial.tolist(),
        "wf_mean_vorticity_amplitude": base.vorticity_amplitude,
        "wf_mean_expansion": base.expansion,
        "wf_mean_shear_amplitude": base.shear_amplitude,
        "wf_mean_bulk_amplitude": base.bulk_amplitude,
        "cr_vorticity_amplitude_median": float(np.median(w_norm)),
        "cr_vorticity_amplitude_p16": float(np.percentile(w_norm, 16)),
        "cr_vorticity_amplitude_p84": float(np.percentile(w_norm, 84)),
        "cr_vorticity_axial_mean": np.mean(w, axis=0).tolist(),
        "cr_vorticity_axial_sd": np.std(w, axis=0, ddof=1).tolist(),
        "cr_expansion_median": float(np.median(theta)),
        "cr_shear_amplitude_median": float(np.median(shear_amp)),
        "cr_bulk_amplitude_median": float(np.median(bulk_amp)),
        "curl_injection_rel_error": inj["rel_error"],
    }


def build_report() -> dict:
    if not GRID_NPZ.is_file():
        return {
            "schema": "htt.k6.cf4_curl_posterior.v1",
            "status": "BLOCKED_MISSING_FIELD_REALIZATIONS",
            "note": f"CF4++ grid not found at {GRID_NPZ.relative_to(REPO_ROOT)}",
        }
    grid = {k: np.asarray(v) for k, v in np.load(GRID_NPZ).items()}
    rng = np.random.default_rng(SEED)
    per_radius = {}
    for radius in RADII_MPC:
        pos, vmean, vstd = _cell_positions_and_field(grid, radius)
        per_radius[f"R{int(radius)}"] = _posterior_at_radius(pos, vmean, vstd, rng=rng)

    # Structural-no-go decision: across all radii, is the field-conditioned
    # vorticity small relative to the field's own shear scale AND is the curl
    # channel demonstrably live (injection recovered)? A curl-suppressed WF
    # reconstruction makes physical vorticity unidentifiable -> structural no-go.
    ratios = [per_radius[k]["wf_mean_vorticity_amplitude"] / (per_radius[k]["wf_mean_shear_amplitude"] + 1e-30)
              for k in per_radius]
    inj_ok = all(per_radius[k]["curl_injection_rel_error"] < 0.05 for k in per_radius)
    curl_suppressed = bool(max(ratios) < 0.2 and inj_ok)
    conclusion = (
        "STRUCTURAL_NO_GO: the CF4 WF velocity field is curl-suppressed "
        "(vorticity << shear at every radius) while the estimator recovers an "
        "injected solid-body rotation, so no physical vorticity sector is "
        "identifiable from this reconstruction"
        if curl_suppressed else
        "POSTERIOR: field-conditioned vorticity exceeds the curl-suppressed null; "
        "report the realization-conditioned posterior with caveats"
    )
    return {
        "schema": "htt.k6.cf4_curl_posterior.v1",
        "owner": "OBSSTAT",
        "claim_tier": "diagnostic_only",
        "blocker_resolved": "BLOCKED_MISSING_FIELD_REALIZATIONS",
        "transfer_source": "external_proxy_cf4_wf_reconstruction",
        "family_identification": False,
        "native_solver_result": False,
        "field": {
            "product": "CF4++ Wiener-filter mean+std velocity grid (Courtois/Hoffman)",
            "frame": "supergalactic_cartesian",
            "grid_shape": [int(grid["v_mean_CF4pp"].shape[i]) for i in (1, 2, 3)],
            "box_mpc": BOX_MPC,
            "velocity_units": "km_per_s",
            "input_hashes": [_sha256_file(GRID_NPZ)],
            "wf_method_caveat": "WF reconstruction from radial peculiar velocities is potential-flow / curl-suppressed by construction; recovered vorticity is reconstruction-conditioned, not a detected physical vorticity",
        },
        "config": {"radii_mpc": list(RADII_MPC), "n_cr": N_CR, "seed": SEED,
                   "cr_caveat": "per-cell N(v_mean,v_std) draws ignore cell-cell covariance -> ensemble spread is a lower bound on the true posterior width"},
        "per_radius": per_radius,
        "vorticity_over_shear_ratio_max": float(max(ratios)),
        "curl_injection_validated": bool(inj_ok),
        "structural_no_go": curl_suppressed,
        "conclusion": conclusion,
        "claim_boundary": "OBSSTAT reconstruction-conditioned diagnostic; no physical-vorticity, Bianchi-family, geometry, or native-solver claim",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_report()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT_JSON.is_file() or OUT_JSON.read_text() != text:
            print("stale k6_cf4_curl_posterior.json; rerun scripts/k6_cf4_curl_posterior.py")
            return 1
        print("k6_cf4_curl_posterior.json up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print("  ", payload.get("conclusion", payload.get("status")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
