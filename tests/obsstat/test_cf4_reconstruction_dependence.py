"""PR-120 gates for the reconstruction-conditioned CF4 method record."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs/generated/cf4_reconstruction_dependence_card.json"
LEGACY = REPO / "legacy/cf4_p0/cards/cf4_reconstruction_dependence_card.json"


def _card() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_reconstruction_card_is_method_only_and_blocked() -> None:
    card = _card()
    artifact = card["artifact"]
    assert card["status"] == "QUARANTINED_OPEN_FINDINGS"
    assert card["claim_tier"] == "blocked"
    assert artifact["allowed_use"] == (
        "reconstruction_conditioned_method_and_systematics_design_only"
    )
    assert artifact["observational_numeric_instantiation"]["values"] is None
    assert artifact["observational_numeric_instantiation"]["replacement_value"] is None
    assert "bulk_flow_amplitude_measurement" in artifact["forbidden_uses"]
    assert "apex_measurement" in artifact["forbidden_uses"]
    assert "global_tilt_pushforward" in artifact["forbidden_uses"]
    assert {row["scientific_status"] for row in card["findings"]} == {"OPEN"}


def test_exact_historical_reconstruction_card_is_legacy_only() -> None:
    assert LEGACY.is_file()
    card = _card()
    assert card["artifact"]["legacy_reproduction_only"] == [
        "legacy/cf4_p0/cards/cf4_reconstruction_dependence_card.json"
    ]
    assert card["artifact"]["legacy_public_use"] is False


def test_reconstruction_wrapper_is_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/cf4_reconstruction_dependence.py", "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
