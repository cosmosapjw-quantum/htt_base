#!/usr/bin/env python3
"""Fail-closed semantic receipt helpers for the PR-167 intake transaction."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


RECEIPT_SCHEMA = "htt.pr167.pre_intake_semantic_receipt.v1"
CANONICALIZATION = "utf8_json_sort_keys_compact_separators"
PERMITTED_MIGRATIONS = {
    "PR-151": {
        "from": "in_progress",
        "to": "background_in_progress",
        "reason": "authenticated_long_running_acquisition_separated_from_foreground_PR",
    }
}
STATUS_LIST_FIELDS = (
    "completed",
    "blocked",
    "skipped",
    "pending",
    "dormant_external",
    "background_in_progress",
)


def canonical_json_bytes(value: Any) -> bytes:
    """Return the one canonical byte representation used by the receipt."""

    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _string_list(status: Mapping[str, Any], field: str) -> list[str]:
    raw = status.get(field, []) or []
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError(f"status {field} must be a list of PR ids")
    if len(raw) != len(set(raw)):
        raise ValueError(f"status {field} contains duplicate PR ids")
    return raw


def status_projection(
    status: Mapping[str, Any], card_ids: Sequence[str]
) -> dict[str, str]:
    """Project orchestration state for an exact card set, rejecting overlap."""

    memberships: dict[str, list[str]] = {}
    for field in STATUS_LIST_FIELDS:
        for pr_id in _string_list(status, field):
            memberships.setdefault(pr_id, []).append(field)
    foreground = status.get("in_progress")
    if foreground is not None:
        if not isinstance(foreground, str) or not foreground:
            raise ValueError("status in_progress must be a PR id or null")
        memberships.setdefault(foreground, []).append("in_progress")

    overlap = {
        pr_id: values for pr_id, values in memberships.items() if len(values) != 1
    }
    if overlap:
        raise ValueError(f"status orchestration states overlap: {overlap}")
    expected = set(card_ids)
    unknown = sorted(set(memberships) - expected)
    if unknown:
        raise ValueError(f"status contains unknown PR ids: {unknown}")
    missing = sorted(expected - set(memberships))
    if missing:
        raise ValueError(f"status orchestration coverage missing PR ids: {missing}")
    return {pr_id: memberships[pr_id][0] for pr_id in card_ids}


def _cards(backlog: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = backlog.get("prs")
    if not isinstance(raw, list) or not all(isinstance(card, dict) for card in raw):
        raise ValueError("backlog prs must be a list of mappings")
    ids = [card.get("id") for card in raw]
    if not all(isinstance(pr_id, str) and pr_id for pr_id in ids):
        raise ValueError("every backlog card must have a non-empty string id")
    if len(ids) != len(set(ids)):
        raise ValueError("backlog card ids must be unique")
    return raw


def _receipt_digest(receipt: Mapping[str, Any]) -> str:
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    return semantic_sha256(unsigned)


def create_pre_intake_receipt(
    *,
    backlog: Mapping[str, Any],
    status: Mapping[str, Any],
    baseline_commit: str,
    backlog_sha256: str,
    status_sha256: str,
    roadmap_sha256: str,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    cards = _cards(backlog)
    card_ids = [str(card["id"]) for card in cards]
    if len(cards) != 113:
        raise ValueError(f"pre-intake receipt requires exactly 113 cards, found {len(cards)}")
    if any(167 <= int(pr_id[-3:]) <= 183 for pr_id in card_ids):
        raise ValueError("pre-intake receipt cannot include PR-167..PR-183")
    projection = status_projection(status, card_ids)
    receipt: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "generated_at_utc": generated_at_utc
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "artifact_mode": "governance_transaction_receipt",
        "allowed_use": "PR-167 intake preservation audit only",
        "public_use": False,
        "scientific_effect": "none",
        "transfer_source": "none",
        "sky_support_mask_status": "not_applicable_governance",
        "covariance_null_mock_status": "not_applicable_governance",
        "baseline_commit": baseline_commit,
        "roadmap_sha256": roadmap_sha256,
        "pre_intake_backlog_sha256": backlog_sha256,
        "pre_intake_status_sha256": status_sha256,
        "canonicalization": CANONICALIZATION,
        "hash_algorithm": "sha256",
        "preserved_card_count": len(cards),
        "preserved_card_ids": card_ids,
        "card_semantic_sha256": {
            str(card["id"]): semantic_sha256(card) for card in cards
        },
        "pre_intake_status_projection": projection,
        "permitted_status_migrations": PERMITTED_MIGRATIONS,
        "caveats": [
            "The receipt proves DAG-card and orchestration preservation only.",
            "It is not scientific validation, native-transfer validation, or family-identification evidence.",
        ],
        "generating_command": (
            "python scripts/codex_harness/intake_advocate_track.py --write"
        ),
        "git_commit_or_worktree_state": f"{baseline_commit}; PR-167 worktree",
    }
    receipt["config_hash"] = semantic_sha256(
        {
            "schema": RECEIPT_SCHEMA,
            "canonicalization": CANONICALIZATION,
            "permitted_status_migrations": PERMITTED_MIGRATIONS,
            "roadmap_sha256": roadmap_sha256,
        }
    )
    receipt["input_hashes"] = [
        f"docs/codex_handoff/pr_backlog.yaml:{backlog_sha256}",
        f"docs/codex_handoff/pr_status.yaml:{status_sha256}",
        f"docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md:{roadmap_sha256}",
    ]
    receipt["receipt_sha256"] = _receipt_digest(receipt)
    return receipt


def validate_pre_intake_receipt(
    receipt: Mapping[str, Any],
    *,
    backlog: Mapping[str, Any],
    status: Mapping[str, Any] | None = None,
    expected_baseline_commit: str | None = None,
    expected_backlog_sha256: str | None = None,
    expected_status_sha256: str | None = None,
    expected_roadmap_sha256: str | None = None,
) -> None:
    """Verify the stored receipt against the preserved prefix and current status."""

    if receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("PR-167 semantic receipt schema mismatch")
    if receipt.get("canonicalization") != CANONICALIZATION:
        raise ValueError("PR-167 semantic receipt canonicalization mismatch")
    fixed_metadata = {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "artifact_mode": "governance_transaction_receipt",
        "allowed_use": "PR-167 intake preservation audit only",
        "public_use": False,
        "scientific_effect": "none",
        "transfer_source": "none",
        "sky_support_mask_status": "not_applicable_governance",
        "covariance_null_mock_status": "not_applicable_governance",
        "hash_algorithm": "sha256",
        "generating_command": "python scripts/codex_harness/intake_advocate_track.py --write",
    }
    for field, expected in fixed_metadata.items():
        if receipt.get(field) != expected:
            raise ValueError(f"PR-167 semantic receipt fixed metadata drift: {field}")
    if receipt.get("permitted_status_migrations") != PERMITTED_MIGRATIONS:
        raise ValueError("PR-167 semantic receipt migration contract mismatch")
    if receipt.get("sky_support_mask_status") != "not_applicable_governance":
        raise ValueError("PR-167 semantic receipt sky-support metadata mismatch")
    if receipt.get("covariance_null_mock_status") != "not_applicable_governance":
        raise ValueError("PR-167 semantic receipt covariance/null metadata mismatch")
    if receipt.get("receipt_sha256") != _receipt_digest(receipt):
        raise ValueError("PR-167 semantic receipt self-hash mismatch")
    if expected_baseline_commit and receipt.get("baseline_commit") != expected_baseline_commit:
        raise ValueError("PR-167 semantic receipt baseline commit mismatch")
    if expected_backlog_sha256 and receipt.get("pre_intake_backlog_sha256") != expected_backlog_sha256:
        raise ValueError("PR-167 semantic receipt pre-intake backlog hash mismatch")
    if expected_status_sha256 and receipt.get("pre_intake_status_sha256") != expected_status_sha256:
        raise ValueError("PR-167 semantic receipt pre-intake status hash mismatch")
    if expected_roadmap_sha256 and receipt.get("roadmap_sha256") != expected_roadmap_sha256:
        raise ValueError("PR-167 semantic receipt roadmap hash mismatch")

    expected_config_hash = semantic_sha256(
        {
            "schema": RECEIPT_SCHEMA,
            "canonicalization": CANONICALIZATION,
            "permitted_status_migrations": PERMITTED_MIGRATIONS,
            "roadmap_sha256": receipt.get("roadmap_sha256"),
        }
    )
    if receipt.get("config_hash") != expected_config_hash:
        raise ValueError("PR-167 semantic receipt config hash mismatch")
    expected_inputs = [
        "docs/codex_handoff/pr_backlog.yaml:"
        f"{receipt.get('pre_intake_backlog_sha256')}",
        "docs/codex_handoff/pr_status.yaml:"
        f"{receipt.get('pre_intake_status_sha256')}",
        "docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md:"
        f"{receipt.get('roadmap_sha256')}",
    ]
    if receipt.get("input_hashes") != expected_inputs:
        raise ValueError("PR-167 semantic receipt input hash list mismatch")

    preserved_ids = receipt.get("preserved_card_ids")
    hashes = receipt.get("card_semantic_sha256")
    pre_projection = receipt.get("pre_intake_status_projection")
    if (
        not isinstance(preserved_ids, list)
        or not all(isinstance(pr_id, str) for pr_id in preserved_ids)
        or not isinstance(hashes, dict)
        or not isinstance(pre_projection, dict)
    ):
        raise ValueError("PR-167 semantic receipt preservation fields are malformed")
    if receipt.get("preserved_card_count") != len(preserved_ids) or len(preserved_ids) != 113:
        raise ValueError("PR-167 semantic receipt must preserve exactly 113 cards")
    if len(set(preserved_ids)) != len(preserved_ids):
        raise ValueError("PR-167 semantic receipt preserved card ids must be unique")
    if set(hashes) != set(preserved_ids) or set(pre_projection) != set(preserved_ids):
        raise ValueError("PR-167 semantic receipt card/status coverage mismatch")

    ordered_current_cards = _cards(backlog)
    current_ids = [str(card["id"]) for card in ordered_current_cards]
    if current_ids[: len(preserved_ids)] != preserved_ids:
        raise ValueError(
            "PR-167 semantic receipt must match the exact ordered pre-intake prefix"
        )
    current_cards = {str(card["id"]): card for card in ordered_current_cards}
    missing = [pr_id for pr_id in preserved_ids if pr_id not in current_cards]
    if missing:
        raise ValueError(f"PR-167 preserved cards missing after intake: {missing}")
    changed = [
        pr_id
        for pr_id in preserved_ids
        if semantic_sha256(current_cards[pr_id]) != hashes.get(pr_id)
    ]
    if changed:
        raise ValueError(f"PR-167 preserved card semantic hash drift: {changed}")

    if status is None:
        return
    current_projection = status_projection(status, list(current_cards))
    for pr_id in preserved_ids:
        expected = pre_projection[pr_id]
        migration = PERMITTED_MIGRATIONS.get(pr_id)
        if migration:
            if expected != migration["from"]:
                raise ValueError(f"PR-167 receipt has invalid pre-intake state for {pr_id}")
            if current_projection[pr_id] != migration["to"]:
                raise ValueError(f"PR-167 required status migration missing for {pr_id}")
        elif current_projection[pr_id] != expected:
            raise ValueError(
                f"PR-167 preserved status drift for {pr_id}: "
                f"{expected!r}->{current_projection[pr_id]!r}"
            )
