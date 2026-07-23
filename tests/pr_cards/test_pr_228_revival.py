from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
CARD = REPO/"docs/generated/pr228_result_card.json"
REPORT = REPO/"docs/generated/revival_v11i_report.md"

def test_report_no_open_p0_no_trackii():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["no_open_p0"] and not c["result"]["track_ii_claims_present"]
    assert c["result"]["n_propositions"] == 19
    assert c["terminal"] == "TRACK_I_V11I_REPORT_EVIDENCE_READY_VALIDATED_DEFERRED"

def test_report_has_no_meta_dev_tokens():
    if not REPORT.exists(): pytest.skip("report")
    text = REPORT.read_text().lower()
    for banned in ["subagent", "adversarial audit", "claim-gate", "auditor", "checkpoint cp-", "mutation kill matrix"]:
        assert banned not in text, banned
