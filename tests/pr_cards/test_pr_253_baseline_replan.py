from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

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
        for conjecture in intake["claim_intake"]["conjectures"]
    )
    assert intake["numerical_intake"]["policy"].startswith(
        "Every value below is quotation-only"
    )
