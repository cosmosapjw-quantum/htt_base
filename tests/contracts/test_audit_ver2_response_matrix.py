from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
MATRIX_JSON = REPO_ROOT / "docs/generated/audit_ver2_response_matrix.json"
MATRIX_MD = REPO_ROOT / "docs/generated/audit_ver2_response_matrix.md"
ARCHIVE_ROOT = REPO_ROOT / "docs/audits/external_research_inputs_2026-06-20_reaudit"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _matrix() -> dict[str, object]:
    return json.loads(MATRIX_JSON.read_text(encoding="utf-8"))


def test_audit_ver2_matrix_prioritizes_strict_audit():
    matrix = _matrix()

    assert matrix["schema_version"] == "htt.audit_ver2_response_matrix.v1"
    assert matrix["strict_audit_controls_conflicts"] is True
    assert matrix["canonical_dag_status"] == "unchanged_complete"
    assert matrix["claim_tier"] == "diagnostic_only"
    blockers = {row["blocker_id"]: row for row in matrix["blockers"]}
    assert {"F1", "F2", "F3", "F4"} <= set(blockers)
    assert blockers["F1"]["required_policy"] == (
        "positive_lnb_reclassified_as_amplitude_fit"
    )
    assert blockers["F2"]["required_policy"] == (
        "normal_frame_vorticity_zero_until_threading_identity"
    )
    assert blockers["F3"]["required_policy"] == (
        "scalar_qf_proxy_until_channel_matched_or_joint_ceiling"
    )
    assert blockers["F4"]["required_policy"] == (
        "no_single_jeffreys_label_without_prior_error_surface"
    )
    assert all(row["next_rev_id"].startswith("REV-R") for row in matrix["blockers"])


def test_audit_ver2_archive_preserves_hashes_and_roles():
    matrix = _matrix()
    archived = {row["source_name"]: row for row in matrix["archived_inputs"]}

    assert {
        "audit_ver2.md",
        "RESEARCH_AUDIT_REPORT.md",
        "2026-06-20-audit-ver2-research-hardening.md",
    } <= set(archived)
    for row in archived.values():
        archive_path = REPO_ROOT / str(row["archive_path"])
        assert archive_path.is_file(), archive_path
        assert row["sha256"] == _sha256(archive_path)
        assert row["status"] == "raw_external_or_plan_input_hash_preserved"

    assert archived["audit_ver2.md"]["role"] == "strict_external_reaudit"
    assert archived["RESEARCH_AUDIT_REPORT.md"]["role"] == "near_pass_external_reaudit"
    assert (
        archived["2026-06-20-audit-ver2-research-hardening.md"]["role"]
        == "repo_authored_execution_plan"
    )


def test_audit_ver2_matrix_categories_and_safe_claim_boundary():
    matrix = _matrix()
    categories = {row["category"] for row in matrix["action_rows"]}

    assert {
        "fatal_blocker",
        "major_required_fix",
        "minor_repair_from_near_pass_audit",
        "defensible_boundary_statement",
    } <= categories
    boundary_statements = " ".join(
        str(row["safe_wording"])
        for row in matrix["action_rows"]
        if row["category"] == "defensible_boundary_statement"
    ).lower()
    assert "single-perfect-fluid" in boundary_statements
    assert "diagnostic" in boundary_statements
    assert "family" in boundary_statements
    assert "identified" not in boundary_statements
    assert "geometry detected" not in boundary_statements


def test_audit_ver2_markdown_has_metadata_and_no_native_promotion():
    text = MATRIX_MD.read_text(encoding="utf-8")
    lowered = text.lower()

    assert "owner: COMMON" in text
    assert "claim_tier: diagnostic_only" in text
    assert "strict audit controls conflicts" in lowered
    assert "positive_lnb_reclassified_as_amplitude_fit" in text
    assert "normal_frame_vorticity_zero_until_threading_identity" in text
    assert "scalar_qf_proxy_until_channel_matched_or_joint_ceiling" in text
    assert "no_single_jeffreys_label_without_prior_error_surface" in text
    assert "native solver result" not in lowered
    assert "family identified" not in lowered
    assert "geometry detected" not in lowered


def test_audit_ver2_archive_manifest_exists():
    manifest = ARCHIVE_ROOT / "ARCHIVE_MANIFEST.md"
    inventory = ARCHIVE_ROOT / "input_inventory.md"

    assert manifest.is_file()
    assert inventory.is_file()
    manifest_text = manifest.read_text(encoding="utf-8")
    assert "strict_external_reaudit" in manifest_text
    assert "not publication evidence" in manifest_text
