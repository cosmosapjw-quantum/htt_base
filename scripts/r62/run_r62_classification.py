#!/usr/bin/env python3
"""Execute joint STF-series class compatibility on owned R62/R58 carriers.

One Gaussian confidence event per carrier. Local fits are feasible upper
bounds. Class incompatibility needs a sound necessary-condition enclosure.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy import linalg, stats


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, (np.integer, np.bool_)):
        return value.item()
    if isinstance(value, (float, np.floating)):
        if not np.isfinite(value):
            raise ValueError("nonfinite JSON output")
        return float(value)
    return value


def run(root, source_dir, output):
    start = time.perf_counter()
    root, source_dir, output = map(lambda x: Path(x).resolve(), (root, source_dir, output))
    if output.exists() and any(output.iterdir()):
        raise ValueError("refusing to overwrite classification results")
    output.mkdir(parents=True, exist_ok=True)
    sys.path[:0] = [str(root / "htt"), str(root / "htt/src")]
    from htt.htt.infer import r62_tensor_classes as tc
    from htt.htt.infer.r61_kinematic_images import quadratic_ellipsoid_range, norm_ellipsoid_range

    source = source_dir / "SOURCE_TENSOR_CARRIERS.npz"
    reference = json.loads((source_dir / "SOURCE_TENSOR_RESULT.json").read_text())
    if sha(source) != reference["carrier_sha256"]:
        raise ValueError("source carrier hash differs")
    saved = np.load(source, allow_pickle=False)
    variants = list(reference["variants"])
    E = tc.stf_basis()
    np.testing.assert_array_equal(E, saved["STF_basis"])
    # These are declared directions for ordinary linear support images, not
    # data-selected physical axes or a normalized occupancy measure.
    directions = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [1, 0, 1], [0, 1, 1], [1, 1, 1]], dtype=float)
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    angular_rows = np.einsum("ni,aij,nj->na", directions, E, directions)
    records, rows, manifest = {}, [], {}
    for name in variants:
        y, C = saved[name + "__y32"], saved[name + "__cov32"]
        raw_h, raw_v = y[12:], C[12:, 12:]
        contrasted = tc.common_offset_contrast(raw_h, raw_v)
        experiments = [
            ("raw_windows", raw_h, raw_v, "Apparent angular-estimator windows; no physical shear transfer"),
            ("raw_differences", contrasted["mean"], contrasted["covariance"], "Arbitrary common estimator-tensor offset quotient; not an empirical calibration bound")]
        for degree in (2, 3):
            prefix = name + f"__J{degree}"
            h, V = saved[prefix + "__estimate"], saved[prefix + "__covariance"]
            experiments.extend([
                (f"J{degree}_coefficients", h[6:], V[6:, 6:], f"J{degree} source-bound Legendre tensor coefficients; common V,d nuisance marginalized"),
                (f"J{degree}_varying", h[11:], V[11:, 11:], f"J{degree} nonconstant source coefficients; arbitrary constant source angular calibration removed")])
        for kind, h, V, meaning in experiments:
            item_start = time.perf_counter()
            cutoff = float(stats.chi2.ppf(.95, h.size))
            result = tc.classify_tensor_series(h, V, cutoff, n_starts=10, grid_size=64,
                                              max_nfev=180, seed=620017,
                                              commutator_solver=quadratic_ellipsoid_range)
            # Check stored witnesses against an independent SPD solve, and
            # preserve enough information to reproduce every status directly.
            max_q_error = 0.
            for class_name, fit in result["classes"].items():
                residual = np.asarray(fit["witness"]) - h
                direct_q = float(residual @ linalg.solve(V, residual, assume_a="pos"))
                max_q_error = max(max_q_error, abs(direct_q - fit["objective"]))
                if abs(direct_q - fit["objective"]) > 2e-7 * max(1., abs(direct_q)):
                    raise ValueError("stored witness objective mismatch")
                if fit["status"] == "INTERSECTS" and direct_q > cutoff + 2e-7:
                    raise ValueError("invalid intersection certificate")
            zero = result["classes"]["ZERO"]
            norm_image = norm_ellipsoid_range(h, V, cutoff=cutoff)
            linear_supports = []
            for j in range(h.size // 5):
                B = np.zeros((len(directions), h.size))
                B[:, 5*j:5*j+5] = angular_rows
                centre = B @ h
                halfwidth = np.sqrt(cutoff * np.einsum("ai,ij,aj->a", B, V, B))
                linear_supports.append(dict(tensor_index=j, center=centre, lower=centre-halfwidth, upper=centre+halfwidth))
            enclosures = result["commutator_enclosures"]
            computed = [x for x in enclosures["ranges"] if x["status"] == "COMPUTED"]
            gap = max((max(x["enclosure"]["minimum"]["optimality_gap"], x["enclosure"]["maximum"]["optimality_gap"]) for x in computed), default=0.)
            record = {
                "schema": "htt.r62.tensor_classification/1", "variant": name, "experiment": kind,
                "interpretation": meaning, "source_carrier_sha256": sha(source),
                "mean": h, "covariance": V, "confidence": {"level": .95, "dimension": h.size, "cutoff": cutoff,
                    "law": "fixed Gaussian tensor marginal; one event for all classes of this carrier"},
                "classification": result,
                "five_view_links": {
                    "x": "Signed joint mean/covariance here; original source precision, score, q0 and stable whitened factor in SOURCE_TENSOR_CARRIERS.npz",
                    "Q_abs_series_norm": {"lower": norm_image["lower"], "upper": norm_image["upper"],
                        "meaning": "Absolute Frobenius series norm in the explicitly retained window or Legendre-coefficient chart; no physical ceiling"},
                    "F_support": {"directions_J2000": directions, "tensor_linear_supports": linear_supports,
                        "occupancy": "UNAVAILABLE: no physical ceiling and occupancy measure supplied"},
                    "Pi_zero": {"statistic": zero["objective"], "df": h.size, "nominal_tail": stats.chi2.sf(zero["objective"], h.size),
                        "law": "fixed Gaussian zero tensor mean; not a Bianchi probability or nonlinear class LRT"},
                    "G_transport": "Full cross-tensor covariance, source-depth coefficient classes and common-offset quotient; no proper-time evolution inference"},
                "verification": {"stored_witness_quadratic_max_abs_difference": max_q_error,
                    "quadratic_enclosures_computed": len(computed), "quadratic_enclosures_unresolved": len(enclosures["ranges"]) - len(computed),
                    "max_quadratic_primal_dual_gap": gap},
                "seconds": time.perf_counter() - item_start}
            file_name = name + "__" + kind + ".json"
            destination = output / file_name
            destination.write_text(json.dumps(clean(record), indent=2) + "\n")
            manifest[file_name] = sha(destination)
            key = name + "/" + kind
            summary = {"dimension": h.size, "cutoff": cutoff, "zero_nominal_p": stats.chi2.sf(zero["objective"], h.size),
                "classes": {c: {"status": f["status"], "feasible_distance2_upper": f["objective"],
                            "ratio_to_cutoff": f["objective"] / cutoff} for c, f in result["classes"].items()},
                "commutator_excluded": enclosures["excludes_commuting_class"], "receipt": file_name, "seconds": record["seconds"]}
            records[key] = summary
            for class_name, fit in result["classes"].items():
                rows.append(dict(variant=name, experiment=kind, dimension=h.size, cutoff=cutoff, class_name=class_name,
                                 status=fit["status"], feasible_distance2_upper=fit["objective"], ratio_to_cutoff=fit["objective"] / cutoff,
                                 zero_nominal_p=summary["zero_nominal_p"]))
            print(f"{key}: " + ", ".join(f"{c}={f['status']}({f['objective']:.4f})" for c, f in result["classes"].items()) + f" [{record['seconds']:.2f}s]", flush=True)
    with (output / "CLASSIFICATION_TABLE.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    final = {
        "schema": "htt.r62.classification_summary/1", "source_sha256": sha(source),
        "script_sha256": sha(__file__),
        "implementation_sha256": sha(root / "htt/htt/htt/infer/r62_tensor_classes.py"),
        "quadratic_solver_sha256": sha(root / "htt/htt/htt/infer/r61_kinematic_images.py"),
        "experiments": records, "receipt_sha256": manifest,
        "status_meaning": {"INTERSECTS": "reconstructed exact-class witness inside one confidence ellipsoid",
            "EXCLUDED": "unique zero state outside or signed commutator numerical necessary-condition enclosure excludes zero",
            "UNRESOLVED": "no inside witness and no valid exclusion; not evidence against a class"},
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__, "seconds": time.perf_counter()-start},
        "interpretive_boundary": "Morphology compatibility conditional on the owned covariance and finite source response; not recovered spacetime shear, full LRS, spatial homogeneity, a Bianchi family posterior or detected tilt."}
    (output / "CLASSIFICATION_SUMMARY.json").write_text(json.dumps(clean(final), indent=2) + "\n")
    print(json.dumps({"n_carriers": len(records), "n_class_queries": len(rows), "seconds": final["runtime"]["seconds"]}), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.root, args.source_dir, args.output)
