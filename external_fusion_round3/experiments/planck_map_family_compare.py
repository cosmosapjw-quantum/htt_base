#!/usr/bin/env python3
"""Compare low-ell pole nuisance envelopes across Planck component maps.

Example:
  PYTHONPATH=src python experiments/planck_map_family_compare.py \
      --map SMICA=/data/COM_CMB_IQU-smica_2048_R3.00_full.fits \
      --map COMMANDER=/data/COM_CMB_IQU-commander_2048_R3.00_full.fits \
      --mask /data/common_mask.fits

The component-separated products are one observed sky.  Pairwise differences are
reported as map-product sensitivity, never as independent-sky sampling error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.poles import angular_separation_deg, mean_axis, pole_from_alm  # noqa: E402


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def full_alm_for_ell(hp, packed, ell: int, lmax: int) -> np.ndarray:
    a = np.zeros(2 * ell + 1, dtype=np.complex128)
    for m in range(ell + 1):
        z = packed[hp.Alm.getidx(lmax, ell, m)]
        a[ell + m] = z.real if m == 0 else z
        if m:
            a[ell - m] = ((-1) ** m) * np.conj(z)
    return a


def parse_map(value: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--map must be LABEL=PATH")
    label, path = value.split("=", 1)
    if not label or not path:
        raise argparse.ArgumentTypeError("--map must be LABEL=PATH")
    return label, path


def load_processed(hp, path: str, field: int, mask_path: str | None, nside: int) -> np.ndarray:
    m = np.asarray(hp.read_map(path, field=field, dtype=np.float64), dtype=float)
    m = hp.ud_grade(m, nside_out=nside)
    good = np.isfinite(m) & (m != hp.UNSEEN)
    if mask_path:
        mask = np.asarray(hp.read_map(mask_path, field=0, dtype=np.float64), dtype=float)
        mask = hp.ud_grade(mask, nside_out=nside)
        good &= mask > 0.5
    # This is a registered quicklook estimator.  A publication lane must replace
    # zero-filled masking with a calibrated masked-sky/inpainting estimator.
    out = np.zeros_like(m)
    out[good] = m[good]
    out = hp.remove_monopole(out, gal_cut=0, fitval=False, verbose=False)
    out = hp.remove_dipole(out, gal_cut=0, fitval=False, verbose=False)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--map", action="append", type=parse_map, required=True)
    ap.add_argument("--mask")
    ap.add_argument("--field", type=int, default=0)
    ap.add_argument("--nside", type=int, default=64)
    ap.add_argument("--lmax", type=int, default=10)
    ap.add_argument("--ells", default="2,3,4,5")
    args = ap.parse_args()
    if len(args.map) < 2:
        raise SystemExit("at least two component-map products are required")
    try:
        import healpy as hp
    except ImportError as exc:
        raise SystemExit("healpy is required for this optional script") from exc

    ells = tuple(int(x) for x in args.ells.split(",") if x.strip())
    products: dict[str, dict] = {}
    for label, path in args.map:
        map_data = load_processed(hp, path, args.field, args.mask, args.nside)
        packed = hp.map2alm(map_data, lmax=args.lmax, iter=3)
        poles = {}
        for ell in ells:
            p, vals = pole_from_alm(full_alm_for_ell(hp, packed, ell, args.lmax), ell)
            poles[str(ell)] = {"pole_unoriented": p.tolist(), "eigenvalues": vals.tolist()}
        products[label] = {"path_basename": Path(path).name, "sha256": sha256(path), "poles": poles}

    comparisons: dict[str, dict] = {}
    labels = list(products)
    for ell in ells:
        pp = np.asarray([products[label]["poles"][str(ell)]["pole_unoriented"] for label in labels])
        pairwise = {}
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                pairwise[f"{labels[i]}__{labels[j]}"] = angular_separation_deg(pp[i], pp[j])
        centre = mean_axis(pp)
        comparisons[str(ell)] = {
            "pairwise_unoriented_angles_deg": pairwise,
            "map_family_mean_axis": centre.tolist(),
            "max_product_angle_deg": max(pairwise.values()),
            "interpretation": "component-map product sensitivity on one sky, not independent sampling variance",
        }

    result = {
        "schema": "htt.planck_map_family_poles.v1",
        "status": "QUICKLOOK_ONLY_MASK_CALIBRATION_REQUIRED",
        "nside": args.nside,
        "lmax": args.lmax,
        "mask": None if not args.mask else {"basename": Path(args.mask).name, "sha256": sha256(args.mask)},
        "products": products,
        "comparisons": comparisons,
        "claim_boundary": "No anomaly/detection/global-tilt claim; publication use requires matched mask/foreground null simulations.",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
