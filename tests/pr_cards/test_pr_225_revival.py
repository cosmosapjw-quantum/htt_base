from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_estcov_evalue import hartlap_stress, evalue_anytime  # noqa: E402
CARD = REPO/"docs/generated/pr225_result_card.json"

def test_hartlap_inflation_and_correction():
    h = hartlap_stress()
    assert h["raw_inflated"] and h["corrected_calibrated"]

def test_evalue_markov_and_ville():
    ev = evalue_anytime()
    assert ev["merged_mean_le_one"] and ev["tails_within_markov"] and ev["ville_holds"]

def test_card_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["terminal"] == "ESTCOV_PARTIAL_ID_ANYTIME_EVALUE_CALIBRATED"
