#!/usr/bin/env python3
"""Run a source-locked, conditional ell6..32 SMICA mask-geometry study."""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE))
from extended_power_envelope import (ELLS, shell_slice, joined_operator,
    independent_shell_covariance, sharp_ellipsoid, shared_coordinate_toy,
    cross_shell_agnostic_std_bound, scenario_templates)

LOOP9 = ROOT / "docs/research_program/theory_obs_application_20261015/loop9_smica_finite_response"
LOOP12 = HERE.parent
OLD_NPZ = LOOP9 / "results/response_v1/baseline_response_matrices.npz"
OLD_JSON = LOOP9 / "results/response_v1/result.json"
NEW_NPZ = LOOP12 / "results/ell17_32_source_v1/ell17_32_mask_response.npz"
NEW_JSON = LOOP12 / "results/ell17_32_source_v1/result.json"
EXPECTED = {
    OLD_NPZ: "a9aaeb393deba03c97ecf45bf4e1ab74e98e3a8747de7c4bc7a96bff27014007",
    OLD_JSON: "85b82fac9e108280d1386bee0ba24cceb8e3e3d7a6a3bb4b4ca5559d285f9248",
    NEW_NPZ: "91f496ca7cd1cbaed65153c64d83cf7abf84b21c141d8955d0cd8e07ed480a35",
    NEW_JSON: "40a1fcfc4efde08bc94714fadc19ee89ac1d8202830ce767d0cf8f4d53b7e264",
}


def digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def source_gate() -> tuple[np.ndarray, dict[str, str], dict]:
    for path, expected in EXPECTED.items():
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f"frozen finite response source SHA mismatch: {path}")
    old_result = json.loads(OLD_JSON.read_text())
    new_result = json.loads(NEW_JSON.read_text())
    if (old_result["cases"][0]["selected_pixels"] != 26846 or
            new_result["source_selected_pixels"] != 26846 or
            new_result["new_shell_ell_range"] != [17, 32] or
            new_result["new_coefficient_count"] != 800 or
            new_result["same_source_replay_old_6_16_max_abs_error"] > 1e-12 or
            new_result["harmonic_sign_and_order_max_abs_error"] > 1e-12):
        raise ValueError("PR536/537 selected mask, ordering or replay gate failed")

    # Reuse the published PR536 gate. This independently rehashes the actual
    # 2 GB full map, official common/HM/OE masks, K1 cache and Loop5 references.
    sys.path.insert(0, str(LOOP9))
    spec = importlib.util.spec_from_file_location("htt_c8_loop9_source", LOOP9 / "run.py")
    if spec is None or spec.loader is None:
        raise ImportError("published Loop9 source gate unavailable")
    prior = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prior)
    raw_hashes = prior.source_gate()
    for path in (prior.COMMON, prior.HM, prior.OE, prior.CACHE):
        if new_result["source_file_sha256"].get(str(path)) != raw_hashes[str(path)]:
            raise ValueError(f"PR537 source mask/cache differs from PR536: {path}")
    fine, coverage, confidence = prior.selection()
    selected = (confidence > .5) & (coverage >= .995)
    if selected.shape != (49152,) or int(selected.sum()) != 26846:
        raise ValueError("reconstructed Loop5/PR536/537 support mismatch")
    mask_sha = sha256(selected.astype(np.uint8).tobytes()).hexdigest()
    with np.load(OLD_NPZ, allow_pickle=False) as source:
        old_full = np.asarray(source["K_full_36x253"], float)
        old23 = np.asarray(source["K_ell23_12x253"], float)
        old32 = np.asarray(source["K_ell2to5_32x253"], float)
    with np.load(NEW_NPZ, allow_pickle=False) as source:
        new_full = np.asarray(source["K_full_36x800"], float)
        new23 = np.asarray(source["K_ell23_12x800"], float)
        new32 = np.asarray(source["K_ell2to5_32x800"], float)
    if (old_full.shape != (36,253) or new_full.shape != (36,800) or
            not np.array_equal(old23, old_full[4:16]) or
            not np.array_equal(old32, old_full[4:36]) or
            not np.array_equal(new23, new_full[4:16]) or
            not np.array_equal(new32, new_full[4:36])):
        raise ValueError("frozen low multipole slices do not match full operators")
    combined = joined_operator(old32, new32)
    for ell in ELLS:
        width = shell_slice(ell).stop - shell_slice(ell).start
        if width != 2 * ell + 1:
            raise ValueError("real harmonic shell ordering/count mismatch")
    hashes = {str(path): expected for path, expected in EXPECTED.items()}
    hashes.update(raw_hashes)
    return combined, hashes, {"selected_pixels": int(selected.sum()),
                             "selected_ring_nside64_mask_sha256": mask_sha,
                             "pr537_replay_max_abs_error": new_result["same_source_replay_old_6_16_max_abs_error"],
                             "pr537_harmonic_max_abs_error": new_result["harmonic_sign_and_order_max_abs_error"]}


