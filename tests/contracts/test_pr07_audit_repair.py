"""Contract gates for the PR07 audit-repair programme.

Asserts that the repaired surface holds: unit-safe anisotropic stress, the
independent dynamics verifier, the PAPER-A closure helpers, the CoVe report and
Wolfram proof record, and the absence of the forbidden overclaim tokens from the
final report. These are repo-local checks (no external data, no Wolfram engine
required for the token/CoVe surface)."""
from __future__ import annotations

import json
from pathlib import Path
import re

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
REPORT_TEX = REPO / "docs/final_report/main.tex"
GEN = REPO / "docs/generated"

FORBIDDEN_TOKENS = (
    r"EGS identity",
    r"cosmic[-\s]variance floor",
    r"tilt signature",
    r"model[-\s]independent anomaly",
    r"Cram[eé]r[-\s]Rao",
    r"\bCRLB\b",
    r"minimum[-\s]variance estimator",
)


def test_unit_safe_anisotropic_stress():
    from bass.background.bi_continuation.moments import (
        normalize_anisotropic_stress, physical_anisotropic_stress)
    from bass.background.bi_continuation.dynamics import (
        shear_rhs_from_physical, shear_rhs_from_normalized)
    H, kappa = 0.73, 1.7
    pi = np.array([[0.2, 0.03, 0.0], [0.03, -0.12, 0.01], [0.0, 0.01, -0.08]])
    Pi = normalize_anisotropic_stress(pi, H, kappa)
    assert np.allclose(physical_anisotropic_stress(Pi, H, kappa), pi, atol=3e-13)
    sigma = np.diag([0.04, -0.01, -0.03])
    a = shear_rhs_from_physical(H, sigma, pi, kappa)
    b = shear_rhs_from_normalized(H, sigma, Pi)
    assert np.max(np.abs(a - b)) < 3e-13


def test_independent_dynamics_verifier():
    from bass.background.bi_continuation.verification import random_species_audit
    r = random_species_audit(samples=300, seed=20260625)
    assert r["passed"]
    assert r["max_energy_residual"] < 1e-10 and r["max_momentum_residual"] < 1e-10


def test_paper_a_closure_helpers():
    from htt.departure.paper_a_closure import (
        numerical_rank, radial_vorticity_response, single_shell_dipole_design,
        temporal_tensor_design, boost_composition_audit, first_jet_counterexample)
    rng = np.random.default_rng(4)
    n = rng.normal(size=(120, 3)); d = rng.uniform(10, 200, size=120)
    assert numerical_rank(radial_vorticity_response(n, d)) == 0          # radial no-go
    assert numerical_rank(single_shell_dipole_design(n, np.full(120, 80.0))) == 3
    assert numerical_rank(temporal_tensor_design(np.eye(3))) == 15
    b = boost_composition_audit(np.array([0.2, 0, 0]), np.array([0, 0.15, 0]))
    assert b["lorentz_error"] < 1e-12 and b["nonadditivity_norm"] > 1e-4
    assert first_jet_counterexample(0.2)["different_first_jet"]


@pytest.mark.xfail(
    reason=(
        "PR-120 quarantined the CF4-P0 final report (docs/final_report/"
        "main.tex deleted; legacy copy is public_use=false); red by "
        "quarantine design until a post-quarantine report exists."
    ),
    strict=False,
)
def test_report_has_no_forbidden_overclaim_tokens():
    text = REPORT_TEX.read_text(encoding="utf-8")
    for pat in FORBIDDEN_TOKENS:
        assert re.search(pat, text, re.IGNORECASE) is None, f"forbidden token present: {pat}"


@pytest.mark.skipif(not (GEN / "pr07_cove_report.json").exists(),
                    reason="run scripts/run_pr07_experiments.py + cove_verify_pr07.py first")
def test_cove_report_passes():
    cove = json.loads((GEN / "pr07_cove_report.json").read_text())
    assert cove["status"] == "PASS_WITH_REGISTERED_DELEGATIONS"
    assert all(c["pass"] for c in cove["checks"])
    assert cove["claim_boundary"].startswith("synthetic/theorem mechanics only")


@pytest.mark.skipif(not (GEN / "pr07_wolfram_proofs.json").exists(),
                    reason="run make pr07-wolfram on a Wolfram host first")
def test_wolfram_proof_record_passes():
    proofs = json.loads((GEN / "pr07_wolfram_proofs.json").read_text())
    assert proofs["status"] == "PASS"
