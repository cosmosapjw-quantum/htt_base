from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_response_quotient import (  # noqa: E402
    LABELS, SCALAR, ENLARGED, quotient, quotient_via_nullspace, rank_lattice, reopening_requirement)
CARD = REPO/"docs/generated/pr219_result_card.json"

def test_scalar_quotient_merges_three_families():
    assert quotient(LABELS, SCALAR) == (("BI","BV","BVIIh"),("FLRW_tilt",))

def test_enlarged_quotient_is_four_singletons():
    assert len(quotient(LABELS, ENLARGED)) == 4

def test_rank_lattice_2_3_4():
    assert rank_lattice() == [2,3,4]

def test_two_lineages_agree():
    a = quotient(LABELS, SCALAR); b = quotient_via_nullspace(LABELS, SCALAR)
    assert set(map(frozenset,a)) == set(map(frozenset,b))

def test_reopening_to_singletons():
    assert reopening_requirement()["reopened_to_singletons"]

def test_card_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["pr127_kernel_rank"] == 2
    assert c["terminal"] == "RESPONSE_QUOTIENT_ATLAS_CERTIFIED_PR127_CONSISTENT"
