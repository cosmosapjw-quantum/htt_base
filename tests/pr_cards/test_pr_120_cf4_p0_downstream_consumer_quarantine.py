"""Focused live-tree and recovery contract for the retired CF4 report lane.

The old publication packages and figures are no longer live repository
surfaces.  Their scientific findings remain OPEN, and their recovery
authorities are the frozen hash ledger plus the historical Git tree where the
payload was tracked.  This test intentionally does not require an ignored
``legacy/`` backup to be mounted in every worktree.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from common.cf4_p0_quarantine import (
    canonical_artifact_bytes,
    load_block_record,
    load_policy,
    quarantine_block_payload,
    validate_active_text,
)


REPO = Path(__file__).resolve().parents[2]
CLEANUP_BASE = "0864b00948143d9b19d4983e50fcd2d905f4a5d3"
LEDGER = Path(
    "docs/research_program/long_horizon_rescue/"
    "cf4_p0_legacy_package_hashes.json"
)

RETIRED_CURRENT_PATHS = (
    "docs/manuscript",
    "figures",
    "external_audit_research_report_20260707_v5",
    "external_audit_research_report_20260721_v10",
    "external_audit_research_report_20260722_v11",
    "docs/generated/cf4_p0_quarantine_block.json",
    "docs/generated/external_audit_package.zip",
    "docs/generated/research_only_external_audit_package.zip",
    "docs/generated/statistical_formalism_audit_package.zip",
    "htt_base_research_evaluation_package.zip",
)


def _git(*args: str, text: bool = True) -> str | bytes:
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        check=True,
        capture_output=True,
        text=text,
    ).stdout


def test_retired_publication_surfaces_stay_absent_from_current_tree() -> None:
    for relative in RETIRED_CURRENT_PATHS:
        assert not (REPO / relative).exists(), relative


def test_live_policy_keeps_findings_blocked_without_release_exceptions() -> None:
    policy, _ = load_policy(REPO)
    assert policy["claim_tier"] == "blocked"
    assert policy["legacy_output_roots"] == []
    assert policy["scan"]["generated_contract_paths"] == []
    assert policy["inventory"]["deterministic_release_outputs"] == {}
    assert policy["inventory"]["reviewed_active_binary_sidecars"] == {}
    assert [
        row["finding_id"]
        for row in policy["root_state"]["required_open_findings"]
    ] == ["C1-K5-MV-F1", "C3-K5-VCORR-ML-F1", "N-DATA-CF4-DOWNSTREAM"]
    signature_ids = {row["id"] for row in policy["stale_signatures"]}
    assert {"cf4_mv_r200_headline", "cf4_ml_shape_factor"} <= signature_ids


def test_retired_generated_contracts_stay_in_memory_only() -> None:
    assert canonical_artifact_bytes(REPO) == {}
    record = load_block_record(REPO)
    assert record.payload["status"] == "QUARANTINED_OPEN_FINDINGS"
    assert record.payload["claim_tier"] == "blocked"
    assert record.payload["allowed_use"] == "blocked_source_record_only"
    assert record.payload["scientific_effect"] == "none"
    assert record.payload["replacement_value"] is None
    assert quarantine_block_payload(REPO) == dict(record.payload)


def test_claim_scan_still_rejects_retired_numeric_promotion() -> None:
    findings = validate_active_text(
        "candidate.md",
        "CF4 bulk-flow B200 amplitude 405.22 km/s",
        repo_root=REPO,
    )
    assert [finding.code for finding in findings] == ["stale_cf4_p0_consumer"]
    assert [finding.signature_id for finding in findings] == [
        "cf4_mv_r200_headline"
    ]
    assert validate_active_text(
        "candidate.md",
        "CF4 P0 findings remain OPEN; no replacement result is admitted.",
        repo_root=REPO,
    ) == ()


def test_recovery_authorities_remain_available_without_live_backup_mount() -> None:
    current = (REPO / LEDGER).read_bytes()
    assert current == _git("show", f"{CLEANUP_BASE}:{LEDGER.as_posix()}", text=False)
    ledger = json.loads(current)
    assert ledger["schema_version"] == "1.0.0"
    assert ledger["package_roots"]
    assert ledger["root_artifacts"]

    # The tracked v5 report is directly recoverable from the accepted base.
    _git(
        "cat-file",
        "-e",
        f"{CLEANUP_BASE}:external_audit_research_report_20260707_v5/MANIFEST.json",
    )
    # v6--v9 were already off-tree; the immutable ledger retains their typed
    # paths and content identities without pretending the backup is mounted.
    assert all(
        row["legacy_path"].startswith("legacy/cf4_p0/")
        for row in ledger["package_roots"]
    )
    assert all(
        row["root_sha256"].startswith("sha256:")
        for row in ledger["package_roots"]
    )
