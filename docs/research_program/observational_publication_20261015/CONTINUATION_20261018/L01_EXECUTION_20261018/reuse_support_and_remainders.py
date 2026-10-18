"""Reuse exact T/EB coefficients and native finite-band checkpoints for L01.

The legacy RING64 T/EB fit, processed RING64 band fit, and matched native fit
are named separately because their supports and estimator objectives differ.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

from analyze_matched_splits import PRODUCTS, REGIONS, compare, groups, read

PROGRAMME = Path(__file__).resolve().parents[2]
SOURCE_NPZ_SHA = "900e6c6fa04a6313f63753747d89e7059486bdeb88d51c91d895fcc8b4e09459"


def finite_bands(contrast):
    keys = ("total_K_CMB", "low_2_to_5_K_CMB", "mid_6_to_8_K_CMB", "tail_9_to_L_K_CMB")
    v = [np.asarray(contrast[key], dtype=float) for key in keys]
    if any(a.shape != (64,) or not np.isfinite(a).all() for a in v):
        raise ValueError("FINITE_64_BAND_VECTORS_REQUIRED")
    scale = max(sum(np.linalg.norm(a) for a in v), np.finfo(float).tiny)
    closure = float(np.linalg.norm(v[0]-v[1]-v[2]-v[3])/scale)
    if closure > 2e-9:
        raise ValueError("FINITE_BAND_CLOSURE")
    result = {"closure_relative": closure}
    for name, ix in groups().items():
        total, low, mid, tail = [a[ix] for a in v]
        result[name] = {"norms_nK_CMB": dict(zip(("total", "low_2_5", "mid_6_8", "tail_9_L"),
                                                  [float(np.linalg.norm(a))*1e9 for a in (total, low, mid, tail)])),
                        "mid_tail_interference_nK_CMB2": float(2*(mid@tail))*1e18,
                        "mid_vs_tail": compare(mid, tail)}
    return result


def temperature_diagnostics(coefficients, names):
    a = np.asarray(coefficients, dtype=float)
    if a.shape != (9, 32) or not np.isfinite(a).all() or len(set(names)) != 9:
        raise ValueError("NINE_T_SOURCE_PRODUCTS_REQUIRED")
    mapping = dict(zip(names, a))
    full = mapping["SMICA_FULL"]
    out = {"product_norms_microK": {key: float(np.linalg.norm(value)) for key, value in mapping.items()}}
    for split in ("HM", "OE"):
        left, right = [mapping["SMICA_"+split+str(i)] for i in (1, 2)]
        mean, difference = (left+right)/2, (left-right)/2
        out[split] = {"half_sum_norm_microK": float(np.linalg.norm(mean)),
                      "half_difference_norm_microK": float(np.linalg.norm(difference)),
                      "full_minus_mean_norm_microK": float(np.linalg.norm(full-mean)),
                      "split_cosine": compare(left, right)["cosine"]}
    out["independent_sky_count"] = 1
    out["noise_fraction_or_covariance_inferred"] = False
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.out.exists(): raise FileExistsError(args.out)
    repo = PROGRAMME.parents[2]
    npz = repo/"docs/research_program/htt_mes_eps_loop9_20261015/inputs/retained_common_support_coefficients.npz"
    if hashlib.sha256(npz.read_bytes()).hexdigest() != SOURCE_NPZ_SHA:
        raise ValueError("ORIGINAL_T_EB_SOURCE_CHANGED")
    with np.load(npz, allow_pickle=False) as z:
        names_t, names_p = z["names_T"].tolist(), z["names_EB"].tolist()
        temp = temperature_diagnostics(z["coeff_T"], names_t)
        if z["coeff_EB"].shape != (8, 64) or names_p != [x for x in names_t if x != "SMICA_noSZ_FULL"]:
            raise ValueError("ORIGINAL_EB_PRODUCT_IDENTITY")
    ledger, ledger_identity = read(PROGRAMME/"L01_20261016/results/source_v1/L01_T_EB_SOURCE_LEDGER.json")
    receipt, receipt_identity = read(args.root/"provenance/L01_NATIVE_PR3_POL_K64x90_v2.json")
    anchor, anchor_identity = read(args.root/"provenance/L01_NATIVE_PIXEL_RESIDUAL_full_20261017T135250Z.json")
    probe, probe_identity = read(args.root/"provenance/L01_LOW_SOURCE_WINDOW_RESPONSE_20261017T150345Z.json")
    if probe["native_report_sha256"] != anchor_identity["sha256"]:
        raise ValueError("RESIDUAL_SOURCE_LINK_MISMATCH")
    if ledger["input_sha256"][npz.name] != SOURCE_NPZ_SHA:
        raise ValueError("ORIGINAL_SOURCE_LEDGER_MISMATCH")
    sys.path.insert(0, str(PROGRAMME/"L01_R8_C8_TWO_MASK_STABILITY_20261017/src"))
    import l01_native_residual_projection as previous
    s = {key: np.asarray(anchor["solver_states"][key]["gram"])-np.asarray(probe["hole_moments"][key]) for key in REGIONS}
    dual, gain_meta = previous.nested_dual_gram(s[REGIONS[0]], s[REGIONS[1]])
    residual_envelope = {}
    for name, ix in groups().items():
        gain = float(np.sqrt(max(0., np.linalg.eigvalsh(dual[np.ix_(ix, ix)])[-1])))
        residual_envelope[name] = {"operator_gain": gain,
                                  "restricted_residual_envelope_nK_CMB": gain*anchor["residual_map_norm_K_CMB"]*1e9}
    checkpoints, checkpoint_sources = {}, []
    for cutoff in (32, 64, 128):
        checkpoints[str(cutoff)] = {}
        for product in PRODUCTS:
            obj, identity = read(args.root/f"provenance/L01_SMICA_WINDOWED_QU_L{cutoff}/{product}.json")
            if (obj["contract"]["native_window_sha256"] != anchor["native_window_sha256"]
                    or obj["contract"]["product"] != product or obj["contract"]["lmax"] != cutoff):
                raise ValueError("CHECKPOINT_SUPPORT_OR_CUTOFF_MISMATCH")
            checkpoints[str(cutoff)][product] = finite_bands(obj["result"]["two_mask_difference"])
            checkpoint_sources.append(identity)
    beam, beam_identity = read(args.root/"provenance/L01_SAME_SKY_WITH_SMICA_BEAM_20261017T073713Z.json")
    result = {"schema": "htt.L01_support_remainder_reuse/1", "owner": "obsstat",
              "status": "DIAGNOSTIC_ONLY", "claim_tier": "C0", "non_claim_bearing": True,
              "transfer_source": "none", "source_coefficients_sha256": SOURCE_NPZ_SHA,
              "support_crosswalk": {
                  "original_T": {"products": names_t, "order": "RING64", "selected_pixels": 26846},
                  "original_EB": {"products": names_p, "order": "RING64", "selected_pixels": 30021},
                  "native_PMASK_coarse": {key: {"order": "RING64", "selected_pixels": receipt[key]["selected_pixels"],
                                                "mask_sha256": receipt[key]["ring64_binary_mask_sha256"]} for key in REGIONS},
                  "native_matched": {"order": "NESTED2048", "window_sha256": anchor["native_window_sha256"],
                                     "counts_reference": "current matched stream raw_moments.selected_pixels"},
                  "different_supports_are_interchangeable": False},
              "original_T_processing": temp,
              "original_T_finite_operator_reused": ledger["temperature_source_geometry"],
              "processed_RING64_finite_bands": checkpoints,
              "native_matched_finite_residual_envelope": {
                  "groups": residual_envelope, "gain_metadata": gain_meta,
                  "unrestricted_saved_residual_norm_K_CMB": anchor["residual_map_norm_K_CMB"],
                  "domain": "matched support U_c=M_c W; solid-angle-weighted Q/U norm",
                  "comparison": "D_matched(raw - W*synthesized_saved_L128)",
                  "norm_input": "Restriction by binary W cannot increase the saved M_c residual norm.",
                  "actual_matched_reconstruction_error_measured": False,
                  "pure_ell_gt128_tail_bound": False,
                  "infinite_physical_tail_bound": False,
                  "interpretation": "Conservative finite-map envelope; not attribution or covariance."},
              "beam_reused": {"status": beam["beam_status"], "beam": beam["beam"],
                              "not_full_component_separation_or_E2E_response": True},
              "sources": [ledger_identity, receipt_identity, anchor_identity, probe_identity, beam_identity]+checkpoint_sources,
              "generating_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "new_map_scan": False, "new_SHT": False, "p_value": None,
              "paper_gate": "NOT_READY_TO_SUBMIT",
              "remaining_runnable": ["Actual matched reconstruction RHS requires an additional W-weighted moment, not stored in the original native residual report.",
                                     "Reconstruct original T mask/operator source links if extending the original T estimator; nine retained T vectors are already reusable."],
              "unqualified_physical_inputs": ["Component-separation/foreground/end-to-end null law", "Physical all-ell tail prior if a physical bound is requested"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({"out": str(args.out), "support_crosswalk": result["support_crosswalk"],
                      "matched_residual_envelope": residual_envelope}, indent=2))


if __name__ == "__main__": main()
