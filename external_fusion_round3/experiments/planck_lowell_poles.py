#!/usr/bin/env python3
"""Extract low-ell poles from an official Planck HEALPix map.

This script is optional and requires healpy plus a user-supplied FITS path.  It
never downloads data and never treats different component-separated maps as
independent skies.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.poles import pole_from_alm  # noqa: E402


def full_alm_for_ell(hp, packed, ell: int, lmax: int) -> np.ndarray:
    a = np.zeros(2 * ell + 1, dtype=np.complex128)
    for m in range(0, ell + 1):
        z = packed[hp.Alm.getidx(lmax, ell, m)]
        a[ell + m] = z
        if m == 0:
            a[ell] = z.real
        else:
            a[ell - m] = ((-1) ** m) * np.conj(z)
    return a


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("map_fits")
    parser.add_argument("--field", type=int, default=0)
    parser.add_argument("--mask-fits")
    parser.add_argument("--lmax", type=int, default=10)
    parser.add_argument("--ells", default="1,2,3,4,5")
    parser.add_argument("--nside", type=int, default=64)
    args = parser.parse_args()
    try:
        import healpy as hp
    except ImportError as exc:
        raise SystemExit("healpy is required for this optional script") from exc

    m = np.asarray(hp.read_map(args.map_fits, field=args.field, dtype=np.float64), dtype=float)
    if args.mask_fits:
        mask = np.asarray(hp.read_map(args.mask_fits, field=0, dtype=np.float64), dtype=float)
        if mask.shape != m.shape:
            mask = hp.ud_grade(mask, hp.get_nside(m))
        m = np.where(mask > 0.5, m, hp.UNSEEN)
    m = hp.ud_grade(m, args.nside)
    good = np.isfinite(m) & (m != hp.UNSEEN)
    cleaned = m.copy()
    cleaned[~good] = 0.0
    cleaned = hp.remove_dipole(cleaned, fitval=False, verbose=False)
    packed = hp.map2alm(cleaned, lmax=args.lmax, iter=3)
    result = {}
    for ell in [int(x) for x in args.ells.split(",") if x.strip()]:
        a = full_alm_for_ell(hp, packed, ell, args.lmax)
        pole, vals = pole_from_alm(a, ell)
        result[str(ell)] = {"pole_cartesian_unoriented": pole.tolist(), "power_tensor_eigenvalues": vals.tolist()}
    print(json.dumps({"status": "PASS", "map": str(Path(args.map_fits).resolve()), "nside": args.nside, "lmax": args.lmax, "poles": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
