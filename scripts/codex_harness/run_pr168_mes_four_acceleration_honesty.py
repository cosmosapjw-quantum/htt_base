#!/usr/bin/env python3
"""Close PR-168 on the fail branch after hostile contract review.

The four CAS engines agreed with one registered fixture.  A later independent
physics review found that the registered statement itself is underdefined and
contains a factor-of-three normalization counterexample.  This runner preserves
the immutable engine evidence, supersedes its provisional production
authorization, and proves that every inventoried production consumer remains at
its pre-CAS hash.

It intentionally does not execute or repair a CAS axis.  A repaired contract
would have a new hash and requires a fresh blind four-axis run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = Path("docs/research_program/long_horizon_rescue/pr168_spec.yaml")
INVENTORY_PATH = Path(
    "docs/research_program/long_horizon_rescue/"
    "pr168_active_b_accel_consumers.yaml"
)
CONTRACT_PATH = Path(
    "docs/generated/pr168_cas/"
    "CAS_CONTRACT_PR168_ACCEL_KINEMATIC_SOURCE_BASIS.json"
)
ORIGINAL_ADJUDICATION_PATH = Path("docs/generated/pr168_cas_adjudication.json")
COLLECTION_RECEIPT_PATH = Path("docs/generated/pr168_cas_collection_receipt.json")
FAILURE_ADJUDICATION_PATH = Path(
    "docs/generated/pr168_contract_failure_adjudication.json"
)
INTEGRITY_PATH = Path("docs/generated/pr168_code_integrity_receipt.json")
THEOREM_SIGNATURE_PATH = Path("docs/generated/pr168_theorem_signature.json")
RESULT_CARD_PATH = Path("docs/generated/pr168_result_card.json")
MANIFEST_PATH = Path("docs/generated/pr168_artifact_manifest.json")

AXES = ("wolfram_xact", "sympy", "sage_singular", "lean")
AXIS_RESULT_PATHS = {
    axis: Path(f"docs/generated/pr168_cas/axis_result_{axis}.json")
    for axis in AXES
}
AXIS_ASSIGNMENT_PATHS = {
    axis: Path(f"docs/generated/pr168_cas/harness_receipts/assignment_{axis}.json")
    for axis in AXES
}
AXIS_OUTER_RESULT_PATHS = {
    axis: Path(f"docs/generated/pr168_cas/harness_receipts/outer_result_{axis}.json")
    for axis in AXES
}
REVIEW_PATHS = {
    role: Path(f"docs/generated/pr168_reviews/result_{role}.json")
    for role in ("physics", "code", "claim")
}
REVIEW_ASSIGNMENT_PATHS = {
    role: Path(f"docs/generated/pr168_reviews/assignment_{role}.json")
    for role in ("physics", "code", "claim")
}
EXPECTED_REVIEW_STATUS = {"physics": "fail", "code": "fail", "claim": "fail"}
EXPECTED_CONTRACT_SHA256 = (
    "d2821237e8c7cf3fc97b27dea5062cc943482d217bbc53f45157848b111a542d"
)
FORBIDDEN_PASS_ONLY_OUTPUTS = (
    Path("docs/generated/pr168_stale_consumer_scan.json"),
    Path("docs/generated/pr168_mutation_report.json"),
    Path("htt/src/common/mes_acceleration_status.py"),
    Path("figures/pr168/fig_MES_two_supported_bounds.png"),
    Path("figures/pr168/fig_MES_two_supported_bounds.png.manifest.json"),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and path.read_text(encoding="utf-8") == rendered:
        return
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(rendered)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def _git_state() -> str:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    return f"{head}{'+dirty' if dirty else ''}"


def _normalization_counterexample(spec: dict[str, Any]) -> dict[str, Any]:
    fixture = spec["registered_exact_fixture"]
    acceleration = Fraction(fixture["acceleration_amplitude"])
    factor = Fraction(fixture["thermodynamic_factor"])
    source = acceleration * factor / Fraction(3)
    amplitude_normalized = source / acceleration
    registered = Fraction(fixture["expected"]["normalized_basis_test"][1])
    return {
        "acceleration_amplitude": str(acceleration),
        "thermodynamic_factor": str(factor),
        "defined_acceleration_source_ell1": str(source),
        "defined_source_divided_by_amplitude": str(amplitude_normalized),
        "registered_normalized_target_ell1": str(registered),
        "mismatch": amplitude_normalized != registered,
        "explanation": (
            "With S_A=(A*G/3) delta_ell1, ordinary amplitude normalization "
            "gives S_A/A=G/3.  The registered target G would require the "
            "unstated operator 3*S_A/A."
        ),
    }


def _production_rows() -> list[dict[str, Any]]:
    inventory = _yaml(REPO / INVENTORY_PATH)
    rows: list[dict[str, Any]] = []
    for registered in inventory["migration_required"]:
        rel = registered["path"]
        path = REPO / rel
        actual = _sha(path) if path.is_file() else None
        rows.append(
            {
                "path": rel,
                "owner": registered["owner"],
                "expected_pre_axis_sha256": registered["sha256_before"],
                "actual_sha256": actual,
                "unchanged": actual == registered["sha256_before"],
            }
        )
    return rows


def _historical_production_rows() -> list[dict[str, Any]]:
    """Reconstruct PR-168's frozen closeout rows without reading live bytes."""
    inventory = _yaml(REPO / INVENTORY_PATH)
    return [
        {
            "path": registered["path"],
            "owner": registered["owner"],
            "expected_pre_axis_sha256": registered["sha256_before"],
            "actual_sha256": registered["sha256_before"],
            "unchanged": True,
        }
        for registered in inventory["migration_required"]
    ]


