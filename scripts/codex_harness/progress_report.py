#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

if __package__:
    from .validate_pr_dag import DagInfo, load_yaml, validate_backlog
else:
    from validate_pr_dag import DagInfo, load_yaml, validate_backlog

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HTT_SRC = _REPO_ROOT / "htt" / "src"
if str(_HTT_SRC) not in sys.path:
    sys.path.insert(0, str(_HTT_SRC))

from common.remediation_state import (  # noqa: E402
    AdjudicatedClaim,
    AdjudicationReceipt,
    AuthorityRegistry,
    DependencyEvidence,
    DependencyMode,
    ExternalDeliveryReceipt,
    resolve_dependency,
)


_RESCUE_FIRST_PR = 119
_TERMINAL_EXECUTION_RESOLUTIONS = frozenset(
    {
        "COMPLETED_SUCCESS",
        "COMPLETED_FAILED_WITH_RECEIPT",
        "BLOCKED_WITH_RECEIPT",
        "ABANDONED_WITH_RECEIPT",
    }
)
_BACKGROUND_ACQUISITION_ALLOWLIST = frozenset({"PR-151"})
_DEPENDENCY_MODES = frozenset(
    {
        "requires_success",
        "requires_terminal_receipt",
        "requires_authenticated_external_receipt",
        "requires_adjudicated_claim_set",
    }
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")


@dataclass(frozen=True)
class ReceiptVerificationContext:
    """Trusted inputs for resolving receipt-gated DAG edges.

    The command-line interface deliberately constructs no instance of this
    class: a YAML authority registry cannot supply the trusted verifier
    callbacks required by :class:`AuthorityRegistry`.  Callers that own a
    trust root may inject a registry, a receipt filesystem root, and a bounded
    evaluation time through this API.  Without that injection, adjudication
    and authenticated-external edges remain unsatisfied.
    """

    registry: AuthorityRegistry
    receipt_root: Path
    at: datetime | date | str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.registry, AuthorityRegistry):
            raise TypeError("registry must be an AuthorityRegistry")
        root = Path(self.receipt_root).resolve()
        if not root.is_dir():
            raise ValueError(f"receipt_root is not a directory: {root}")
        object.__setattr__(self, "receipt_root", root)


def _pr_number(pr_id: str) -> int | None:
    match = re.fullmatch(r"PR-(\d+)", pr_id)
    return int(match.group(1)) if match else None


def _is_rescue_pr(pr_id: str) -> bool:
    number = _pr_number(pr_id)
    return number is not None and number >= _RESCUE_FIRST_PR


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_receipt_reference(value: object) -> bool:
    """Accept the canonical non-empty process-receipt path/identifier string."""

    return _nonempty_string(value)


