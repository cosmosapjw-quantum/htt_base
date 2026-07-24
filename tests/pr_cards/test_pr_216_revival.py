from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_sharpness_ladder import (  # noqa: E402
    SharpnessError, SharpnessLadder, build_certified_ladder, homogeneous_momentum_constraint_residual)
CARD = REPO/"docs/generated/pr216_result_card.json"

def test_certified_ladder_global_blocked():
    s = build_certified_ladder().snapshot()
    assert s["algebraic"]["status"] == "ATTAINED"
    assert s["global"]["status"] == "BLOCKED"

def test_cannot_skip_stages():
    L = SharpnessLadder()
    with pytest.raises(SharpnessError):
        L.auto_promote_global_from_algebraic()

def test_caller_evidence_cannot_overwrite_global_block():
    L = build_certified_ladder()
    with pytest.raises(SharpnessError, match="native solver"):
        L.attain("global", "ATTAINED", "caller supplied evidence")
    assert L.snapshot()["global"]["status"] == "BLOCKED"

def test_constraint_residual_exactly_zero():
    assert homogeneous_momentum_constraint_residual() == 0

def test_local_before_constraint_refused():
    L = SharpnessLadder()
    L.attain("algebraic","ATTAINED","x")
    with pytest.raises(SharpnessError):
        L.attain("local","ATTAINED","skipped constraint")

def test_card_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["terminal"] == "SHARPNESS_LADDER_STAGED_GLOBAL_BLOCKED_WITH_OBLIGATION"
