"""PR-120 regression: the active CF4 ML shape-correction lane is blocked."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/cf4_velocity_correlation_ml.py"
OUT = REPO / "docs/generated/cf4_velocity_correlation_ml_card.json"
LEGACY = REPO / "legacy/cf4_p0/cards/cf4_velocity_correlation_ml_card.json"


def _load():
    spec = importlib.util.spec_from_file_location("active_cf4_ml", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["active_cf4_ml"] = module
    spec.loader.exec_module(module)
    return module


def test_active_card_is_canonical_open_finding_block():
    card = json.loads(OUT.read_text())
    assert card["status"] == "QUARANTINED_OPEN_FINDINGS"
    assert card["claim_tier"] == "blocked"
    assert card["replacement_value"] is None
    assert card["artifact"]["artifact_id"] == "cf4_velocity_correlation_ml_card"
    assert card["artifact"]["legacy_public_use"] is False
    assert {row["scientific_status"] for row in card["findings"]} == {"OPEN"}


def test_active_producer_exposes_block_only_and_is_current():
    module = _load()
    card = module.measure()
    assert card == json.loads(OUT.read_text())
    assert "shape_correction_pk_corr" not in card
    assert "per_variant" not in card
    assert module.main(["--check"]) == 0


def test_exact_legacy_ml_card_is_preserved_off_public_path():
    legacy = json.loads(LEGACY.read_text())
    assert legacy["status"] == "MEASURED_ML_FSIGMA8"
    assert "shape_correction_pk_corr" in legacy
