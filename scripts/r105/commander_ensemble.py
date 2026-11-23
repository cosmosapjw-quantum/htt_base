"""Resume the R105 Commander quadrupole ensemble with one raw pair at a time."""
import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from scripts.r102.acquire_commander_pair import (
    COMMANDER_SIZE, DEFAULT_DEST, acquire_commander_product, ensemble_job,
)
from scripts.r102.commander_pair_check import DEFAULT_MASK_INT, DEFAULT_MASK_POL, DEFAULT_OBS
from scripts.r103.commander_ensemble import RAW, PARTS, _validated_local, atomic_json, inventory
from scripts.r105.commander_transfer import ranks, reduce_files


def merge(receipts):
    calibration = None
    observed = None
    sims = {}
    provenance = {}
    for receipt in receipts:
        if receipt.get("schema") != "r105.commander.galactic.real_l2_masked_fit.v1":
            raise ValueError("Incompatible estimator")
        records = receipt["input_sha256_and_bytes"]
        key = [receipt[k] for k in ("code_sha256", "healpy", "real_basis", "field_order",
                                     "ell", "nside", "net_response_TP", "kept_fraction_TP")]
        key += [records[k] for k in ("observed", "temperature_mask", "polarization_mask")]
        fitted_obs = np.array(receipt["observed"]["fit_uK"])
        if fitted_obs.shape != (3, 5) or not np.isfinite(fitted_obs).all():
            raise ValueError("Invalid observation coefficients")
        if calibration is None:
            calibration, observed = key, fitted_obs
        elif key != calibration or not np.allclose(observed, fitted_obs, rtol=1e-11, atol=1e-12):
            raise ValueError("Incompatible observation, mask, beam, or code identity")
        for index, realization in receipt["realizations"].items():
            row = np.array(realization["paired"]["fit_uK"])
            if row.shape != (3, 5) or not np.isfinite(row).all():
                raise ValueError("Invalid paired coefficients")
            if not np.allclose(row, np.add(realization["signal"]["fit_uK"], realization["noise"]["fit_uK"]),
                               rtol=1e-11, atol=1e-12):
                raise ValueError("Inconsistent linear split")
            ids = [records[f"{kind}_{index}"] for kind in PARTS]
            for kind, record in zip(PARTS, ids, strict=True):
                if record["filename"] != ensemble_job(kind, int(index))["id"]:
                    raise ValueError("Wrong realization identity")
            if index in sims and (ids != provenance[index] or not np.allclose(
                    sims[index], row, rtol=1e-11, atol=1e-12)):
                raise ValueError("Conflicting duplicate pair")
            provenance[index] = ids
            sims[index] = row
    if not sims:
        raise ValueError("No R105 realizations")
    return {"schema": "r105.commander.galactic.real_l2_masked_rank.v1",
            "indices": sorted(sims), "input_identities": provenance,
            "estimator_sha256": calibration[0], "field_order": ["T","E","B"],
            "observed_mean_square_uK2": np.mean(observed**2, axis=1).tolist(),
            "rank": ranks(np.mean(observed**2, axis=1),
                          [np.mean(sims[i]**2, axis=1) for i in sorted(sims)])}


def reduce_pair(index, paths, scratch):
    with TemporaryDirectory(dir=scratch, prefix="r105-pair-") as tmp:
        resolved = []
        fetched = []
        for kind in PARTS:
            if (index, kind) in paths:
                path, _ = _validated_local(paths[index, kind], ensemble_job(kind, index))
            else:
                rec = acquire_commander_product(kind, index, Path(tmp), max_bytes=COMMANDER_SIZE)
                path = Path(rec["path"])
                fetched.append({k: rec[k] for k in
                                ("filename", "url", "transferred_bytes", "sha256", "status", "http_status")})
            resolved.append(path)
        result = reduce_files(DEFAULT_OBS, DEFAULT_MASK_INT, DEFAULT_MASK_POL, {index:resolved})
        result["acquisitions_this_reduction"] = fetched
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    join = sub.add_parser("merge")
    join.add_argument("receipts", type=Path, nargs="+")
    join.add_argument("--output", type=Path, required=True)
    pair = sub.add_parser("pair")
    pair.add_argument("index", type=int)
    pair.add_argument("--output", type=Path, required=True)
    batch = sub.add_parser("batch")
    batch.add_argument("--start", type=int, required=True)
    batch.add_argument("--stop", type=int, required=True, help="exclusive upper bound")
    batch.add_argument("--directory", type=Path, required=True)
    batch.add_argument("--include", nargs="*", type=Path, default=[])
    for p in (pair, batch):
        p.add_argument("--root", type=Path, action="append")
        p.add_argument("--scratch", type=Path, default=Path.home()/"Downloads/htt_r105_commander")
        p.add_argument("--max-download-bytes", type=int, default=0)
    args = parser.parse_args()
    if args.action == "merge":
        atomic_json(args.output, merge([json.loads(p.read_text()) for p in args.receipts]))
        return
    roots = args.root or [RAW, DEFAULT_DEST, args.scratch]
    start, stop = (args.index,args.index+1) if args.action == "pair" else (args.start,args.stop)
    paths = inventory(roots, start, stop)
    receipts = []
    completed = set()
    if args.action == "batch":
        existing = [args.directory/f"commander_{i:05d}.json" for i in range(start,stop)]
        receipts = [json.loads(p.read_text()) for p in [*args.include, *(p for p in existing if p.exists())]]
        if receipts:
            completed = set(map(int,merge(receipts)["indices"]))
    pending = [i for i in range(start,stop) if i not in completed]
    needed = COMMANDER_SIZE * sum((i,k) not in paths for i in pending for k in PARTS)
    if needed > args.max_download_bytes:
        parser.error(f"Required download bytes {needed} exceed allowance {args.max_download_bytes}")
    args.scratch.mkdir(parents=True, exist_ok=True)
    for i in pending:
        output = args.output if args.action == "pair" else args.directory/f"commander_{i:05d}.json"
        if output.exists():
            parser.error(f"Result already exists at {output}; pass it to merge")
        receipt = reduce_pair(i,paths,args.scratch)
        atomic_json(output,receipt,immutable=True)
        receipts.append(receipt)
    if args.action == "batch":
        atomic_json(args.directory/"merged.json", merge(receipts))


if __name__ == "__main__":
    main()
