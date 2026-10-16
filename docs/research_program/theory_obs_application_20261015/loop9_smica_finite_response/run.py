#!/usr/bin/env python3
"""Execute source-locked NSIDE64 full-SMICA finite mask response."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

import healpy as hp
import numpy as np
import scipy
from astropy.io import fits

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "htt"))
sys.path.insert(0, str(ROOT / "htt/src"))

from finite_response import (fit_response, injection_checks, json_dump_create,
                             fit_vector, per_shell, sha256, source_result, spectrum)
from obsstat.r7_cmb_product_response import pixel_fit_geometry, real_design

RAW = Path("/mnt/extdrive/workdir/raw")
MAP = RAW / "planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits"
COMMON = RAW / "planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
HM = RAW / "planck_pr3_smica_hm_20261015/COM_Mask_CMB-HM-Misspix-Mask-Int_2048_R3.00.fits"
OE = RAW / "planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-OE-Misspix-Mask-Int_2048_R3.00.fits"
CACHE = ROOT / "workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz"
LOOP5 = ROOT / "docs/research_program/theory_obs_application_20261015/loop8_mes_eps_20261016/inputs/loop5"

EXPECTED = {
    MAP: "60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac",
    COMMON: "23f49a3479073408b83a7f1bb2cca490d9be7f934b2e0e891524b6a1d06a5fc4",
    HM: "f4fd909734d80fb80214018b3ef9b44a378a4d04418337786c48f6d388dfb2a0",
    OE: "ecb39152ad5b93ea309baf396aad404a062edd6745a30c0b941b3556ca28aff9",
    CACHE: "86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb",
    LOOP5 / "result.json": "abbc49075634899499f1ba615c5f2ba0192e4f949d3d6cc8bfe2171bf862312a",
    LOOP5 / "retained_common_support_coefficients.npz": "900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459",
}


def source_gate() -> dict[str, str]:
    found = {}
    for path, expected in EXPECTED.items():
        if not path.is_file():
            raise FileNotFoundError(f"source absent: {path}")
        actual = sha256(path)
        if actual != expected:
            raise ValueError(f"source SHA mismatch: {path}: {actual} != {expected}")
        found[str(path)] = actual
    return found


def native_mask(path: Path, column: str) -> np.ndarray:
    """Loop5 native NESTED binary mask convention, in this publishable unit."""
    if path.stat().st_size != 201335040:
        raise ValueError(f"official Planck mask size mismatch: {path}")
    with fits.open(path, memmap=True) as ff:
        h = ff[1]
        if (h.header.get("NSIDE") != 2048 or
                h.header.get("ORDERING") != "NESTED" or
                column not in h.columns.names):
            raise ValueError(f"mask geometry/field mismatch: {path}")
        return np.asarray(h.data[column]) > .5


def coarse_masked_mean(values, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Loop5 contiguous NESTED child mean and coverage, returned as RING."""
    nout, children = 49152, 1024
    if valid.shape != (nout * children,):
        raise ValueError("NSIDE2048 fine mask required")
    coarse = np.empty(nout, float)
    coverage = np.empty(nout, float)
    for start in range(0, nout, 384):
        stop = min(nout, start + 384)
        block = np.asarray(values[start*children:stop*children], dtype=float).reshape(stop-start, children)
        mask = valid[start*children:stop*children].reshape(stop-start, children)
        mask = mask & np.isfinite(block) & (block > -1e20)
        count = mask.sum(axis=1)
        coverage[start:stop] = count / children
        numerator = np.sum(np.where(mask, block, 0.), axis=1, dtype=float)
        coarse[start:stop] = np.divide(numerator, count, out=np.full(stop-start, np.nan), where=count>0)
    return hp.reorder(coarse, n2r=True), hp.reorder(coverage, n2r=True)