def _authorized_post_closeout_transition(
    relative_path: str, prior_sha256: str, current_sha256: str
) -> bool:
    """Delegate later exact-hash transitions to the PR-248 authority."""
    src_root = str(REPO / "htt/src")
    if src_root not in sys.path:
        sys.path.insert(0, src_root)
    from common.pr248_pr168_integrity_supersession import (
        authorized_pr168_transition,
    )

    return authorized_pr168_transition(
        REPO,
        relative_path=relative_path,
        prior_sha256=prior_sha256,
        current_sha256=current_sha256,
    )


def _review_refs() -> dict[str, dict[str, Any]]:
    refs: dict[str, dict[str, Any]] = {}
    for role, rel in REVIEW_PATHS.items():
        payload = _json(REPO / rel)
        assignment_rel = REVIEW_ASSIGNMENT_PATHS[role]
        refs[role] = {
            "path": rel.as_posix(),
            "sha256": _sha(REPO / rel),
            "assignment_path": assignment_rel.as_posix(),
            "assignment_sha256": _sha(REPO / assignment_rel),
            "assignment_id": payload.get("assignment_id"),
            "context_version": payload.get("context_version"),
            "status": payload.get("status"),
        }
    return refs


def evidence_errors() -> list[str]:
    errors: list[str] = []
    required = (
        SPEC_PATH,
        INVENTORY_PATH,
        CONTRACT_PATH,
        ORIGINAL_ADJUDICATION_PATH,
        COLLECTION_RECEIPT_PATH,
        *AXIS_RESULT_PATHS.values(),
        *AXIS_ASSIGNMENT_PATHS.values(),
        *AXIS_OUTER_RESULT_PATHS.values(),
        *REVIEW_PATHS.values(),
        *REVIEW_ASSIGNMENT_PATHS.values(),
    )
    for rel in required:
        if not (REPO / rel).is_file():
            errors.append(f"missing required evidence: {rel}")
    if errors:
        return errors

    contract_sha = _sha(REPO / CONTRACT_PATH)
    if contract_sha != EXPECTED_CONTRACT_SHA256:
        errors.append("registered contract hash drifted")

    original = _json(REPO / ORIGINAL_ADJUDICATION_PATH)
    if original.get("aggregate_status") != "CAS_4AXIS_PASS":
        errors.append("original computational adjudication is not CAS_4AXIS_PASS")
    if original.get("contract_sha256") != contract_sha:
        errors.append("original adjudication contract binding drifted")
    for field in ("errors", "missing_axes", "exceptions_applied"):
        if original.get(field) != []:
            errors.append(f"original adjudication {field} is nonempty")

    receipt = _json(REPO / COLLECTION_RECEIPT_PATH)
    if receipt.get("contract_sha256") != contract_sha:
        errors.append("collection receipt contract binding drifted")
    if receipt.get("aggregate_status") != "CAS_4AXIS_PASS":
        errors.append("collection receipt lost the original computational pass")
    if receipt.get("production_authorized") is not True:
        errors.append("historical provisional authorization was rewritten")
    normalized_hashes = receipt.get("normalized_axis_sha256")
    if not isinstance(normalized_hashes, dict) or set(normalized_hashes) != set(AXES):
        errors.append("collection receipt axis-hash set is incomplete")
        normalized_hashes = {}

    contract = _json(REPO / CONTRACT_PATH)
    expected_checks = set(contract["target"]["exact_test_obligations"])
    for axis, rel in AXIS_RESULT_PATHS.items():
        path = REPO / rel
        payload = _json(path)
        assignment = _json(REPO / AXIS_ASSIGNMENT_PATHS[axis])
        outer_path = REPO / AXIS_OUTER_RESULT_PATHS[axis]
        outer = _json(outer_path)
        if normalized_hashes.get(axis) != _sha(path):
            errors.append(f"{axis}: normalized result hash differs from receipt")
        if receipt.get("outer_envelope_sha256", {}).get(axis) != _sha(outer_path):
            errors.append(f"{axis}: durable outer-envelope hash differs from receipt")
        if outer.get("payload", {}).get("cas_axis_result") != payload:
            errors.append(f"{axis}: normalized result differs from durable outer envelope")
        if outer.get("status") != "pass":
            errors.append(f"{axis}: durable outer harness status is not pass")
        if outer.get("assignment_id") != assignment.get("assignment_id"):
            errors.append(f"{axis}: assignment identity differs from outer envelope")
        if outer.get("run_id") != assignment.get("run_id"):
            errors.append(f"{axis}: assignment run differs from outer envelope")
        if outer.get("context_version") != assignment.get("context_version"):
            errors.append(f"{axis}: assignment context differs from outer envelope")
        if assignment.get("cas_axis") != axis:
            errors.append(f"{axis}: durable assignment axis differs")
        if assignment.get("independence_mode") != "blind-results":
            errors.append(f"{axis}: durable assignment is not blind-results")
        if assignment.get("allowed_sibling_results") != []:
            errors.append(f"{axis}: durable assignment allowed sibling results")
        if payload.get("axis") != axis or payload.get("status") != "PASS":
            errors.append(f"{axis}: original normalized result is not PASS")
        if payload.get("contract_sha256") != contract_sha:
            errors.append(f"{axis}: contract hash binding drifted")
        if payload.get("evidence_class") != "exact":
            errors.append(f"{axis}: evidence_class is not exact")
        if set(payload.get("checks", {})) != expected_checks:
            errors.append(f"{axis}: exact check-key set is incomplete")
        elif not all(value is True for value in payload["checks"].values()):
            errors.append(f"{axis}: one or more registered checks is false")
        if not payload.get("commands") or not payload.get("completed_at"):
            errors.append(f"{axis}: execution provenance is missing")
        if not payload.get("verified_input_hashes"):
            errors.append(f"{axis}: verified input hashes are missing")
        if payload.get("redistributed_fixture_matches") is not True:
            errors.append(f"{axis}: redistribution receipt is not true")
        if payload.get("counterexample") is not None:
            errors.append(f"{axis}: PASS payload contains a counterexample")
        if payload.get("domain_assumption_diff") != []:
            errors.append(f"{axis}: domain assumptions differ")
        if payload.get("sibling_results_read") != []:
            errors.append(f"{axis}: blind-results isolation was violated")
        if payload.get("source_output_hashes") != contract["axes"][axis]["sources"]:
            errors.append(f"{axis}: axis-source hash binding drifted")

    refs = _review_refs()
    for role, expected_status in EXPECTED_REVIEW_STATUS.items():
        assignment = _json(REPO / REVIEW_ASSIGNMENT_PATHS[role])
        result = _json(REPO / REVIEW_PATHS[role])
        if refs[role]["status"] != expected_status:
            errors.append(
                f"{role} review status is {refs[role]['status']!r}, "
                f"expected {expected_status!r}"
            )
        if not refs[role]["assignment_id"] or not refs[role]["context_version"]:
            errors.append(f"{role} review lacks assignment/context provenance")
        if assignment.get("assignment_id") != result.get("assignment_id"):
            errors.append(f"{role} durable review assignment identity differs")
        if assignment.get("context_version") != result.get("context_version"):
            errors.append(f"{role} durable review assignment context differs")

    physics = _json(REPO / REVIEW_PATHS["physics"])
    physics_findings = {
        row.get("finding_id") for row in physics.get("findings", [])
        if isinstance(row, dict)
    }
    for required_finding in ("F-PR168-PHYS-001", "F-PR168-PHYS-002"):
        if required_finding not in physics_findings:
            errors.append(f"physics review lacks {required_finding}")

    code = _json(REPO / REVIEW_PATHS["code"])
    code_findings = {
        row.get("finding_id")
        for row in code.get("payload", {}).get("findings", [])
        if isinstance(row, dict)
    }
    for required_finding in (
        "F-PR168-CODE-001",
        "F-PR168-CODE-002",
        "F-PR168-CODE-003",
    ):
        if required_finding not in code_findings:
            errors.append(f"code review lacks {required_finding}")

    counterexample = _normalization_counterexample(_yaml(REPO / SPEC_PATH))
    if counterexample["mismatch"] is not True:
        errors.append("registered normalization counterexample disappeared")
    return errors


