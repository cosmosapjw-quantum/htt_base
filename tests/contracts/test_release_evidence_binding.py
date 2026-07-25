from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from common.evidence_graph import (
    EvidenceAxes,
    EvidenceGraphError,
    EvidenceNode,
    EvidenceNodeKind,
    EvidenceStatus,
    ProcessResult,
    load_literal_release_pin_fields,
)
from common.remediation_state import ScientificStatus
from common.release_evidence_binding import (
    DEFAULT_RELEASE_EVIDENCE_PIN,
    _verify_artifact_manifest,
    _verify_graph_sources,
    consume_release_evidence,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
WRONG_DIGEST = "f" * 64


def test_exact_audit_disclosure_preserves_all_three_axes_and_blocks_release():
    disclosure = consume_release_evidence(REPO_ROOT, mode="audit_disclosure")

    assert disclosure["mode"] == "audit_disclosure"
    assert disclosure["graph_ref"] == DEFAULT_RELEASE_EVIDENCE_PIN.graph_ref
    assert disclosure["receipt_id"] == DEFAULT_RELEASE_EVIDENCE_PIN.receipt_id
    assert disclosure["parent_receipt_id"] == (
        DEFAULT_RELEASE_EVIDENCE_PIN.parent_receipt_id
    )
    assert (
        disclosure["authority_registry_ref"]
        == DEFAULT_RELEASE_EVIDENCE_PIN.authority_registry_ref
    )
    assert disclosure["process_result"] == "PASS"
    # PR-124: mechanics evidence is PRESENT (governance authority delivered);
    # the release kill switch is claim_release_allowed=False, not a BLOCKED
    # evidence status.
    assert disclosure["evidence_status"] == "PRESENT"
    assert disclosure["evidence_statuses"] == ["PRESENT"]
    assert disclosure["scientific_status"] == "OPEN"
    assert disclosure["claim_release_allowed"] is False
    assert disclosure["audit_disclosure_allowed"] is True
    assert disclosure["authority_status"] == "REQUIRES_TRUSTED_REGISTRY_VALIDATION"


def test_claim_release_mode_fails_closed_for_the_checked_in_receipt():
    with pytest.raises(EvidenceGraphError):
        consume_release_evidence(REPO_ROOT, mode="claim_release")


@pytest.mark.parametrize(
    ("field", "error"),
    (
        ("graph_file_sha256", "evidence graph file hash mismatch"),
        ("receipt_file_sha256", "evidence receipt file hash mismatch"),
        ("receipt_id", "loaded evidence receipt does not match expected_receipt_id"),
        ("parent_receipt_file_sha256", "parent evidence receipt file hash mismatch"),
        ("closure_file_sha256", "closure report file hash mismatch"),
        ("artifact_manifest_file_sha256", "artifact manifest file hash mismatch"),
    ),
)
def test_exact_pin_tampering_is_rejected(field: str, error: str):
    tampered_pin = replace(DEFAULT_RELEASE_EVIDENCE_PIN, **{field: WRONG_DIGEST})

    with pytest.raises(EvidenceGraphError, match=error):
        consume_release_evidence(REPO_ROOT, pin=tampered_pin)


def test_caller_cannot_supply_readiness_flag_or_unknown_mode():
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        consume_release_evidence(REPO_ROOT, ready=True)  # type: ignore[call-arg]

    with pytest.raises(EvidenceGraphError, match="unknown evidence consumption mode"):
        consume_release_evidence(REPO_ROOT, mode="release_even_if_blocked")


@pytest.mark.parametrize(
    "alternate_path",
    (
        "../docs/generated/pr122_claim_evidence_graph.json",
        "docs/generated/../generated/pr122_claim_evidence_graph.json",
        str(REPO_ROOT / DEFAULT_RELEASE_EVIDENCE_PIN.graph_path),
    ),
)
def test_alternate_or_escaping_graph_paths_cannot_replace_the_pinned_path(
    alternate_path: str,
):
    with pytest.raises(
        EvidenceGraphError, match="graph_path must be repository-relative"
    ):
        replace(DEFAULT_RELEASE_EVIDENCE_PIN, graph_path=alternate_path)


def test_non_pin_objects_cannot_override_the_release_policy():
    forged = {
        **DEFAULT_RELEASE_EVIDENCE_PIN.__dict__,
        "claim_release_allowed": True,
        "skip_authority_validation": True,
    }

    with pytest.raises(TypeError, match="pin must be a ReleaseEvidencePin"):
        consume_release_evidence(REPO_ROOT, pin=forged)  # type: ignore[arg-type]


def test_stale_but_well_formed_release_pin_is_rejected_before_audit_disclosure() -> (
    None
):
    tampered = replace(
        DEFAULT_RELEASE_EVIDENCE_PIN,
        artifact_manifest_file_sha256=WRONG_DIGEST,
    )
    with pytest.raises(
        EvidenceGraphError, match="artifact manifest file hash mismatch"
    ):
        consume_release_evidence(REPO_ROOT, pin=tampered)


def test_invalid_artifact_manifest_structure_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    artifact = tmp_path / "artifact.txt"
    source.write_text("source\n", encoding="utf-8")
    artifact.write_text("artifact\n", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "htt.pr122.artifact_manifest.v1",
                "owner": "COMMON",
                "implementation_scope": "common",
                "claim_tier": "exploratory",
                "transfer_source": "none",
                "config_hash": "0" * 64,
                "input_hashes": [
                    f"source.txt:{hashlib.sha256(source.read_bytes()).hexdigest()}"
                ],
                "sky_support_status": "not_directional",
                "null_mock_status": "not_statistical",
                "caveats": ["test-only invalid manifest"],
                "generating_command": "test-only",
                "git_commit_or_worktree_state": "test-only",
                "artifacts": [
                    {
                        "path": "artifact.txt",
                        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
                        "artifact_role": "test",
                        "undeclared_field": "must fail",
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        EvidenceGraphError, match="invalid PR-122 artifact manifest row"
    ):
        _verify_artifact_manifest(tmp_path, manifest)


def test_artifact_manifest_rejects_path_aliases_and_symlink_parents(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.txt"
    artifact = tmp_path / "artifact.txt"
    source.write_text("source\n", encoding="utf-8")
    artifact.write_text("artifact\n", encoding="utf-8")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    artifact_hash = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.json"
    payload = {
        "schema": "htt.pr122.artifact_manifest.v1",
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "exploratory",
        "transfer_source": "none",
        "config_hash": "0" * 64,
        "input_hashes": [f"source.txt:{source_hash}"],
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "caveats": ["test-only invalid manifest"],
        "generating_command": "test-only",
        "git_commit_or_worktree_state": "test-only",
        "artifacts": [
            {
                "path": "sub/../artifact.txt",
                "sha256": artifact_hash,
                "artifact_role": "test",
            }
        ],
    }
    (tmp_path / "sub").mkdir()
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(
        EvidenceGraphError, match="canonical repository-relative"
    ):
        _verify_artifact_manifest(tmp_path, manifest)

    (tmp_path / "real").mkdir()
    (tmp_path / "real" / "artifact.txt").write_bytes(artifact.read_bytes())
    (tmp_path / "alias").symlink_to(tmp_path / "real", target_is_directory=True)
    payload["artifacts"][0]["path"] = "alias/artifact.txt"
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    with pytest.raises(EvidenceGraphError, match="symlink component"):
        _verify_artifact_manifest(tmp_path, manifest)


def test_data_only_pin_rejects_noncanonical_trust_root_fields() -> None:
    pin_source = REPO_ROOT / "htt/src/common/release_evidence_pin.py"
    tree = ast.parse(pin_source.read_text(encoding="utf-8"))
    assert not any(
        isinstance(
            node,
            (
                ast.Import,
                ast.ImportFrom,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        )
        for node in tree.body
    )
    with pytest.raises(
        EvidenceGraphError, match="graph_path must be repository-relative"
    ):
        replace(DEFAULT_RELEASE_EVIDENCE_PIN, graph_path="../graph.json")
    with pytest.raises(
        EvidenceGraphError, match="graph_ref must be a lowercase SHA-256"
    ):
        replace(DEFAULT_RELEASE_EVIDENCE_PIN, graph_ref="not-a-digest")


def test_executable_release_pin_payload_is_rejected_without_execution(
    tmp_path: Path,
) -> None:
    source = REPO_ROOT / "htt/src/common/release_evidence_pin.py"
    assert load_literal_release_pin_fields(source) == (
        DEFAULT_RELEASE_EVIDENCE_PIN.__dict__
    )

    sentinel = tmp_path / "executed.txt"
    malicious = tmp_path / "release_evidence_pin.py"
    malicious.write_text(
        '"""malicious fixed-point payload"""\n'
        "DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS = {\n"
        f"    'graph_path': __import__('pathlib').Path({str(sentinel)!r}).write_text('executed'),\n"
        "}\n"
        "__all__ = ['DEFAULT_RELEASE_EVIDENCE_PIN_FIELDS']\n",
        encoding="utf-8",
    )
    with pytest.raises(EvidenceGraphError, match="executable syntax"):
        load_literal_release_pin_fields(malicious)
    assert not sentinel.exists()


def test_historical_source_hash_is_not_live_authority(tmp_path: Path) -> None:
    source = tmp_path / "verifier.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    node = EvidenceNode(
        kind=EvidenceNodeKind.PRODUCER,
        label="release-verifier",
        content_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        axes=EvidenceAxes(
            ProcessResult.PASS,
            EvidenceStatus.PRESENT,
            ScientificStatus.OPEN,
        ),
        metadata={"path": "verifier.py"},
    )
    graph = SimpleNamespace(nodes=(node,))
    _verify_graph_sources(tmp_path, graph)  # type: ignore[arg-type]

    source.write_text("VALUE = 2\n", encoding="utf-8")
    _verify_graph_sources(tmp_path, graph)  # type: ignore[arg-type]


def test_non_source_graph_input_drift_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "config.yaml"
    source.write_text("value: 1\n", encoding="utf-8")
    node = EvidenceNode(
        kind=EvidenceNodeKind.INPUT,
        label="frozen-config",
        content_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        axes=EvidenceAxes(
            ProcessResult.PASS,
            EvidenceStatus.PRESENT,
            ScientificStatus.OPEN,
        ),
        metadata={"path": "config.yaml"},
    )
    graph = SimpleNamespace(nodes=(node,))
    _verify_graph_sources(tmp_path, graph)  # type: ignore[arg-type]

    source.write_text("value: 2\n", encoding="utf-8")
    with pytest.raises(EvidenceGraphError, match="file hash mismatch"):
        _verify_graph_sources(tmp_path, graph)  # type: ignore[arg-type]
