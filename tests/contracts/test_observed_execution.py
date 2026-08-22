from __future__ import annotations

import json
from pathlib import Path

import pytest

from common.observed_execution import (
    ArtifactMode,
    NonceConsumptionReceiptV1,
    ObservedExecutionBindingV1,
    ObservedExecutionError,
    ObservedRunStartReceiptV1,
    ObservedRunTerminalReceiptV1,
    assert_resume_compatible,
    parse_strict_json_bytes,
    require_production_terminal,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "docs/research_program/post_pr275/schemas"
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64
SHA_D = "sha256:" + "d" * 64
GIT_A = "a" * 40
GIT_B = "b" * 40


def _binding(*, candidate_tree: str = GIT_B) -> ObservedExecutionBindingV1:
    return ObservedExecutionBindingV1.build(
        artifact_mode=ArtifactMode.SYNTHETIC_FIXTURE,
        run_id="synthetic-run-001",
        lane_id="PLANCK",
        candidate_commit=GIT_A,
        candidate_tree=candidate_tree,
        exact_admission_record_ids=(SHA_A, SHA_B),
        lane_admission_bundle_id=SHA_C,
        authorization_id=SHA_D,
        model_contract_content_id=SHA_A,
        runtime_environment_receipt_id=SHA_B,
        computed_response_rank_receipt_id=SHA_C,
        normalization_evidence_id=SHA_D,
        execution_plan_content_id=SHA_A,
        launcher_binary_sha256=SHA_B,
        output_root="/tmp/htt-pr305-synthetic-output",
    )


def test_binding_id_covers_ordered_records_and_candidate_tree() -> None:
    first = _binding()
    reordered = ObservedExecutionBindingV1.build(
        **{
            **first.unsigned_payload(),
            "exact_admission_record_ids": tuple(
                reversed(first.exact_admission_record_ids)
            ),
        }
    )
    changed_tree = _binding(candidate_tree="c" * 40)

    assert reordered.binding_id != first.binding_id
    assert changed_tree.binding_id != first.binding_id
    assert ObservedExecutionBindingV1.from_mapping(first.as_payload()) == first


def test_nonce_receipt_rejects_raw_nonce_and_binds_ledger_entry() -> None:
    receipt = NonceConsumptionReceiptV1.build(
        artifact_mode=ArtifactMode.SYNTHETIC_FIXTURE,
        authorization_id=SHA_A,
        run_id="synthetic-run-001",
        nonce_sha256=SHA_B,
        consumed_at_utc="2026-08-22T00:00:00Z",
        ledger_entry_identity=SHA_C,
    )

    assert "nonce" not in receipt.as_payload()
    assert receipt.receipt_id.startswith("sha256:")
    assert NonceConsumptionReceiptV1.from_mapping(receipt.as_payload()) == receipt

    with pytest.raises(ObservedExecutionError, match="nonce_sha256"):
        NonceConsumptionReceiptV1.build(
            artifact_mode=ArtifactMode.SYNTHETIC_FIXTURE,
            authorization_id=SHA_A,
            run_id="synthetic-run-001",
            nonce_sha256="nonce:v1:" + "1" * 64,
            consumed_at_utc="2026-08-22T00:00:00Z",
            ledger_entry_identity=SHA_C,
        )


def test_start_receipt_cannot_claim_observed_bytes_opened() -> None:
    binding = _binding()
    start = ObservedRunStartReceiptV1.build(
        artifact_mode=ArtifactMode.SYNTHETIC_FIXTURE,
        binding_id=binding.binding_id,
        started_at_utc="2026-08-22T00:00:00Z",
        observed_bytes_opened=False,
    )
    assert start.observed_bytes_opened is False

    payload = start.as_payload()
    payload["observed_bytes_opened"] = True
    with pytest.raises(ObservedExecutionError, match="observed_bytes_opened"):
        ObservedRunStartReceiptV1.from_mapping(payload)


@pytest.mark.parametrize(
    ("terminal", "exit_code", "signal", "timeout"),
    [
        ("SUCCESS", 0, None, False),
        ("ERROR", 7, None, False),
        ("TIMEOUT", None, None, True),
        ("SIGNAL", None, 15, False),
    ],
)
def test_terminal_receipt_has_consistent_exit_semantics(
    terminal: str,
    exit_code: int | None,
    signal: int | None,
    timeout: bool,
) -> None:
    binding = _binding()
    receipt = ObservedRunTerminalReceiptV1.build(
        artifact_mode=ArtifactMode.SYNTHETIC_FIXTURE,
        binding_id=binding.binding_id,
        terminal=terminal,
        exit_code=exit_code,
        observed_bytes_opened=False,
        output_artifact_hashes={},
        stdout_sha256=SHA_A,
        stderr_sha256=SHA_B,
        started_at_utc="2026-08-22T00:00:00Z",
        ended_at_utc="2026-08-22T00:00:01Z",
        signal=signal,
        timeout=timeout,
    )
    assert receipt.terminal == terminal
    assert ObservedRunTerminalReceiptV1.from_mapping(receipt.as_payload()) == receipt


def test_synthetic_terminal_is_never_accepted_as_production() -> None:
    binding = _binding()
    terminal = ObservedRunTerminalReceiptV1.build(
        artifact_mode=ArtifactMode.SYNTHETIC_FIXTURE,
        binding_id=binding.binding_id,
        terminal="SUCCESS",
        exit_code=0,
        observed_bytes_opened=False,
        output_artifact_hashes={},
        stdout_sha256=SHA_A,
        stderr_sha256=SHA_B,
        started_at_utc="2026-08-22T00:00:00Z",
        ended_at_utc="2026-08-22T00:00:01Z",
        signal=None,
        timeout=False,
    )

    with pytest.raises(ObservedExecutionError, match="synthetic"):
        require_production_terminal(terminal)


def test_resume_rejects_any_binding_identity_drift() -> None:
    with pytest.raises(ObservedExecutionError, match="resume binding"):
        assert_resume_compatible(_binding(), _binding(candidate_tree="c" * 40))


def test_strict_json_rejects_duplicate_keys_and_noncanonical_bytes() -> None:
    with pytest.raises(ObservedExecutionError, match="duplicate"):
        parse_strict_json_bytes(b'{"schema":"x","schema":"x"}')

    with pytest.raises(ObservedExecutionError, match="canonical"):
        parse_strict_json_bytes(b'{ "schema": "x" }')


@pytest.mark.parametrize(
    "name",
    [
        "root_registry_signature_payload.v1.json",
        "launcher_install_manifest.v1.json",
        "observed_execution_binding.v1.json",
        "observed_run_start_receipt.v1.json",
        "observed_run_terminal_receipt.v1.json",
        "nonce_consumption_receipt.v1.json",
    ],
)
def test_wire_schema_files_are_closed_world(name: str) -> None:
    payload = json.loads((SCHEMA_ROOT / name).read_text(encoding="utf-8"))
    assert payload["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert payload["type"] == "object"
    assert payload["additionalProperties"] is False
    assert set(payload["required"]) == set(payload["properties"])
