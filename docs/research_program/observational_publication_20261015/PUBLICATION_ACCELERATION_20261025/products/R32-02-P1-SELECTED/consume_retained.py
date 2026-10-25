#!/usr/bin/env python3
"""Reproduce the paper's compact tables from frozen sufficient statistics.

This reads saved results only. It performs no row fit, selection estimation,
random draw, null simulation, or physical-response inference.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent


def load_bound(spec: dict, override: str | None) -> dict:
    path = Path(override or spec["path"])
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != spec["sha256"]:
        raise ValueError(f"source identity mismatch: {path}: {digest}")
    return json.loads(raw)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected-law", help="path to the hash-bound selected-law RESULT.json")
    parser.add_argument("--distance", help="path to the hash-bound distance RESULT.json")
    parser.add_argument("--selection", help="path to the hash-bound selection RESULT.json")
    parser.add_argument("--out", type=Path, default=HERE / "tables")
    args = parser.parse_args()

    sources = json.loads((HERE / "SOURCE_INPUTS.json").read_text())
    selected = load_bound(sources["selected_law"], args.selected_law)["r24_selected_C_union"]
    distance = load_bound(sources["distance_models"], args.distance)
    selection = load_bound(sources["selection"], args.selection)
    if (distance["cohort"]["released"], distance["cohort"]["selected"],
            distance["cohort"]["undefined"]) != (274, 628, 354):
        raise ValueError("cohort identity is inconsistent with the manuscript")
    if (selection["cohort_size"], selection["known_frame_size"],
            selection["undefined_binary_rows"]) != (274, 628, 354):
        raise ValueError("selection frame is inconsistent with the manuscript")

    likelihood, stf, scores = [], [], []
    radius = 27.058502419705658
    shape_keys = list(selected["scenarios"])
    if len(shape_keys) != 4 or set(shape_keys) != set(distance["scenarios"]):
        raise ValueError("four matched covariance shapes are required")
    for shape in shape_keys:
        item = selected["scenarios"][shape]
        if (item["n"], item["p"], item["nu"]) != (274, 15, 259):
            raise ValueError(f"incorrect full coefficient dimension: {shape}")
        covariance = np.asarray(item["covariance_ML_full_including_cross_blocks"], dtype=float)
        if covariance.shape != (15, 15):
            raise ValueError(f"incomplete coefficient covariance: {shape}")
        region = item["exact_F_region"]
        if not math.isclose(region["radius_sq_full"], radius, rel_tol=1e-12):
            raise ValueError(f"finite-F radius mismatch: {shape}")
        beta = np.asarray(region["STF5_signed_beta_mag"], dtype=float)
        stf_cov = covariance[-5:, -5:]
        if not np.allclose(stf_cov, region["STF5_covariance_ML_mag2"], rtol=1e-12, atol=1e-12):
            raise ValueError(f"STF covariance mismatch: {shape}")
        zero_q = float(beta @ np.linalg.solve(stf_cov, beta))
        old_q = item["historical_chi2_reference"]["zero_STF_mahalanobis_sq"]
        if not math.isclose(zero_q, old_q, rel_tol=1e-10, abs_tol=1e-10):
            raise ValueError(f"projected joint zero check mismatch: {shape}")
        if zero_q > radius:
            raise ValueError(f"zero leaves projected joint STF region: {shape}")
        for index, (value, pair) in enumerate(zip(beta, region["STF5_coordinate_bounds_mag"]), 1):
            width = math.sqrt(radius * stf_cov[index - 1, index - 1])
            if not np.allclose(pair, [value - width, value + width], rtol=1e-10, atol=1e-10):
                raise ValueError(f"coordinate projection mismatch: {shape}, {index}")
            stf.append({"shape": shape, "coordinate": index, "estimate_mag": value,
                        "lower_mag": pair[0], "upper_mag": pair[1]})
        tails = [p["two_sided_tail"] for p in selected["fold_diagnostics"]["pivots"]
                 if p["shape"] == shape]
        if len(tails) != 5:
            raise ValueError(f"five saved group-fold checks required: {shape}")
        likelihood.append({"shape": shape, "n": item["n"], "p": item["p"],
                           "nu": item["nu"], "rss": item["rss_saved"],
                           "sigma2_ml": item["sigma2_ML_saved"],
                           "normalized_log_likelihood": item["likelihood"]["logL_at_saved_beta_and_sigma2_ML"],
                           "finite_F_radius_sq": region["radius_sq_full"],
                           "minimum_fold_two_sided_tail": min(tails),
                           "projected_STF_zero_mahalanobis_sq": zero_q,
                           "projected_STF_zero_inside": True})
        models = distance["scenarios"][shape]["models"]
        scores.append({"shape": shape, **{key: models[key]["total_joint_log_predictive_score"]
                                             for key in ("A_calibration_flow", "B_optical_STF", "C_union")}})

    surface = [row for row in selection["fixed_surface"]
               if row["threshold_mag"] == 0.5 and row["gamma"] in (1.0, 2.0, 4.0)]
    if len(surface) != 36:
        raise ValueError("expected twelve model-shape cases at each of three sensitivity levels")
    missing = []
    for row in surface:
        if row["gamma"] == 1.0 and not math.isclose(row["frame628_width"], 354 / 628, abs_tol=1e-12):
            raise ValueError("finite-frame missingness width mismatch")
        missing.append({key: row[key] for key in
                        ("scenario", "model", "threshold_mag", "gamma", "event_count",
                         "frame628_lower", "frame628_upper", "frame628_width")})
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "likelihood.csv", list(likelihood[0]), likelihood)
    write_csv(args.out / "stf_projection.csv", list(stf[0]), stf)
    write_csv(args.out / "model_scores.csv", list(scores[0]), scores)
    write_csv(args.out / "missingness.csv", list(missing[0]), missing)
    receipt = {
        "schema": "htt.r32.p1.retained_consumer/1",
        "scope": "saved sufficient-statistic and fixed-surface consumer; no new fit or law",
        "source_sha256": {key: value["sha256"] for key, value in sources.items()},
        "shape_count": 4,
        "full_coefficient_dimension": 15,
        "stf_projection_rows": len(stf),
        "fold_pivots": len(selected["fold_diagnostics"]["pivots"]),
        "minimum_fold_two_sided_tail": min(row["minimum_fold_two_sided_tail"] for row in likelihood),
        "joint_projected_STF_zero_inside_each_shape": True,
        "missingness_fixed_surface_rows": len(missing),
        "frame_hull_width_at_gamma_one": 354 / 628,
        "tables": {name: hashlib.sha256((args.out / name).read_bytes()).hexdigest()
                   for name in ("likelihood.csv", "stf_projection.csv", "model_scores.csv", "missingness.csv")},
    }
    (args.out / "CONSUMER_RESULT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "output": str(args.out),
                      "tables": list(receipt["tables"]), "zero_inside": True}))


if __name__ == "__main__":
    main()
