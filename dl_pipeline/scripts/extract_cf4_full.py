#!/usr/bin/env python3
"""Download + parse the full Cosmicflows-4 release (VizieR J/ApJ/944/94).

Produces a release-hashed group catalog (table4: group distances + peculiar
velocities) as an npz for the LR-06D hierarchical bulk-flow likelihood. Tables:
  table2.dat  55877 individual-galaxy distances
  table3.dat  38053 group distances
  table4.dat  38053 group distances + peculiar velocities  <- parsed here

Idempotent: skips downloads when the .dat files already exist. No raw-data
analysis is performed here; this is acquisition + schema extraction only.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

# These scripts are run as files and are also loaded by path from repo-root
# tests, so the sibling import needs this directory on sys.path either way.
_SCRIPTS_DIR = str(Path(__file__).resolve().parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from external_store import ensure_data_dir

BASE = "https://cdsarc.cds.unistra.fr/ftp/J/ApJ/944/94"
TABLES = ("table2.dat", "table3.dat", "table4.dat")

# table4 fixed-width columns (1-indexed byte ranges from the VizieR ReadMe).
TABLE4_COLS = {
    "PGC": (1, 7), "DMzp": (9, 14), "e_DMzp": (16, 20), "Dist": (22, 26),
    "Vh": (28, 32), "Vls": (34, 38), "V3k": (40, 44), "Vpec": (65, 69),
    "RAdeg": (84, 91), "DEdeg": (93, 100), "GLON": (102, 109), "GLAT": (111, 118),
    "SGL": (120, 127), "SGB": (129, 136), "SGX": (138, 143), "SGY": (145, 150),
    "SGZ": (152, 157),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _download(url: str, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size > 0:
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("curl"):
        rc = subprocess.run(["curl", "-sS", "-L", "--fail", "--retry", "4",
                             "--retry-delay", "5", "--max-time", "300", "-o", str(dst), url]).returncode
        return rc == 0 and dst.exists() and dst.stat().st_size > 0
    return False


def _parse_table4(path: Path) -> dict[str, np.ndarray]:
    cols: dict[str, list] = {k: [] for k in TABLE4_COLS}
    with path.open(encoding="latin-1") as fh:
        for line in fh:
            if not line.strip():
                continue
            for name, (a, b) in TABLE4_COLS.items():
                tok = line[a - 1:b].strip()
                try:
                    cols[name].append(float(tok) if tok not in ("", "-") else np.nan)
                except ValueError:
                    cols[name].append(np.nan)
    return {k: np.asarray(v, dtype=float) for k, v in cols.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", type=Path, required=True, help="workdir/raw/cf4_full")
    ap.add_argument("--out", type=Path, required=True, help="output npz path")
    args = ap.parse_args(argv)
    raw = args.raw_dir
    ensure_data_dir(raw)

    _download(f"{BASE}/ReadMe", raw / "ReadMe")
    for t in TABLES:
        gz = raw / f"{t}.gz"
        dat = raw / t
        if not dat.exists():
            if _download(f"{BASE}/{t}.gz", gz):
                with gzip.open(gz, "rb") as fi, dat.open("wb") as fo:
                    shutil.copyfileobj(fi, fo)
    t4 = raw / "table4.dat"
    if not t4.exists():
        print("BLOCKED_MISSING_FULL_RELEASE_BINDING: table4.dat not available")
        return 1

    parsed = parsed4 = _parse_table4(t4)
    n = len(parsed["PGC"])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.out, **parsed)
    manifest = {
        "release": "Cosmicflows-4 (Tully+ 2023), VizieR J/ApJ/944/94",
        "table4_groups": n,
        "table4_sha256": _sha256(t4),
        "columns": list(TABLE4_COLS),
        "frames": ["Vh", "Vls", "V3k"],
        "out_npz": args.out.name,
        "out_sha256": _sha256(args.out),
    }
    (args.out.parent / "cf4_full_release_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"parsed {n} CF4 groups -> {args.out} (release_hash={manifest['table4_sha256'][:16]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
