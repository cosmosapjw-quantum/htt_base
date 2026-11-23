"""Index, fetch and reduce matched PR3 fullmission Commander signal/noise pairs.

Plan uses only the local catalogue; reduce reads full maps. Missing products can
be fetched into per-pair temporary storage with an explicit transfer allowance.
The output is raw masked pseudo-Cl. PR4 has a different release and transfer.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

import healpy as hp
import numpy as np

from scripts.r98.acquisition_preflight import validate_payload
from scripts.r102.acquire_commander_pair import COMMANDER_SIZE, DEFAULT_DEST, acquire_commander_product, ensemble_job
from scripts.r102.commander_pair_check import (
    DEFAULT_MASK_INT, DEFAULT_MASK_POL, _read_healpix_to_ring, _sha256_file,
)

RAW = Path("/mnt/extdrive/workdir/raw/planck_ffp10/commander")
PARTS = ("cmb", "noise")
CHANNELS = ("TT", "EE", "BB", "TE", "EB", "TB")
ESTIMATOR = "raw.PR3.RING.common_binary_mask.gt0p5.map2alm_iter3.pol.v1"


def inventory(roots, start, stop):
    if not 0 <= start < stop <= 300:
        raise ValueError("require 0 <= start < stop <= 300 (exclusive stop)")
    wanted = {ensemble_job(p, i)["id"]: (i, p) for i in range(start, stop) for p in PARTS}
    paths = {}
    for root in roots:
        if root.is_dir():
            for f in root.rglob("dx12_v3_commander_*_raw.fits"):
                if f.name in wanted and f.is_file() and not f.is_symlink() and f.stat().st_size == COMMANDER_SIZE:
                    paths.setdefault(wanted[f.name], set()).add(f.resolve())
    return {k: sorted(v) for k, v in paths.items()}


def plan(paths, start, stop):
    available = {p: [i for i in range(start, stop) if (i, p) in paths] for p in PARTS}
    return {
        "schema": "htt.r103.commander.fullmission-plan/1", "range_start_stop_exclusive": [start, stop],
        "available_size_checked_only": available,
        "available_pairs_size_checked_only": sorted(set.intersection(*(set(v) for v in available.values()))),
        "existing_candidates": {f"{i:05d}.{p}": [str(f) for f in fs] for (i,p),fs in sorted(paths.items())},
        "missing_bytes": COMMANDER_SIZE * (2*(stop-start)-len(paths)),
        "max_temporary_raw_bytes_per_pair": 2*COMMANDER_SIZE, "bytes_per_raw_file": COMMANDER_SIZE,
        "url_examples": {p: ensemble_job(p, start)["url"] for p in PARTS},
        "qualification": "Release-specific effective beam, matched observed estimator and qualified null required.",
        "commander_null_qualified": False, "physical_Pi": None,
    }


def atomic_json(path, data, *, immutable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".r103-", delete=False, mode="w") as f:
        temp = Path(f.name)
        try:
            json.dump(data, f, indent=2, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            temp.unlink(missing_ok=True)
            raise
    try:
        if immutable:
            try:
                os.link(temp, path)
            except FileExistsError:
                if json.loads(path.read_text()) != data:
                    raise FileExistsError(f"conflicting result preserved: {path}") from None
        else:
            os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def masked_alms(path, masks, lmax):
    maps, meta = _read_healpix_to_ring(path, (0, 1, 2))
    if any(meta["n_bad_pixels_by_channel"]):
        raise ValueError(f"nonfinite/UNSEEN simulation pixels in {path.name}")
    if maps.shape != (3, len(masks[0])) or len(masks[1]) != maps.shape[1]:
        raise ValueError("mask/map shape mismatch")
    maps[0] *= masks[0]
    maps[1:] *= masks[1]
    return np.asarray(hp.map2alm(maps, lmax=lmax, iter=3, pol=True, use_pixel_weights=False))


def reduce_alms(signal, noise):
    if signal.shape != noise.shape or signal.ndim != 2 or signal.shape[0] != 3:
        raise ValueError("matched T,E,B alm arrays required")
    # alm2cl uses TT, EE, BB, TE, EB, TB. The combined map contains BOTH
    # cross terms for each mixed spectrum, including TE when T and E masks differ.
    spectra = np.asarray(hp.alm2cl(signal + noise)) * 1e12
    if not np.isfinite(spectra).all():
        raise ValueError("nonfinite pseudo spectrum")
    return {ch: row[2:].tolist() for ch,row in zip(CHANNELS, spectra, strict=True)}


def _validated_local(paths, job):
    vals = [(f,validate_payload(f,job)) for f in paths]
    if len({r["sha256"] for _,r in vals}) != 1:
        raise ValueError(f"conflicting bytes for {job['id']}")
    f, rec = vals[0]
    return f, rec


def run_batch(args, paths):
    if not 2 <= args.lmax <= 3*2048-1 or args.max_download_bytes < 0:
        raise ValueError("invalid harmonic bound or download allowance")
    weights = []
    mask_ids = []
    for f in (args.mask_int, args.mask_pol):
        mask, meta = _read_healpix_to_ring(f)
        if meta["hdus"][1]["nside"] != 2048 or meta["n_bad_pixels"]:
            raise ValueError("expected finite PR3 NSIDE 2048 mask")
        weights.append(mask > .5)
        mask_ids.append(_sha256_file(f))
    config = {"estimator": ESTIMATOR, "lmax": args.lmax, "mask_sha256": mask_ids,
              "healpy_version": hp.__version__, "estimator_sha256": _sha256_file(Path(__file__)),
              "reader_sha256": _sha256_file(Path(__file__).parents[1]/"r102/commander_pair_check.py")}
    args.scratch.mkdir(parents=True, exist_ok=True)
    spent = 0
    for i in range(args.start, args.stop):
        out = args.output_dir / f"commander_pr3_{i:05d}.json"
        if out.exists():
            saved = json.loads(out.read_text())
            spectra = saved.get("pseudo_cl_ell2_up_uK2", {})
            ids = saved.get("raw_sha256", {})
            if (saved.get("config") != config or saved.get("index") != i or
                    saved.get("commander_null_qualified") is not False or
                    "physical_Pi" not in saved or saved["physical_Pi"] is not None or
                    set(spectra) != set(CHANNELS) or set(ids) != set(PARTS) or
                    ids.get("cmb") == ids.get("noise") or
                    any(np.shape(spectra[c]) != (args.lmax-1,) or not np.isfinite(spectra[c]).all() for c in CHANNELS) or
                    any(len(ids[p]) != 64 or any(ch not in "0123456789abcdef" for ch in ids[p]) for p in PARTS)):
                raise ValueError(f"existing incompatible reduction: {out}")
            for p in PARTS:
                if any(_sha256_file(f) != ids[p] for f in paths.get((i,p), [])):
                    raise ValueError(f"cached reduction conflicts with current raw bytes: {out}")
            continue
        needed = COMMANDER_SIZE * sum((i,p) not in paths for p in PARTS)
        if needed > args.max_download_bytes-spent:
            raise ValueError(f"pair {i}: {needed} missing bytes exceed remaining allowance; preceding pairs are saved")
        if needed and shutil.disk_usage(args.scratch).free < needed:
            raise OSError(f"insufficient scratch space for pair {i}")
        with tempfile.TemporaryDirectory(prefix="htt-r103-pr3-",dir=args.scratch) as owned:
            alms, hashes = {}, {}
            for p in PARTS:
                job = ensemble_job(p,i)
                if (i,p) in paths:
                    f, rec = _validated_local(paths[i,p],job)
                else:
                    rec = acquire_commander_product(p,i,Path(owned),max_bytes=COMMANDER_SIZE)
                    f = Path(rec["path"])
                    spent += rec["transferred_bytes"]
                hashes[p] = rec["sha256"]
                alms[p] = masked_alms(f, weights, args.lmax)
            if hashes["cmb"] == hashes["noise"]:
                raise ValueError(f"identical signal and noise bytes: realization {i}")
            atomic_json(out, {"index":i,"config":config,"raw_sha256":hashes,
                     "pseudo_cl_ell2_up_uK2":reduce_alms(alms["cmb"],alms["noise"]),
                     "commander_null_qualified":False,"physical_Pi":None}, immutable=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan","reduce"))
    parser.add_argument("--root", type=Path, action="append")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--stop", type=int, default=300)
    parser.add_argument("--mask-int",type=Path,default=DEFAULT_MASK_INT)
    parser.add_argument("--mask-pol",type=Path,default=DEFAULT_MASK_POL)
    parser.add_argument("--scratch",type=Path,default=Path.home()/"Downloads/htt_r103/tmp")
    parser.add_argument("--output-dir",type=Path,default=Path.home()/"Downloads/htt_r103/reductions")
    parser.add_argument("--plan-json",type=Path)
    parser.add_argument("--max-download-bytes",type=int,default=0)
    parser.add_argument("--lmax",type=int,default=64)
    args = parser.parse_args()
    paths = inventory(args.root or (RAW, DEFAULT_DEST),args.start,args.stop)
    if args.action == "plan":
        result = plan(paths,args.start,args.stop)
        if args.plan_json:
            atomic_json(args.plan_json,result)
        else:
            print(json.dumps(result,indent=2))
    else:
        run_batch(args,paths)


if __name__ == "__main__":
    main()
