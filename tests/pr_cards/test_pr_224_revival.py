from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_directional_falsifier import SCALINGS, falsify, no_bulk_equals_divergence, no_h0_percentage_without_scaling  # noqa: E402
CARD = REPO/"docs/generated/pr224_result_card.json"

def test_recovers_and_falsifies():
    f = falsify()
    assert f["recovers_truth"] and f["depth_mode_falsifies_bridge_without_it"]

def test_anti_drift_guards():
    assert no_bulk_equals_divergence() and no_h0_percentage_without_scaling()

def test_bulk_divergence_guard_kills_aliased_responses(monkeypatch):
    monkeypatch.setitem(SCALINGS, "depth_inverse", SCALINGS["constant"])
    assert not no_bulk_equals_divergence()

def test_h0_percentage_requires_declared_depth_scaling():
    assert not no_h0_percentage_without_scaling({"h0_percentage": 7.5})
    assert not no_h0_percentage_without_scaling(
        {"h0_percentage": 7.5, "depth_scaling_law": "post_hoc"}
    )
    assert no_h0_percentage_without_scaling(
        {"h0_percentage": 7.5, "depth_scaling_law": "depth_inverse"}
    )

def test_card_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["terminal"] == "DIRECTIONAL_DEPTH_HOST_FALSIFIER_CERTIFIED"
