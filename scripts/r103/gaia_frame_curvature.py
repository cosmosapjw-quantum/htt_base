"""Spatial influence of finite-redshift VSH curvature in the four R98 Quaia shells."""
from __future__ import annotations

import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

import numpy as np


BASE = Path("docs/research_program/observational_publication_20261015")
SOURCE = BASE / "R98_FOURTH_RESEARCH_CYCLE_20261123/GAIA_FULL_SHARED_PATCH.json"
SOURCE_SHA = "0a56bc358b6048f4b018d93d2b55be2f2ac5526e22191a44ca6a9f1148a9d800"
OUTPUT = BASE / "R103_SOLVER_SOURCE_CONTINUATION_20261123/GAIA_FRAME_RESULT.json"
SHELLS = tuple(f"quaia_z{i}" for i in range(4))
SECTORS = {"glide": slice(0, 3), "spin": slice(3, 6), "E2": slice(6, 11), "B2": slice(11, 16)}


def curvature_rows(redshift):
    """Twice the second divided difference. Maps c*z**2 to 2*c."""
    z = np.asarray(redshift, dtype=float)
    if z.shape != (4,) or not np.all(np.isfinite(z)) or np.any(np.diff(z) <= 0):
        raise ValueError("four finite strictly increasing median redshifts required")
    rows = np.zeros((2, 4))
    for i in range(2):
        dz1, dz2 = np.diff(z[i:i + 3])
        rows[i, i:i + 3] = (2 / (dz1 + dz2)) * np.array(
            [1 / dz1, -(1 / dz1 + 1 / dz2), 1 / dz2]
        )
    return rows


def shared_patch_refits(fisher, rhs):
    """Solve weighted normal equations after dropping the same patch(es) in all shells."""
    f = np.asarray(fisher, dtype=float)
    s = np.asarray(rhs, dtype=float)
    if f.ndim != 4 or f.shape[-1] != f.shape[-2] or s.shape != f.shape[:-1]:
        raise ValueError("expected shell x patch x coefficient normal equations")
    if not np.all(np.isfinite(f)) or not np.all(np.isfinite(s)):
        raise ValueError("non-finite patch statistics")
    nshell, npatch, ncoef, _ = f.shape
    if npatch < 3:
        raise ValueError("at least three spatial patches required")
    if not np.allclose(f, f.swapaxes(-1, -2), atol=0, rtol=1e-10):
        raise ValueError("nonsymmetric Fisher block")
    ft = f.sum(axis=1)
    st = s.sum(axis=1)

    def solve(fblocks, sblocks):
        # The cache RHS carries mas/yr. Cholesky also rejects unidentified retained fits.
        chol = np.linalg.cholesky(fblocks)
        mid = np.linalg.solve(chol, sblocks[..., None])
        return np.linalg.solve(chol.swapaxes(-1, -2), mid)[..., 0] * 1000

    full = solve(ft, st)
    one = solve(ft[None] - f.swapaxes(0, 1), st[None] - s.swapaxes(0, 1))
    pairs = np.asarray(list(combinations(range(npatch), 2)), dtype=int)
    two = np.empty((len(pairs), nshell, ncoef))
    # Group by first deletion, retaining O(patches * shells * ncoef^2) workspace.
    pos = 0
    for i in range(npatch - 1):
        fj = f[:, i + 1:].swapaxes(0, 1)
        sj = s[:, i + 1:].swapaxes(0, 1)
        chunk = solve(ft - f[:, i] - fj, st - s[:, i] - sj)
        two[pos:pos + len(chunk)] = chunk
        pos += len(chunk)
    return full, one, two, pairs


def delete_covariance(samples, npatch, ndeleted):
    flat = samples.reshape(len(samples), -1)
    centered = flat - flat.mean(axis=0)
    return ((npatch - ndeleted) / (ndeleted * len(samples))) * centered.T @ centered


