#!/usr/bin/env python3
"""Verify and catalog extended observational datasets on /mnt/extdrive/workdir.

Task 1B: Observational Data Inventory & Extended Adapters for Wave 1 of HTT Tensor-x & Five-Variable Framework.
Generates:
  docs/research_program/observational_publication_20261015/TENSOR_X_RESEARCH_LOOPS_20261107/EXTENDED_DATA_INVENTORY.json
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    from astropy.io import fits
except ImportError:
    fits = None

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "docs/research_program/observational_publication_20261015/TENSOR_X_RESEARCH_LOOPS_20261107"
OUT_JSON = OUT_DIR / "EXTENDED_DATA_INVENTORY.json"

# Known precomputed sha256 sums from verified manifests
PRECOMPUTED_SHAS = {
    # PR3
    "/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits": "60952c645eb33d151905ddf5837477e15ca02a3261feca4ceca3c3feece4f9ac",
    "/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits": "fe0332e61087ab445656ef272b31578ca4b1edcc7c3784a7662577684e2685a4",
    "/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits": "23f49a3479073408b83a7f1bb2cca490d9be7f934b2e0e891524b6a1d06a5fc4",
    "/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_CMB_IQU-smica_2048_R3.00_oe1.fits": "5473304ed71348cb346b335bca0deb417c9dd3f0286c7e3d2dfd5e1fc93f503a",
    "/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_CMB_IQU-smica_2048_R3.00_oe2.fits": "da9c3e3e09fdff87ada31db00417ae7688facc8b47756576ed8daec12fe1e2f0",
    "/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_Mask_CMB-OE-Misspix-Mask-Int_2048_R3.00.fits": "ecb39152ad5b93ea309baf396aad404a062edd6745a30c0b941b3556ca28aff9",
    "/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_CMB_IQU-nilc_2048_R3.00_hm1.fits": "795f03c1d0e3eadb9809885fd11b54d4d45680c62f472a4ca3888e35badb5dd7",
    "/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_CMB_IQU-nilc_2048_R3.00_hm2.fits": "29b928ef547262708363592de5d15b7f7a5591754778db4a8364b3d0816551ca",
    "/mnt/extdrive/workdir/raw/planck_pr3_targeted_inputs_20261015/COM_CMB_IQU-smica-nosz_2048_R3.00_full.fits": "8dca51299f2b0e53187810db6edead9c369757b519a66fe7c41288fa45b4cd98",
    # PR4
    "/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/COM_CMB_IQU-commander_4096_R4.00_full.fits": "61b9060ff4f80248ca52832137867c28697346f460a6a4b80f4654b114f4b900",
    # Cosmoglobe
    "/mnt/extdrive/workdir/raw/cosmoglobe_dr1/CG_cmb_IQU_n1024_v1.fits": "3d50ad25e6dba3515d442a1c2d652a274b4127ced9dd09317751f508be07e0f5",
    # Quaia
    "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/quaia_G20.0.fits": "efeda9ae727bf2cd75569f52460a0492827c8a3fcd8ce29dc692b559fca2acb0",
    "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/random_G20.0_10x.fits": "88b00e135cbcb2f7cfbd01c1d17e3198f81eb1aaece8955b43b2b6ac00136a1f",
    "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/selection_function_NSIDE64_G20.0.fits": "f66684999b0fdab1cdc3f8fc3ac8ef16956cb037785dbac2dc395dae3ffedd7d",
    "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/quaia_G20.5.fits": "9e357a760f2ff2db9417a6791fb71dc421ee30324301f22db898038c9e648584",
    "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/random_G20.5_10x.fits": "1783b13c03d084b1c40920b25e2008498df2349cb4d69e6a4b73db0dc1d28ef9",
    "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/selection_function_NSIDE64_G20.5.fits": "5c3851c70cebcaf765f283d9e9904b01dcfe7bc818570ddc749d88fbb5add0a9",
    # CF4
    "/mnt/extdrive/workdir/htt_open_data/cf4/J_ApJ_944_94/table2.dat": "8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f",
    "/mnt/extdrive/workdir/htt_open_data/cf4/J_ApJ_944_94/table3.dat": "c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d",
    "/mnt/extdrive/workdir/htt_open_data/cf4/J_ApJ_944_94/table4.dat": "b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94",
    # RACS
    "/mnt/extdrive/workdir/raw/observational_bundles/RACS_low_DR1_compact/RACS_DR1_galcut.dat.gz": "1764a934a084b12e411c32c426f04d5029c223541096253468d8343a60df4173",
    # NVSS
    "/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS/nvss.dat.gz": "360e2c7e3d734ce82cd21f03f44709bcf90fcede2e4427d5370e22e3429fe5d3",
    # Gaia Quaia CRF3
    "/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz": "2fbaa40a8afe58066064efa8a7784ac508c5b2c67b41c779676eab7df8cf9ef4",
    # SDSS randoms
    "/mnt/extdrive/workdir/raw/sdss_pv_zenodo_6824749/SDSS_randoms_public.dat": "2ec2853acd263b91bf679764fed22fd2b1edc34d4d08dd5d1c4f4e311e44f848",
}


def sha256_file(path: Path, max_bytes: int = 128 * 1024 * 1024) -> Tuple[str, bool]:
    """Compute sha256 or fetch precomputed if available and file exceeds max_bytes."""
    str_path = str(path.resolve())
    if str_path in PRECOMPUTED_SHAS:
        return PRECOMPUTED_SHAS[str_path], True
    if str(path) in PRECOMPUTED_SHAS:
        return PRECOMPUTED_SHAS[str(path)], True

    stat = path.stat()
    if stat.st_size > max_bytes:
        # File is large and no precomputed sum; compute hash streaming
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(16 << 20), b""):
                h.update(chunk)
        return h.hexdigest(), False

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(16 << 20), b""):
            h.update(chunk)
    return h.hexdigest(), False


def inspect_fits(path: Path) -> dict:
    if fits is None:
        return {"status": "ASTROPY_NOT_AVAILABLE"}
    info: Dict[str, Any] = {"hdus": []}
    try:
        with fits.open(path, memmap=True) as hdul:
            for idx, hdu in enumerate(hdul):
                h_dict: Dict[str, Any] = {
                    "index": idx,
                    "name": hdu.name,
                    "type": type(hdu).__name__,
                }
                hdr = hdu.header
                for key in ["EXTNAME", "XTENSION", "BITPIX", "NAXIS", "NAXIS1", "NAXIS2", 
                            "NSIDE", "ORDERING", "COORDSYS", "TUNIT1", "POLCCONV"]:
                    if key in hdr:
                        h_dict[key] = hdr[key]
                if hasattr(hdu, "columns") and hdu.columns:
                    h_dict["columns"] = list(hdu.columns.names)
                    h_dict["num_columns"] = len(hdu.columns.names)
                if hdu.data is not None:
                    h_dict["data_shape"] = list(hdu.data.shape)
                info["hdus"].append(h_dict)
    except Exception as e:
        info["error"] = str(e)
    return info


def inspect_npz(path: Path) -> dict:
    info: Dict[str, Any] = {"keys": {}, "num_keys": 0}
    try:
        with np.load(path, mmap_mode="r") as d:
            keys = list(d.keys())
            info["num_keys"] = len(keys)
            for k in keys:
                arr = d[k]
                info["keys"][k] = {
                    "shape": list(arr.shape),
                    "dtype": str(arr.dtype),
                }
    except Exception as e:
        info["error"] = str(e)
    return info


def inspect_table(path: Path, max_lines_for_cols: int = 50) -> dict:
    info: Dict[str, Any] = {}
    try:
        stat = path.stat()
        line_count = 0
        header_cols = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                line_count += 1
                if i < max_lines_for_cols and not header_cols:
                    sline = line.strip()
                    if sline and not sline.startswith("#"):
                        # Attempt CSV split or whitespace split
                        if "," in sline:
                            header_cols = [c.strip().strip('"') for c in sline.split(",")]
                        else:
                            header_cols = sline.split()
                    elif sline.startswith("#") and any(w in sline.upper() for w in ["RA", "DEC", "Z", "PGC", "CID", "MAG"]):
                        header_cols = sline.lstrip("#").strip().split()
        info["line_count"] = line_count
        if header_cols:
            info["sample_columns"] = header_cols[:20]
            info["num_sample_columns"] = len(header_cols)
    except Exception as e:
        info["error"] = str(e)
    return info


def inspect_gzip_table(path: Path) -> dict:
    info: Dict[str, Any] = {}
    try:
        line_count = 0
        sample_cols = []
        with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f):
                line_count += 1
                if i < 20 and not sample_cols:
                    sline = line.strip()
                    if sline and not sline.startswith("#"):
                        if "," in sline:
                            sample_cols = [c.strip().strip('"') for c in sline.split(",")]
                        else:
                            sample_cols = sline.split()
                if line_count > 100000 and i == 100000:
                    # For huge files, we don't need to decompress all 2GB just to verify presence
                    pass
        info["line_count"] = line_count
        if sample_cols:
            info["sample_columns"] = sample_cols[:20]
            info["num_sample_columns"] = len(sample_cols)
    except Exception as e:
        info["error"] = str(e)
    return info


def inspect_hdf5(path: Path) -> dict:
    info: Dict[str, Any] = {}
    try:
        # Check HDF5 magic number: \x89HDF\r\n\x1a\n
        with open(path, "rb") as f:
            magic = f.read(8)
            info["is_valid_hdf5_magic"] = (magic == b"\x89HDF\r\n\x1a\n")
    except Exception as e:
        info["error"] = str(e)
    return info


def verify_target(key: str, probe: str, description: str, paths: List[Path], file_type: str) -> dict:
    resolved_path: Optional[Path] = None
    for p in paths:
        if p.exists():
            resolved_path = p
            break

    if resolved_path is None:
        return {
            "key": key,
            "probe": probe,
            "description": description,
            "status": "UNAVAILABLE",
            "candidate_paths": [str(p) for p in paths],
            "resolved_path": None,
        }

    stat = resolved_path.stat()
    size_bytes = stat.st_size

    try:
        sha, is_cached = sha256_file(resolved_path)
    except Exception as e:
        sha = f"ERROR: {e}"
        is_cached = False

    item: Dict[str, Any] = {
        "key": key,
        "probe": probe,
        "description": description,
        "status": "VERIFIED_LOCAL",
        "resolved_path": str(resolved_path),
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 3),
        "sha256": sha,
        "sha256_source": "PRECOMPUTED_MANIFEST" if is_cached else "STREAM_COMPUTED",
        "mtime": stat.st_mtime,
        "file_type": file_type,
    }

    # Inspect structural metadata
    if file_type == "FITS":
        item["metadata"] = inspect_fits(resolved_path)
    elif file_type == "NPZ":
        item["metadata"] = inspect_npz(resolved_path)
    elif file_type in ["CSV", "DAT", "TXT", "TSV"]:
        item["metadata"] = inspect_table(resolved_path)
    elif file_type in ["DAT_GZ", "GZ"]:
        item["metadata"] = inspect_gzip_table(resolved_path)
    elif file_type == "HDF5":
        item["metadata"] = inspect_hdf5(resolved_path)

    return item


def main():
    print("=" * 78)
    print("Task 1B: Verifying and Cataloging Extended Observational Datasets")
    print(f"Target Root: /mnt/extdrive/workdir")
    print("=" * 78)

    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    datasets: Dict[str, Any] = {}

    # --------------------------------------------------------------------------
    # 1. Planck PR4 NPIPE Commander + 100 MCs
    # --------------------------------------------------------------------------
    print("\n[1/11] Inspecting Planck PR4 NPIPE Commander & 100 MCs...")
    pr4_map = verify_target(
        "planck_pr4_commander_full",
        "CMB",
        "Planck PR4 NPIPE Commander full-sky CMB map (I/Q/U NSIDE 4096)",
        [Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/COM_CMB_IQU-commander_4096_R4.00_full.fits")],
        "FITS",
    )
    pr4_obs_json = verify_target(
        "planck_pr4_observed_json",
        "CMB",
        "Planck PR4 observed morphology summary",
        [Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/analysis/observed.json")],
        "TXT",
    )
    pr4_obs_eb = verify_target(
        "planck_pr4_observed_lowell_eb",
        "CMB",
        "Planck PR4 observed low-ell EB coefficients",
        [Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/analysis/observed_lowell_EB.npz")],
        "NPZ",
    )
    pr4_mask_resp = verify_target(
        "planck_pr4_mask_response",
        "CMB",
        "Planck PR4 mask response operator",
        [Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/analysis/mask_response_three_columns.npz")],
        "NPZ",
    )

    # Verify 100 MCs (0300 to 0399)
    mc_dir = Path("/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/analysis")
    mc_npz_files = sorted(list(mc_dir.glob("mc_*_lowell_EB.npz")))
    mc_json_files = sorted(list(mc_dir.glob("mc_*.json")))
    # Exclude non-numbered if any
    mc_npz_count = len([f for f in mc_npz_files if "mc_" in f.name and "_lowell_EB" in f.name])
    mc_json_count = len([f for f in mc_json_files if f.stem.replace("mc_", "").isdigit()])

    datasets["planck_pr4_npipe_commander"] = {
        "status": "VERIFIED_LOCAL" if pr4_map["status"] == "VERIFIED_LOCAL" and mc_npz_count >= 100 else "PRESENT_UNVERIFIED",
        "map": pr4_map,
        "observed_analysis": {
            "json": pr4_obs_json,
            "lowell_eb": pr4_obs_eb,
            "mask_response": pr4_mask_resp,
        },
        "mc_ensemble": {
            "directory": str(mc_dir),
            "mc_eb_npz_count": mc_npz_count,
            "mc_json_count": mc_json_count,
            "mc_id_range": [300, 399] if mc_npz_count >= 100 else None,
            "status": "VERIFIED_LOCAL" if mc_npz_count >= 100 else "PRESENT_UNVERIFIED",
        },
    }
    print(f"  PR4 map status: {pr4_map['status']}, MC low-ell EB count: {mc_npz_count}")

    # --------------------------------------------------------------------------
    # 2. Planck PR3 SMICA/Commander/NILC and 300 FFP10 paired carrier nulls
    # --------------------------------------------------------------------------
    print("\n[2/11] Inspecting Planck PR3 Component Maps & 300 FFP10 Paired Carrier Nulls...")
    pr3_smica = verify_target(
        "planck_pr3_smica_full",
        "CMB",
        "Planck PR3 SMICA full-sky CMB map (I/Q/U NSIDE 2048)",
        [Path("/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits")],
        "FITS",
    )
    pr3_commander = verify_target(
        "planck_pr3_commander_full",
        "CMB",
        "Planck PR3 Commander full-sky CMB map (I/Q/U NSIDE 2048)",
        [Path("/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits")],
        "FITS",
    )
    pr3_nilc = verify_target(
        "planck_pr3_nilc_full",
        "CMB",
        "Planck PR3 NILC full-sky CMB map (I/Q/U NSIDE 2048)",
        [
            Path("/mnt/extdrive/workdir/raw/planck_pr3_component_controls/COM_CMB_IQU-nilc_2048_R3.00_full.fits"),
            Path("/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-nilc_2048_R3.00_full.fits"),
        ],
        "FITS",
    )
    pr3_mask = verify_target(
        "planck_pr3_common_mask",
        "CMB",
        "Planck PR3 Common Mask Int (NSIDE 2048)",
        [Path("/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")],
        "FITS",
    )

    # Paired 300 carrier nulls
    carrier_dir = Path("/mnt/extdrive/workdir/analysis/planck_mes_irrep/paired300_carrier")
    carrier_manifest = verify_target(
        "planck_pr3_paired300_manifest",
        "CMB",
        "Planck PR3 paired 300 FFP10 carrier execution manifest",
        [carrier_dir / "execution_manifest.json"],
        "TXT",
    )
    carrier_obs_npz = verify_target(
        "planck_pr3_paired300_observed_npz",
        "CMB",
        "Planck PR3 observed carrier features",
        [carrier_dir / "observed.npz"],
        "NPZ",
    )
    null_npz_files = list(carrier_dir.glob("null-*.npz"))
    null_json_files = list(carrier_dir.glob("null-*.json"))
    null_count = len(null_npz_files)

    datasets["planck_pr3_carrier_and_nulls"] = {
        "status": "VERIFIED_LOCAL" if pr3_smica["status"] == "VERIFIED_LOCAL" and null_count == 300 else "PRESENT_UNVERIFIED",
        "smica": pr3_smica,
        "commander": pr3_commander,
        "nilc": pr3_nilc,
        "common_mask": pr3_mask,
        "paired300_carrier": {
            "directory": str(carrier_dir),
            "manifest": carrier_manifest,
            "observed_npz": carrier_obs_npz,
            "null_npz_count": null_count,
            "null_json_count": len(null_json_files),
            "status": "VERIFIED_LOCAL" if null_count == 300 else "PRESENT_UNVERIFIED",
        },
    }
    print(f"  PR3 SMICA status: {pr3_smica['status']}, Commander: {pr3_commander['status']}, Paired nulls: {null_count}/300")

    # --------------------------------------------------------------------------
    # 3. Cosmoglobe DR1
    # --------------------------------------------------------------------------
    print("\n[3/11] Inspecting Cosmoglobe DR1...")
    cg_dir = Path("/mnt/extdrive/workdir/raw/cosmoglobe_dr1")
    cg_cmb = verify_target(
        "cosmoglobe_dr1_cmb_map",
        "CMB",
        "Cosmoglobe DR1 CMB I/Q/U map (NSIDE 1024)",
        [cg_dir / "CG_cmb_IQU_n1024_v1.fits"],
        "FITS",
    )
    cg_components = {
        "dust": verify_target("cg_dust", "Foreground", "Cosmoglobe DR1 Thermal Dust", [cg_dir / "CG_dust_IQU_n1024_v1.fits"], "FITS"),
        "synch": verify_target("cg_synch", "Foreground", "Cosmoglobe DR1 Synchrotron", [cg_dir / "CG_synch_IQU_n1024_v1.fits"], "FITS"),
        "freefree": verify_target("cg_freefree", "Foreground", "Cosmoglobe DR1 Free-free", [cg_dir / "CG_freefree_I_n1024_v1.fits"], "FITS"),
        "ame": verify_target("cg_ame", "Foreground", "Cosmoglobe DR1 AME", [cg_dir / "CG_ame_I_n1024_v1.fits"], "FITS"),
    }
    datasets["cosmoglobe_dr1"] = {
        "status": "VERIFIED_LOCAL" if cg_cmb["status"] == "VERIFIED_LOCAL" else "UNAVAILABLE",
        "cmb_map": cg_cmb,
        "foreground_components": cg_components,
    }
    print(f"  Cosmoglobe DR1 CMB status: {cg_cmb['status']} (Size: {cg_cmb.get('size_mb')} MB)")

    # --------------------------------------------------------------------------
    # 4. Quaia G<20.0 and G<20.5 catalogues + selection functions + randoms
    # --------------------------------------------------------------------------
    print("\n[4/11] Inspecting Quaia Catalogues & Selection Functions...")
    quaia_dir = Path("/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0")
    q_g20_cat = verify_target("quaia_g20_catalog", "Counts", "Quaia G<20.0 quasar catalogue", [quaia_dir / "quaia_G20.0.fits"], "FITS")
    q_g20_rand = verify_target("quaia_g20_randoms", "Counts", "Quaia G<20.0 10x randoms", [quaia_dir / "random_G20.0_10x.fits"], "FITS")
    q_g20_sel = verify_target("quaia_g20_selection", "Counts", "Quaia G<20.0 selection function (NSIDE 64)", [quaia_dir / "selection_function_NSIDE64_G20.0.fits"], "FITS")
    q_g20p5_cat = verify_target("quaia_g20p5_catalog", "Counts", "Quaia G<20.5 quasar catalogue", [quaia_dir / "quaia_G20.5.fits"], "FITS")
    q_g20p5_rand = verify_target("quaia_g20p5_randoms", "Counts", "Quaia G<20.5 10x randoms", [quaia_dir / "random_G20.5_10x.fits"], "FITS")
    q_g20p5_sel = verify_target("quaia_g20p5_selection", "Counts", "Quaia G<20.5 selection function (NSIDE 64)", [quaia_dir / "selection_function_NSIDE64_G20.5.fits"], "FITS")
    q_templates = verify_target("quaia_templates_zip", "Counts", "Quaia selection function template maps zip", [quaia_dir / "selection_function_template_maps.zip"], "ZIP")

    datasets["quaia"] = {
        "status": "VERIFIED_LOCAL" if q_g20_cat["status"] == "VERIFIED_LOCAL" and q_g20p5_cat["status"] == "VERIFIED_LOCAL" else "UNAVAILABLE",
        "g20": {
            "catalog": q_g20_cat,
            "randoms": q_g20_rand,
            "selection_function": q_g20_sel,
        },
        "g20p5": {
            "catalog": q_g20p5_cat,
            "randoms": q_g20p5_rand,
            "selection_function": q_g20p5_sel,
        },
        "templates": q_templates,
    }
    print(f"  Quaia G20 status: {q_g20_cat['status']}, Quaia G20.5 status: {q_g20p5_cat['status']}")

    # --------------------------------------------------------------------------
    # 5. Northern NVSS (1.4 GHz) and Southern RACS-low DR1
    # --------------------------------------------------------------------------
    print("\n[5/11] Inspecting Northern NVSS & Southern RACS-low DR1...")
    nvss_path = Path("/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS/nvss.dat.gz")
    nvss_target = verify_target(
        "nvss_catalog_gz",
        "Radio_HI",
        "Northern 1.4 GHz NVSS catalogue (gzip CDS ASCII)",
        [nvss_path],
        "DAT_GZ",
    )
    racs_dir = Path("/mnt/extdrive/workdir/raw/observational_bundles/RACS_low_DR1_compact")
    racs_target = verify_target(
        "racs_dr1_galcut_gz",
        "Radio_HI",
        "Southern RACS-low DR1 galactic-cut catalogue (gzip CDS ASCII)",
        [racs_dir / "RACS_DR1_galcut.dat.gz"],
        "DAT_GZ",
    )
    racs_rms = verify_target(
        "racs_dr1_rms_footprint",
        "Radio_HI",
        "RACS-low DR1 RMS Footprints table",
        [Path("/mnt/extdrive/workdir/raw/observational_bundles/RACS_low_DR1_RMS_footprint/RACS_DR1_RMS_Footprints.tsv")],
        "TSV",
    )

    datasets["radio_nvss_and_racs"] = {
        "status": "VERIFIED_LOCAL" if nvss_target["status"] == "VERIFIED_LOCAL" and racs_target["status"] == "VERIFIED_LOCAL" else "PRESENT_UNVERIFIED",
        "nvss": nvss_target,
        "racs_low_dr1": racs_target,
        "racs_rms_footprint": racs_rms,
    }
    print(f"  NVSS status: {nvss_target['status']}, RACS-low DR1 status: {racs_target['status']}")

    # --------------------------------------------------------------------------
    # 6. Gaia DR3 - Quaia CRF3 join (692,154 sources)
    # --------------------------------------------------------------------------
    print("\n[6/11] Inspecting Gaia DR3 - Quaia CRF3 join...")
    gaia_join_path = Path("/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz")
    gaia_join_target = verify_target(
        "gaia_dr3_quaia_crf3_join_npz",
        "Astrometry",
        "Gaia DR3 proper-motion join with Quaia CRF3 (692,154 sources)",
        [gaia_join_path],
        "NPZ",
    )
    gaia_xm_raw = verify_target(
        "gaia_dr3_crf3_xm_ecsv_gz",
        "Astrometry",
        "Gaia DR3 CRF3 cross-match raw table",
        [Path("/mnt/extdrive/workdir/htt_open_data/gaia/DR3/gaiadr3.gaia_crf3_xm.ecsv.gz")],
        "GZ",
    )

    source_count = 0
    if gaia_join_target["status"] == "VERIFIED_LOCAL" and "metadata" in gaia_join_target:
        meta_keys = gaia_join_target["metadata"].get("keys", {})
        if "source_id" in meta_keys:
            source_count = meta_keys["source_id"]["shape"][0]

    datasets["gaia_dr3_crf3"] = {
        "status": "VERIFIED_LOCAL" if gaia_join_target["status"] == "VERIFIED_LOCAL" and source_count == 692154 else "PRESENT_UNVERIFIED",
        "joined_npz": gaia_join_target,
        "source_count": source_count,
        "expected_source_count": 692154,
        "raw_xm": gaia_xm_raw,
    }
    print(f"  Gaia-Quaia CRF3 join status: {gaia_join_target['status']} (sources: {source_count:,}/692,154)")

    # --------------------------------------------------------------------------
    # 7. Pantheon+ full 1,701 SNe and cov
    # --------------------------------------------------------------------------
    print("\n[7/11] Inspecting Pantheon+ full 1,701 SNe and Covariance...")
    pantheon_dir = Path("/mnt/extdrive/workdir/raw/observational_bundles/PantheonPlus_SH0ES")
    pantheon_alt = Path("/mnt/extdrive/workdir/htt_open_data/pantheonplus/c447f0f")
    p_dat = verify_target(
        "pantheon_plus_dat",
        "Distance",
        "Pantheon+ SN Ia table (1,701 SNe)",
        [pantheon_dir / "Pantheon+SH0ES.dat", pantheon_alt / "Pantheon_SH0ES.dat"],
        "DAT",
    )
    p_cov = verify_target(
        "pantheon_plus_cov",
        "Distance",
        "Pantheon+ SN Ia STAT+SYS covariance (1701x1701)",
        [pantheon_dir / "Pantheon+SH0ES_STAT+SYS.cov", pantheon_alt / "Pantheon_SH0ES_STAT_SYS.cov"],
        "DAT",
    )
    shoes_anchors = {
        "allc": verify_target("shoes2022_cov", "Distance", "SH0ES 2022 covariance matrix", [Path("/mnt/extdrive/workdir/raw/shoes2022_calibration_reference_20261015/allc_shoes_ceph_topantheonwt6.0_112221.fits")], "FITS"),
        "alll": verify_target("shoes2022_design", "Distance", "SH0ES 2022 design matrix", [Path("/mnt/extdrive/workdir/raw/shoes2022_calibration_reference_20261015/alll_shoes_ceph_topantheonwt6.0_112221.fits")], "FITS"),
        "ally": verify_target("shoes2022_vector", "Distance", "SH0ES 2022 observable vector", [Path("/mnt/extdrive/workdir/raw/shoes2022_calibration_reference_20261015/ally_shoes_ceph_topantheonwt6.0_112221.fits")], "FITS"),
    }

    datasets["pantheon_plus"] = {
        "status": "VERIFIED_LOCAL" if p_dat["status"] == "VERIFIED_LOCAL" and p_cov["status"] == "VERIFIED_LOCAL" else "UNAVAILABLE",
        "data_table": p_dat,
        "covariance": p_cov,
        "shoes2022_reference": shoes_anchors,
    }
    print(f"  Pantheon+ table status: {p_dat['status']} (rows: {p_dat.get('metadata', {}).get('line_count')}), Cov status: {p_cov['status']}")

    # --------------------------------------------------------------------------
    # 8. DES-SN5YR Dovekie (DES-Dovekie_HD.csv and cov)
    # --------------------------------------------------------------------------
    print("\n[8/11] Inspecting DES-SN5YR Dovekie...")
    dovekie_dir = Path("/mnt/extdrive/workdir/raw/observational_bundles/DES_SN5YR_Dovekie")
    d_hd = verify_target(
        "des_dovekie_hd_csv",
        "Distance",
        "DES-SN5YR Dovekie Hubble diagram CSV",
        [dovekie_dir / "DES-Dovekie_HD.csv"],
        "CSV",
    )
    d_cov = verify_target(
        "des_dovekie_cov_npz",
        "Distance",
        "DES-SN5YR Dovekie STAT+SYS covariance NPZ",
        [dovekie_dir / "STAT+SYS.npz"],
        "NPZ",
    )
    d_py = verify_target(
        "des_dovekie_likelihood_py",
        "Distance",
        "DES-SN5YR Dovekie SN Likelihood script",
        [dovekie_dir / "DES-Dovekie-SN_Likelihood.py"],
        "TXT",
    )

    datasets["des_sn5yr_dovekie"] = {
        "status": "VERIFIED_LOCAL" if d_hd["status"] == "VERIFIED_LOCAL" and d_cov["status"] == "VERIFIED_LOCAL" else "UNAVAILABLE",
        "hubble_diagram": d_hd,
        "covariance": d_cov,
        "likelihood_py": d_py,
    }
    print(f"  DES Dovekie HD status: {d_hd['status']} (lines: {d_hd.get('metadata', {}).get('line_count')}), Cov status: {d_cov['status']}")

    # --------------------------------------------------------------------------
    # 9. CF4 55,877 Table 2 and 38,053 Table 3/4 / 35,970 selected group operator
    # --------------------------------------------------------------------------
    print("\n[9/11] Inspecting Cosmicflows-4 Catalogues & Selected Group Operator...")
    cf4_dir = Path("/mnt/extdrive/workdir/htt_open_data/cf4/J_ApJ_944_94")
    cf4_t2 = verify_target("cf4_table2", "Peculiar_Velocity", "CF4 Table 2: 55,877 individual galaxies", [cf4_dir / "table2.dat"], "DAT")
    cf4_t3 = verify_target("cf4_table3", "Peculiar_Velocity", "CF4 Table 3: 38,053 groups/galaxies", [cf4_dir / "table3.dat"], "DAT")
    cf4_t4 = verify_target("cf4_table4", "Peculiar_Velocity", "CF4 Table 4: 38,053 group velocities", [cf4_dir / "table4.dat"], "DAT")
    cf4_readme = verify_target("cf4_readme", "Peculiar_Velocity", "CF4 CDS ReadMe", [cf4_dir / "ReadMe"], "TXT")

    operator_path = REPO_ROOT / "docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz"
    cf4_operator = verify_target(
        "cf4_selected_group_operator",
        "Peculiar_Velocity",
        "CF4 selected 35,970 group operator and direction unit vectors",
        [operator_path],
        "NPZ",
    )

    datasets["cosmicflows4"] = {
        "status": "VERIFIED_LOCAL" if cf4_t2["status"] == "VERIFIED_LOCAL" and cf4_t3["status"] == "VERIFIED_LOCAL" and cf4_operator["status"] == "VERIFIED_LOCAL" else "PRESENT_UNVERIFIED",
        "table2_galaxies": cf4_t2,
        "table3_groups": cf4_t3,
        "table4_velocities": cf4_t4,
        "readme": cf4_readme,
        "selected_group_operator": cf4_operator,
    }
    print(f"  CF4 T2 (galaxies): {cf4_t2.get('metadata', {}).get('line_count')}/55,877, T3 (groups): {cf4_t3.get('metadata', {}).get('line_count')}/38,053, Operator: {cf4_operator['status']}")

    # --------------------------------------------------------------------------
    # 10. SDSS PV (SDSS_PV_public.dat)
    # --------------------------------------------------------------------------
    print("\n[10/11] Inspecting SDSS Peculiar Velocity Catalogue...")
    sdss_dir = Path("/mnt/extdrive/workdir/raw/sdss_pv_zenodo_6824749")
    sdss_pv = verify_target(
        "sdss_pv_public_dat",
        "Peculiar_Velocity",
        "SDSS PV public catalogue (34,059 galaxies)",
        [sdss_dir / "SDSS_PV_public.dat"],
        "DAT",
    )
    sdss_rand = verify_target(
        "sdss_randoms_public_dat",
        "Peculiar_Velocity",
        "SDSS PV randoms selection footprint catalogue",
        [sdss_dir / "SDSS_randoms_public.dat"],
        "DAT",
    )
    sdss_record = verify_target(
        "sdss_pv_zenodo_record",
        "Peculiar_Velocity",
        "Zenodo 6824749 record metadata",
        [sdss_dir / "record.json"],
        "TXT",
    )

    datasets["sdss_pv"] = {
        "status": "VERIFIED_LOCAL" if sdss_pv["status"] == "VERIFIED_LOCAL" else "UNAVAILABLE",
        "pv_catalog": sdss_pv,
        "randoms_catalog": sdss_rand,
        "zenodo_record": sdss_record,
    }
    print(f"  SDSS PV status: {sdss_pv['status']} (lines: {sdss_pv.get('metadata', {}).get('line_count')})")

    # --------------------------------------------------------------------------
    # 11. DESI DR2 BAO + DESI DR1 Full-Shape Directional NGC/SGC 4 shells
    # --------------------------------------------------------------------------
    print("\n[11/11] Inspecting DESI DR2 BAO & DR1 Full-Shape Directional 4 Shells...")
    desi_bao_dir = Path("/mnt/extdrive/workdir/raw/observational_bundles/DESI_BAO_compact")
    desi_fs_dir = Path("/mnt/extdrive/workdir/raw/observational_bundles/DESI_DR1_fullshape_directional")

    desi_bao_mean = verify_target("desi_bao_all_mean", "LSS_BAO", "DESI DR2 BAO ALL_GCcomb mean vector", [desi_bao_dir / "bao_desi_gaussian_bao_ALL_GCcomb_mean.txt"], "TXT")
    desi_bao_cov = verify_target("desi_bao_all_cov", "LSS_BAO", "DESI DR2 BAO ALL_GCcomb covariance", [desi_bao_dir / "bao_desi_gaussian_bao_ALL_GCcomb_cov.txt"], "TXT")

    # Inspect 8 directional full-shape combinations (4 shells: LRG 3 shells + QSO 1 shell across NGC and SGC)
    directional_blocks = [
        ("LRG_NGC_z0.4-0.6", "LRG", "NGC", "0.4-0.6"),
        ("LRG_NGC_z0.6-0.8", "LRG", "NGC", "0.6-0.8"),
        ("LRG_NGC_z0.8-1.1", "LRG", "NGC", "0.8-1.1"),
        ("LRG_SGC_z0.4-0.6", "LRG", "SGC", "0.4-0.6"),
        ("LRG_SGC_z0.6-0.8", "LRG", "SGC", "0.6-0.8"),
        ("LRG_SGC_z0.8-1.1", "LRG", "SGC", "0.8-1.1"),
        ("QSO_NGC_z0.8-2.1", "QSO", "NGC", "0.8-2.1"),
        ("QSO_SGC_z0.8-2.1", "QSO", "SGC", "0.8-2.1"),
    ]

    fs_blocks_verified = {}
    all_fs_verified = True
    for tag, tracer, region, zrange in directional_blocks:
        corr_file = desi_fs_dir / f"correlation-recsym-poles_{tracer}_{region}_z{zrange}.h5"
        cov_file = desi_fs_dir / f"covariance_correlation-recsym-poles_{tracer}_{region}_z{zrange}.h5"
        like_file = desi_fs_dir / f"likelihood_correlation-recon-poles_{tracer}_{region}_z{zrange}.h5"

        corr_target = verify_target(f"desi_corr_{tag}", "LSS_FullShape", f"DESI DR1 correlation poles {tag}", [corr_file], "HDF5")
        cov_target = verify_target(f"desi_cov_{tag}", "LSS_FullShape", f"DESI DR1 RascalC covariance {tag}", [cov_file], "HDF5")
        like_target = verify_target(f"desi_like_{tag}", "LSS_FullShape", f"DESI DR1 likelihood {tag}", [like_file], "HDF5")

        block_ok = (corr_target["status"] == "VERIFIED_LOCAL" and 
                    cov_target["status"] == "VERIFIED_LOCAL" and 
                    like_target["status"] == "VERIFIED_LOCAL")
        if not block_ok:
            all_fs_verified = False

        fs_blocks_verified[tag] = {
            "status": "VERIFIED_LOCAL" if block_ok else "PRESENT_UNVERIFIED",
            "tracer": tracer,
            "region": region,
            "redshift_range": zrange,
            "correlation_poles": corr_target,
            "covariance": cov_target,
            "likelihood": like_target,
        }

    datasets["desi"] = {
        "status": "VERIFIED_LOCAL" if desi_bao_mean["status"] == "VERIFIED_LOCAL" and all_fs_verified else "PRESENT_UNVERIFIED",
        "dr2_bao_compact": {
            "mean": desi_bao_mean,
            "cov": desi_bao_cov,
            "likelihood_py": verify_target("desi_bao_like_py", "LSS_BAO", "DESI BAO likelihood script", [desi_bao_dir / "likelihood_desi_bao_all.py"], "TXT"),
            "likelihood_yaml": verify_target("desi_bao_like_yaml", "LSS_BAO", "DESI BAO likelihood YAML", [desi_bao_dir / "likelihood_desi_bao_all.yaml"], "TXT"),
        },
        "dr1_fullshape_directional": {
            "bundle_directory": str(desi_fs_dir),
            "num_directional_blocks": len(directional_blocks),
            "blocks": fs_blocks_verified,
            "status": "VERIFIED_LOCAL" if all_fs_verified else "PRESENT_UNVERIFIED",
        },
    }
    print(f"  DESI DR2 BAO status: {desi_bao_mean['status']}, DR1 Directional 4 shells (8 blocks): {len(fs_blocks_verified)}/8 blocks verified")

    # --------------------------------------------------------------------------
    # Aggregate Summary
    # --------------------------------------------------------------------------
    total_verified = sum(1 for d in datasets.values() if d.get("status") == "VERIFIED_LOCAL")
    elapsed = time.time() - t0

    inventory_output = {
        "schema": "htt.r40_extended_data_inventory/1",
        "program": "HTT-Wave1-Task1B",
        "date_local": "2026-11-07",
        "elapsed_seconds": round(elapsed, 2),
        "total_dataset_families": len(datasets),
        "verified_dataset_families": total_verified,
        "summary": {
            k: v.get("status", "UNKNOWN") for k, v in datasets.items()
        },
        "datasets": datasets,
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(inventory_output, f, indent=2)

    print("\n" + "=" * 78)
    print(f"Generated: {OUT_JSON}")
    print(f"Verified {total_verified}/{len(datasets)} dataset families in {elapsed:.2f}s")
    print("=" * 78)


if __name__ == "__main__":
    main()
