#!/usr/bin/env python3
"""Acquire DESI DR1 BGS validation mocks with bounded transient storage.

PR-151 needs the official FFA clustering-data catalogues *and* the selection
window associated with each mock.  DESI publishes 18 independent random
realisations per cap.  Retaining all 36 random files for every mock would cost
about 19 TB and is unnecessary for the frozen NSIDE=64, ell<=8 dipole lane.

This stage therefore uses the following restart-safe policy:

* retain the NGC/SGC FFA clustering-data files for all 1000 EZmocks and 25
  AbacusSummit validation mocks;
* download random realisation 0 for each mock in small batches, authenticate it
  against the official per-mock SHA256 receipt, reduce it to a weighted
  NSIDE=64 pre-mask window, authenticate the compact product, and only then
  delete that transient random FITS file;
* also reduce random realisation 1 for a preregistered small audit subset so the
  final estimator can quantify sensitivity to using one random realisation;
* use aria2 with low concurrency, resumable ``.part`` files, persistent session
  receipts, and atomic per-realisation records.

The output manifest is input provenance, not a scientific result.  The actual
mock-calibrated measurement is produced by ``scripts/desi_official_mock_card.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Iterable

import numpy as np

EZ_BASE = (
    "https://data.desi.lbl.gov/public/dr1/survey/catalogs/dr1/mocks/"
    "EZmock/bright/v1"
)
ABACUS_BASE = (
    "https://data.desi.lbl.gov/public/dr1/survey/catalogs/dr1/mocks/"
    "AbacusSummit/bright/v1"
)
OBS_BASE = (
    "https://data.desi.lbl.gov/public/dr1/survey/catalogs/dr1/LSS/iron/"
    "LSScats/v1.5"
)
OBS_SHA = "dr1_survey_catalogs_dr1_LSS_iron_LSScats_v1.5.sha256sum"
OBS_DATA = (
    "BGS_BRIGHT-21.5_NGC_clustering.dat.fits",
    "BGS_BRIGHT-21.5_SGC_clustering.dat.fits",
)
OBS_RANDOM = (
    "BGS_BRIGHT-21.5_NGC_0_clustering.ran.fits",
    "BGS_BRIGHT-21.5_SGC_0_clustering.ran.fits",
)
NSIDE = 64
ZMIN = 0.1
ZMAX = 0.4
CHUNK_ROWS = 1_000_000
EXTRACTION_CONFIG = {
    "schema": "htt.desi_mock_window_extraction.v1",
    "nside": NSIDE,
    "ordering": "RING",
    "coordinate_input": "ICRS_RA_DEC_degrees",
    "z_min_inclusive": ZMIN,
    "z_max_inclusive": ZMAX,
    "weight_column": "WEIGHT",
    "mask_application": "none_pre_mask",
    "dtype": "float64",
}
EXTRACTION_CONFIG_SHA256 = hashlib.sha256(
    json.dumps(EXTRACTION_CONFIG, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_receipt(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line_number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1):
        fields = line.split()
        if not fields:
            continue
        if len(fields) < 2 or len(fields[0]) != 64:
            raise ValueError(f"malformed checksum row {path}:{line_number}")
        try:
            int(fields[0], 16)
        except ValueError as exc:
            raise ValueError(f"malformed SHA256 {path}:{line_number}") from exc
        raw_name = fields[-1].lstrip("*")
        name_path = Path(raw_name)
        if (name_path.is_absolute() or len(name_path.parts) != 1 or
                raw_name in {"", ".", ".."}):
            raise ValueError(f"unsafe checksum path {path}:{line_number}: {raw_name}")
        if raw_name in rows:
            raise ValueError(f"duplicate checksum basename {path}:{line_number}: {raw_name}")
        rows[raw_name] = fields[0].lower()
    return rows


def receipt_name(family: str, realization: int) -> str:
    stem = ("dr1_survey_catalogs_dr1_mocks_EZmock_bright_v1_mock"
            if family == "ezmock" else
            "dr1_survey_catalogs_dr1_mocks_AbacusSummit_bright_v1_mock")
    return f"{stem}{realization}.sha256sum"


def family_contract(family: str, realization: int) -> dict:
    if family == "ezmock":
        base = EZ_BASE
        rel = Path("EZmock/bright/v1") / f"mock{realization}"
        prefix = "BGS_ffa"
    elif family == "abacus":
        base = ABACUS_BASE
        rel = Path("AbacusSummit/bright/v1") / f"mock{realization}"
        prefix = "BGS_BRIGHT-21.5_ffa"
    else:
        raise ValueError(f"unknown DESI mock family: {family}")
    return {
        "family": family,
        "realization": realization,
        "base": f"{base}/mock{realization}",
        "relative_dir": rel,
        "receipt": receipt_name(family, realization),
        "data": tuple(f"{prefix}_{cap}_clustering.dat.fits"
                      for cap in ("NGC", "SGC")),
        "random": {
            index: tuple(f"{prefix}_{cap}_{index}_clustering.ran.fits"
                         for cap in ("NGC", "SGC"))
            for index in (0, 1)
        },
    }


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


def _aria_input(path: Path, entries: Iterable[dict]) -> int:
    entries = list(entries)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in entries:
            handle.write(row["url"] + "\n")
            handle.write(f"  dir={row['dir']}\n")
            handle.write(f"  out={row['out']}\n")
            if row.get("sha256"):
                handle.write(f"  checksum=sha-256={row['sha256']}\n")
    return len(entries)


def run_aria(target: Path, label: str, entries: Iterable[dict], jobs: int) -> None:
    queue_dir = target / ".aria2"
    queue = queue_dir / f"{label}.txt"
    n = _aria_input(queue, entries)
    if n == 0:
        return
    session = queue_dir / "unfinished.session"
    log = queue_dir / "aria2.log"
    command = [
        "aria2c", f"--input-file={queue}", "--continue=true",
        f"--max-concurrent-downloads={jobs}", "--split=2",
        "--max-connection-per-server=2", "--min-split-size=64M",
        "--file-allocation=none",
        "--auto-file-renaming=false", "--allow-overwrite=false",
        "--check-integrity=true", "--max-tries=12", "--retry-wait=30",
        "--connect-timeout=30", "--timeout=60", "--lowest-speed-limit=8K",
        "--max-file-not-found=3", "--summary-interval=60",
        f"--save-session={session}", "--save-session-interval=60",
        f"--log={log}", "--log-level=notice", "--console-log-level=notice",
    ]
    print(f"aria2 batch {label}: {n} files, concurrency={jobs}", flush=True)
    started = time.time()
    result = subprocess.run(command, check=False)
    version = subprocess.run(["aria2c", "--version"], capture_output=True,
                             text=True, check=True).stdout.splitlines()[0]
    receipt = {
        "schema": "htt.desi_aria_batch_receipt.v1", "label": label,
        "aria2_version": version, "argv": command,
        "queue_path": str(queue), "queue_sha256": sha256(queue),
        "item_count": n, "exit_code": result.returncode,
        "elapsed_seconds": round(time.time() - started, 3),
    }
    _atomic_json(queue_dir / f"{label}.receipt.json", receipt)
    if result.returncode:
        raise subprocess.CalledProcessError(result.returncode, command)


def _valid_final(path: Path, expected: str) -> dict | None:
    if not path.is_file():
        return None
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(
            f"authenticated destination changed: {path}; expected {expected}, got {actual}")
    return {"path": str(path), "sha256": expected,
            "size_bytes": path.stat().st_size, "status": "present"}


def prepare_file(base: str, directory: Path, name: str, expected: str) -> tuple[dict | None, dict | None]:
    final = directory / name
    present = _valid_final(final, expected)
    if present is not None:
        return present, None
    part = final.with_name(final.name + ".part")
    if part.is_file() and sha256(part) == expected:
        part.replace(final)
        return {"path": str(final), "sha256": expected,
                "size_bytes": final.stat().st_size, "status": "resumed"}, None
    entry = {"url": f"{base}/{name}", "dir": str(directory),
             "out": part.name, "sha256": expected}
    return None, entry


def promote_file(directory: Path, name: str, expected: str) -> dict:
    final = directory / name
    present = _valid_final(final, expected)
    if present is not None:
        return present
    part = final.with_name(final.name + ".part")
    if not part.is_file():
        raise FileNotFoundError(f"aria2 did not produce {part}")
    actual = sha256(part)
    if actual != expected:
        raise RuntimeError(
            f"SHA256 mismatch for {part}: expected {expected}, got {actual}")
    part.replace(final)
    return {"path": str(final), "sha256": expected,
            "size_bytes": final.stat().st_size, "status": "downloaded"}


def ensure_receipts(target: Path, contracts: list[dict], jobs: int,
                    label: str) -> None:
    entries = []
    for contract in contracts:
        directory = target / contract["relative_dir"]
        receipt = directory / contract["receipt"]
        required = set(contract["data"] + contract["random"][0])
        if receipt.is_file() and required.issubset(parse_receipt(receipt)):
            continue
        part = receipt.with_name(receipt.name + ".part")
        entries.append({"url": f"{contract['base']}/{contract['receipt']}",
                        "dir": str(directory), "out": part.name})
    run_aria(target, f"{label}-receipts", entries, min(jobs, 2))
    for contract in contracts:
        directory = target / contract["relative_dir"]
        receipt = directory / contract["receipt"]
        required = set(contract["data"] + contract["random"][0])
        if not receipt.is_file():
            part = receipt.with_name(receipt.name + ".part")
            if not part.is_file():
                raise FileNotFoundError(f"missing receipt after aria2: {receipt}")
            parsed = parse_receipt(part)
            if not required.issubset(parsed):
                raise RuntimeError(f"official receipt lacks required files: {part}")
            part.replace(receipt)
        if not required.issubset(parse_receipt(receipt)):
            raise RuntimeError(f"official receipt lacks required files: {receipt}")


def _column(table, name: str, sl: slice, default: float = 1.0) -> np.ndarray:
    if name not in table.columns.names:
        return np.full(sl.stop - sl.start, default, dtype=np.float64)
    return np.asarray(table[name][sl], dtype=np.float64)


def random_pixel_counts(path: Path, nside: int = NSIDE) -> dict:
    """Reduce a DESI clustering random to the frozen weighted redshift window."""
    import healpy as hp
    from astropy.io import fits

    counts = np.zeros(hp.nside2npix(nside), dtype=np.float64)
    selected = 0
    weight_sum = 0.0
    with fits.open(path, memmap=True, lazy_load_hdus=True) as hdus:
        table = hdus[1].data
        names = set(table.columns.names)
        required = {"RA", "DEC", "Z", "WEIGHT"}
        if not required.issubset(names):
            raise ValueError(f"{path} lacks required columns {sorted(required - names)}")
        n_rows = len(table)
        for start in range(0, n_rows, CHUNK_ROWS):
            stop = min(start + CHUNK_ROWS, n_rows)
            sl = slice(start, stop)
            ra = _column(table, "RA", sl)
            dec = _column(table, "DEC", sl)
            z = _column(table, "Z", sl)
            weight = _column(table, "WEIGHT", sl)
            keep = ((z >= ZMIN) & (z <= ZMAX) & np.isfinite(ra)
                    & np.isfinite(dec) & np.isfinite(weight) & (weight > 0))
            if not np.any(keep):
                continue
            pix = hp.ang2pix(nside, ra[keep], dec[keep], lonlat=True)
            counts += np.bincount(pix, weights=weight[keep],
                                  minlength=counts.size)
            selected += int(np.count_nonzero(keep))
            weight_sum += float(np.sum(weight[keep]))
    if selected == 0 or weight_sum <= 0:
        raise ValueError(f"no rows survive the frozen z/weight cut in {path}")
    return {"counts": counts, "n_rows": int(n_rows),
            "n_selected": selected, "weight_sum": weight_sum}


def _compact_paths(directory: Path, random_index: int) -> tuple[Path, Path]:
    stem = f"random_window_r{random_index}_nside{NSIDE}"
    return directory / f"{stem}.npz", directory / f"{stem}.json"


def _compact_valid(npz_path: Path, meta_path: Path, source: dict[str, str]) -> dict | None:
    if not npz_path.is_file() or not meta_path.is_file():
        return None
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if (meta.get("source_sha256") != source or
            meta.get("compact_sha256") != sha256(npz_path) or
            meta.get("extraction_config_sha256") != EXTRACTION_CONFIG_SHA256):
        return None
    with np.load(npz_path) as data:
        if (int(data["nside"]) != NSIDE or
                set(("NGC", "SGC")) - set(data.files) or
                data["NGC"].shape != data["SGC"].shape):
            return None
        for cap in ("NGC", "SGC"):
            array = np.asarray(data[cap])
            if (array.shape != (12 * NSIDE * NSIDE,) or
                    array.dtype != np.dtype("float64") or
                    not np.all(np.isfinite(array)) or np.any(array < 0) or
                    not np.isclose(array.sum(), meta["caps"][cap]["weight_sum"],
                                   rtol=1e-12, atol=1e-8)):
                return None
    return {"path": str(npz_path), "sha256": meta["compact_sha256"],
            "metadata_path": str(meta_path), "metadata_sha256": sha256(meta_path),
            "random_index": meta["random_index"],
            "source_sha256": source, "caps": meta["caps"]}


def compact_random_pair(directory: Path, names: tuple[str, str], expected: dict[str, str],
                        random_index: int, target: Path, *, retain_raw: bool) -> dict:
    source = {name: expected[name] for name in names}
    npz_path, meta_path = _compact_paths(directory, random_index)
    valid = _compact_valid(npz_path, meta_path, source)
    if valid is not None:
        if not retain_raw:
            for name in names:
                raw = directory / name
                if raw.is_file():
                    _delete_transient(raw, target, npz_path, meta_path)
                else:
                    _recover_deletion_receipt(raw, npz_path, meta_path)
            valid["deletion_receipts"] = [
                str(_deletion_receipt_path(directory / name)) for name in names]
        return valid

    loaded = {"NGC": random_pixel_counts(directory / names[0]),
              "SGC": random_pixel_counts(directory / names[1])}
    temp = npz_path.with_suffix(npz_path.suffix + ".tmp")
    npz_path.parent.mkdir(parents=True, exist_ok=True)
    with temp.open("wb") as handle:
        np.savez_compressed(
            handle, NGC=loaded["NGC"]["counts"], SGC=loaded["SGC"]["counts"],
            nside=np.asarray(NSIDE), zmin=np.asarray(ZMIN), zmax=np.asarray(ZMAX),
            random_index=np.asarray(random_index),
        )
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(npz_path)
    compact_hash = sha256(npz_path)
    caps = {
        cap: {key: value for key, value in row.items() if key != "counts"}
        for cap, row in loaded.items()
    }
    meta = {
        "schema": "htt.desi_mock_random_window.v1",
        "owner": "DL_PIPELINE", "claim_tier": "input_provenance_only",
        "nside": NSIDE, "z_min_inclusive": ZMIN, "z_max_inclusive": ZMAX,
        "extraction_config": EXTRACTION_CONFIG,
        "extraction_config_sha256": EXTRACTION_CONFIG_SHA256,
        "random_index": random_index,
        "source_sha256": source, "compact_path": str(npz_path),
        "compact_sha256": compact_hash, "caps": caps,
        "raw_retained": bool(retain_raw),
    }
    _atomic_json(meta_path, meta)
    valid = _compact_valid(npz_path, meta_path, source)
    if valid is None:
        raise RuntimeError(f"compact window verification failed: {npz_path}")
    if not retain_raw:
        for name in names:
            _delete_transient(directory / name, target, npz_path, meta_path)
        valid["deletion_receipts"] = [
            str(_deletion_receipt_path(directory / name)) for name in names]
    return valid


def _deletion_receipt_path(raw: Path) -> Path:
    return raw.with_name(raw.name + ".deleted.json")


def _predelete_path(raw: Path) -> Path:
    return raw.with_name(raw.name + ".predelete.json")


def _delete_transient(raw: Path, target: Path, npz_path: Path, meta_path: Path) -> None:
    raw.resolve().relative_to(target.resolve())
    if not raw.name.endswith("_clustering.ran.fits"):
        raise RuntimeError(f"refusing non-random transient deletion: {raw}")
    if not npz_path.is_file() or not meta_path.is_file():
        raise RuntimeError(f"refusing deletion before compact verification: {raw}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    expected = meta["source_sha256"].get(raw.name)
    if expected is None or sha256(raw) != expected:
        raise RuntimeError(f"refusing deletion of unauthenticated source: {raw}")
    if _compact_valid(npz_path, meta_path, meta["source_sha256"]) is None:
        raise RuntimeError(f"refusing deletion with invalid compact window: {npz_path}")
    journal = {
        "schema": "htt.desi_random_predelete.v1", "source_path": str(raw),
        "source_sha256": expected, "compact_path": str(npz_path),
        "compact_sha256": sha256(npz_path), "metadata_sha256": sha256(meta_path),
        "extraction_config_sha256": EXTRACTION_CONFIG_SHA256,
    }
    _atomic_json(_predelete_path(raw), journal)
    raw.unlink()
    control = raw.with_name(raw.name + ".aria2")
    if control.is_file():
        control.unlink()
    receipt = {**journal, "schema": "htt.desi_random_deletion_receipt.v1",
               "source_absent": True, "recovered_after_interruption": False}
    _atomic_json(_deletion_receipt_path(raw), receipt)
    print(f"deleted authenticated transient random after compact verification: {raw}",
          flush=True)


def _recover_deletion_receipt(raw: Path, npz_path: Path, meta_path: Path) -> None:
    receipt_path = _deletion_receipt_path(raw)
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if (not receipt.get("source_absent") or raw.exists() or
                receipt.get("source_path") != str(raw) or
                receipt.get("source_sha256") != meta["source_sha256"].get(raw.name) or
                receipt.get("compact_sha256") != sha256(npz_path) or
                receipt.get("metadata_sha256") != sha256(meta_path) or
                receipt.get("extraction_config_sha256") != EXTRACTION_CONFIG_SHA256):
            raise RuntimeError(f"invalid existing random deletion receipt: {receipt_path}")
        return
    journal_path = _predelete_path(raw)
    if not journal_path.is_file():
        raise RuntimeError(f"random source absent without pre-delete journal: {raw}")
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if (journal.get("source_path") != str(raw) or
            journal.get("source_sha256") != meta["source_sha256"].get(raw.name) or
            journal.get("compact_sha256") != sha256(npz_path) or
            journal.get("metadata_sha256") != sha256(meta_path) or
            _compact_valid(npz_path, meta_path, meta["source_sha256"]) is None):
        raise RuntimeError(f"cannot recover interrupted random deletion: {raw}")
    receipt = {**journal, "schema": "htt.desi_random_deletion_receipt.v1",
               "source_absent": True, "recovered_after_interruption": True}
    _atomic_json(receipt_path, receipt)


def _record_path(target: Path, contract: dict) -> Path:
    return target / contract["relative_dir"] / "acquisition_record.json"


def _record_complete(path: Path, audit_required: bool) -> bool:
    if not path.is_file():
        return False
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
        if (row.get("schema") != "htt.desi_dr1_mock_acquisition_record.v1"
                or row.get("status") != "authenticated"):
            return False
        data_files = row.get("data_files", [])
        data_paths = [Path(file_row.get("path", ""))
                      for file_row in data_files if isinstance(file_row, dict)]
        if (len(data_files) != 2 or len(data_paths) != 2
                or len(set(data_paths)) != 2
                or sum("NGC" in item.name for item in data_paths) != 1
                or sum("SGC" in item.name for item in data_paths) != 1):
            return False
        if any(not Path(f["path"]).is_file() or
               Path(f["path"]).stat().st_size != f["size_bytes"] or
               sha256(Path(f["path"])) != f["sha256"]
               for f in data_files):
            return False
        windows = row.get("random_windows", {})
        required = {"0", "1"} if audit_required else {"0"}
        for index in required:
            w = windows.get(index)
            if not w or not Path(w["path"]).is_file() or not Path(w["metadata_path"]).is_file():
                return False
            if _compact_valid(Path(w["path"]), Path(w["metadata_path"]),
                              dict(w["source_sha256"])) is None:
                return False
            deletion_receipts = w.get("deletion_receipts", [])
            if len(deletion_receipts) != 2:
                return False
            for receipt in deletion_receipts:
                deletion = json.loads(Path(receipt).read_text(encoding="utf-8"))
                if (not deletion.get("source_absent") or
                        Path(deletion["source_path"]).exists() or
                        deletion.get("compact_sha256") != w["sha256"] or
                        deletion.get("metadata_sha256") != w["metadata_sha256"] or
                        deletion.get("extraction_config_sha256") !=
                        EXTRACTION_CONFIG_SHA256):
                    return False
        if sha256(Path(row["receipt"])) != row["receipt_sha256"]:
            return False
        return True
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def process_batch(target: Path, contracts: list[dict], audit_ids: set[tuple[str, int]],
                  jobs: int, label: str) -> None:
    ensure_receipts(target, contracts, jobs, label)
    entries = []
    completed: dict[tuple[str, int], bool] = {}
    for contract in contracts:
        key = (contract["family"], contract["realization"])
        completed[key] = _record_complete(
            _record_path(target, contract), key in audit_ids)
        if completed[key]:
            continue
        directory = target / contract["relative_dir"]
        expected = parse_receipt(directory / contract["receipt"])
        names = list(contract["data"] + contract["random"][0])
        if (contract["family"], contract["realization"]) in audit_ids:
            names.extend(contract["random"][1])
        for name in names:
            if name not in expected:
                raise RuntimeError(f"official receipt lacks {name}")
            _present, entry = prepare_file(contract["base"], directory, name,
                                           expected[name])
            if entry is not None:
                entries.append(entry)
    run_aria(target, f"{label}-payload", entries, jobs)

    for contract in contracts:
        audit = (contract["family"], contract["realization"]) in audit_ids
        record_path = _record_path(target, contract)
        if completed[(contract["family"], contract["realization"])]:
            continue
        directory = target / contract["relative_dir"]
        receipt = directory / contract["receipt"]
        expected = parse_receipt(receipt)
        data_files = [promote_file(directory, name, expected[name])
                      for name in contract["data"]]
        windows: dict[str, dict] = {}
        for random_index in ((0, 1) if audit else (0,)):
            names = contract["random"][random_index]
            for name in names:
                promote_file(directory, name, expected[name])
            windows[str(random_index)] = compact_random_pair(
                directory, names, expected, random_index, target, retain_raw=False)
        record = {
            "schema": "htt.desi_dr1_mock_acquisition_record.v1",
            "family": contract["family"], "realization": contract["realization"],
            "status": "authenticated", "receipt": str(receipt),
            "receipt_sha256": sha256(receipt), "data_files": data_files,
            "random_windows": windows,
            "storage_policy": "data retained; authenticated raw randoms deleted only after compact-window verification",
        }
        _atomic_json(record_path, record)
        print(f"authenticated {contract['family']} {contract['realization']} "
              f"(random windows {sorted(windows)})", flush=True)


def process_observed(target: Path, jobs: int) -> dict:
    directory = target / "observed/v1.5"
    receipt = directory / OBS_SHA
    if not receipt.is_file() or not set(OBS_DATA + OBS_RANDOM).issubset(parse_receipt(receipt)):
        run_aria(target, "observed-receipt", [{
            "url": f"{OBS_BASE}/{OBS_SHA}", "dir": str(directory),
            "out": OBS_SHA + ".part",
        }], 1)
        part = receipt.with_name(receipt.name + ".part")
        if not part.is_file():
            raise FileNotFoundError(f"missing observed receipt: {part}")
        if not set(OBS_DATA + OBS_RANDOM).issubset(parse_receipt(part)):
            raise RuntimeError("observed receipt lacks required BGS_BRIGHT files")
        part.replace(receipt)
    expected = parse_receipt(receipt)
    entries = []
    for name in OBS_DATA + OBS_RANDOM:
        _present, entry = prepare_file(OBS_BASE, directory, name, expected[name])
        if entry is not None:
            entries.append(entry)
    run_aria(target, "observed-payload", entries, jobs)
    data = [promote_file(directory, name, expected[name]) for name in OBS_DATA]
    random_files = [promote_file(directory, name, expected[name]) for name in OBS_RANDOM]
    window = compact_random_pair(directory, OBS_RANDOM, expected, 0, target,
                                 retain_raw=True)
    record = {
        "schema": "htt.desi_dr1_observed_acquisition_record.v1",
        "sample": "DESI_DR1_BGS_BRIGHT-21.5", "redshift_range": [ZMIN, ZMAX],
        "status": "authenticated", "receipt": str(receipt),
        "receipt_sha256": sha256(receipt), "data_files": data,
        "random_files": random_files, "random_window": window,
    }
    _atomic_json(directory / "acquisition_record.json", record)
    return record


def _all_records(target: Path) -> list[dict]:
    records = []
    for family, ids in (("ezmock", range(1, 1001)), ("abacus", range(25))):
        for realization in ids:
            contract = family_contract(family, realization)
            path = _record_path(target, contract)
            if path.is_file():
                records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def _aggregate_hash(records: list[dict], observed: dict | None = None) -> str:
    h = hashlib.sha256()
    rows = []
    for record in records:
        rows.extend((f["path"], f["sha256"]) for f in record["data_files"])
        rows.extend((w["path"], w["sha256"])
                    for w in record["random_windows"].values())
        rows.extend((w["metadata_path"], w["metadata_sha256"])
                    for w in record["random_windows"].values())
        rows.append((record["receipt"], record["receipt_sha256"]))
    if observed:
        rows.extend((f["path"], f["sha256"])
                    for f in observed.get("data_files", []))
        rows.extend((f["path"], f["sha256"])
                    for f in observed.get("random_files", []))
        window = observed.get("random_window") or {}
        if window:
            rows.append((window["path"], window["sha256"]))
            rows.append((window["metadata_path"], window["metadata_sha256"]))
        if observed.get("receipt"):
            rows.append((observed["receipt"], observed["receipt_sha256"]))
    for path, digest in sorted(rows):
        h.update((path + "\0" + digest + "\n").encode())
    return h.hexdigest()


def final_rehash(records: list[dict], observed: dict) -> None:
    total = sum(len(row["data_files"]) for row in records)
    done = 0
    for record in records:
        for file_row in record["data_files"]:
            path = Path(file_row["path"])
            actual = sha256(path)
            if actual != file_row["sha256"]:
                raise RuntimeError(f"final SHA256 audit failed: {path}")
            done += 1
            if done % 100 == 0 or done == total:
                print(f"final data rehash {done}/{total}", flush=True)
        for window in record["random_windows"].values():
            if sha256(Path(window["path"])) != window["sha256"]:
                raise RuntimeError(f"final compact-window hash failed: {window['path']}")
            if sha256(Path(window["metadata_path"])) != window["metadata_sha256"]:
                raise RuntimeError(f"final compact metadata hash failed: {window['metadata_path']}")
            for receipt in window.get("deletion_receipts", []):
                deletion = json.loads(Path(receipt).read_text(encoding="utf-8"))
                if (not deletion.get("source_absent") or
                        Path(deletion["source_path"]).exists() or
                        deletion.get("compact_sha256") != window["sha256"] or
                        deletion.get("metadata_sha256") != window["metadata_sha256"] or
                        deletion.get("extraction_config_sha256") !=
                        EXTRACTION_CONFIG_SHA256):
                    raise RuntimeError(f"transient deletion receipt failed: {receipt}")
        if sha256(Path(record["receipt"])) != record["receipt_sha256"]:
            raise RuntimeError(f"frozen official receipt changed: {record['receipt']}")
    for file_row in observed["data_files"] + observed["random_files"]:
        if sha256(Path(file_row["path"])) != file_row["sha256"]:
            raise RuntimeError(f"final observed SHA256 audit failed: {file_row['path']}")
    window = observed["random_window"]
    if sha256(Path(window["path"])) != window["sha256"]:
        raise RuntimeError("final observed compact-window hash failed")
    if sha256(Path(window["metadata_path"])) != window["metadata_sha256"]:
        raise RuntimeError("final observed compact-window metadata hash failed")
    if sha256(Path(observed["receipt"])) != observed["receipt_sha256"]:
        raise RuntimeError("final observed official receipt changed")


def _batches(rows: list[dict], size: int):
    for start in range(0, len(rows), size):
        yield start // size + 1, rows[start:start + size]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--aria-jobs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--ez-start", type=int, default=1)
    parser.add_argument("--ez-stop", type=int, default=1000)
    parser.add_argument("--skip-ezmock", action="store_true")
    parser.add_argument("--skip-abacus", action="store_true")
    parser.add_argument("--skip-observed", action="store_true")
    parser.add_argument("--audit-ez-count", type=int, default=10)
    parser.add_argument("--audit-abacus-count", type=int, default=5)
    parser.add_argument("--skip-final-rehash", action="store_true",
                        help="development/partial runs only; a complete manifest requires the final rehash")
    args = parser.parse_args(argv)
    if args.aria_jobs < 1 or args.batch_size < 1:
        parser.error("--aria-jobs and --batch-size must be positive")
    if not 1 <= args.ez_start <= args.ez_stop <= 1000:
        parser.error("EZmock range must satisfy 1 <= start <= stop <= 1000")
    if shutil.which("aria2c") is None:
        raise SystemExit("aria2c is required for the resumable DESI stage")

    target = args.target.expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    started = time.time()
    if args.skip_observed:
        observed_path = target / "observed/v1.5/acquisition_record.json"
        observed = (json.loads(observed_path.read_text(encoding="utf-8"))
                    if observed_path.is_file() else None)
    else:
        observed = process_observed(target, args.aria_jobs)
    audit_ids = ({("ezmock", i) for i in range(1, 1 + args.audit_ez_count)} |
                 {("abacus", i) for i in range(args.audit_abacus_count)})
    frozen_audit_ids = (
        {("ezmock", i) for i in range(1, 11)} |
        {("abacus", i) for i in range(5)}
    )
    audit_registry = {
        "schema": "htt.desi_random_replication_registry.v1",
        "selection_frozen_before_results": True,
        "random_indices": [0, 1],
        "members": [{"family": family, "realization": realization}
                    for family, realization in sorted(frozen_audit_ids)],
    }
    audit_registry_hash = hashlib.sha256(json.dumps(
        audit_registry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    selected: list[dict] = []
    if not args.skip_ezmock:
        selected.extend(family_contract("ezmock", i)
                        for i in range(args.ez_start, args.ez_stop + 1))
    if not args.skip_abacus:
        selected.extend(family_contract("abacus", i) for i in range(25))

    failure: BaseException | None = None
    error = None
    try:
        for batch_index, batch in _batches(selected, args.batch_size):
            family = batch[0]["family"]
            label = f"{family}-batch{batch_index:04d}"
            process_batch(target, batch, audit_ids, args.aria_jobs, label)
    except BaseException as exc:
        failure = exc
        error = {"type": type(exc).__name__, "message": str(exc)}
    records = _all_records(target)
    counts = {family: sum(r["family"] == family for r in records)
              for family in ("ezmock", "abacus")}
    complete_counts = counts == {"ezmock": 1000, "abacus": 25}
    observed_complete = bool(observed and observed.get("status") == "authenticated")
    record_lookup = {(row["family"], int(row["realization"])): row
                     for row in records}
    audit_complete = all(
        key in record_lookup and "1" in record_lookup[key].get("random_windows", {})
        for key in frozen_audit_ids
    )
    final_rehash_complete = False
    if (complete_counts and observed_complete and audit_complete and
            not args.skip_final_rehash and error is None):
        try:
            final_rehash(records, observed)
            final_rehash_complete = True
        except BaseException as exc:
            failure = exc
            error = {"type": type(exc).__name__, "message": str(exc)}
    fully_authenticated = bool(
        complete_counts and observed_complete and audit_complete and
        final_rehash_complete and error is None
    )
    manifest = {
            "schema": "htt.desi_dr1_mock_acquisition.v2",
            "owner": "DL_PIPELINE", "claim_tier": "input_provenance_only",
            "implementation_scope": "authenticated FFA clustering data plus per-mock compact random windows",
            "source": "DESI DR1 public LSS mocks",
            "source_url": "https://data.desi.lbl.gov/doc/releases/dr1/",
            "target": str(target), "observed": observed,
            "records": sorted(records, key=lambda r: (r["family"], r["realization"])),
            "authenticated_counts": counts,
            "expected_counts": {"ezmock": 1000, "abacus": 25},
            "aggregate_input_hash": _aggregate_hash(records, observed),
            "failure": error,
            "storage_policy": {
                "retained": "NGC/SGC FFA data, official receipts, NSIDE64 random-0 windows, and random-1 windows for 10 EZmock plus 5 Abacus audit realizations",
                "transient_deleted": "authenticated raw mock random FITS only after compact-window verification",
                "full_18_random_policy": "not required for the frozen low-ell estimator; 18 randoms are independent Monte Carlo integration realizations, not 18 distinct survey selections",
            },
            "network_policy": {
                "client": "aria2c", "parallel_jobs": args.aria_jobs,
                "batch_size": args.batch_size, "resume_partial_files": True,
                "official_sha256_required": True,
            },
            "extraction_config": EXTRACTION_CONFIG,
            "extraction_config_sha256": EXTRACTION_CONFIG_SHA256,
            "random_replication_registry": audit_registry,
            "random_replication_registry_sha256": audit_registry_hash,
            "completion_gates": {
                "expected_mock_counts": complete_counts,
                "observed_authenticated": observed_complete,
                "registered_random_replication_complete": audit_complete,
                "final_full_data_rehash": final_rehash_complete,
            },
            "final_full_data_rehash": final_rehash_complete,
            "elapsed_seconds": round(time.time() - started, 3),
            "status": "complete" if fully_authenticated else "incomplete",
            "generating_command": " ".join(sys.argv if argv is None else
                                             [str(Path(__file__)), *list(argv)]),
    }
    _atomic_json(target / "desi_dr1_mock_acquisition_manifest.json", manifest)
    print(f"manifest status={manifest['status']} counts={counts}", flush=True)
    if failure is not None:
        raise failure
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