def _load_hash_bound_json_receipt(
    value: object,
    context: ReceiptVerificationContext | None,
) -> dict[str, Any] | None:
    """Load a repository-local JSON receipt through a path+SHA-256 pointer.

    A status-file envelope is never itself authority.  Receipt bytes must
    exist beneath the caller-selected root, match the supplied digest, parse
    as one mapping, and subsequently pass typed authority/attestation checks.
    """

    if context is None or not isinstance(value, dict):
        return None
    if set(value) != {"path", "sha256"}:
        return None
    relative_path = value.get("path")
    expected_digest = value.get("sha256")
    if not _nonempty_string(relative_path):
        return None
    if not isinstance(expected_digest, str) or not _SHA256_RE.fullmatch(
        expected_digest
    ):
        return None
    candidate = Path(relative_path)
    if candidate.is_absolute():
        return None
    try:
        resolved = (context.receipt_root / candidate).resolve(strict=True)
        resolved.relative_to(context.receipt_root)
    except (OSError, ValueError):
        return None
    if not resolved.is_file() or resolved.is_symlink():
        return None
    try:
        payload_bytes = resolved.read_bytes()
    except OSError:
        return None
    if hashlib.sha256(payload_bytes).hexdigest() != expected_digest:
        return None
    try:
        payload = json.loads(payload_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _adjudication_receipt_from_record(
    value: dict[str, Any],
) -> AdjudicationReceipt:
    required = {
        "receipt_id",
        "author",
        "author_identity_fingerprint",
        "adjudicator",
        "adjudicator_identity_fingerprint",
        "scope",
        "accepted_claims",
        "issued_at",
        "attestation",
    }
    if set(value) != required or not isinstance(value["accepted_claims"], list):
        raise ValueError("invalid adjudication receipt fields")
    accepted_claims = tuple(
        AdjudicatedClaim(
            claim_id=claim["claim_id"],
            identity_fingerprint=claim["identity_fingerprint"],
            scientific_status=claim["scientific_status"],
        )
        for claim in value["accepted_claims"]
        if isinstance(claim, dict)
        and set(claim)
        == {"claim_id", "identity_fingerprint", "scientific_status"}
    )
    if len(accepted_claims) != len(value["accepted_claims"]):
        raise ValueError("invalid adjudicated claim fields")
    return AdjudicationReceipt(
        receipt_id=value["receipt_id"],
        author=value["author"],
        author_identity_fingerprint=value["author_identity_fingerprint"],
        adjudicator=value["adjudicator"],
        adjudicator_identity_fingerprint=value[
            "adjudicator_identity_fingerprint"
        ],
        scope=value["scope"],
        accepted_claims=accepted_claims,
        issued_at=value["issued_at"],
        attestation=value["attestation"],
    )


def _external_receipt_from_record(
    value: dict[str, Any],
) -> ExternalDeliveryReceipt:
    required = {
        "receipt_id",
        "provider",
        "provider_identity_fingerprint",
        "scope",
        "artifact_fingerprint",
        "issued_at",
        "attestation",
    }
    if set(value) != required:
        raise ValueError("invalid external delivery receipt fields")
    return ExternalDeliveryReceipt(
        receipt_id=value["receipt_id"],
        provider=value["provider"],
        provider_identity_fingerprint=value["provider_identity_fingerprint"],
        scope=value["scope"],
        artifact_fingerprint=value["artifact_fingerprint"],
        issued_at=value["issued_at"],
        attestation=value["attestation"],
    )


def _verified_adjudication_record(
    value: object,
    *,
    expected_scope: str,
    context: ReceiptVerificationContext | None,
) -> bool:
    if not isinstance(value, dict):
        return False
    payload = _load_hash_bound_json_receipt(value.get("receipt"), context)
    if payload is None or context is None:
        return False
    try:
        receipt = _adjudication_receipt_from_record(payload)
        decision = resolve_dependency(
            DependencyMode.REQUIRES_ADJUDICATED_CLAIM_SET,
            DependencyEvidence(adjudication_receipt=receipt),
            registry=context.registry,
            scope=expected_scope,
            at=context.at,
        )
    except Exception:
        return False
    return (
        decision.satisfied
        and decision.scientific_input_allowed
        and bool(decision.accepted_claims)
    )


def _verified_external_event(
    event_id: str,
    value: object,
    *,
    expected_scope: str,
    context: ReceiptVerificationContext | None,
) -> bool:
    if not _nonempty_string(event_id) or not isinstance(value, dict):
        return False
    payload = _load_hash_bound_json_receipt(value.get("receipt"), context)
    if payload is None or context is None:
        return False
    try:
        receipt = _external_receipt_from_record(payload)
        decision = resolve_dependency(
            DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT,
            DependencyEvidence(external_receipt=receipt),
            registry=context.registry,
            scope=expected_scope,
            at=context.at,
        )
    except Exception:
        return False
    return decision.satisfied


def _execution_record(status: dict[str, Any], pr_id: str) -> dict[str, Any] | None:
    resolutions = status.get("execution_resolutions", {}) or {}
    record = resolutions.get(pr_id)
    return record if isinstance(record, dict) else None


def _dependency_contracts(info: DagInfo, pr_id: str) -> tuple[dict[str, str], ...]:
    card = next(card for card in info.prs if card["id"] == pr_id)
    raw = card.get("dependency_contracts")
    if raw is None:
        return tuple(
            {"upstream_id": dependency, "mode": "requires_success"}
            for dependency in info.prereqs[pr_id]
        )
    if not isinstance(raw, list) or not all(isinstance(item, dict) for item in raw):
        raise ValueError(f"{pr_id} dependency_contracts must be a list of mappings")
    contracts: list[dict[str, str]] = []
    for contract in raw:
        upstream = contract.get("upstream_id")
        mode = contract.get("mode")
        if not isinstance(upstream, str) or mode not in _DEPENDENCY_MODES:
            raise ValueError(f"{pr_id} has invalid typed dependency contract: {contract}")
        contracts.append({"upstream_id": upstream, "mode": str(mode)})
    if [contract["upstream_id"] for contract in contracts] != list(
        info.prereqs[pr_id]
    ):
        raise ValueError(
            f"{pr_id} typed dependency projection must exactly match depends"
        )
    return tuple(contracts)


def _edge_satisfied(
    *,
    mode: str,
    upstream_id: str,
    completed: set[str],
    status: dict[str, Any],
    verification_context: ReceiptVerificationContext | None = None,
) -> bool:
    record = _execution_record(status, upstream_id)
    resolution = record.get("resolution") if record else None
    has_receipt = bool(record) and _valid_receipt_reference(record.get("receipt"))

    if mode == "requires_success":
        if resolution is not None:
            return resolution == "COMPLETED_SUCCESS" and has_receipt
        # The frozen pre-PR-119 DAG predates execution-resolution receipts.
        return upstream_id in completed and not _is_rescue_pr(upstream_id)
    if mode == "requires_terminal_receipt":
        return resolution in _TERMINAL_EXECUTION_RESOLUTIONS and has_receipt
    if mode == "requires_adjudicated_claim_set":
        return (
            resolution == "COMPLETED_SUCCESS"
            and has_receipt
            and _verified_adjudication_record(
                record.get("adjudication"),
                expected_scope=upstream_id,
                context=verification_context,
            )
        )
    # External events are not PR execution records and are handled separately.
    return False


def _card_dependencies_satisfied(
    info: DagInfo,
    pr_id: str,
    completed: set[str],
    status: dict[str, Any],
    verification_context: ReceiptVerificationContext | None = None,
) -> bool:
    if not all(
        _edge_satisfied(
            mode=contract["mode"],
            upstream_id=contract["upstream_id"],
            completed=completed,
            status=status,
            verification_context=verification_context,
        )
        for contract in _dependency_contracts(info, pr_id)
    ):
        return False

    return _external_dependencies_satisfied(
        info,
        pr_id,
        status,
        verification_context=verification_context,
    )


def _external_dependencies_satisfied(
    info: DagInfo,
    pr_id: str,
    status: dict[str, Any],
    verification_context: ReceiptVerificationContext | None = None,
) -> bool:
    card = next(card for card in info.prs if card["id"] == pr_id)
    external = card.get("external_dependency_contracts", []) or []
    if not isinstance(external, list) or not all(
        isinstance(item, dict) for item in external
    ):
        raise ValueError(
            f"{pr_id} external_dependency_contracts must be a list of mappings"
        )
    events = status.get("external_events", {}) or {}
    for contract in external:
        event_id = contract.get("upstream_id")
        expected_scope = contract.get("scope")
        if (
            set(contract) != {"upstream_id", "mode", "scope"}
            or not isinstance(event_id, str)
            or not _nonempty_string(expected_scope)
            or contract.get("mode") != "requires_authenticated_external_receipt"
            or not _verified_external_event(
                event_id,
                events.get(event_id),
                expected_scope=str(expected_scope),
                context=verification_context,
            )
        ):
            return False
    return True


def _as_id_list(status: dict[str, Any], key: str) -> list[str]:
    value = status.get(key, []) or []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"status {key} must be a list of PR ids")
    duplicate = sorted({item for item in value if value.count(item) > 1})
    if duplicate:
        raise ValueError(f"duplicate {key} PR ids: {duplicate}")
    return value


