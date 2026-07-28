#!/usr/bin/env python3
"""Fail-closed intake and conjecture gates for PR-253/PR-254.

These gates do not promote J1-EXACT or J2-UNIFORM.  They distinguish evidence
that could make a conjecture ready for independent adjudication from evidence
that refutes or restricts it.  Final claim promotion remains outside this
module.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping, Sequence


GATE_EVALUATOR_REF = (
    "scripts/codex_harness/premise_anchor_gates.py:"
    "evaluate_conjecture_gate"
)
READY_OUTCOME = "READY_FOR_INDEPENDENT_ADJUDICATION"
MISSING_OUTCOME = "BLOCKED_MISSING_EVIDENCE"
INVALID_OUTCOME = "BLOCKED_INVALID_EVIDENCE"
REFUTED_OUTCOME = "REFUTED_OR_RESTRICTED"

_COMMON_REFUTING_OUTCOMES = [
    "VALID_COUNTEREXAMPLE",
    "COUNTEREXAMPLE_FOUND",
    "PROOF_FAILURE",
    "CAS_FAIL",
]

CONJECTURE_GATE_CONTRACTS: dict[str, dict[str, Any]] = {
    "J1-EXACT": {
        "claim_id": "J1-EXACT",
        "owner": "COMMON",
        "claim_status": "CONJECTURE_COUNTEREXAMPLE_FIRST",
        "promotion_gate": "ALL_J1_EVIDENCE_REQUIRED",
        "gate_evaluator": GATE_EVALUATOR_REF,
        "statement_components": [
            "physical_set_equality",
            "essential_uniqueness_under_declared_equivalence",
        ],
        "obligations": [
            {
                "obligation_id": "PHYSICAL_SET_EQUALITY_PROOF",
                "required_outcome": "PASS",
            },
            {
                "obligation_id": "ESSENTIAL_UNIQUENESS_PROOF",
                "required_outcome": "PASS",
            },
            {
                "obligation_id": "FOUR_AXIS_CAS",
                "required_outcome": "CAS_4AXIS_PASS",
            },
            {
                "obligation_id": "COUNTEREXAMPLE_ADJUDICATION",
                "required_outcome": "NO_VALID_COUNTEREXAMPLE",
            },
        ],
        "refuting_outcomes": _COMMON_REFUTING_OUTCOMES,
        "ready_outcome": READY_OUTCOME,
        "failure_disposition": REFUTED_OUTCOME,
    },
    "J2-UNIFORM": {
        "claim_id": "J2-UNIFORM",
        "owner": "HTT",
        "claim_status": "CONJECTURE_COUNTEREXAMPLE_FIRST",
        "promotion_gate": "ALL_J2_EVIDENCE_REQUIRED",
        "gate_evaluator": GATE_EVALUATOR_REF,
        "statement_components": [
            "registered_joint_random_anchor_law",
            "whole_composite_null_finite_sample_uniform_validity",
        ],
        "obligations": [
            {
                "obligation_id": "JOINT_NUMERATOR_ANCHOR_LAW",
                "required_outcome": "PASS",
            },
            {
                "obligation_id": "FINITE_SAMPLE_UNIFORM_VALIDITY_PROOF",
                "required_outcome": "PASS",
            },
            {
                "obligation_id": "INDEPENDENT_COVERAGE_ORACLE",
                "required_outcome": "PASS",
            },
            {
                "obligation_id": "COUNTEREXAMPLE_ADJUDICATION",
                "required_outcome": "NO_VALID_COUNTEREXAMPLE",
            },
        ],
        "refuting_outcomes": _COMMON_REFUTING_OUTCOMES,
        "ready_outcome": READY_OUTCOME,
        "failure_disposition": REFUTED_OUTCOME,
    },
}


def claim_contracts_for_backlog() -> list[dict[str, Any]]:
    """Return detached gate contracts in canonical J1/J2 order."""

    return [
        deepcopy(CONJECTURE_GATE_CONTRACTS[claim_id])
        for claim_id in ("J1-EXACT", "J2-UNIFORM")
    ]


def evaluate_conjecture_gate(
    claim_id: str,
    evidence_results: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Evaluate result outcomes without ever promoting the conjecture.

    A valid counterexample or proof/CAS failure wins over mere evidence
    presence.  Exact required outcomes make the claim ready only for a
    separate independent adjudication.
    """

    if claim_id not in CONJECTURE_GATE_CONTRACTS:
        raise ValueError(f"unknown premise-anchor conjecture: {claim_id}")
    contract = CONJECTURE_GATE_CONTRACTS[claim_id]
    expected = {
        item["obligation_id"]: item["required_outcome"]
        for item in contract["obligations"]
    }
    observed: dict[str, str] = {}
    for item in evidence_results:
        if not isinstance(item, Mapping):
            raise ValueError("conjecture evidence result must be a mapping")
        obligation_id = item.get("obligation_id")
        outcome = item.get("outcome")
        if obligation_id not in expected:
            raise ValueError(
                f"{claim_id} has unknown evidence obligation: {obligation_id!r}"
            )
        if obligation_id in observed:
            raise ValueError(
                f"{claim_id} has duplicate evidence obligation: {obligation_id}"
            )
        if not isinstance(outcome, str) or not outcome:
            raise ValueError(
                f"{claim_id} evidence outcome must be a nonempty string"
            )
        observed[obligation_id] = outcome

    refuting = sorted(
        obligation_id
        for obligation_id, outcome in observed.items()
        if outcome in contract["refuting_outcomes"]
    )
    if refuting:
        return {
            "claim_id": claim_id,
            "status": REFUTED_OUTCOME,
            "ready": False,
            "refuting_obligations": refuting,
            "missing_obligations": [],
            "invalid_obligations": [],
        }

    missing = sorted(set(expected) - set(observed))
    if missing:
        return {
            "claim_id": claim_id,
            "status": MISSING_OUTCOME,
            "ready": False,
            "refuting_obligations": [],
            "missing_obligations": missing,
            "invalid_obligations": [],
        }

    invalid = sorted(
        obligation_id
        for obligation_id, required_outcome in expected.items()
        if observed[obligation_id] != required_outcome
    )
    if invalid:
        return {
            "claim_id": claim_id,
            "status": INVALID_OUTCOME,
            "ready": False,
            "refuting_obligations": [],
            "missing_obligations": [],
            "invalid_obligations": invalid,
        }

    return {
        "claim_id": claim_id,
        "status": READY_OUTCOME,
        "ready": True,
        "refuting_obligations": [],
        "missing_obligations": [],
        "invalid_obligations": [],
    }


