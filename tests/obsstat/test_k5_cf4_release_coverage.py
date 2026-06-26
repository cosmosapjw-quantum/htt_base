"""Regression: K5 CF4 release-matched cosmic-variance coverage on the real catalogue.

Validates that the cosmic-variance-inclusive coverage is nominal while the
measurement-noise-only coverage under-covers, and the claim firewall.
"""
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
    assert d["family_identification"] is False
    assert d["native_solver_result"] is False
    assert d["claim_tier"] == "diagnostic_only"
    assert d["blocker_resolved"] == "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP"


def test_cosmic_variance_restores_nominal_coverage():
    d = json.loads(OUT.read_text())
    c = d["coverage"]
    # measurement-noise-only coverage under-covers a real cosmic-variance flow ...
    assert c["measurement_noise_only"]["amplitude_coverage"] < 0.5
    # ... and the cosmic-variance-inclusive coverage is nominal (~68%)
    assert 0.60 <= c["cosmic_variance_inclusive"]["amplitude_coverage"] <= 0.76
    for comp in c["cosmic_variance_inclusive"]["component_coverage"]:
        assert 0.58 <= comp <= 0.78
    # cosmic variance dominates the bulk-flow error budget
    assert c["cosmic_variance_amplitude_error_kms"] > c["measurement_amplitude_error_kms"]
    # estimator is (near) unbiased
    assert abs(c["cosmic_variance_inclusive"]["amplitude_bias_kms"]) < 10.0


def test_deterministic_against_real_catalogue_when_present():
    if not CAT.is_file():
        return
    mod = _load()
    assert mod.main(["--check"]) == 0
