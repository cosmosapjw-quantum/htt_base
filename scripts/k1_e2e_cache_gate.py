#!/usr/bin/env python3
"""K1 E2E faithful-cache gate: prove the reduced cache reproduces the from-RAW estimator
BEFORE any raw PR3/PR4 deletion. Fail-closed.

`scripts/k1_e2e_reduce.py` writes an estimator-agnostic Tier-2 cache (pre-mask
downgraded maps + a_lm) so the ~1 TB raw ensemble can be deleted. That deletion is
irreversible, so this gate is the mandatory checkpoint: for a sample (or all) of
realizations it recomputes the K1 6-statistic vector TWO independent ways --

  (1) from the RAW FITS via the estimator's own load path
      (`k1_global_maxscan._load_sim_map(raw, proc_nside)` -> compute_map_statistics), and
  (2) from the CACHED reduced map (ud_grade(cache_map, proc_nside) -> compute_map_statistics)

-- and asserts they agree to `--tol` (bit-identical is expected because
ud_grade(2048 -> reduce_nside) -> proc_nside == ud_grade(2048 -> proc_nside) for
power-of-two steps). It ALSO re-hashes the sampled raw files and checks them against
the manifest, so the cache is proven to have come from THESE raws. Only when the gate
is GREEN does it emit `safe_to_delete_raw: true`.

Usage:

    venv/bin/python scripts/k1_e2e_cache_gate.py \\
        --manifest docs/generated/k1_e2e_reduced_manifest_ffp10_smica.json \\
        --cmb-mc-dir   workdir/raw/planck_ffp10/smica/cmb_mc \\
        --noise-mc-dir workdir/raw/planck_ffp10/smica/noise_mc \\
        --sample 24         # or --all for the full ensemble (slower, reads all raw)

Exit 0 + safe_to_delete_raw:true only if every sampled realization matches AND every
sampled raw hash matches the manifest. Any mismatch -> exit 1, do NOT delete raw.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import k1_global_maxscan as k1  # noqa: E402
import make_lowell_morphology_real_map as rm  # noqa: E402

GEN = REPO_ROOT / "docs/generated"
PROC_NSIDE = rm.NSIDE          # canonical v1 analysis resolution (NSIDE=16)


def _stats_from_map(m_any_nside: np.ndarray, pix, apex) -> np.ndarray:
    keys = list(rm.TAILS)
    m16 = rm.hp.ud_grade(np.asarray(m_any_nside, float), nside_out=PROC_NSIDE)
    s = rm.compute_map_statistics(m16, pix, apex)
    return np.asarray([float(s[k]) for k in keys], dtype=float)


def run(manifest: Path, dirs: dict[str, Path | None], sample: int, do_all: bool,
        tol: float) -> dict:
    manifest = manifest.resolve()
    man = json.loads(manifest.read_text())
    cache_path = Path(man["tier2_cache"]["path"])
    if not cache_path.is_file():
        raise FileNotFoundError(f"Tier-2 cache not found: {cache_path}")
    if k1._sha256_file(cache_path) != man["tier2_cache"]["cache_hash"]:
        raise ValueError("cache hash mismatch: the reduced cache changed since the reduce run")
    cache = np.load(cache_path)
    reduce_nside = int(man["config"]["reduce_nside"])

    pix = np.asarray(rm.hp.pix2vec(PROC_NSIDE, np.arange(rm.hp.nside2npix(PROC_NSIDE)))).T
    obs_defaults = json.loads(rm.OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    apex = np.asarray(rm.lb_to_unitvec(np.array(cmb["l_deg"]),
                                       np.array(cmb["b_deg"])), float).reshape(3)

    checks: list[dict] = []
    max_abs = 0.0
    hash_ok = True
    for label, prov_key in (("noise", "noise"), ("cmb", "cmb")):
        part = man["parts"].get(label)
        d = dirs.get(label)
        if part is None or d is None:
            continue
        ids = cache[f"{label}_ids"]
        maps = cache[f"{label}_maps"]
        prov = {p["mc_id"]: p for p in part["input_hashes"]}
        order = list(range(len(ids)))
        if not do_all:
            # deterministic evenly-spaced sample (no RNG -> reproducible)
            step = max(1, len(order) // max(1, sample))
            order = order[::step][:sample]
        for i in order:
            mc_id = int(ids[i])
            raw = d / prov[mc_id]["file"]
            if not raw.is_file():
                checks.append({"label": label, "mc_id": mc_id, "status": "RAW_ABSENT",
                               "note": "cannot verify -- raw already gone; gate cannot pass"})
                hash_ok = False
                continue
            # (i) raw hash must match the manifest
            rh = k1._sha256_file(raw)
            if rh != prov[mc_id]["input_hash"]:
                hash_ok = False
                checks.append({"label": label, "mc_id": mc_id, "status": "HASH_MISMATCH"})
                continue
            # (ii) statistics from raw vs from cache
            s_raw = _stats_from_map(k1._load_sim_map(raw, reduce_nside), pix, apex)
            s_cache = _stats_from_map(maps[i], pix, apex)
            d_abs = float(np.max(np.abs(s_raw - s_cache)))
            max_abs = max(max_abs, d_abs)
            checks.append({"label": label, "mc_id": mc_id,
                           "max_abs_stat_diff": d_abs,
                           "status": "OK" if d_abs <= tol else "STAT_MISMATCH"})

    n_checked = len(checks)
    stat_ok = all(c["status"] == "OK" for c in checks) and n_checked > 0
    safe = bool(stat_ok and hash_ok)
    return {
        "schema": "htt.k1.e2e_cache_gate.v1",
        "owner": "OBSSTAT", "claim_tier": "diagnostic_only",
        "manifest": manifest.name,
        "cache_path": str(cache_path), "cache_hash": man["tier2_cache"]["cache_hash"],
        "proc_nside": PROC_NSIDE, "reduce_nside": reduce_nside, "tol": tol,
        "mode": "all" if do_all else f"sample={sample}",
        "n_checked": n_checked, "max_abs_stat_diff": max_abs,
        "raw_hash_ok": hash_ok, "stat_reproduced": stat_ok,
        "safe_to_delete_raw": safe,
        "checks": checks,
        "decision": ("RAW SAFE TO DELETE: cache reproduces the from-raw statistics and "
                     "all sampled raw hashes match the manifest"
                     if safe else
                     "DO NOT DELETE RAW: at least one realization failed the "
                     "statistic-reproduction or hash check"),
        "family_identification": False, "native_solver_result": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--cmb-mc-dir", type=Path, default=None)
    ap.add_argument("--noise-mc-dir", type=Path, default=None)
    ap.add_argument("--sample", type=int, default=24)
    ap.add_argument("--all", action="store_true", help="check every realization (reads all raw)")
    ap.add_argument("--tol", type=float, default=1e-9)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    dirs = {"cmb": args.cmb_mc_dir, "noise": args.noise_mc_dir}
    payload = run(args.manifest, dirs, args.sample, args.all, args.tol)
    out = args.out or (GEN / (args.manifest.stem.replace("k1_e2e_reduced_manifest",
                                                          "k1_e2e_cache_gate") + ".json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"wrote {out.relative_to(REPO_ROOT)}")
    print(f"   checked {payload['n_checked']}; max|Δstat|={payload['max_abs_stat_diff']:.2e}; "
          f"raw_hash_ok={payload['raw_hash_ok']}; safe_to_delete_raw={payload['safe_to_delete_raw']}")
    return 0 if payload["safe_to_delete_raw"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
