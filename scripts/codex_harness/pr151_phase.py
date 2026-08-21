#!/usr/bin/env python3
"""Explicit two-phase orchestration for PR-151 DESI acquisition."""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Iterator

try:  # package import in tests
    from .pr151_contract import (
        ACQUISITION_MANIFEST,
        EXPECTED_ARTIFACTS,
        FINALIZATION_RECEIPT,
        finalize_commands,
    )
    from .pr151_progress import (
        DEFAULT_LOG,
        DEFAULT_TARGET,
        FINALIZATION_READY_STATUS,
        REPO,
        _formalism_status,
        build_progress,
    )
except ImportError:  # direct script execution
    from pr151_contract import (
        ACQUISITION_MANIFEST,
        EXPECTED_ARTIFACTS,
        FINALIZATION_RECEIPT,
        finalize_commands,
    )
    from pr151_progress import (
        DEFAULT_LOG,
        DEFAULT_TARGET,
        FINALIZATION_READY_STATUS,
        REPO,
        _formalism_status,
        build_progress,
    )

CommandRunner = Callable[..., subprocess.CompletedProcess]
RECEIPT = FINALIZATION_RECEIPT


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temp.replace(path)


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _validate_target(target: Path, *, create: bool) -> Path:
    target = target.expanduser().resolve()
    if target.is_relative_to(REPO):
        raise SystemExit("PR-151 production target must be external to the repository")
    if create:
        target.mkdir(parents=True, exist_ok=True)
    elif not target.is_dir():
        raise SystemExit("PR-151 target does not exist")
    return target


@contextlib.contextmanager
def writer_lock(target: Path, phase: str) -> Iterator[None]:
    lock_path = target / ".pr151_phase.lock"
    owner_path = target / ".pr151_phase_owner.json"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o660)
    acquired = False
    owner_written = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("PR-151 target writer lock is held") from exc
        acquired = True
        _atomic_json(owner_path, {
            "schema": "htt.pr151.phase_owner.v1",
            "pid": os.getpid(), "phase": phase, "target": str(target),
            "argv": sys.argv,
            "started_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        })
        owner_written = True
        yield
    finally:
        try:
            if owner_written:
                owner_path.unlink(missing_ok=True)
        finally:
            if acquired:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)


def _failure_is_transient(target: Path) -> bool:
    path = target / ACQUISITION_MANIFEST
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    failure = payload.get("failure") or {}
    text = f"{failure.get('type', '')} {failure.get('message', '')}".lower()
    return any(token in text for token in (
        "calledprocesserror", "aria2", "timeout", "connection", "transport"
    ))


def _downloader_argv(target: Path, jobs: int, batch_size: int) -> list[str]:
    return [
        str(REPO / "venv/bin/python"), "-B",
        str(REPO / "dl_pipeline/scripts/download_desi_dr1_mocks.py"),
        "--target", str(target), "--aria-jobs", str(jobs),
        "--batch-size", str(batch_size), "--audit-ez-count", "10",
        "--audit-abacus-count", "5",
    ]


def acquire(target: Path, *, runner: CommandRunner = subprocess.run,
            retry_wait: int = 60, max_restarts: int = 0,
            jobs: int = 3, batch_size: int = 10) -> int:
    restarts = 0
    while True:
        result = runner(_downloader_argv(target, jobs, batch_size), cwd=REPO,
                        check=False)
        if result.returncode == 0:
            break
        if not _failure_is_transient(target):
            return 5
        restarts += 1
        if max_restarts > 0 and restarts >= max_restarts:
            return 75
        print(f"transient DESI acquisition failure rc={result.returncode}; "
              f"restart={restarts} in {retry_wait}s", flush=True)
        time.sleep(retry_wait)
    progress = build_progress(target, DEFAULT_LOG)
    return 0 if progress["terminal"]["acquisition_ready"] else 3


def _git_state(runner: CommandRunner) -> dict:
    head = runner(["git", "rev-parse", "HEAD"], cwd=REPO, check=False,
                  capture_output=True, text=True)
    state = runner(["git", "status", "--porcelain"], cwd=REPO, check=False,
                   capture_output=True, text=True)
    return {"commit": head.stdout.strip(), "worktree_state": state.stdout.splitlines()}


def finalize(target: Path, *, runner: CommandRunner = subprocess.run) -> int:
    formalism_status = _formalism_status()
    if formalism_status != FINALIZATION_READY_STATUS:
        print(
            "PR-151 finalization blocked: formalism status is "
            f"{formalism_status}; required={FINALIZATION_READY_STATUS}",
            file=sys.stderr,
        )
        return 7
    progress = build_progress(target, DEFAULT_LOG)
    if not progress["terminal"]["acquisition_ready"]:
        return 3
    manifest = target / ACQUISITION_MANIFEST
    receipts = []
    status = "complete"
    exit_code = 0
    for argv in finalize_commands(target, REPO):
        result = runner(argv, cwd=REPO, check=False)
        receipts.append({"argv": argv, "exit_code": result.returncode})
        if result.returncode != 0:
            status = "failed"
            exit_code = 6
            break
    artifact_hashes = {
        rel: _sha(REPO / rel) for rel in EXPECTED_ARTIFACTS
        if (REPO / rel).is_file()
    }
    if status == "complete" and set(artifact_hashes) != set(EXPECTED_ARTIFACTS):
        status, exit_code = "failed", 6
    receipt = {
        "schema": "htt.pr151.finalization_receipt.v1",
        "status": status,
        "target": str(target),
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "acquisition_manifest": str(manifest),
        "acquisition_manifest_sha256": _sha(manifest),
        "command_receipts": receipts,
        "artifact_hashes": artifact_hashes,
        "git_state": _git_state(runner),
        "terminal": status == "complete",
    }
    _atomic_json(target / RECEIPT, receipt)
    return exit_code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True,
                        choices=("acquire", "finalize", "all", "progress"))
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--previous", type=Path)
    parser.add_argument("--compact", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = _validate_target(args.target,
                              create=args.phase in {"acquire", "all"})
    if args.phase == "progress":
        previous = None
        if args.previous:
            previous = json.loads(args.previous.read_text(encoding="utf-8"))
        payload = build_progress(target, args.log, previous)
        print(json.dumps(payload, sort_keys=True,
                         indent=None if args.compact else 2))
        return 0
    try:
        with writer_lock(target, args.phase):
            if args.phase == "acquire":
                return acquire(
                    target,
                    retry_wait=int(os.environ.get("DESI_RETRY_WAIT_SECONDS", "60")),
                    max_restarts=int(os.environ.get("DESI_MAX_RESTARTS", "0")),
                    jobs=int(os.environ.get("DESI_ARIA_JOBS", "3")),
                    batch_size=int(os.environ.get("DESI_BATCH_SIZE", "10")),
                )
            if args.phase == "finalize":
                return finalize(target)
            result = acquire(
                target,
                retry_wait=int(os.environ.get("DESI_RETRY_WAIT_SECONDS", "60")),
                max_restarts=int(os.environ.get("DESI_MAX_RESTARTS", "0")),
                jobs=int(os.environ.get("DESI_ARIA_JOBS", "3")),
                batch_size=int(os.environ.get("DESI_BATCH_SIZE", "10")),
            )
            return finalize(target) if result == 0 else result
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
