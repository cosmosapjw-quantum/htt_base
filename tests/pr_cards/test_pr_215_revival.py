from __future__ import annotations
import json, sys
from fractions import Fraction as Fr
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_joint_comparator import analysis, joint_interval_exact, product_box_interval_exact, grid_joint_interval  # noqa: E402
CARD = REPO/"docs/generated/pr215_result_card.json"

def test_joint_strictly_narrower_than_box():
    a = analysis()
    assert a["strictly_narrower"] and a["joint_subset_of_product"]

def test_exact_joint_is_8_to_10_hundredths():
    lo, hi = joint_interval_exact()
    assert lo == Fr(8,100) and hi == Fr(10,100)

def test_product_box_is_wider():
    plo, phi = product_box_interval_exact()
    assert phi - plo == Fr(1,10)  # exact box from manifold component ranges

def test_grid_agrees_with_exact():
    lo, hi = joint_interval_exact(); glo, ghi = grid_joint_interval()
    assert abs(glo-float(lo))<1e-9 and abs(ghi-float(hi))<1e-9

def test_card_check_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["pr189_crossref"]["pr189_cas"] == "CAS_5AXIS_PASS"
    assert c["terminal"] == "JOINT_COMPARATOR_STRICTLY_NARROWER_PR189_CERTIFIED"
