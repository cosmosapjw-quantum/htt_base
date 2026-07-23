"""PR-214 gates: legacy mutation corpus kill matrix + clean surface."""
from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if entry not in sys.path: sys.path.insert(0, entry)
from common.revival_mutation_lab import (  # noqa: E402
    active_surface_clean, bianchi_class_swap_caught, factor_three_w2_caught,
    inactive_occam_caught, local_equals_global_caught)
CARD = REPO/"docs/generated/pr214_result_card.json"

def test_factor_three_w2_caught():
    assert factor_three_w2_caught()

def test_class_swap_is_exactly_vi0_viih():
    assert bianchi_class_swap_caught() == {"VI0", "VIIh"}

def test_inactive_occam_caught():
    assert inactive_occam_caught()

def test_local_equals_global_caught():
    assert local_equals_global_caught()

def test_active_surface_has_no_retired_numbers():
    assert active_surface_clean() == []

def test_card_all_killed_and_stable():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["all_mutations_killed"] is True
    assert c["result"]["active_surface_clean"] is True
    assert c["terminal"] == "LEGACY_MUTATION_CORPUS_ALL_KILLED_ACTIVE_SURFACE_CLEAN"
