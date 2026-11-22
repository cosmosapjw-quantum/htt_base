"""R95 linear-superposition full-resolution (NSIDE=2048) FFP10 SMICA T/E/B streamer.

Exploits exact linearity of masked hp.map2alm(..., iter=0) and hp.map2alm_spin:
  alm(CMB_i + Noise_{i%300} - beta_i . X) = alm(CMB_i) + alm(Noise_{i%300}) - beta_i . alm(X * maskI)
Reads each of the 300 unique noise FITS files ONCE and each of the 999 valid CMB FITS
files ONCE (instead of 1,998 opens + 999x pix2vec(2048) recomputations) using a bounded
1-reader / 1-FFT-worker pipeline so peak RSS stays well below 6 GiB.

Also transforms observed PR3 SMICA and PR3 Commander (both NESTED -> RING) into the
exact same masked lmax=48 T/E/B harmonic basis, keeping SMICA and Commander strictly
separated and never replacing or editing raw FITS files.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import queue
import threading
import time
import warnings
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import healpy as hp
import numpy as np
from astropy.io import fits
from astropy.utils.exceptions import AstropyWarning


def _load_r94_stream():
    spec = importlib.util.spec_from_file_location(
        "htt_scripts_r94_stream_fullres",
        ROOT / "scripts/r94/stream_fullres.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


r94 = _load_r94_stream()

R95_DIR = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122"
DEST = r94.DEST
OBS_SMICA = r94.MASKROOT / "COM_CMB_IQU-smica_2048_R3.00_full.fits"
OBS_COMMANDER = r94.MASKROOT / "COM_CMB_IQU-commander_2048_R3.00_full.fits"
PILOT_NPZ = DEST / "pilot_00000_00818_00999.npz"
L_MAX = r94.L_MAX
NPIX = r94.NPIX
NOISE_IDS = tuple(range(300))


def _atomic_savez(target: Path, **arrays) -> None:
    tmp = target.with_suffix(".partial")
    if tmp.exists():
        tmp.unlink()
    with tmp.open("xb") as f:
        np.savez(f, **arrays)
    os.replace(tmp, target)


def _compute_or_load_basis(maskI: np.ndarray, maskP: np.ndarray, verify_shas: bool = False) -> tuple[np.ndarray, dict]:
    basis_path = DEST / "alm_basis_lmax48.npz"
    maskI_path = r94.MASKROOT / "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
    maskP_path = r94.MASKROOT / "COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits"
    mI_sha = r94.sha(maskI_path) if verify_shas or not basis_path.exists() else None
    mP_sha = r94.sha(maskP_path) if verify_shas or not basis_path.exists() else None
    if basis_path.exists():
        with np.load(basis_path, allow_pickle=False) as d:
            basis = np.asarray(d["basis_T_alm"], dtype=np.complex128).copy()
            stored_mI = str(d["maskI_sha256"])
            stored_mP = str(d["maskP_sha256"])
        if verify_shas and (stored_mI != mI_sha or stored_mP != mP_sha):
            raise RuntimeError("Stored alm_basis mask SHA drift")
        return basis, {"maskI_sha256": stored_mI, "maskP_sha256": stored_mP, "cached": True}

    DEST.mkdir(parents=True, exist_ok=True)
    basis = np.empty((4, hp.Alm.getsize(L_MAX)), dtype=np.complex128)
    basis[0] = hp.map2alm(np.asarray(maskI, dtype=np.float64), lmax=L_MAX, iter=0, pol=False)
    pix = np.arange(NPIX)
    x, y, z = hp.pix2vec(2048, pix)
    del pix
    for k, vec in enumerate((x, y, z), start=1):
        basis[k] = hp.map2alm(vec * maskI, lmax=L_MAX, iter=0, pol=False)
    del x, y, z
    _atomic_savez(
        basis_path,
        basis_T_alm=basis,
        maskI_sha256=np.asarray(mI_sha),
        maskP_sha256=np.asarray(mP_sha),
    )
    return basis, {"maskI_sha256": mI_sha, "maskP_sha256": mP_sha, "cached": False}


def _read_fits_tqu_ring(path: Path, id_: int, kind: str, reg: dict, verify_sha: bool) -> dict:
    if path.name not in reg:
        raise RuntimeError(f"Missing K1 raw hash registration for {path.name}")
    if verify_sha and r94.sha(path) != reg[path.name]:
        raise RuntimeError(f"SHA mismatch for {path.name}")
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", AstropyWarning)
        with fits.open(path, memmap=True) as h:
            ext = h[1]
            if ext.header.get("NSIDE") != 2048 or ext.header.get("ORDERING") != "RING":
                raise RuntimeError(f"FFP10 {kind} {id_:05d} sky pixelization unexpected")
            t = np.asarray(ext.data["INTENSITY"], np.float64).reshape(-1).copy() * 1e6
            q = np.asarray(ext.data["Q-POLARISATION"], np.float64).reshape(-1).copy() * 1e6
            u = np.asarray(ext.data["U-POLARISATION"], np.float64).reshape(-1).copy() * 1e6
    warn = [str(w.message)[:200] for w in captured]
    if warn and not (kind == "cmb" and id_ == 818):
        raise RuntimeError(f"Unexpected FITS warning for {kind} {id_:05d}: {warn[:3]}")
    return {"id": int(id_), "kind": kind, "name": path.name, "warnings": warn, "t": t, "q": q, "u": u}


def _transform_single_map(item: dict, maskI: np.ndarray, maskP: np.ndarray) -> tuple[np.ndarray, dict]:
    t = item.pop("t")
    q = item.pop("q")
    u = item.pop("u")
    t *= maskI
    aT = hp.map2alm(t, lmax=L_MAX, iter=0, pol=False)
    del t
    q *= maskP
    u *= maskP
    aE, aB = hp.map2alm_spin([q, u], spin=2, lmax=L_MAX)
    del q, u
    teb = np.asarray([aT, aE, aB], dtype=np.complex128)
    meta = {"id": item["id"], "kind": item["kind"], "file": item["name"], "warnings": item["warnings"]}
    return teb, meta


def _stream_items_pipelined(specs: list[tuple[int, str, Path]], maskI: np.ndarray, maskP: np.ndarray, reg: dict, verify_sha: bool):
    """Sequential single-thread disk reader overlapped with libsharp worker via bounded Queue(maxsize=1)."""
    q: queue.Queue = queue.Queue(maxsize=1)
    SENTINEL = object()
    err_box: list[BaseException] = []

    def reader():
        try:
            for id_, kind, path in specs:
                rec = _read_fits_tqu_ring(path, id_, kind, reg, verify_sha)
                q.put(rec)
        except BaseException as exc:
            err_box.append(exc)
        finally:
            q.put(SENTINEL)

    th = threading.Thread(target=reader, daemon=True)
    th.start()
    results = {}
    metas = {}
    while True:
        item = q.get()
        if item is SENTINEL:
            break
        teb, meta = _transform_single_map(item, maskI, maskP)
        results[meta["id"]] = teb
        metas[meta["id"]] = meta
    th.join()
    if err_box:
        raise err_box[0]
    return results, metas


def _combine_paired(cmb_id: int, cmb_teb: np.ndarray, noise_teb: np.ndarray, beta4: np.ndarray, basis_T: np.ndarray) -> np.ndarray:
    paired = cmb_teb + noise_teb
    paired[0] -= beta4 @ basis_T
    return np.asarray(paired, dtype=np.complex64)


def transform_observed_pr3(maskI: np.ndarray, maskP: np.ndarray, basis_T: np.ndarray, beta_obs64: np.ndarray) -> dict:
    """Transform PR3 SMICA and PR3 Commander observed IQU maps (NESTED->RING), strictly separated."""
    out_path = DEST / "observed_smica_commander_TEB_alm.npz"
    if out_path.exists():
        with np.load(out_path, allow_pickle=False) as d:
            return {
                "path": str(out_path),
                "sha256": r94.sha(out_path),
                "cached": True,
                "smica_beta_n64_uK": d["smica_beta_n64_uK"].tolist(),
                "commander_beta_n2048_uK": d["commander_beta_n2048_uK"].tolist(),
            }

    # Build exact weighted full-res normal matrix once for observed maps ONLY (small helper to check N64 vs N2048 beta)
    def read_obs_nested_to_ring(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
        file_sha = r94.sha(path)
        with fits.open(path, memmap=True) as h:
            ext = h[1]
            if ext.header.get("NSIDE") != 2048 or ext.header.get("ORDERING") != "NESTED":
                raise RuntimeError(f"Observed Planck map {path.name} ordering/NSIDE unexpected")
            t = hp.reorder(np.asarray(ext.data["I_STOKES"], np.float32).reshape(-1), n2r=True).astype(np.float64) * 1e6
            q = hp.reorder(np.asarray(ext.data["Q_STOKES"], np.float32).reshape(-1), n2r=True).astype(np.float64) * 1e6
            u = hp.reorder(np.asarray(ext.data["U_STOKES"], np.float32).reshape(-1), n2r=True).astype(np.float64) * 1e6
        return t, q, u, file_sha

    pix = np.arange(NPIX)
    vx, vy, vz = hp.pix2vec(2048, pix)
    del pix
    w = np.asarray(maskI, dtype=np.float64)
    sw = float(np.sum(w))
    sx = float(np.dot(w, vx)); sy = float(np.dot(w, vy)); sz = float(np.dot(w, vz))
    G = np.array([
        [sw, sx, sy, sz],
        [sx, float(np.dot(w * vx, vx)), float(np.dot(w * vx, vy)), float(np.dot(w * vx, vz))],
        [sy, float(np.dot(w * vy, vx)), float(np.dot(w * vy, vy)), float(np.dot(w * vy, vz))],
        [sz, float(np.dot(w * vz, vx)), float(np.dot(w * vz, vy)), float(np.dot(w * vz, vz))],
    ], dtype=np.float64)

    def fit_and_alm(t: np.ndarray, q: np.ndarray, u: np.ndarray):
        rhs = np.array([
            float(np.dot(w, t)),
            float(np.dot(w * vx, t)),
            float(np.dot(w * vy, t)),
            float(np.dot(w * vz, t)),
        ], dtype=np.float64)
        beta2048 = np.linalg.solve(G, rhs)
        aT_raw = hp.map2alm(np.nan_to_num(t * maskI, nan=0.0, posinf=0.0, neginf=0.0), lmax=L_MAX, iter=0, pol=False)
        q_m = np.nan_to_num(q * maskP, nan=0.0, posinf=0.0, neginf=0.0)
        u_m = np.nan_to_num(u * maskP, nan=0.0, posinf=0.0, neginf=0.0)
        aE, aB = hp.map2alm_spin([q_m, u_m], spin=2, lmax=L_MAX)
        return aT_raw, aE, aB, beta2048

    t_s, q_s, u_s, sha_s = read_obs_nested_to_ring(OBS_SMICA)
    aTs_raw, aEs, aBs, beta_s2048 = fit_and_alm(t_s, q_s, u_s)
    del t_s, q_s, u_s

    t_c, q_c, u_c, sha_c = read_obs_nested_to_ring(OBS_COMMANDER)
    aTc_raw, aEc, aBc, beta_c2048 = fit_and_alm(t_c, q_c, u_c)
    del t_c, q_c, u_c, vx, vy, vz, w

    smica_n64sub = np.asarray([aTs_raw - beta_obs64 @ basis_T, aEs, aBs], dtype=np.complex128)
    smica_n2048sub = np.asarray([aTs_raw - beta_s2048 @ basis_T, aEs, aBs], dtype=np.complex128)
    commander_n2048sub = np.asarray([aTc_raw - beta_c2048 @ basis_T, aEc, aBc], dtype=np.complex128)

    _atomic_savez(
        out_path,
        smica_TEB_n64sub=smica_n64sub,
        smica_TEB_n2048sub=smica_n2048sub,
        commander_TEB_n2048sub=commander_n2048sub,
        smica_beta_n64_uK=np.asarray(beta_obs64, dtype=np.float64),
        smica_beta_n2048_uK=np.asarray(beta_s2048, dtype=np.float64),
        commander_beta_n2048_uK=np.asarray(beta_c2048, dtype=np.float64),
        smica_sha256=np.asarray(sha_s),
        commander_sha256=np.asarray(sha_c),
    )
    return {
        "path": str(out_path),
        "sha256": r94.sha(out_path),
        "cached": False,
        "smica_sha256": sha_s,
        "commander_sha256": sha_c,
        "smica_beta_n64_uK": beta_obs64.tolist(),
        "smica_beta_n2048_uK": beta_s2048.tolist(),
        "commander_beta_n2048_uK": beta_c2048.tolist(),
    }


def _load_k1_obs_beta(mask64: np.ndarray) -> np.ndarray:
    with np.load(r94.CACHE, allow_pickle=False) as d:
        obs64 = np.asarray(d["observed_map"], np.float64)
    xyz = np.stack(hp.pix2vec(64, np.arange(len(mask64))), axis=1)
    X = np.column_stack([np.ones(len(mask64)), xyz])
    u = np.asarray(mask64, np.float64)
    return np.linalg.solve(X.T @ (u[:, None] * X), X.T @ (u * obs64))


def verify_pilot() -> dict:
    t0 = time.perf_counter()
    if not PILOT_NPZ.is_file():
        raise FileNotFoundError(PILOT_NPZ)
    ids, cmb, noise, mask64 = r94.input_identity()
    want = tuple(int(i) for i in r94.PILOT_IDS)
    beta = r94.prep_low_beta(ids, set(want), cmb, noise, mask64)
    reg = r94.registry()
    maskI = r94.load_mask("COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
    maskP = r94.load_mask("COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits")
    basis_T, basis_meta = _compute_or_load_basis(maskI, maskP, verify_shas=True)

    noise_specs = [(i % 300, "noise", r94.read_pair_file(i % 300, "noise")) for i in want]
    cmb_specs = [(i, "cmb", r94.read_pair_file(i, "cmb")) for i in want]
    noise_res, _ = _stream_items_pipelined(noise_specs, maskI, maskP, reg, verify_sha=False)
    cmb_res, cmb_meta = _stream_items_pipelined(cmb_specs, maskI, maskP, reg, verify_sha=False)

    reconstructed = np.stack([
        _combine_paired(i, cmb_res[i], noise_res[i % 300], beta[i], basis_T)
        for i in want
    ])
    with np.load(PILOT_NPZ, allow_pickle=False) as p:
        ref = np.asarray(p["TEB_alm"], dtype=np.complex64)
        np.testing.assert_array_equal(p["cmb_ids"], np.asarray(want, dtype=np.int32))

    abs_diff = np.abs(reconstructed - ref)
    rel_diff = abs_diff / np.maximum(np.abs(ref), 1e-12)
    channel_names = ("T", "E", "B")
    parity = {}
    for ch_idx, ch in enumerate(channel_names):
        parity[ch] = {
            "max_abs": float(np.max(abs_diff[:, ch_idx, :])),
            "max_rel_gt_1e-4": float(np.max(abs_diff[:, ch_idx, :][np.abs(ref[:, ch_idx, :]) > 1e-4] / np.abs(ref[:, ch_idx, :][np.abs(ref[:, ch_idx, :]) > 1e-4]))),
        }
        # Strictly verify float32/complex64 parity
        np.testing.assert_allclose(reconstructed[:, ch_idx, :], ref[:, ch_idx, :], rtol=2e-5, atol=2e-4)

    elapsed = time.perf_counter() - t0
    R95_DIR.mkdir(parents=True, exist_ok=True)
    receipt = {
        "schema": "htt.r95.ffp10_linear_pilot_parity/1",
        "pilot_ids": list(want),
        "pilot_npz_sha256": r94.sha(PILOT_NPZ),
        "basis_meta": basis_meta,
        "parity_by_channel_complex64": parity,
        "cmb_00818_warning_preserved": cmb_meta[818]["warnings"],
        "elapsed_wall_seconds": elapsed,
        "parity_pass": True,
    }
    (R95_DIR / "FFP10_LINEAR_PILOT_PARITY.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def run_full(verify_sha: bool = False) -> dict:
    t0 = time.perf_counter()
    DEST.mkdir(parents=True, exist_ok=True)
    ids, cmb, noise, mask64 = r94.input_identity()
    beta_obs64 = _load_k1_obs_beta(mask64)
    want = tuple(int(i) for i in ids)
    beta = r94.prep_low_beta(ids, set(want), cmb, noise, mask64)
    del cmb, noise
    reg = r94.registry()
    maskI = r94.load_mask("COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
    maskP = r94.load_mask("COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits")
    basis_T, basis_meta = _compute_or_load_basis(maskI, maskP, verify_shas=verify_sha)

    # 1. Observed PR3 SMICA & Commander (separated)
    obs_info = transform_observed_pr3(maskI, maskP, basis_T, beta_obs64)
    print("OBS_PR3_DONE", json.dumps(obs_info), flush=True)

    # 2. Stream all 300 unique noise FITS ONCE in 50-map chunks
    noise_master = DEST / "noise_300_TEB_alm.npz"
    noise_chunks_info = []
    if noise_master.exists():
        with np.load(noise_master, allow_pickle=False) as d:
            noise_all = np.asarray(d["TEB_alm"], dtype=np.complex128).copy()
            if noise_all.shape != (300, 3, hp.Alm.getsize(L_MAX)):
                raise RuntimeError("noise_300_TEB_alm shape mismatch")
        noise_chunks_info.append({"file": noise_master.name, "status": "ALREADY_VERIFIED"})
    else:
        noise_all = np.empty((300, 3, hp.Alm.getsize(L_MAX)), dtype=np.complex128)
        n_chunk = 50
        for s in range(0, 300, n_chunk):
            sec = NOISE_IDS[s : s + n_chunk]
            cpath = DEST / f"noise_TEB_{sec[0]:05d}_{sec[-1]:05d}.npz"
            if cpath.exists():
                with np.load(cpath, allow_pickle=False) as d:
                    if d["noise_ids"].tolist() != list(sec):
                        raise RuntimeError(f"noise chunk ID mismatch: {cpath.name}")
                    noise_all[s : s + n_chunk] = d["TEB_alm"]
                noise_chunks_info.append({"chunk": cpath.name, "status": "ALREADY_VERIFIED"})
                continue
            specs = [(nid, "noise", r94.read_pair_file(nid, "noise")) for nid in sec]
            res, metas = _stream_items_pipelined(specs, maskI, maskP, reg, verify_sha)
            arr = np.stack([res[nid] for nid in sec])
            noise_all[s : s + n_chunk] = arr
            _atomic_savez(cpath, noise_ids=np.asarray(sec, dtype=np.int32), TEB_alm=arr)
            noise_chunks_info.append({"chunk": cpath.name, "sha256": r94.sha(cpath), "status": "COMPUTED"})
            print(f"NOISE_CHUNK {s}..{s+len(sec)-1} elapsed={time.perf_counter()-t0:.1f}s", flush=True)
        _atomic_savez(noise_master, noise_ids=np.asarray(NOISE_IDS, dtype=np.int32), TEB_alm=noise_all)

    # 3. Stream all 999 valid CMB FITS ONCE in 25-map chunks, saving BOTH paired & cmb_only
    chunk = 25
    cmb_chunks_info = []
    warnings_log = {}
    for start in range(0, len(want), chunk):
        section = want[start : start + chunk]
        target = DEST / f"full_TEB_{section[0]:05d}_{section[-1]:05d}.npz"
        if target.exists():
            with np.load(target, allow_pickle=False) as d:
                if d["cmb_ids"].tolist() != list(section) or "cmb_only_TEB_alm" not in d.files:
                    raise RuntimeError(f"existing chunk conflict or incomplete schema: {target.name}")
            cmb_chunks_info.append({"chunk": target.name, "ids": list(section), "sha256": r94.sha(target), "status": "ALREADY_VERIFIED"})
            continue
        specs = [(cid, "cmb", r94.read_pair_file(cid, "cmb")) for cid in section]
        res, metas = _stream_items_pipelined(specs, maskI, maskP, reg, verify_sha)
        for cid, m in metas.items():
            if m["warnings"]:
                warnings_log[str(cid)] = m["warnings"]
        cmb_only = np.stack([np.asarray(res[cid], dtype=np.complex64) for cid in section])
        paired = np.stack([
            _combine_paired(cid, res[cid], noise_all[cid % 300], beta[cid], basis_T)
            for cid in section
        ])
        _atomic_savez(
            target,
            cmb_ids=np.asarray(section, dtype=np.int32),
            noise_ids=np.asarray(section, dtype=np.int32) % 300,
            TEB_alm=paired,
            cmb_only_TEB_alm=cmb_only,
        )
        cmb_chunks_info.append({"chunk": target.name, "ids": list(section), "sha256": r94.sha(target), "status": "COMPUTED"})
        print(f"FULL_CHUNK {start}..{start+len(section)-1} {target.name} elapsed={time.perf_counter()-t0:.1f}s", flush=True)

    manifest = {
        "schema": "htt.r95.full_999_linear_harmonic_stream/1",
        "nside": 2048,
        "lmax": L_MAX,
        "cmb_count": len(want),
        "noise_count": 300,
        "missing_cmb_id": r94.ID_MISSING,
        "input_cache_sha256": r94.sha(r94.CACHE),
        "basis_meta": basis_meta,
        "observed_info": obs_info,
        "noise_chunks": noise_chunks_info,
        "noise_master_sha256": r94.sha(noise_master),
        "cmb_chunks": cmb_chunks_info,
        "warnings_log": warnings_log,
        "raw_file_sha_actual": verify_sha,
        "total_seconds": time.perf_counter() - t0,
        "science_status": "STREAMED_NSIDE2048_TEB_HARMONICS_ONLY_NOT_BIANCHI_LIKELIHOOD",
    }
    p_manifest = DEST / "full_stream_manifest_r95.json"
    p_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    return {"private_manifest": str(p_manifest), "cmb_count": len(want), "noise_count": 300, "chunks": len(cmb_chunks_info), "total_seconds": manifest["total_seconds"]}


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--verify-pilot", action="store_true")
    g.add_argument("--full", action="store_true")
    p.add_argument("--sha", action="store_true")
    opts = p.parse_args()
    if opts.verify_pilot:
        res = verify_pilot()
    else:
        res = run_full(verify_sha=opts.sha)
    print(json.dumps(res, ensure_ascii=False))


if __name__ == "__main__":
    main()
