"""R108 A3/D07: Commander half-mission and odd-even splits for a split-difference zero-signal check.

PLA identifiers (resolved 2026-11-24 from Content-Disposition of product-action requests):
  observed  MAP.MAP_ID=COM_CMB_IQU-commander_2048_R3.00_{hm1,hm2,oe1,oe2}.fits
  noise     SIMULATED_MAP.FILE_ID=dx12_v3_commander_noise_{hm1,hm2,oe1,oe2}_mc_NNNNN_raw.fits
``fetch`` downloads them one at a time (https only, no clobber, private temporary file,
Content-Disposition must name the requested file, FITS header checked, SHA-256 and size
recorded in RECEIPTS.jsonl).  ``reduce`` applies the R105/R106 estimator (design,
masks, beam x pixel window and normal equations of scripts/r105/commander_transfer.py)
to the half differences d = (X1 - X2) / 2 of the observed splits and of the matching
noise splits, and reports the observed half-difference coefficients against the noise
half-difference ensemble (the CMB signal cancels in d, so the observed d must look like
noise: zero-signal check).  Units: micro-kelvin (K_CMB x 1e6).

Usage:
  PYTHONPATH=.:htt:htt/src python -m scripts.r108.commander_splits fetch --stop 7 --max-bytes 30000000000
  PYTHONPATH=.:htt:htt/src python -m scripts.r108.commander_splits reduce --stop 7
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import tempfile
import time
from email.message import Message
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

import healpy as hp
import numpy as np
from astropy.io import fits

from scripts.r102.commander_pair_check import DEFAULT_MASK_INT, DEFAULT_MASK_POL, DEFAULT_OBS
from scripts.r105.commander_transfer import chunk_terms, design, fit_vectors, read_column
from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json

WORK = Path.home() / "Downloads/htt_r108/commander_splits"
PLA = "https://pla.esac.esa.int/pla/aio/product-action?"
SPLITS = (("hm1", "hm2"), ("oe1", "oe2"))
NOISE_BYTES = 603987840


class _HttpsOnly(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlparse(newurl).scheme != "https":
            raise ValueError(f"refusing non-https redirect to {newurl}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def products(stop: int) -> list[dict]:
    out = [{"id": f"COM_CMB_IQU-commander_2048_R3.00_{s}.fits", "url": PLA + f"MAP.MAP_ID=COM_CMB_IQU-commander_2048_R3.00_{s}.fits",
            "kind": "observed", "split": s, "bytes": None} for pair in SPLITS for s in pair]
    for i in range(stop):
        for pair in SPLITS:
            for s in pair:
                name = f"dx12_v3_commander_noise_{s}_mc_{i:05d}_raw.fits"
                out.append({"id": name, "url": PLA + f"SIMULATED_MAP.FILE_ID={name}", "kind": "noise", "split": s,
                            "index": i, "bytes": NOISE_BYTES})
    return out


def _check_fits(path: Path, kind: str) -> dict:
    with fits.open(path, memmap=True) as h:
        h.verify("exception")
        t = h[1]
        if t.header.get("NSIDE") != 2048:
            raise ValueError(f"{path.name}: NSIDE {t.header.get('NSIDE')}")
        names = tuple(t.columns.names[:3])
        want = ("I_STOKES", "Q_STOKES", "U_STOKES") if kind == "observed" else ("INTENSITY", "Q-POLARISATION", "U-POLARISATION")
        if names != want:
            raise ValueError(f"{path.name}: columns {names}")
        return {"ordering": t.header.get("ORDERING"), "coordsys": t.header.get("COORDSYS"),
                "polcconv": t.header.get("POLCCONV"), "tunit1": t.header.get("TUNIT1"), "columns": list(names)}


def fetch_one(job: dict, max_bytes: int) -> dict:
    target = WORK / job["id"]
    if target.exists():
        return {"id": job["id"], "status": "PRESENT", "bytes": target.stat().st_size}
    WORK.mkdir(parents=True, exist_ok=True)
    opener = build_opener(_HttpsOnly)
    req = Request(job["url"], headers={"Accept-Encoding": "identity", "User-Agent": "htt-r108-acquisition"})
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=".r108-intake-", dir=WORK) as work:
        tmp = Path(work) / job["id"]
        sha, n = hashlib.sha256(), 0
        with opener.open(req, timeout=300) as resp, open(tmp, "wb") as out:
            msg = Message()
            msg["Content-Disposition"] = resp.headers.get("Content-Disposition", "")
            if resp.status != 200 or msg.get_filename() != job["id"]:
                raise ValueError(f"{job['id']}: HTTP {resp.status}, filename {msg.get_filename()!r}")
            final_url = resp.geturl()
            while True:
                chunk = resp.read(1 << 22)
                if not chunk:
                    break
                n += len(chunk)
                if n > max_bytes:
                    raise ValueError(f"{job['id']}: exceeded {max_bytes} bytes")
                sha.update(chunk)
                out.write(chunk)
        if job["bytes"] is not None and n != job["bytes"]:
            raise ValueError(f"{job['id']}: received {n} bytes, expected {job['bytes']}")
        header = _check_fits(tmp, job["kind"])
        os.link(tmp, target)
    rec = {"id": job["id"], "url": job["url"], "final_url": final_url, "bytes": n, "sha256": sha.hexdigest(),
           "status": "FETCHED", "seconds": time.perf_counter() - t0, "header": header,
           "fetched_at_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    with open(WORK / "RECEIPTS.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def fetch(args) -> None:
    budget = int(args.max_bytes)
    for job in products(args.stop):
        rec = fetch_one(job, budget)
        budget -= rec["bytes"] if rec["status"] == "FETCHED" else 0
        print(json.dumps({k: rec.get(k) for k in ("id", "status", "bytes", "seconds")}), flush=True)


def reduce(args, chunk: int = 131072) -> None:
    t0 = time.perf_counter()
    jobs = products(args.stop)
    paths = {j["id"]: WORK / j["id"] for j in jobs}
    missing = [k for k, p in paths.items() if not p.is_file()]
    if missing:
        raise SystemExit(f"missing products: {missing[:4]} ... ({len(missing)})")
    receipts = {json.loads(l)["id"]: json.loads(l) for l in (WORK / "RECEIPTS.jsonl").read_text().splitlines()}
    for k, p in paths.items():
        if k not in receipts or receipts[k]["bytes"] != p.stat().st_size:
            raise SystemExit(f"{k}: no matching receipt")
    obs_cols = ("I_STOKES", "Q_STOKES", "U_STOKES")
    sim_cols = ("INTENSITY", "Q-POLARISATION", "U-POLARISATION")
    diffs = []
    for a, b in SPLITS:
        diffs.append((f"observed_{a}-{b}", paths[f"COM_CMB_IQU-commander_2048_R3.00_{a}.fits"],
                      paths[f"COM_CMB_IQU-commander_2048_R3.00_{b}.fits"], obs_cols))
        for i in range(args.stop):
            diffs.append((f"noise_{a}-{b}_{i:05d}", paths[f"dx12_v3_commander_noise_{a}_mc_{i:05d}_raw.fits"],
                          paths[f"dx12_v3_commander_noise_{b}_mc_{i:05d}_raw.fits"], sim_cols))
    files = sorted({p for d in diffs for p in d[1:3]})
    with fits.open(DEFAULT_OBS, memmap=True) as h:
        b = np.array([h[2].data[name][2] for name in ("INT_BEAM", "POL_BEAM")], float)
    win = np.array([p[2] for p in hp.pixwin(2048, pol=True, lmax=2)])
    response = b * win
    handles = {p: fits.open(p, memmap=True) for p in files}
    masks = [fits.open(DEFAULT_MASK_INT, memmap=True), fits.open(DEFAULT_MASK_POL, memmap=True)]
    # same input guards as scripts/r105/commander_transfer.reduce_files (R108 review S-5)
    for p, h in handles.items():
        hd = h[1].header
        if hd.get("NSIDE") != 2048 or hd.get("ORDERING") not in ("NESTED", "RING"):
            raise SystemExit(f"{p.name}: unexpected HEALPix geometry")
        if any(hd.get(f"TUNIT{k}") != "K_CMB" for k in (1, 2, 3)):
            raise SystemExit(f"{p.name}: expected K_CMB units, got {[hd.get(f'TUNIT{k}') for k in (1, 2, 3)]}")
        if hd.get("POLCCONV", "COSMO") != "COSMO" or (p.name.startswith("COM_CMB") and hd.get("POLCCONV") != "COSMO"):
            raise SystemExit(f"{p.name}: expected COSMO polarisation convention, got {hd.get('POLCCONV')!r}")
    try:
        ns = 2048
        npix = hp.nside2npix(ns)
        gram = [np.zeros((9, 9)), np.zeros((5, 5), complex)]
        rhs = [np.zeros((9, len(diffs))), np.zeros((5, len(diffs)), complex)]
        for start in range(0, npix, chunk):
            ring = np.arange(start, min(start + chunk, npix))
            nest = hp.ring2nest(ns, ring)

            def col(hdul, name):
                t = hdul[1]
                ids = nest if t.header["ORDERING"] == "NESTED" else ring
                return read_column(t.data.field(name), ids).astype(np.float64)

            keep = [col(masks[0], "TMASK") > 0.5, col(masks[1], "PMASK") > 0.5]
            X = design(*hp.pix2ang(ns, ring), response)
            vals = [np.empty((ring.size, len(diffs))) for _ in range(3)]
            for j, (_, p1, p2, cols) in enumerate(diffs):
                for k in range(3):
                    a, b2 = col(handles[p1], cols[k]), col(handles[p2], cols[k])
                    kept = keep[0] if k == 0 else keep[1]
                    bad = ~(np.isfinite(a) & np.isfinite(b2) & (a > -1e29) & (b2 > -1e29))
                    if np.any(bad & kept):
                        raise SystemExit(f"{p1.name}/{p2.name} field {cols[k]}: UNSEEN or non-finite pixel inside the mask")
                    vals[k][:, j] = 0.5 * (a - b2) * 1e6
            for m, (Xm, data) in enumerate(zip(X, (vals[0], vals[1] + 1j * vals[2]))):
                g, r = chunk_terms(Xm, data, keep[m])
                gram[m] += g
                rhs[m] += r
        fit = fit_vectors(gram, rhs)
    finally:
        for h in [*handles.values(), *masks]:
            h.close()
    out = {"schema": "htt.r108.commander_split_difference.1", "estimator": "scripts/r105/commander_transfer.py",
           "estimator_sha256": sha256_file(REPO / "scripts/r105/commander_transfer.py"),
           "response_TP": response.tolist(), "units": "micro-kelvin (half differences)",
           "inputs": {p.name: receipts[p.name]["sha256"] for p in files}, "git": git_state(), "splits": {}}
    for a, bb in SPLITS:
        lab = f"{a}-{bb}"
        idx_obs = [j for j, d in enumerate(diffs) if d[0] == f"observed_{lab}"][0]
        idx_sim = [j for j, d in enumerate(diffs) if d[0].startswith(f"noise_{lab}_")]
        obs = fit[:, :, idx_obs]
        sims = np.stack([fit[:, :, j] for j in idx_sim])
        ms_obs = np.mean(obs ** 2, axis=1)
        ms_sim = np.mean(sims ** 2, axis=2)
        rank = [(1 + int(np.sum(ms_sim[:, f] >= ms_obs[f]))) / (1 + len(idx_sim)) for f in range(3)]
        out["splits"][lab] = {"observed_fit_uK": obs.tolist(), "noise_fit_uK": sims.tolist(),
                              "observed_mean_square_uK2_TEB": ms_obs.tolist(),
                              "noise_mean_square_uK2_TEB_median": np.median(ms_sim, axis=0).tolist(),
                              "upper_tail_rank_TEB": rank, "n_noise": len(idx_sim)}
    out["seconds"] = time.perf_counter() - t0
    write_json(OUT_DIR / "COMMANDER" / "SPLIT_DIFFERENCE.json", out)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--stop", type=int, default=7)
    f.add_argument("--max-bytes", type=int, required=True)
    r = sub.add_parser("reduce")
    r.add_argument("--stop", type=int, default=7)
    a = ap.parse_args()
    fetch(a) if a.cmd == "fetch" else reduce(a)


if __name__ == "__main__":
    main()
