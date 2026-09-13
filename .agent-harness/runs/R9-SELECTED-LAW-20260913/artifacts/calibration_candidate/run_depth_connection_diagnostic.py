"""Concrete downstream diagnostic for the unshifted individual CF3 candidate.

This does not calibrate the preferred group-richness product and cannot replay
the paper's group result.  Its quoted-width weights are a declared point
estimator convention only; no covariance, standard error, confidence law, or
mock-law claim is made.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
sys.path[:0] = [str(REPO / "htt"), str(REPO / "htt/src")]
from obsstat.sdss_pv_depth import angular_basis, representation  # noqa: E402
from cf3_sdss_calibration_candidate import (  # noqa: E402
    cf3_eta_from_distance_modulus, depth_calibration_operator, read_public_pgc_join,
)

SDSS = Path("/mnt/sn850x2t/htt_base_e2e/workdir/raw/sdss_pv_zenodo_6824749/SDSS_PV_public.dat")
CF3 = ROOT / "sources" / "CF3_table3.dat"
MAXIMA = np.array([.025, .05, .075, .1])
ZMIN = .0033


def read_sdss() -> np.ndarray:
    return np.genfromtxt(SDSS, names=True, dtype=None, encoding="ascii")


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
    data = read_sdss()
    if len(data) != 34059:
        raise ValueError(f"unexpected public SDSS row count {len(data)}")
    joined = read_public_pgc_join(SDSS, CF3, corrected=False)
    index = {int(pgc): i for i, pgc in enumerate(data["PGC"])}
    overlap_rows = np.asarray([index[int(pgc)] for pgc in joined.pgc])
    eta = cf3_eta_from_distance_modulus(joined.cf3_distance_modulus, joined.sdss_zcmb)
    widths = np.hypot(joined.sdss_logdist_err, joined.cf3_distance_modulus_err / 5.0)
    retained = ~np.isin(joined.cf3_distance_source, ["H", "I"])
    pair_weights = np.zeros(len(joined.pgc))
    pair_weights[retained] = 1.0 / widths[retained]**2
    pair_weights /= pair_weights.sum()
    # l acts on [full SDSS rows, CF3 overlap eta rows].  It is a point-estimator
    # coefficient only, so no C_joint is constructed or propagated.
    l = np.zeros(len(data) + len(joined.pgc))
    l[overlap_rows] = -pair_weights
    l[len(data):] = pair_weights
    m = depth_projection(data)
    g = depth_calibration_operator(m, l, n_sdss_rows=len(data))
    joint_values = np.concatenate((data["logdist"].astype(float), eta))
    delta = float(l @ joint_values)
    y_before = m @ data["logdist"]
    y_after = g @ joint_values
    direct_refit = m @ (data["logdist"] + delta)
    rep = representation(MAXIMA)
    shift = y_after - y_before
    result = {
        "status": "PUBLIC_INDIVIDUAL_DEPTH_CONNECTION_DIAGNOSTIC_ONLY",
        "n_sdss_rows": int(len(data)), "n_pgc_overlap": int(len(joined.pgc)),
        "n_rule_based_public294": int(retained.sum()), "excluded_tf_pgc": joined.pgc[~retained].tolist(),
        "value": "unshifted SDSS logdist only; logdist_corr and Eq25 are not used",
        "windows": MAXIMA.tolist(), "z_min": ZMIN, "mask": "in_mask == 1",
        "projection": "unit-weight SVD of existing angular_basis",
        "delta_cf3_minus_sdss_dex_descriptive": delta,
        "weight_definition": "exclude r_Dist H/I Tully-Fisher rows then inverse(logdist_err^2+(e_DM/5)^2), normalized; point estimate only",
        "joint_covariance_status": "UNAVAILABLE_NOT_ZERO_FILLED",
        "g_shape": list(g.shape),
        "g_times_joint_equals_direct_refit_max_abs": float(np.max(np.abs(y_after-direct_refit))),
        "contrast_shift_max_abs": float(np.max(np.abs(rep.H @ shift))),
        "initial_level_shift": shift[:9].tolist(),
        "anchored_before": (rep.T @ y_before).tolist(),
        "anchored_after": (rep.T @ y_after).tolist(),
        "full_mock_repetition_status": "UNAVAILABLE: released mocks lack Tempel group and CF3-anchor inputs",
    }
    np.savez_compressed(ROOT / "individual_depth_connection.npz",
                        pgc=joined.pgc, sdss_row_indices=overlap_rows,
                        rule_based_public294_mask=retained, pair_weights=pair_weights, offset_coefficients=l,
                        full_input_order=np.asarray("[SDSS_PV_public row order, CF3 exact-PGC overlap sorted PGC]"),
                        y_before=y_before, y_after=y_after, initial_level_shift=shift[:9],
                        anchored_before=rep.T @ y_before, anchored_after=rep.T @ y_after,
                        joint_covariance_status=np.asarray("UNAVAILABLE_NOT_ZERO_FILLED"))
    (ROOT / "individual_depth_connection.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