def production_errors() -> list[str]:
    errors: list[str] = []
    for row in _production_rows():
        if row["unchanged"]:
            continue
        if _authorized_post_closeout_transition(
            row["path"],
            row["expected_pre_axis_sha256"],
            row["actual_sha256"] or "",
        ):
            continue
        errors.append(
            f"production consumer changed on fail branch: {row['path']}"
        )
    status_source = REPO / "htt/src/common/mes_acceleration_status.py"
    if status_source.exists():
        errors.append("pass-only typed status source still exists")
    return errors


def _failure_adjudication() -> dict[str, Any]:
    contract_sha = _sha(REPO / CONTRACT_PATH)
    return {
        "schema": "htt.pr168.post_cas_contract_adjudication.v1",
        "pr_id": "PR-168",
        "claim_id": "C-PR168-ACCEL-KINEMATIC-SOURCE-BASIS",
        "adjudication_layer": "post_cas_scientific_contract_review",
        "aggregate_status": "CAS_FAIL",
        "original_computational_aggregate": "CAS_4AXIS_PASS",
        "original_computational_agreement_preserved": True,
        "scientific_contract_status": "INVALID_UNDERDEFINED",
        "production_authorized": False,
        "supersedes_provisional_production_authorization": {
            "path": COLLECTION_RECEIPT_PATH.as_posix(),
            "sha256": _sha(REPO / COLLECTION_RECEIPT_PATH),
            "reason": (
                "Hostile review found a direct normalization counterexample "
                "and undefined negative-control equations in the registered "
                "statement.  Engine agreement with that fixture cannot "
                "authorize production mutation."
            ),
        },
        "contract_sha256": contract_sha,
        "normalization_counterexample": _normalization_counterexample(
            _yaml(REPO / SPEC_PATH)
        ),
        "review_receipts": _review_refs(),
        "fatal_finding_ids": [
            "F-PR168-PHYS-001",
            "F-PR168-PHYS-002",
            "F-PR168-CODE-001",
            "F-PR168-CODE-002",
            "F-PR168-CODE-003",
        ],
        "required_next_attempt": (
            "Freeze a repaired schema-v2 contract with explicit normalization "
            "and negative-control equations, then execute four fresh blind "
            "axes and a fresh adjudication.  Reuse of these PASS envelopes is "
            "forbidden."
        ),
        "production_disposition": "all inventoried consumers unchanged",
        "public_use": False,
        "generated_at": _now(),
    }


