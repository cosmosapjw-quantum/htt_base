"""Public CF3--SDSS individual calibration and depth diagnostic.

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

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "htt/htt"), str(REPO / "htt"), str(REPO / "htt/src")]
from htt.infer import sdss_cf3_calibration as calibration
from htt.infer.sdss_cf3_calibration import cf3_eta_from_distance_modulus, depth_calibration_operator, read_public_pgc_join
from obsstat import sdss_pv_depth
from obsstat.sdss_pv_depth import angular_basis, representation, read_catalogue, extract_depth

MAXIMA = np.array([.025, .05, .075, .1])
ZMIN = .0033

OFFICIAL_SDSS_MD5 = "b5b6e31caf7ea469c2ac2cb775fa8d14"


def digest(path: Path, name: str) -> str:
    h = hashlib.new(name)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def depth_projection(data: np.ndarray) -> np.ndarray:
    """The release's unit-weight SVD projection, scattered into all 34,059 rows."""
    n = len(data)
    basis = angular_basis(data["RA"], data["Dec"])
    out = np.zeros((36, n))
    eligible = (data["in_mask"] == 1) & (data["zcmb"] > ZMIN)
    for j, maximum in enumerate(MAXIMA):
        rows = np.flatnonzero(eligible & (data["zcmb"] < maximum))
        design = basis[rows]
        u, singular, vt = np.linalg.svd(design, full_matrices=False)
        if len(singular) != 9 or singular[-1] <= 1e-10 * singular[0]:
            raise ValueError(f"unresolved public-data angular response in window {j}")
        out[9*j:9*(j+1), rows] = (vt.T / singular) @ u.T
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--cf3", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cf3-sha256", required=True, help="Frozen CF3 table3 byte identity for this run")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("--output must name a new non-existing directory")
    if digest(args.data, "md5") != OFFICIAL_SDSS_MD5:
        raise ValueError("SDSS official MD5 mismatch")
    if digest(args.cf3, "sha256") != args.cf3_sha256:
        raise ValueError("CF3 frozen input SHA256 mismatch")
    args.output.mkdir(parents=True)
    data = np.genfromtxt(args.data, names=True, dtype=None, encoding="ascii")
    joined = read_public_pgc_join(args.data, args.cf3, corrected=False)
    index = {int(p): i for i, p in enumerate(data["PGC"])}
    rows = np.asarray([index[int(p)] for p in joined.pgc])
    eta = cf3_eta_from_distance_modulus(joined.cf3_distance_modulus, joined.sdss_zcmb)
    retained = np.array([not ({"H", "I"} & set(code.split(","))) for code in joined.cf3_distance_source])
    widths = np.hypot(joined.sdss_logdist_err, joined.cf3_distance_modulus_err / 5)
    if not np.any(retained) or not np.all(np.isfinite(widths)) or np.any(widths <= 0):
        raise ValueError("retained rows and finite positive diagnostic widths required")
    w = np.zeros(len(joined.pgc)); w[retained] = 1 / widths[retained]**2; w /= w.sum()
    l = np.zeros(len(data) + len(joined.pgc)); l[rows] = -w; l[len(data):] = w
    m = depth_projection(data)
    g = depth_calibration_operator(m, l, n_sdss_rows=len(data))
    joint = np.concatenate((data["logdist"].astype(float), eta))
    y0 = m @ data["logdist"]; y1 = g @ joint; shift = y1-y0; rep = representation(MAXIMA)
    reference = extract_depth(read_catalogue(args.data.read_bytes()), z_min=ZMIN, maxima=MAXIMA)
    original_projection_error = float(np.max(np.abs(y0 - reference["Y"])))
    if original_projection_error > 1e-12:
        raise ValueError("calibration projection differs from existing SDSS depth path")
    all_weights = 1 / widths**2
    payload = {
        "owner": "HTT calibration with obsstat depth extraction", "claim_tier": "DIAGNOSTIC_ONLY",
        "alpha_spent": 0, "selected_observation_law": "UNAVAILABLE",
        "physical_local_global_response": "UNAVAILABLE", "state_jet_anchor_coverage": "UNAVAILABLE",
        "all_296_descriptive_offset_dex": float(np.average(eta - joined.sdss_logdist, weights=all_weights)),
        "existing_depth_projection_max_abs": original_projection_error,
        "depth_row_counts": reference["counts"].tolist(),
        "sources": {"SDSS": "https://zenodo.org/records/6824749", "CF3": "https://cdsarc.cds.unistra.fr/viz-bin/cat/J/AJ/152/50"},
        "source_sha256": {"runner": digest(Path(__file__), "sha256"), "calibration": digest(Path(calibration.__file__), "sha256"), "depth_extraction": digest(Path(sdss_pv_depth.__file__), "sha256")},
        "status": "RULE_BASED_PUBLIC294_DEPTH_DIAGNOSTIC_ONLY",
        "non_admission": ["no joint covariance", "no standard error or confidence law", "not Eq25/group292", "no full mock repetition"],
        "inputs": {"sdss_path": str(args.data), "sdss_md5": OFFICIAL_SDSS_MD5, "sdss_sha256": digest(args.data, "sha256"), "cf3_path": str(args.cf3), "cf3_sha256": digest(args.cf3, "sha256")},
        "code_sha256": digest(Path(__file__), "sha256"), "versions": {"python": platform.python_version(), "numpy": np.__version__},
        "config": {"omega_m": .31, "h0_km_s_mpc": 75, "z_min": ZMIN, "maxima": MAXIMA.tolist(), "mask": "in_mask == 1", "projection": "unit-weight SVD angular_basis", "distance_convention": "log10(Dcom(SDSS zcmb;H0=75)/(10^((CF3 DM-25)/5)/(1+SDSS zcmb)))"},
        "counts": {"sdss_rows": int(len(data)), "exact_pgc_overlap": int(len(joined.pgc)), "rule_based_public294": int(retained.sum()), "excluded_tf_pgc": joined.pgc[~retained].tolist()},
        "descriptive_offset_dex": float(l @ joint), "weight_convention": "inverse(logdist_err^2+(e_DM/5)^2), point estimator only", "joint_covariance_status": "UNAVAILABLE_NOT_ZERO_FILLED",
        "depth": {"g_shape": list(g.shape), "direct_refit_max_abs": float(np.max(abs(y1 - m @ (data["logdist"] + (l @ joint))))), "contrast_shift_max_abs": float(np.max(abs(rep.H @ shift))), "initial_level_shift": shift[:9].tolist(), "anchored_before": (rep.T@y0).tolist(), "anchored_after": (rep.T@y1).tolist()}
    }
    (args.output / "result.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    np.savez_compressed(args.output / "rows_and_coefficients.npz", pgc=joined.pgc, sdss_row_indices=rows, rule_based_public294_mask=retained, pair_weights=w, offset_coefficients=l, sdss_objid=data["objid"].astype(str), cf3_eta=eta, sdss_zcmb=joined.sdss_zcmb, cf3_distance_modulus=joined.cf3_distance_modulus, cf3_distance_modulus_err=joined.cf3_distance_modulus_err, cf3_source=joined.cf3_distance_source, y_before=y0, y_after=y1, r_before=rep.H@y0, r_after=rep.H@y1, anchored_before=rep.T@y0, anchored_after=rep.T@y1)
    print(json.dumps(payload, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
