#!/usr/bin/env python3
"""Acquire JWST distance-anchor catalogues (for CF4 cross-match) via the shared download
pattern (curl --retry + sha256 + manifest), mirroring `extract_cf4_full.py`.

JWST-based galaxy distances (CCHP TRGB/JAGB, SH0ES Cepheids, TRGB-SBF) are published as
IOPscience / arXiv machine-readable tables (not yet in VizieR as of 2026-07). This fetches
the authoritative tables when reachable and writes them to `workdir/raw/jwst_anchors/`
(gitignored) with a provenance manifest. When offline, the committed cited seed
`dl_pipeline/data/jwst_distances_seed.csv` preserves catalogue-linkage mechanics.

Targets (real, published):
  * Freedman et al. 2025, ApJ 985, 203  (CCHP JWST TRGB/JAGB), doi:10.3847/1538-4357/adce78
  * Riess et al. 2024/2025 (SH0ES JWST Cepheids)
  * Blakeslee et al. 2025 (TRGB-SBF Project III), arXiv:2502.15935

Diagnostic-only acquisition and catalogue linkage.  PR-120 blocks every CF4-conditioned
precision or global-tilt forecast while N-DATA-CF4-DOWNSTREAM remains OPEN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

REPO = Path(__file__).resolve().parents[2]
SEED = REPO / "dl_pipeline/data/jwst_distances_seed.csv"

# (label, url) authoritative machine-readable tables; kept explicit so provenance is auditable.
TARGETS = [
    ("cchp_freedman2025_t2",
     "https://iopscience.iop.org/article/10.3847/1538-4357/adce78/data/apjadce78t2_mrt.txt"),
    ("shoes_riess_jwst_cepheids",
     "https://arxiv.org/abs/2509.01667"),
    ("trgb_sbf_blakeslee2025",
     "https://arxiv.org/abs/2502.15935"),
]


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _download(url: str, dst: Path) -> bool:
    if dst.exists() and dst.stat().st_size > 0:
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    if shutil.which("curl"):
        rc = subprocess.run(["curl", "-sS", "-L", "--fail", "--retry", "4",
                             "--retry-delay", "5", "--max-time", "300",
                             "-o", str(dst), url]).returncode
        return rc == 0 and dst.exists() and dst.stat().st_size > 0
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw-dir", type=Path, default=REPO / "workdir/raw/jwst_anchors")
    args = ap.parse_args(argv)
    raw = args.raw_dir
    raw.mkdir(parents=True, exist_ok=True)

    fetched, missing = [], []
    for label, url in TARGETS:
        dst = raw / f"{label}{Path(url).suffix or '.txt'}"
        if _download(url, dst):
            fetched.append({"label": label, "url": url, "path": dst.name, "sha256": _sha256(dst)})
        else:
            missing.append({"label": label, "url": url})

    seed_present = SEED.is_file()
    manifest = {
        "product": "JWST distance anchors for CF4 cross-match",
        "fetched": fetched,
        "missing": missing,
        "seed_csv": str(SEED.relative_to(REPO)) if seed_present else None,
        "seed_sha256": _sha256(SEED) if seed_present else None,
        "status": "downloaded" if fetched else "seed_only_offline",
        "note": ("authoritative JWST tables are IOPscience/arXiv (not yet in VizieR); the "
                 "committed cited seed preserves catalogue-linkage mechanics offline. "
                 "Downstream public_use is false while N-DATA-CF4-DOWNSTREAM is OPEN; "
                 "no precision or global-tilt forecast is authorized."),
    }
    (raw / "jwst_anchors_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"JWST anchors: fetched {len(fetched)}, missing {len(missing)}, "
          f"seed={'present' if seed_present else 'ABSENT'} -> {raw}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
