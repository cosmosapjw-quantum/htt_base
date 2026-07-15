"""PR-120 regression: the active PR08-006 artifact is quarantine-only."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/pr08_006_joint_artifact.py"
OUT = REPO_ROOT / "docs/generated/pr08_006_joint_artifact.json"
EXPECTED_FINDINGS = {
    "C1-K5-MV-F1",
    "C3-K5-VCORR-ML-F1",
    "N-DATA-CF4-DOWNSTREAM",
}


def _load():
    spec = importlib.util.spec_from_file_location("pr08_006_joint_artifact", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["pr08_006_joint_artifact"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_committed_and_check_passes():
    assert OUT.is_file()
    assert _load().main(["--check"]) == 0


def test_claim_firewall():
    d = json.loads(OUT.read_text())
    assert d["schema"] == "htt.cf4_p0_quarantine_block.v1"
    assert d["owner"] == "COMMON"
    assert d["claim_tier"] == "blocked"
    assert d["status"] == "QUARANTINED_OPEN_FINDINGS"
    assert d["allowed_use"] == "blocked_source_record_only"
    assert d["scientific_effect"] == "none"


def test_blind_sectors_fail_closed_not_zeroed():
    d = json.loads(OUT.read_text())
    assert {row["finding_id"] for row in d["findings"]} == EXPECTED_FINDINGS
    assert all(row["scientific_status"] == "OPEN" for row in d["findings"])
    assert d["replacement_value"] is None
    assert "sectors" not in d
    assert "two_sector_no_go" not in d


def test_no_collapsed_scalar_and_rank_separation():
    d = json.loads(OUT.read_text())
    assert d["implementation_scope"] == "propagation_quarantine_only"
    assert d["replacement_policy"] == (
        "forbidden_without_later_authenticated_adjudication"
    )
    assert "x_C_single_scalar" not in d
    assert "data_rank" not in d
    assert "prior_conditioned_rank" not in d