def _integrity_receipt() -> dict[str, Any]:
    rows = _production_rows()
    return {
        "schema": "htt.pr168.fail_branch_code_integrity.v1",
        "pr_id": "PR-168",
        "outcome": "PRODUCTION_UNCHANGED",
        "contract_sha256": _sha(REPO / CONTRACT_PATH),
        "production_rows": rows,
        "all_inventoried_consumers_unchanged": all(
            row["unchanged"] for row in rows
        ),
        "pass_only_status_source_absent": not (
            REPO / "htt/src/common/mes_acceleration_status.py"
        ).exists(),
        "git_commit_or_worktree_state": _git_state(),
        "generated_at": _now(),
    }


def _common_metadata() -> dict[str, Any]:
    return {
        "owner": "COMMON",
        "contributors": ["BASS", "HTT"],
        "affected_owner_review": "rejected_by_adversarial_closeout",
        "implementation_scope": ["common", "harness", "docs"],
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "not_applicable_exact_mechanics",
        "config_hash": _sha(REPO / CONTRACT_PATH),
        "sky_support_mask_status": "not_applicable",
        "covariance_null_mock_status": "not_applicable",
        "caveats": [
            "The four-engine agreement is computational evidence under an invalid contract.",
            "No acceleration API or production consumer was removed.",
            "No independent physical derivation was established.",
            "No finite-k, transfer, observational, geometry, family, evidence, posterior, or detection claim is allowed.",
        ],
        "git_commit_or_worktree_state": _git_state(),
        "runtime": {
            "python": sys.version.split()[0],
            "axis_tools": {
                axis: _json(REPO / rel).get("tool_versions")
                for axis, rel in AXIS_RESULT_PATHS.items()
            },
        },
    }


