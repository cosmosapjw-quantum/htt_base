from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from scripts.codex_harness.premise_anchor_gates import (
    READY_OUTCOME,
    REFUTED_OUTCOME,
    evaluate_conjecture_gate,
    validate_premise_anchor_intake,
)
from scripts.codex_harness.validate_pr_dag import (
    PREMISE_ANCHOR_DEPENDENCY_OVERLAY,
    validate_backlog,
    validate_long_horizon_rescue_slice,
)


ROOT = Path(__file__).resolve().parents[2]
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
INTAKE = (
    ROOT
    / "docs/research_program/premise_anchor/pr253_input_intake.yaml"
)


def _load(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _strict_validate(backlog: dict, status: dict) -> None:
    validate_long_horizon_rescue_slice(
        backlog,
        validate_backlog(backlog),
        status=status,
    )


def test_registered_premise_anchor_slice_is_atomic_and_status_bound() -> None:
    backlog = _load(BACKLOG)
    status = _load(STATUS)

    _strict_validate(backlog, status)
    cards = {card["id"]: card for card in backlog["prs"]}
    assert set(cards).issuperset({f"PR-{index}" for index in range(253, 259)})
    assert backlog["policy"]["dependency_overlays"] == (
        PREMISE_ANCHOR_DEPENDENCY_OVERLAY
    )
    assert status["in_progress"] == "PR-253"
    assert status["background_execution_contracts"]["PR-151"] == {
        "kind": "acquisition",
        "allowed_phase": "acquire",
        "partial_scientific_use": "forbidden",
    }


def test_missing_premise_anchor_card_kills_atomic_intake() -> None:
    backlog = _load(BACKLOG)
    status = _load(STATUS)
    mutated = copy.deepcopy(backlog)
    mutated["prs"] = [
        card for card in mutated["prs"] if card["id"] != "PR-258"
    ]
    mutated["policy"]["topological_order"].remove("PR-258")

    with pytest.raises(ValueError, match="premise-anchor intake must be atomic"):
        _strict_validate(mutated, status)


def test_overlay_cannot_be_retroactively_attributed_to_pr248() -> None:
    backlog = _load(BACKLOG)
    status = _load(STATUS)
    mutated = copy.deepcopy(backlog)
    mutated["policy"]["dependency_overlays"]["authority"] = "PR-248"

    with pytest.raises(
        ValueError,
        match="premise-anchor dependency overlay drifted",
    ):
        _strict_validate(mutated, status)


def test_new_card_dependency_contract_is_fail_closed() -> None:
    backlog = _load(BACKLOG)
    status = _load(STATUS)
    mutated = copy.deepcopy(backlog)
    card = next(card for card in mutated["prs"] if card["id"] == "PR-256")
    card["depends"] = ["PR-255", "PR-251"]
    card["dependency_contracts"] = [
        {"upstream_id": dependency, "mode": "requires_success"}
        for dependency in card["depends"]
    ]

    with pytest.raises(ValueError, match="PR-256 dependencies drifted"):
        _strict_validate(mutated, status)


def test_methodology_inputs_and_quoted_numbers_are_not_evidence() -> None:
    intake = _load(INTAKE)
    conjectures = intake["claim_intake"]["conjectures"]

    assert intake["status"] == "PROPOSED_UNVERIFIED_INPUT"
    assert intake["evidence_eligible"] is False
    assert intake["canonical_authority"] is None
    assert len(intake["sources"]) == 5
    assert all(
        source["disposition"]
        in {
            "PROPOSED_UNVERIFIED_INPUT",
            "PROPOSED_REQUIRES_CLAIM_REPAIR",
            "WITHHELD_UNTIL_PR258",
        }
        for source in intake["sources"]
    )
    assert all(
        conjecture["promotion_blocked"] is True
        for conjecture in conjectures
    )
    assert {conjecture["owner"] for conjecture in conjectures} == {
        "COMMON",
        "HTT",
    }
    assert all(conjecture["evidence_status"] == "NONE" for conjecture in conjectures)
    assert all(conjecture["evidence_required"] for conjecture in conjectures)
    assert len({conjecture["promotion_gate"] for conjecture in conjectures}) == 2
    assert all(
        conjecture["gate_status_on_intake"] == "BLOCKED_MISSING_EVIDENCE"
        for conjecture in conjectures
    )
    assert all(
        conjecture["gate_contract"]["gate_evaluator"].endswith(
            "premise_anchor_gates.py:evaluate_conjecture_gate"
        )
        for conjecture in conjectures
    )
    assert intake["numerical_intake"]["policy"].startswith(
        "Every value below is quotation-only"
    )
    assert all(
        item["evidence_status"] == "QUOTATION_ONLY"
        and item["evidence_eligible"] is False
        for item in intake["numerical_intake"]["claims"]
    )
    validate_premise_anchor_intake(intake)


def test_j1_j2_claim_gates_cannot_collapse_to_one_owner() -> None:
    backlog = _load(BACKLOG)
    status = _load(STATUS)
    mutated = copy.deepcopy(backlog)
    card = next(card for card in mutated["prs"] if card["id"] == "PR-254")
    j2 = next(
        contract
        for contract in card["claim_contracts"]
        if contract["claim_id"] == "J2-UNIFORM"
    )
    j2["owner"] = "COMMON"

    with pytest.raises(
        ValueError,
        match="PR-254 conjecture claim contracts drifted",
    ):
        _strict_validate(mutated, status)


def test_pr255_scalar_information_gain_is_compatibility_only() -> None:
    backlog = _load(BACKLOG)
    card = next(card for card in backlog["prs"] if card["id"] == "PR-255")
    done_text = " ".join(card["dod"])

    assert "compatibility view only" in done_text
    assert "anchor scaling alone is never information gain" in done_text


def test_quoted_number_cannot_be_promoted_inside_unverified_intake() -> None:
    mutated = copy.deepcopy(_load(INTAKE))
    mutated["numerical_intake"]["claims"][0]["evidence_status"] = "VALIDATED"

    with pytest.raises(ValueError, match="must remain quotation-only"):
        validate_premise_anchor_intake(mutated)


def test_j1_uniqueness_obligation_cannot_be_removed() -> None:
    mutated = copy.deepcopy(_load(INTAKE))
    j1 = next(
        item
        for item in mutated["claim_intake"]["conjectures"]
        if item["claim_id"] == "J1-EXACT"
    )
    j1["gate_contract"]["obligations"] = [
        obligation
        for obligation in j1["gate_contract"]["obligations"]
        if obligation["obligation_id"] != "ESSENTIAL_UNIQUENESS_PROOF"
    ]

    with pytest.raises(
        ValueError,
        match="J1-EXACT outcome-aware gate contract drifted",
    ):
        validate_premise_anchor_intake(mutated)


def test_j2_counterexample_refutes_instead_of_satisfying_gate() -> None:
    decision = evaluate_conjecture_gate(
        "J2-UNIFORM",
        [
            {"obligation_id": "JOINT_NUMERATOR_ANCHOR_LAW", "outcome": "PASS"},
            {
                "obligation_id": "FINITE_SAMPLE_UNIFORM_VALIDITY_PROOF",
                "outcome": "COUNTEREXAMPLE_FOUND",
            },
            {"obligation_id": "INDEPENDENT_COVERAGE_ORACLE", "outcome": "PASS"},
            {
                "obligation_id": "COUNTEREXAMPLE_ADJUDICATION",
                "outcome": "VALID_COUNTEREXAMPLE",
            },
        ],
    )

    assert decision["status"] == REFUTED_OUTCOME
    assert decision["ready"] is False


def test_j1_all_passes_only_reaches_independent_adjudication() -> None:
    decision = evaluate_conjecture_gate(
        "J1-EXACT",
        [
            {"obligation_id": "PHYSICAL_SET_EQUALITY_PROOF", "outcome": "PASS"},
            {"obligation_id": "ESSENTIAL_UNIQUENESS_PROOF", "outcome": "PASS"},
            {"obligation_id": "FOUR_AXIS_CAS", "outcome": "CAS_4AXIS_PASS"},
            {
                "obligation_id": "COUNTEREXAMPLE_ADJUDICATION",
                "outcome": "NO_VALID_COUNTEREXAMPLE",
            },
        ],
    )

    assert decision["status"] == READY_OUTCOME
    assert decision["ready"] is True
    assert "PROMOT" not in decision["status"]