def compute(receipt_path=SOURCE, cache_path=None):
    raw = Path(receipt_path).read_bytes()
    if sha256(raw).hexdigest() != SOURCE_SHA:
        raise ValueError("R98 input receipt identity mismatch")
    source = json.loads(raw)
    meta = source["joint_160d_patch_covariance"]
    cache_path = Path(meta["cache_path"] if cache_path is None else cache_path)
    if sha256(cache_path.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError("R98 patch cache identity mismatch")
    z = np.array(source["redshift_bin_medians"])
    w = curvature_rows(z)
    with np.load(cache_path, allow_pickle=False) as data:
        names = list(data["names"].astype(str))
        if names != meta["order"]:
            raise ValueError("R98 shell order mismatch")
        f = np.stack([data[n + "__F"] for n in SHELLS])
        s = np.stack([data[n + "__s"] for n in SHELLS])
        cov160 = data["cov"]
    if f.shape != (4, 48, 16, 16):
        raise ValueError("unexpected R98 shell statistics shape")
    full, one, two, pairs = shared_patch_refits(f, s)
    ref = np.array([source["fits"][n]["coefs_microasyr"] for n in SHELLS])
    fit_err = float(np.max(np.abs(full - ref)))
    if fit_err > 1e-8:
        raise ValueError("published full-source shell coefficients failed replay")
    ids = np.concatenate([np.arange(16 * names.index(n), 16 * (names.index(n) + 1)) for n in SHELLS])
    transform = np.kron(w, np.eye(16))
    ref_cov = transform @ cov160[np.ix_(ids, ids)] @ transform.T
    measured = w @ full
    one_w = w @ one
    two_w = w @ two
    npatch = len(one)
    cov1 = delete_covariance(one_w, npatch, 1)
    cov2 = delete_covariance(two_w, npatch, 2)
    cov_err = float(np.max(np.abs(cov1 - ref_cov)))
    if not np.allclose(cov1, ref_cov, rtol=1e-9, atol=1e-9):
        raise ValueError("delete-one replay disagrees with published shared covariance")
    # Pair departure from separately added one-patch influences; zero for an additive estimator.
    pair_interaction = two_w - one_w[pairs[:, 0]] - one_w[pairs[:, 1]] + measured
    rows = []
    for i in range(2):
        for name, sector in SECTORS.items():
            observed = measured[i, sector]
            delta = two_w[:, i, sector] - observed
            norms = np.linalg.norm(delta, axis=1)
            imax = int(np.argmax(norms))
            diagonal = np.arange(i * 16 + sector.start, i * 16 + sector.stop)
            jk1_trace = float(np.trace(cov1[np.ix_(diagonal, diagonal)]))
            jk2_trace = float(np.trace(cov2[np.ix_(diagonal, diagonal)]))
            rows.append({
                "shell_indices": [i, i + 1, i + 2], "sector": name,
                "coefficients_microasyr_per_z2": observed.tolist(),
                "observed_coefficient_norm": float(np.linalg.norm(observed)),
                "jk1_rms": float(np.sqrt(jk1_trace)), "jk2_rms": float(np.sqrt(jk2_trace)),
                "maximum_pair_shift_norm": float(norms[imax]), "worst_pair_nside2_ring": pairs[imax].tolist(),
                "max_pair_nonadditive_norm": float(np.max(np.linalg.norm(pair_interaction[:, i, sector], axis=1))),
            })
    return {
        "schema": "htt.r103.gaia_frame_curvature/1", "status": "SOURCE_CONDITIONED_SPATIAL_INFLUENCE",
        "receipt_sha256": SOURCE_SHA, "patch_cache_sha256": meta["sha256"],
        "qualified_quaia_total": source["source_row_census"]["quaia_qualified"],
        "shell_counts": [source["fits"][n]["n_sources"] for n in SHELLS],
        "source_rows_reread": 0, "exact_shared_one_deletions": len(one), "exact_shared_pair_deletions": len(two),
        "shell_median_redshifts": z.tolist(), "curvature_rows": w.tolist(),
        "affine_annihilation_max_abs": float(np.max(np.abs(w @ np.column_stack((np.ones(4), z))))),
        "full_shell_coefficient_replay_max_abs_microasyr": fit_err,
        "jk1_vs_committed_r98_covariance_max_abs": cov_err,
        "joint_jk1_curvature_rank": int(np.linalg.matrix_rank(cov1)),
        "joint_jk2_curvature_rank": int(np.linalg.matrix_rank(cov2)),
        "coefficient_norm_units": "microarcsec/year per unit redshift squared in R98 coefficient basis",
        "rows": rows, "calibrated_p": None, "physical_Pi": None, "physical_GF": None,
        "limitations": [
            "Finite differences of bin fits at median redshifts. Exact affine cancellation refers to these four coefficients; within-shell selection and redshift evolution are unresolved.",
            "Nested overlapping deletions reuse the same 48 sky patches. Their RMS values describe spatial sensitivity and share the underlying noise realization.",
            "AGN centroid and calibrated Gaia spatial systematics, a physical shear transfer, and an independent sampling law remain unavailable."
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = compute(args.source, args.cache)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
