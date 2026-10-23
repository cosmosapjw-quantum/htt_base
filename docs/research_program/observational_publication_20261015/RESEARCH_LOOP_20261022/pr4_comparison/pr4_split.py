"""Descriptive native-resolution PR4 Q/U half-sum and half-difference.

The NSIDE16 RING mask selects whole NSIDE1024 NESTED parents. Q/U values are
never smoothed or regridded. This is a one-realization map comparison, not a
noise estimate, null test, foreground correction, or CMB inference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import healpy as hp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.io import fits


HERE = Path(__file__).resolve().parent
INTAKE = HERE.parent / "data" / "pr4" / "VALIDATION.json"
MASK_NSIDE = 16
MAP_NSIDE = 1024
CHILDREN = (MAP_NSIDE // MASK_NSIDE) ** 2
PSI = 0.371
REL_TOL = 1e-10
ABS_SCALE_K2 = 1e-18  # 10^-6 microK^2, a scale guard, not an added tolerance
IDS = ("PR4_LFI30_OBS_YEAR13", "PR4_LFI30_OBS_YEAR24", "PR4_LOLLIPOP_NS16_MASK")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def nest_mask_from_ring(mask_ring: np.ndarray, nside: int) -> np.ndarray:
    """Return NESTED values indexed by their exact RING pixel equivalents."""
    mask_ring = np.asarray(mask_ring)
    if mask_ring.shape != (hp.nside2npix(nside),):
        raise ValueError("mask has wrong HEALPix pixel count")
    if not np.all(np.isfinite(mask_ring)) or not np.all((mask_ring == 0) | (mask_ring == 1)):
        raise ValueError("mask must contain finite binary values")
    return mask_ring[hp.nest2ring(nside, np.arange(mask_ring.size))].astype(bool)


def child_bounds(parent_nested: int, coarse_nside: int = MASK_NSIDE,
                 fine_nside: int = MAP_NSIDE) -> tuple[int, int]:
    if fine_nside < coarse_nside or fine_nside % coarse_nside:
        raise ValueError("NSIDE ratio must be integral and nondecreasing")
    ratio = fine_nside // coarse_nside
    if ratio & (ratio - 1):
        raise ValueError("NSIDE ratio must be a power of two")
    if not 0 <= parent_nested < hp.nside2npix(coarse_nside):
        raise ValueError("parent pixel out of range")
    count = ratio * ratio
    return parent_nested * count, (parent_nested + 1) * count


def split_chunk(aq: np.ndarray, au: np.ndarray, bq: np.ndarray,
                bu: np.ndarray, psi: float = PSI) -> dict[str, float]:
    """Float64 scalar sums for one exact native child block."""
    vectors = [np.asarray(v, dtype=np.float64).reshape(-1) for v in (aq, au, bq, bu)]
    if len({len(v) for v in vectors}) != 1 or not all(np.isfinite(v).all() for v in vectors):
        raise ValueError("Q/U chunk sizes must agree and all values be finite")
    aq, au, bq, bu = vectors
    sq, su = 0.5 * (aq + bq), 0.5 * (au + bu)
    dq, du = 0.5 * (aq - bq), 0.5 * (au - bu)
    c, s = math.cos(2 * psi), math.sin(2 * psi)

    def power(q: np.ndarray, u: np.ndarray) -> float:
        return float(np.sum(q * q + u * u, dtype=np.float64))

    def rotated_power(q: np.ndarray, u: np.ndarray) -> float:
        return power(c * q + s * u, -s * q + c * u)

    return {
        "count": len(aq), "S2": power(sq, su), "D2": power(dq, du),
        "A2": power(aq, au), "B2": power(bq, bu),
        "AB": float(np.sum(aq * bq + au * bu, dtype=np.float64)),
        "S2_rot": rotated_power(sq, su), "D2_rot": rotated_power(dq, du),
        "A2_rot": rotated_power(aq, au), "B2_rot": rotated_power(bq, bu),
        "AB_rot": float(np.sum((c * aq + s * au) * (c * bq + s * bu)
                               + (-s * aq + c * au) * (-s * bq + c * bu),
                               dtype=np.float64)),
    }


def check_identity(name: str, observed: float, expected: float) -> dict:
    residual = observed - expected
    scale = max(abs(observed), abs(expected), ABS_SCALE_K2)
    relative_guarded = abs(residual) / scale
    if not np.isfinite(relative_guarded) or relative_guarded > REL_TOL:
        raise ArithmeticError(f"{name}: {residual:.17g} K^2; relative {relative_guarded:.3g}")
    return {"residual_K2": residual, "absolute_residual_K2": abs(residual),
            "relative_with_1e-18_K2_scale_guard": relative_guarded,
            "criterion": "<=1e-10"}


def positive_power_ratio(d2: float, s2: float) -> float:
    if not np.isfinite(d2) or not np.isfinite(s2) or d2 < 0 or s2 <= 0:
        raise ArithmeticError("ratio requires finite nonnegative D power and positive S power")
    return d2 / s2


def _header(hdu: fits.BinTableHDU, *, nside: int, ordering: str, fields: tuple[str, ...]) -> None:
    hdr = hdu.header
    if (hdr["NSIDE"], hdr["ORDERING"].strip(), hdr["COORDSYS"].strip(),
            hdr["PIXTYPE"].strip()) != (nside, ordering, "G", "HEALPIX"):
        raise ValueError("FITS HEALPix geometry/frame differs from qualified intake")
    if tuple(hdu.columns.names[:len(fields)]) != fields:
        raise ValueError("FITS fields differ from qualified intake")


def run() -> tuple[dict, np.ndarray]:
    raw = INTAKE.read_bytes()
    intake = json.loads(raw)
    entries = {r["id"]: r for r in intake["resources"]}
    if set(entries) != set(IDS) or intake["qualification"] != "TRANSPORT_SCHEMA_PIXEL_ONLY":
        raise ValueError("unexpected source validation")
    for spec in entries.values():
        path = Path(spec["path"])
        receipt = json.loads(Path(str(path) + ".receipt.json").read_text())
        if path.stat().st_size != spec["bytes"] or receipt["sha256"] != spec["sha256"]:
            raise ValueError(f"source size/receipt identity mismatch: {path}")

    apath, bpath, mpath = (Path(entries[k]["path"]) for k in IDS)
    with fits.open(mpath, memmap=True) as mh:
        _header(mh[1], nside=MASK_NSIDE, ordering="RING", fields=("T",))
        mask_ring = np.asarray(mh[1].data["T"]).reshape(-1)
        mask_nested = nest_mask_from_ring(mask_ring, MASK_NSIDE)
    parents = np.flatnonzero(mask_nested)
    if len(parents) != 1273:
        raise ValueError(f"unexpected native support parents: {len(parents)}")
    expected_count = len(parents) * CHILDREN
    if expected_count != 5_214_208:
        raise ValueError("unexpected lifted pixel count")

    keys = ("S2", "D2", "A2", "B2", "AB", "S2_rot", "D2_rot", "A2_rot", "B2_rot", "AB_rot")
    parent_sums = {k: [] for k in keys}
    d_rms_microk = np.full(hp.nside2npix(MASK_NSIDE), hp.UNSEEN, dtype=np.float64)
    with fits.open(apath, memmap=True) as ah, fits.open(bpath, memmap=True) as bh:
        for hdu in (ah[1], bh[1]):
            _header(hdu, nside=MAP_NSIDE, ordering="NESTED",
                    fields=("I_STOKES", "Q_STOKES", "U_STOKES"))
            if hdu.header["POLCCONV"].strip() != "COSMO":
                raise ValueError("FITS polarization convention changed")
            if any(hdu.header[f"TUNIT{i}"].strip() != "K_CMB" for i in (2, 3)):
                raise ValueError("FITS Q/U unit changed")
        ad, bd = ah[1].data, bh[1].data
        count = 0
        for parent in parents:
            lo, hi = child_bounds(int(parent))
            if lo % 1024 or hi % 1024:
                raise ValueError("native parent does not align with FITS vector rows")
            rows = slice(lo // 1024, hi // 1024)
            sums = split_chunk(ad["Q_STOKES"][rows], ad["U_STOKES"][rows],
                               bd["Q_STOKES"][rows], bd["U_STOKES"][rows])
            if sums["count"] != CHILDREN:
                raise ValueError("wrong native child count")
            count += sums["count"]
            for key in keys:
                parent_sums[key].append(sums[key])
            d_rms_microk[parent] = math.sqrt(sums["D2"] / CHILDREN) * 1e6
    if count != expected_count:
        raise ValueError("selected native count differs from exact lifted support")

    means = {k: math.fsum(parent_sums[k]) / count for k in keys}
    if not all(np.isfinite(v) for v in means.values()):
        raise ArithmeticError("nonfinite powers")
    checks = {
        "parallelogram_S2_plus_D2": check_identity(
            "parallelogram", means["S2"] + means["D2"], (means["A2"] + means["B2"]) / 2),
        "cross_S2_minus_D2": check_identity(
            "cross", means["S2"] - means["D2"], means["AB"]),
    }
    for key in ("S2", "D2", "A2", "B2", "AB"):
        checks[f"basis_rotation_{key}"] = check_identity(
            f"basis_rotation_{key}", means[f"{key}_rot"], means[key])
    powers = {k: {"K_CMB2": means[k], "microK_CMB2": means[k] * 1e12}
              for k in ("S2", "D2", "A2", "B2", "AB")}
    selected_rms = d_rms_microk[parents]
    result = {
        "status": "SOURCE_CONDITIONAL_DESCRIPTIVE_SPLIT_COMPARISON",
        "claim_tier": "C0_NON_CLAIM_BEARING", "owner": "HTT observational research intake",
        "scope": "one observed PR4 LFI 30 GHz A/B Q/U split on lifted LoLLiPoP binary support",
        "transfer_source": "none; no Bianchi transfer or beam inversion",
        "source_validation": {"path": str(INTAKE), "sha256": hashlib.sha256(raw).hexdigest(),
                              "byte_checks": "reused prior independent intake; current run checked sizes and receipt hashes"},
        "inputs": [{k: entries[i][k] for k in ("id", "path", "bytes", "sha256", "url")} for i in IDS],
        "geometry": {"map_nside": MAP_NSIDE, "map_ordering": "NESTED", "mask_nside": MASK_NSIDE,
                     "mask_original_ordering": "RING", "mask_calculation_ordering": "NESTED",
                     "frame": "Galactic", "polarization_convention": "COSMO", "input_unit": "K_CMB",
                     "mask_rule": "mask_ring[nest2ring(16, parent_nested)] == 1; native children [4096p,4096(p+1))",
                     "selected_parent_pixels": len(parents), "selected_native_pixels": count,
                     "full_sky_parent_pixels": hp.nside2npix(MASK_NSIDE),
                     "full_sky_native_pixels": hp.nside2npix(MAP_NSIDE),
                     "selected_sky_fraction": len(parents) / hp.nside2npix(MASK_NSIDE),
                     "selected_area_sq_deg": len(parents) / hp.nside2npix(MASK_NSIDE) * 4 * math.pi * (180 / math.pi) ** 2},
        "formula": "S=(A+B)/2, D=(A-B)/2, |P|^2=Q^2+U^2, equal-area mean over selected native pixels",
        "powers": powers, "D2_over_S2": positive_power_ratio(means["D2"], means["S2"]),
        "checks": checks, "basis_rotation_psi_rad": PSI,
        "scalar_rms_map": {"nside": MASK_NSIDE, "ordering": "NESTED",
                           "definition": "sqrt(mean_native_children |D|^2) in microK_CMB for each selected parent; other pixels masked",
                           "selected_parent_min_microK": float(np.min(selected_rms)),
                           "selected_parent_median_microK": float(np.median(selected_rms)),
                           "selected_parent_equal_area_mean_microK": float(np.mean(selected_rms)),
                           "selected_parent_max_microK": float(np.max(selected_rms))},
        "caveats": ["Single observed split pair; differential sky, foreground and instrument response may contribute.",
                    "No pure-noise, null-law, significance, isolated CMB polarization, or Bianchi interpretation.",
                    "The binary mask threshold and equal-area means are descriptive; mask/statistic compatibility is uncalibrated.",
                    "AB spectrum beam windows are not a map operator and are not applied.",
                    "Original 17/42 status, F06 and L03 HOLD are unchanged."],
    }
    return result, d_rms_microk


def plot_rms(values: np.ndarray, result: dict) -> None:
    hp.mollview(values, nest=True, title="PR4 30 GHz A/B: half-difference scalar RMS",
                unit="microK_CMB", cmap="viridis", min=0, xsize=1200)
    hp.graticule()
    fig = plt.gcf()
    fig.set_size_inches(11, 7.5)
    fig.subplots_adjust(bottom=0.25)
    g = result["geometry"]
    fig.text(0.5, 0.012,
             f"Galactic / COSMO; {g['selected_parent_pixels']}/{g['full_sky_parent_pixels']} "
             f"binary-mask parents ({100*g['selected_sky_fraction']:.2f}% sky).\n"
             "Each colored pixel is native-child scalar RMS, not regridded Q/U. "
             "Mask threshold and equal-area means are descriptive.",
             ha="center", va="bottom", fontsize=9)
    fig.savefig(HERE / "D_RMS_NS16.png", dpi=170, bbox_inches="tight")
    fig.savefig(HERE / "D_RMS_NS16.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-artifacts", action="store_true")
    args = parser.parse_args()
    result, values = run()
    if args.write_artifacts:
        plot_rms(values, result)
        (HERE / "RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        receipt = {"generator": "pr4_split.py --write-artifacts",
                   "source_code_sha256": sha256(Path(__file__)),
                   "result_sha256": sha256(HERE / "RESULT.json"),
                   "images": {name: sha256(HERE / name) for name in ("D_RMS_NS16.png", "D_RMS_NS16.pdf")},
                   "plot_semantics": result["scalar_rms_map"]["definition"]}
        (HERE / "PLOT_RECEIPT.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "selected_native_pixels": result["geometry"]["selected_native_pixels"],
                      "D2_over_S2": result["D2_over_S2"], "checks": result["checks"]}, indent=2))


if __name__ == "__main__":
    main()
