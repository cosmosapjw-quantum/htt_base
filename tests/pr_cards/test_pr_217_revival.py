from __future__ import annotations
import json, sys
from pathlib import Path
import pytest
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.revival_mes_attribution import (  # noqa: E402
    FROZEN_W2_MAX, GEODESIC_SAG, NON_GEODESIC_UNSOURCED, attribution_surface,
    MES_AUTHORITY_BRANCHES, coefficient_is_live_ceiling,
    epsilon1_zero_is_branch_choice_not_uniqueness)
CARD = REPO/"docs/generated/pr217_result_card.json"

def test_zero_endpoint_matches_frozen_anchor_exactly():
    s = attribution_surface()
    assert s["W2_intrinsic_zero"] == FROZEN_W2_MAX
    assert s["endpoint_matches_frozen_anchor"]

def test_full_dipole_excluded_by_hierarchy():
    s = attribution_surface()
    assert s["zero_admissible"] and not s["full_dipole_admissible"]

def test_sourced_vs_unsourced_ceiling():
    assert coefficient_is_live_ceiling(GEODESIC_SAG)
    assert not coefficient_is_live_ceiling(NON_GEODESIC_UNSOURCED)

def test_status_string_cannot_self_authorize_a_live_ceiling():
    assert not coefficient_is_live_ceiling(
        {"source_status": "accessible_primary_source_reduction"}
    )

def test_sourced_branch_rejects_swapped_coefficients():
    branch = dict(GEODESIC_SAG)
    branch["omega"] = NON_GEODESIC_UNSOURCED["omega"]
    assert not coefficient_is_live_ceiling(branch)

def test_live_ceiling_requires_authority_source_equations(monkeypatch):
    authority = MES_AUTHORITY_BRANCHES["MES_G_OMEGA"]
    sources = [dict(source, equation="") for source in authority["sources"]]
    monkeypatch.setitem(authority, "sources", sources)
    assert not coefficient_is_live_ceiling(GEODESIC_SAG)

def test_epsilon1_zero_is_a_choice_not_uniqueness():
    assert epsilon1_zero_is_branch_choice_not_uniqueness()

def test_card_stable_frozen_safe():
    if not CARD.exists(): pytest.skip("card")
    c = json.loads(CARD.read_text())
    assert c["result"]["frozen_anchor_consistent"] is True
    assert c["result"]["pr186_frozen_W2_max"] == FROZEN_W2_MAX
    assert c["terminal"] == "MES_ATTRIBUTION_SURFACE_FROZEN_ANCHORED_HIERARCHY_EXCLUDES_FULL_DIPOLE"
