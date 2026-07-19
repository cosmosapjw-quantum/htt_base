#!/usr/bin/env python3
"""Fast, read-only progress receipt for the PR-151 DESI acquisition.

The probe intentionally does not hash DESI payloads.  It validates the small
record/manifest identity surface, stats partial files and a bounded log tail,
and verifies a finalization receipt when one exists.  Full payload
authentication remains the responsibility of the acquisition final rehash.
"""
from __future__ import annotations

import argparse
import datetime as dt
import fcntl
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any

try:  # package import in tests
    from .pr151_contract import (
        ACQUISITION_MANIFEST,
        EXPECTED_ARTIFACTS,
        FINALIZATION_RECEIPT,
        finalize_commands,
    )
except ImportError:  # direct script execution
    from pr151_contract import (
        ACQUISITION_MANIFEST,
        EXPECTED_ARTIFACTS,
        FINALIZATION_RECEIPT,
        finalize_commands,
    )

REPO = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = Path(
    "/mnt/sn850x2t/htt_base_e2e/workdir/raw/desi_dr1_mocks"
)
DEFAULT_LOG = REPO / "workdir/pr151_desi_tmux.log"
EXPECTED = {"observed": 1, "ezmock": 1000, "abacus": 25,
            "audit_ezmock": 10, "audit_abacus": 5}
AUDIT_IDS = {
    *(('ezmock', i) for i in range(1, 11)),
    *(('abacus', i) for i in range(0, 5)),
}
GIB = 1024 ** 3


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _iso(timestamp: float | None) -> str | None:
    if timestamp is None:
        return None
    return dt.datetime.fromtimestamp(timestamp, dt.timezone.utc).isoformat()


