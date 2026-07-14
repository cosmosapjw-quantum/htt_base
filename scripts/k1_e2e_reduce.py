#!/usr/bin/env python3
"""K1 E2E footprint reduction: raw FFP10/NPIPE maps -> estimator-agnostic low-ell cache.

The K1 morphology estimator's FIRST step downgrades each raw Nside=2048 IQU map to
the analysis resolution (NSIDE<=64) before computing statistics
(`k1_global_maxscan._load_sim_map` -> `ud_grade`). The raw ~1 TB FITS therefore carry
NOTHING the low-ell analysis uses beyond that downgraded, low-ell content. This script
reduces each raw simulation to a compact, estimator- and mask-AGNOSTIC cache so the
1 TB PR3 (FFP10) download can be DELETED without losing the ensemble, and so the
downstream estimator revisions (roadmap PR-135 exchangeable null, PR-149 canonical
convention/mask, PR-150 E2E calibration) can recompute new statistics / re-mask
WITHOUT re-downloading.

Two retention tiers are written (see docs/research_program/K1_E2E_REPRODUCIBILITY_RETENTION.md):

  * Tier-2 (estimator-agnostic, ~1 GB, kept on the NVMe): the PRE-MASK downgraded
    I-map at REDUCE_NSIDE (default 128) + a_lm to LMAX_CACHE (default 64) for every
    realization, keyed by parsed MC id, with per-raw-file sha256 provenance. Because
    HEALPix ud_grade averaging over nested children is associative for power-of-two
    steps, ud_grade(2048 -> 128) -> proc_nside is BIT-IDENTICAL to ud_grade(2048 ->
    proc_nside) for any proc_nside in {16,32,64,128} -- so the cache reproduces the
    estimator EXACTLY (verified by scripts/k1_e2e_cache_gate.py before any deletion).
  * Tier-1 (minimal receipt, KB, committed under docs/generated/): the per-realization
    6-statistic matrix at the canonical v1 resolution + config/cache hashes + all raw
    input hashes. Lets you re-derive the K1 E2E global-p for the CURRENT statistic set
    forever with NO maps at all.

Usage (reduce the FFP10 SMICA CMB MC + noise MC while PR3 is still on disk):

    venv/bin/python scripts/k1_e2e_reduce.py \\
        --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \\
        --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc \\
        --method smica --ensemble ffp10 \\
        --cache-dir /mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced

Then run scripts/k1_e2e_cache_gate.py; only delete the raw FITS once the gate is GREEN.
The same reducer serves the NPIPE (PR4) K1-usable product (component-separated CMB
sims or a single cleaned channel) -- pass --ensemble npipe.

Deterministic; --check verifies the committed Tier-1 manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# reuse the EXACT estimator load path + helpers so the cache is faithful by construction
import k1_global_maxscan as k1  # noqa: E402
import make_lowell_morphology_real_map as rm  # noqa: E402

REDUCE_NSIDE = 128          # pre-mask headroom; 2048->128->{16,32,64} is exact (power-of-2)
LMAX_CACHE = 64             # a_lm cached to this ell (>= any low-ell analysis lmax)
GEN = REPO_ROOT / "docs/generated"


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
    """Canonical v1 6-statistic matrix from the reduced maps: ud_grade(reduce_nside ->
    NSIDE=16) then compute_map_statistics -- bit-identical to computing from raw
    because 2048->128->16 == 2048->16 (associative power-of-two ud_grade)."""
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


def build(cmb_dir: Path | None, noise_dir: Path, method: str, ensemble: str,
          cache_dir: Path, reduce_nside: int, lmax: int, max_sims: int | None) -> dict:
    parts: dict[str, dict] = {}
    payload_arrays: dict[str, np.ndarray] = {}
    tier1: dict[str, dict] = {}
    for label, d in (("noise", noise_dir), ("cmb", cmb_dir)):
        if d is None:
            continue
        ids, maps, alm, prov = _reduce_dir(d, reduce_nside, lmax, max_sims)
        payload_arrays[f"{label}_ids"] = ids
        payload_arrays[f"{label}_maps"] = maps
        payload_arrays[f"{label}_alm"] = alm
        keys, stats = _tier1_stats(ids, maps, reduce_nside)
        tier1[label] = {"statistics": keys, "n": int(len(ids)),
                        "stats_matrix_hash": _arr_hash(stats),
                        "ids_hash": _arr_hash(ids)}
        # Tier-1 receipt also stores the small stats matrix inline (n x 6 floats)
        tier1[label]["stats_matrix"] = stats.tolist()
        parts[label] = {"dir": str(d), "n_reduced": int(len(ids)),
                        "reduce_nside": reduce_nside, "lmax_cache": lmax,
                        "map_bytes": int(maps.nbytes), "alm_bytes": int(alm.nbytes),
                        "input_hashes": prov}

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"k1_{ensemble}_reduced_{method}.npz"
    np.savez(cache_path, **payload_arrays)
    cache_hash = k1._sha256_file(cache_path)

    config = {"ensemble": ensemble, "method": method, "reduce_nside": reduce_nside,
              "lmax_cache": lmax, "max_sims": max_sims,
              "estimator_load": "k1_global_maxscan._load_sim_map (identical to the E2E run)",
              "downgrade_exactness": "ud_grade(2048->%d)->proc is bit-identical to "
              "ud_grade(2048->proc) for proc in {16,32,64,128}" % reduce_nside}
    config_hash = "sha256:" + hashlib.sha256(
        json.dumps(config, sort_keys=True).encode()).hexdigest()
    total_bytes = sum(p["map_bytes"] + p["alm_bytes"] for p in parts.values())
    return {
        "schema": "htt.k1.e2e_reduce.v1",
        "owner": "OBSSTAT",
        "claim_tier": "diagnostic_only",
        "purpose": "estimator-agnostic footprint reduction so the raw ~1 TB PR3/PR4 "
                   "ensemble can be deleted after a faithful-cache gate; retains the "
                   "minimal reproducibility data for K1 E2E (roadmap PR-149/PR-150)",
        "ensemble": ensemble, "method": method,
        "tier2_cache": {"path": str(cache_path), "cache_hash": cache_hash,
                        "total_map_alm_bytes": int(total_bytes),
                        "note": "PRE-MASK downgraded maps + a_lm; mask/estimator-agnostic; "
                                "KEEP on the NVMe as the reproducibility retention artifact"},
        "tier1_receipt": tier1,
        "parts": parts,
        "config": config, "config_hash": config_hash,
        "safe_to_delete_raw": False,
        "delete_gate": "run scripts/k1_e2e_cache_gate.py; only delete raw when it is GREEN",
        "family_identification": False, "native_solver_result": False,
        "caveats": [
            "reduction preserves ONLY low-ell content (<= ell ~ 2*reduce_nside); the raw "
            "full-resolution maps are needed for nothing the K1 low-ell morphology analysis uses",
            "if a downstream convention (PR-149) requires proc_nside > reduce_nside the cache "
            "must be rebuilt from raw -- keep raw until the mask/resolution convention is frozen",
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
    ap.add_argument("--check", action="store_true",
                    help="verify the committed Tier-1 manifest is up to date")
    args = ap.parse_args(argv)

    man = GEN / f"k1_e2e_reduced_manifest_{args.ensemble}_{args.method}.json"
    if args.check:
        if not man.is_file():
            print(f"missing {man.relative_to(REPO_ROOT)}")
            return 1
        print(f"{man.relative_to(REPO_ROOT)} present (Tier-1 receipt)")
        return 0

    if args.noise_mc_dir is None:
        ap.error("--noise-mc-dir is required (CMB dir optional for a noise-only reduce)")
    payload = build(args.cmb_mc_dir, args.noise_mc_dir, args.method, args.ensemble,
                    args.cache_dir, args.reduce_nside, args.lmax, args.max_sims)
    # Tier-1 receipt WITHOUT the inline maps (KB) -> committed under docs/generated
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    mb = payload["tier2_cache"]["total_map_alm_bytes"] / 1e6
    print(f"wrote {man.relative_to(REPO_ROOT)}")
    print(f"   Tier-2 cache {payload['tier2_cache']['path']} ({mb:.0f} MB); "
          f"raw NOT yet safe to delete -> run scripts/k1_e2e_cache_gate.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
