"""Observed Gaia angular-pair response under the frozen R25 working contract.

One source-row traversal forms pair means. All output coordinates are responses,
not estimates of physical field coefficients.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CONTRACT = HERE.parent / "R25-GAIA-PAIR-SEPARATION_INPUT.json"
SOURCE = ROOT / "docs/observational_reboot_20261014/results/gaia_frame_v1/qualified_rows.npz"
BINS = np.array([0, .5, 1, 2, 5, 10, 30, 60, 120, 180.], dtype=float)
STF = np.array([
    [[1, 0, 0], [0, -1, 0], [0, 0, 0]],
    [[-1, 0, 0], [0, -1, 0], [0, 0, 2]],
    [[0, 1, 0], [1, 0, 0], [0, 0, 0]],
    [[0, 0, 1], [0, 0, 0], [1, 0, 0]],
    [[0, 0, 0], [0, 0, 1], [0, 1, 0]],
], dtype=float) / np.array([np.sqrt(2), np.sqrt(6), np.sqrt(2), np.sqrt(2), np.sqrt(2)])[:, None, None]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def geometry(ra, dec):
    a, d = np.deg2rad(ra), np.deg2rad(dec)
    ca, sa, cd, sd = np.cos(a), np.sin(a), np.cos(d), np.sin(d)
    n = np.stack((cd * ca, cd * sa, sd), axis=-1)
    ea = np.stack((-sa, ca, np.zeros_like(a)), axis=-1)
    ed = np.stack((-sd * ca, -sd * sa, cd), axis=-1)
    return n, np.stack((ea, ed), axis=-1)


def designs(n, E):
    count = len(n)
    X = np.empty((count, 2, 13))
    Et = np.swapaxes(E, 1, 2)
    X[:, :, :3] = Et
    Sn = np.einsum("kij,nj->nki", STF, n)
    X[:, :, 3:8] = np.einsum("nac,nkc->nak", Et, Sn)
    X[:, :, 8:13] = np.einsum("nac,nkc->nak", Et, np.cross(n[:, None, :], Sn))
    B = np.einsum("nac,nkc->nak", Et, np.cross(np.eye(3)[None, :, :], n[:, None, :]))
    return X, B


def pair_terms(n, E, X, y, i, js):
    nj, ni = n[js], n[i]
    li = nj @ E[i]
    lj = np.einsum("nka,k->na", E[js], ni)
    a = li @ X[i] + np.einsum("na,nak->nk", lj, X[js])
    kappa = li @ y[i] + np.einsum("na,na->n", lj, y[js])
    c = np.einsum("nk,k->n", nj, ni)
    s = np.linalg.norm(np.cross(ni, nj), axis=1)
    theta = np.arctan2(s, c)
    bins = np.searchsorted(np.deg2rad(BINS), theta, side="right") - 1
    bins = np.minimum(bins, len(BINS) - 2)
    return li, lj, a, kappa, c, theta, bins


def accumulate(n, E, X, y, *, chunk_max=32768, pair_list=None):
    """Return all nine 13-coordinate pair means and their source operators.

    pair_list is only for small independent controls; production visits all i<j.
    """
    count = len(n)
    assert 0 < chunk_max <= 32768
    nb = len(BINS) - 1
    H = np.zeros((nb, 13, count * 2))
    D = np.zeros((nb, 13, 13))
    d = np.zeros((nb, 13))
    counts = np.zeros(nb, dtype=np.int64)
    touched = np.zeros((nb, count), dtype=bool)
    near = np.zeros(2, dtype=np.int64)
    if pair_list is None:
        groups = ((i, np.arange(i + 1, count, dtype=np.int64)) for i in range(count - 1))
    else:
        groups = ((i, np.asarray(js, dtype=np.int64)) for i, js in pair_list)
    for i, all_js in groups:
        for off in range(0, len(all_js), chunk_max):
            js = all_js[off:off + chunk_max]
            li, lj, a, k, c, theta, bins = pair_terms(n, E, X, y, i, js)
            near[0] += np.count_nonzero((theta <= 1e-12) & (c >= 0))
            near[1] += np.count_nonzero((np.pi - theta <= 1e-12) & (c < 0))
            for b in np.unique(bins):
                take = bins == b
                j = js[take]
                ab, lb_i, lb_j, kb = a[take], li[take], lj[take], k[take]
                counts[b] += len(j)
                touched[b, i] = True
                touched[b, j] = True
                d[b] += ab.T @ kb
                D[b] += ab.T @ ab
                H[b, :, 2*i:2*i+2] += ab.T @ lb_i
                if pair_list is None:
                    H[b, :, 2*j] += ab * lb_j[:, 0, None]
                    H[b, :, 2*j+1] += ab * lb_j[:, 1, None]
                else:
                    np.add.at(H[b].T, 2*j, ab * lb_j[:, 0, None])
                    np.add.at(H[b].T, 2*j+1, ab * lb_j[:, 1, None])
    nz = counts > 0
    H[nz] /= counts[nz, None, None]
    D[nz] /= counts[nz, None, None]
    d[nz] /= counts[nz, None]
    return H, D, d, counts, touched.sum(axis=1), near


def covariance(H, C):
    flat = H.reshape(-1, H.shape[-1])
    h = flat.reshape(flat.shape[0], len(C), 2)
    weighted = np.einsum("ani,nij->anj", h, C, optimize=True)
    return weighted.reshape(flat.shape) @ flat.T


def inspect_reference(d, D, Cd):
    """Descriptive fixed-covariance projection; numerical ranks are diagnostics."""
    from scipy.stats import chi2
    dv, A = d.reshape(-1), D.reshape(-1, 13)
    eigenvalues, U = np.linalg.eigh((Cd + Cd.T) / 2)
    top = max(float(np.max(eigenvalues)), 0.0)
    thresholds = [1e-8, 1e-10, 1e-12]
    rank_diagnostics = {str(t): int(np.count_nonzero(eigenvalues > t * top)) for t in thresholds}
    retain = eigenvalues > 1e-10 * top if top > 0 else np.zeros(len(eigenvalues), bool)
    r = int(np.count_nonzero(retain))
    W = U[:, retain].T / np.sqrt(eigenvalues[retain, None]) if r else np.empty((0, len(dv)))
    initial_white = W @ Cd @ W.T
    initial_wr = float(np.linalg.norm(initial_white - np.eye(r), ord=2)) if r else None
    # One y-independent correction of the already fixed covariance projection.
    # This is numerical whitening control, never a certified spectral bound.
    if r:
        W = (np.eye(r) - .5 * (initial_white - np.eye(r))) @ W
    z, M = W @ dv, W @ A
    white = W @ Cd @ W.T
    wr = float(np.linalg.norm(white - np.eye(r), ord=2)) if r else None
    recon = float(np.linalg.norm(Cd - (U * eigenvalues) @ U.T) / max(np.linalg.norm(Cd), 1.0))
    designs = {}
    projectors = {}
    for name, m in (("E1", M[:, :3]), ("full13", M)):
        left, sv, _ = np.linalg.svd(m, full_matrices=False)
        q = int(np.count_nonzero(sv > 1e-10 * sv[0])) if len(sv) and sv[0] else 0
        projector = left[:, :q] @ left[:, :q].T
        projectors[name] = projector
        fit = np.linalg.lstsq(m, z, rcond=1e-10)[0] if r else np.zeros(m.shape[1])
        profile = m @ fit
        original_profile = A[:, :m.shape[1]] @ fit
        designs[name] = {
            "singular_values": sv.tolist(), "fit_representative": fit.tolist(),
            "profile": profile.tolist(), "residual": (z-profile).tolist(),
            "unprojected_fit_profile": original_profile.reshape(9, 13).tolist(),
            "unprojected_residual_profile": (dv-original_profile).reshape(9, 13).tolist(),
            "T": float(np.sum((z-profile)**2)),
            "ranks_relative": {str(t): int(np.count_nonzero(sv > t * sv[0])) if len(sv) and sv[0] else 0 for t in thresholds},
            "image_certification": "UNAVAILABLE_NUMERICAL_THRESHOLD_ONLY",
        }
    e1, full = designs["E1"], designs["full13"]
    return {
        "covariance_eigenvalues": eigenvalues.tolist(), "covariance_eigenvectors": U.tolist(),
        "retained_indices": np.flatnonzero(retain).tolist(), "rank_diagnostics": rank_diagnostics,
        "discarded_mode_status": "POSITIVE_OR_AMBIGUOUS_UNCONSTRAINED; NO_EXACT_NULL_ASSERTION",
        "W_definition": "Rows u_k^T/sqrt(lambda_k), relative threshold 1e-10, then one y-independent Newton covariance correction",
        "W": W.tolist(), "initial_whitening_residual_spectral": initial_wr,
        "whitening_residual_spectral": wr, "covariance_reconstruction_relative": recon,
        "projector_diagnostics": {
            name: {"symmetry_max_abs": float(np.max(np.abs(P-P.T))),
                   "idempotence_spectral": float(np.linalg.norm(P@P-P, ord=2))}
            for name, P in projectors.items()
        },
        "E1_full_nesting_spectral": float(np.linalg.norm((np.eye(r)-projectors["full13"])@projectors["E1"], ord=2)) if r else None,
        "z": z.tolist(), "M": M.tolist(), "models": designs,
        "Delta_E1_minus_full": e1["T"] - full["T"],
        "tail_status": "TAIL_UNRESOLVED_INCOMPLETE_IMAGE_CERTIFICATION",
        "ordinary_reference_status": "NUMERICAL_WORKING_CHI_SQUARE_APPROXIMATION_ONLY",
        "projected_mean_ball": {
            "confidence": 0.95, "dimension": r,
            "status": "NUMERICAL_WORKING_CHI_SQUARE_APPROXIMATION_ONLY" if r else "ZERO_DIMENSION_UNDEFINED_INFERENCE",
            "center": z.tolist(), "radius_squared": float(chi2.ppf(.95, r)) if r else None,
            "reason": "Ordinary fixed Gaussian/C0 working reference only; no certified spectral bound or exact whitening; full coefficient fiber remains unconstrained",
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, required=True)
    args = ap.parse_args()
    t0 = time.monotonic()
    contract = json.loads(CONTRACT.read_text())
    expected = {Path(x["path"]).name: x["sha256"] for x in contract["inputs"]}
    if sha256(CONTRACT) != "620d92030d235ee6ed8fb5e6d7ff999f4777f7540abbcb1841c23af50e878d50":
        raise RuntimeError("contract identity drift")
    if sha256(SOURCE) != expected[SOURCE.name]:
        raise RuntimeError("source identity drift")
    with np.load(SOURCE) as a:
        source_id = a["source_id"].copy()
        ra, dec = a["ra"].copy(), a["dec"].copy()
        y, C = a["proper_motion"].copy() * 1000, a["covariance"].copy() * 1e6
        octant = a["octant"].copy()
    if len(source_id) != 4756 or len(np.unique(source_id)) != len(source_id):
        raise RuntimeError("source population mismatch")
    order = np.argsort(source_id)
    source_id, ra, dec, y, C, octant = [a[order] for a in (source_id, ra, dec, y, C, octant)]
    n, E = geometry(ra, dec)
    X, B = designs(n, E)
    print(json.dumps({"stage":"production_start", "seconds":time.monotonic()-t0, "sources":len(n), "pid":os.getpid()}), flush=True)
    H, D, d, counts, touched, near = accumulate(n, E, X, y)
    print(json.dumps({"stage":"production_end", "seconds":time.monotonic()-t0, "pairs":int(counts.sum())}), flush=True)
    # Commit full carrier first; downstream diagnostics never repeat pair traversal.
    args.raw.mkdir(parents=True, exist_ok=True)
    raw = args.raw / "full_carrier.npz"
    np.savez(raw, H=H, D=D, d=d, counts=counts, source_counts=touched, near_endpoints=near,
             source_id=source_id, ra=ra, dec=dec, octant=octant, n=n, E=E, X=X, B=B,
             y=y, C=C, bins_degrees=BINS, STF=STF)
    print(json.dumps({"stage":"raw_saved", "seconds":time.monotonic()-t0, "path":str(raw), "sha256":sha256(raw)}), flush=True)
    Cd = covariance(H, C)
    np.save(args.raw / "covariance.npy", Cd)
    flatH, flatD, flatd = H.reshape(117, -1), D.reshape(117, 13), d.reshape(117)
    checks = {
        "d_Hy_max_abs": float(np.max(np.abs(flatd-flatH @ y.reshape(-1)))),
        "D_HX_max_abs": float(np.max(np.abs(flatD-flatH @ X.reshape(-1, 13)))),
        "HB_max_abs": float(np.max(np.abs(flatH @ B.reshape(-1, 3)))),
        "covariance_symmetry_max_abs": float(np.max(np.abs(Cd-Cd.T))),
        "covariance_min_eigenvalue": float(np.linalg.eigvalsh((Cd+Cd.T)/2)[0]),
    }
    checks["normalized_accumulation_error"] = max(
        checks["d_Hy_max_abs"] / max(1, np.max(np.abs(flatd))),
        checks["D_HX_max_abs"] / max(1, np.max(np.abs(flatD))),
    )
    if counts.sum() != 11307390 or checks["normalized_accumulation_error"] > 1e-9 or checks["HB_max_abs"] > 1e-10:
        raise RuntimeError(f"frozen actual control failure: {checks}")
    ref = inspect_reference(d, D, Cd)
    result = {
        "task_id": contract["task_id"], "status":"DESCRIPTIVE_CONDITIONAL_CANDIDATE_PENDING_INDEPENDENT_REVIEW",
        "source_count":len(n), "pair_count":int(counts.sum()), "pair_counts_per_bin":counts.tolist(),
        "source_counts_per_bin":touched.tolist(), "near_endpoint_counts":near.tolist(),
        "units":{"d":"microarcsecond-equivalent/year times model-coordinate response", "H":"dimensionless pair/source response", "C_d":"squared response units"},
        "checks":checks, "reference":ref,
        "functional_bundle":{"x":"FULL_UNPROJECTED_TYPED_RESPONSE_SAVED", "F":"PROJECTED_WORKING_PROFILE_ONLY", "Pi":"FORMAL_WORKING_LAW_ONLY", "Q":"NO_PHYSICAL_MES_ANCHOR", "G_F":"DEPTH_UNAVAILABLE"},
        "caveats":["Outcome-selected in-sample frame sources", "Actual cross-source covariance UNKNOWN", "Angular coordinate is not depth", "No physical boost, shear, family, or native-transfer claim"],
        "raw_full_carrier":str(raw), "raw_full_carrier_sha256":sha256(raw),
        "raw_covariance":str(args.raw / "covariance.npy"), "raw_covariance_sha256":sha256(args.raw / "covariance.npy"),
        "elapsed_seconds":time.monotonic()-t0,
    }
    (args.raw / "RESULT.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"stage":"complete", "seconds":time.monotonic()-t0, "checks":checks}), flush=True)


if __name__ == "__main__":
    main()