def _evidence_hashes() -> dict[str, str]:
    paths = (
        SPEC_PATH,
        INVENTORY_PATH,
        CONTRACT_PATH,
        ORIGINAL_ADJUDICATION_PATH,
        COLLECTION_RECEIPT_PATH,
        FAILURE_ADJUDICATION_PATH,
        *AXIS_RESULT_PATHS.values(),
        *AXIS_ASSIGNMENT_PATHS.values(),
        *AXIS_OUTER_RESULT_PATHS.values(),
        *REVIEW_PATHS.values(),
        *REVIEW_ASSIGNMENT_PATHS.values(),
    )
    return {rel.as_posix(): _sha(REPO / rel) for rel in paths}


def _theorem_signature() -> dict[str, Any]:
    payload = {
        "schema": "htt.pr168.theorem_signature.v2",
        "signature_id": "SIG-PR168-ACCEL-KINEMATIC-SOURCE-BASIS",
        "claim_id": "C-PR168-ACCEL-KINEMATIC-SOURCE-BASIS",
        "title": "Withheld acceleration/kinematic source-basis identity",
        "signature_status": "WITHHELD_CONTRACT_INVALID",
        "evidence_grade": "computational_agreement_under_invalid_contract",
        "aggregate_status": "CAS_FAIL",
        "counts_as_independent_derivation": False,
        "counts_toward_legacy_theorem_count": False,
        "quantified_variables": [],
        "target_identity": None,
        "result": None,
        "normalization_counterexample": _normalization_counterexample(
            _yaml(REPO / SPEC_PATH)
        ),
        "required_next_attempt": (
            "A new theorem signature may be issued only after a repaired "
            "contract and fresh blind four-axis adjudication."
        ),
        "input_hashes": _evidence_hashes(),
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/"
            "run_pr168_mes_four_acceleration_honesty.py write-closeout"
        ),
        **_common_metadata(),
    }
    return payload


def _result_card() -> dict[str, Any]:
    return {
        "schema": "htt.pr168.result_card.v2",
        "pr_id": "PR-168",
        "claim_id": "C-PR168-ACCEL-KINEMATIC-SOURCE-BASIS",
        "result_status": "CAS_FAIL_CONTRACT_INVALID_PRODUCTION_UNCHANGED",
        "scientific_result": (
            "A direct factor-of-three counterexample invalidates the "
            "registered amplitude-normalization obligation.  The separately "
            "registered negative controls also lack defining equations.  "
            "Therefore the four-engine fixture agreement is not a valid "
            "scientific authorization, and all inventoried production "
            "consumers remain unchanged."
        ),
        "original_computational_result": {
            "aggregate_status": "CAS_4AXIS_PASS",
            "interpretation": "preserved but superseded for production use",
        },
        "final_adjudicated_result": {
            "aggregate_status": "CAS_FAIL",
            "production_authorized": False,
            "normalization_counterexample": _normalization_counterexample(
                _yaml(REPO / SPEC_PATH)
            ),
        },
        "production_disposition": "unchanged",
        "fresh_axis_requirement": (
            "Contract repair changes semantics and hash; all four axes must be "
            "rerun blind.  Current axis envelopes may not be reused."
        ),
        "input_hashes": _evidence_hashes(),
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/"
            "run_pr168_mes_four_acceleration_honesty.py write-closeout"
        ),
        **_common_metadata(),
    }


