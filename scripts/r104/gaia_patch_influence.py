"""Per-patch Gaia/Quaia curvature influence: all 48 delete-one and 1,128 delete-two refits.

Reuses the R98 hash-pinned normal equations (634,233 qualified Quaia sources in four
shells) and the R103 second-difference rows that annihilate any redshift-affine frame.
Reports, per sector (glide, spin, E2, B2) and per curvature row, the observed curvature
coefficients, their chi^2 against the delete-one and delete-two jackknife covariances,
and the patch/pair whose removal moves the coefficients most.
Units: coefficients in microarcsec/yr per unit z^2 (R98 VSH basis); chi^2 dimensionless.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from scripts.r103 import gaia_frame_curvature as g


def analyze(receipt=g.SOURCE):
    raw = Path(receipt).read_bytes()
    if sha256(raw).hexdigest() != g.SOURCE_SHA:
        raise ValueError("R98 receipt identity mismatch")
    src = json.loads(raw)
    meta = src["joint_160d_patch_covariance"]
    cache = Path(meta["cache_path"])
    if sha256(cache.read_bytes()).hexdigest() != meta["sha256"]:
        raise ValueError("R98 patch cache identity mismatch")
    w = g.curvature_rows(np.array(src["redshift_bin_medians"]))
    with np.load(cache, allow_pickle=False) as data:
        f = np.stack([data[n + "__F"] for n in g.SHELLS])
        s = np.stack([data[n + "__s"] for n in g.SHELLS])
    full, one, two, pairs = g.shared_patch_refits(f, s)
    measured, one_w, two_w = w @ full, w @ one, w @ two
    npatch = len(one)
    cov1 = g.delete_covariance(one_w, npatch, 1)
    cov2 = g.delete_covariance(two_w, npatch, 2)
    rows = []
    for i in range(2):
        for name, sec in g.SECTORS.items():
            d = np.arange(i * 16 + sec.start, i * 16 + sec.stop)
            obs = measured[i, sec]
            shift1 = one_w[:, i, sec] - obs
            shift2 = two_w[:, i, sec] - obs
            n1 = np.linalg.norm(shift1, axis=1)
            n2 = np.linalg.norm(shift2, axis=1)
            order = np.argsort(n1)[::-1]
            c1, c2 = cov1[np.ix_(d, d)], cov2[np.ix_(d, d)]
            chi1 = float(obs @ np.linalg.solve(c1, obs))
            chi2 = float(obs @ np.linalg.solve(c2, obs))
            rows.append({
                "curvature_row": i, "shell_indices": [i, i + 1, i + 2], "sector": name, "dof": len(obs),
                "coefficients": obs.tolist(), "norm": float(np.linalg.norm(obs)),
                "chi2_vs_delete_one_cov": chi1, "chi2_vs_delete_two_cov": chi2,
                "delete_one_top5_patches": order[:5].tolist(), "delete_one_top5_shift_norm": n1[order[:5]].tolist(),
                "delete_one_shift_norm_median": float(np.median(n1)),
                "most_influential_patch_shift": shift1[order[0]].tolist(),
                "most_influential_patch_shift_over_norm": float(n1[order[0]] / max(np.linalg.norm(obs), 1e-300)),
                "delete_two_shift_norm_quantiles_50_90_99_max": np.quantile(n2, [.5, .9, .99, 1.]).tolist(),
                "delete_two_worst_pair": pairs[int(np.argmax(n2))].tolist(),
                "delete_two_worst_pair_contains_top_patch": bool(order[0] in pairs[int(np.argmax(n2))]),
            })
    return {"schema": "htt.r104.gaia_patch_influence/1", "receipt_sha256": g.SOURCE_SHA,
            "patch_cache_sha256": meta["sha256"], "qualified_quaia_total": src["source_row_census"]["quaia_qualified"],
            "n_patches": npatch, "n_delete_one": len(one), "n_delete_two": len(two),
            "units": "microarcsec/yr per unit z^2 (R98 VSH coefficient basis)", "rows": rows,
            "calibrated_p": None, "physical_Pi": None,
            "scope": "Nested overlapping patch deletions of one noise realization; chi^2 values are spatial-jackknife "
                     "diagnostics, not calibrated probabilities. AGN/scan systematics nonlinear in z survive the curvature rows."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    a.output.write_text(json.dumps(analyze(), indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
