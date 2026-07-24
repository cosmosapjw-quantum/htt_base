from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_teff_surrogate import certify, overlapping_split_is_a_defect, split_rows_overlap  # noqa: E402
CARD = REPO/"docs/generated/pr218_result_card.json"

def test_envelope_holds_on_independent_test():
    c = certify()
    assert c["held_out_envelope_holds"] and c["test_violations"] == 0

def test_out_of_domain_rejected():
    assert certify()["out_of_domain_rejected"]

def test_no_native_no_inference():
    assert certify()["authorizes_inference"] is False

def test_overlapping_split_flagged():
    assert overlapping_split_is_a_defect()

def test_copied_and_partial_row_overlap_flagged():
    train = [[0.0, 0.1, 0.2], [1.0, 1.1, 1.2]]
    assert split_rows_overlap(train, [train[0]])
    assert split_rows_overlap(train, [[-0.0, 0.1, 0.2]])
    assert not split_rows_overlap(train, [[2.0, 2.1, 2.2]])
    with pytest.raises(ValueError):
        split_rows_overlap(train, [[0.0, 0.1]])

def test_card_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["certificate"]["authorizes_inference"] is False
    assert c["terminal"] == "TEFF_SURROGATE_CERTIFIED_METHODOLOGY_INFERENCE_WITHHELD_NO_NATIVE"