def validate_premise_anchor_intake(payload: Mapping[str, Any]) -> None:
    """Validate that PR-253 input remains non-evidence and fail closed."""

    if payload.get("status") != "PROPOSED_UNVERIFIED_INPUT":
        raise ValueError("premise-anchor intake status must remain unverified")
    if payload.get("evidence_eligible") is not False:
        raise ValueError("premise-anchor intake must remain evidence-ineligible")
    if payload.get("canonical_authority") is not None:
        raise ValueError("premise-anchor intake must not declare authority")

    claim_intake = payload.get("claim_intake")
    if not isinstance(claim_intake, Mapping):
        raise ValueError("premise-anchor claim_intake must be a mapping")
    conjectures = claim_intake.get("conjectures")
    if not isinstance(conjectures, list):
        raise ValueError("premise-anchor conjectures must be a list")
    by_id = {
        item.get("claim_id"): item
        for item in conjectures
        if isinstance(item, Mapping)
    }
    if set(by_id) != set(CONJECTURE_GATE_CONTRACTS):
        raise ValueError("premise-anchor conjecture set drifted")

    for claim_id, contract in CONJECTURE_GATE_CONTRACTS.items():
        item = by_id[claim_id]
        if item.get("owner") != contract["owner"]:
            raise ValueError(f"{claim_id} owner drifted")
        if item.get("status") != "CONJECTURE_COUNTEREXAMPLE_FIRST":
            raise ValueError(f"{claim_id} must remain counterexample-first")
        if item.get("evidence_status") != "NONE":
            raise ValueError(f"{claim_id} intake evidence status must remain NONE")
        if item.get("promotion_blocked") is not True:
            raise ValueError(f"{claim_id} must remain promotion-blocked")
        if item.get("promotion_gate") != contract["promotion_gate"]:
            raise ValueError(f"{claim_id} promotion gate drifted")
        if item.get("gate_contract") != contract:
            raise ValueError(f"{claim_id} outcome-aware gate contract drifted")
        intake_decision = evaluate_conjecture_gate(claim_id, [])
        if item.get("gate_status_on_intake") != intake_decision["status"]:
            raise ValueError(f"{claim_id} intake gate status is not fail-closed")

    numerical = payload.get("numerical_intake")
    if not isinstance(numerical, Mapping):
        raise ValueError("premise-anchor numerical_intake must be a mapping")
    claims = numerical.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("premise-anchor numerical claims must be a nonempty list")
    allowed_fields = {
        "label",
        "quoted_value",
        "target_card",
        "evidence_status",
        "evidence_eligible",
    }
    for item in claims:
        if not isinstance(item, Mapping):
            raise ValueError("quoted numerical claim must be a mapping")
        label = item.get("label")
        if not isinstance(label, str) or not label:
            raise ValueError("quoted numerical claim requires a label")
        extra_fields = sorted(set(item) - allowed_fields)
        if extra_fields:
            raise ValueError(
                f"quoted number {label} has unregistered fields: {extra_fields}"
            )
        if item.get("evidence_status") != "QUOTATION_ONLY":
            raise ValueError(
                f"quoted number {label} must remain quotation-only"
            )
        if item.get("evidence_eligible") is not False:
            raise ValueError(
                f"quoted number {label} must remain evidence-ineligible"
            )