def load_status(path: str | Path) -> dict[str, Any]:
    status_path = Path(path)
    if not status_path.exists():
        return {}
    status = yaml.safe_load(status_path.read_text(encoding="utf-8")) or {}
    if not isinstance(status, dict):
        raise ValueError("status YAML must contain a mapping")
    return status


def validate_status(
    status: dict[str, Any],
    info: DagInfo,
    *,
    verification_context: ReceiptVerificationContext | None = None,
) -> tuple[set[str], set[str], set[str]]:
    completed_list = _as_id_list(status, "completed")
    blocked_list = _as_id_list(status, "blocked")
    skipped_list = _as_id_list(status, "skipped")
    pending_list = _as_id_list(status, "pending")
    dormant_list = _as_id_list(status, "dormant_external")
    background_list = _as_id_list(status, "background_in_progress")
    idset = set(info.ids)

    unknown_completed = sorted(set(completed_list) - idset)
    if unknown_completed:
        raise ValueError(f"unknown completed PR ids: {unknown_completed}")

    unknown_blocked = sorted(set(blocked_list) - idset)
    if unknown_blocked:
        raise ValueError(f"unknown blocked PR ids: {unknown_blocked}")

    unknown_skipped = sorted(set(skipped_list) - idset)
    if unknown_skipped:
        raise ValueError(f"unknown skipped PR ids: {unknown_skipped}")

    unknown_pending = sorted(set(pending_list) - idset)
    if unknown_pending:
        raise ValueError(f"unknown pending PR ids: {unknown_pending}")

    unknown_dormant = sorted(set(dormant_list) - idset)
    if unknown_dormant:
        raise ValueError(f"unknown dormant_external PR ids: {unknown_dormant}")

    unknown_background = sorted(set(background_list) - idset)
    if unknown_background:
        raise ValueError(
            f"unknown background_in_progress PR ids: {unknown_background}"
        )

    completed = set(completed_list)
    blocked = set(blocked_list)
    skipped = set(skipped_list)
    pending = set(pending_list)
    dormant = set(dormant_list)
    background = set(background_list)
    overlap = sorted(completed & blocked)
    if overlap:
        raise ValueError(f"PR ids cannot be both completed and blocked: {overlap}")
    completed_skipped = sorted(completed & skipped)
    if completed_skipped:
        raise ValueError(
            f"PR ids cannot be both completed and skipped: {completed_skipped}"
        )
    blocked_skipped = sorted(blocked & skipped)
    if blocked_skipped:
        raise ValueError(f"PR ids cannot be both blocked and skipped: {blocked_skipped}")

    in_progress = status.get("in_progress")
    if in_progress is not None:
        if not isinstance(in_progress, str):
            raise ValueError("status in_progress must be a PR id or null")
        if in_progress not in idset:
            raise ValueError(f"unknown in_progress PR id: {in_progress}")
        if in_progress in completed or in_progress in blocked or in_progress in skipped:
            raise ValueError(
                "in_progress PR id cannot be completed, blocked, or skipped: "
                f"{in_progress}"
            )

    state_sets = {
        "completed": completed,
        "blocked": blocked,
        "skipped": skipped,
        "pending": pending,
        "dormant_external": dormant,
        "background_in_progress": background,
    }
    membership: dict[str, list[str]] = {}
    for state_name, values in state_sets.items():
        for pr_id in values:
            membership.setdefault(pr_id, []).append(state_name)
    if in_progress is not None:
        membership.setdefault(in_progress, []).append("in_progress")
    overlaps = {
        pr_id: names for pr_id, names in membership.items() if len(names) > 1
    }
    if overlaps:
        raise ValueError(f"status orchestration states overlap: {overlaps}")

    managed_ids = {pr_id for pr_id in info.ids if _is_rescue_pr(pr_id)}
    missing_managed = sorted(managed_ids - set(membership))
    if missing_managed:
        raise ValueError(
            f"status orchestration coverage missing PR-119+ ids: {missing_managed}"
        )

    cards = {card["id"]: card for card in info.prs}
    dormant_expected = {
        pr_id
        for pr_id, card in cards.items()
        if card.get("activation_state") in {"DORMANT_EXTERNAL", "NEEDS_NATIVE"}
    }
    if dormant != dormant_expected:
        raise ValueError(
            "dormant_external must follow typed activation_state: "
            f"missing={sorted(dormant_expected - dormant)}, "
            f"unexpected={sorted(dormant - dormant_expected)}"
        )

    lanes = status.get("execution_lane", {}) or {}
    if not isinstance(lanes, dict) or not all(
        isinstance(pr_id, str) and lane in {
            "defensible",
            "hypothesis_only",
            "needs_native",
        }
        for pr_id, lane in lanes.items()
    ):
        raise ValueError("status execution_lane must contain only typed lane values")
    card_lanes = {
        pr_id: card["execution_lane"]
        for pr_id, card in cards.items()
        if "execution_lane" in card
    }
    if lanes != card_lanes:
        raise ValueError("status execution_lane must exactly match advocate card lanes")

    resolutions = status.get("execution_resolutions", {}) or {}
    if not isinstance(resolutions, dict):
        raise ValueError("status execution_resolutions must be a mapping")
    unknown_resolutions = sorted(set(resolutions) - idset)
    if unknown_resolutions:
        raise ValueError(
            f"execution_resolutions contain unknown PR ids: {unknown_resolutions}"
        )
    terminal = completed | blocked | skipped
    for pr_id, record in resolutions.items():
        if pr_id not in terminal:
            raise ValueError(f"non-terminal PR has execution resolution: {pr_id}")
        if not isinstance(record, dict):
            raise ValueError(f"execution resolution for {pr_id} must be a mapping")
        resolution = record.get("resolution")
        if resolution not in _TERMINAL_EXECUTION_RESOLUTIONS:
            raise ValueError(f"invalid execution resolution for {pr_id}: {resolution!r}")
        if not _valid_receipt_reference(record.get("receipt")):
            raise ValueError(f"execution resolution for {pr_id} lacks a valid receipt")
        if pr_id in completed and resolution != "COMPLETED_SUCCESS":
            raise ValueError(
                f"completed PR {pr_id} must have COMPLETED_SUCCESS resolution"
            )
        if pr_id in blocked and resolution not in {
            "COMPLETED_FAILED_WITH_RECEIPT",
            "BLOCKED_WITH_RECEIPT",
        }:
            raise ValueError(
                f"blocked PR {pr_id} must have a documented negative resolution"
            )
        if pr_id in skipped and resolution != "ABANDONED_WITH_RECEIPT":
            raise ValueError(
                f"skipped PR {pr_id} must have ABANDONED_WITH_RECEIPT resolution"
            )
    missing_resolutions = sorted(
        pr_id for pr_id in terminal & managed_ids if pr_id not in resolutions
    )
    if missing_resolutions:
        raise ValueError(
            "terminal PR-119+ cards require execution resolution receipts: "
            f"{missing_resolutions}"
        )

    external_events = status.get("external_events", {}) or {}
    if not isinstance(external_events, dict):
        raise ValueError("status external_events must be a mapping")
    if not all(isinstance(event_id, str) for event_id in external_events):
        raise ValueError("status external_events keys must be strings")

    background_contracts = status.get("background_execution_contracts", {}) or {}
    if not isinstance(background_contracts, dict):
        raise ValueError("status background_execution_contracts must be a mapping")
    if set(background_contracts) != background:
        raise ValueError(
            "background_execution_contracts must exactly cover background_in_progress"
        )
    expected_background_contract = {
        "kind": "acquisition",
        "allowed_phase": "acquire",
        "partial_scientific_use": "forbidden",
    }
    malformed_background = sorted(
        pr_id
        for pr_id, contract in background_contracts.items()
        if contract != expected_background_contract
    )
    if malformed_background:
        raise ValueError(
            "background acquisition contract is malformed: "
            f"{malformed_background}"
        )
    unauthorized_background = sorted(
        background - _BACKGROUND_ACQUISITION_ALLOWLIST
    )
    if unauthorized_background:
        raise ValueError(
            "background_in_progress lacks PR-167 acquisition authorization: "
            f"{unauthorized_background}"
        )

    active_ids = ([in_progress] if in_progress is not None else []) + sorted(background)
    unauthorized_active: list[str] = []
    for pr_id in active_ids:
        card = cards[pr_id]
        lane = card.get("execution_lane", "defensible")
        authorization = card.get("execution_authorization", "DAG_SCHEDULABLE")
        if lane != "defensible" or authorization in {
            "REGISTERED_NOT_SCHEDULED",
            "NATIVE_BLOCKED",
        }:
            unauthorized_active.append(
                f"{pr_id}(lane={lane},authorization={authorization})"
            )
    if unauthorized_active:
        raise ValueError(
            "active PRs must be defensible and execution-authorized: "
            + ", ".join(unauthorized_active)
        )
    dependency_blocked_active = [
        pr_id
        for pr_id in active_ids
        if not _card_dependencies_satisfied(
            info,
            pr_id,
            completed,
            status,
            verification_context=verification_context,
        )
    ]
    if dependency_blocked_active:
        raise ValueError(
            "active PRs have incomplete dependency contracts: "
            f"{dependency_blocked_active}"
        )

    incomplete_dependencies = [
        f"{contract['upstream_id']}->{pr_id}"
        for pr_id in info.order
        if pr_id in completed
        for contract in _dependency_contracts(info, pr_id)
        if not _edge_satisfied(
            mode=contract["mode"],
            upstream_id=contract["upstream_id"],
            completed=completed,
            status=status,
            verification_context=verification_context,
        )
    ]
    incomplete_external_dependencies = [
        pr_id
        for pr_id in info.order
        if pr_id in completed
        and not _external_dependencies_satisfied(
            info,
            pr_id,
            status,
            verification_context=verification_context,
        )
    ]
    if incomplete_dependencies or incomplete_external_dependencies:
        details = [*incomplete_dependencies]
        details.extend(f"external_event->{pr_id}" for pr_id in incomplete_external_dependencies)
        raise ValueError(
            "completed PRs have incomplete dependencies: " + ", ".join(details)
        )

    return completed, blocked, skipped


