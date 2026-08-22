from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = ROOT / "scripts/codex_harness/run_pr305_preprovisioning.py"
RELEASE = ROOT / "tools/htt-auth-launcher/target/release/htt-auth-launcher"
MAIN = ROOT / "tools/htt-auth-launcher/src/main.rs"
STALE = ROOT / "docs/generated/pr289_data_identity_v2_receipt.json"


def _runner():
    spec = importlib.util.spec_from_file_location("pr305_preprovisioning", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_contract_is_rehearsal_only_and_fixed_path() -> None:
    completed = subprocess.run(
        [str(RELEASE), "--contract"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    payload = json.loads(completed.stdout)
    assert payload["production_path_overrides_absent"] is True
    assert payload["production_launcher_installed"] is False
    assert payload["active_authorities"] == 0
    assert payload["real_signature_present"] is False
    assert payload["production_nonce_consumed"] is False
    assert payload["observed_data_executed"] is False
    assert payload["ready_state_emitted"] is False


@pytest.mark.parametrize(
    "flag",
    [
        "--root-key",
        "--root-fingerprint",
        "--nonce-store",
        "--run-store",
        "--candidate-repo",
        "--output-root",
    ],
)
def test_release_binary_rejects_path_override_flags(flag: str) -> None:
    completed = subprocess.run(
        [str(RELEASE), "--contract", flag, "/tmp/attacker"],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode == 78
    assert not STALE.exists()


def test_transaction_order_is_lock_nonce_start_worker_terminal() -> None:
    source = MAIN.read_text(encoding="utf-8")
    ordered = (
        "ReceiptStore::acquire",
        "consume_nonce(",
        "store.write_start(",
        "run_worker(",
        "store.write_terminal(",
    )
    positions = tuple(source.index(marker) for marker in ordered)
    assert positions == tuple(sorted(positions))


def test_private_signing_keys_are_fixture_only() -> None:
    source = MAIN.read_text(encoding="utf-8")
    production, test_only = source.split("#[cfg(test)]\nmod tests", maxsplit=1)
    assert "SigningKey" not in production
    assert "SigningKey" in test_only
    for path in ROOT.glob("**/*"):
        if path.is_file() and ".git" not in path.parts and "target" not in path.parts:
            if path.suffix in {".pem", ".key", ".p12", ".pfx"}:
                pytest.fail(f"candidate contains forbidden key-like file: {path}")


def test_preprovisioning_payload_is_zero_authority_zero_execution() -> None:
    payload = _runner().build_payload()
    assert payload["decision"] == "PASS_PREPROVISIONING_TRANSACTION_REHEARSAL"
    assert payload["artifact_mode"] == "synthetic_fixture"
    assert payload["active_authority_count"] == 0
    assert payload["production_launcher_installed"] is False
    assert payload["external_root_key_provisioned"] is False
    assert payload["real_registry_signature_present"] is False
    assert payload["real_authorization_issued"] is False
    assert payload["production_nonce_consumed"] is False
    assert payload["observed_data_executed"] is False
    assert payload["ready_state_emitted"] is False
    assert set(payload["hostile_gates"].values()) == {"PASS"}


def test_root_payload_schema_is_closed_world() -> None:
    payload = json.loads(
        (
            ROOT
            / "docs/research_program/post_pr275/schemas/root_registry_signature_payload.v1.json"
        ).read_text(encoding="utf-8")
    )
    assert payload["additionalProperties"] is False
    assert set(payload["required"]) == set(payload["properties"])
    assert set(payload["properties"]) == {
        "schema",
        "registry_blob_sha256",
        "candidate_commit",
        "candidate_tree",
        "authorization_domain",
        "registry_version",
        "issued_at_utc",
        "root_authority_key_id",
    }
