"""Exact PR-122 evidence verifier for freeze/package consumers.

This implementation is hash-bound by the evidence graph.  The literal-only pin
fields in :mod:`common.release_evidence_pin` remain outside the graph to break
the otherwise unavoidable verifier -> graph -> verifier cycle.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Mapping, Sequence

from common.evidence_graph import (
    EvidenceGraph,
    EvidenceGraphError,
    EvidenceNodeKind,
    EvidenceReceipt,
    EvidenceStatus,
    ProcessResult,
    ReceiptDependencyKind,
    TestExecution,
    load_literal_release_pin_fields,
    load_exact_evidence_graph,
    load_exact_evidence_receipt,
    verify_pytest_selector_inputs,
)
from common.mes_successor_registry import (  # noqa: E402
    MesConsumerDeclaration,
    MesConsumerIssueCode,
    SourceAvailability,
    SourceHashBinding,
    finding_codes,
    scan_declared_mes_consumers,
    validate_mes_successor_registry,
)


_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class ReleaseEvidencePin:
    graph_path: str
    graph_file_sha256: str
    graph_ref: str
    receipt_path: str
    receipt_file_sha256: str
    receipt_id: str
    parent_receipt_path: str
    parent_receipt_file_sha256: str
    parent_receipt_id: str
    closure_path: str
    closure_file_sha256: str
    artifact_manifest_path: str
    artifact_manifest_file_sha256: str
    authority_registry_ref: str

    def __post_init__(self) -> None:
        for field in (
            "graph_path",
            "receipt_path",
            "parent_receipt_path",
            "closure_path",
            "artifact_manifest_path",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or not value or value != value.strip():
                raise EvidenceGraphError(f"{field} must be an exact path")
            path = PurePosixPath(value)
            if path.is_absolute() or any(
                part in {"", ".", ".."} for part in path.parts
            ):
                raise EvidenceGraphError(f"{field} must be repository-relative")
        for field in (
            "graph_file_sha256",
            "graph_ref",
            "receipt_file_sha256",
            "receipt_id",
            "parent_receipt_file_sha256",
            "parent_receipt_id",
            "closure_file_sha256",
            "artifact_manifest_file_sha256",
            "authority_registry_ref",
        ):
            value = getattr(self, field)
            if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
                raise EvidenceGraphError(f"{field} must be a lowercase SHA-256")


DEFAULT_RELEASE_EVIDENCE_PIN = ReleaseEvidencePin(
    **load_literal_release_pin_fields(
        Path(__file__).with_name("release_evidence_pin.py")
    )
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bound_path(root: Path, relative: str) -> Path:
    candidate = root.joinpath(*PurePosixPath(relative).parts)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EvidenceGraphError(
            f"evidence path escapes repository: {relative}"
        ) from exc
    if candidate.is_symlink() or not candidate.is_file():
        raise EvidenceGraphError(f"evidence path is missing or non-regular: {relative}")
    return candidate


def _require_file_hash(path: Path, expected: str, label: str) -> None:
    actual = _sha256_file(path)
    if actual != expected:
        raise EvidenceGraphError(
            f"{label} file hash mismatch: expected {expected}, got {actual}"
        )


def _verify_graph_sources(root: Path, graph: EvidenceGraph) -> None:
    """Rehash every path-bearing node so a stale generator cannot stay green."""

    for node in graph.nodes:
        raw_path = node.metadata.get("path")
        if raw_path is None:
            continue
        if not isinstance(raw_path, str):
            raise EvidenceGraphError("evidence node path metadata must be text")
        path = _bound_path(root, raw_path)
        if node.kind is EvidenceNodeKind.TEST:
            expected = node.metadata.get("file_sha256")
            if not isinstance(expected, str) or not _SHA256_RE.fullmatch(expected):
                raise EvidenceGraphError("test evidence node lacks exact file_sha256")
        else:
            expected = node.content_sha256
        _require_file_hash(path, expected, f"graph node {node.label}")
        if node.kind is EvidenceNodeKind.TEST:
            payload = _load_json(path, artifact=f"test evidence {node.label}")
            execution = TestExecution.from_pytest_evidence(payload)
            if node.test_execution is None:
                raise EvidenceGraphError("test evidence node lacks embedded execution")
            if execution.execution_ref != node.test_execution.execution_ref:
                raise EvidenceGraphError(
                    "live test evidence does not match graph execution_ref"
                )
            verify_pytest_selector_inputs(root, payload)


def _verify_mes_inventory(root: Path, graph: EvidenceGraph) -> None:
    declarations: list[MesConsumerDeclaration] = []
    for node in graph.nodes:
        consumer_id = node.metadata.get("consumer_id")
        if consumer_id is None:
            continue
        path = node.metadata.get("path")
        if (
            node.kind is not EvidenceNodeKind.INPUT
            or not isinstance(consumer_id, str)
            or not isinstance(path, str)
        ):
            raise EvidenceGraphError("invalid graph-bound MES consumer node")
        declarations.append(
            MesConsumerDeclaration(
                consumer_id=consumer_id,
                source=SourceHashBinding(
                    path=path,
                    availability=SourceAvailability.AVAILABLE,
                    sha256=node.content_sha256,
                ),
            )
        )
    if not declarations:
        raise EvidenceGraphError("graph has no hash-bound MES consumer inventory")
    report = scan_declared_mes_consumers(root, tuple(declarations))
    codes = finding_codes(report)
    registry_report = validate_mes_successor_registry(root)
    registry_codes = finding_codes(registry_report)
    integrity_codes = {
        MesConsumerIssueCode.SOURCE_MISSING.value,
        MesConsumerIssueCode.SOURCE_NOT_REGULAR.value,
        MesConsumerIssueCode.SOURCE_HASH_MISMATCH.value,
        MesConsumerIssueCode.CONSUMER_PARSE_ERROR.value,
        MesConsumerIssueCode.NO_ACTIVE_CONSUMERS_DECLARED.value,
        MesConsumerIssueCode.UNTRUSTED_REGISTRY_OVERRIDE.value,
        MesConsumerIssueCode.DIAGNOSTIC_WITNESS_INVALID.value,
        MesConsumerIssueCode.INVENTORY_INVALID.value,
        MesConsumerIssueCode.UNDECLARED_ACTIVE_CONSUMER.value,
        MesConsumerIssueCode.DECLARED_CONSUMER_NOT_DISCOVERED.value,
        MesConsumerIssueCode.EXCLUSION_HASH_MISMATCH.value,
    }
    if codes & integrity_codes or registry_codes & integrity_codes:
        failures = (codes | registry_codes) & integrity_codes
        raise EvidenceGraphError(
            f"live MES inventory integrity failure: {sorted(failures)}"
        )
    # PR-124: the typed MES authority is delivered. The kill switch inverts —
    # the live scan must now be CLEAN (no successor blocker, no stale triple,
    # no bypass) and the receipt-verified MES governance release must hold at
    # conditional C1. Any receipt drift re-introduces
    # SCIENTIFIC_AUTHORITY_BLOCKED via the live verifier and trips this gate.
    forbidden_blockers = {
        MesConsumerIssueCode.SUCCESSOR_MISSING.value,
        MesConsumerIssueCode.SCIENTIFIC_AUTHORITY_BLOCKED.value,
        MesConsumerIssueCode.SUCCESSOR_POINTER_MISSING.value,
        MesConsumerIssueCode.SUCCESSOR_BYPASS.value,
        MesConsumerIssueCode.STALE_MES_TRIPLE.value,
        MesConsumerIssueCode.SUCCESSOR_ID_MISMATCH.value,
    }
    if codes & forbidden_blockers or not report.release_allowed:
        raise EvidenceGraphError(
            "live MES inventory is not clean under the PR-124 authority: "
            f"{sorted(codes & forbidden_blockers)}"
        )
    if registry_codes & forbidden_blockers or not registry_report.release_allowed:
        raise EvidenceGraphError(
            "live MES witness is not clean under the PR-124 authority: "
            f"{sorted(registry_codes & forbidden_blockers)}"
        )


def _load_json(path: Path, *, artifact: str) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceGraphError(f"invalid {artifact} JSON") from exc
    if not isinstance(payload, Mapping):
        raise EvidenceGraphError(f"{artifact} root must be an object")
    return payload


def _load_closure(path: Path) -> Mapping[str, object]:
    return _load_json(path, artifact="PR-122 closure report")


def _verify_artifact_manifest(root: Path, path: Path) -> Mapping[str, object]:
    payload = _load_json(path, artifact="PR-122 artifact manifest")
    required_metadata = {
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "null_mock_status",
        "caveats",
        "generating_command",
        "git_commit_or_worktree_state",
    }
    if payload.get("schema") != "htt.pr122.artifact_manifest.v1":
        raise EvidenceGraphError("unsupported PR-122 artifact manifest schema")
    if not required_metadata <= set(payload):
        raise EvidenceGraphError("PR-122 artifact manifest lacks required metadata")
    input_rows = payload.get("input_hashes")
    if (
        not isinstance(input_rows, Sequence)
        or isinstance(input_rows, (str, bytes))
        or not input_rows
    ):
        raise EvidenceGraphError("PR-122 artifact manifest requires input hashes")
    seen_inputs: set[str] = set()
    for item in input_rows:
        if not isinstance(item, str) or ":" not in item:
            raise EvidenceGraphError("invalid PR-122 manifest input-hash row")
        relative, expected = item.rsplit(":", 1)
        if relative in seen_inputs:
            raise EvidenceGraphError("duplicate PR-122 manifest input path")
        seen_inputs.add(relative)
        if not _SHA256_RE.fullmatch(expected):
            raise EvidenceGraphError("manifest input hash must be SHA-256")
        _require_file_hash(
            _bound_path(root, relative), expected, f"manifest input {relative}"
        )
    rows = payload.get("artifacts")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        raise EvidenceGraphError("PR-122 artifact manifest requires artifacts")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {
            "path",
            "sha256",
            "artifact_role",
        }:
            raise EvidenceGraphError("invalid PR-122 artifact manifest row")
        relative = row["path"]
        expected = row["sha256"]
        if not isinstance(relative, str) or relative in seen:
            raise EvidenceGraphError("duplicate or invalid manifest artifact path")
        if not isinstance(expected, str) or not _SHA256_RE.fullmatch(expected):
            raise EvidenceGraphError("manifest artifact hash must be SHA-256")
        seen.add(relative)
        _require_file_hash(
            _bound_path(root, relative), expected, f"manifest artifact {relative}"
        )
    return payload


def consume_release_evidence(
    repo_root: Path | str,
    *,
    pin: ReleaseEvidencePin = DEFAULT_RELEASE_EVIDENCE_PIN,
    mode: str = "audit_disclosure",
) -> dict[str, object]:
    """Consume the exact graph/receipt/parent/closure set under one mode."""

    if not isinstance(pin, ReleaseEvidencePin):
        raise TypeError("pin must be a ReleaseEvidencePin")
    if mode not in {"audit_disclosure", "claim_release"}:
        raise EvidenceGraphError(f"unknown evidence consumption mode {mode!r}")
    root = Path(repo_root).resolve()
    graph_path = _bound_path(root, pin.graph_path)
    receipt_path = _bound_path(root, pin.receipt_path)
    parent_receipt_path = _bound_path(root, pin.parent_receipt_path)
    closure_path = _bound_path(root, pin.closure_path)
    artifact_manifest_path = _bound_path(root, pin.artifact_manifest_path)
    _require_file_hash(graph_path, pin.graph_file_sha256, "evidence graph")
    _require_file_hash(receipt_path, pin.receipt_file_sha256, "evidence receipt")
    _require_file_hash(
        parent_receipt_path,
        pin.parent_receipt_file_sha256,
        "parent evidence receipt",
    )
    _require_file_hash(closure_path, pin.closure_file_sha256, "closure report")
    _require_file_hash(
        artifact_manifest_path,
        pin.artifact_manifest_file_sha256,
        "artifact manifest",
    )

    graph = load_exact_evidence_graph(graph_path, expected_graph_ref=pin.graph_ref)
    receipt = load_exact_evidence_receipt(
        receipt_path, expected_receipt_id=pin.receipt_id
    )
    parent_receipt = load_exact_evidence_receipt(
        parent_receipt_path, expected_receipt_id=pin.parent_receipt_id
    )
    if receipt.body.graph_ref != graph.graph_ref:
        raise EvidenceGraphError("exact receipt does not bind the exact graph root")
    if receipt.body.authority_registry_ref != pin.authority_registry_ref:
        raise EvidenceGraphError("receipt authority registry ref is not the pinned ref")
    if parent_receipt.body.authority_registry_ref != pin.authority_registry_ref:
        raise EvidenceGraphError("parent receipt authority registry ref is not pinned")
    if parent_receipt.body.graph_ref != graph.graph_ref:
        raise EvidenceGraphError("parent receipt does not bind the exact graph")
    dependencies = tuple(receipt.body.dependencies)
    if (
        len(dependencies) != 1
        or dependencies[0].kind is not ReceiptDependencyKind.PARENT
        or dependencies[0].receipt_ref != parent_receipt.receipt_id
    ):
        raise EvidenceGraphError("release receipt lacks its exact parent receipt edge")
    if parent_receipt.body.dependencies:
        raise EvidenceGraphError("PR-122 mechanics parent must be lineage root")
    closure = graph.closure(receipt.body.claim_ref)
    expected_receipt_axes = (
        receipt.body.closure_ref,
        receipt.body.node_refs,
        receipt.body.edge_refs,
        receipt.body.process_result,
        receipt.body.evidence_status,
        receipt.body.evidence_statuses,
        receipt.body.scientific_status,
    )
    recomputed_axes = (
        closure.closure_ref,
        closure.node_refs,
        closure.edge_refs,
        closure.process_result,
        closure.evidence_status,
        closure.evidence_statuses,
        closure.scientific_status,
    )
    if expected_receipt_axes != recomputed_axes:
        raise EvidenceGraphError("receipt axes do not match recomputed closure")
    parent_closure = graph.closure(parent_receipt.body.claim_ref)
    parent_axes = (
        parent_receipt.body.closure_ref,
        parent_receipt.body.node_refs,
        parent_receipt.body.edge_refs,
        parent_receipt.body.process_result,
        parent_receipt.body.evidence_status,
        parent_receipt.body.evidence_statuses,
        parent_receipt.body.scientific_status,
    )
    recomputed_parent_axes = (
        parent_closure.closure_ref,
        parent_closure.node_refs,
        parent_closure.edge_refs,
        parent_closure.process_result,
        parent_closure.evidence_status,
        parent_closure.evidence_statuses,
        parent_closure.scientific_status,
    )
    if parent_axes != recomputed_parent_axes or not parent_closure.mechanics_closed:
        raise EvidenceGraphError("parent receipt does not bind closed mechanics")
    _verify_graph_sources(root, graph)
    _verify_mes_inventory(root, graph)
    manifest = _verify_artifact_manifest(root, artifact_manifest_path)
    required_manifest_paths = {
        pin.graph_path,
        pin.receipt_path,
        pin.parent_receipt_path,
        pin.closure_path,
        "docs/generated/pr122_claim_closure_report.md",
        "docs/generated/pr122_mes_successor_scan.json",
        "docs/generated/pr122_test_execution.json",
    }
    manifest_paths = {
        str(row["path"]) for row in manifest["artifacts"] if isinstance(row, Mapping)
    }
    if not required_manifest_paths <= manifest_paths:
        raise EvidenceGraphError("artifact manifest does not cover every PR-122 output")

    report = _load_closure(closure_path)
    if (
        report.get("graph_ref") != graph.graph_ref
        or report.get("release_receipt_id") != receipt.receipt_id
        or report.get("parent_receipt_id") != parent_receipt.receipt_id
        or report.get("authority_registry_ref") != pin.authority_registry_ref
    ):
        raise EvidenceGraphError(
            "closure report does not bind exact graph/receipt/authority"
        )
    if report.get("claim_release_allowed") is not False:
        raise EvidenceGraphError(
            "checked-in PR-122 closure must remain claim-release blocked"
        )
    if report.get("audit_disclosure_allowed") is not True:
        raise EvidenceGraphError(
            "checked-in PR-122 closure must allow only audit disclosure"
        )

    integrity_failures = {
        EvidenceStatus.INVALID,
        EvidenceStatus.STALE,
        EvidenceStatus.MISSING,
    }
    if set(closure.evidence_statuses) & integrity_failures:
        raise EvidenceGraphError(
            "blocked policy cannot conceal invalid, stale, or missing evidence"
        )

    if mode == "claim_release":
        # The checked-in envelope has no trusted external verifier.  Even if a
        # caller edits a boolean, exact hashes and the derived closure prevent
        # it from becoming a claim-release receipt.
        closure.require_claim_release_eligible()
        raise EvidenceGraphError(
            "claim release requires trusted authority validation, not audit disclosure"
        )
    if receipt.body.process_result is not ProcessResult.PASS:
        raise EvidenceGraphError("audit disclosure receipt process did not pass")
    # PR-124: the mechanics evidence is PRESENT (governance authority
    # delivered) while claim release stays ineligible; disclosure must
    # expose exactly the current derived state — never a claim release.
    if receipt.body.evidence_status is not closure.evidence_status:
        raise EvidenceGraphError(
            "audit disclosure must expose the current derived evidence state"
        )
    if closure.claim_release_eligible:
        raise EvidenceGraphError(
            "audit disclosure cannot proceed once a claim appears "
            "release-eligible without trusted authority validation"
        )

    disclosure = receipt.audit_disclosure()
    return {
        "mode": mode,
        "graph_path": pin.graph_path,
        "graph_file_sha256": pin.graph_file_sha256,
        "graph_ref": graph.graph_ref,
        "receipt_path": pin.receipt_path,
        "receipt_file_sha256": pin.receipt_file_sha256,
        "receipt_id": receipt.receipt_id,
        "receipt_version": disclosure["schema_version"],
        "parent_receipt_path": pin.parent_receipt_path,
        "parent_receipt_file_sha256": pin.parent_receipt_file_sha256,
        "parent_receipt_id": parent_receipt.receipt_id,
        "closure_path": pin.closure_path,
        "closure_file_sha256": pin.closure_file_sha256,
        "closure_ref": closure.closure_ref,
        "artifact_manifest_path": pin.artifact_manifest_path,
        "artifact_manifest_file_sha256": pin.artifact_manifest_file_sha256,
        "authority_registry_ref": pin.authority_registry_ref,
        "process_result": receipt.body.process_result.value,
        "evidence_status": receipt.body.evidence_status.value,
        "evidence_statuses": [
            status.value for status in receipt.body.evidence_statuses
        ],
        "scientific_status": receipt.body.scientific_status.value,
        "authority_status": disclosure["authority_status"],
        "claim_release_allowed": False,
        "audit_disclosure_allowed": True,
    }


__all__ = [
    "DEFAULT_RELEASE_EVIDENCE_PIN",
    "ReleaseEvidencePin",
    "consume_release_evidence",
]
