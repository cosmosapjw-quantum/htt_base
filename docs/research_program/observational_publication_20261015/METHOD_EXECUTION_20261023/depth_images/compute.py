"""Joint functional depth images of the reviewed tensor scenario.

All linear maps act on one retained full24 carrier and one retained sample law.
The ellipsoid, empirical law, and reference ball are computational objects.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
INPUT = BASE / "R24-DEPTH-IMAGES_EXECUTION_INPUT.json"
INPUT_SHA = "4337e37b166e7bdc824e856202f8ed212b715ed72ae38f8c65da7e874963c9da"
REGION_ID = "K03-full24-common-C-rho-reported-z-scenario"
RADII = (0, 1, 2, 4, 8)
NORM_THRESHOLDS = (0, 1, 2, 5, 10, 20)
DOT_THRESHOLDS = (-25, 0, 25)
PAIRS = ((0, 1), (1, 2), (0, 2))
LABELS = tuple(f"bin{b}_{mode}" for b in range(3) for mode in ("E1", "B1")) + tuple(
    f"bin{j}-bin{i}_{mode}" for i, j in PAIRS for mode in ("E1", "B1"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source():
    if digest(INPUT) != INPUT_SHA:
        raise ValueError("frozen depth input identity mismatch")
    contract = json.loads(INPUT.read_text())
    for source in contract["sources"]:
        path = ROOT / source["path"]
        if digest(path) != source["sha256"] or path.stat().st_size != source["bytes"]:
            raise ValueError(f"immutable source identity mismatch: {path}")
    tensor = BASE / "tensor_bundle"
    result = json.loads((tensor / "RESULT.json").read_text())
    manifest = json.loads((tensor / "MANIFEST.json").read_text())
    if result["qualified_products"] != ["tensor_scenario"] or manifest["qualified_products"] != ["tensor_scenario"]:
        raise ValueError("reviewed scenario product missing")
    with np.load(tensor / "SAMPLES.npz") as archive:
        samples = archive["sample24_uasyr"].copy()
        source_functionals = archive["x_sample_functional_uasyr"].copy()
    mean = np.asarray(result["full24"]["mean_uasyr"], float)
    cov = np.asarray(result["full24"]["cov_uasyr2"], float)
    if mean.shape != (24,) or cov.shape != (24, 24) or samples.shape != (4096, 24):
        raise ValueError("full24 source shape mismatch")
    if source_functionals.shape != (4096, 8, 3) or not np.array_equal(source_functionals, samples.reshape(4096, 8, 3)):
        raise ValueError("source joint sample law mismatch")
    if not np.isfinite(samples).all() or not np.isfinite(cov).all() or not np.isfinite(mean).all():
        raise ValueError("nonfinite source")
    if np.max(np.abs(cov - cov.T)) > 1e-10 or np.linalg.eigvalsh(cov).min() <= 0:
        raise ValueError("invalid source covariance")
    if result["region_id"] != REGION_ID or tuple(r["rho"] for r in result["F"]["region_family"]) != RADII:
        raise ValueError("common region identity mismatch")
    return result, mean, cov, samples


def functional_map(m24_to_y18: np.ndarray) -> np.ndarray:
    """Image the reported-bin Y18 values and their contrasts from one full24 state."""
    m = np.asarray(m24_to_y18, dtype=float)
    if m.shape != (18, 24) or not np.isfinite(m).all():
        raise ValueError("reported-bin M24→Y18 map required")
    bmap = np.zeros((36, 18))
    for bin_index in range(3):
        for mode in range(2):
            row = 6*bin_index + 3*mode
            bmap[row:row+3, row:row+3] = np.eye(3)
    for p, (i, j) in enumerate(PAIRS):
        for mode in range(2):
            row = 18 + 6*p + 3*mode
            bmap[row:row+3, 6*j+3*mode:6*j+3*mode+3] = np.eye(3)
            bmap[row:row+3, 6*i+3*mode:6*i+3*mode+3] = -np.eye(3)
    return bmap @ m


def contrast_covariance(ci: np.ndarray, cj: np.ndarray, cij: np.ndarray | None) -> np.ndarray | None:
    """None means cross-depth covariance unavailable; it is never zero-filled."""
    return None if cij is None else ci + cj - cij - cij.T


def strict_frequency(values: np.ndarray, thresholds: np.ndarray) -> np.ndarray:
    """Empirical frequency under the retained rows; exact ties are excluded."""
    values, thresholds = np.asarray(values), np.asarray(thresholds)
    return (values[..., None] > thresholds).mean(axis=0)


def compute():
    source, mean, cov, samples = load_source()
    m = np.asarray(source["G_F"]["M24_to_Y18_matrix"], float)
    t = np.asarray(source["G_F"]["Y18_to_Z18_matrix"], float)
    a = functional_map(m)
    fmean = a @ mean
    fcov = a @ cov @ a.T
    fsamples = samples @ a.T
    vectors = fsamples.reshape(4096, 12, 3)
    norms = np.linalg.norm(vectors, axis=2)
    dot = np.einsum("nki,nki->nk", vectors[:, ::2, :], vectors[:, 1::2, :])
    empirical_norm_pi = strict_frequency(norms, np.asarray(NORM_THRESHOLDS))
    empirical_dot_pi = strict_frequency(dot, np.asarray(DOT_THRESHOLDS))

    support = np.empty((len(RADII), 36, 2))
    norm_outer = np.empty((len(RADII), 12, 2))
    for ir, rho in enumerate(RADII):
        widths = rho * np.sqrt(np.diag(fcov))
        support[ir, :, 0], support[ir, :, 1] = fmean-widths, fmean+widths
        for k in range(12):
            mu = fmean[3*k:3*k+3]
            block = fcov[3*k:3*k+3, 3*k:3*k+3]
            outer = rho*np.sqrt(np.linalg.eigvalsh(block)[-1])
            norm_outer[ir, k] = (max(0.0, np.linalg.norm(mu)-outer), np.linalg.norm(mu)+outer)

    ymean, ycov, ysamples = m@mean, m@cov@m.T, samples@m.T
    zmean, zcov, zsamples = t@ymean, t@ycov@t.T, ysamples@t.T
    diag = []
    for p, (i, j) in enumerate(PAIRS):
        for mode, name in enumerate(("E1", "B1")):
            si, sj = slice(6*i+3*mode, 6*i+3*mode+3), slice(6*j+3*mode, 6*j+3*mode+3)
            ci, cj, cij = ycov[si, si], ycov[sj, sj], ycov[si, sj]
            full = contrast_covariance(ci, cj, cij)
            zero_cross = ci+cj  # counterfactual only; no separate law is created
            diff = full-zero_cross
            diag.append({"contrast": f"bin{j}-bin{i}_{name}",
                         "full_cov_uasyr2": full.tolist(),
                         "zero_cross_counterfactual_cov_uasyr2": zero_cross.tolist(),
                         "signed_full_minus_zero_cov_uasyr2": diff.tolist(),
                         "full_component_sigma_uasyr": np.sqrt(np.diag(full)).tolist(),
                         "counterfactual_component_sigma_uasyr": np.sqrt(np.diag(zero_cross)).tolist(),
                         "full_eigen_uasyr2": np.linalg.eigvalsh(full).tolist(),
                         "counterfactual_eigen_uasyr2": np.linalg.eigvalsh(zero_cross).tolist(),
                         "full_rank": int(np.linalg.matrix_rank(full)),
                         "counterfactual_rank": int(np.linalg.matrix_rank(zero_cross)),
                         "spectral_scale_ratio_full_to_zero": float(np.sqrt(np.linalg.eigvalsh(full)[-1]/np.linalg.eigvalsh(zero_cross)[-1]))})

    result = {
        "task_id": "R24-DEPTH-IMAGES", "product": "tensor_scenario",
        "source_candidate": f"sha256:{digest(BASE/'tensor_bundle/MANIFEST.json')}",
        "region_id": REGION_ID, "radii": RADII, "functional_labels": LABELS,
        "parity": ["polar" if x.endswith("E1") else "axial" for x in LABELS],
        "units": {"vectors": "microarcsec/year", "covariance": "(microarcsec/year)^2", "E_dot_B": "(microarcsec/year)^2"},
        "full24": {"mean_uasyr": mean.tolist(), "cov_uasyr2": cov.tolist(), "retained_samples": 4096},
        "raw_intercepts": {"mean18_uasyr": mean[:18].tolist(), "cov18_uasyr2": cov[:18, :18].tolist(),
                           "sample_array": "IMAGES.npz:raw_intercept_sample_uasyr", "relation": "full24 first 18 coordinates; distinct from reported-bin Y18"},
        "linear_image": {"map_36x24": a.tolist(), "mean_36": fmean.tolist(), "cov_36x36": fcov.tolist(),
                         "exact_coordinate_support_5x36x2": support.tolist(), "bounds_order": ["min", "max"]},
        "nonlinear_image": {"norm_outer_5x12x2": norm_outer.tolist(), "norm_outer_kind": "conservative_spectral_triangle_not_sharp",
                            "empirical_norm_thresholds_uasyr": NORM_THRESHOLDS,
                            "empirical_strict_norm_Pi_12x6": empirical_norm_pi.tolist(),
                            "empirical_dot_thresholds_uasyr2": DOT_THRESHOLDS,
                            "empirical_strict_E_dot_B_Pi_6x3": empirical_dot_pi.tolist(),
                            "dot_definition": "signed polar E1 dot axial B1; pseudoscalar"},
        "depth": {"Y18_mean": ymean.tolist(), "Y18_cov": ycov.tolist(), "Z18_mean": zmean.tolist(), "Z18_cov": zcov.tolist(),
                  "M24_to_Y18": m.tolist(), "Y18_to_Z18": t.tolist(),
                  "rank_M": int(np.linalg.matrix_rank(m)), "rank_T": int(np.linalg.matrix_rank(t)),
                  "rank_delta_only": int(np.linalg.matrix_rank(t[6:]@m)),
                  "full24_carrier_retained": True, "physical_true_depth": None,
                  "reported_bin_centers_only": True},
        "cross_depth_discriminator": diag,
        "nonvacuity": {"positive_norm_lower_count_by_rho": (norm_outer[:, :, 0] > 0).sum(axis=1).tolist(),
                       "zero_contained_count_by_rho": (norm_outer[:, :, 0] == 0).sum(axis=1).tolist(),
                       "strict_empirical_norm_Pi_nontrivial_cells": int(((empirical_norm_pi > 0)&(empirical_norm_pi < 1)).sum()),
                       "strict_empirical_dot_Pi_nontrivial_cells": int(((empirical_dot_pi > 0)&(empirical_dot_pi < 1)).sum())},
        "law": {"kind": "retained_4096_joint_Gaussian_replicates", "source_seed": 20261023,
                "sample_size": 4096, "new_draws": 0, "Pi_rule": "strict >; finite empirical frequency only",
                "physical_law": None, "physical_Pi_interval": [0, 1], "unknown_mass": 1},
        "Q": {"computational_direct_sum_radius_uasyr": 10, "per_image_reference_norm_uasyr": 10,
              "per_image_reference_kind": "typed computational norm reference, not MES ceiling",
              "per_image_references": [{"functional": label, "norm_radius_uasyr": 10,
                                        "status": "COMPUTATIONAL_REFERENCE_ONLY"} for label in LABELS],
              "physical_MES_anchor": None},
        "F": {"finite_directional_support": "exact", "nonlinear_norm_bounds": "certified_conservative_outer",
              "common_region_source_occupancy": [
                  {"rho": row["rho"], "reference_occupancy_exact": row["reference_occupancy_exact"],
                   "reference_occupancy_empirical": row["reference_occupancy_empirical"]}
                  for row in source["F"]["region_family"]],
              "sample_occupancy": "source_common_region_only", "physical_occupancy": None},
        "G_F": {"status": "reported_bin_depth_diagnostic", "true_depth_status": "UNAVAILABLE"},
        "strata": {"signed_dot": "retained", "zero": "retained", "undefined_denominator": "UNDEFINED_NOT_ZERO",
                   "missing_cross_covariance": "UNAVAILABLE_NOT_ZERO_FILLED"},
        "claim_ceiling": "conditional functional depth images; no physical confidence, true-depth, tilt, source, R9, or original-acceptance promotion"
    }
    arrays = {"sample24_uasyr": samples, "raw_intercept_sample_uasyr": samples[:, :18],
              "Y18_sample_uasyr": ysamples, "Z18_sample_uasyr": zsamples,
              "functional_sample_uasyr": vectors, "norm_sample_uasyr": norms,
              "E_dot_B_sample_uasyr2": dot, "linear_map_36x24": a,
              "linear_mean_36": fmean, "linear_cov_36x36": fcov,
              "coordinate_support_5x36x2": support, "norm_outer_5x12x2": norm_outer,
              "empirical_norm_Pi_12x6": empirical_norm_pi, "empirical_dot_Pi_6x3": empirical_dot_pi}
    return result, arrays


if __name__ == "__main__":
    result, arrays = compute()
    (HERE/"RESULT.json").write_text(json.dumps(result, indent=2)+"\n")
    np.savez_compressed(HERE/"IMAGES.npz", **arrays)
    print(json.dumps({"task_id": result["task_id"], "product": result["product"],
                      "sample_shape": arrays["functional_sample_uasyr"].shape,
                      "nontrivial_norm_Pi_cells": result["nonvacuity"]["strict_empirical_norm_Pi_nontrivial_cells"]}))
