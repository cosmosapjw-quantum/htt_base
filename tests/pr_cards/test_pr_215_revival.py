from __future__ import annotations
import json, sys
from fractions import Fraction as Fr
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_joint_comparator import analysis, joint_interval_exact, product_box_interval_exact, grid_joint_interval  # noqa: E402
from scripts.codex_harness import run_pr215_joint as runner  # noqa: E402
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

def test_stored_pr189_cas_results_are_diagnostic_only():
    xref = runner._xref()
    assert xref["stored_cas_diagnostic_only"] is True
    assert xref["pr189_cas"] == "CAS_BLOCKED"
    assert runner.build_payload()["terminal"] == "BLOCKED_JOINT_GATE_FAILURE"

def test_historical_card_preserves_pre_ma04_five_axis_label():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["pr189_crossref"]["pr189_cas"] == "CAS_5AXIS_PASS"
    assert c["terminal"] == "JOINT_COMPARATOR_STRICTLY_NARROWER_PR189_CERTIFIED"
