"""Regression: K1 global look-elsewhere max-scan on the real Planck low-ell map.

Property-tests the committed JSON (the 2000-null recomputation is deterministic
by seed but too slow for CI; the seed + config hash pin reproducibility).
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / "docs/generated/k1_global_maxscan.json"


def test_report_is_committed_and_claim_gated():
    assert OUT.is_file()
    d = json.loads(OUT.read_text())
    assert d["family_identification"] is False
    assert d["native_solver_result"] is False
    assert d["claim_tier"] == "diagnostic_only"
    # partial discharge: look-elsewhere done, E2E null still blocked + documented
    assert d["blocker_partial"] == "BLOCKED_MISSING_PR4_E2E_ACCESS"
    assert "E2E" in d["blocker_partial_note"] or "e2e" in d["blocker_partial_note"].lower()


def test_global_p_is_a_valid_look_elsewhere_pvalue():
    d = json.loads(OUT.read_text())
    for method in ("smica", "commander"):
        gp = d[method]["global_p"]
        assert 0.0 < gp <= 1.0
    # global (look-elsewhere) p must not be smaller than the best single local p
    smica = d["smica"]
    assert smica["global_p"] >= min(smica["local_p"].values())
    # the registered statistics are all present
    assert set(d["statistics"]) == set(smica["local_p"])


def test_null_is_labelled_idealised_not_e2e():
    d = json.loads(OUT.read_text())
    assert d["config"]["null_model"] == "isotropic_lambdacdm_grf"
    joined = " ".join(d["caveats"]).lower()
    assert "ffp10" in joined or "e2e" in joined or "end-to-end" in joined
