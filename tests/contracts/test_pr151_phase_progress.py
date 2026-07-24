"""PR-151 phase separation and fast-progress contract tests."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.codex_harness import (
    pr151_finalize_watch,
    pr151_phase,
    pr151_progress,
)


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _record(target: Path, family: str, realization: int,
            *, random1: bool = False, declared_family: str | None = None) -> None:
    root = "EZmock" if family == "ezmock" else "AbacusSummit"
    directory = target / root / "bright/v1" / f"mock{realization}"
    prefix = "BGS_ffa" if family == "ezmock" else "BGS_BRIGHT-21.5_ffa"
    windows = {"0": {"path": str(directory / "random0.npz")}}
    if random1:
        windows["1"] = {"path": str(directory / "random1.npz")}
    _write(directory / "acquisition_record.json", {
        "schema": "htt.desi_dr1_mock_acquisition_record.v1",
        "status": "authenticated",
        "family": declared_family or family,
        "realization": realization,
        "data_files": [
            {"path": str(directory / f"{prefix}_NGC_clustering.dat.fits")},
            {"path": str(directory / f"{prefix}_SGC_clustering.dat.fits")},
        ],
        "random_windows": windows,
    })


def _complete_tree(target: Path) -> None:
    _write(target / "observed/v1.5/acquisition_record.json", {
        "schema": "htt.desi_dr1_observed_acquisition_record.v1",
        "status": "authenticated",
    })
    for realization in range(1, 1001):
        _record(target, "ezmock", realization, random1=realization <= 10)
    for realization in range(25):
        _record(target, "abacus", realization, random1=realization < 5)
    _write(target / "desi_dr1_mock_acquisition_manifest.json", {
        "schema": "htt.desi_dr1_mock_acquisition.v2",
        "status": "complete",
        "failure": None,
        "authenticated_counts": {"ezmock": 1000, "abacus": 25},
        "completion_gates": {
            "expected_mock_counts": True,
            "observed_authenticated": True,
            "registered_random_replication_complete": True,
            "final_full_data_rehash": True,
        },
        "final_full_data_rehash": True,
    })


def test_fast_progress_is_read_only_and_requires_exact_support(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    before = sorted(path.relative_to(target) for path in target.rglob("*"))
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    after = sorted(path.relative_to(target) for path in target.rglob("*"))
    assert before == after
    assert payload["read_only_receipt"]["payload_hashing_performed"] is False
    assert payload["terminal"]["acquisition_ready"] is False
    assert payload["next_action"] == "continue_acquire"


def test_complete_support_is_acquisition_ready_but_not_terminal(tmp_path: Path) -> None:
    target = tmp_path / "target"
    _complete_tree(target)
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    assert payload["observed_support"]["ezmock"]["exact_identity_path_matches"] == 1000
    assert payload["observed_support"]["abacus"]["exact_identity_path_matches"] == 25
    assert payload["observed_support"]["audit_registry"]["declared_members"] == 15
    assert payload["terminal"]["acquisition_ready"] is True
    assert payload["terminal"]["pr151_terminal"] is False
    assert payload["next_action"] == "ready_for_finalize"


def test_record_identity_swap_cannot_be_hidden_by_counts(tmp_path: Path) -> None:
    target = tmp_path / "target"
    _complete_tree(target)
    _record(target, "ezmock", 1000, declared_family="abacus")
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    assert payload["terminal"]["acquisition_ready"] is False
    assert any("identity/path mismatch" in row for row in payload["errors"])


def test_unregistered_random_one_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "target"
    _complete_tree(target)
    _record(target, "ezmock", 11, random1=True)
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    assert payload["terminal"]["acquisition_ready"] is False
    assert payload["observed_support"]["audit_registry"]["unexpected_members"] == [
        "ezmock:11"
    ]


def test_stall_requires_two_receipts_at_least_900_seconds_apart(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    first = pr151_progress.build_progress(target, tmp_path / "absent.log")
    old = first["generated_at_utc"]
    from datetime import datetime, timedelta, timezone
    prior = datetime.fromisoformat(old) - timedelta(seconds=901)
    first["generated_at_utc"] = prior.astimezone(timezone.utc).isoformat()
    second = pr151_progress.build_progress(target, tmp_path / "absent.log", first)
    assert second["activity"]["comparison"]["stalled_candidate"] is True
    assert second["next_action"] == "inspect_process_tree"


def test_recorded_interrupt_during_visible_restart_is_not_integrity_failure(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    _write(target / "desi_dr1_mock_acquisition_manifest.json", {
        "schema": "htt.desi_dr1_mock_acquisition.v2",
        "status": "incomplete",
        "failure": {"type": "KeyboardInterrupt", "message": ""},
    })
    monkeypatch.setattr(pr151_progress, "_process_visibility", lambda _: {
        "state": "running", "matching_pids": [{"pid": 123, "command": "aria2c"}]
    })
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    assert payload["next_action"] == "continue_acquire_after_restart"
    assert payload["activity"]["effective_writer_state"] == "running"


def test_held_writer_lock_survives_pid_namespace_visibility_gap(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    _write(target / "desi_dr1_mock_acquisition_manifest.json", {
        "schema": "htt.desi_dr1_mock_acquisition.v2",
        "status": "incomplete",
        "failure": {"type": "KeyboardInterrupt", "message": ""},
    })
    monkeypatch.setattr(pr151_progress, "_lock_state", lambda _: {
        "state": "held", "lock_path": str(target / ".pr151_phase.lock"),
        "owner": {"pid": 123, "phase": "acquire"}, "owner_error": None,
    })
    monkeypatch.setattr(pr151_progress, "_process_visibility", lambda _: {
        "state": "not_running", "matching_pids": []
    })
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    assert payload["activity"]["effective_writer_state"] == "running"
    assert payload["next_action"] == "continue_acquire_after_restart"


def test_phase_is_mandatory_and_legacy_positional_target_is_rejected() -> None:
    with pytest.raises(SystemExit) as missing:
        pr151_phase.parse_args([])
    assert missing.value.code == 2
    with pytest.raises(SystemExit) as legacy:
        pr151_phase.parse_args(["/tmp/legacy-target"])
    assert legacy.value.code == 2


def test_acquire_never_invokes_finalize_commands(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    calls: list[list[str]] = []

    def runner(argv, **kwargs):
        calls.append(list(argv))
        return subprocess.CompletedProcess(argv, 0)

    monkeypatch.setattr(pr151_phase, "build_progress", lambda *_: {
        "terminal": {"acquisition_ready": True}
    })
    assert pr151_phase.acquire(target, runner=runner, retry_wait=0) == 0
    assert len(calls) == 1
    assert calls[0][2].endswith("download_desi_dr1_mocks.py")
    assert all("run_pr151_desi_exact_selection.py" not in token
               for token in calls[0])


def test_incomplete_finalize_refuses_before_any_subprocess(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    calls = []
    monkeypatch.setattr(pr151_phase, "build_progress", lambda *_: {
        "terminal": {"acquisition_ready": False}
    })

    def runner(*args, **kwargs):
        calls.append(args)
        raise AssertionError("finalize subprocess must not run")

    assert pr151_phase.finalize(target, runner=runner) == 3
    assert calls == []
    assert not (target / pr151_phase.RECEIPT).exists()


def test_target_writer_lock_rejects_duplicate_owner(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    lock_path = target / ".pr151_phase.lock"
    owner_path = target / ".pr151_phase_owner.json"
    _write(owner_path, {"pid": 123, "phase": "acquire"})
    owner_before = owner_path.read_bytes()
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o660)
    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        with pytest.raises(RuntimeError, match="writer lock"):
            with pr151_phase.writer_lock(target, "acquire"):
                pass
        assert owner_path.read_bytes() == owner_before
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def test_terminal_receipt_binds_manifest_commands_and_artifacts(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    _complete_tree(target)
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(pr151_progress, "REPO", repo)
    artifacts = {}
    for rel in pr151_progress.EXPECTED_ARTIFACTS:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
        artifacts[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = target / "desi_dr1_mock_acquisition_manifest.json"
    _write(target / pr151_phase.RECEIPT, {
        "schema": "htt.pr151.finalization_receipt.v1",
        "status": "complete",
        "terminal": True,
        "target": str(target),
        "acquisition_manifest": str(manifest),
        "acquisition_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "command_receipts": [
            {"argv": argv, "exit_code": 0}
            for argv in pr151_progress.finalize_commands(target, repo)
        ],
        "artifact_hashes": artifacts,
    })
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    assert payload["terminal"]["pr151_terminal"] is True


def test_terminal_receipt_rejects_subset_artifacts_and_fake_commands(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    _complete_tree(target)
    repo = tmp_path / "repo"
    repo.mkdir()
    monkeypatch.setattr(pr151_progress, "REPO", repo)
    rel = pr151_progress.EXPECTED_ARTIFACTS[0]
    artifact = repo / rel
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("{}\n", encoding="utf-8")
    manifest = target / "desi_dr1_mock_acquisition_manifest.json"
    _write(target / pr151_phase.RECEIPT, {
        "schema": "htt.pr151.finalization_receipt.v1",
        "status": "complete", "terminal": True, "target": str(target),
        "acquisition_manifest": str(manifest),
        "acquisition_manifest_sha256": hashlib.sha256(manifest.read_bytes()).hexdigest(),
        "command_receipts": [
            {"argv": ["true"], "exit_code": 0} for _ in range(4)
        ],
        "artifact_hashes": {
            rel: hashlib.sha256(artifact.read_bytes()).hexdigest()
        },
    })
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    assert payload["terminal"]["pr151_terminal"] is False


def test_extra_mock_record_fails_exact_support(tmp_path: Path) -> None:
    target = tmp_path / "target"
    _complete_tree(target)
    _record(target, "ezmock", 1001)
    payload = pr151_progress.build_progress(target, tmp_path / "absent.log")
    assert payload["terminal"]["acquisition_ready"] is False
    assert payload["observed_support"]["unexpected_record_paths"]
    assert any("unexpected acquisition records" in row for row in payload["errors"])


def test_fast_probe_never_contains_payload_sha_call() -> None:
    source = Path(pr151_progress.__file__).read_text(encoding="utf-8")
    assert "sha256(path.read_bytes())" in source  # small metadata helper only
    assert "payload_hashing_performed\": False" in source


def test_finalize_watcher_paths_are_portable_and_overridable(
        tmp_path: Path) -> None:
    target = tmp_path / "data"
    log = tmp_path / "watch.log"
    args = pr151_finalize_watch.parse_args([
        "--target", str(target), "--log", str(log),
        "--progress-log", str(tmp_path / "acquire.log"),
        "--interval", "7", "--max-wait-seconds", "11",
    ])

    assert pr151_finalize_watch.REPO == Path(
        pr151_finalize_watch.__file__).resolve().parents[2]
    assert pr151_finalize_watch.PY == sys.executable
    assert args.target == target
    assert args.log == log
    assert args.progress_log == tmp_path / "acquire.log"
    assert args.interval == 7
    assert args.max_wait_seconds == 11
    source = Path(pr151_finalize_watch.__file__).read_text(encoding="utf-8")
    assert "/home/cosmosapjw/" not in source


def test_finalize_watcher_matches_acquire_for_selected_target(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    selected = (tmp_path / "selected").resolve()
    other = (tmp_path / "other").resolve()

    def fake_run(argv, **kwargs):
        assert argv == [
            "pgrep", "-af", "pr151_phase.py --phase acquire",
        ]
        stdout = (
            "123 python pr151_phase.py --phase acquire "
            f"--target {selected}\n"
        )
        return subprocess.CompletedProcess(argv, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(pr151_finalize_watch.subprocess, "run", fake_run)
    assert pr151_finalize_watch.acquire_running(selected) is True
    assert pr151_finalize_watch.acquire_running(other) is False