def longest_critical_path(info: DagInfo) -> list[str]:
    if not info.ids:
        return []

    rank = {pr_id: index for index, pr_id in enumerate(info.order)}
    best_path: dict[str, list[str]] = {}
    for pr_id in info.order:
        dep_paths = [best_path[dep] for dep in info.prereqs[pr_id]]
        if dep_paths:
            dep_paths.sort(key=lambda path: (-len(path), [rank[item] for item in path]))
            path = [*dep_paths[0], pr_id]
        else:
            path = [pr_id]
        best_path[pr_id] = path

    return sorted(
        best_path.values(),
        key=lambda path: (-len(path), [rank[item] for item in path]),
    )[0]


def dependency_weighted_percent(info: DagInfo, completed: set[str]) -> float:
    weights = {pr_id: 1 + len(info.children[pr_id]) for pr_id in info.ids}
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    completed_weight = sum(weight for pr_id, weight in weights.items() if pr_id in completed)
    return round(100 * completed_weight / total_weight, 2)


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def _input_hash(path: Path) -> str:
    if not path.is_file():
        return "MISSING"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_commit_or_worktree_state() -> str:
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return "git_state_unavailable"
    return f"{head}; {'dirty' if dirty.strip() else 'clean'}"


def _default_artifact_metadata() -> dict[str, Any]:
    return {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "config_hash": "unavailable",
        "input_hashes": [],
        "sky_support_mask_status": "not_applicable_governance",
        "covariance_null_mock_status": "not_applicable_governance",
        "caveats": [
            "DAG progress is orchestration metadata, not scientific evidence."
        ],
        "generating_command": "not_recorded",
        "git_commit_or_worktree_state": "not_recorded",
    }