def _manifest_input_paths() -> tuple[Path, ...]:
    return (
        SPEC_PATH,
        INVENTORY_PATH,
        CONTRACT_PATH,
        ORIGINAL_ADJUDICATION_PATH,
        COLLECTION_RECEIPT_PATH,
        *AXIS_ASSIGNMENT_PATHS.values(),
        *AXIS_OUTER_RESULT_PATHS.values(),
        *REVIEW_PATHS.values(),
        *REVIEW_ASSIGNMENT_PATHS.values(),
        Path("scripts/codex_harness/run_pr168_mes_four_acceleration_honesty.py"),
    )


def _manifest_artifact_paths() -> tuple[Path, ...]:
    return (
        *AXIS_RESULT_PATHS.values(),
        FAILURE_ADJUDICATION_PATH,
        INTEGRITY_PATH,
        THEOREM_SIGNATURE_PATH,
        RESULT_CARD_PATH,
    )


def _artifact_manifest() -> dict[str, Any]:
    return {
        "schema": "htt.pr168.artifact_manifest.v2",
        "pr_id": "PR-168",
        "outcome": "CAS_FAIL_CONTRACT_INVALID_PRODUCTION_UNCHANGED",
        "input_hashes": {
            rel.as_posix(): _sha(REPO / rel) for rel in _manifest_input_paths()
        },
        "artifact_hashes": {
            rel.as_posix(): _sha(REPO / rel)
            for rel in _manifest_artifact_paths()
        },
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/"
            "run_pr168_mes_four_acceleration_honesty.py write-closeout"
        ),
        **_common_metadata(),
        "generated_at": _now(),
    }


def _hash_map_errors(
    actual: Any, expected_paths: tuple[Path, ...], label: str
) -> list[str]:
    expected_keys = {rel.as_posix() for rel in expected_paths}
    if not isinstance(actual, dict):
        return [f"manifest {label} is not a mapping"]
    if not actual:
        return [f"manifest {label} is empty"]
    if set(actual) != expected_keys:
        return [f"manifest {label} key set is not exact"]
    errors: list[str] = []
    for rel, expected in actual.items():
        path = REPO / rel
        if not path.is_file():
            errors.append(f"manifest {label} hash binding failed: {rel}")
            continue
        observed = _sha(path)
        if observed != expected and not _authorized_post_closeout_transition(
            rel, expected, observed
        ):
            errors.append(f"manifest {label} hash binding failed: {rel}")
    return errors


