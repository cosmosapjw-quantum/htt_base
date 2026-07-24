from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
import common.revival_data_lane_closure as data_lane  # noqa: E402
from common.revival_data_lane_closure import closure_summary, pr151_is_terminal  # noqa: E402
CARD = REPO/"docs/generated/pr226_result_card.json"

def test_three_lanes_closed():
    s = closure_summary()
    assert set(s["closed_lanes"]) >= {"planck_k1","cf4","act"}

@pytest.mark.parametrize("lane", sorted(data_lane.LANE_RECEIPTS))
def test_lane_requires_complete_receipt_set(tmp_path, monkeypatch, lane):
    monkeypatch.setattr(data_lane, "GEN", tmp_path)
    required = data_lane.LANE_RECEIPTS[lane]
    (tmp_path / required[0]).touch()
    assert data_lane.lane_closure()[lane]["status"] == "BLOCKED_MISSING_RECEIPT"

def test_desi_blocked_on_pr151():
    s = closure_summary()
    assert s["desi_blocked_on_pr151"]
    assert not pr151_is_terminal()  # PR-151 still acquiring

def test_no_partial_mock_in_headline():
    assert closure_summary()["headline_discipline_ok"]

def test_card_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["terminal"] == "DATA_LANE_CLOSURE_PARTIAL_THREE_LANES_CLOSED_DESI_BLOCKED_ON_PR151"
    assert c["metadata"]["desi_official_mock_lane"] == "BLOCKED_ON_PR151_TERMINAL"
