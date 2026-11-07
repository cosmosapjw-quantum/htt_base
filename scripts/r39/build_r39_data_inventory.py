#!/usr/bin/env python3
"""Build exact local observational data inventory and manifests for R39.

Work Package D of HTT-R39 Observational Convergence.
Rehashes all local candidate files across 7 probe families:
Planck PR3/PR4, Quaia, Radio NVSS, CF4, Pantheon+, Gaia DR3/CRF3, and DESI DR2 BAO.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_R39 = REPO_ROOT / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_R39_20261107"
DOCS_R38 = REPO_ROOT / "docs/research_program/observational_publication_20261015/OBSERVATIONAL_CONVERGENCE_20261107"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(16 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    print("Starting exact local data rehash for HTT-R39...")
    r38_inv_path = DOCS_R38 / "LOCAL_DATA_INVENTORY.json"
    if not r38_inv_path.exists():
        print(f"Error: {r38_inv_path} not found")
        sys.exit(1)

    with open(r38_inv_path, "r", encoding="utf-8") as f:
        r38_data = json.load(f)

    r39_items = []
    sha256_entries = []
    total_bytes = 0

    for item in r38_data.get("items", []):
        p = Path(item["path"])
        if not p.exists():
            print(f"FAILED: missing local path {p}")
            sys.exit(1)
        
        stat = p.stat()
        actual_size = stat.st_size
        print(f"Rehashing: {item['key']} ({actual_size / (1024*1024):.2f} MB)...")
        actual_sha = sha256_file(p)
        
        if "sha256" in item and item["sha256"] != actual_sha:
            print(f"SHA mismatch for {item['key']}: expected {item['sha256']}, got {actual_sha}")
            sys.exit(1)

        total_bytes += actual_size
        new_item = dict(item)
        new_item["size_bytes"] = actual_size
        new_item["sha256"] = actual_sha
        new_item["status"] = "VERIFIED_LOCAL_R39"
        r39_items.append(new_item)
        sha256_entries.append(f"{actual_sha}  {p}")

    out_inv = {
        "schema": "htt.r39_local_data_inventory/1",
        "program": "HTT-R39",
        "date_local": "2026-11-07",
        "verified_items_count": len(r39_items),
        "total_verified_bytes": total_bytes,
        "items": r39_items,
    }

    out_inv_path = DOCS_R39 / "LOCAL_DATA_INVENTORY_R39.json"
    with open(out_inv_path, "w", encoding="utf-8") as f:
        json.dump(out_inv, f, indent=2)
    print(f"Saved {out_inv_path} ({len(r39_items)} items, {total_bytes / (1024**3):.3f} GB)")

    out_sha_path = DOCS_R39 / "PAYLOAD_SHA256SUMS_R39.txt"
    with open(out_sha_path, "w", encoding="utf-8") as f:
        f.write("\n".join(sha256_entries) + "\n")
    print(f"Saved {out_sha_path}")

    # Build Source-Bound Likelihood Manifest
    manifest = {
        "schema": "htt.r39_source_bound_likelihood_manifest/1",
        "program": "HTT-R39",
        "date_local": "2026-11-07",
        "status": "QUALIFIED_FAIL_CLOSED",
        "probes": {
            "CMB": {
                "dataset": "Planck PR4 Commander",
                "map_path": "/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/COM_CMB_IQU-commander_4096_R4.00_full.fits",
                "sha256": "4be7054dff31d5aa11df83e58c9b32115169a910ec3f631ff3d85d77ce0970a0",
                "mc_count": 100,
                "covariance_identity": "EMPIRICAL_FFP_NOISE_FOREGROUND_RESIDUAL",
                "modes": "ell=2,3 (quadrupole, octopole) T/E carriers",
            },
            "COUNTS": {
                "dataset": "Quaia G<20.0 + NVSS Radio",
                "quaia_path": "/mnt/extdrive/workdir/htt_open_data/quaia/quaia_G20.0.fits",
                "quaia_sha256": "ab186fa5b2f9fa2a0614068593a20728cbe9b736b42b6a67f0f6bbbe812d8a5c",
                "randoms_path": "/mnt/extdrive/workdir/htt_open_data/quaia/quaia_G20.0_randoms_10x.fits",
                "selection_map": "/mnt/extdrive/workdir/htt_open_data/quaia/quaia_G20.0_selection_nside64.fits",
                "nvss_path": "/mnt/extdrive/workdir/htt_open_data/radio/nvss.dat.gz",
                "tracer_kinematic_factor": "2 + x*(1 + alpha)",
            },
            "ASTROMETRY": {
                "dataset": "Gaia DR3 CRF3 Quasars",
                "path": "/mnt/extdrive/workdir/htt_open_data/gaia/quaia_crf3_join.npz",
                "sha256": "aa3346d0e653fbb8b8bb13b3d1b82fa7bba9b51fa16d1df3ddf4d6d62372d8a9",
                "source_count": 692154,
                "covariance_identity": "FULL_SOURCE_ASTROMETRIC_PMRA_PMDEC",
                "modes": "E1 glide, B1 spin, E2 shear",
            },
            "DISTANCE": {
                "pantheon_data": "/mnt/extdrive/workdir/htt_open_data/pantheonplus/Pantheon+SH0ES.dat",
                "pantheon_cov": "/mnt/extdrive/workdir/htt_open_data/pantheonplus/Pantheon+SH0ES_STAT+SYS.cov",
                "pantheon_sha256": "3cb611ec5a285d82fe6c3d5e23737b6a48f7f2b1d3dca4aa3bb519e49a888c03",
                "selected_block": "490 rows (z in [0.0233, 0.15]) 2-axis sliced",
                "cf4_operator": "/mnt/extdrive/workdir/htt_open_data/cf4/selected_source_observables.npz",
                "cf4_selected_groups": 35970,
            },
            "DESI": {
                "dataset": "DESI DR2 BAO ALL_GCcomb",
                "mean_path": "/mnt/extdrive/workdir/htt_open_data/desi/desi_dr2_mean.txt",
                "cov_path": "/mnt/extdrive/workdir/htt_open_data/desi/desi_dr2_cov.txt",
                "role": "ISOTROPIC_BACKGROUND_EXPANSION_ONLY",
                "sky_axis_leverage": "NONE_ISOTROPIC_COMPRESSION",
            }
        },
        "joint_likelihood_model": "p(D|theta_K, psi, eta) with conditional independence across disparate observable channels and shared latent parameters (theta_K, H0, M_abs, Omega_triad)",
    }

    manifest_path = DOCS_R39 / "SOURCE_BOUND_LIKELIHOOD_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved {manifest_path}")


if __name__ == "__main__":
    main()