def output_errors() -> list[str]:
    errors: list[str] = []
    required = (
        FAILURE_ADJUDICATION_PATH,
        INTEGRITY_PATH,
        THEOREM_SIGNATURE_PATH,
        RESULT_CARD_PATH,
        MANIFEST_PATH,
    )
    for rel in required:
        if not (REPO / rel).is_file():
            errors.append(f"missing closeout output: {rel}")
    if errors:
        return errors

    failure = _json(REPO / FAILURE_ADJUDICATION_PATH)
    if failure.get("aggregate_status") != "CAS_FAIL":
        errors.append("final contract adjudication is not CAS_FAIL")
    if failure.get("production_authorized") is not False:
        errors.append("final adjudication does not reject production authorization")
    if failure.get("contract_sha256") != _sha(REPO / CONTRACT_PATH):
        errors.append("final adjudication contract binding is stale")
    if failure.get("normalization_counterexample", {}).get("mismatch") is not True:
        errors.append("final adjudication lacks the normalization counterexample")
    if failure.get("review_receipts") != _review_refs():
        errors.append("final adjudication review bindings are stale")

    integrity = _json(REPO / INTEGRITY_PATH)
    if integrity.get("all_inventoried_consumers_unchanged") is not True:
        errors.append("integrity receipt does not prove unchanged production")
    historical_rows = _historical_production_rows()
    if integrity.get("production_rows") != historical_rows:
        errors.append("integrity historical production receipt is stale")
    else:
        for row in historical_rows:
            path = REPO / row["path"]
            current_sha = _sha(path) if path.is_file() else ""
            if current_sha == row["actual_sha256"]:
                continue
            if not _authorized_post_closeout_transition(
                row["path"], row["actual_sha256"], current_sha
            ):
                errors.append(
                    "integrity production hash drift lacks a post-closeout "
                    f"supersession: {row['path']}"
                )
    if integrity.get("pass_only_status_source_absent") is not True:
        errors.append("integrity receipt retained pass-only status source")

    theorem = _json(REPO / THEOREM_SIGNATURE_PATH)
    if theorem.get("signature_status") != "WITHHELD_CONTRACT_INVALID":
        errors.append("theorem signature was not withheld")
    if theorem.get("aggregate_status") != "CAS_FAIL":
        errors.append("theorem signature does not carry CAS_FAIL")
    if theorem.get("result") is not None or theorem.get("target_identity") is not None:
        errors.append("invalid theorem signature still exposes a checked theorem")
    if theorem.get("public_use") is not False:
        errors.append("invalid theorem signature is public-use enabled")

    card = _json(REPO / RESULT_CARD_PATH)
    if card.get("result_status") != (
        "CAS_FAIL_CONTRACT_INVALID_PRODUCTION_UNCHANGED"
    ):
        errors.append("result card status differs from fail outcome")
    if card.get("production_disposition") != "unchanged":
        errors.append("result card does not preserve production")
    if card.get("final_adjudicated_result", {}).get("production_authorized") is not False:
        errors.append("result card still authorizes production")
    if card.get("claim_tier") != "exploratory" or card.get("public_use") is not False:
        errors.append("result card claim tier/public-use state is unsafe")

    manifest = _json(REPO / MANIFEST_PATH)
    errors.extend(
        _hash_map_errors(
            manifest.get("input_hashes"), _manifest_input_paths(), "input_hashes"
        )
    )
    errors.extend(
        _hash_map_errors(
            manifest.get("artifact_hashes"),
            _manifest_artifact_paths(),
            "artifact_hashes",
        )
    )
    if manifest.get("affected_owner_review") != (
        "rejected_by_adversarial_closeout"
    ):
        errors.append("manifest affected-owner review is not resolved as rejected")
    if manifest.get("outcome") != (
        "CAS_FAIL_CONTRACT_INVALID_PRODUCTION_UNCHANGED"
    ):
        errors.append("manifest outcome differs from fail result")

    for rel in FORBIDDEN_PASS_ONLY_OUTPUTS:
        if (REPO / rel).exists():
            errors.append(f"pass-only output remains after failed closeout: {rel}")
    return errors


def validate_evidence() -> int:
    errors = evidence_errors() + production_errors()
    print(
        json.dumps(
            {
                "ok": not errors,
                "errors": errors,
                "original_computational_aggregate": "CAS_4AXIS_PASS",
                "final_required_aggregate": "CAS_FAIL",
                "production_disposition": "unchanged",
            },
            indent=2,
        )
    )
    return 0 if not errors else 2


def write_closeout() -> int:
    errors = evidence_errors() + production_errors()
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 2

    _write_json(REPO / FAILURE_ADJUDICATION_PATH, _failure_adjudication())
    _write_json(REPO / INTEGRITY_PATH, _integrity_receipt())
    _write_json(REPO / THEOREM_SIGNATURE_PATH, _theorem_signature())
    _write_json(REPO / RESULT_CARD_PATH, _result_card())
    _write_json(REPO / MANIFEST_PATH, _artifact_manifest())

    errors = evidence_errors() + production_errors() + output_errors()
    print(
        json.dumps(
            {
                "ok": not errors,
                "errors": errors,
                "aggregate_status": "CAS_FAIL",
                "original_computational_aggregate": "CAS_4AXIS_PASS",
                "production_disposition": "unchanged",
                "manifest": MANIFEST_PATH.as_posix(),
            },
            indent=2,
        )
    )
    return 0 if not errors else 2


def check() -> int:
    errors = evidence_errors() + production_errors() + output_errors()
    print(
        json.dumps(
            {
                "ok": not errors,
                "errors": errors,
                "aggregate_status": "CAS_FAIL",
                "production_disposition": "unchanged",
            },
            indent=2,
        )
    )
    return 0 if not errors else 2


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate-evidence")
    sub.add_parser("write-closeout")
    sub.add_parser("check")
    args = parser.parse_args()
    if args.command == "validate-evidence":
        raise SystemExit(validate_evidence())
    if args.command == "write-closeout":
        raise SystemExit(write_closeout())
    raise SystemExit(check())


if __name__ == "__main__":
    main()
