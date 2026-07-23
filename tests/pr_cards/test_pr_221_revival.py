from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_dipole_discrimination import run  # noqa: E402
CARD = REPO/"docs/generated/pr221_result_card.json"

def test_discrimination_gate():
    r = run()
    assert r["gate_pass"]
    assert r["scenario_results"]["confusable_weak"]["abstain_rate"] > 0.95
    assert r["scenario_results"]["superposition"]["correct_rate"] > 0.94

def test_card_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["terminal"] == "DIPOLE_SOURCE_DISCRIMINATION_WITH_MANDATORY_ABSTENTION"
