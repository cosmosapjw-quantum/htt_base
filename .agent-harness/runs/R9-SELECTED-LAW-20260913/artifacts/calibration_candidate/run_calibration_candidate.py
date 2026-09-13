"""One-shot public CF3--SDSS candidate diagnostic CLI.

The output directory must not exist.  This protects prior diagnostic evidence
from accidental replacement.  The result is descriptive and non-claim-bearing.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
sys.path[:0] = [str(ROOT), str(REPO / "htt"), str(REPO / "htt/src")]
from cf3_sdss_calibration_candidate import cf3_eta_from_distance_modulus, depth_calibration_operator, read_public_pgc_join
from run_depth_connection_diagnostic import MAXIMA, ZMIN, depth_projection
from obsstat.sdss_pv_depth import representation

OFFICIAL_SDSS_MD5 = "b5b6e31caf7ea469c2ac2cb775fa8d14"


def digest(path: Path, name: str) -> str:
    h = hashlib.new(name)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--cf3", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("--output must name a new non-existing directory")
    if digest(args.data, "md5") != OFFICIAL_SDSS_MD5:
        raise ValueError("SDSS official MD5 mismatch")
    args.output.mkdir(parents=True)
    data = np.genfromtxt(args.data, names=True, dtype=None, encoding="ascii")
    joined = read_public_pgc_join(args.data, args.cf3, corrected=False)
    index = {int(p): i for i, p in enumerate(data["PGC"])}
    rows = np.asarray([index[int(p)] for p in joined.pgc])
    eta = cf3_eta_from_distance_modulus(joined.cf3_distance_modulus, joined.sdss_zcmb)
    retained = ~np.isin(joined.cf3_distance_source, ["H", "I"])
    widths = np.hypot(joined.sdss_logdist_err, joined.cf3_distance_modulus_err / 5)
    w = np.zeros(len(joined.pgc)); w[retained] = 1 / widths[retained]**2; w /= w.sum()
    l = np.zeros(len(data) + len(joined.pgc)); l[rows] = -w; l[len(data):] = w
    m = depth_projection(data)
    g = depth_calibration_operator(m, l, n_sdss_rows=len(data))
    joint = np.concatenate((data["logdist"].astype(float), eta))
    y0 = m @ data["logdist"]; y1 = g @ joint; shift = y1-y0; rep = representation(MAXIMA)
    payload = {
        "status": "RULE_BASED_PUBLIC294_DEPTH_DIAGNOSTIC_ONLY",
        "non_admission": ["no joint covariance", "no standard error or confidence law", "not Eq25/group292", "no full mock repetition"],
        "inputs": {"sdss_path": str(args.data), "sdss_md5": OFFICIAL_SDSS_MD5, "sdss_sha256": digest(args.data, "sha256"), "cf3_path": str(args.cf3), "cf3_sha256": digest(args.cf3, "sha256")},
        "code_sha256": digest(Path(__file__), "sha256"), "versions": {"python": platform.python_version(), "numpy": np.__version__},
        "config": {"omega_m": .31, "h0_km_s_mpc": 75, "z_min": ZMIN, "maxima": MAXIMA.tolist(), "mask": "in_mask == 1", "projection": "unit-weight SVD angular_basis", "distance_convention": "log10(Dcom(SDSS zcmb;H0=75)/(10^((CF3 DM-25)/5)/(1+SDSS zcmb)))"},
        "counts": {"sdss_rows": int(len(data)), "exact_pgc_overlap": int(len(joined.pgc)), "rule_based_public294": int(retained.sum()), "excluded_tf_pgc": joined.pgc[~retained].tolist()},
        "descriptive_offset_dex": float(l @ joint), "weight_convention": "inverse(logdist_err^2+(e_DM/5)^2), point estimator only", "joint_covariance_status": "UNAVAILABLE_NOT_ZERO_FILLED",
        "depth": {"g_shape": list(g.shape), "direct_refit_max_abs": float(np.max(abs(y1 - m @ (data["logdist"] + (l @ joint))))), "contrast_shift_max_abs": float(np.max(abs(rep.H @ shift))), "initial_level_shift": shift[:9].tolist(), "anchored_before": (rep.T@y0).tolist(), "anchored_after": (rep.T@y1).tolist()}
    }
    (args.output / "result.json").write_text(json.dumps(payload, indent=2) + "\n")
    np.savez_compressed(args.output / "rows_and_coefficients.npz", pgc=joined.pgc, sdss_row_indices=rows, rule_based_public294_mask=retained, offset_coefficients=l, y_before=y0, y_after=y1)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
