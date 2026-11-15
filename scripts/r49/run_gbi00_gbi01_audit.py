#!/usr/bin/env python3
"""GBI-00 and GBI-01 audit script for HTT R49.

Produces in `docs/research_program/observational_publication_20261015/R49_GENERAL_TILTED_BIANCHI_20261112/`:
  - CURRENT_AUTHORITY.json
  - BIANCHI_CONVENTION_BRIDGE.json
  - TILT_CALLSITE_MAP.json
  - DATA_REHASH_RECEIPT.json
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any

from astropy.io import fits
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
for extra in (REPO_ROOT, REPO_ROOT / "htt", REPO_ROOT / "htt/src", REPO_ROOT / "htt/htt"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from bass.background import bianchi_types as bt, geometry as g
from bass.background.convention_bridge import (
    ALL_TWELVE_FAMILIES,
    PC_TO_VER2_PROPER_ROTATION,
    exact_spatial_ricci_from_compact,
    verify_all_families_convention_bridge,
)

R49_DIR = (
    REPO_ROOT
    / "docs/research_program/observational_publication_20261015/R49_GENERAL_TILTED_BIANCHI_20261112"
)
R48_MANIFEST_PATH = (
    REPO_ROOT
    / "docs/research_program/observational_publication_20261015/HTT_SIX_LOOP_INTEGRATED_20261109/RAW_DATA_MANIFEST.json"
)


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def inspect_fits_map_header(path: Path) -> dict[str, Any]:
    with fits.open(str(path), memmap=True) as hdul:
        hdr = hdul[1].header if len(hdul) > 1 else hdul[0].header
        return {
            "nside": int(hdr["NSIDE"]) if "NSIDE" in hdr else None,
            "ordering": str(hdr["ORDERING"]).strip() if "ORDERING" in hdr else None,
            "coordsys": str(hdr["COORDSYS"]).strip() if "COORDSYS" in hdr else None,
            "naxis2": int(hdr["NAXIS2"]) if "NAXIS2" in hdr else None,
            "tfields": int(hdr["TFIELDS"]) if "TFIELDS" in hdr else None,
        }


def build_current_authority() -> dict[str, Any]:
    head_sha = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    branch_name = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--abbrev-ref", "HEAD"], text=True
    ).strip()

    import astropy
    import camb
    import cobaya
    import emcee
    import healpy
    import scipy
    import sympy

    return {
        "schema_version": "r49_current_authority_v1",
        "worktree_path": str(REPO_ROOT),
        "branch": branch_name,
        "head_commit": head_sha,
        "primary_checkout_policy": {
            "primary_checkout": "/home/cosmosapjw/Dropbox/bianchi/htt_base",
            "must_remain_untouched": True,
            "auto_merge_to_main": False,
        },
        "python_environment": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "packages": {
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "healpy": healpy.__version__,
                "astropy": astropy.__version__,
                "emcee": emcee.__version__,
                "camb": camb.__version__,
                "cobaya": cobaya.__version__,
                "sympy": sympy.__version__,
            },
        },
        "physics_and_inference_authorities": {
            "algebra_and_types": "htt/bass/background/bianchi_types.py",
            "convention_bridge": "htt/bass/background/convention_bridge.py",
            "geometry_connection_route": "htt/bass/background/geometry.py",
            "r49_tilted_state": "htt/bass/background/tilted_bianchi_state.py",
            "r49_tilted_evolution": "htt/bass/background/general_tilted_evolution.py",
            "r49_polarized_transfer": "htt/bass/transport/general_bianchi_transfer.py",
            "r49_source_bound_likelihood_and_five_view": "htt/htt/htt/infer/r49_general_bianchi_likelihood.py",
            "legacy_scalar_tilt_quarantined": [
                "htt/bass/background/nonperturbative_tilt.py",
                "htt/bass/background/codazzi_tilt_rhs.py",
                "htt/bass/background/einstein_bianchi.py",
            ],
        },
        "cmb_lane_separation_policy": {
            "primary_calibrated_lane": {
                "observed_map": "/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits",
                "half_mission_splits": [
                    "/mnt/extdrive/workdir/raw/planck_pr3_smica_hm_20261015/COM_CMB_IQU-smica_2048_R3.00_hm1.fits",
                    "/mnt/extdrive/workdir/raw/planck_pr3_smica_hm_20261015/COM_CMB_IQU-smica_2048_R3.00_hm2.fits",
                ],
                "matched_simulations": "/mnt/extdrive/workdir/raw/planck_ffp10/smica/",
                "calibration_grade": "CALIBRATED_PR3_FFP10",
            },
            "secondary_robustness_lane": {
                "observed_maps": "/mnt/extdrive/workdir/raw/planck_npipe_pr4/frequency_maps/Single-frequency/",
                "npipe_smica_present": False,
                "npipe_mc_ensemble_present": False,
                "calibration_grade": "PR4_NULL_NOT_FORMABLE",
                "forbid_pr3_sims_for_pr4": True,
            },
        },
        "claim_guardrails": {
            "transfer_status": "transfer_conditional_pre_native_boltzmann_solver",
            "no_new_downloads": True,
            "chains_stored_outside_git_under": "/mnt/extdrive/workdir/r49_chains",
        },
    }


def build_convention_bridge_receipt() -> dict[str, Any]:
    bridge_res = verify_all_families_convention_bridge()
    legacy_geometry_discrepancies: dict[str, dict[str, Any]] = {}
    for name in bt.ALL_BIANCHI_TYPES:
        alg = bt.build_bianchi_algebra(name)
        geom = g.build_geometry(alg)
        R_exact, S_exact, _ = exact_spatial_ricci_from_compact(alg.a, alg.n, a_sign=1)
        legacy_err = float(geom.dual_route_curvature_residual_norm)
        exact_err = float(np.max(np.abs(geom.ricci_tensor - R_exact)))
        legacy_geometry_discrepancies[name] = {
            "class_label": alg.class_label,
            "legacy_compact_vs_connection_max_abs": legacy_err,
            "r49_exact_compact_vs_connection_max_abs": exact_err,
            "r49_exact_ricci_scalar": float(S_exact),
            "legacy_omitted_class_b_axn_offdiag": bool(legacy_err > 1.0e-12),
        }
    return {
        "schema_version": "r49_convention_bridge_receipt_v1",
        "proper_rotation_pc_to_ver2": PC_TO_VER2_PROPER_ROTATION.tolist(),
        "verification": bridge_res,
        "legacy_geometry_compact_bug_comparison": legacy_geometry_discrepancies,
    }


def build_tilt_callsite_map() -> dict[str, Any]:
    patterns = {
        "nonperturbative_tilt_scalar_6var": re.compile(r"nonperturbative_tilt|rhs_bianchi"),
        "codazzi_tilt_rhs_scalar": re.compile(r"codazzi_tilt_rhs|evolve_codazzi_tilt_background"),
        "species_tilt_pc_frame": re.compile(r"bass\.tilt\.species_tilt|total_momentum_constraint"),
        "scalar_beta_threshold": re.compile(r"beta_threshold|baryon_only_policy|velocity_to_rapidity|beta_tilt"),
        "ver2_vector_frame": re.compile(r"tilted_bianchi_state|general_tilted_evolution|project_species_to_normal_frame"),
        "relativistic_velocity_closure": re.compile(r"relativistic_velocity_closure|compose_velocities_sr"),
    }
    search_roots = [REPO_ROOT / "htt", REPO_ROOT / "scripts"]
    callsites_by_category: dict[str, list[str]] = {k: [] for k in patterns}
    total_scanned = 0
    for root in search_roots:
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            total_scanned += 1
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            rel = str(path.relative_to(REPO_ROOT))
            for cat, pat in patterns.items():
                if pat.search(text):
                    callsites_by_category[cat].append(rel)

    return {
        "schema_version": "r49_tilt_callsite_map_v1",
        "python_files_scanned": total_scanned,
        "categories": {
            cat: {
                "count": len(paths),
                "sample_paths": paths[:50],
                "all_paths": paths,
            }
            for cat, paths in callsites_by_category.items()
        },
        "scalar_vs_vector_classification": {
            "scalar_beta_legacy_paths": [
                "htt/bass/background/nonperturbative_tilt.py",
                "htt/bass/background/codazzi_tilt_rhs.py",
                "htt/bass/species/tilted.py",
                "htt/bass/tilt/baryon_only_policy.py",
            ],
            "vector_3d_pc_frame_paths": [
                "htt/bass/tilt/species_tilt.py",
                "htt/src/common/relativistic_velocity_closure.py",
            ],
            "r49_multi_congruence_general_paths": [
                "htt/bass/background/convention_bridge.py",
                "htt/bass/background/tilted_bianchi_state.py",
                "htt/bass/background/general_tilted_evolution.py",
                "htt/bass/transport/general_bianchi_transfer.py",
            ],
        },
    }


def build_data_rehash_receipt() -> dict[str, Any]:
    r48_manifest = {}
    if R48_MANIFEST_PATH.exists():
        r48_manifest = json.loads(R48_MANIFEST_PATH.read_text(encoding="utf-8"))

    # Primary datasets to hash directly on disk (small/medium files + PR3 SMICA observed/HM).
    files_to_hash = {
        "pr3_smica_full": "/mnt/extdrive/workdir/raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits",
        "pr3_smica_hm1": "/mnt/extdrive/workdir/raw/planck_pr3_smica_hm_20261015/COM_CMB_IQU-smica_2048_R3.00_hm1.fits",
        "pr3_smica_hm2": "/mnt/extdrive/workdir/raw/planck_pr3_smica_hm_20261015/COM_CMB_IQU-smica_2048_R3.00_hm2.fits",
        "pr3_mask_int": "/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits",
        "pr3_mask_pol": "/mnt/extdrive/workdir/raw/planck_data/COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits",
        "pr3_hfi_rimo": "/mnt/extdrive/workdir/raw/planck_pr3_ancillary_20261110/HFI_RIMO_R3.00.fits",
        "pr3_theory_cl": "/mnt/extdrive/workdir/raw/planck_data/COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt",
        "pr3_nilc_full": "/mnt/extdrive/workdir/raw/planck_pr3_component_maps_20261110/COM_CMB_IQU-nilc_2048_R3.00_full.fits",
        "pr3_sevem_full": "/mnt/extdrive/workdir/raw/planck_pr3_component_maps_20261110/COM_CMB_IQU-sevem_2048_R3.00_full.fits",
        "quaia_g200": "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/quaia_G20.0.fits",
        "quaia_g205": "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/quaia_G20.5.fits",
        "quaia_sel_g200": "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/selection_function_NSIDE64_G20.0.fits",
        "quaia_sel_g205": "/mnt/extdrive/workdir/raw/observational_bundles/Quaia_zenodo_10403370_v1.0.0/selection_function_NSIDE64_G20.5.fits",
        "nvss_catalog": "/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS_nrao_20261110/CATALOG.FIT",
        "racs_galcut": "/mnt/extdrive/workdir/raw/observational_bundles/RACS_low_DR1_compact/RACS_DR1_galcut.dat.gz",
        "racs_footprints": "/mnt/extdrive/workdir/raw/observational_bundles/RACS_low_DR1_RMS_footprint/RACS_DR1_RMS_Footprints.tsv",
        "gaia_crf3_full": "/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits",
        "quaia_crf3_join_npz": "/mnt/extdrive/workdir/htt_open_data/a22_20261023/quaia_join/quaia_crf3_join.npz",
        "icrf3_sx": "/mnt/extdrive/workdir/raw/icrf3_iers_20261110/icrf3sx.txt",
        "pantheon_dat": "/mnt/extdrive/workdir/raw/pantheonplus_release_c447f0f_20261110/Pantheon+SH0ES.dat",
        "pantheon_cov": "/mnt/extdrive/workdir/raw/pantheonplus_release_c447f0f_20261110/Pantheon+SH0ES_STAT+SYS.cov",
        "cf4_mean_std_grids": "/mnt/extdrive/workdir/raw/cf4/CF4pp_mean_std_grids.npz",
        "cf4_table2": "/mnt/extdrive/workdir/raw/cf4_full/table2.dat",
        "cf4_table3": "/mnt/extdrive/workdir/raw/cf4_full/table3.dat",
        "cf4_table4": "/mnt/extdrive/workdir/raw/cf4_full/table4.dat",
    }

    records: dict[str, Any] = {}
    all_present = True
    for key, path_str in files_to_hash.items():
        p = Path(path_str)
        if not p.exists():
            all_present = False
            records[key] = {"path": path_str, "exists": False}
            continue
        rec: dict[str, Any] = {
            "path": path_str,
            "exists": True,
            "size_bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        }
        if key.startswith("pr3_smica") or key.startswith("pr3_mask"):
            rec["fits_map_header"] = inspect_fits_map_header(p)
        records[key] = rec

    # FFP10 SMICA inventory and SHA256SUMS reconciliation
    ffp10_root = Path("/mnt/extdrive/workdir/raw/planck_ffp10/smica")
    cmb_files = sorted((ffp10_root / "cmb_mc").glob("dx12_v3_smica_cmb_mc_*_raw.fits"))
    noise_files = sorted((ffp10_root / "noise_mc").glob("dx12_v3_smica_noise_mc_*_raw.fits"))
    sum_file = ffp10_root / "logs/SHA256SUMS.raw_fits.available1299.txt"
    sum_map: dict[str, str] = {}
    if sum_file.exists():
        for line in sum_file.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                sum_map[Path(parts[1]).name] = parts[0]

    cmb_ids = {p.name.split("_")[-2] for p in cmb_files}
    noise_ids = {p.name.split("_")[-2] for p in noise_files}
    matched_ids = sorted(cmb_ids & noise_ids)

    spot_checks = {}
    for idx_label, path in (
        ("cmb_00000", ffp10_root / "cmb_mc/dx12_v3_smica_cmb_mc_00000_raw.fits"),
        ("cmb_00299", ffp10_root / "cmb_mc/dx12_v3_smica_cmb_mc_00299_raw.fits"),
        ("noise_00000", ffp10_root / "noise_mc/dx12_v3_smica_noise_mc_00000_raw.fits"),
        ("noise_00299", ffp10_root / "noise_mc/dx12_v3_smica_noise_mc_00299_raw.fits"),
    ):
        if path.exists():
            computed = sha256_file(path)
            recorded = sum_map.get(path.name)
            spot_checks[idx_label] = {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256_computed": computed,
                "sha256_manifest": recorded,
                "manifest_match": (computed == recorded),
                "fits_map_header": inspect_fits_map_header(path),
            }

    # PR4 NPIPE single-frequency inventory + header + size audit + sample sha256
    npipe_dir = Path("/mnt/extdrive/workdir/raw/planck_npipe_pr4/frequency_maps/Single-frequency")
    npipe_records: dict[str, Any] = {}
    for p in sorted(npipe_dir.glob("HFI_SkyMap_*_2048_R4.00_*.fits")):
        npipe_records[p.name] = {
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "fits_map_header": inspect_fits_map_header(p),
        }
    npipe_rimo = Path("/mnt/extdrive/workdir/raw/planck_npipe_pr4/misc/PLANCK_RIMO_TF_R4.00.tar.gz")
    npipe_mask_512 = Path("/mnt/extdrive/workdir/raw/planck_npipe_pr4/misc/mask_PR4_Lollipop_ns512.fits")

    # DESI compact / fullshape file listing
    desi_compact = sorted(
        str(p)
        for p in Path("/mnt/extdrive/workdir/raw/observational_bundles/DESI_BAO_compact").rglob("*")
        if p.is_file()
    )
    desi_dir = sorted(
        str(p)
        for p in Path("/mnt/extdrive/workdir/raw/observational_bundles/DESI_DR1_fullshape_directional").rglob("*")
        if p.is_file()
    )

    return {
        "schema_version": "r49_data_rehash_receipt_v1",
        "all_primary_files_present": all_present,
        "r48_manifest_path": str(R48_MANIFEST_PATH) if R48_MANIFEST_PATH.exists() else None,
        "r48_manifest_keys": sorted(r48_manifest.keys()) if isinstance(r48_manifest, dict) else [],
        "hashed_primary_files": records,
        "ffp10_smica_inventory": {
            "cmb_mc_count": len(cmb_files),
            "noise_mc_count": len(noise_files),
            "matched_pair_count": len(matched_ids),
            "matched_id_range": [matched_ids[0], matched_ids[-1]] if matched_ids else [],
            "sha256_manifest_entries": len(sum_map),
            "spot_checks": spot_checks,
        },
        "npipe_pr4_inventory": {
            "single_frequency_maps": npipe_records,
            "rimo_tf_r4_tar_gz": {
                "path": str(npipe_rimo),
                "exists": npipe_rimo.exists(),
                "size_bytes": npipe_rimo.stat().st_size if npipe_rimo.exists() else None,
                "sha256": sha256_file(npipe_rimo) if npipe_rimo.exists() else None,
            },
            "lollipop_mask_ns512": {
                "path": str(npipe_mask_512),
                "exists": npipe_mask_512.exists(),
                "size_bytes": npipe_mask_512.stat().st_size if npipe_mask_512.exists() else None,
                "sha256": sha256_file(npipe_mask_512) if npipe_mask_512.exists() else None,
            },
        },
        "desi_files": {
            "bao_compact": desi_compact[:30],
            "dr1_fullshape_directional": desi_dir[:30],
        },
    }


def main() -> int:
    t0 = time.monotonic()
    R49_DIR.mkdir(parents=True, exist_ok=True)

    auth = build_current_authority()
    (R49_DIR / "CURRENT_AUTHORITY.json").write_text(json.dumps(auth, indent=2), encoding="utf-8")

    bridge = build_convention_bridge_receipt()
    (R49_DIR / "BIANCHI_CONVENTION_BRIDGE.json").write_text(
        json.dumps(bridge, indent=2), encoding="utf-8"
    )
    if not bridge["verification"]["all_passed"]:
        print("ERROR: convention bridge verification failed!", file=sys.stderr)
        return 1

    calls = build_tilt_callsite_map()
    (R49_DIR / "TILT_CALLSITE_MAP.json").write_text(json.dumps(calls, indent=2), encoding="utf-8")

    rehash = build_data_rehash_receipt()
    (R49_DIR / "DATA_REHASH_RECEIPT.json").write_text(json.dumps(rehash, indent=2), encoding="utf-8")

    dt = time.monotonic() - t0
    print(
        f"GBI-00/01 audit PASS in {dt:.2f}s | families={len(ALL_TWELVE_FAMILIES)} "
        f"| ffp10_pairs={rehash['ffp10_smica_inventory']['matched_pair_count']} "
        f"| py_scanned={calls['python_files_scanned']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
