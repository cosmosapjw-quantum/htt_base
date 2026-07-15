"""PR-120 gates for the treatment-conditioned CF4 pair-statistic record."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "docs/generated/cf4_velocity_correlation_card.json"
LEGACY = REPO / "legacy/cf4_p0/cards/cf4_velocity_correlation_card.json"


def _card() -> dict:
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_pair_card_retains_only_conditioned_method_mechanics() -> None:
    card = _card()
    artifact = card["artifact"]
    assert card["status"] == "QUARANTINED_OPEN_FINDINGS"
    assert artifact["allowed_use"] == (
        "treatment_conditioned_pair_statistic_and_systematics_design_only"
    )
    assert artifact["observational_numeric_instantiation"]["values"] is None
    assert artifact["observational_numeric_instantiation"]["replacement_value"] is None
    assert "growth_amplitude_measurement" in artifact["forbidden_uses"]
    assert "f_sigma8_constraint" in artifact["forbidden_uses"]
    assert "global_tilt_pushforward" in artifact["forbidden_uses"]
    assert {row["scientific_status"] for row in card["findings"]} == {"OPEN"}


def test_pair_card_has_no_active_estimate_arrays_or_amplitudes() -> None:
    card = _card()
    forbidden_keys = {
        "per_variant",
        "f_sigma8",
        "f_sigma8_jackknife_error",
        "psi_par_data_kms2",
        "psi_perp_data_kms2",
        "cosmic_mach_number",
    }

    def walk(value: object) -> None:
        if isinstance(value, dict):
            assert not (forbidden_keys & set(value))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(card)
    assert LEGACY.is_file()
    assert card["artifact"]["legacy_public_use"] is False


def test_pair_wrapper_is_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/cf4_velocity_correlation.py", "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
