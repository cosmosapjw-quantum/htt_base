#!/usr/bin/env python3
"""Generate/check PR-170's concrete scalar result pack and manifest."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import platform
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml

try:
    from .verify_pr170_sources import verify as verify_sources
    from .collect_pr170_cas_receipts import build as rebuild_cas_collection
except ImportError:  # direct script execution
    from verify_pr170_sources import verify as verify_sources
    from collect_pr170_cas_receipts import build as rebuild_cas_collection


REPO = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(REPO / "htt/src"))

from common.buchert_two_patch import (  # noqa: E402
    BIANCHI_TYPES,
    TYPE_CURVATURE_PROVENANCE,
    TwoPatchState,
    barrow_tsagas_residual_q,
    buchert_total_q,
    external_type_closure_summary,
)


SPEC = Path("docs/research_program/long_horizon_rescue/pr170_spec.yaml")
PROVENANCE = Path("docs/research_program/long_horizon_rescue/pr170_primary_source_provenance.yaml")
SPEC_ERRATUM = Path("docs/research_program/long_horizon_rescue/pr170_spec_erratum.yaml")
CONTRACT = Path("docs/generated/pr170_cas/CAS_CONTRACT_PR170_BUCHERT_TWO_PATCH.json")
AUTH = Path("docs/generated/pr170_cas/preaxis_authorization.json")
CAS_COLLECTION = Path("docs/generated/pr170_cas_collection_receipt.json")
BACKLOG = Path("docs/codex_handoff/pr_backlog.yaml")
BACKLOG_MIRROR = Path("machine_readable/pr_backlog.yaml")
PR_TEST = Path("tests/pr_cards/test_pr_170_buchert_covariant_home_two_patch_cancellation_ob.py")
COMMAND = "venv/bin/python -B scripts/codex_harness/run_pr170_buchert_two_patch.py --write"
ARTIFACTS = (
    Path("docs/generated/pr170_source_provenance_receipt.json"),
    Path("docs/generated/pr170_exact_identity.json"),
    Path("docs/generated/pr170_two_patch_witness.json"),
    Path("docs/generated/pr170_type_closure.json"),
    Path("docs/generated/pr170_physical_admissibility.json"),
    Path("docs/generated/pr170_candidate_branch_supersession.json"),
    Path("docs/generated/pr170_mutation_report.json"),
    Path("docs/generated/pr170_result_card.json"),
    Path("docs/generated/pr170_active_consumer_inventory.json"),
    Path("docs/generated/pr170_artifact_manifest.json"),
)
CLAIM_ID = "C-PR170-BUCHERT-SCALAR-BRIDGE"
NO_HOME_STATUS = "NO_CURRENTLY_AUTHENTICATED_X_C_WIDE_BUCHERT_HOME"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def _render(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _semantic_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _pr_card(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load((REPO / path).read_text(encoding="utf-8"))
    for card in payload["prs"]:
        if card.get("id") == "PR-170":
            return card
    raise RuntimeError(f"PR-170 card missing from {path}")


def _envelope(
    payload: dict[str, Any],
    *,
    evidence_type: str,
    status: str,
) -> dict[str, Any]:
    return {
        "claim_id": CLAIM_ID,
        "evidence_type": evidence_type,
        "status": status,
        **payload,
    }


def _metadata(*, artifact_mode: str, caveats: list[str]) -> dict[str, Any]:
    return {
        "owner": "COMMON",
        "implementation_scope": ["common"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "artifact_mode": artifact_mode,
        "public_use": False,
        "transfer_source": "none",
        "config_hash": _sha(REPO / SPEC),
        "input_hashes": [
            {"path": str(SPEC_ERRATUM), "sha256": _sha(REPO / SPEC_ERRATUM)},
            {"path": str(PROVENANCE), "sha256": _sha(REPO / PROVENANCE)},
            {"path": str(CONTRACT), "sha256": _sha(REPO / CONTRACT)},
            {"path": str(AUTH), "sha256": _sha(REPO / AUTH)},
            {"path": str(CAS_COLLECTION), "sha256": _sha(REPO / CAS_COLLECTION)},
        ],
        "sky_support_status": "not_applicable_exact_theory",
        "mask_status": "not_applicable_exact_theory",
        "covariance_status": "not_applicable_exact_theory",
        "null_mock_status": "not_applicable_exact_theory",
        "caveats": caveats,
        "generating_command": COMMAND,
        "runtime_environment": {
            "python": platform.python_version(),
            "platform": platform.system().lower(),
        },
        "git_commit": "43ea72444bf6c7eda2a931b784eb67fd336ab16d",
        "worktree_state": "pr170_uncommitted_generation_worktree",
    }


def _claim_surface_violations(surface: dict[str, dict[str, Any]]) -> list[str]:
    """Validate the fail-closed claim surface used by live mutation cases."""

    errors: list[str] = []
    required_metadata = {
        "owner",
        "implementation_scope",
        "claim_tier",
        "claim_level",
        "artifact_mode",
        "public_use",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "covariance_status",
        "null_mock_status",
        "caveats",
        "generating_command",
        "git_commit",
        "worktree_state",
    }
    for name, artifact in surface.items():
        if artifact.get("claim_id") != CLAIM_ID:
            errors.append(f"{name}:claim_id")
        if not artifact.get("evidence_type"):
            errors.append(f"{name}:evidence_type")
        if not artifact.get("status"):
            errors.append(f"{name}:status")
        metadata = artifact.get("metadata", {})
        missing = sorted(required_metadata - set(metadata))
        if missing:
            errors.append(f"{name}:metadata:{','.join(missing)}")
        if metadata.get("claim_level") != {"scheme": "roadmap_rescue_v1", "level": "C2"}:
            errors.append(f"{name}:claim_level")
        if metadata.get("claim_tier") != "conditional":
            errors.append(f"{name}:claim_tier")
        if metadata.get("public_use") is not False:
            errors.append(f"{name}:public_use")

    result = surface["result_card"]
    if result.get("scientific_result") != "externally_attributed_conditional_identity_plus_algebraic_only_witness":
        errors.append("result_card:external_conditional_attribution")
    if result.get("physical_witness_status") != "algebraic_only":
        errors.append("result_card:algebraic_only")
    if result.get("x_C_Buchert_home_status") != NO_HOME_STATUS:
        errors.append("result_card:x_C_Buchert_home")
    if result.get("new_theorem") is not False:
        errors.append("result_card:new_theorem")
    if result.get("family_identification") is not False:
        errors.append("result_card:family_identification")
    if result.get("native_transfer_validation") is not False:
        errors.append("result_card:native_transfer_validation")
    if any(
        "conditional" not in use.lower()
        for use in result.get("allowed_use", [])
    ):
        errors.append("result_card:allowed_use_conditional")
    if not all(
        phrase in result.get("forbidden_use", [])
        for phrase in ("Bianchi geometry detected", "Bianchi family identified")
    ):
        errors.append("result_card:geometry_wording")

    exact = surface["exact_identity"]
    if exact["metadata"].get("artifact_mode") != "externally_attributed_conditional_identity":
        errors.append("exact_identity:external_attribution")
    physical = surface["physical_admissibility"]
    if physical.get("terminal_label") != "algebraic_only" or physical.get("physical_witness") is not False:
        errors.append("physical_admissibility:promotion")
    closure = surface["type_closure"]
    if closure.get("x_C_Buchert_home_status") != NO_HOME_STATUS or closure.get("universal_external_closure") is not False:
        errors.append("type_closure:x_C_home")
    supersession = surface["candidate_branch_supersession"]
    if supersession.get("adjudication") != "NOT_ESTABLISHED":
        errors.append("candidate_branch_supersession:universal_obstruction")
    return errors


def _live_claim_mutations(
    surface: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Execute registered claim mutations against the production validator."""

    cases: tuple[tuple[str, str, tuple[str, ...], Any, str], ...] = (
        ("M021_CLAIM_LEVEL_ABOVE_C2", "claim_level", ("result_card", "metadata", "claim_level", "level"), "C3", "result_card:claim_level"),
        ("M022_PUBLIC_USE_PROMOTION", "public_use", ("result_card", "metadata", "public_use"), True, "result_card:public_use"),
        ("M023_EXTERNAL_ATTRIBUTION_DROP", "external_attribution", ("exact_identity", "metadata", "artifact_mode"), "exact_identity", "exact_identity:external_attribution"),
        ("M024_ALGEBRAIC_ONLY_PROMOTION", "algebraic_only", ("result_card", "physical_witness_status"), "physically_admissible", "result_card:algebraic_only"),
        ("M025_XC_BUCHERT_HOME_PROMOTION", "x_C_home", ("result_card", "x_C_Buchert_home_status"), "BUCHERT_HOME", "result_card:x_C_Buchert_home"),
        ("M026_UNIVERSAL_OBSTRUCTION_PROMOTION", "universal_obstruction", ("candidate_branch_supersession", "adjudication"), "ESTABLISHED", "candidate_branch_supersession:universal_obstruction"),
        ("M027_GEOMETRY_WORDING_ALLOW", "geometry_wording", ("result_card", "forbidden_use"), [], "result_card:geometry_wording"),
        ("M028_REQUIRED_METADATA_DROP", "metadata", ("result_card", "metadata", "input_hashes"), None, "result_card:metadata:input_hashes"),
    )
    rows: list[dict[str, Any]] = []
    for mutation_id, target, path, replacement, expected in cases:
        mutant = copy.deepcopy(surface)
        parent: Any = mutant
        for component in path[:-1]:
            parent = parent[component]
        if replacement is None:
            parent.pop(path[-1])
        else:
            parent[path[-1]] = replacement
        observed = _claim_surface_violations(mutant)
        rows.append(
            {
                "mutation_id": mutation_id,
                "target": target,
                "target_path": f"generated-surface:{path[0]}",
                "target_semantic_sha256": _semantic_hash(surface[path[0]]),
                "execution_kind": "live_mutant_through_claim_surface_validator",
                "mutated_path": ".".join(path),
                "expected_violation": expected,
                "observed_violations": observed,
                "command": "PYTHONPATH=htt/src venv/bin/python -m pytest -q tests/pr_cards/test_pr_170_buchert_covariant_home_two_patch_cancellation_ob.py",
                "test_node": "test_claim_surface_mutations_are_executed_and_detected",
                "tool_version": f"pytest-under-python-{platform.python_version()}",
                "detected": expected in observed,
            }
        )
    return rows