def execute(output: Path) -> dict:
    if output.exists():
        raise FileExistsError("create-only result directory required")
    k, hashes, selection = source_gate()
    saved = {"K_ell2to5_32x1053": k}
    cases = []
    for name, power in scenario_templates().items():
        cov = independent_shell_covariance(k, power)
        eigen = np.linalg.eigvalsh(cov)
        radii = {ell: float(np.sqrt((2*ell+1) * power[ell])) for ell in ELLS}
        envelope = sharp_ellipsoid(k, radii)
        toy = {}
        for rho in (0., .25, .5, 1.):
            current = shared_coordinate_toy(k, power, rho)
            toy[str(rho)] = {"trace": float(np.trace(current)),
                             "leading_std": float(np.sqrt(max(np.linalg.eigvalsh(current)[-1], 0.)))}
        shell_trace = {str(ell): float(power[ell] * np.linalg.norm(k[:, shell_slice(ell)], "fro")**2)
                       for ell in ELLS}
        record = {"name": name, "input_class": "HYPOTHETICAL_SCENARIO",
                  "C_l_units": "DECLARED_ARBITRARY_VARIANCE_PER_REAL_HARMONIC_COORDINATE",
                  "C_l": {str(ell): float(power[ell]) for ell in ELLS},
                  "independent_shell_assumption": "Cov(a_l,a_lprime)=delta_llprime C_l I; no observed C_l supplied",
                  "output_covariance_trace": float(np.trace(cov)),
                  "output_leading_std": float(np.sqrt(max(eigen[-1], 0.))),
                  "per_shell_trace": shell_trace,
                  "trace_old_6_16": float(sum(shell_trace[str(ell)] for ell in range(6,17))),
                  "trace_new_17_32": float(sum(shell_trace[str(ell)] for ell in range(17,33))),
                  "ellipsoid_radii": "R_l=sqrt((2l+1)C_l), sum ||a_l||^2/R_l^2 <=1",
                  "ellipsoid_gram_encoding": "G=(gram_scale)^2 * saved_normalized_gram",
                  "ellipsoid_gram_scale": envelope["gram_scale"],
                  "sharp_ellipsoid_bound": envelope["bound"],
                  "ellipsoid_witness_constraint": envelope["witness_constraint"],
                  "ellipsoid_witness_achieved": envelope["achieved"],
                  "manufactured_shared_coordinate_toy": toy,
                  "cross_shell_agnostic_std_bound_given_declared_marginals": cross_shell_agnostic_std_bound(k, power)}
        cases.append(record)
        saved[f"C_{name}"] = cov
        saved[f"ELLIPSOID_NORMALIZED_GRAM_{name}"] = envelope["normalized_gram"]
    result = {"schema": "htt.C8_SMICA_ELL6_32_POWER_ENVELOPE_LOCAL/1",
              "owner": "obsstat", "claim_tier": "SOURCE_CONDITIONAL_MASK_GEOMETRY_SCENARIOS_ONLY",
              "source_sha256": hashes, "source_selected_mask": selection,
              "operator_layout": "ell2..5 retained 32 rows, ell6..32 real harmonics 1053 columns; first 253 ell6..16, next 800 ell17..32",
              "operator_shape": list(k.shape),
              "operator_norm": float(np.linalg.norm(k, 2)),
              "source_map_used_for_K": "NO; mask geometry only, map bytes independently authenticated",
              "empirical_C_l": "UNKNOWN_NOT_SUPPLIED", "forecast_C_l": "UNKNOWN_NOT_SUPPLIED",
              "actual_high_mode_amplitudes": "UNKNOWN",
              "cross_shell_and_cross_product_covariance": "UNKNOWN",
              "beam_foreground_component_separation_E2E": "UNKNOWN",
              "ell_gt32_tail": "UNKNOWN", "physical_covariant_EGS": "HOLD",
              "Bianchi_geometry_frame_shear_tilt": "HOLD",
              "cases": cases}
    output.mkdir(parents=True)
    np.savez_compressed(output / "conditional_covariances.npz", **saved)
    with (output / "result.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = execute(args.output)
    print(json.dumps({"status": "SOURCE_LOCKED_CONDITIONAL_ENVELOPE",
                      "operator_norm": result["operator_norm"],
                      "scenario_count": len(result["cases"])}))
