"""Finite coefficient diagnostics of the existing native matched split stream.

No map scan, SHT, covariance estimate, significance or physical attribution.
The native producer's full replay is required before inspecting split vectors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

PRODUCTS = ("full", "hm1", "hm2", "oe1", "oe2")
REGIONS = ("common", "three_way_intersection")


def read(path):
    data = Path(path).read_bytes()
    return json.loads(data), {"path": str(Path(path).resolve()),
                              "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def groups():
    # Each ell stores E(m0,cos1,sin1,...) then B(m0,cos1,sin1,...).
    e, b, offset = [], [], 0
    for ell in range(2, 6):
        size = 2*ell+1
        e.extend(range(offset, offset+size))
        b.extend(range(offset+size, offset+2*size))
        offset += 2*size
    return {"all": np.arange(64), "E": np.array(e), "B": np.array(b)}


def array(value, shape):
    a = np.asarray(value)
    if a.dtype.kind not in "fiu" or a.shape != shape or not np.isfinite(a).all():
        raise ValueError("FINITE_REAL_COEFFICIENT_SHAPE")
    return a.astype(float)


def compare(left, right):
    """Angle and optimal nonnegative scalar fit right -> left, in coefficient space."""
    x, y = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if (x.shape != y.shape or x.ndim != 1 or not np.isfinite(x).all()
            or not np.isfinite(y).all()):
        raise ValueError("FINITE_SAME_VECTOR_SHAPE")
    nx, ny = float(np.linalg.norm(x)), float(np.linalg.norm(y))
    if not np.isfinite([nx, ny]).all():
        raise ValueError("VECTOR_NORM_RANGE")
    if nx == 0 or ny == 0:
        return {"left_norm_K_CMB": nx, "right_norm_K_CMB": ny,
                "cosine": None, "angle_degrees": None,
                "nonnegative_gain_right_to_left": None,
                "nonnegative_fit_residual_fraction": None,
                "distance_K_CMB": float(np.linalg.norm(x-y))}
    cosine = float(np.clip((x/nx)@(y/ny), -1., 1.))
    gain = max(0., cosine)*nx/ny
    return {"left_norm_K_CMB": nx, "right_norm_K_CMB": ny,
            "cosine": cosine, "angle_degrees": float(np.degrees(np.arccos(cosine))),
            "nonnegative_gain_right_to_left": gain,
            "nonnegative_fit_residual_fraction": float(np.linalg.norm(x-gain*y)/nx),
            "distance_K_CMB": float(np.linalg.norm(x-y))}


def subjects(matrix):
    a = array(matrix, (64, 5))
    result = {product: a[:, i] for i, product in enumerate(PRODUCTS)}
    for label, i, j in (("HM", 1, 2), ("OE", 3, 4)):
        result[label+"_half_sum"] = (a[:, i]+a[:, j])/2
        result[label+"_half_difference"] = (a[:, i]-a[:, j])/2
        result["full_minus_"+label+"_mean"] = a[:, 0]-result[label+"_half_sum"]
    return result


def diagnostics(matrix):
    vectors = subjects(matrix)
    result = {}
    for name, index in groups().items():
        v = {key: value[index] for key, value in vectors.items()}
        energy = {key: float(value@value) for key, value in v.items()}
        denominator = energy["full"]
        result[name] = {
            "norms_nK_CMB": {key: float(np.linalg.norm(value))*1e9 for key, value in v.items()},
            "energy_ratios_to_full": {key: val/denominator if denominator else None
                                      for key, val in energy.items()},
            "HM_OE_half_difference_comparison": compare(v["HM_half_difference"], v["OE_half_difference"]),
            "HM_split_cosine": compare(v["hm1"], v["hm2"])["cosine"],
            "OE_split_cosine": compare(v["oe1"], v["oe2"])["cosine"],
            "HM_half_sum_vs_full": compare(v["HM_half_sum"], v["full"]),
            "OE_half_sum_vs_full": compare(v["OE_half_sum"], v["full"]),
        }
    return result


def analyze(native, anchor, bound):
    expected = {"schema": "htt.L01_native_matched_split_stream/1",
                "status": "PASS_NATIVE_MATCHED_SPLIT_ACCOUNTING", "products": list(PRODUCTS),
                "nside": 2048, "native_SHT_run": False, "beam_applied_again": False,
                "paper_gate": "NOT_READY_TO_SUBMIT"}
    if any(native.get(key) != value for key, value in expected.items()):
        raise ValueError("NATIVE_MATCHED_STREAM_CONTRACT")
    if native["source_window_sha256"] != anchor["native_window_sha256"]:
        raise ValueError("ANCHOR_SUPPORT_MISMATCH")
    replay = native["full_native_moment_replay"]
    if (set(replay) != set(REGIONS) or not all(np.isfinite(x) and 0 <= x <= 2e-9
                                              for x in replay.values())):
        raise ValueError("NATIVE_FULL_REPLAY_REQUIRED")
    result = native["result"]
    matrices = {key: array(value, (64, 5)) for key, value in result["matched_coefficients"].items()}
    if set(matrices) != set(REGIONS):
        raise ValueError("EXACT_MATCHED_REGIONS_REQUIRED")
    delta = matrices[REGIONS[1]]-matrices[REGIONS[0]]
    archived = array(result["matched_contrast"], (64, 5))
    np.testing.assert_allclose(delta, archived, rtol=2e-9, atol=0)
    raw = array(anchor["contrast_raw_K_CMB"], (64,))
    reconstructed = array(anchor["contrast_reconstructed_K_CMB"], (64,))
    original = {key: array(result["original_coefficients"][key], (64, 5)) for key in REGIONS}
    np.testing.assert_allclose((original[REGIONS[1]]-original[REGIONS[0]])[:, 0], raw,
                               rtol=2e-9, atol=1e-20)
    comparison = {}
    for name, index in groups().items():
        measured = compare(delta[index, 0], reconstructed[index])
        actual_lengths = {"anchor_norm": np.linalg.norm(raw[index]),
                          "matched_norm": np.linalg.norm(delta[index, 0]),
                          "reconstructed_norm": np.linalg.norm(reconstructed[index]),
                          "anchor_matched_distance": np.linalg.norm(raw[index]-delta[index, 0]),
                          "anchor_reconstructed_distance": np.linalg.norm(raw[index]-reconstructed[index])}
        for key, value in actual_lengths.items():
            np.testing.assert_allclose(value, bound["groups"][name]["input_lengths_K_CMB"][key],
                                       rtol=2e-9, atol=1e-20)
        interval = (bound["all_refined_using_orthogonal_E_B_blocks"] if name == "all"
                    else bound["groups"][name])["matched_reconstructed_angle_degrees_interval"]
        if not interval[0]-1e-6 <= measured["angle_degrees"] <= interval[1]+1e-6:
            raise ValueError("ACTUAL_ANGLE_OUTSIDE_PRIOR_SHARP_GEOMETRY")
        comparison[name] = {"matched_vs_native_L128": measured,
                            "matched_vs_direct_native": compare(delta[index, 0], raw[index]),
                            "prior_bound_input_lengths_reproduced": True,
                            "previous_conditional_angle_interval_degrees": interval,
                            "inside_previous_interval": True}
    return {"schema": "htt.L01_executed_matched_split_diagnostics/1",
            "owner": "obsstat", "scope": "finite same-sky processing diagnostics",
            "status": "DIAGNOSTIC_ONLY", "claim_tier": "C0", "non_claim_bearing": True,
            "transfer_source": "none", "sky_support_status": "SOURCE_MATCHED_FIXED_NATIVE_WINDOW",
            "null_mock_status": "NOT_QUALIFIED", "independent_sky_count": 1,
            "p_value": None, "noise_covariance": None, "noise_debiasing": False,
            "coefficient_convention": "real ell2..5, E then B within ell; sin=-sqrt(2)*Im(alm)",
            "matched_contrast": diagnostics(delta),
            "matched_region_fits": {key: diagnostics(value) for key, value in matrices.items()},
            "full_comparison": comparison,
            "native_checks": {"selected_pixels": native["raw_moments"]["selected_pixels"],
                              "full_native_moment_replay": replay,
                              "shell_identity_relative": result["shell_identity_relative"],
                              "split_linearity_relative": result["split_linearity_relative"],
                              "seconds": native["seconds"]},
            "limitations": ["One sky and correlated products; split energies are not noise fractions.",
                            "Coefficient B is a finite masked fit, not identified cosmic B.",
                            "No additional beam operation; inherited delivered-map beam remains.",
                            "Raw inputs are not truncated to ell<=5; this labels the fitted basis.",
                            "No infinite harmonic-tail bound or physical null calibration.",
                            "L01 remains pending; independent review and full acceptance still required."],
            "node_acceptance": "PARTIAL_EXECUTION_L01_PENDING",
            "paper_gate": "NOT_READY_TO_SUBMIT"}, matrices, delta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native", type=Path, required=True)
    ap.add_argument("--anchor", type=Path, required=True)
    ap.add_argument("--bound", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    objects, identities = [], []
    for path in (args.native, args.anchor, args.bound):
        obj, identity = read(path)
        objects.append(obj); identities.append(identity)
    if objects[0]["input_evidence"]["native_report_sha256"] != identities[1]["sha256"]:
        raise ValueError("NATIVE_ANCHOR_BYTE_LINK_MISMATCH")
    report, matrices, delta = analyze(*objects)
    report["sources"] = identities
    report["generating_code_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir/"MATCHED_SPLIT_DIAGNOSTICS.json"
    npz_path = args.out_dir/"MATCHED_SPLIT_COEFFICIENTS.npz"
    if json_path.exists() or npz_path.exists():
        raise FileExistsError("CREATE_ONLY_OUTPUT_EXISTS")
    with npz_path.open("xb") as stream:
        np.savez_compressed(stream, **matrices, matched_contrast=delta, products=np.array(PRODUCTS))
    with json_path.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({"out": str(json_path), "checks": report["native_checks"],
                      "matched_contrast": report["matched_contrast"]}, indent=2))


if __name__ == "__main__":
    main()
