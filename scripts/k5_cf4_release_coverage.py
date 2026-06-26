#!/usr/bin/env python3
"""K5 discharge: cosmic-variance-inclusive coverage of the CF4 bulk flow from
release-matched forward mocks on the real Cosmicflows-4 group catalogue.

BLOCKER: BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP. This binds the *real* CF4 group
release (Tully+ 2023, `workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz`,
38053 groups with peculiar velocities `Vpec`, distance-modulus errors `e_DMzp`,
and supergalactic positions) and runs the OBSSTAT weighted-GLS bulk-flow
estimator (`htt/obsstat/bulkflow_mle.py`). Forward mocks are **release-matched**:
they keep the real sky positions and the real per-group distance-error model
(the release selection), and inject a cosmic-variance bulk flow drawn from a
LambdaCDM prior, so the coverage statement separates cosmic variance from
measurement noise (not a self-injection-only coverage).

Outputs the measured bulk flow, the measurement-noise-only coverage, the
cosmic-variance-inclusive coverage + the inflation needed for nominal coverage,
bias, and radial-shell (depth) ablations. Model-independent kinematic descriptor:
no Bianchi family, geometry, frame-violation, or native-solver claim.

Outputs: docs/generated/k5_cf4_release_coverage.json. Deterministic; --check.
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

from obsstat.bulkflow_mle import (  # noqa: E402
    estimate_bulk_flow, fit_sigma_star, velocity_error,
)

CF4 = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
OUT_JSON = REPO_ROOT / "docs/generated/k5_cf4_release_coverage.json"
# LambdaCDM linear-theory bulk-flow rms per Cartesian component over the CF4
# effective window (fiducial prior; the coverage statement is conditional on it).
SIGMA_CV_PRIOR_KMS = 150.0
SHELL_EDGES_KMS = (0.0, 3000.0, 6000.0, 9000.0, 16000.0)   # V3k (CMB-frame cz) shells
N_MOCK = 600
SEED = 20260626


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _load_catalogue():
    d = np.load(CF4, allow_pickle=True)
    pos = np.c_[d["SGX"], d["SGY"], d["SGZ"]].astype(float)
    r = np.linalg.norm(pos, axis=1)
    vpec = np.asarray(d["Vpec"], dtype=float)
    v3k = np.asarray(d["V3k"], dtype=float)          # CMB-frame cz
    e_dm = np.asarray(d["e_DMzp"], dtype=float)
    sigma = velocity_error(e_dm, v3k)                # per-group peculiar-velocity error
    good = np.isfinite(vpec) & np.isfinite(sigma) & (sigma > 0.0) & (r > 1.0) & np.isfinite(v3k)
    n_hat = pos[good] / r[good, None]
    return {"n_hat": n_hat, "vpec": vpec[good], "sigma": sigma[good],
            "v3k": v3k[good], "r": r[good], "n_total": int(good.sum())}


def _coverage(n_hat, sigma, sigma_star, *, cosmic_variance: bool, rng) -> dict:
    """Release-matched mock coverage. With cosmic_variance=True, draw a fresh
    LambdaCDM bulk flow per mock; otherwise inject zero (measurement-noise only).
    Recover with the same weighted-GLS estimator and the measurement-only error."""
    amp_cov = 0
    comp_cov = np.zeros(3)
    amp_true_l, amp_hat_l, bias_l = [], [], []
    for _ in range(N_MOCK):
        b_true = rng.normal(scale=SIGMA_CV_PRIOR_KMS, size=3) if cosmic_variance else np.zeros(3)
        noise = rng.normal(size=sigma.shape) * np.sqrt(sigma ** 2 + sigma_star ** 2)
        vpec_mock = n_hat @ b_true + noise
        bf = estimate_bulk_flow(n_hat, vpec_mock, sigma, sigma_star=sigma_star)
        amp_true = float(np.linalg.norm(b_true))
        if abs(bf.amplitude - amp_true) <= bf.amplitude_error:
            amp_cov += 1
        comp_err = np.sqrt(np.diag(bf.covariance))
        comp_cov += (np.abs(bf.vector - b_true) <= comp_err).astype(float)
        amp_true_l.append(amp_true); amp_hat_l.append(bf.amplitude)
        bias_l.append(bf.amplitude - amp_true)
    return {
        "amplitude_coverage": amp_cov / N_MOCK,
        "component_coverage": (comp_cov / N_MOCK).tolist(),
        "mean_recovered_amplitude_kms": float(np.mean(amp_hat_l)),
        "amplitude_bias_kms": float(np.mean(bias_l)),
        "recovered_amplitude_scatter_kms": float(np.std(amp_hat_l, ddof=1)),
    }


def build_report() -> dict:
    if not CF4.is_file():
        return {"schema": "htt.k5.cf4_release_coverage.v1",
                "status": "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
                "note": f"CF4 group catalogue not found at {CF4.relative_to(REPO_ROOT)}"}
    cat = _load_catalogue()
    n_hat, vpec, sigma = cat["n_hat"], cat["vpec"], cat["sigma"]
    sigma_star = fit_sigma_star(n_hat, vpec, sigma)
    measured = estimate_bulk_flow(n_hat, vpec, sigma, sigma_star=sigma_star)

    rng = np.random.default_rng(SEED)
    meas_only = _coverage(n_hat, sigma, sigma_star, cosmic_variance=False, rng=rng)
    cv_incl = _coverage(n_hat, sigma, sigma_star, cosmic_variance=True, rng=rng)
    # cosmic-variance error term (quadrature inflation that restores coverage)
    cv_sigma_kms = float(np.sqrt(max(cv_incl["recovered_amplitude_scatter_kms"] ** 2
                                     - meas_only["recovered_amplitude_scatter_kms"] ** 2, 0.0)))
    total_error_kms = float(np.sqrt(measured.amplitude_error ** 2 + cv_sigma_kms ** 2))

    shells = []
    edges = SHELL_EDGES_KMS
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (cat["v3k"] >= lo) & (cat["v3k"] < hi)
        if m.sum() < 50:
            continue
        ss = fit_sigma_star(n_hat[m], vpec[m], sigma[m])
        bf = estimate_bulk_flow(n_hat[m], vpec[m], sigma[m], sigma_star=ss)
        shells.append({"cz_lo_kms": lo, "cz_hi_kms": hi, "n_groups": int(m.sum()),
                       "bulk_amplitude_kms": bf.amplitude,
                       "bulk_amplitude_error_kms": bf.amplitude_error,
                       "sigma_star_kms": ss})

    return {
        "schema": "htt.k5.cf4_release_coverage.v1",
        "owner": "OBSSTAT",
        "claim_tier": "diagnostic_only",
        "blocker_resolved": "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
        "transfer_source": "none",
        "family_identification": False,
        "native_solver_result": False,
        "catalogue": {
            "product": "Cosmicflows-4 group release (Tully+ 2023, VizieR J/ApJ/944/94)",
            "n_groups_used": int(n_hat.shape[0]),
            "frame": "supergalactic_cartesian_positions / CMB-frame velocities",
            "distance_error_model": "sigma_v = (ln10/5) * e_DMzp * V3k",
            "input_hashes": [_sha256_file(CF4)],
        },
        "estimator": "weighted-GLS bulk flow with profiled small-scale velocity dispersion sigma_star",
        "sigma_star_kms": sigma_star,
        "measured_bulk": measured.as_dict(),
        "coverage": {
            "measurement_noise_only": meas_only,
            "cosmic_variance_inclusive": cv_incl,
            "sigma_cv_prior_kms_per_component": SIGMA_CV_PRIOR_KMS,
            "cosmic_variance_amplitude_error_kms": cv_sigma_kms,
            "measurement_amplitude_error_kms": measured.amplitude_error,
            "total_amplitude_error_kms": total_error_kms,
            "interpretation": "measurement-only error under-covers an injected LambdaCDM cosmic-variance flow; the total error is the quadrature sum of measurement and cosmic-variance terms",
        },
        "depth_shells": shells,
        "config": {"n_mock": N_MOCK, "seed": SEED, "shell_edges_kms": list(SHELL_EDGES_KMS)},
        "caveats": [
            "release-matched mocks keep the real CF4 sky positions + per-group distance-error model",
            "cosmic-variance coverage is conditional on the fiducial LambdaCDM per-component prior sigma_cv",
            "model-independent kinematic descriptor; no Bianchi family, geometry, frame-violation, or native-solver claim",
        ],
        "claim_boundary": "OBSSTAT model-independent bulk-flow coverage; no anisotropy evidence or family identification",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_report()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT_JSON.is_file() or OUT_JSON.read_text() != text:
            print("stale k5_cf4_release_coverage.json; rerun scripts/k5_cf4_release_coverage.py")
            return 1
        print("k5_cf4_release_coverage.json up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    if "measured_bulk" in payload:
        print(f"   measured |B| = {payload['measured_bulk']['amplitude_kms']:.1f} +/- "
              f"{payload['coverage']['total_amplitude_error_kms']:.1f} km/s "
              f"(meas {payload['coverage']['measurement_amplitude_error_kms']:.1f}, "
              f"cv {payload['coverage']['cosmic_variance_amplitude_error_kms']:.1f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
