"""Regression: K6 CF4 curl/vorticity discharge on the real WF field.

Validates the structural-no-go outcome and the claim firewall. The script is
deterministic; if the CF4++ grid is present it must reproduce the committed JSON.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/k6_cf4_curl_posterior.py"
OUT = REPO_ROOT / "docs/generated/k6_cf4_curl_posterior.json"
GRID = REPO_ROOT / "workdir/raw/cf4/CF4pp_mean_std_grids.npz"


def _load():
    spec = importlib.util.spec_from_file_location("k6_cf4_curl_posterior", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["k6_cf4_curl_posterior"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_report_is_committed_and_claim_gated():
    assert OUT.is_file()
    d = json.loads(OUT.read_text())
    assert d["family_identification"] is False
    assert d["native_solver_result"] is False
    assert d["claim_tier"] == "diagnostic_only"
    assert d["blocker_resolved"] == "BLOCKED_MISSING_FIELD_REALIZATIONS"


def test_structural_no_go_with_live_curl_channel():
    d = json.loads(OUT.read_text())
    # the WF field is curl-suppressed (vorticity << shear) ...
    assert d["vorticity_over_shear_ratio_max"] < 0.2
    assert d["structural_no_go"] is True
    # ... but the estimator's curl channel is validated (injection recovered)
    assert d["curl_injection_validated"] is True
    for radius in d["per_radius"].values():
        assert radius["curl_injection_rel_error"] < 1e-6
        assert radius["wf_mean_vorticity_amplitude"] < radius["wf_mean_shear_amplitude"]


def test_deterministic_against_real_grid_when_present():
    if not GRID.is_file():
        return  # grid is outside git; skip when absent
    mod = _load()
    assert mod.main(["--check"]) == 0
