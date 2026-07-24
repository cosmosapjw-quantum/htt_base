"""PR-213 gates: dual-axis claim-state successor + PR-185 cross-ref."""
from __future__ import annotations
import json, sys
from itertools import product
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if entry not in sys.path: sys.path.insert(0, entry)
from common.revival_claim_state import (  # noqa: E402
    AdjudicationReceipt, ClaimState, ClaimStateError, Novelty, Readiness, can_transition)
from scripts.codex_harness import run_pr213_claim_state as runner  # noqa: E402
CARD = REPO/"docs/generated/pr213_result_card.json"

def test_all_novelty_readiness_combos_legal_without_public_use():
    for nov, rd in product(Novelty, Readiness):
        ClaimState(nov, rd, public_use=False).validate()

def test_S_novelty_alone_does_not_open_public_use():
    with pytest.raises(ClaimStateError):
        ClaimState(Novelty.S, Readiness.OPEN, public_use=True).validate()

def test_validated_requires_valid_receipt():
    with pytest.raises(ClaimStateError):
        ClaimState(Novelty.S, Readiness.VALIDATED, public_use=True).validate()

def test_author_equals_adjudicator_rejected():
    with pytest.raises(ClaimStateError):
        ClaimState(Novelty.P, Readiness.VALIDATED, public_use=True,
                   receipt=AdjudicationReceipt("A","A","l",True)).validate()

def test_self_asserted_signed_receipt_cannot_open_public_use():
    with pytest.raises(ClaimStateError, match="authenticated external"):
        ClaimState(
            Novelty.S,
            Readiness.VALIDATED,
            public_use=True,
            receipt=AdjudicationReceipt("A", "B", "l", True),
        ).validate()

def test_forward_only_ladder():
    assert can_transition(Readiness.EVIDENCE_READY, Readiness.ADJUDICATION_PENDING)
    assert not can_transition(Readiness.VALIDATED, Readiness.OPEN)

def test_current_runner_stays_blocked_without_authenticated_receipt():
    payload = runner.build_payload()
    assert payload["result"]["kill_battery"]["legal_public_use_accepted"] is False
    assert payload["terminal"] == "BLOCKED_CLAIM_STATE_GATE_FAILURE"

def test_historical_card_preserves_pre_ma04_terminal():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["terminal"] == "DUAL_AXIS_SUCCESSOR_CERTIFIED_PR185_CONSISTENT"
    assert c["result"]["pr185_crossref"]["kill_battery_all_caught"] is True
