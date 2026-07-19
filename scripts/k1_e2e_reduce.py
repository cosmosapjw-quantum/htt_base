#!/usr/bin/env python3
"""K1 E2E footprint reduction: raw FFP10/NPIPE maps -> registered low-ell cache.

The registered PR-150 K1 estimator's FIRST step downgrades each raw Nside=2048
IQU map directly to NSIDE=64 before computing the registered masked ell<=30 statistics
(`k1_global_maxscan._load_sim_map` -> `ud_grade`). The raw ~1 TB FITS therefore carry
NOTHING the low-ell analysis uses beyond that downgraded, low-ell content. This script
reduces each raw simulation to a compact registered-estimator cache so the
731 GB PR3 (FFP10) download can be deleted later, after both the compact-replay
and separate PR4 replacement-ready gates pass, and so the
downstream estimator revisions (roadmap PR-135 exchangeable null, PR-149 canonical
convention/mask, PR-150 E2E calibration) can recompute new statistics / re-mask
WITHOUT re-downloading.

Two retention tiers are written (see docs/research_program/K1_E2E_REPRODUCIBILITY_RETENTION.md):

  * Tier-2 (registered-estimator input, ~1 GB including replay files, kept on the
    NVMe): the direct PRE-MASK NSIDE=64 float64 I-map + ell<=8 a_lm for every
    realization, keyed by parsed MC id, with per-raw-file SHA256 provenance and
    directly consumable per-realization NPZ replay files.  No staged-downgrade
    associativity assumption is used.  A combined cache is copied to a second
    filesystem when ``--backup-dir`` is supplied.
  * Auxiliary component receipt (committed under docs/generated/): legacy
    unmasked NSIDE16 component statistics plus config/cache hashes and all raw
    input hashes. This is not the registered PR-150 result matrix. The cache gate
    writes the authoritative paired 999x6 precision receipt after full replay.

Usage (reduce the FFP10 SMICA CMB MC + noise MC while PR3 is still on disk):

    venv/bin/python scripts/k1_e2e_reduce.py \\
        --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \\
        --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc \\
        --method smica --ensemble ffp10 \\
        --cache-dir /mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced

Then run scripts/k1_e2e_cache_gate.py.  Even a green compact-reproducibility gate
does not permit immediate deletion: raw PR3 stays until an authenticated PR4
replacement-ready receipt is also supplied.  The gate never deletes files.
The same reducer serves the NPIPE (PR4) K1-usable product (component-separated CMB
sims or a single cleaned channel) -- pass --ensemble npipe.

Deterministic; --check verifies that the committed provenance manifest exists.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# reuse the EXACT estimator load path + helpers so the cache is faithful by construction
import k1_global_maxscan as k1  # noqa: E402
import make_lowell_morphology_real_map as rm  # noqa: E402

REDUCE_NSIDE = 64           # exact first transform of the registered PR-150 run
# Auxiliary unmasked a_lm ceiling only. The retained NSIDE64 float64 maps are
# authoritative and replay the registered masked ell_max=30 estimator.
LMAX_CACHE = 8
GEN = REPO_ROOT / "docs/generated"
EXPECTED_PR150_CMB_IDS = set(range(1000)) - {970}
EXPECTED_PR150_NOISE_IDS = set(range(300))


def _reduce_dir(sim_dir: Path, reduce_nside: int, lmax: int, max_sims: int | None):
    """Downgrade every raw sim in ``sim_dir`` to ``reduce_nside`` via the estimator's own
    load path and compute a_lm to ``lmax``. Returns (ids, maps[n,npix] f32,
    alm[n,nalm] c64, provenance[list])."""
    files = k1._list_sims(sim_dir)
    files = sorted(files, key=k1._parse_mc_id)
    if max_sims is not None:
        files = files[:max_sims]
    if not files:
        raise FileNotFoundError(f"no sims (*.fits/*.fits.gz/*.npz) in {sim_dir}")
    npix = rm.hp.nside2npix(reduce_nside)
    nalm = rm.hp.Alm.getsize(lmax)
    # maps stored float64 so the cache reproduces the from-raw statistics BIT-EXACTLY
    # (float32 would inject ~1e-5 storage rounding and fail the faithful-cache gate that
    # authorizes deleting 1 TB of raw); a_lm are an auxiliary convenience -> complex64.
    maps = np.empty((len(files), npix), dtype=np.float64)
    alm = np.empty((len(files), nalm), dtype=np.complex64)
    ids: list[int] = []
    prov: list[dict] = []
    for i, f in enumerate(files):
        mc_id = k1._parse_mc_id(f)
        m = k1._load_sim_map(f, reduce_nside)          # EXACT estimator load path (uK)
        maps[i] = m
        alm[i] = rm.hp.map2alm(m, lmax=lmax, iter=0).astype(np.complex64)
        ids.append(mc_id)
        prov.append({"file": f.name, "mc_id": mc_id, "input_hash": k1._sha256_file(f)})
    return np.asarray(ids, dtype=int), maps, alm, prov


def _tier1_stats(ids: np.ndarray, maps: np.ndarray, reduce_nside: int):
    """Legacy unmasked component statistics retained as an auxiliary receipt.

    These per-component NSIDE16 values are not the masked, paired, ell_max=30
    PR-150 precision matrix and must never be used as its scientific receipt.
    """
    keys = list(rm.TAILS)
    pix = np.asarray(rm.hp.pix2vec(rm.NSIDE, np.arange(rm.hp.nside2npix(rm.NSIDE)))).T
    obs_defaults = json.loads(rm.OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    apex = np.asarray(rm.lb_to_unitvec(np.array(cmb["l_deg"]),
                                       np.array(cmb["b_deg"])), float).reshape(3)
    rows = []
    for m in maps:
        m16 = rm.hp.ud_grade(np.asarray(m, float), nside_out=rm.NSIDE)
        s = rm.compute_map_statistics(m16, pix, apex)
        rows.append([float(s[k]) for k in keys])
    return keys, np.asarray(rows, dtype=float)


def _arr_hash(a: np.ndarray) -> str:
    return "sha256:" + hashlib.sha256(np.ascontiguousarray(a)).hexdigest()


def _validate_pr150_inventory(parts: dict[str, tuple[np.ndarray, np.ndarray,
                                                     np.ndarray, list[dict]]]) -> None:
    expected = {"cmb": EXPECTED_PR150_CMB_IDS, "noise": EXPECTED_PR150_NOISE_IDS}
    for label, required in expected.items():
        if label not in parts:
            raise ValueError(f"PR150 compact pack requires the {label} ensemble")
        ids = [int(value) for value in parts[label][0]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate {label} MC ids in PR150 input")
        present = set(ids)
        if present != required:
            raise ValueError(
                f"PR150 {label} inventory mismatch: missing={sorted(required - present)} "
                f"extra={sorted(present - required)}")


def _write_replay_files(cache_dir: Path, ensemble: str, method: str,
                        label: str, ids: np.ndarray, maps: np.ndarray,
                        reduce_nside: int) -> list[dict]:
    out = cache_dir / f"k1_{ensemble}_{method}_replay" / f"{label}_mc"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for mc_id, array in zip(ids, maps):
        path = out / f"dx12_v3_{method}_{label}_mc_{int(mc_id):05d}.npz"
        temp = path.with_suffix(path.suffix + ".tmp")
        with temp.open("wb") as handle:
            np.savez(handle, I=np.asarray(array, dtype=np.float64), unit="uK",
                     mc_id=np.asarray(int(mc_id)), nside=np.asarray(reduce_nside))
        temp.replace(path)
        rows.append({"mc_id": int(mc_id), "path": str(path),
                     "file_hash": k1._sha256_file(path),
                     "array_hash": _arr_hash(np.asarray(array, dtype=np.float64))})
    return rows


def build(cmb_dir: Path | None, noise_dir: Path, method: str, ensemble: str,
          cache_dir: Path, reduce_nside: int, lmax: int, max_sims: int | None,
          *, require_pr150_inventory: bool = False,
          backup_dir: Path | None = None) -> dict:
    parts: dict[str, dict] = {}
    reduced: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]] = {}
    payload_arrays: dict[str, np.ndarray] = {}
    auxiliary: dict[str, dict] = {}
    for label, d in (("noise", noise_dir), ("cmb", cmb_dir)):
        if d is None:
            continue
        ids, maps, alm, prov = _reduce_dir(d, reduce_nside, lmax, max_sims)
        reduced[label] = (ids, maps, alm, prov)
        payload_arrays[f"{label}_ids"] = ids
        payload_arrays[f"{label}_maps"] = maps
        payload_arrays[f"{label}_alm"] = alm
        keys, stats = _tier1_stats(ids, maps, reduce_nside)
        auxiliary[label] = {
            "status": "legacy_unmasked_component_diagnostic_not_pr150_result",
            "statistics": keys, "n": int(len(ids)),
            "stats_matrix_hash": _arr_hash(stats), "ids_hash": _arr_hash(ids),
            "stats_matrix": stats.tolist(),
        }
        parts[label] = {"dir": str(d), "n_reduced": int(len(ids)),
                        "reduce_nside": reduce_nside, "lmax_cache": lmax,
                        "map_bytes": int(maps.nbytes), "alm_bytes": int(alm.nbytes),
                        "input_hashes": prov}

    if require_pr150_inventory:
        if not (ensemble == "ffp10" and method == "smica" and
                reduce_nside == 64 and lmax == 8):
            raise ValueError("the PR150 inventory lock requires ffp10/smica, NSIDE64, lmax8")
        _validate_pr150_inventory(reduced)

    replay = {
        label: _write_replay_files(cache_dir, ensemble, method, label, ids, maps,
                                   reduce_nside)
        for label, (ids, maps, _alm, _prov) in reduced.items()
    }

    observed_receipt = None
    if (require_pr150_inventory and method in k1.FULLRES_OBS and
            k1.FULLRES_OBS[method].is_file() and k1.MASK_HI.is_file()):
        observed_map = k1._load_sim_map(k1.FULLRES_OBS[method], reduce_nside)
        mask_hi = np.asarray(rm.hp.read_map(k1.MASK_HI), dtype=np.float64)
        mask_map = (rm.hp.ud_grade(mask_hi, nside_out=reduce_nside)
                    if rm.hp.npix2nside(mask_hi.size) != reduce_nside else mask_hi)
        payload_arrays["observed_map"] = observed_map
        payload_arrays["common_mask"] = mask_map
        observed_receipt = {
            "observed_source": str(k1.FULLRES_OBS[method]),
            "observed_source_hash": k1._sha256_file(k1.FULLRES_OBS[method]),
            "observed_array_hash": _arr_hash(observed_map),
            "mask_source": str(k1.MASK_HI),
            "mask_source_hash": k1._sha256_file(k1.MASK_HI),
            "mask_array_hash": _arr_hash(mask_map),
            "nside": reduce_nside,
        }

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"k1_{ensemble}_reduced_{method}.npz"
    cache_temp = cache_path.with_suffix(cache_path.suffix + ".tmp")
    with cache_temp.open("wb") as handle:
        np.savez(handle, **payload_arrays)
    cache_temp.replace(cache_path)
    cache_hash = k1._sha256_file(cache_path)

    backup = None
    if backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / cache_path.name
        backup_temp = backup_path.with_suffix(backup_path.suffix + ".tmp")
        shutil.copy2(cache_path, backup_temp)
        if k1._sha256_file(backup_temp) != cache_hash:
            raise RuntimeError("independent compact-cache copy failed hash verification")
        backup_temp.replace(backup_path)
        backup = {"path": str(backup_path), "cache_hash": cache_hash,
                  "filesystem_device": int(backup_path.stat().st_dev)}

    config = {"ensemble": ensemble, "method": method, "reduce_nside": reduce_nside,
              "lmax_cache": lmax, "max_sims": max_sims,
              "estimator_load": "k1_global_maxscan._load_sim_map (identical to the E2E run)",
              "retention_contract": "direct raw-to-NSIDE64 float64 pre-mask maps for the registered PR150 run",
              "require_pr150_inventory": bool(require_pr150_inventory)}
    config_hash = "sha256:" + hashlib.sha256(
        json.dumps(config, sort_keys=True).encode()).hexdigest()
    total_bytes = sum(p["map_bytes"] + p["alm_bytes"] for p in parts.values())
    return {
        "schema": "htt.k1.e2e_reduce.v1",
        "owner": "OBSSTAT",
        "claim_tier": "conditional",
        "purpose": "registered-estimator input reduction that preserves PR3 raw until "
                   "both compact replay and future PR4 replacement-ready gates pass",
        "ensemble": ensemble, "method": method,
        "tier2_cache": {"path": str(cache_path), "cache_hash": cache_hash,
                        "total_map_alm_bytes": int(total_bytes),
                        "note": "PRE-MASK downgraded maps + a_lm; mask/estimator-agnostic; "
                                "KEEP on the NVMe as the reproducibility retention artifact"},
        "independent_backup": backup,
        "replay_directories": {
            label: {"path": str(Path(rows[0]["path"]).parent),
                    "n_files": len(rows), "files": rows}
            for label, rows in replay.items()
        },
        "observed_and_mask": observed_receipt,
        "auxiliary_component_receipt": auxiliary,
        "parts": parts,
        "config": config, "config_hash": config_hash,
        "cache_reproducibility_gate_passed": False,
        "safe_to_delete_raw": False,
        "delete_gate": "raw deletion additionally requires a green full-ensemble cache gate AND an authenticated PR4 replacement-ready receipt",
        "family_identification": False, "native_solver_result": False,
        "caveats": [
            "reduction preserves ONLY the registered PR150 NSIDE64 low-ell content; the raw "
            "full-resolution maps are needed for nothing the K1 low-ell morphology analysis uses",
            "a future analysis requiring proc_nside > 64 needs the retained raw maps or a separately validated higher-resolution cache",
            "the raw PR3 ensemble remains retained until PR4 inputs are access-authorized, size-probed, and authenticated as replacement-ready",
            "no Bianchi family, geometry, anisotropy-evidence, or native-solver claim",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cmb-mc-dir", type=Path, default=None)
    ap.add_argument("--noise-mc-dir", type=Path, required=False)
    ap.add_argument("--method", default="smica")
    ap.add_argument("--ensemble", choices=["ffp10", "npipe"], default="ffp10")
    ap.add_argument("--cache-dir", type=Path,
                    default=Path("/mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced"))
    ap.add_argument("--reduce-nside", type=int, default=REDUCE_NSIDE)
    ap.add_argument("--lmax", type=int, default=LMAX_CACHE)
    ap.add_argument("--max-sims", type=int, default=None, help="cap per ensemble (smoke)")
    ap.add_argument("--require-pr150-inventory", action="store_true",
                    help="require exactly FFP10 SMICA CMB ids 00000..00999 except 00970 and noise ids 00000..00299")
    ap.add_argument("--backup-dir", type=Path, default=None,
                    help="second filesystem location for a verified copy of the combined cache")
    ap.add_argument("--check", action="store_true",
                    help="verify the committed compact-input manifest is present")
    args = ap.parse_args(argv)

    man = GEN / f"k1_e2e_reduced_manifest_{args.ensemble}_{args.method}.json"
    if args.check:
        if not man.is_file():
            print(f"missing {man.relative_to(REPO_ROOT)}")
            return 1
        print(f"{man.relative_to(REPO_ROOT)} present (compact-input receipt)")
        return 0

    if args.noise_mc_dir is None:
        ap.error("--noise-mc-dir is required (CMB dir optional for a noise-only reduce)")
    payload = build(args.cmb_mc_dir, args.noise_mc_dir, args.method, args.ensemble,
                    args.cache_dir, args.reduce_nside, args.lmax, args.max_sims,
                    require_pr150_inventory=args.require_pr150_inventory,
                    backup_dir=args.backup_dir)
    # Provenance manifest without inline maps -> committed under docs/generated.
    # The authoritative paired precision receipt is added by the cache gate.
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    mb = payload["tier2_cache"]["total_map_alm_bytes"] / 1e6
    print(f"wrote {man.relative_to(REPO_ROOT)}")
    print(f"   Tier-2 cache {payload['tier2_cache']['path']} ({mb:.0f} MB); "
          f"raw NOT yet safe to delete -> run scripts/k1_e2e_cache_gate.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