def source_temperature(path: Path, fine_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Read the released K_CMB map with Loop5's masked downgrade."""
    if path.stat().st_size < 402_000_000:
        raise ValueError(f"unqualified FITS size: {path}")
    with fits.open(path, memmap=True) as ff:
        h = ff[1]
        if (h.header.get("NSIDE") != 2048 or
                h.header.get("ORDERING") != "NESTED" or
                h.header.get("TUNIT1") != "K_CMB" or
                "I_STOKES" not in h.columns.names):
            raise ValueError(f"unqualified Planck release header: {path}")
        temperature, coverage = coarse_masked_mean(h.data["I_STOKES"], fine_mask)
    return temperature * 1e6, coverage


def selection(coverage_floor: float = .995):
    fine = native_mask(COMMON, "TMASK") & native_mask(HM, "TMASK") & native_mask(OE, "TMASK")
    # NESTED 2048 children are contiguous in each NSIDE64 parent; reorder
    # the exact integer coverage fraction to RING, matching Loop5's helper.
    fraction = hp.reorder(fine.reshape(49152, 1024).sum(axis=1) / 1024., n2r=True)
    with np.load(CACHE, allow_pickle=False) as z:
        confidence = np.asarray(z["common_mask"], float)
    if confidence.shape != (49152,) or not np.isfinite(confidence).all():
        raise ValueError("K1 common temperature confidence mismatch")
    return fine, fraction, confidence


def harmonic_conventions(directions: np.ndarray, full_design: np.ndarray,
                         old_design: np.ndarray) -> dict:
    error = float(np.max(np.abs(full_design[:, :36] - old_design)))
    if error > 1e-13:
        raise ValueError("Loop5 harmonic design mismatch")
    c = np.sqrt(3 / (4 * np.pi))
    checks = [full_design[:, 0] - 1 / np.sqrt(4 * np.pi),
              full_design[:, 2] + c * directions[:, 0],
              full_design[:, 3] + c * directions[:, 1],
              full_design[:, 1] - c * directions[:, 2]]
    sign_error = max(float(np.max(np.abs(x))) for x in checks)
    if sign_error > 1e-13:
        raise ValueError("real harmonic sign/normalization mismatch")
    return {"first36_loop5_max_abs_delta": error,
            "ell0_ell1_cartesian_max_abs_delta": sign_error,
            "ordering": "ell,m0,sqrt2 Re Y_lm,sqrt2 Im Y_lm; m=1..ell",
            "scipy_condon_shortley_phase": True, "healpix_order": "RING_NSIDE64"}


def run(output: Path) -> dict:
    if output.exists():
        raise FileExistsError("create-only output directory required")
    source_hashes = source_gate()
    fine, coverage, confidence = selection()
    baseline = (confidence > .5) & (coverage >= .995)
    if int(baseline.sum()) != 26846:
        raise ValueError(f"Loop5 exact support mismatch: {baseline.sum()}")
    directions, old_design = pixel_fit_geometry()
    design = real_design(directions, ell_max=16)
    conventions = harmonic_conventions(directions, design, old_design)
    with np.load(LOOP5 / "retained_common_support_coefficients.npz", allow_pickle=False) as z:
        names = tuple(z["names_T"].tolist())
        old = np.asarray(z["coeff_T"], float)
    if names.count("SMICA_FULL") != 1 or old.shape != (9, 32):
        raise ValueError("Loop5 reference shape/name mismatch")
    temperature, map_coverage = source_temperature(MAP, fine)
    if np.any(map_coverage[baseline] < .995 - 1e-12):
        raise ValueError("full SMICA selected-pixel coverage mismatch")
    cases = [("loop5_mask_fit5", .5, .995, 5),
             ("confidence_0p8_fit5", .8, .995, 5),
             ("coverage_1p0_fit5", .5, 1., 5),
             ("loop5_mask_fit8", .5, .995, 8),
             ("loop5_mask_fit12", .5, .995, 12)]
    summaries = []
    matrices = {}
    base_retained = None
    base_norm = None
    for label, threshold, floor, fit_lmax in cases:
        selected = (confidence > threshold) & (coverage >= floor)
        response = fit_response(design, selected, fit_lmax)
        retained = fit_vector(response, temperature[selected])[4:36]
        kfull = response["K_full_fit"]
        k23 = response["K_ell23"]
        k32 = response["K_ell2to5"]
        rec = {"case": label, "confidence_threshold": threshold,
               "coverage_floor": floor, "fit_lmax": fit_lmax,
               "selected_pixels": response["n_selected"],
               "weighting": "binary W=1 selected; W=0 excluded",
               "low_design_shape": [response["n_selected"], (fit_lmax + 1) ** 2],
               "high_design_shape": [response["n_selected"], 253],
               "low_rank": response["rank_low"],
               "low_condition": response["condition"],
               "low_identity_residual": response["identity_residual"],
               "K_full_fit": spectrum(kfull), "K_ell23": spectrum(k23),
               "K_ell2to5": spectrum(k32),
               "per_shell_ell23": per_shell(k23),
               "per_shell_ell2to5": per_shell(k32)}
        if label == "loop5_mask_fit5":
            rec["actual_smica_regression"] = source_result(
                response, temperature[selected], old[names.index("SMICA_FULL")])
            rec["injection"] = injection_checks(response)
            base_retained = retained
            base_norm = rec["K_ell2to5"]["operator_norm"]
            matrices = {"K_full_36x253": kfull, "K_ell23_12x253": k23,
                        "K_ell2to5_32x253": k32,
                        "SMICA_FULL_retained_32_microK": retained}
        else:
            rec["retained_delta_from_loop5_baseline_norm_microK"] = float(
                np.linalg.norm(retained - base_retained))
            rec["K_ell2to5_norm_ratio_to_baseline"] = float(
                rec["K_ell2to5"]["operator_norm"] / base_norm)
        summaries.append(rec)
        del response
    result = {"schema": "htt.C8_SMICA_FULL_MASK_FINITE_RESPONSE/1",
              "owner": "obsstat", "claim_tier": "SOURCE_CONDITIONAL_FINITE_HARMONIC_RESPONSE",
              "transfer_source": "released_planck_pr3_full_smica_processed_map",
              "source_sha256": source_hashes, "source_base_head": "13d8d85fa470d645d008986e8f77d8d0f70fdf54",
              "parent_pr535_head": "2752a927c191f296139ca61483e9f4f31cf4335a",
              "units": "thermodynamic microK for observed map; K dimensionless",
              "assumptions": ["same selected NSIDE64 RING pixels as Loop5",
                              "unweighted simultaneous OLS; real orthonormal harmonics",
                              "finite ell6..16 injected pixel harmonics only"],
              "harmonic_conventions": conventions,
              "scope_limits": {"ell_gt16_tail": "UNKNOWN", "actual_high_mode_norm": "UNKNOWN",
                               "beam_component_separation_transfer": "UNKNOWN",
                               "foreground_residual_e2e_covariance": "UNKNOWN",
                               "cosmological_residual_epsilon1": "UNKNOWN",
                               "almost_egs_covariant_time_space_derivatives": "UNKNOWN",
                               "observer_to_bianchi_geometry_frame_response": "UNKNOWN",
                               "physical_egs_mes_admission": "HOLD"},
              "finite_bound": "||delta a_L||_2 <= ||K_LH||_2 ||a_H||_2 on ell6..16 only",
              "cases": summaries,
              "environment": {"python": sys.version.split()[0], "numpy": np.__version__,
                              "scipy": scipy.__version__, "healpy": hp.__version__,
                              "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS", "UNSET")}}
    output.mkdir(parents=True)
    np.savez_compressed(output / "baseline_response_matrices.npz", **matrices)
    json_dump_create(output / "result.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = run(args.output)
    print(json.dumps({"status": "FINITE_RESPONSE_COMPUTED",
                      "baseline_pixels": payload["cases"][0]["selected_pixels"],
                      "K32_norm": payload["cases"][0]["K_ell2to5"]["operator_norm"]}))
