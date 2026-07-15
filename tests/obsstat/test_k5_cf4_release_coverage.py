"""PR-120 regression: the active K5 coverage artifact is quarantine-only."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/k5_cf4_release_coverage.py"
OUT = REPO_ROOT / "docs/generated/k5_cf4_release_coverage.json"
CAT = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"


def _load():
    spec = importlib.util.spec_from_file_location("k5_cf4_release_coverage", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["k5_cf4_release_coverage"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_report_is_committed_and_claim_gated():
    assert OUT.is_file()
    d = json.loads(OUT.read_text())
    assert d["schema"] == "htt.cf4_p0_quarantine_block.v1"
    assert d["owner"] == "COMMON"
    assert d["claim_tier"] == "blocked"
    assert d["status"] == "QUARANTINED_OPEN_FINDINGS"
    assert d["allowed_use"] == "blocked_source_record_only"
    assert d["replacement_value"] is None


def test_cosmic_variance_restores_nominal_coverage():
    d = json.loads(OUT.read_text())
    assert "coverage" not in d
    assert "blocker_resolved" not in d
    assert {row["finding_id"] for row in d["findings"]} == {
        "C1-K5-MV-F1",
        "C3-K5-VCORR-ML-F1",
        "N-DATA-CF4-DOWNSTREAM",
    }
    assert all(row["scientific_status"] == "OPEN" for row in d["findings"])


def test_deterministic_against_real_catalogue_when_present():
    if not CAT.is_file():
        return
    mod = _load()
    assert mod.main(["--check"]) == 0
