from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_reproduction import RUNNERS  # noqa: E402
CARD = REPO/"docs/generated/pr227_result_card.json"

def test_eighteen_runners_registered():
    assert len(RUNNERS) == 18

def test_card_verified_independence_open():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["reproduction"]["all_byte_stable"] is True
    assert c["metadata"]["independence_gate"] == "OPEN"
    assert c["terminal"] == "TRACK_I_AUTHOR_REPRODUCTION_VERIFIED_INDEPENDENCE_OPEN"
