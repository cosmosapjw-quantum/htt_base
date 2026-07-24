from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_inactive_evidence import (  # noqa: E402
    inactive_invariance, sympy_mass_seal, duplicate_response_no_preference,
    response_log_bayes_factor)
CARD = REPO/"docs/generated/pr220_result_card.json"

def test_inactive_creates_no_occam():
    inv = inactive_invariance()
    assert inv["inactive_creates_no_occam"] and inv["unnormalized_mutation_caught"]

def test_sympy_mass_seal():
    assert sympy_mass_seal()["seal_pass"]

def test_duplicate_no_preference():
    assert duplicate_response_no_preference()

def test_nonduplicate_response_changes_evidence():
    y = [0.4, -0.1, 0.8, 0.2]
    response = [1.0, 0.5, -0.2, 0.8]
    perturbed = [1.5, 0.5, -0.2, 0.8]
    assert abs(response_log_bayes_factor(y, response, response)) < 1e-12
    assert abs(response_log_bayes_factor(y, response, perturbed)) > 1e-3

def test_card_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["terminal"] == "INACTIVE_INVARIANCE_CERTIFIED_LEGACY_LNB_NEGATIVE_CONTROL"