def _artifact_metadata(
    backlog_path: str | Path,
    status_path: str | Path,
    *,
    checkpoint_every: int,
    generating_command: str,
) -> dict[str, Any]:
    inputs = [Path(backlog_path), Path(status_path)]
    input_hashes = [
        f"{_display_path(path)}:{_input_hash(path)}" for path in inputs
    ]
    config_payload = {
        "checkpoint_every": checkpoint_every,
        "input_hashes": input_hashes,
        "schema": "htt.progress_artifact_metadata.v1",
    }
    config_hash = hashlib.sha256(
        json.dumps(
            config_payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "sky_support_mask_status": "not_applicable_governance",
        "covariance_null_mock_status": "not_applicable_governance",
        "caveats": [
            "Progress percentages count DAG bookkeeping only.",
            "This artifact cannot establish scientific readiness, native transfer validation, posterior support, or family identification.",
        ],
        "generating_command": generating_command,
        "git_commit_or_worktree_state": _git_commit_or_worktree_state(),
    }


def build_report(
    info: DagInfo,
    completed: set[str],
    blocked: set[str],
    skipped: set[str],
    checkpoint_every: int,
    *,
    status: dict[str, Any] | None = None,
    verification_context: ReceiptVerificationContext | None = None,
    artifact_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if checkpoint_every <= 0:
        raise ValueError("--checkpoint-every must be positive")

    status = status or {}
    dormant = set(_as_id_list(status, "dormant_external"))
    pending = set(_as_id_list(status, "pending"))
    background = set(_as_id_list(status, "background_in_progress"))
    in_progress = status.get("in_progress")
    lanes = status.get("execution_lane", {}) or {}
    if not isinstance(lanes, dict):
        raise ValueError("status execution_lane must be a mapping")
    unblocked_candidates = [
        pr_id
        for pr_id in info.order
        if pr_id not in completed
        and pr_id not in blocked
        and pr_id not in skipped
        and pr_id not in dormant
        and pr_id not in background
        and pr_id != in_progress
        and _card_dependencies_satisfied(
            info,
            pr_id,
            completed,
            status,
            verification_context=verification_context,
        )
    ]
    unblocked = [
        pr_id
        for pr_id in unblocked_candidates
        if lanes.get(pr_id, "defensible") == "defensible"
    ]
    hypothesis_only_unblocked = [
        pr_id
        for pr_id in unblocked_candidates
        if lanes.get(pr_id) == "hypothesis_only"
    ]
    critical_path = longest_critical_path(info)
    critical_done = sum(1 for pr_id in critical_path if pr_id in completed)
    next_checkpoint = ((len(completed) // checkpoint_every) + 1) * checkpoint_every

    checkpoint_due = len(completed) > 0 and len(completed) % checkpoint_every == 0
    default_replan_reason = (
        "checkpoint due; rerun with --write-checkpoint-dir to evaluate replan state"
        if checkpoint_due
        else "checkpoint not due"
    )
    return {
        "total": len(info.ids),
        "completed": len(completed),
        "blocked": [pr_id for pr_id in info.order if pr_id in blocked],
        "skipped": [pr_id for pr_id in info.order if pr_id in skipped],
        "skipped_count": len(skipped),
        "pending": [pr_id for pr_id in info.order if pr_id in pending],
        "pending_count": len(pending),
        "dormant_external": [pr_id for pr_id in info.order if pr_id in dormant],
        "dormant_external_count": len(dormant),
        "in_progress": in_progress,
        "background_in_progress": [
            pr_id for pr_id in info.order if pr_id in background
        ],
        "background_in_progress_count": len(background),
        "execution_lane": dict(lanes),
        "execution_resolved_count": len(status.get("execution_resolutions", {}) or {}),
        "percent_complete": round(100 * len(completed) / len(info.ids), 2) if info.ids else 0.0,
        "dependency_weighted_percent_complete": dependency_weighted_percent(info, completed),
        "critical_path": critical_path,
        "critical_path_completed": critical_done,
        "critical_path_total": len(critical_path),
        "critical_path_percent_complete": round(100 * critical_done / len(critical_path), 2)
        if critical_path
        else 0.0,
        "unblocked_next": unblocked[:10],
        "hypothesis_only_unblocked": hypothesis_only_unblocked[:10],
        "current_checkpoint_at": len(completed) if checkpoint_due else None,
        "next_checkpoint_at": next_checkpoint,
        "checkpoint_due": checkpoint_due,
        "checkpoint_artifact": None,
        "previous_checkpoint_completed": None,
        "progress_delta_completed": None,
        "replan_required": False,
        "replan_reason": default_replan_reason,
        "artifact_metadata": artifact_metadata or _default_artifact_metadata(),
    }


def _checkpoint_metadata(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    first_line = path.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
    if not first_line:
        return None
    match = re.match(r"<!-- checkpoint_meta (.*?) -->", first_line[0])
    if not match:
        return None
    try:
        metadata = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if not isinstance(metadata, dict):
        return None
    return metadata


def _latest_checkpoint_metadata(checkpoint_dir: Path, current_completed: int) -> dict[str, Any] | None:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for path in checkpoint_dir.glob("checkpoint_*.md"):
        match = re.fullmatch(r"checkpoint_(\d+)\.md", path.name)
        if not match:
            continue
        checkpoint_number = int(match.group(1))
        if checkpoint_number >= current_completed:
            continue
        metadata = _checkpoint_metadata(path)
        if metadata is None:
            raise ValueError(f"malformed checkpoint metadata: {path}")
        candidates.append((checkpoint_number, metadata))
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: item[0])[-1][1]


def _checkpoint_state(report: dict[str, Any], previous: dict[str, Any] | None) -> dict[str, Any]:
    previous_completed = int(previous.get("completed", -1)) if previous else -1
    previous_percent = float(previous.get("percent_complete", -1.0)) if previous else -1.0
    progress_stalled = (
        previous is not None
        and report["completed"] <= previous_completed
        and report["percent_complete"] <= previous_percent
    )
    replan_required = progress_stalled
    replan_reason = (
        "progress did not advance since the previous checkpoint"
        if progress_stalled
        else "progress advanced; no replan required"
    )
    return {
        "previous_checkpoint_completed": previous_completed if previous else None,
        "progress_delta_completed": report["completed"] - previous_completed
        if previous
        else None,
        "replan_required": progress_stalled,
        "replan_reason": replan_reason,
    }


def _artifact_metadata_markdown(metadata: dict[str, Any]) -> list[str]:
    input_hashes = metadata.get("input_hashes", [])
    caveats = metadata.get("caveats", [])
    lines = [
        "## Artifact metadata",
        "",
        f"- Owner: `{metadata.get('owner', 'unknown')}`",
        (
            "- Implementation scope: "
            f"`{metadata.get('implementation_scope', 'unknown')}`"
        ),
        f"- Claim tier: `{metadata.get('claim_tier', 'unknown')}`",
        f"- Transfer source: `{metadata.get('transfer_source', 'unknown')}`",
        f"- Config hash: `{metadata.get('config_hash', 'unknown')}`",
        (
            "- Sky support / mask status: "
            f"`{metadata.get('sky_support_mask_status', 'unknown')}`"
        ),
        (
            "- Covariance / null mock status: "
            f"`{metadata.get('covariance_null_mock_status', 'unknown')}`"
        ),
        (
            "- Generating command: "
            f"`{metadata.get('generating_command', 'unknown')}`"
        ),
        (
            "- Git commit / worktree state: "
            f"`{metadata.get('git_commit_or_worktree_state', 'unknown')}`"
        ),
        "- Input hashes:",
    ]
    lines.extend(
        f"  - `{value}`" for value in input_hashes
    )
    if not input_hashes:
        lines.append("  - `none_recorded`")
    lines.append("- Caveats:")
    lines.extend(f"  - {value}" for value in caveats)
    if not caveats:
        lines.append("  - none recorded")
    return lines


def _checkpoint_markdown(report: dict[str, Any], state: dict[str, Any]) -> str:
    metadata = {
        "completed": report["completed"],
        "total": report["total"],
        "percent_complete": report["percent_complete"],
        "dependency_weighted_percent_complete": report["dependency_weighted_percent_complete"],
        "critical_path_percent_complete": report["critical_path_percent_complete"],
        "replan_required": state["replan_required"],
    }
    blocked = ", ".join(report["blocked"]) or "none"
    skipped = ", ".join(report["skipped"]) or "none"
    dormant = ", ".join(report["dormant_external"]) or "none"
    foreground = report.get("in_progress") or "none"
    background = ", ".join(report.get("background_in_progress", [])) or "none"
    unblocked_next = ", ".join(report["unblocked_next"]) or "none"
    hypothesis_only = ", ".join(report.get("hypothesis_only_unblocked", [])) or "none"
    critical_path = " -> ".join(report["critical_path"]) or "none"
    replan_text = "yes" if state["replan_required"] else "no"
    lines = [
        f"<!-- checkpoint_meta {json.dumps(metadata, sort_keys=True)} -->",
        f"# Progress checkpoint {report['completed']:03d}",
        "",
        *_artifact_metadata_markdown(report["artifact_metadata"]),
        "",
        f"- Completed PRs: {report['completed']}/{report['total']} = {report['percent_complete']}%",
        f"- Dependency-weighted completion: {report['dependency_weighted_percent_complete']}%",
        (
            f"- Critical path completion: {report['critical_path_completed']}/"
            f"{report['critical_path_total']} = {report['critical_path_percent_complete']}%"
        ),
        f"- Critical path: {critical_path}",
        f"- Blocked PRs: {blocked}",
        f"- Skipped PRs: {skipped}",
        f"- Dormant external PRs: {dormant}",
        f"- Foreground in progress: {foreground}",
        f"- Background in progress: {background}",
        f"- Unblocked next: {unblocked_next}",
        f"- Hypothesis-only unblocked (not auto-scheduled): {hypothesis_only}",
        f"- Replan required: {replan_text}",
        f"- Replan reason: {state['replan_reason']}",
        "",
        "Progress percentages count DAG bookkeeping only and are not scientific readiness evidence.",
        "They do not validate native solver behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null calibration, morphology compatibility, or Bianchi family identification.",
    ]
    if state["replan_required"]:
        lines.extend(
            [
                "",
                "## Adversarial replan entry",
                "",
                "- Step-back: the same completed count and percent recurred at a checkpoint.",
                "- Required action: open a small replan PR before further feature work.",
            ]
        )
    return "\n".join(lines) + "\n"


def _scoreboard_markdown(report: dict[str, Any]) -> str:
    blocked = ", ".join(report["blocked"]) or "none"
    skipped = ", ".join(report["skipped"]) or "none"
    dormant = ", ".join(report["dormant_external"]) or "none"
    foreground = report.get("in_progress") or "none"
    background = ", ".join(report.get("background_in_progress", [])) or "none"
    unblocked_next = ", ".join(report["unblocked_next"]) or "none"
    hypothesis_only = ", ".join(report.get("hypothesis_only_unblocked", [])) or "none"
    critical_path = " -> ".join(report["critical_path"]) or "none"
    if report["checkpoint_due"] and report.get("checkpoint_artifact"):
        checkpoint_due = f"yes; satisfied by {report['checkpoint_artifact']}"
    elif report["checkpoint_due"]:
        checkpoint_due = "yes; rerun with --write-checkpoint-dir to satisfy"
    else:
        checkpoint_due = "no"
    replan_required = "yes" if report["replan_required"] else "no"
    lines = [
        "# Progress scoreboard",
        "",
        *_artifact_metadata_markdown(report["artifact_metadata"]),
        "",
        f"- Completed PRs: {report['completed']}/{report['total']} = {report['percent_complete']}%",
        f"- Dependency-weighted completion: {report['dependency_weighted_percent_complete']}%",
        (
            f"- Critical path completion: {report['critical_path_completed']}/"
            f"{report['critical_path_total']} = {report['critical_path_percent_complete']}%"
        ),
        f"- Critical path: {critical_path}",
        f"- Blocked PRs: {blocked}",
        f"- Skipped PRs: {skipped}",
        f"- Dormant external PRs: {dormant}",
        f"- Foreground in progress: {foreground}",
        f"- Background in progress: {background}",
        f"- Unblocked next: {unblocked_next}",
        f"- Hypothesis-only unblocked (not auto-scheduled): {hypothesis_only}",
        f"- Checkpoint due: {checkpoint_due}",
        f"- Next checkpoint at: {report['next_checkpoint_at']}",
        f"- Replan required: {replan_required}",
        f"- Replan reason: {report['replan_reason']}",
        "",
        "Progress percentages count DAG bookkeeping only and are not scientific readiness evidence.",
        "They do not validate native solver behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null calibration, morphology compatibility, or Bianchi family identification.",
    ]
    return "\n".join(lines) + "\n"


def write_checkpoint(
    report: dict[str, Any],
    checkpoint_dir: str | Path,
    *,
    checkpoint_every: int,
) -> Path | None:
    output_dir = Path(checkpoint_dir)
    previous = _latest_checkpoint_metadata(output_dir, report["completed"])
    previous_completed = int(previous.get("completed", 0)) if previous else 0
    overdue = report["completed"] - previous_completed >= checkpoint_every
    if not report["checkpoint_due"] and not overdue:
        return None
    report["checkpoint_due"] = True
    report["current_checkpoint_at"] = report["completed"]
    output_dir.mkdir(parents=True, exist_ok=True)
    state = _checkpoint_state(report, previous)
    report.update(state)
    checkpoint_path = output_dir / f"checkpoint_{report['completed']:03d}.md"
    rendered = _checkpoint_markdown(report, state)
    if checkpoint_path.exists():
        existing = checkpoint_path.read_text(encoding="utf-8")
        if existing != rendered:
            raise ValueError(
                "refusing to overwrite differing immutable checkpoint: "
                f"{checkpoint_path}"
            )
    else:
        checkpoint_path.write_text(rendered, encoding="utf-8")
    report["checkpoint_artifact"] = str(checkpoint_path)
    return checkpoint_path


def write_scoreboard(report: dict[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_scoreboard_markdown(report), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser()
    parser.add_argument("backlog")
    parser.add_argument("status")
    parser.add_argument("--checkpoint-every", type=int, default=5)
    parser.add_argument("--write-checkpoint-dir")
    parser.add_argument("--write-scoreboard")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    try:
        info = validate_backlog(load_yaml(args.backlog))
        status = load_status(args.status)
        completed, blocked, skipped = validate_status(status, info)
        metadata = _artifact_metadata(
            args.backlog,
            args.status,
            checkpoint_every=args.checkpoint_every,
            generating_command=shlex.join(
                [
                    sys.executable,
                    _display_path(Path(__file__)),
                    *raw_argv,
                ]
            ),
        )
        report = build_report(
            info,
            completed,
            blocked,
            skipped,
            args.checkpoint_every,
            status=status,
            artifact_metadata=metadata,
        )
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    checkpoint_path = None
    if args.write_checkpoint_dir:
        try:
            checkpoint_path = write_checkpoint(
                report,
                args.write_checkpoint_dir,
                checkpoint_every=args.checkpoint_every,
            )
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.write_scoreboard:
        try:
            write_scoreboard(report, args.write_scoreboard)
        except Exception as exc:
            print(str(exc), file=sys.stderr)
            return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"Completed {report['completed']}/{report['total']} = "
            f"{report['percent_complete']}%"
        )
        print(
            "Dependency-weighted completion:",
            f"{report['dependency_weighted_percent_complete']}%",
        )
        print(
            "Critical path:",
            " -> ".join(report["critical_path"]),
            f"({report['critical_path_percent_complete']}%)",
        )
        print("Unblocked next:", ", ".join(report["unblocked_next"]) or "none")
        print(
            "Hypothesis-only unblocked:",
            ", ".join(report.get("hypothesis_only_unblocked", [])) or "none",
        )
        print("Skipped:", ", ".join(report["skipped"]) or "none")
        print("Checkpoint due:", report["checkpoint_due"])
        if checkpoint_path is not None:
            print(f"Checkpoint artifact: {checkpoint_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
