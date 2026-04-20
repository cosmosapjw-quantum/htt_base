#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np

try:
    from astropy.io import fits
except Exception as e:
    raise SystemExit("astropy is required: pip install astropy") from e


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def lower_map(names):
    return {str(n).lower(): str(n) for n in names}


def read_fits_table(path: Path):
    with fits.open(path, memmap=True) as hdul:
        data = hdul[1].data
        cols = list(data.columns.names)
        return data, cols


def get_col(data, cmap, candidates, required=True, default=None):
    for cand in candidates:
        key = cand.lower()
        if key in cmap:
            return np.asarray(data[cmap[key]])
    if required:
        raise KeyError(f"Missing required columns; tried {candidates}")
    if default is None:
        return None
    return np.asarray(default)


def build_nhat(ra_deg, dec_deg):
    ra = np.deg2rad(ra_deg)
    dec = np.deg2rad(dec_deg)
    cosd = np.cos(dec)
    return np.stack([cosd*np.cos(ra), cosd*np.sin(ra), np.sin(dec)], axis=1).astype(np.float32)


def cast_or_none(arr, dtype):
    if arr is None:
        return None
    return np.asarray(arr, dtype=dtype)


def process_one(path: Path, outdir: Path, mode: str):
    data, cols = read_fits_table(path)
    cmap = lower_map(cols)

    ra = get_col(data, cmap, ["RA"])
    dec = get_col(data, cmap, ["DEC"])
    z = get_col(data, cmap, ["Z", "Z_not4clus"], required=True)

    weight = get_col(
        data, cmap,
        ["WEIGHT", "WEIGHT_COMP", "WEIGHT_SYS", "WEIGHT_ZFAIL"],
        required=False,
        default=np.ones(len(ra), dtype=np.float32),
    )

    nhat = build_nhat(ra, dec)

    payload = {
        "ra": np.asarray(ra, dtype=np.float32),
        "dec": np.asarray(dec, dtype=np.float32),
        "z": np.asarray(z, dtype=np.float32),
        "weight": np.asarray(weight, dtype=np.float32),
        "n_hat": nhat,
    }

    if mode == "extended":
        payload["weight_fkp"] = cast_or_none(get_col(data, cmap, ["WEIGHT_FKP"], required=False), np.float32)
        payload["weight_sys"] = cast_or_none(get_col(data, cmap, ["WEIGHT_SYS"], required=False), np.float32)
        payload["weight_zfail"] = cast_or_none(get_col(data, cmap, ["WEIGHT_ZFAIL"], required=False), np.float32)
        payload["targetid"] = cast_or_none(get_col(data, cmap, ["TARGETID"], required=False), np.int64)
        payload["ntile"] = cast_or_none(get_col(data, cmap, ["NTILE"], required=False), np.int16)
        photsys = get_col(data, cmap, ["PHOTSYS"], required=False)
        if photsys is not None:
            payload["photsys"] = np.asarray(photsys)

    out = outdir / (path.name.replace(".fits", "").replace(".dat", "") + f"_{mode}.npz")
    np.savez(out, **payload)

    manifest = {
        "source": str(path),
        "out": str(out),
        "mode": mode,
        "fields": list(payload.keys()),
        "n_rows": int(len(ra)),
    }
    return manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True, help="Directory containing DESI *clustering.dat.fits files")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mode", choices=["minimal", "extended"], default="extended",
                    help="extended (default): keep FKP/sys/zfail weights, targetid, "
                         "ntile, photsys. minimal: strip to ra/dec/z/weight/n_hat only "
                         "(sandbox-era default; use only if disk is tight).")
    ap.add_argument("--glob", default="*_clustering.dat.fits")
    args = ap.parse_args()

    input_dir = Path(args.input_dir)
    outdir = Path(args.outdir)
    ensure_dir(outdir)

    manifests = []
    for path in sorted(input_dir.glob(args.glob)):
        manifests.append(process_one(path, outdir, args.mode))

    man_path = outdir / f"desi_compact_manifest_{args.mode}.json"
    man_path.write_text(json.dumps(manifests, indent=2, ensure_ascii=False))
    print(f"[done] wrote {len(manifests)} compact files")
    print(man_path)


if __name__ == "__main__":
    main()
