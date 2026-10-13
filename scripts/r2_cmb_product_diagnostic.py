#!/usr/bin/env python3
"""R2-03 actual reduced Planck PR3 controls; optional explicit dipole sensitivity."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from obsstat.r2_cmb_product_bridge import reduced_same_sky_diagnostic, sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controls", default="docs/generated/tensor_joint_r8/owned_controls/cmb/cmb_controls.npz")
    parser.add_argument("--metadata", default="docs/generated/tensor_joint_r8/owned_controls/cmb/cmb.json")
    parser.add_argument("--output", required=True)
    parser.add_argument("--T0-K", type=float)
    parser.add_argument("--dipole-K", type=float, nargs=3)
    parser.add_argument("--dipole-source-id")
    parser.add_argument("--hash-original-fits", action="store_true",
                        help="Optional exact replay provenance; reads multi-GB originals")
    args = parser.parse_args()
    result = reduced_same_sky_diagnostic(args.controls, args.metadata,
        T0_K=args.T0_K, dipole_K=args.dipole_K, dipole_source_id=args.dipole_source_id)
    from astropy.io import fits
    base = Path("/mnt/extdrive/workdir/raw/planck_data")
    raw = []
    for name in ("COM_CMB_IQU-smica_2048_R3.00_full.fits",
                 "COM_CMB_IQU-commander_2048_R3.00_full.fits",
                 "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"):
        path = base / name
        with fits.open(path, memmap=True) as hdus:
            header = hdus[1].header
            raw.append({"path": str(path),
                "sha256": sha256_file(path) if args.hash_original_fits else None,
                "sha256_status": "MEASURED" if args.hash_original_fits else "NOT_MEASURED_EXPLORATORY_SOURCE_IDENTITY",
                "header_sha256": hashlib.sha256(header.tostring().encode("ascii")).hexdigest(),
                "mtime_ns": path.stat().st_mtime_ns,
                "size": path.stat().st_size,
                "header": {key: header.get(key) for key in
                           ("NSIDE", "ORDERING", "COORDSYS", "TUNIT1", "TTYPE1")}})
    result["released_source_headers"] = raw
    result["released_source_usage"] = "source identity/header binding only; numerical controls reused from R8 reduction"
    result["runtime"] = {"interpreter": sys.executable,
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "requested_model": "gpt-6.1-sol", "requested_effort": "medium",
        "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN"}
    result["code_identities"] = {path: sha256_file(path) for path in
        ("htt/obsstat/r2_cmb_product_bridge.py", "htt/htt/htt/core/teff_invariants.py",
         "htt/htt/htt/core/teff_extended.py", "scripts/r2_cmb_product_diagnostic.py")}
    Path(args.output).write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"output": args.output, "pairs": len(result["contrasts"]),
                      "full_field": result["full_field_F4_status"],
                      "posterior": result["posterior_status"]}))


if __name__ == "__main__":
    main()
