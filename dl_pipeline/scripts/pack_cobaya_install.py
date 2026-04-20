#!/usr/bin/env python3
"""
pack_cobaya_install.py
======================

Wrap the BICEP/Keck and Planck-lensing data installed by cobaya-install
into a single NPZ each. Replaces the inline Python heredoc inside the
old download_obs_data.sh.

Usage:
    python pack_cobaya_install.py --module bicep_keck_2018 \\
        --packages-path ./cobaya_packages --out ./obs_extra/bicep_keck_2018_BB.npz
"""
from __future__ import annotations
import argparse
import glob
import os
from pathlib import Path
import numpy as np


# Search hints for each cobaya likelihood. The exact directory name varies
# by cobaya version; we search by glob if the canonical path is missing.
SEARCH_HINTS = {
    "bicep_keck_2018": [
        "data/bicep_keck_2018",
        "**/BK18*",
        "**/bicep*",
    ],
    "planck_2018_lensing.native": [
        "data/planck_2018_lensing_native",
        "data/planck_2018_lensing.native",
        "**/*lensing*",
        "**/*smicadx12*",
    ],
}


def find_data_dir(packages_path: Path, module: str) -> Path | None:
    hints = SEARCH_HINTS.get(module, [f"**/{module.split('.')[0]}*"])
    for hint in hints:
        # Direct path first
        cand = packages_path / hint
        if cand.is_dir():
            return cand
        # Then glob search
        for hit in glob.glob(str(packages_path / hint), recursive=True):
            if Path(hit).is_dir():
                return Path(hit)
    return None


def collect_files(root: Path) -> dict[str, str]:
    """Return {filename: absolute_path} for every file under root."""
    out = {}
    for r, _, files in os.walk(root):
        for f in files:
            out[f] = os.path.join(r, f)
    return out


def load_text(fpath: str) -> np.ndarray | None:
    try:
        arr = np.loadtxt(fpath, comments='#')
        return arr if isinstance(arr, np.ndarray) and arr.size > 0 else None
    except Exception:
        return None


def load_fits(fpath: str) -> dict[str, np.ndarray]:
    try:
        from astropy.io import fits
    except ImportError:
        return {}
    out = {}
    try:
        with fits.open(fpath) as hdul:
            for i, hdu in enumerate(hdul):
                if hdu.data is not None:
                    out[f"hdu{i}"] = np.array(hdu.data)
    except Exception:
        pass
    return out


def pack(module: str, packages_path: Path, out_path: Path) -> dict:
    data_dir = find_data_dir(packages_path, module)
    if data_dir is None or not data_dir.is_dir():
        raise SystemExit(
            f"[err] {module} data dir not found under {packages_path}. "
            f"Did cobaya-install {module} succeed?"
        )

    files = collect_files(data_dir)
    print(f"[info] {module}: found {len(files)} files in {data_dir}")

    payload: dict[str, np.ndarray] = {}
    for fname, fpath in files.items():
        if fname.endswith(('.txt', '.dat', '.csv')):
            arr = load_text(fpath)
            if arr is not None:
                payload[fname] = arr
        elif fname.endswith('.fits'):
            for k, v in load_fits(fpath).items():
                payload[f"{fname}_{k}"] = v

    if not payload:
        raise SystemExit(f"[err] no numeric arrays loaded from {data_dir}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        out_path,
        **payload,
        data_path=str(data_dir),
        file_list=list(files.keys()),
        source=f"{module} via cobaya-install",
    )
    print(f"[ok] {module} → {out_path} ({out_path.stat().st_size / 1024:.1f} KB, {len(payload)} arrays)")
    return {"module": module, "data_path": str(data_dir), "n_arrays": len(payload), "out": str(out_path)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", required=True,
                    help="cobaya likelihood module name (e.g. bicep_keck_2018)")
    ap.add_argument("--packages-path", default=os.path.expanduser("~/cobaya_packages"),
                    help="cobaya-install -p target")
    ap.add_argument("--out", required=True, help="output NPZ path")
    args = ap.parse_args()

    pack(args.module, Path(args.packages_path).expanduser().resolve(),
         Path(args.out).expanduser().resolve())


if __name__ == "__main__":
    main()
