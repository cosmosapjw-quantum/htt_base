"""PR-120 claim boundary for the retained JWST-to-CF4 catalogue linkage."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def test_jwst_cf4_anchor_artifact_is_catalogue_linkage_only() -> None:
    payload = json.loads(
        (REPO / "docs/generated/jwst_cf4_anchors.json").read_text(encoding="utf-8")
    )
    assert payload["status"] == "matched_catalogue_linkage_only"
    assert payload["allowed_use"] == "catalogue_linkage_and_anchor_error_metadata_only"
    assert payload["finding_state"] == {
        "canonical_source": "docs/generated/cf4_p0_quarantine_block.json",
        "finding_id": "N-DATA-CF4-DOWNSTREAM",
        "scientific_status": "OPEN",
    }
    forecast = payload["downstream_global_tilt_forecast"]
    assert forecast["status"] == "QUARANTINED_OPEN_FINDING"
    assert forecast["value"] is None
    assert forecast["replacement_value"] is None
    assert forecast["public_use"] is False
    assert payload["anchors"]  # identity/error rows remain available


def test_jwst_cf4_generator_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/jwst_cf4_crossmatch.py", "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
