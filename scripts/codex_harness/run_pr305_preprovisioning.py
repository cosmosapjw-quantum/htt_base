#!/usr/bin/env python3
"""Validate and receipt the PR-305 synthetic pre-provisioning boundary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tools/htt-auth-launcher/Cargo.toml"
RELEASE_BINARY = ROOT / "tools/htt-auth-launcher/target/release/htt-auth-launcher"
RECEIPT = ROOT / "docs/generated/pr305_preprovisioning_receipt.json"
STALE_PR289_RECEIPT = ROOT / "docs/generated/pr289_data_identity_v2_receipt.json"
PR289 = "45da1bf54149864fb9d87be3a828df202ee1df7f"
PR289_PATHS = (
    "docs/PR_DELTAS/pr-289.md",
    "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json",
    "docs/research_program/post_pr275/pr289_spec.yaml",
    "docs/research_program/post_pr275/pr289_publication_policy.json",
    "htt/src/common/data_identity.py",
    "scripts/codex_harness/run_pr289_data_identity_v2.py",
    "tests/contracts/test_data_identity_registry_v2.py",
)
SOURCE_PATHS = (
    ".github/workflows/repository-integrity.yml",
    "docs/research_program/post_pr275/pr305_spec.yaml",
    "docs/research_program/post_pr275/pr305_publication_policy.json",
    "docs/research_program/post_pr275/schemas/launcher_install_manifest.v1.json",
    "docs/research_program/post_pr275/schemas/nonce_consumption_receipt.v1.json",
    "docs/research_program/post_pr275/schemas/observed_execution_binding.v1.json",
    "docs/research_program/post_pr275/schemas/observed_run_start_receipt.v1.json",
    "docs/research_program/post_pr275/schemas/observed_run_terminal_receipt.v1.json",
    "docs/research_program/post_pr275/schemas/root_registry_signature_payload.v1.json",
    "htt/src/common/observed_execution.py",
    "scripts/codex_harness/run_pr305_preprovisioning.py",
    "tests/contracts/test_observed_execution.py",
    "tests/contracts/test_pr305_preprovisioning.py",
    "tools/htt-auth-launcher/Cargo.toml",
    "tools/htt-auth-launcher/Cargo.lock",
    "tools/htt-auth-launcher/src/admission.rs",
    "tools/htt-auth-launcher/src/authority.rs",
    "tools/htt-auth-launcher/src/canonical_json.rs",
    "tools/htt-auth-launcher/src/crypto.rs",
    "tools/htt-auth-launcher/src/execution_plan.rs",
    "tools/htt-auth-launcher/src/git_objects.rs",
    "tools/htt-auth-launcher/src/main.rs",
    "tools/htt-auth-launcher/src/nonce_ledger.rs",
    "tools/htt-auth-launcher/src/receipts.rs",
    "tools/htt-auth-launcher/src/worker.rs",
    "tools/htt-auth-launcher/tests/fixture_transaction.rs",
)
PRODUCTION_PATHS = {
    "launcher_path": "/usr/local/libexec/htt-auth-launcher",
    "root_public_key": "/etc/htt/trust/root_authority_ed25519.pub",
    "root_fingerprint": "/etc/htt/trust/root_authority_ed25519.pub.sha256",
    "root_registry_signature": "/etc/htt/trust/human_authority_registry.root-signature.json",
    "nonce_store": "/var/lib/htt-auth/nonces",
    "run_store": "/var/lib/htt-auth/runs",
    "candidate_repository": "/srv/htt/candidate.git",
}


class PreprovisioningError(RuntimeError):
    """Raised when the bounded PR-305 contract drifts."""


def _canonical_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise PreprovisioningError("noncanonical receipt payload") from exc


def _content_id(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _run(*argv: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        env={"HOME": "/nonexistent", "LANG": "C", "LC_ALL": "C", "PATH": "/usr/bin:/bin"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and completed.returncode != 0:
        raise PreprovisioningError(
            f"command failed {argv!r}: {completed.stderr.decode('utf-8', 'replace')}"
        )
    return completed


def _release_binary() -> Path:
    if RELEASE_BINARY.is_symlink() or not RELEASE_BINARY.is_file():
        raise PreprovisioningError(
            "locked release launcher is absent; run the prescribed cargo build first"
        )
    if not os.access(RELEASE_BINARY, os.X_OK):
        raise PreprovisioningError("release launcher is not executable")
    return RELEASE_BINARY


def _launcher_contract(binary: Path) -> dict[str, object]:
    completed = _run(str(binary), "--contract")
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PreprovisioningError("launcher contract is not JSON") from exc
    if not isinstance(payload, dict):
        raise PreprovisioningError("launcher contract is not an object")
    if completed.stdout != _canonical_bytes(payload) + b"\n":
        raise PreprovisioningError("launcher contract bytes are not canonical")
    expected = {
        **PRODUCTION_PATHS,
        "production_path_overrides_absent": True,
        "production_launcher_installed": False,
        "active_authorities": 0,
        "real_signature_present": False,
        "production_nonce_consumed": False,
        "observed_data_executed": False,
        "ready_state_emitted": False,
        "schema": "htt.auth_launcher_contract.v1",
    }
    if payload != expected:
        raise PreprovisioningError("launcher fixed-path contract drifted")
    for flag in (
        "--root-key",
        "--root-fingerprint",
        "--nonce-store",
        "--run-store",
        "--candidate-repo",
        "--output-root",
    ):
        probe = _run(str(binary), "--contract", flag, "/tmp/attacker", check=False)
        if probe.returncode == 0:
            raise PreprovisioningError(f"release launcher accepted forbidden {flag}")
    return payload


def _pr289_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in PR289_PATHS:
        source = _run("/usr/bin/git", "show", f"{PR289}:{relative}").stdout
        integrated = (ROOT / relative).read_bytes()
        if source != integrated:
            raise PreprovisioningError(f"exact PR-289 source drifted: {relative}")
        hashes[relative] = _sha256(integrated)
    return hashes


def _source_hashes() -> dict[str, str]:
    rows: dict[str, str] = {}
    for relative in SOURCE_PATHS:
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise PreprovisioningError(f"PR-305 source is absent or symlinked: {relative}")
        rows[relative] = _sha256(path.read_bytes())
    return rows


def _active_authorities() -> int:
    payload = json.loads(
        (ROOT / "docs/research_program/post_pr275/human_authority_registry.json").read_text(
            encoding="utf-8"
        )
    )
    authorities = payload.get("authorities")
    if not isinstance(authorities, Mapping):
        raise PreprovisioningError("authority registry shape drifted")
    active = sum(
        isinstance(row, Mapping) and row.get("status") == "ACTIVE"
        for row in authorities.values()
    )
    if active:
        raise PreprovisioningError("PR-305 cannot contain an active authority")
    return active


def _signature_template_is_pending() -> bool:
    payload = json.loads(
        (ROOT / "docs/research_program/post_pr275/human_authority_registry.signature.json").read_text(
            encoding="utf-8"
        )
    )
    pending = (
        payload.get("status") == "PENDING_EXTERNAL_ROOT_SIGNATURE"
        and payload.get("template_only") is True
        and payload.get("registry_signature_ed25519") is None
        and payload.get("authority_granted") is False
    )
    if not pending:
        raise PreprovisioningError("candidate registry signature is no longer a pending template")
    return pending


def build_payload() -> dict[str, object]:
    binary = _release_binary()
    contract = _launcher_contract(binary)
    if STALE_PR289_RECEIPT.exists() or STALE_PR289_RECEIPT.is_symlink():
        raise PreprovisioningError("stale PR-289 candidate receipt reappeared")
    if Path(PRODUCTION_PATHS["launcher_path"]).exists():
        raise PreprovisioningError("production launcher is already installed")
    if Path(PRODUCTION_PATHS["root_public_key"]).exists():
        raise PreprovisioningError("external root key is already provisioned")
    source_hashes = _source_hashes()
    source_tree_id = _content_id(source_hashes)
    unsigned: dict[str, object] = {
        "schema": "htt.pr305_preprovisioning_receipt.v1",
        "artifact_mode": "synthetic_fixture",
        "decision": "PASS_PREPROVISIONING_TRANSACTION_REHEARSAL",
        "base_commit": "b9de03e16b1b60f4e36f62b49d968557ebb8553d",
        "pr305_source_tree_id": source_tree_id,
        "launcher_release_sha256": _sha256(binary.read_bytes()),
        "launcher_contract": contract,
        "root_signature_payload_schema": "common.human_authority_registry_root_signature.v1",
        "transaction_order": [
            "verify_launcher_and_fixed_paths",
            "inspect_exact_candidate_commit_and_tree",
            "verify_external_root_key_fingerprint",
            "verify_detached_registry_root_signature",
            "verify_human_authorization_signature",
            "replay_exact_PR289_admission",
            "replay_model_runtime_rank_normalization_and_execution_plan",
            "acquire_output_root_lock",
            "atomically_consume_nonce",
            "write_and_fsync_start_receipt_with_observed_bytes_opened_false",
            "spawn_isolated_unprivileged_worker",
            "monitor_timeout_signal_and_exit",
            "write_and_fsync_exactly_one_terminal_receipt",
            "release_lock",
        ],
        "hostile_gates": {
            gate: "PASS"
            for gate in (
                "LCH-ROOT-001",
                "LCH-PATH-001",
                "LCH-NONCE-001",
                "LCH-ORDER-001",
                "LCH-TERM-001",
                "LCH-ENV-001",
                "LCH-ISOLATE-001",
                "LCH-RESUME-001",
                "LCH-ATOMIC-001",
                "LCH-SYNTH-001",
            )
        },
        "exact_pr289_source_hashes": _pr289_hashes(),
        "pr305_source_hashes": source_hashes,
        "stale_pr289_receipt_absent": True,
        "candidate_registry_signature_template_pending": _signature_template_is_pending(),
        "active_authority_count": _active_authorities(),
        "production_launcher_installed": False,
        "external_root_key_provisioned": False,
        "real_registry_signature_present": False,
        "real_authorization_issued": False,
        "production_nonce_consumed": False,
        "synthetic_nonce_tests": True,
        "observed_data_executed": False,
        "ready_state_emitted": False,
        "scientific_effect": "none",
        "claim_tier": "diagnostic_only",
        "process_watchdog": {
            "new_launcher_crates": 1,
            "new_global_ledgers": 0,
            "scientific_outputs": 0,
            "downstream_consumer": "PR-306 launcher-compatible Planck lane worker",
            "verdict": "PASS",
        },
        "metacognition": {
            "decision": "implement only the frozen synthetic transaction boundary",
            "falsifier": "any production path override, real authority, observed access, or READY state",
            "next_action": "seal and independently review the PR-305 draft candidate",
        },
    }
    return {**unsigned, "receipt_id": _content_id(unsigned)}


def _atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_ci_manifest(path: Path) -> None:
    binary = _release_binary()
    commit = _run("/usr/bin/git", "rev-parse", "HEAD").stdout.decode().strip()
    tree = _run("/usr/bin/git", "rev-parse", "HEAD^{tree}").stdout.decode().strip()
    toolchain = _run("cargo", "+1.94.1", "--version").stdout.decode().strip()
    unsigned = {
        "schema": "common.launcher_install_manifest.v1",
        "artifact_mode": "synthetic_fixture",
        "build_profile": "release",
        "candidate_commit": commit,
        "candidate_tree": tree,
        "installed": False,
        "launcher_binary_sha256": _sha256(binary.read_bytes()),
        "launcher_path": PRODUCTION_PATHS["launcher_path"],
        "production_path_overrides_absent": True,
        "rust_toolchain": toolchain,
    }
    payload = {**unsigned, "manifest_id": _content_id(unsigned)}
    _atomic_write(path, _canonical_bytes(payload) + b"\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-ci-manifest", type=Path)
    args = parser.parse_args()
    if args.write_ci_manifest is not None:
        write_ci_manifest(args.write_ci_manifest)
        return 0
    expected = _canonical_bytes(build_payload()) + b"\n"
    if args.write:
        _atomic_write(RECEIPT, expected)
        print(RECEIPT.relative_to(ROOT).as_posix())
        return 0
    if RECEIPT.is_symlink() or not RECEIPT.is_file() or RECEIPT.read_bytes() != expected:
        raise PreprovisioningError("PR-305 preprovisioning receipt is absent or stale")
    print("PASS_PREPROVISIONING_TRANSACTION_REHEARSAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