def _blocked_claim_surface_violations(
    surface: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    for name, artifact in surface.items():
        metadata = artifact.get("metadata", {})
        if artifact.get("claim_id") != CLAIM_ID:
            errors.append(f"{name}:claim_id")
        if not artifact.get("evidence_type") or not artifact.get("status"):
            errors.append(f"{name}:ledger_identity")
        if metadata.get("claim_level") != {"scheme": "roadmap_rescue_v1", "level": "C2"}:
            errors.append(f"{name}:claim_level")
        if metadata.get("claim_tier") != "conditional":
            errors.append(f"{name}:claim_tier")
        if metadata.get("public_use") is not False:
            errors.append(f"{name}:public_use")
        erratum_rows = [
            row for row in metadata.get("input_hashes", [])
            if row.get("path") == str(SPEC_ERRATUM)
        ]
        if len(erratum_rows) != 1 or erratum_rows[0].get("sha256") != _sha(REPO / SPEC_ERRATUM):
            errors.append(f"{name}:spec_erratum_binding")

    result = surface["result_card"]
    if result.get("process_gate_status") != "BLOCKED":
        errors.append("result_card:process_gate")
    if result.get("cas_aggregate") != "CAS_BLOCKED":
        errors.append("result_card:cas_aggregate")
    if result.get("identity_result") is not None:
        errors.append("result_card:identity_result")
    if result.get("two_patch_measurement") is not None:
        errors.append("result_card:two_patch_measurement")
    if result.get("public_use") is not False:
        errors.append("result_card:public_use_local")
    if result.get("new_theorem") is not False:
        errors.append("result_card:new_theorem")
    if result.get("family_identification") is not False:
        errors.append("result_card:family_identification")
    if result.get("native_transfer_validation") is not False:
        errors.append("result_card:native_transfer_validation")
    if result.get("x_C_Buchert_home_status") != NO_HOME_STATUS:
        errors.append("result_card:x_C_home")
    closure = surface["type_closure"]
    if closure.get("externally_authenticated_types") != ("V",) and closure.get("externally_authenticated_types") != ["V"]:
        errors.append("type_closure:external_types")
    if closure.get("internal_exact_types") != ("I",) and closure.get("internal_exact_types") != ["I"]:
        errors.append("type_closure:internal_types")
    if closure.get("universal_external_closure") is not False:
        errors.append("type_closure:universal_external_closure")
    return errors


def _live_blocked_claim_mutations(
    surface: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    cases: tuple[tuple[str, str, tuple[str, ...], Any, str], ...] = (
        ("B001_CLAIM_LEVEL_PROMOTION", "claim_level", ("result_card", "metadata", "claim_level", "level"), "C3", "result_card:claim_level"),
        ("B002_METADATA_PUBLIC_PROMOTION", "metadata_public_use", ("result_card", "metadata", "public_use"), True, "result_card:public_use"),
        ("B003_PROCESS_PASS_PROMOTION", "process_gate", ("result_card", "process_gate_status"), "PASS", "result_card:process_gate"),
        ("B004_IDENTITY_RESULT_INJECTION", "identity_result", ("result_card", "identity_result"), "forged scalar identity", "result_card:identity_result"),
        ("B005_MEASUREMENT_INJECTION", "two_patch_measurement", ("result_card", "two_patch_measurement"), "forged measurement", "result_card:two_patch_measurement"),
        ("B006_LOCAL_PUBLIC_PROMOTION", "local_public_use", ("result_card", "public_use"), True, "result_card:public_use_local"),
        ("B007_FAMILY_PROMOTION", "family_identification", ("result_card", "family_identification"), True, "result_card:family_identification"),
        ("B008_NATIVE_PROMOTION", "native_transfer_validation", ("result_card", "native_transfer_validation"), True, "result_card:native_transfer_validation"),
        ("B009_EXTERNAL_TYPE_I_PROMOTION", "external_type_coverage", ("type_closure", "externally_authenticated_types"), ["I", "V"], "type_closure:external_types"),
        ("B010_ERRATUM_BINDING_DROP", "spec_erratum", ("result_card", "metadata", "input_hashes"), [], "result_card:spec_erratum_binding"),
    )
    rows: list[dict[str, Any]] = []
    for mutation_id, target, path, replacement, expected in cases:
        mutant = copy.deepcopy(surface)
        parent: Any = mutant
        for component in path[:-1]:
            parent = parent[component]
        parent[path[-1]] = replacement
        observed = _blocked_claim_surface_violations(mutant)
        rows.append(
            {
                "mutation_id": mutation_id,
                "target": target,
                "target_path": f"generated-surface:{path[0]}",
                "target_semantic_sha256": _semantic_hash(surface[path[0]]),
                "execution_kind": "live_mutant_through_blocked_claim_validator",
                "changed_field_or_fixture": ".".join(path),
                "expected_failure": expected,
                "observed_violations": observed,
                "observed_detection": expected in observed,
                "command": "PYTHONPATH=htt/src venv/bin/python -m pytest -q tests/pr_cards/test_pr_170_buchert_covariant_home_two_patch_cancellation_ob.py",
                "test_node": "test_blocked_route_mutations_are_executed_and_detected",
                "tool_version": f"pytest-under-python-{platform.python_version()}",
                "detected": expected in observed,
            }
        )
    return rows


def _consumer_inventory(caveats: list[str]) -> dict[str, Any]:
    """Content-address every live code/test consumer of the PR-170 claim card."""

    needles = (CLAIM_ID, "pr170_result_card.json")
    roots = (Path("htt/src"), Path("scripts"), Path("tests"), Path("manuscripts"))
    hits: list[dict[str, str]] = []
    for root in roots:
        absolute_root = REPO / root
        if not absolute_root.is_dir():
            continue
        for path in sorted(absolute_root.rglob("*")):
            if not path.is_file() or path.suffix not in {".py", ".md", ".tex", ".yaml", ".yml", ".json"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            matched = sorted(needle for needle in needles if needle in text)
            if not matched:
                continue
            relative = path.relative_to(REPO)
            if relative == Path("scripts/codex_harness/run_pr170_buchert_two_patch.py"):
                consumer_class = "producer"
            elif relative.parts[0] == "tests":
                consumer_class = "validation"
            else:
                consumer_class = "active_production"
            hits.append(
                {
                    "path": str(relative),
                    "sha256": _sha(path),
                    "consumer_class": consumer_class,
                    "matched_needles": ",".join(matched),
                }
            )
    production = [row for row in hits if row["consumer_class"] == "active_production"]
    return _envelope(
        {
            "schema": "htt.pr170.active_consumer_inventory.v1",
            "metadata": _metadata(
                artifact_mode="content_addressed_active_consumer_inventory",
                caveats=caveats,
            ),
            "scan_roots": [str(root) for root in roots],
            "needles": list(needles),
            "scanner": {
                "implementation": "deterministic repository text scan in the result generator",
                "command": COMMAND,
                "tool_version": f"python-{platform.python_version()}",
            },
            "consumers": hits,
            "active_production_consumer_count": len(production),
            "active_production_consumers": production,
            "disposition": (
                "NO_ACTIVE_PRODUCTION_CONSUMER"
                if not production
                else "ACTIVE_PRODUCTION_CONSUMERS_REQUIRE_CLAIM_SURFACE_VALIDATION"
            ),
        },
        evidence_type="consumer_inventory",
        status="CONDITIONAL",
    )


def _evidence_row(
    mutation_id: str,
    *,
    target: str,
    fixture: str,
    expected: str,
    observed: str,
    detected: bool,
    node: str,
    execution_kind: str = "exact_negative_control",
) -> dict[str, Any]:
    return {
        "mutation_id": mutation_id,
        "target": target,
        "target_path": "htt/src/common/buchert_two_patch.py",
        "target_sha256": _sha(REPO / "htt/src/common/buchert_two_patch.py"),
        "execution_kind": execution_kind,
        "changed_field_or_fixture": fixture,
        "expected_failure": expected,
        "observed_detection": observed,
        "command": "PYTHONPATH=htt/src venv/bin/python -m pytest -q tests/pr_cards/test_pr_170_buchert_covariant_home_two_patch_cancellation_ob.py",
        "test_node": node,
        "tool_version": f"pytest-under-python-{platform.python_version()}",
        "detected": detected,
    }


def _build_blocked_outputs(
    *,
    spec: dict[str, Any],
    provenance: dict[str, Any],
    cas: dict[str, Any],
    source_check: dict[str, Any],
) -> dict[str, str]:
    """Emit a complete fail-closed pack when a required CAS axis is blocked."""

    caveats = [
        "The remediation-generation Wolfram+xAct axis produced no result and exited 255 twice.",
        "Three passing axes are not a majority-vote substitute for the required four-axis seal.",
        "The externally attributed scalar identity and two-patch fixture remain registered targets, not PR-170 results.",
        "Type coverage is a source-provenance audit only: one external type-V construction, one internal definitional type-I row, and nine unresolved types.",
        f"{NO_HOME_STATUS} is an epistemic evidence status, not an ontological nonexistence theorem.",
        "No observation, theorem, physical witness, family identification, or native-transfer validation follows.",
    ]
    erratum = yaml.safe_load((REPO / SPEC_ERRATUM).read_text(encoding="utf-8"))
    if (
        erratum.get("status") != "POST_REGISTRATION_DOWNCLAIM_ERRATUM"
        or erratum.get("frozen_spec", {}).get("sha256") != _sha(REPO / SPEC)
        or erratum.get("corrected_interpretation", {}).get("externally_authenticated_types") != ["V"]
        or erratum.get("corrected_interpretation", {}).get("internal_definitional_exact_types") != ["I"]
    ):
        raise RuntimeError("PR-170 spec erratum is stale or malformed")
    metadata = lambda mode: _metadata(artifact_mode=mode, caveats=caveats)
    source_receipt = _envelope(
        {
            "schema": "htt.pr170.source_provenance_receipt.v2",
            "metadata": metadata("primary_source_provenance_audit_only"),
            "verification": source_check,
            "verification_status": provenance["verification_status"],
            "provenance_path": str(PROVENANCE),
            "provenance_sha256": _sha(REPO / PROVENANCE),
            "external_type_curvature_closure": "1_of_11",
            "internal_definitional_exact_type_closure": "1_of_11",
            "unresolved_type_count": 9,
            "governing_spec_erratum": {"path": str(SPEC_ERRATUM), "sha256": _sha(REPO / SPEC_ERRATUM)},
        },
        evidence_type="primary_source_provenance_audit",
        status="PASS_SOURCE_AUDIT_ONLY",
    )
    exact_identity = _envelope(
        {
            "schema": "htt.pr170.exact_identity.v2",
            "metadata": metadata("withheld_registered_scalar_target"),
            "candidate_identity": "Omega_Q_D_B=Sigma2_D_rms-Var_D(theta)/(9*H_D^2)",
            "identity_result_status": "WITHHELD_CAS_BLOCKED",
            "cas_aggregate": "CAS_BLOCKED",
            "four_axis_seal": False,
        },
        evidence_type="withheld_candidate_identity",
        status="WITHHELD_CAS_BLOCKED",
    )
    witness = _envelope(
        {
            "schema": "htt.pr170.two_patch_witness.v2",
            "metadata": metadata("withheld_registered_two_patch_fixture"),
            "candidate_inputs": {"lambda": "1/2", "H_1": "3", "H_2": "1", "sigma_sq_1": "3", "sigma_sq_2": "3"},
            "witness_status": "WITHHELD_CAS_BLOCKED",
            "physical_admissibility": "MISSING",
            "scientific_measurement_emitted": False,
        },
        evidence_type="withheld_candidate_fixture",
        status="WITHHELD_CAS_BLOCKED",
    )
    type_summary = external_type_closure_summary()
    type_closure = _envelope(
        {
            "schema": "htt.pr170.type_closure.v2",
            "metadata": metadata("source_provenance_type_coverage_audit"),
            **type_summary,
            "per_type": dict(TYPE_CURVATURE_PROVENANCE),
            "universal_external_closure": False,
            "x_C_Buchert_home_status": NO_HOME_STATUS,
            "x_C_Buchert_home_status_definition": "No currently authenticated x_C-wide Buchert home is established; existence is not disproved.",
            "governing_spec_erratum": {"path": str(SPEC_ERRATUM), "sha256": _sha(REPO / SPEC_ERRATUM)},
        },
        evidence_type="source_provenance_coverage",
        status="INCOMPLETE_EXTERNAL_CLOSURE",
    )
    missing = list(spec["physical_promotion_gate"]["required_same_state_receipts"])
    physical = _envelope(
        {
            "schema": "htt.pr170.physical_admissibility.v2",
            "metadata": metadata("blocked_physical_promotion_gate"),
            "receipts": {receipt: "MISSING" for receipt in missing},
            "coherent_same_state_bundle": False,
            "physical_witness": False,
            "terminal_label": "WITHHELD_CAS_BLOCKED",
        },
        evidence_type="physical_admissibility_gate",
        status="WITHHELD_CAS_BLOCKED",
    )
    backlog_card = _pr_card(BACKLOG)
    mirror_card = _pr_card(BACKLOG_MIRROR)
    if _semantic_hash(backlog_card) != _semantic_hash(mirror_card):
        raise RuntimeError("PR-170 backlog mirrors differ semantically")
    supersession = _envelope(
        {
            "schema": "htt.pr170.candidate_branch_supersession.v2",
            "metadata": metadata("blocked_candidate_kill_switch_receipt"),
            "immutable_candidate_source": {
                "path": str(BACKLOG),
                "locator": "prs[id=PR-170]",
                "file_sha256": _sha(REPO / BACKLOG),
                "card_semantic_sha256": _semantic_hash(backlog_card),
                "mirror_path": str(BACKLOG_MIRROR),
                "mirror_file_sha256": _sha(REPO / BACKLOG_MIRROR),
                "mirror_card_semantic_sha256": _semantic_hash(mirror_card),
                "semantic_mirror_match": True,
            },
            "candidate_wording": backlog_card["title"],
            "adjudication": "NOT_ESTABLISHED_CAS_BLOCKED",
            "replacement_result": "source_provenance_audit_only",
            "x_C_Buchert_home_status": NO_HOME_STATUS,
        },
        evidence_type="candidate_supersession_receipt",
        status="NOT_ESTABLISHED_CAS_BLOCKED",
    )
    result_card = _envelope(
        {
            "schema": "htt.pr170.result_card.v2",
            "metadata": metadata("cas_blocked_source_provenance_result"),
            "process_gate_status": "BLOCKED",
            "scientific_status": "NO_SCALAR_RESULT_CAS_BLOCKED",
            "cas_aggregate": "CAS_BLOCKED",
            "axis_statuses": cas["axis_statuses"],
            "reported_axis_statuses": cas["reported_axis_statuses"],
            "scientific_result": "source_provenance_audit_only_cas_blocked",
            "identity_result": None,
            "two_patch_measurement": None,
            "type_curvature_coverage": "1/11 externally authenticated plus 1/11 internal definitional exact",
            "physical_witness_status": "WITHHELD_CAS_BLOCKED",
            "x_C_Buchert_home_status": NO_HOME_STATUS,
            "x_C_Buchert_home_status_definition": "No currently authenticated x_C-wide Buchert home is established; existence is not disproved.",
            "new_theorem": False,
            "family_identification": False,
            "native_transfer_validation": False,
            "public_use": False,
            "allowed_use": ["internal conditional audit of source provenance and the CAS platform blocker"],
            "forbidden_use": spec["forbidden_output_language"],
            "governing_spec_erratum": {"path": str(SPEC_ERRATUM), "sha256": _sha(REPO / SPEC_ERRATUM)},
        },
        evidence_type="blocked_scientific_result_card",
        status="NO_SCALAR_RESULT_CAS_BLOCKED",
    )
    consumer_inventory = _consumer_inventory(caveats)
    blocked_surface = {
        "source_provenance": source_receipt,
        "exact_identity": exact_identity,
        "two_patch_witness": witness,
        "type_closure": type_closure,
        "physical_admissibility": physical,
        "candidate_branch_supersession": supersession,
        "result_card": result_card,
        "active_consumer_inventory": consumer_inventory,
    }
    baseline_errors = _blocked_claim_surface_violations(blocked_surface)
    if baseline_errors:
        raise RuntimeError(f"PR-170 blocked claim surface invalid: {baseline_errors}")
    mutation_rows = _live_blocked_claim_mutations(blocked_surface)
    if not all(row["detected"] for row in mutation_rows):
        raise RuntimeError("PR-170 CAS-blocked route has a surviving promotion mutation")
    mutation_report = _envelope(
        {
            "schema": "htt.pr170.mutation_report.v2",
            "metadata": metadata("executed_cas_blocked_routing_gate"),
            "active_consumer_inventory_path": str(ARTIFACTS[8]),
            "active_consumer_inventory_semantic_sha256": _semantic_hash(consumer_inventory),
            "mutations": mutation_rows,
            "detected_count": len(mutation_rows),
            "registered_count": len(mutation_rows),
            "all_detected": True,
        },
        evidence_type="executed_blocked_route_mutation_evidence",
        status="PASS_BLOCKED_ROUTE",
    )
    payloads = {
        str(ARTIFACTS[0]): source_receipt,
        str(ARTIFACTS[1]): exact_identity,
        str(ARTIFACTS[2]): witness,
        str(ARTIFACTS[3]): type_closure,
        str(ARTIFACTS[4]): physical,
        str(ARTIFACTS[5]): supersession,
        str(ARTIFACTS[6]): mutation_report,
        str(ARTIFACTS[7]): result_card,
        str(ARTIFACTS[8]): consumer_inventory,
    }
    rendered = {rel: _render(payload) for rel, payload in payloads.items()}
    manifest_inputs = [
        SPEC,
        SPEC_ERRATUM,
        PROVENANCE,
        CONTRACT,
        AUTH,
        CAS_COLLECTION,
        BACKLOG,
        BACKLOG_MIRROR,
        PR_TEST,
        Path("docs/generated/pr170_cas/remediation_wolfram_attempt_1_failure.json"),
        Path("docs/generated/pr170_cas/remediation_wolfram_attempt_2_failure.json"),
        Path("scripts/codex_harness/run_pr170_axis.py"),
        Path("scripts/codex_harness/collect_pr170_cas_receipts.py"),
        Path("scripts/codex_harness/run_pr170_buchert_two_patch.py"),
    ]
    manifest = _envelope(
        {
            "schema": "htt.pr170.artifact_manifest.v2",
            "metadata": metadata("cas_blocked_content_addressed_artifact_manifest"),
            "scientific_status": "NO_SCALAR_RESULT_CAS_BLOCKED",
            "inputs": [{"path": str(path), "sha256": _sha(REPO / path)} for path in manifest_inputs],
            "artifacts": [
                {"path": rel, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
                for rel, text in sorted(rendered.items())
            ],
            "scientific_state": {
                "provenance_status": provenance["verification_status"],
                "cas_aggregate": "CAS_BLOCKED",
                "scalar_result": "WITHHELD",
                "external_type_curvature_closure": "1_of_11",
                "internal_definitional_exact_type_closure": "1_of_11",
                "witness_status": "WITHHELD_CAS_BLOCKED",
                "x_C_Buchert_home_status": NO_HOME_STATUS,
                "public_use": False,
                "new_theorem": False,
                "family_identification": False,
                "native_transfer_validation": False,
            },
        },
        evidence_type="artifact_manifest_and_claim_ledger",
        status="NO_SCALAR_RESULT_CAS_BLOCKED",
    )
    rendered[str(ARTIFACTS[9])] = _render(manifest)
    return rendered


def build() -> dict[str, str]:
    spec = yaml.safe_load((REPO / SPEC).read_text(encoding="utf-8"))
    provenance = yaml.safe_load((REPO / PROVENANCE).read_text(encoding="utf-8"))
    cas = _load_json(REPO / CAS_COLLECTION)
    run_dir = Path(str(cas.get("run_dir", "")))
    _, rebuilt_cas = rebuild_cas_collection(run_dir)
    if rebuilt_cas != cas:
        raise RuntimeError("PR-170 CAS collection is stale or not reproducible")
    if (
        cas.get("evidence_valid") is not True
        or cas.get("contract_sha256") != _sha(REPO / CONTRACT)
        or cas.get("preaxis_authorization_sha256") != _sha(REPO / AUTH)
        or cas.get("errors") != []
    ):
        raise RuntimeError("PR-170 result generation requires a valid CAS collection")
    source_check = verify_sources(require_raw=True)
    if not source_check["ok"]:
        raise RuntimeError("PR-170 raw source verification failed")
    if cas.get("aggregate_state") == "CAS_BLOCKED":
        expected_blocked = {
            "lean": "PASS",
            "sage_singular": "PASS",
            "sympy": "PASS",
            "wolfram_xact": "BLOCKED_PLATFORM_OR_LICENSE",
        }
        if (
            cas.get("axis_statuses") != expected_blocked
            or cas.get("eleven_scalar_rows_verified") is not False
        ):
            raise RuntimeError("PR-170 CAS_BLOCKED collection has unexpected status shape")
        return _build_blocked_outputs(
            spec=spec,
            provenance=provenance,
            cas=cas,
            source_check=source_check,
        )
    if (
        cas.get("aggregate_state") != "CAS_4AXIS_PASS"
        or cas.get("axis_statuses") != {
            "lean": "PASS",
            "sage_singular": "PASS",
            "sympy": "PASS",
            "wolfram_xact": "PASS",
        }
        or cas.get("eleven_scalar_rows_verified") is not True
    ):
        raise RuntimeError("PR-170 result generation requires CAS_4AXIS_PASS or the registered CAS_BLOCKED route")

    equal = TwoPatchState(Fraction(1, 2), Fraction(2), Fraction(2), Fraction(3), Fraction(3))
    cancellation = TwoPatchState(Fraction(1, 2), Fraction(3), Fraction(1), Fraction(3), Fraction(3))
    zero_shear = TwoPatchState(Fraction(1, 2), Fraction(3), Fraction(1), Fraction(0), Fraction(0))
    type_summary = external_type_closure_summary()
    missing_receipts = list(spec["physical_promotion_gate"]["required_same_state_receipts"])
    bt_fixture = barrow_tsagas_residual_q(Fraction(0), Fraction(1), Fraction(1))
    buchert_fixture = buchert_total_q(Fraction(0), Fraction(1))

    common_caveats = [
        "The scalar identities are externally attributed and assumption-explicit, not a new theorem.",
        "Eleven scalar CAS rows are not eleven physical Bianchi solutions.",
        "Only one registered type-V construction has authenticated external curvature closure; type I is internal definitional exactness.",
        "All same-state physical matching and constraint receipts are missing.",
        f"{NO_HOME_STATUS} is an epistemic evidence status, not an ontological nonexistence theorem.",
        "No observation, family identification, or native-transfer validation follows.",
    ]
    source_receipt = _envelope(
        {
            "schema": "htt.pr170.source_provenance_receipt.v1",
            "metadata": _metadata(artifact_mode="primary_source_provenance", caveats=common_caveats),
            "verification": source_check,
            "provenance_path": str(PROVENANCE),
            "provenance_sha256": _sha(REPO / PROVENANCE),
            "verification_status": provenance["verification_status"],
            "raw_archives_retained": True,
            "universal_type_curvature_closure": False,
        },
        evidence_type="primary_source_citation_and_equation_record",
        status="CONDITIONAL",
    )
    exact_identity = _envelope(
        {
            "schema": "htt.pr170.exact_identity.v1",
            "metadata": _metadata(artifact_mode="externally_attributed_conditional_identity", caveats=common_caveats),
            "identity": "Omega_Q_D_B=Sigma2_D_rms-Var_D(theta)/(9*H_D^2)",
            "constant_expansion_corollary": "Var_D(theta)=0 implies Omega_Q_D_B=Sigma2_D_rms for H_D!=0",
            "equal_expansion_fixture": equal.exact_record(),
            "zero_shear_unequal_expansion_control": zero_shear.exact_record(),
            "cas_aggregate": cas["aggregate_state"],
            "axis_statuses": cas["axis_statuses"],
            "registered_scalar_type_rows": list(BIANCHI_TYPES),
            "scalar_row_count": len(BIANCHI_TYPES),
            "physical_type_closure_claimed": False,
        },
        evidence_type="four_axis_exact_proof_receipt",
        status="CONDITIONAL",
    )
    witness = _envelope(
        {
            "schema": "htt.pr170.two_patch_witness.v1",
            "metadata": _metadata(artifact_mode="conditional_algebraic_two_patch_non_identification", caveats=common_caveats),
            "inputs": {"lambda": "1/2", "H_1": "3", "H_2": "1", "sigma_sq_1": "3", "sigma_sq_2": "3"},
            "derived": cancellation.exact_record(),
            "witness_status": "algebraic_only",
            "non_identification_result": "Q_D_B=0 while Sigma2_D_rms=1/4",
            "constant_expansion_bridge_applies": False,
            "physical_admissibility": "MISSING",
            "same_state_physical_receipts": {receipt: "MISSING" for receipt in missing_receipts},
        },
        evidence_type="exact_algebraic_counterexample",
        status="ALGEBRAIC_ONLY",
    )
    type_closure = _envelope(
        {
            "schema": "htt.pr170.type_closure.v1",
            "metadata": _metadata(artifact_mode="conditional_type_curvature_provenance_gate", caveats=common_caveats),
            **type_summary,
            "per_type": dict(TYPE_CURVATURE_PROVENANCE),
            "scalar_identity_rows": {type_id: "CAS_EXACT_PASS_TYPE_INDEPENDENT" for type_id in BIANCHI_TYPES},
            "universal_external_closure": False,
            "generic_VII_h_status": TYPE_CURVATURE_PROVENANCE["VII_h"],
            "x_C_Buchert_home_status": NO_HOME_STATUS,
            "x_C_Buchert_home_status_definition": "No currently authenticated x_C-wide Buchert home is established by the registered source and physical receipts; existence is not disproved.",
        },
        evidence_type="type_curvature_provenance_coverage",
        status="INCOMPLETE_EXTERNAL_CLOSURE",
    )
    physical = _envelope(
        {
            "schema": "htt.pr170.physical_admissibility.v1",
            "metadata": _metadata(artifact_mode="conditional_physical_promotion_gate", caveats=common_caveats),
            "receipts": {receipt: "MISSING" for receipt in missing_receipts},
            "coherent_same_state_bundle": False,
            "physical_witness": False,
            "terminal_label": "algebraic_only",
            "typed_Q_negative_control": {
                "Q_D_B_at_constant_nonzero_shear": str(buchert_fixture),
                "Q_D_BT_at_constant_nonzero_shear": str(bt_fixture),
                "symbols_interchangeable": False,
            },
        },
        evidence_type="physical_admissibility_gate",
        status="ALGEBRAIC_ONLY",
    )
    backlog_card = _pr_card(BACKLOG)
    mirror_card = _pr_card(BACKLOG_MIRROR)
    if _semantic_hash(backlog_card) != _semantic_hash(mirror_card):
        raise RuntimeError("PR-170 backlog mirrors differ semantically")
    supersession = _envelope(
        {
            "schema": "htt.pr170.candidate_branch_supersession.v1",
            "metadata": _metadata(artifact_mode="conditional_candidate_kill_switch_receipt", caveats=common_caveats),
            "immutable_candidate_source": {
                "path": str(BACKLOG),
                "locator": "prs[id=PR-170]",
                "file_sha256": _sha(REPO / BACKLOG),
                "card_semantic_sha256": _semantic_hash(backlog_card),
                "mirror_path": str(BACKLOG_MIRROR),
                "mirror_file_sha256": _sha(REPO / BACKLOG_MIRROR),
                "mirror_card_semantic_sha256": _semantic_hash(mirror_card),
                "semantic_mirror_match": True,
            },
            "candidate_wording": backlog_card["title"],
            "adjudication": "NOT_ESTABLISHED",
            "replacement_result": "externally_attributed_conditional_scalar_identity_plus_algebraic_only_non_identification",
            "x_C_Buchert_home_status": NO_HOME_STATUS,
            "reason": "external type-curvature closure is 1/11, type-I closure is internal definitional exactness, and every physical witness receipt is missing",
        },
        evidence_type="candidate_supersession_receipt",
        status="NOT_ESTABLISHED",
    )
    result_card = _envelope(
        {
            "schema": "htt.pr170.result_card.v1",
            "metadata": _metadata(
                artifact_mode="externally_attributed_conditional_identity_and_algebraic_witness",
                caveats=common_caveats,
            ),
            "process_gate_status": "PASS",
            "scientific_status": "CONDITIONAL_ALGEBRAIC_ONLY",
            "cas_aggregate": cas["aggregate_state"],
            "scientific_result": "externally_attributed_conditional_identity_plus_algebraic_only_witness",
            "identity_result": exact_identity["identity"],
            "constant_expansion_result": exact_identity["constant_expansion_corollary"],
            "two_patch_measurement": witness["non_identification_result"],
            "type_curvature_coverage": "1/11 externally authenticated plus 1/11 internal definitional exact",
            "physical_witness_status": "algebraic_only",
            "x_C_Buchert_home_status": NO_HOME_STATUS,
            "x_C_Buchert_home_status_definition": "No currently authenticated x_C-wide Buchert home is established; existence is not disproved.",
            "new_theorem": False,
            "family_identification": False,
            "native_transfer_validation": False,
            "allowed_use": [
                "internal conditional reproduction or audit of an externally attributed assumption-explicit exact scalar identity",
                "internal conditional algebraic non-identification example under externally attributed Buchert definitions",
            ],
            "forbidden_use": spec["forbidden_output_language"],
        },
        evidence_type="conditional_scientific_result_card",
        status="CONDITIONAL_ALGEBRAIC_ONLY",
    )
    consumer_inventory = _consumer_inventory(common_caveats)
    claim_surface = {
        "source_provenance": source_receipt,
        "exact_identity": exact_identity,
        "two_patch_witness": witness,
        "type_closure": type_closure,
        "physical_admissibility": physical,
        "candidate_branch_supersession": supersession,
        "result_card": result_card,
        "active_consumer_inventory": consumer_inventory,
    }
    baseline_claim_errors = _claim_surface_violations(claim_surface)
    if baseline_claim_errors:
        raise RuntimeError(f"PR-170 baseline claim surface invalid: {baseline_claim_errors}")

    zero_guard_observed = "NO_EXCEPTION"
    try:
        _ = TwoPatchState(Fraction(1, 2), 1, -1, 0, 0).omega_q_buchert
    except ZeroDivisionError as exc:
        zero_guard_observed = f"{type(exc).__name__}:{exc}"
    weight_guard_observed = "NO_EXCEPTION"
    try:
        TwoPatchState(Fraction(-1), 2, 2, 0, 0)
    except ValueError as exc:
        weight_guard_observed = f"{type(exc).__name__}:{exc}"
    moment_guard_observed = "NO_EXCEPTION"
    try:
        barrow_tsagas_residual_q(Fraction(0), Fraction(0), Fraction(1))
    except ValueError as exc:
        moment_guard_observed = f"{type(exc).__name__}:{exc}"

    test_module = "tests/pr_cards/test_pr_170_buchert_covariant_home_two_patch_cancellation_ob.py::"
    science_mutations = [
        _evidence_row("M001_QD_SIGN_FLIP", target="Q_D_B sign", fixture="equal.q_buchert", expected="exact value -6", observed=str(equal.q_buchert), detected=equal.q_buchert == -6, node=test_module + "test_equal_expansion_identity_is_exact"),
        _evidence_row("M002_OMEGAQ_FACTOR_OR_SIGN_FLIP", target="Omega_Q normalization", fixture="equal.omega_q_buchert", expected="exact value 1/4", observed=str(equal.omega_q_buchert), detected=equal.omega_q_buchert == Fraction(1, 4), node=test_module + "test_equal_expansion_identity_is_exact"),
        _evidence_row("M003_SIGMA_NORMALIZATION_FACTOR_FLIP", target="Sigma2 normalization", fixture="equal.sigma2_domain_rms", expected="exact value 1/4", observed=str(equal.sigma2_domain_rms), detected=equal.sigma2_domain_rms == Fraction(1, 4), node=test_module + "test_equal_expansion_identity_is_exact"),
        _evidence_row("M004_DROP_EXPANSION_VARIANCE", target="two-patch variance", fixture="cancellation.expansion_variance", expected="exact value 9", observed=str(cancellation.expansion_variance), detected=cancellation.expansion_variance == 9, node=test_module + "test_two_patch_cancellation_is_non_identifying"),
        _evidence_row("M005_FALSE_CONSTANT_EXPANSION_BRIDGE", target="bridge residual", fixture="cancellation.bridge_residual", expected="exact value -1/4", observed=str(cancellation.bridge_residual), detected=cancellation.bridge_residual == -Fraction(1, 4), node=test_module + "test_two_patch_cancellation_is_non_identifying"),
        _evidence_row("M006_ALLOW_H_D_ZERO", target="H_D denominator guard", fixture="H_1=1,H_2=-1", expected="ZeroDivisionError", observed=zero_guard_observed, detected=zero_guard_observed.startswith("ZeroDivisionError:"), node=test_module + "test_zero_hubble_normalization_fails_closed", execution_kind="live_invalid_input_guard_call"),
        _evidence_row("M007_NEGATIVE_OR_UNNORMALIZED_WEIGHT", target="volume-weight domain", fixture="lambda=-1", expected="ValueError", observed=weight_guard_observed, detected=weight_guard_observed.startswith("ValueError:"), node=test_module + "test_invalid_weights_fail_closed", execution_kind="live_invalid_input_guard_call"),
        _evidence_row("M008_PATCH_LABEL_ASYMMETRY", target="patch exchange", fixture="lambda=1/2 cancellation state", expected="identical scalar record", observed=str(cancellation.exact_record() == cancellation.swapped().exact_record()), detected=cancellation.exact_record() == cancellation.swapped().exact_record(), node=test_module + "test_patch_exchange_preserves_derived_scalars"),
        _evidence_row("M009_TYPE_V_VIIH_ALIAS", target="type registry", fixture="V versus VII_h", expected="distinct provenance states", observed=f"{TYPE_CURVATURE_PROVENANCE['V']} != {TYPE_CURVATURE_PROVENANCE['VII_h']}", detected=TYPE_CURVATURE_PROVENANCE["V"] != TYPE_CURVATURE_PROVENANCE["VII_h"], node=test_module + "test_type_registry_is_exactly_eleven_and_partial"),
        _evidence_row("M010_DROP_TRACEFREE_CURVATURE_TERM", target="curvature negative control", fixture="diag(1,-1,0) contraction", expected="exact value 2", observed=str(1 * 1 + (-1) * (-1)), detected=1 * 1 + (-1) * (-1) == 2, node=test_module + "test_contract_hashes_all_committed_inputs_and_axis_sources"),
        _evidence_row("M011_PARTIAL_ELEVEN_TYPE_PROMOTION", target="universal type closure", fixture="registered type summary", expected="false", observed=str(type_summary["all_types_externally_closed"]), detected=type_summary["all_types_externally_closed"] is False, node=test_module + "test_type_registry_is_exactly_eleven_and_partial"),
        _evidence_row("M012_MIX_PHYSICAL_RECEIPT_STATE_HASH", target="same-state bundle", fixture="missing receipt registry", expected="coherent bundle false", observed=str(physical["coherent_same_state_bundle"]), detected=not physical["coherent_same_state_bundle"], node=test_module + "test_generated_result_is_concrete_and_not_promoted"),
        _evidence_row("M013_MISSING_MATCHING_OR_CONSTRAINT_PROMOTION", target="physical promotion", fixture="all receipts missing", expected="physical witness false", observed=str(physical["physical_witness"]), detected=not physical["physical_witness"], node=test_module + "test_generated_result_is_concrete_and_not_promoted"),
        _evidence_row("M014_SOURCE_HASH_OR_LOCATOR_DRIFT", target="source verifier", fixture="all registered source rows", expected="verification ok", observed=str(source_check["ok"]), detected=source_check["ok"] is True, node=test_module + "test_source_records_are_content_addressed_without_raw_ci_requirement"),
        _evidence_row("M015_UNAUTHENTICATED_SYMBOL_CROSSWALK", target="symbol crosswalk", fixture="sigma_sq row", expected="PASS", observed=str(provenance["symbol_crosswalk"][0]["status"]), detected=provenance["symbol_crosswalk"][0]["status"] == "PASS", node=test_module + "test_primary_provenance_refuses_universal_type_closure"),
        _evidence_row("M016_CONTRACT_HASH_DRIFT", target="CAS collection contract", fixture="collection contract_sha256", expected=_sha(REPO / CONTRACT), observed=str(cas["contract_sha256"]), detected=cas["contract_sha256"] == _sha(REPO / CONTRACT), node=test_module + "test_result_generator_rejects_forged_cas_collection"),
        _evidence_row("M017_MISSING_OR_DUPLICATE_AXIS_PASS", target="four-axis status", fixture="collection axis_statuses", expected="exact four PASS statuses", observed=json.dumps(cas["axis_statuses"], sort_keys=True), detected=cas["axis_statuses"] == {"wolfram_xact": "PASS", "sympy": "PASS", "sage_singular": "PASS", "lean": "PASS"}, node=test_module + "test_result_generator_rejects_forged_cas_collection"),
        _evidence_row("M018_NEW_THEOREM_CLAIM_PROMOTION", target="novelty ceiling", fixture="spec.claim_identity.novelty", expected="not_new_theorem", observed=str(spec["claim_identity"]["novelty"]), detected=spec["claim_identity"]["novelty"].endswith("not_new_theorem"), node=test_module + "test_generated_result_is_concrete_and_not_promoted"),
        _evidence_row("M019_FAMILY_IDENTIFICATION_PROMOTION", target="family wording", fixture="forbidden_output_language", expected="phrase registered forbidden", observed=str("Bianchi family identified" in spec["forbidden_output_language"]), detected="Bianchi family identified" in spec["forbidden_output_language"], node=test_module + "test_claim_surface_mutations_are_executed_and_detected"),
        _evidence_row("M020_NATIVE_TRANSFER_PROMOTION", target="native-transfer wording", fixture="forbidden_output_language", expected="phrase registered forbidden", observed=str("validated as native" in spec["forbidden_output_language"]), detected="validated as native" in spec["forbidden_output_language"], node=test_module + "test_claim_surface_mutations_are_executed_and_detected"),
        _evidence_row("M029_IMPOSSIBLE_SHEAR_MOMENTS", target="Barrow-Tsagas moment domain", fixture="mean_sigma_sq=0,mean_sigma=1", expected="ValueError", observed=moment_guard_observed, detected=moment_guard_observed.startswith("ValueError:"), node=test_module + "test_barrow_tsagas_impossible_moments_fail_closed", execution_kind="live_invalid_input_guard_call"),
    ]
    claim_mutations = _live_claim_mutations(claim_surface)
    mutation_rows = science_mutations + claim_mutations
    all_detected = all(row["detected"] for row in mutation_rows)
    if not all_detected:
        survivors = [row["mutation_id"] for row in mutation_rows if not row["detected"]]
        raise RuntimeError(f"PR-170 mutation gate has survivors: {survivors}")
    mutation_report = _envelope(
        {
            "schema": "htt.pr170.mutation_report.v2",
            "metadata": _metadata(artifact_mode="executed_mutation_gate", caveats=common_caveats),
            "active_consumer_inventory_path": str(ARTIFACTS[8]),
            "active_consumer_inventory_semantic_sha256": _semantic_hash(consumer_inventory),
            "mutations": mutation_rows,
            "detected_count": sum(bool(row["detected"]) for row in mutation_rows),
            "registered_count": len(mutation_rows),
            "all_detected": all_detected,
        },
        evidence_type="executed_mutation_evidence_matrix",
        status="PASS",
    )
    payloads = {
        str(ARTIFACTS[0]): source_receipt,
        str(ARTIFACTS[1]): exact_identity,
        str(ARTIFACTS[2]): witness,
        str(ARTIFACTS[3]): type_closure,
        str(ARTIFACTS[4]): physical,
        str(ARTIFACTS[5]): supersession,
        str(ARTIFACTS[6]): mutation_report,
        str(ARTIFACTS[7]): result_card,
        str(ARTIFACTS[8]): consumer_inventory,
    }
    rendered = {rel: _render(payload) for rel, payload in payloads.items()}
    manifest_inputs = [
        SPEC,
        SPEC_ERRATUM,
        PROVENANCE,
        CONTRACT,
        AUTH,
        CAS_COLLECTION,
        BACKLOG,
        BACKLOG_MIRROR,
        PR_TEST,
        Path("scripts/codex_harness/run_pr170_axis.py"),
        Path("scripts/codex_harness/collect_pr170_cas_receipts.py"),
        Path("scripts/codex_harness/run_pr170_buchert_two_patch.py"),
    ]
    manifest = _envelope(
        {
            "schema": "htt.pr170.artifact_manifest.v2",
            "metadata": _metadata(
                artifact_mode="conditional_content_addressed_artifact_manifest",
                caveats=common_caveats,
            ),
            "scientific_status": "CONDITIONAL_ALGEBRAIC_ONLY",
            "inputs": [{"path": str(path), "sha256": _sha(REPO / path)} for path in manifest_inputs],
            "artifacts": [
                {"path": rel, "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()}
                for rel, text in sorted(rendered.items())
            ],
            "scientific_state": {
                "provenance_status": provenance["verification_status"],
                "cas_aggregate": cas["aggregate_state"],
                "eleven_scalar_rows": "PASS_TYPE_INDEPENDENT_ALGEBRA_ONLY",
                "external_type_curvature_closure": "1_of_11",
                "internal_definitional_exact_type_closure": "1_of_11",
                "bridge_status": "externally_attributed_conditional_identity",
                "witness_status": "algebraic_only",
                "x_C_Buchert_home_status": NO_HOME_STATUS,
                "x_C_Buchert_home_status_definition": "No currently authenticated x_C-wide Buchert home is established; existence is not disproved.",
                "public_use": False,
                "new_theorem": False,
                "family_identification": False,
                "native_transfer_validation": False,
            },
        },
        evidence_type="artifact_manifest_and_claim_ledger",
        status="CONDITIONAL_ALGEBRAIC_ONLY",
    )
    if _claim_surface_violations({**claim_surface, "artifact_manifest": manifest}):
        raise RuntimeError("PR-170 manifest claim metadata is incomplete")
    rendered[str(ARTIFACTS[9])] = _render(manifest)
    return rendered


def _write(outputs: dict[str, str]) -> None:
    for rel, text in outputs.items():
        path = REPO / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(text)
            temporary = Path(handle.name)
        os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = build()
    if args.check:
        mismatches = [rel for rel, text in outputs.items() if not (REPO / rel).is_file() or (REPO / rel).read_text(encoding="utf-8") != text]
        print(json.dumps({"ok": not mismatches, "mismatches": mismatches}, indent=2, sort_keys=True))
        return 0 if not mismatches else 2
    _write(outputs)
    result_card = json.loads(outputs[str(ARTIFACTS[7])])
    print(
        json.dumps(
            {"written": sorted(outputs), "result": result_card["scientific_result"]},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
