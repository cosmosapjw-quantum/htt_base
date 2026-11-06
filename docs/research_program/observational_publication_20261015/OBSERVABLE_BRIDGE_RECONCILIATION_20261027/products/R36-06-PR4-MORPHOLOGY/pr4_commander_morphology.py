"""Frozen PR4 Commander FULL processed-map morphology consumer.

Each public MC ID is one processed sky.  This program never constructs a total
map from a CMB component and a regression residual, or changes the fixed ID set
in response to the observed statistic.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import healpy as hp
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np
from astropy.io import fits
from scipy.stats import beta


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
EXTERNAL = Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual")
CACHE = EXTERNAL / "cache"
ANALYSIS = EXTERNAL / "analysis"
CONTRACT = Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_contract_preparation/IMPLEMENTATION_CONTRACT.json")
CONTRACT_SHA = "fa08a55ccbf7a5e488cfc2866f0138d0682d3732fe01a785870f8adf9fc677d4"
DONOR = REPO / "docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation/cmb_counterpairs/morphology.py"
POLES = REPO / "htt/obsstat/lowell_poles.py"
OBSERVED = EXTERNAL / "COM_CMB_IQU-commander_4096_R4.00_full.fits"
OBS_RECEIPT = Path(str(OBSERVED) + ".receipt.json")
MASK = Path("/mnt/extdrive/workdir/htt_open_data/research20261022/pr4/mask_PR4_Lollipop_ns16.fits")
MASK_SHA = "7d7df63e77066a7739cc7faed3a005593bb3612af6cdeea2ed48a37fb600946d"
PACKET = "902ebd6a521d6b31864e0bfce63336c62d6cec5ff2f6c3128de7ab68046fce35"
INPUT = "sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43"
NSIDE = 2048
LMAX = 4
NPIX = hp.nside2npix(NSIDE)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def source_binding() -> dict:
    if sha256(CONTRACT) != CONTRACT_SHA or sha256(MASK) != MASK_SHA:
        raise ValueError("frozen contract or mask bytes changed")
    contract = json.loads(CONTRACT.read_text())
    if contract["packet_id"] != PACKET or contract["input_identity"] != INPUT:
        raise ValueError("contract packet/input binding changed")
    return contract


def donor_module():
    spec = importlib.util.spec_from_file_location("r36_pr4_morphology_features", DONOR)
    if spec is None or spec.loader is None:
        raise ImportError("morphology feature donor unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def mask_and_index() -> tuple[np.ndarray, np.ndarray, dict]:
    with fits.open(MASK, memmap=True) as hdus:
        h = hdus[1].header
        if (h.get("NSIDE"), h.get("ORDERING"), h.get("COORDSYS"), h.get("PIXTYPE")) != (16, "RING", "G", "HEALPIX"):
            raise ValueError("mask header contradiction")
        ring16 = np.asarray(hdus[1].data["T"]).reshape(-1)
        if ring16.size != hp.nside2npix(16) or not np.all((ring16 == 0) | (ring16 == 1)):
            raise ValueError("mask is not exact binary NS16")
        nest16 = ring16[hp.nest2ring(16, np.arange(ring16.size))].astype(bool)
    if int(nest16.sum()) != 1273:
        raise ValueError("mask retained parent count")
    child_count = (NSIDE // 16) ** 2
    native_nested = np.repeat(nest16, child_count)
    ring_to_nested = hp.ring2nest(NSIDE, np.arange(NPIX, dtype=np.int64))
    mask_ring = native_nested[ring_to_nested]
    if int(mask_ring.sum()) != 1273 * child_count:
        raise ValueError("mask retained child count")
    return mask_ring, ring_to_nested, {"source": str(MASK), "sha256": MASK_SHA,
        "coarse_nside": 16, "coarse_ordering": "RING", "retained_coarse_pixels": 1273,
        "native_nside": NSIDE, "native_ordering": "NESTED", "child_count_per_parent": child_count,
        "retained_native_pixels": int(mask_ring.sum()), "operator_ordering": "RING",
        "rule": "RING16 to NESTED16, exact parent child repetition, then RING2048 indexing; same scalar binary mask for Q and U"}


def map_identity(kind: str, mc_id: int | None = None) -> tuple[Path, dict, int, tuple[str, str], float]:
    if kind == "observed":
        receipt = json.loads(OBS_RECEIPT.read_text())
        if receipt["path"] != str(OBSERVED) or receipt["bytes"] != 1_207_972_800:
            raise ValueError("observed source receipt contradiction")
        path, hdu, names, scale = OBSERVED, 2, ("Q_POLARIZATION", "U_POLARIZATION"), 1.0
        expected_hash = receipt["sha256"]
    else:
        if mc_id is None or mc_id not in range(300, 400):
            raise ValueError("MC ID outside frozen set")
        name = f"npipe6v20_commander_cmb_2048_mc_{mc_id:04d}_005a.fits"
        path = CACHE / name
        receipt_path = Path(str(path) + ".verified.json")
        if not receipt_path.is_file():
            raise FileNotFoundError(f"verified source receipt missing for MC {mc_id:04d}")
        receipt = json.loads(receipt_path.read_text())
        if receipt["item"]["id"] != mc_id or receipt["item"]["filename"] != name or receipt["item"]["bytes"] != 603_990_720:
            raise ValueError("MC receipt role/size contradiction")
        if receipt["item"]["url"] != "https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID=" + name:
            raise ValueError("MC URL/ID contradiction")
        expected_hash = receipt["sha256"]
        hdu, names, scale = 1, ("Q_STOKES", "U_STOKES"), 1e-6
    if not path.is_file() or path.stat().st_size != (1_207_972_800 if kind == "observed" else 603_990_720):
        raise FileNotFoundError(f"source file missing/incomplete: {path}")
    actual_hash = sha256(path)
    if actual_hash != expected_hash:
        raise ValueError(f"immutable source SHA mismatch: {path}")
    return path, {"path": str(path), "sha256": actual_hash, "size_bytes": path.stat().st_size,
                  "receipt": str(OBS_RECEIPT if kind == "observed" else receipt_path),
                  "role": "released observed Commander FULL" if kind == "observed" else "processed Commander FULL MC sky",
                  "mc_id": mc_id, "hdu": hdu}, hdu, names, scale


def check_header(hdu: fits.BinTableHDU, kind: str, names: tuple[str, str]) -> None:
    h = hdu.header
    expected = (NSIDE, "NESTED", "GALACTIC", "COSMO", "HEALPIX")
    actual = tuple(h.get(k) for k in ("NSIDE", "ORDERING", "COORDSYS", "POLCCONV", "PIXTYPE"))
    if actual != expected:
        raise ValueError(f"{kind} polarized HDU geometry/frame contradiction: {actual}")
    if kind == "observed":
        if tuple(hdu.columns.names) != names or h.get("TFIELDS") != 2:
            raise ValueError("observed polarized field contradiction")
        indices = (1, 2)
        expected_unit = "K_CMB"
    else:
        if tuple(hdu.columns.names) != ("I_STOKES",) + names or h.get("TFIELDS") != 3:
            raise ValueError("MC polarized field contradiction")
        if h.get("METHOD") != "Commander" or h.get("AST-COMP") != "CMB":
            raise ValueError("MC processed component role contradiction")
        indices = (2, 3)
        expected_unit = "uK_CMB"
    if any(h.get(f"TUNIT{i}") != expected_unit for i in indices):
        raise ValueError("polarization unit contradiction")


def masked_qu_from_nested(hdu: fits.BinTableHDU, names: tuple[str, str], scale: float,
                          mask_ring: np.ndarray, ring_to_nested: np.ndarray) -> list[np.ndarray]:
    fields = []
    for name in names:
        nested = np.asarray(hdu.data[name]).reshape(-1)
        if nested.size != NPIX:
            raise ValueError("polarization pixel count contradiction")
        ring = np.asarray(nested[ring_to_nested], dtype=np.float64)
        ring *= scale
        if not np.isfinite(ring[mask_ring]).all() or np.any(np.abs(ring[mask_ring]) >= 1e20):
            raise ValueError("nonfinite or sentinel retained polarization")
        ring[~mask_ring] = 0.0
        if np.any(ring[~mask_ring] != 0):
            raise ArithmeticError("masked pixels not exactly zero")
        fields.append(ring)
    return fields


def packed_coefficients(a: np.ndarray, lmax: int) -> dict[tuple[int, int], complex]:
    out = {}
    for ell in (2, 3, 4):
        for m in range(ell + 1):
            v = complex(a[hp.Alm.getidx(lmax, ell, m)])
            out[ell, m] = v
            if m:
                out[ell, -m] = (-1) ** m * v.conjugate()
    return out


def serialize_coefficients(a: np.ndarray, lmax: int) -> dict[str, list[float]]:
    return {f"{ell},{m}": [float(z.real), float(z.imag)]
            for (ell, m), z in packed_coefficients(a, lmax).items()}


def retained_norm(a: np.ndarray, b: np.ndarray, lmax: int) -> float:
    return float(np.sqrt(sum(abs(a[hp.Alm.getidx(lmax, ell, m)]) ** 2 + abs(b[hp.Alm.getidx(lmax, ell, m)]) ** 2
                             for ell in (2, 3, 4) for m in range(ell + 1))))


def coefficient_stability(fields: list[np.ndarray], e4: np.ndarray, b4: np.ndarray) -> dict:
    e8, b8 = hp.map2alm_spin(fields, spin=2, lmax=8, mmax=8)
    diff = 0.0
    for ell in (2, 3, 4):
        for m in range(ell + 1):
            diff += abs(e4[hp.Alm.getidx(4, ell, m)] - e8[hp.Alm.getidx(8, ell, m)]) ** 2
            diff += abs(b4[hp.Alm.getidx(4, ell, m)] - b8[hp.Alm.getidx(8, ell, m)]) ** 2
    denom = retained_norm(e4, b4, 4)
    if denom == 0:
        raise ValueError("zero retained E/B norm")
    relative = float(np.sqrt(diff) / denom)
    if relative > 1e-10:
        raise ArithmeticError(f"lmax4/lmax8 retained coefficient discrepancy {relative}")
    return {"relative_joint_EB_norm_residual": relative, "limit": 1e-10}


def output_controls(coeff: dict[tuple[int, int], complex], feature: dict, donor) -> dict:
    parity = donor.features(donor.intervention(coeff, donor.Factor.PARITY, 0.0))
    rotation = donor.features(donor.intervention(coeff, donor.Factor.ORIENTATION, 0.41))
    scaled = donor.features({k: 1e6 * v for k, v in coeff.items()})
    j = feature["J234"]
    errors = {"parity_J_sign": abs(parity["J234"] + j),
              "z_rotation_J": abs(rotation["J234"] - j),
              "positive_unit_rescale_J": abs(scaled["J234"] - j)}
    for ell in (2, 3, 4):
        key = str(ell)
        errors[f"rotation_C{ell}_relative"] = abs(rotation["C_ell_K_CMB2"][key] / feature["C_ell_K_CMB2"][key] - 1)
        errors[f"rescale_C{ell}_relative"] = abs(scaled["C_ell_K_CMB2"][key] / (1e12 * feature["C_ell_K_CMB2"][key]) - 1)
    if max(errors.values()) > 1e-12:
        raise ArithmeticError(f"output algebra control failed: {errors}")
    return {"errors": errors, "limit": 1e-12,
            "parity": "a_lm -> (-1)^ell a_lm", "z_rotation_radians": 0.41,
            "positive_rescaling": 1e6, "stage": "post-extraction algebra; not a rotated sky through fixed mask"}


def consume(kind: str, mc_id: int | None = None, *, stability: bool = False) -> dict:
    source_binding()
    path, source, hdu_index, names, scale = map_identity(kind, mc_id)
    mask_ring, ring_to_nested, mask_meta = mask_and_index()
    donor = donor_module()
    started = time.monotonic()
    with fits.open(path, memmap=True, lazy_load_hdus=True) as hdus:
        if len(hdus) != (3 if kind == "observed" else 2):
            raise ValueError("FITS HDU count contradiction")
        hdu = hdus[hdu_index]
        check_header(hdu, kind, names)
        fields = masked_qu_from_nested(hdu, names, scale, mask_ring, ring_to_nested)
        e4, b4 = hp.map2alm_spin(fields, spin=2, lmax=4, mmax=4)
        stability_result = coefficient_stability(fields, e4, b4) if stability else None
    if not np.isfinite(e4).all() or not np.isfinite(b4).all():
        raise ValueError("nonfinite harmonic extraction")
    coeff = packed_coefficients(e4, 4)
    feature = donor.features(coeff)
    controls = output_controls(coeff, feature, donor)
    label = "observed" if kind == "observed" else f"mc_{mc_id:04d}"
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    alm_path = ANALYSIS / f"{label}_lowell_EB.npz"
    row_path = ANALYSIS / f"{label}.json"
    if alm_path.exists() or row_path.exists():
        raise FileExistsError("existing analyzed product requires inspection; no overwrite")
    np.savez_compressed(alm_path, E=e4, B=b4)
    row = {"schema": "htt.r36_pr4_commander_map_morphology/1", "task_id": "R36-06-PR4-MORPHOLOGY",
           "packet_id": PACKET, "input_identity": INPUT, "contract_sha256": CONTRACT_SHA,
           "kind": kind, "mc_id": mc_id, "source": source, "mask": mask_meta,
           "consumer_source_sha256": sha256(Path(__file__)),
           "feature_source": {"path": str(DONOR), "sha256": sha256(DONOR),
                              "reused_functions": ["features", "intervention"],
                              "power_tensor_kernel": {"path": str(POLES), "sha256": sha256(POLES)}},
           "operator": {"frame": "GALACTIC", "polconv": "COSMO", "units": "K_CMB", "native_nside": NSIDE,
                        "native_ordering": "NESTED", "analysis_ordering": "RING", "spin": 2, "lmax": 4,
                        "mask_order": "native QU before spin2", "additional_smoothing": False,
                        "beam_inversion": False, "noise_subtraction": False,
                        "nominal_release_resolution": "5 arcmin descriptor; no FITS FWHM card or measured beam claimed",
                        "response": "delivered NPIPE/Commander processing plus exact stated mask/spin operator; no all-m upstream transfer reconstruction",
                        "input_conversion_to_K_CMB": scale},
           "E_l2_l3_l4_full_signed_m": serialize_coefficients(e4, 4),
           "B_l2_l3_l4_full_signed_m": serialize_coefficients(b4, 4),
           "features": feature, "T_abs_J234": abs(feature["J234"]),
           "controls": controls, "stability": stability_result,
           "alms": {"path": str(alm_path), "sha256": sha256(alm_path), "size_bytes": alm_path.stat().st_size},
           "execution": {"utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": time.monotonic() - started,
                         "python": platform.python_version(), "numpy": np.__version__, "healpy": hp.__version__,
                         "astropy": __import__("astropy").__version__, "pid": os.getpid()},
           "status": "PROCESSED_ONE_SKY_ROW; NO_P_VALUE"}
    row_path.write_text(json.dumps(row, indent=2, allow_nan=False) + "\n")
    return row


def exact_interval(k: int, n: int) -> tuple[float, float]:
    if not (0 <= k <= n and n > 0):
        raise ValueError("invalid binomial count")
    return (0.0 if k == 0 else float(beta.ppf(0.025, k, n-k+1)),
            1.0 if k == n else float(beta.ppf(0.975, k+1, n-k)))


def mask_response() -> dict:
    """Three frozen unit columns of the native spin synthesis/masked analysis."""
    source_binding()
    mask_ring, _, mask_meta = mask_and_index()
    size = hp.Alm.getsize(4)
    definitions = (("E2_m0", "E", 2, 0, 1.0 + 0j),
                   ("E3_m1_real", "E", 3, 1, 1 / np.sqrt(2) + 0j),
                   ("B4_m2_imag", "B", 4, 2, 1j / np.sqrt(2)))
    qsum = np.zeros(NPIX, dtype=np.float64)
    usum = np.zeros(NPIX, dtype=np.float64)
    e_sum = np.zeros(size, dtype=np.complex128)
    b_sum = np.zeros(size, dtype=np.complex128)
    rows = []
    npz_arrays = {}
    for label, field, ell, m, value in definitions:
        e_in = np.zeros(size, dtype=np.complex128)
        b_in = np.zeros(size, dtype=np.complex128)
        (e_in if field == "E" else b_in)[hp.Alm.getidx(4, ell, m)] = value
        q, u = hp.alm2map_spin([e_in, b_in], nside=NSIDE, spin=2, lmax=4, mmax=4)
        for arr in (q, u):
            arr[~mask_ring] = 0.0
            if np.any(arr[~mask_ring] != 0) or not np.isfinite(arr[mask_ring]).all():
                raise ArithmeticError("unit injection mask/finite control failed")
        qsum += q
        usum += u
        e_out, b_out = hp.map2alm_spin([q, u], spin=2, lmax=4, mmax=4)
        if not np.isfinite(e_out).all() or not np.isfinite(b_out).all():
            raise ArithmeticError("nonfinite response column")
        e_sum += e_out
        b_sum += b_out
        npz_arrays[label + "_E"] = e_out
        npz_arrays[label + "_B"] = b_out
        intended_e = e_in if field == "E" else np.zeros_like(e_in)
        intended_b = b_in if field == "B" else np.zeros_like(b_in)
        leakage_e = float(np.linalg.norm(e_out - intended_e))
        leakage_b = float(np.linalg.norm(b_out - intended_b))
        rows.append({"label": label, "injection_field": field, "ell": ell, "m_positive": m,
                     "positive_m_value": [float(value.real), float(value.imag)],
                     "reality_relation": "a(l,-m)=(-1)^m conjugate(a(l,m))",
                     "E_l2_l3_l4_full_signed_m": serialize_coefficients(e_out, 4),
                     "B_l2_l3_l4_full_signed_m": serialize_coefficients(b_out, 4),
                     "relative_to_unmasked_unit_E_residual": leakage_e,
                     "relative_to_unmasked_unit_B_residual": leakage_b,
                     "opposite_parity_norm": float(np.linalg.norm(b_out if field == "E" else e_out))})
        del q, u
    e_joint, b_joint = hp.map2alm_spin([qsum, usum], spin=2, lmax=4, mmax=4)
    denominator = float(np.linalg.norm(np.r_[e_sum, b_sum]))
    if denominator == 0:
        raise ArithmeticError("zero joint response")
    residual = float(np.linalg.norm(np.r_[e_joint-e_sum, b_joint-b_sum]) / denominator)
    if residual > 1e-10:
        raise ArithmeticError(f"masked map transform linearity failed: {residual}")
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    npz = ANALYSIS / "mask_response_three_columns.npz"
    out = ANALYSIS / "mask_response_three_columns.json"
    if npz.exists() or out.exists():
        raise FileExistsError("existing mask response requires inspection")
    np.savez_compressed(npz, **npz_arrays, joint_E=e_joint, joint_B=b_joint)
    result = {"schema": "htt.r36_pr4_native_mask_response/1", "packet_id": PACKET,
              "contract_sha256": CONTRACT_SHA, "mask": mask_meta,
              "operator": "native NSIDE2048 RING QU spin2 synthesis, same frozen mask, lmax4 spin2 analysis",
              "columns": rows, "linearity_relative_joint_EB_residual": residual,
              "linearity_limit": 1e-10, "masked_pixels_exactly_zero": True,
              "npz": {"path": str(npz), "sha256": sha256(npz), "size_bytes": npz.stat().st_size},
              "interpretation": "Three output columns show the actual anisotropic masked analysis response for selected unit modes, including E/B leakage where present; not a full upstream transfer matrix or beam deconvolution."}
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def assemble() -> dict:
    source_binding()
    rows = [json.loads((ANALYSIS / f"mc_{i:04d}.json").read_text()) for i in range(300, 400)]
    obs = json.loads((ANALYSIS / "observed.json").read_text())
    if any(r["mc_id"] != i or r["contract_sha256"] != CONTRACT_SHA for i, r in zip(range(300, 400), rows)):
        raise ValueError("fixed MC row set/binding contradiction")
    if obs["contract_sha256"] != CONTRACT_SHA or obs["kind"] != "observed":
        raise ValueError("observed row binding contradiction")
    if any(not (r["source"]["path"] and r["source"]["sha256"] and r["controls"]) for r in rows):
        raise ValueError("incomplete MC source/operator rows")
    t = obs["T_abs_J234"]
    k = sum(r["T_abs_J234"] >= t for r in rows)
    lo, hi = exact_interval(k, 100)
    if (hi-lo)/2 > 0.105:
        raise ArithmeticError("declared MC interval accuracy not met")
    result = {"schema": "htt.r36_pr4_commander_morphology_result/1", "task_id": "R36-06-PR4-MORPHOLOGY",
              "packet_id": PACKET, "input_identity": INPUT, "contract_sha256": CONTRACT_SHA,
              "owner": "obsstat", "claim_tier": "PROPOSED_PENDING_INDEPENDENT_REVIEW",
              "transfer_source": "No Bianchi transfer; retained delivered NPIPE/Commander anisotropic processing response",
              "sky_support_status": "one observed full sky; 100 distinct processed MC parent skies under one frozen Galactic mask",
              "null_mock_status": "100 fixed public PR4 Commander processed FULL MC products consumed, pending independent review",
              "estimand": "Commander FULL processed E pseudoalm singleton T=abs(J234), ell=(2,3,4)",
              "source_release": "Planck PR4 NPIPE npipe6v20 Commander CMB FULL; delivered 005a products",
              "observed": obs, "mc_rows": rows,
              "fixed_mc_ids": list(range(300, 400)), "independent_null_units": 100,
              "rank": {"inclusive_tail_count_k": k, "B": 100, "p_rank": (1+k)/101,
                       "empirical_tail_k_over_B": k/100, "clopper_pearson_95": [lo, hi],
                       "interval_half_width": (hi-lo)/2, "ties_included": True},
              "supplemental_030": {"path": str(HERE / "RESULT.json"),
                                    "status": "one observed sky descriptive only; separate T=max(|J_A|,|J_B|,|J_C|), p=null"},
              "ideal_U": {"law": "U=3sqrt(3)|z1 z2 z3| for z uniform S6", "mean": "15sqrt(3)/(64pi)",
                          "second_moment": "3/77", "status": "separate ideal reference, never used as J null"},
              "physical_interpretation": "Conditional comparison to the released processed Commander working law, assuming observed/simulated exchangeability. Finite-MC interval covers simulation-tail uncertainty only; no unconditional physical false-positive or Bianchi-family claim.",
              "caveats": ["Foreground and Commander mixing matrices are fixed from observed data in the public simulations; this is a plug-in released-pipeline working law.",
                          "The native NPIPE/Commander anisotropic response is retained in delivered maps; no all-m upstream transfer matrix or deconvolved cosmic E inference is claimed.",
                          "A/B temporal splits and synthetic coadd are one observed sky and are not added as null units.",
                          "Original PR3 and original 42-node acceptances remain unchanged."],
              "qualification_status": "PROPOSED_PENDING_FRESH_INDEPENDENT_REVIEW",
              "acceptance_met": False}
    out = HERE / "COMMANDER_RESULT.json"
    if out.exists():
        raise FileExistsError("existing final result requires inspection")
    out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    fig, ax = plt.subplots(figsize=(8.5, 5.2), constrained_layout=True)
    values = np.array([r["T_abs_J234"] for r in rows])
    ax.hist(values, bins="fd", color="#6488a4", edgecolor="white", alpha=0.88,
            label="100 fixed PR4 processed MC skies")
    ax.axvline(t, color="#b34036", linewidth=2.1, label=f"observed FULL T={t:.5f}")
    ax.set(xlabel="T = |J234| from masked Commander E pseudoalms", ylabel="MC sky count",
           title="PR4 Commander FULL low-ell morphology, processed-map working law")
    ax.legend(loc="best", fontsize=8)
    ax.text(0.98, 0.97, f"k = {k} / 100, inclusive tail\nplus-one p = {(1+k)/101:.4f}\n95% CP [{lo:.3f}, {hi:.3f}]",
            ha="right", va="top", transform=ax.transAxes,
            bbox={"facecolor": "white", "edgecolor": "#999", "alpha": 0.9}, fontsize=8)
    fig.text(0.5, 0.01, "Conditional released-pipeline comparison; interval is MC tail uncertainty, not physical coverage or Bianchi identification.",
             ha="center", fontsize=8)
    fig.savefig(HERE / "COMMANDER_MORPHOLOGY.png", dpi=180)
    fig.savefig(HERE / "COMMANDER_MORPHOLOGY.pdf")
    plt.close(fig)
    return result


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("observed", "mc", "response", "assemble"))
    p.add_argument("--id", type=int)
    p.add_argument("--stability", action="store_true")
    a = p.parse_args()
    if a.mode == "response":
        r = mask_response()
        print(json.dumps({"columns": len(r["columns"]),
                          "linearity_residual": r["linearity_relative_joint_EB_residual"]}))
    elif a.mode == "assemble":
        r = assemble()
        print(json.dumps({"status": r["qualification_status"], "k": r["rank"]["inclusive_tail_count_k"], "p": r["rank"]["p_rank"]}))
    else:
        r = consume(a.mode, a.id, stability=a.stability)
        print(json.dumps({"kind": r["kind"], "mc_id": r["mc_id"], "T": r["T_abs_J234"],
                          "elapsed_seconds": r["execution"]["elapsed_seconds"]}))


if __name__ == "__main__":
    main()
