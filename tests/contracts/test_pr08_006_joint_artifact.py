"""Contract: the PR08-006 joint artifact obeys the ticket's claim discipline.

Only identified sectors enter the pushforward; blind sectors are explicit and
fail-closed (never zeroed); data rank is reported separately from
prior-conditioned rank; no MIO-as-odds; no scalar-to-family promotion.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/pr08_006_joint_artifact.py"
OUT = REPO_ROOT / "docs/generated/pr08_006_joint_artifact.json"


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
    assert d["family_identification"] is False
    assert d["native_solver_result"] is False
    assert d["mio_as_odds"] is False
    assert d["scalar_to_family_promotion"] is False


def test_blind_sectors_fail_closed_not_zeroed():
    d = json.loads(OUT.read_text())
    blind = d["two_sector_no_go"]["blind_sectors"]
    assert set(blind) == {"W2", "Omega_k"}
    for s in blind:
        sec = d["sectors"][s]
        assert sec["status"].startswith("fail_closed")
        # fail-closed must NOT be a zero value masquerading as a measurement
        assert "value_kms" not in sec or sec.get("value_kms") is None


def test_no_collapsed_scalar_and_rank_separation():
    d = json.loads(OUT.read_text())
    assert d["x_C_single_scalar"] is None          # not collapsed over blind sectors
    assert d["data_rank"]["data_rank_count"] == 2   # Omega_tilt measured + Sigma2 partial
    assert "Omega_tilt" in d["data_rank"]["reachable_full"]
    assert "Sigma2" in d["data_rank"]["reachable_partial"]
    # data rank and prior-conditioned rank are reported separately
    assert "data_rank" in d and "prior_conditioned_rank" in d
