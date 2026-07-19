"""Canonical PR-167 card, dependency, lane, and claim-ceiling assertions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[2]


def _yaml(relative: str) -> dict:
    payload = yaml.safe_load((REPO / relative).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_advocate_suffix_is_complete_typed_and_non_promoting() -> None:
    backlog = _yaml("docs/codex_handoff/pr_backlog.yaml")
    status = _yaml("docs/codex_handoff/pr_status.yaml")
    cards = {card["id"]: card for card in backlog["prs"]}
    advocate_ids = [f"PR-{number:03d}" for number in range(167, 184)]
    assert [card["id"] for card in backlog["prs"][-17:]] == advocate_ids
    assert set(status["execution_lane"]) == set(advocate_ids)
    assert status["execution_lane"]["PR-171"] == "defensible"
    assert status["execution_lane"]["PR-174"] == "hypothesis_only"
    assert status["execution_lane"]["PR-175"] == "hypothesis_only"
    assert status["execution_lane"]["PR-182"] == "hypothesis_only"
    assert status["execution_lane"]["PR-183"] == "needs_native"
    assert cards["PR-183"]["activation_state"] == "NEEDS_NATIVE"
    assert cards["PR-171"]["scientific_artifact_mode"] == "hypothesis_only"
    assert cards["PR-171"]["execution_authorization"] == "EXPLICIT_APPROVED_SEQUENCE"
    assert cards["PR-174"]["execution_authorization"] == "REGISTERED_NOT_SCHEDULED"
    assert cards["PR-183"]["execution_authorization"] == "NATIVE_BLOCKED"
    assert all(cards[pr_id]["public_use"] is False for pr_id in advocate_ids)
    assert all(cards[pr_id]["scientific_status_on_intake"] == "OPEN" for pr_id in advocate_ids)


def test_required_dependency_hardening_is_canonical() -> None:
    cards = {
        card["id"]: card
        for card in _yaml("docs/codex_handoff/pr_backlog.yaml")["prs"]
    }
    assert cards["PR-176"]["depends"] == [
        "PR-133", "PR-144", "PR-146", "PR-148", "PR-167", "PR-173"
    ]
    assert cards["PR-177"]["depends"] == ["PR-152", "PR-167", "PR-173"]
    assert cards["PR-179"]["depends"] == [
        "PR-134", "PR-135", "PR-139", "PR-144", "PR-167", "PR-173"
    ]
    assert cards["PR-180"]["depends"] == [
        "PR-134", "PR-149", "PR-150", "PR-167", "PR-172", "PR-173"
    ]
    assert cards["PR-181"]["depends"] == [
        "PR-140", "PR-141", "PR-143", "PR-155", "PR-167", "PR-173"
    ]
    assert cards["PR-178"]["depends"] == [
        "PR-151", "PR-155", "PR-156", "PR-157", "PR-158", "PR-167"
    ]
    assert cards["PR-178"]["dependency_contracts"][0]["mode"] == "requires_terminal_receipt"


def test_theory_cards_require_blind_four_axis_cas() -> None:
    cards = {
        card["id"]: card
        for card in _yaml("docs/codex_handoff/pr_backlog.yaml")["prs"]
    }
    for pr_id in ("PR-168", "PR-169", "PR-170", "PR-171", "PR-175", "PR-182"):
        assert cards[pr_id]["cas_contract"] == {
            "schema": "htt.cas_contract.v2",
            "required_axes": [
                "wolfram_xact",
                "sympy_high_precision",
                "sage_singular",
                "lean_mathlib",
            ],
            "missing_axis_outcome": "CAS_BLOCKED",
            "result_blinding": "required_until_adjudication",
        }
        prose = json.dumps(cards[pr_id], ensure_ascii=False).lower()
        assert "dual-engine" not in prose
        assert "두 engine" not in prose


def test_preservation_and_four_axis_acceptance_prose_matches_typed_contract() -> None:
    cards = {
        card["id"]: card
        for card in _yaml("docs/codex_handoff/pr_backlog.yaml")["prs"]
    }
    pr167 = json.dumps(cards["PR-167"], ensure_ascii=False)
    assert "every canonical PR-000--166 card (expected count 113)" in pr167
    assert "65개 원 상태" not in pr167
    assert "blind four-axis identity seal" in json.dumps(
        cards["PR-170"], ensure_ascii=False
    )
    assert "all four registered CAS axes" in json.dumps(
        cards["PR-175"], ensure_ascii=False
    )


def test_mandatory_claim_downclaims_are_present() -> None:
    cards = {
        card["id"]: card
        for card in _yaml("docs/codex_handoff/pr_backlog.yaml")["prs"]
    }
    prose = {
        pr_id: json.dumps(card, ensure_ascii=False).lower()
        for pr_id, card in cards.items()
    }
    assert "numerically unresolved at the current monte carlo budget" in prose["PR-173"]
    assert "structurally distinct from monopole leakage" in prose["PR-176"]
    assert "act-release-simulation-conditional modulation candidate or null" in prose["PR-177"]
    assert "not raw-qe reproduction" in prose["PR-177"]
    assert "selection/systematics-conditional raw-catalogue directional statistic" in prose["PR-179"]
    assert "consistency with a pure boost" in prose["PR-180"]
    assert "never confirmation" in prose["PR-180"]
    assert cards["PR-177"]["title"] == (
        "ACT DR6 in-band kappa off-diagonal modulation diagnostic "
        "(release-simulation-conditional)"
    )
    assert "future native-atlas" in prose["PR-182"]
    assert "no proxy" in prose["PR-183"]


def test_legacy_intake_owner_is_byte_preserved_and_still_forbids_advocate_write() -> None:
    legacy = REPO / "scripts/codex_harness/intake_long_horizon_roadmap.py"
    assert hashlib.sha256(legacy.read_bytes()).hexdigest() == (
        "d18114aedb9e33d6495ba214c95c5b62283cf02a14f10441878b9da9bbb8cde9"
    )
    source = legacy.read_text(encoding="utf-8")
    assert "deliberately refuses" in source
    assert "forbidden PR-167..PR-183 already present" in source
