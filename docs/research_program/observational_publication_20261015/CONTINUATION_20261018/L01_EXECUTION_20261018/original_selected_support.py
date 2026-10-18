"""Finite native-mask bridge back to the original 30,021-pixel EB support.

Reconstructs the historical AND-before-coarsening coverage rule, checks actual
spin-2 injections, and projects existing L128 checkpoints on that same support.
No raw map refit, new forward SHT, beam deconvolution or null calibration.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.linalg import qr, solve_triangular

from analyze_matched_splits import PRODUCTS, read

PROGRAMME = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROGRAMME/"L01_R8_C8_TWO_MASK_STABILITY_20261017/src"))
import l01_smica_processed_bands as producer
from spin2_finite import block_design, response_from_design
from l01_k_spectral_certificate import inspect_operator


def parent_coverage(nested_window, nside_in=2048, nside_out=64):
    """Exact original native-child valid fraction, before the .995 threshold."""
    w = np.asarray(nested_window)
    if (w.dtype != np.bool_ or nside_in < nside_out or nside_in % nside_out
            or w.shape != (12*nside_in*nside_in,)):
        raise ValueError("NESTED_MASK_COVERAGE_SHAPE")
    ratio = (nside_in//nside_out)**2
    return w.reshape(-1, ratio).sum(axis=1)/ratio


def high_alms(coefficients, hp):
    a = np.asarray(coefficients)
    if a.shape != (90,) or not np.isfinite(a).all():
        raise ValueError("FINITE_REAL_HIGH90")
    out = np.zeros((2, hp.Alm.getsize(8)), dtype=complex)
    offset = 0
    for ell in range(6, 9):
        size = 2*ell+1
        for field in range(2):
            c = a[offset:offset+size]; offset += size
            out[field, hp.Alm.getidx(8, ell, 0)] = c[0]
            for m in range(1, ell+1):
                out[field, hp.Alm.getidx(8, ell, m)] = (c[2*m-1]-1j*c[2*m])/np.sqrt(2.)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    json_path = args.out_dir/"ORIGINAL_SELECTED_SUPPORT_RESPONSE.json"
    npz_path = args.out_dir/"ORIGINAL_SELECTED_SUPPORT_RESPONSE.npz"
    if json_path.exists() or npz_path.exists(): raise FileExistsError("CREATE_ONLY_OUTPUT_EXISTS")
    import healpy as hp
    receipt_path = args.root/"provenance/L01_NATIVE_PR3_POL_K64x90_v2.json"
    receipt, _ = producer.verify_receipt(receipt_path)
    window, _, window_sha = producer.read_windows(args.root, hp, receipt)
    coverage = hp.reorder(parent_coverage(window), n2r=True)
    mask = coverage >= .995
    if int(mask.sum()) != 30021:
        raise ValueError("ORIGINAL_SELECTED_EB_SUPPORT_COUNT_NOT_REPRODUCED")
    print(json.dumps({"phase": "ORIGINAL_SELECTED_SUPPORT_RECONSTRUCTED", "pixels": int(mask.sum()),
                      "native_window_sha256": window_sha}), flush=True)
    theta, phi = hp.pix2ang(64, np.arange(hp.nside2npix(64)), nest=False)
    low = block_design(theta, phi, 2, 5)
    high = block_design(theta, phi, 6, 8)
    K, meta = response_from_design(low, high, mask)
    if abs(meta["low_condition"]-3.1309622770574452) > 1e-10:
        raise ValueError("ORIGINAL_LOW_DESIGN_CONDITION_NOT_REPRODUCED")
    operator = inspect_operator(K)
    projector = producer.Projector.from_design(low, mask)
    controls = {}
    for seed in (101, 203):
        coefficients = np.random.default_rng(seed).standard_normal(90)
        q, u = hp.alm2map_spin(high_alms(coefficients, hp), 64, spin=2, lmax=8, mmax=8)
        synthesized = np.r_[q, u]
        design_error = float(np.max(np.abs(high@coefficients-synthesized)))
        projected = projector.apply(synthesized)
        predicted = K@coefficients
        fit_error = float(np.linalg.norm(projected-predicted)/max(np.linalg.norm(predicted), 1.))
        if design_error > 5e-9*max(1., float(np.max(np.abs(synthesized)))) or fit_error > 2e-8:
            raise ValueError("ORIGINAL_SUPPORT_NATIVE_HIGH_INJECTION_FAILED")
        controls[str(seed)] = {"native_vs_design_max_abs": design_error,
                               "projected_vs_response_relative": fit_error}
    # Independent low synthesis, using healpy's actual alm2map_spin convention.
    low_coeff = np.random.default_rng(309).standard_normal(64)
    low_alms = np.zeros((2, hp.Alm.getsize(5)), complex)
    offset = 0
    for ell in range(2, 6):
        n = 2*ell+1
        for field in range(2):
            c = low_coeff[offset:offset+n]; offset += n
            low_alms[field, hp.Alm.getidx(5, ell, 0)] = c[0]
            for m in range(1, ell+1):
                low_alms[field, hp.Alm.getidx(5, ell, m)] = (c[2*m-1]-1j*c[2*m])/np.sqrt(2.)
    q, u = hp.alm2map_spin(low_alms, 64, spin=2, lmax=5, mmax=5)
    low_replay = float(np.linalg.norm(projector.apply(np.r_[q, u])-low_coeff)/np.linalg.norm(low_coeff))
    if low_replay > 2e-8: raise ValueError("ORIGINAL_LOW_NATIVE_REPLAY_FAILED")
    checkpoints, identities, coefficient_arrays = {}, [], {}
    for product in PRODUCTS:
        path = args.root/f"provenance/L01_SMICA_WINDOWED_QU_L128/{product}.json"
        checkpoint, identity = read(path)
        contract = checkpoint["contract"]
        if (contract["healpy_version"] != hp.__version__ or contract["native_window_sha256"] != window_sha
                or contract["product"] != product or contract["lmax"] != 128):
            raise ValueError("CHECKPOINT_SOURCE_OR_RUNTIME_MISMATCH")
        npz = path.with_suffix(".npz")
        data = npz.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        if digest != checkpoint["alms_npz_sha256"]:
            raise ValueError("SAVED_ALMS_SOURCE_CHANGED")
        with np.load(npz, allow_pickle=False) as z:
            alms = np.stack((z["E"], z["B"]))
        result = producer.analyze_alms(alms, 128, hp,
            {"common": projector, "three_way_intersection": projector},
            {"common": K, "three_way_intersection": K})
        checkpoints[product] = result["masks"]["common"]
        coefficient_arrays[product] = np.asarray(checkpoints[product]["total_K_CMB"])
        identities.extend((identity, {"path": str(npz), "sha256": digest, "bytes": len(data)}))
    coefficient_matrix = np.column_stack([coefficient_arrays[p] for p in PRODUCTS])
    result = {"schema": "htt.L01_original_selected_support_finite_response/1",
              "owner": "obsstat", "claim_tier": "C0", "status": "DIAGNOSTIC_ONLY",
              "non_claim_bearing": True, "transfer_source": "none",
              "source_script": {"commit": "c2889730d2b5e5b778951f15e8f09afd55bed4e3",
                                "path": "scripts/run_htt_planck_multisplit_spin_20261015.py",
                                "support_rule": "AND_NATIVE_PMASKS_THEN_PARENT_VALID_FRACTION_GE_0.995"},
              "selected_support": {"nside": 64, "order": "RING", "selected_pixels": int(mask.sum()),
                                   "mask_sha256": hashlib.sha256(mask.astype(np.uint8).tobytes()).hexdigest(),
                                   "native_window_sha256": window_sha,
                                   "threshold": .995, "native_children_per_parent": 1024},
              "native_mask_sha256": receipt["mask_native_sha256"],
              "low_design": meta, "high_response": operator,
              "native_injection_controls": controls, "native_low_replay_relative": low_replay,
              "saved_L128_projections_on_original_selected_support": checkpoints,
              "processing_subjects": {}, "independent_sky_count": 1,
              "original_child_averaged_QU_refit": False,
              "original_observed_EB_coefficients_replaced": False,
              "new_forward_SHT": False, "new_native_QU_scan": False,
              "finite_response_input": "RING64 Q/U field in original Galactic pixel polar frame",
              "source_coarsening_limit": "Native-child Q/U averaging is a different forward operation; no equivalence to a physically transported polarization field is assumed.",
              "beam_or_component_separation_inverted": False,
              "remaining_tail": "ell>128 and native-child averaging mismatch NOT_BOUNDED; retained explicitly",
              "p_value": None, "noise_covariance": None, "paper_gate": "NOT_READY_TO_SUBMIT",
              "sources": identities,
              "generating_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    from analyze_matched_splits import subjects, diagnostics
    result["processing_subjects"] = diagnostics(coefficient_matrix)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with npz_path.open("xb") as stream:
        np.savez_compressed(stream, selected_mask_ring64=mask, coverage_ring64=coverage,
                            high6_8_to_low2_5=K, low_gram=low[np.r_[mask, mask]].T@low[np.r_[mask, mask]],
                            saved_L128_coefficients_K_CMB=coefficient_matrix, products=np.array(PRODUCTS))
    with json_path.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({"out": str(json_path), "selected_support": result["selected_support"],
                      "low_design": meta, "operator_norm": operator["norm_total"],
                      "E_high_to_B_low_norm": operator["norm_E_high_to_B_low"],
                      "native_injection_controls": controls}, indent=2))


if __name__ == "__main__": main()