def _small_sha(path: Path) -> str:
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError(f"refusing to hash non-metadata file in fast probe: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(value, dict):
        return None, "top-level JSON value is not an object"
    return value, None


def _record_path(target: Path, family: str, realization: int) -> Path:
    root = "EZmock" if family == "ezmock" else "AbacusSummit"
    return target / root / "bright/v1" / f"mock{realization}" / "acquisition_record.json"


def _expected_records(target: Path):
    for realization in range(1, 1001):
        yield "ezmock", realization, _record_path(target, "ezmock", realization)
    for realization in range(25):
        yield "abacus", realization, _record_path(target, "abacus", realization)


def _caps_from_data_files(rows: object) -> set[str]:
    caps: set[str] = set()
    if not isinstance(rows, list):
        return caps
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = Path(str(row.get("path", ""))).name
        if "_NGC_" in name or name.endswith("_NGC_clustering.dat.fits"):
            caps.add("NGC")
        if "_SGC_" in name or name.endswith("_SGC_clustering.dat.fits"):
            caps.add("SGC")
    return caps


def _inspect_records(target: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    families: dict[str, dict[str, int]] = {
        family: {
            "record_paths_present": 0,
            "json_parseable": 0,
            "declared_authenticated": 0,
            "random0_declared": 0,
            "random1_declared": 0,
            "exact_identity_path_matches": 0,
        }
        for family in ("ezmock", "abacus")
    }
    present_ids: set[tuple[str, int]] = set()
    random1_ids: set[tuple[str, int]] = set()
    last: list[tuple[float, str]] = []
    expected_paths = {
        path.resolve() for _, _, path in _expected_records(target)
    }
    observed_path = target / "observed/v1.5/acquisition_record.json"
    expected_paths.add(observed_path.resolve())
    discovered_paths = {
        path.resolve() for path in target.rglob("acquisition_record.json")
        if path.is_file()
    } if target.is_dir() else set()
    unexpected_paths = sorted(
        str(path) for path in discovered_paths - expected_paths
    )
    if unexpected_paths:
        errors.append(f"unexpected acquisition records: {unexpected_paths}")
    for family, realization, path in _expected_records(target):
        if not path.is_file():
            continue
        state = families[family]
        state["record_paths_present"] += 1
        payload, error = _load_json(path)
        if error:
            errors.append(f"{path}: {error}")
            continue
        state["json_parseable"] += 1
        identity_ok = (
            payload.get("schema") == "htt.desi_dr1_mock_acquisition_record.v1"
            and payload.get("family") == family
            and payload.get("realization") == realization
        )
        if identity_ok:
            state["exact_identity_path_matches"] += 1
            present_ids.add((family, realization))
        else:
            errors.append(
                f"record identity/path mismatch: {path} declares "
                f"{payload.get('family')}:{payload.get('realization')}"
            )
        if payload.get("status") == "authenticated":
            state["declared_authenticated"] += 1
        if _caps_from_data_files(payload.get("data_files")) != {"NGC", "SGC"}:
            errors.append(f"record data cap cardinality mismatch: {path}")
        windows = payload.get("random_windows")
        if not isinstance(windows, dict):
            errors.append(f"random_windows absent or malformed: {path}")
            continue
        if isinstance(windows.get("0"), dict):
            state["random0_declared"] += 1
        else:
            errors.append(f"random-0 window absent: {path}")
        if isinstance(windows.get("1"), dict):
            state["random1_declared"] += 1
            random1_ids.add((family, realization))
        unexpected_keys = set(windows) - {"0", "1"}
        if unexpected_keys:
            errors.append(f"unexpected random indices {sorted(unexpected_keys)}: {path}")
        try:
            last.append((path.stat().st_mtime, f"{family}:{realization}"))
        except OSError:
            pass

    observed = "absent"
    if observed_path.is_file():
        payload, error = _load_json(observed_path)
        if error:
            observed = "unparseable"
            errors.append(f"{observed_path}: {error}")
        elif (payload.get("schema") == "htt.desi_dr1_observed_acquisition_record.v1"
              and payload.get("status") == "authenticated"):
            observed = "declared_authenticated"
        else:
            observed = "declared_not_authenticated"

    missing_audit = sorted(f"{f}:{r}" for f, r in AUDIT_IDS - random1_ids)
    unexpected_audit = sorted(f"{f}:{r}" for f, r in random1_ids - AUDIT_IDS)
    if unexpected_audit:
        errors.append(f"unregistered random-1 records: {unexpected_audit}")
    return {
        "observed_record": observed,
        "ezmock": families["ezmock"],
        "abacus": families["abacus"],
        "audit_registry": {
            "expected_members": len(AUDIT_IDS),
            "declared_members": len(random1_ids & AUDIT_IDS),
            "missing_members": missing_audit,
            "unexpected_members": unexpected_audit,
        },
        "unexpected_record_paths": unexpected_paths,
        "last_authenticated_records": [label for _, label in sorted(last)[-5:]],
        "warning": "declared authentication is metadata, not a fresh payload rehash",
    }, errors


def _stat_files(paths: list[Path]) -> dict[str, Any]:
    stats = []
    for path in paths:
        try:
            row = path.stat()
        except OSError:
            continue
        stats.append((row.st_size, row.st_mtime))
    return {
        "count": len(stats),
        "total_stat_bytes": sum(row[0] for row in stats),
        "newest_mtime_utc": _iso(max((row[1] for row in stats), default=None)),
        "oldest_mtime_utc": _iso(min((row[1] for row in stats), default=None)),
    }


def _tail_log(path: Path, now: dt.datetime) -> dict[str, Any]:
    if not path.is_file():
        return {"path": str(path), "exists": False, "size_bytes": 0,
                "mtime_utc": None, "age_seconds": None,
                "last_error_classification": None}
    stat = path.stat()
    with path.open("rb") as handle:
        handle.seek(max(0, stat.st_size - 65536))
        text = handle.read().decode("utf-8", errors="replace")
    lowered = text.lower()
    classification = None
    for token, label in (
        ("sha256", "integrity_or_hash_message"),
        ("error", "error_message"),
        ("failed", "failure_message"),
        ("retry", "retry_message"),
    ):
        if token in lowered:
            classification = label
            break
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    age = max(0.0, now.timestamp() - stat.st_mtime)
    return {
        "path": str(path), "exists": True, "size_bytes": stat.st_size,
        "mtime_utc": _iso(stat.st_mtime), "age_seconds": round(age, 3),
        "last_nonempty_line": lines[-1][-500:] if lines else None,
        "last_error_classification": classification,
    }


def _manifest_state(target: Path) -> dict[str, Any]:
    path = target / ACQUISITION_MANIFEST
    if not path.is_file():
        return {"exists": False, "path": str(path)}
    payload, error = _load_json(path)
    if error:
        return {"exists": True, "path": str(path), "parseable": False,
                "error": error}
    return {
        "exists": True,
        "path": str(path),
        "parseable": True,
        "sha256": _small_sha(path),
        "schema": payload.get("schema"),
        "status": payload.get("status"),
        "failure": payload.get("failure"),
        "authenticated_counts": payload.get("authenticated_counts"),
        "completion_gates": payload.get("completion_gates"),
        "final_full_data_rehash": payload.get("final_full_data_rehash"),
    }


def _lock_state(target: Path) -> dict[str, Any]:
    lock = target / ".pr151_phase.lock"
    metadata = target / ".pr151_phase_owner.json"
    owner, owner_error = (None, None)
    if metadata.is_file():
        owner, owner_error = _load_json(metadata)
    state = "unlocked"
    if lock.is_file():
        fd = os.open(lock, os.O_RDONLY)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
                state = "stale_or_inconsistent" if owner else "unlocked"
            except BlockingIOError:
                state = "held"
        finally:
            os.close(fd)
    elif owner:
        state = "stale_or_inconsistent"
    return {"state": state, "lock_path": str(lock), "owner": owner,
            "owner_error": owner_error}


def _process_visibility(target: Path) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    try:
        entries = list(Path("/proc").iterdir())
    except OSError as exc:
        return {"state": "unavailable", "error": str(exc), "matching_pids": []}
    target_text = str(target)
    for entry in entries:
        if not entry.name.isdigit() or int(entry.name) == os.getpid():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
            executable = (entry / "exe").resolve().name
        except OSError:
            continue
        command = raw.replace(b"\0", b" ").decode("utf-8", errors="replace")
        if (executable in {"aria2c", "bash", "python", "python3", "python3.12"}
                and target_text in command and any(token in command for token in (
            "download_desi_dr1_mocks.py", "run_pr151_desi_e2e.sh", "aria2c"
                ))):
            matches.append({"pid": int(entry.name), "command": command[-1000:]})
    return {"state": "running" if matches else "not_running",
            "matching_pids": matches}


def _finalization_state(target: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    path = target / FINALIZATION_RECEIPT
    if not path.is_file():
        return {"exists": False, "path": str(path), "valid": False}
    payload, error = _load_json(path)
    if error:
        return {"exists": True, "path": str(path), "valid": False,
                "error": error}
    expected_manifest = target / ACQUISITION_MANIFEST
    expected_commands = finalize_commands(target, REPO)
    command_receipts = payload.get("command_receipts")
    artifact_hashes = payload.get("artifact_hashes")
    valid = (
        payload.get("schema") == "htt.pr151.finalization_receipt.v1"
        and payload.get("status") == "complete"
        and payload.get("terminal") is True
        and payload.get("target") == str(target)
        and payload.get("acquisition_manifest") == str(expected_manifest)
        and manifest.get("sha256") == payload.get("acquisition_manifest_sha256")
        and isinstance(command_receipts, list)
        and len(command_receipts) == len(expected_commands)
        and all(
            isinstance(row, dict)
            and row.get("argv") == expected_argv
            and row.get("exit_code") == 0
            for row, expected_argv in zip(command_receipts or [], expected_commands)
        )
        and isinstance(artifact_hashes, dict)
        and set(artifact_hashes or {}) == set(EXPECTED_ARTIFACTS)
    )
    artifact_errors = []
    for rel, expected in (artifact_hashes or {}).items():
        candidate = (REPO / rel).resolve()
        if not candidate.is_relative_to(REPO) or not candidate.is_file():
            artifact_errors.append(f"missing or unsafe artifact: {rel}")
        elif _small_sha(candidate) != expected:
            artifact_errors.append(f"artifact hash mismatch: {rel}")
    valid = valid and not artifact_errors
    return {"exists": True, "path": str(path), "parseable": True,
            "status": payload.get("status"), "valid": valid,
            "sha256": _small_sha(path), "artifact_errors": artifact_errors}


def _acquisition_ready(observed: dict[str, Any], manifest: dict[str, Any],
                       structural_errors: list[str]) -> bool:
    if structural_errors or observed.get("observed_record") != "declared_authenticated":
        return False
    for family, expected in (("ezmock", 1000), ("abacus", 25)):
        state = observed[family]
        for key in ("record_paths_present", "json_parseable",
                    "declared_authenticated", "random0_declared",
                    "exact_identity_path_matches"):
            if state.get(key) != expected:
                return False
    audit = observed["audit_registry"]
    if (audit.get("declared_members") != 15 or audit.get("missing_members")
            or audit.get("unexpected_members")):
        return False
    gates = manifest.get("completion_gates") or {}
    return bool(
        manifest.get("schema") == "htt.desi_dr1_mock_acquisition.v2"
        and manifest.get("status") == "complete"
        and manifest.get("failure") is None
        and manifest.get("authenticated_counts") == {"ezmock": 1000, "abacus": 25}
        and all(gates.get(key) is True for key in (
            "expected_mock_counts", "observed_authenticated",
            "registered_random_replication_complete", "final_full_data_rehash"
        ))
        and manifest.get("final_full_data_rehash") is True
    )


def build_progress(target: Path, log: Path = DEFAULT_LOG,
                   previous: dict[str, Any] | None = None) -> dict[str, Any]:
    target = target.resolve()
    now = _utc_now()
    observed, errors = _inspect_records(target)
    parts = _stat_files(list(target.rglob("*.part")) if target.exists() else [])
    aria_root = target / ".aria2"
    aria = _stat_files(list(aria_root.iterdir()) if aria_root.is_dir() else [])
    log_state = _tail_log(log, now)
    manifest = _manifest_state(target)
    lock = _lock_state(target)
    process = _process_visibility(target)
    ready = _acquisition_ready(observed, manifest, errors)
    finalization = _finalization_state(target, manifest)
    terminal = bool(ready and finalization.get("valid"))
    disk = shutil.disk_usage(target if target.exists() else target.parent)
    comparison = None
    if previous:
        try:
            prior_time = dt.datetime.fromisoformat(previous["generated_at_utc"])
            interval = (now - prior_time).total_seconds()
            prior_parts = previous["transfer_state"]["part_files"]["total_stat_bytes"]
            prior_log = previous["transfer_state"]["log"]["size_bytes"]
            delta_part = parts["total_stat_bytes"] - prior_parts
            delta_log = log_state["size_bytes"] - prior_log
            comparison = {
                "interval_seconds": round(interval, 3),
                "delta_part_bytes": delta_part,
                "delta_log_bytes": delta_log,
                "stalled_candidate": bool(interval >= 900 and delta_part == 0
                                          and delta_log == 0),
            }
        except (KeyError, TypeError, ValueError):
            errors.append("previous progress receipt is not comparable")
    if lock["state"] == "stale_or_inconsistent":
        errors.append("writer lock metadata is stale or inconsistent")
    if disk.free < 200 * GIB:
        errors.append("disk free space below 200 GiB large-job kill switch")
    sample_material = json.dumps({
        "time": now.isoformat(), "parts": parts, "log_size": log_state["size_bytes"],
        "ez": observed["ezmock"]["record_paths_present"],
        "ab": observed["abacus"]["record_paths_present"],
    }, sort_keys=True).encode()
    if terminal:
        next_action = "terminal_complete"
    elif ready:
        next_action = "ready_for_finalize"
    elif comparison and comparison["stalled_candidate"]:
        next_action = "inspect_process_tree"
    elif manifest.get("failure") and process["state"] == "running":
        next_action = "continue_acquire_after_restart"
    elif manifest.get("failure"):
        next_action = "resolve_recorded_failure"
    else:
        next_action = "continue_acquire"
    return {
        "schema": "htt.pr151.fast_progress.v1",
        "generated_at_utc": now.isoformat(),
        "target": str(target),
        "probe_mode": "fast_read_only",
        "read_only_receipt": {
            "network_access": False, "files_written": False,
            "payload_hashing_performed": False,
            "small_metadata_hashing_performed": True,
        },
        "expected_support": EXPECTED,
        "observed_support": observed,
        "transfer_state": {
            "part_files": parts, "aria2_control_files": aria,
            "log": log_state, "manifest": manifest,
            "finalization_receipt": finalization,
        },
        "activity": {
            "writer_lock": lock, "process_visibility": process,
            "sample_id": hashlib.sha256(sample_material).hexdigest(),
            "comparison": comparison,
            "stalled_rule": "two probes >=900 s apart with zero part and log growth",
        },
        "disk": {
            "free_bytes": disk.free,
            "free_gib": disk.free / GIB,
            "new_nvme_heavy_job_allowed": disk.free >= 300 * GIB,
            "all_new_large_jobs_deferred": disk.free < 200 * GIB,
            "desi_stop_authorized": False,
        },
        "errors": errors[:100],
        "terminal": {
            "acquisition_ready": ready,
            "finalization_complete": bool(finalization.get("valid")),
            "pr151_terminal": terminal,
        },
        "next_action": next_action,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--require-acquisition-ready", action="store_true")
    parser.add_argument("--require-terminal", action="store_true")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    previous = None
    if args.previous:
        previous, error = _load_json(args.previous)
        if error:
            raise SystemExit(f"invalid previous progress receipt: {error}")
    payload = build_progress(args.target, args.log, previous)
    print(json.dumps(payload, sort_keys=True,
                     indent=None if args.compact else 2))
    if args.require_terminal and not payload["terminal"]["pr151_terminal"]:
        return 3
    if (args.require_acquisition_ready
            and not payload["terminal"]["acquisition_ready"]):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
