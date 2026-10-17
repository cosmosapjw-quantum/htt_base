"""R9/C9 same-sky source response and optional Planck SMICA scalar beam.

Reuses the existing L01 native, spectral, and C8 verification modules.
No Q/U observation, ell>8 tail, foreground, or matched FFP10 null is inferred.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.linalg import svd
from l01_k_spectral_certificate import digest_file, eb_indices, inspect_operator
from l01_mask_difference_stability import validate_reported_native_input

LOW = (2, 3, 4, 5)
HIGH = (6, 7, 8)
C8_SCHEMA = "htt.L01_two_mask_R8_C8_spectral_stability/1"
EXPECTED_NATIVE_SHA = "7b4763afe8e5d30a02be296b0d4f7281a30f4e80937975dcda5f929643c2a7b6"
OBSERVED_DELTA = 0.4396287723908507
OBSERVED_DELTA_BE = 0.2564294649638681
SMICA_FULL_NAME = "COM_CMB_IQU-smica_2048_R3.00_full.fits"


def multipole_diagonal(beam, ells, *, invert=False):
    b = np.asarray(beam)
    if b.ndim != 1 or np.iscomplexobj(b) or len(b) <= max(ells):
        raise ValueError("BEAM_VECTOR_MISSING_OR_WRONG")
    if not np.issubdtype(b.dtype, np.number) or not np.isfinite(b[:max(ells)+1]).all():
        raise ValueError("NONFINITE_BEAM")
    v = np.concatenate([np.full(2 * (2 * ell + 1), float(b[ell])) for ell in ells])
    if np.any(v < 0) or (invert and np.any(v <= 1e-12)):
        raise ValueError("INADMISSIBLE_BEAM_OR_SINGULAR_LOW")
    return 1 / v if invert else v


def beam_difference(common, triple, beam):
    """Exact *conditional* scalar/axisymmetric D_L^-1 (Kt-Kc) D_H."""
    c = np.asarray(common, float)
    t = np.asarray(triple, float)
    if c.shape != (64, 90) or t.shape != c.shape:
        raise ValueError("EXPECTED_K_64X90")
    lo_inv = multipole_diagonal(beam, LOW, invert=True)
    hi = multipole_diagonal(beam, HIGH)
    delta = t - c
    observed = delta * hi[None, :]
    deconvolved = lo_inv[:, None] * observed
    inspect_operator(observed)
    inspect_operator(deconvolved)
    bl = eb_indices(LOW)[1]
    he = eb_indices(HIGH)[0]
    return {
        "observed_low_norm": float(np.linalg.norm(observed, 2)),
        "observed_low_E_to_B_norm": float(np.linalg.norm(observed[np.ix_(bl, he)], 2)),
        "deconvolved_low_norm": float(np.linalg.norm(deconvolved, 2)),
        "deconvolved_low_E_to_B_norm": float(np.linalg.norm(deconvolved[np.ix_(bl, he)], 2)),
        "assumption": "AXISYMMETRIC_E_B_EQUAL_DIAGONAL_BEAM_NOT_E2E",
    }


def shared_source_covariance(common, triple, covariance):
    """Cross terms are mandatory: two masks operate on ONE source h."""
    c = np.asarray(common, float)
    t = np.asarray(triple, float)
    cov = np.asarray(covariance, float)
    if c.shape != (64, 90) or t.shape != c.shape or cov.shape != (90, 90):
        raise ValueError("MATRIX_SHAPE_MISMATCH")
    if not np.isfinite(cov).all() or not np.allclose(cov, cov.T, rtol=0, atol=1e-11):
        raise ValueError("SOURCE_COVARIANCE_NOT_SYMMETRIC_FINITE")
    cov = (cov + cov.T) / 2
    if np.linalg.eigvalsh(cov)[0] < -1e-10 * max(1., float(np.linalg.norm(cov,2))):
        raise ValueError("SOURCE_COVARIANCE_NOT_PSD")
    d = t-c
    return {
        "common": c @ cov @ c.T,
        "triple": t @ cov @ t.T,
        "cross": c @ cov @ t.T,
        "difference": d @ cov @ d.T,
    }


def min_norm_lift(delta, target, *, rtol=1e-11):
    """Minimum high-mode norm for one given low-mode target; not a physical fit."""
    a = np.asarray(delta, float)
    y = np.asarray(target, float)
    if a.shape != (64, 90) or y.shape != (64,) or not np.isfinite(a).all() or not np.isfinite(y).all():
        raise ValueError("SOURCE_OR_TARGET_INVALID")
    if not 0 < rtol < 1:
        raise ValueError("INVALID_RTOL")
    u, s, vh = svd(a, full_matrices=False, check_finite=False)
    active = s > (s[0] * rtol if s[0] > 0 else 0.)
    f = np.zeros_like(s)
    f[active] = (u.T @ y)[active] / s[active]
    witness = vh.T @ f
    residual = float(np.linalg.norm(a @ witness - y))
    reachable = residual <= rtol * max(1., float(np.linalg.norm(y)))
    return {
        "numerical_rank": int(np.count_nonzero(active)),
        "reachable": bool(reachable),
        "min_source_norm_if_reachable": float(np.linalg.norm(witness)) if reachable else None,
        "target_residual": residual,
        "rank_tolerance": rtol,
    }


def read_official_smica_pol_beam(path):
    """Read only the small POL_BEAM FITS extension; never load the 2GB map."""
    p = Path(path)
    if p.name != SMICA_FULL_NAME or not p.is_file() or p.is_symlink():
        raise ValueError("OFFICIAL_SMICA_FULL_FITS_REQUIRED")
    from astropy.io import fits
    with fits.open(p, memmap=True, lazy_load_hdus=True) as hd:
        if len(hd) < 3:
            raise ValueError("MISSING_POL_BEAM_EXTENSION")
        head = hd[1].header
        for k, v in {"NSIDE": 2048, "ORDERING": "NESTED", "COORDSYS": "GALACTIC",
                     "POLCCONV": "COSMO", "METHOD": "SMICA"}.items():
            observed = head.get(k)
            if isinstance(v, str):
                observed = str(observed).strip().upper()
            if observed != v:
                raise ValueError("SMICA_HEADER_" + k)
        names = list(hd[1].columns.names)
        for field in ("Q_STOKES", "U_STOKES"):
            if field not in names or str(head.get("TUNIT" + str(names.index(field)+1), "")).strip() != "K_CMB":
                raise ValueError("SMICA_Q_U_UNIT_CONTRACT")
        if hd[2].header.get("LMIN") != 0 or "POL_BEAM" not in hd[2].columns.names:
            raise ValueError("SMICA_POL_BEAM_LAYOUT")
        b = np.asarray(hd[2].data["POL_BEAM"], float).reshape(-1).copy()
    multipole_diagonal(b, LOW, invert=True)
    multipole_diagonal(b, HIGH)
    return b


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--native-receipt", required=True)
    ap.add_argument("--spectral-receipt", required=True)
    ap.add_argument("--c8-receipt", required=True)
    ap.add_argument("--smica-full", default=None)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    pair, source = validate_reported_native_input(args.native_receipt, args.spectral_receipt)
    receipt = json.loads(Path(args.c8_receipt).read_text(encoding="utf-8"))
    if receipt.get("schema") != C8_SCHEMA or receipt.get("input_native_receipt_sha256") != EXPECTED_NATIVE_SHA or receipt.get("paper_gate") != "NOT_READY_TO_SUBMIT":
        raise ValueError("C8_PROVENANCE_OR_SCIENCE_GATE_MISMATCH")
    for key, val in (("norm_delta", OBSERVED_DELTA),
                     ("sharp_unit_high_E_to_low_B_difference", OBSERVED_DELTA_BE)):
        if not np.isclose(float(receipt.get(key, float("nan"))), val, rtol=2e-10, atol=2e-11):
            raise ValueError("C8_REPORTED_NUMERICAL_MISMATCH")
    if receipt.get("numerical_rank_delta") != 64:
        raise ValueError("C8_REPORTED_RANK_MISMATCH")
    delta = pair["three_way_intersection"] - pair["common"]
    meta = inspect_operator(delta)
    bl, he = eb_indices(LOW)[1], eb_indices(HIGH)[0]
    norm = float(np.linalg.norm(delta, 2))
    e2b = float(np.linalg.norm(delta[np.ix_(bl, he)], 2))
    if not np.isclose(norm, OBSERVED_DELTA, rtol=2e-10, atol=2e-11) or not np.isclose(e2b, OBSERVED_DELTA_BE, rtol=2e-10, atol=2e-11):
        raise ValueError("NATIVE_NPZ_MISMATCH")
    output = {
        "schema": "htt.L01_R9C9_same_sky_beam/1",
        "delta_norm": norm,
        "delta_E_to_B_norm": e2b,
        "numerical_rank": meta["numerical_rank"],
        "left_nullity_numeric": 64 - meta["numerical_rank"],
        "same_sky_covariance": "COV_DELTA=DELTA_K C_H DELTA_K_TRANSPOSE_NOT_INDEPENDENT",
        "source_prior": "NOT_SUPPLIED",
        "ell_ge9_tail": "UNBOUNDED",
        "beam_status": "NOT_RUN_NO_FULL_SMICA",
        "paper_gate": "NOT_READY_TO_SUBMIT",
        "source_sha256": digest_file(args.native_receipt),
        "spectral_receipt_sha256": digest_file(args.spectral_receipt),
        "c8_receipt_sha256": digest_file(args.c8_receipt),
    }
    if args.smica_full:
        b = read_official_smica_pol_beam(args.smica_full)
        output["beam"] = beam_difference(pair["common"], pair["three_way_intersection"], b)
        output["beam_FITS_local_sha256"] = digest_file(args.smica_full)
        output["beam_status"] = "CONDITIONAL_POL_BEAM_DIAGONAL_ONLY"
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS_SCOPED_FINITE_R9C9", "delta_norm": norm, "delta_E_to_B_norm": e2b, "beam_status": output["beam_status"], "out": str(dest)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
