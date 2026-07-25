"""PR-131 contract tests: near-FLRW expansion + singular map."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
import sympy as sp

from common.omk_near_flrw_expansion import (
    C2_EXACT,
    C3_EXACT,
    DECLARED_DOMAIN,
    KAPPA_EXACT,
    W,
    OmkNearFlrwError,
    fd_plateau,
    generate_caption,
    invariance_coefficients,
    jacobian_at_flrw,
    lint_caption,
    resonance_w,
    system_checks,
    validate_claim,
    validate_declared_domain,
    validate_plateau_report,
    verify_kappa_candidate,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    runner_path = (
        REPO_ROOT / "scripts/codex_harness/run_pr131_omk_near_flrw.py"
    )
    spec = importlib.util.spec_from_file_location("run_pr131", runner_path)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    return runner


def test_current_expansion_hash_is_generation_time_provenance() -> None:
    runner = _load_runner()
    source = runner.EXPANSION_SOURCE
    system = runner.OUTPUTS["system"]
    stored = {
        "negative_scan": {
            "targets": {
                source: {"sha256": "1" * 64, "hits": []},
            }
        }
    }
    current = {
        "negative_scan": {
            "targets": {
                source: {"sha256": "2" * 64, "hits": []},
            }
        }
    }
    assert runner._semantic_artifact(
        system, stored
    ) == runner._semantic_artifact(system, current)
    current["negative_scan"]["targets"][source]["hits"] = [{"line": 1}]
    assert runner._semantic_artifact(
        system, stored
    ) != runner._semantic_artifact(system, current)

    legacy = "htt/obsstat/egs3_omega_k_reopening.py"
    manifest = runner.OUTPUTS["manifest"]
    stored = {
        "input_hashes": [
            f"{source}:{'1' * 64}",
            f"{legacy}:{'3' * 64}",
        ]
    }
    current = {
        "input_hashes": [
            f"{source}:{'2' * 64}",
            f"{legacy}:{'3' * 64}",
        ]
    }
    assert runner._semantic_artifact(
        manifest, stored
    ) == runner._semantic_artifact(manifest, current)
    current["input_hashes"][1] = f"{legacy}:{'4' * 64}"
    assert runner._semantic_artifact(
        manifest, stored
    ) != runner._semantic_artifact(manifest, current)


def test_jacobian_and_exact_coefficients() -> None:
    lam = jacobian_at_flrw()
    assert sp.simplify(lam["lambda_sigma"]
                       + sp.Rational(3, 2) * (1 - W)) == 0
    assert sp.simplify(lam["lambda_k"] - (1 + 3 * W)) == 0
    inv = invariance_coefficients(order=3)
    assert sp.simplify(inv["kappa"] - KAPPA_EXACT) == 0
    assert sp.simplify(inv["c2"] - C2_EXACT) == 0
    assert sp.simplify(inv["c3"] - C3_EXACT) == 0
    # reference values
    assert sp.nsimplify(KAPPA_EXACT.subs(W, 0)) == sp.Rational(-2, 5)
    assert sp.nsimplify(KAPPA_EXACT.subs(W, sp.Rational(1, 3))) == \
        sp.Rational(-1, 3)
    assert sp.nsimplify(C2_EXACT.subs(W, 0)) == sp.Rational(-26, 175)
    assert sp.nsimplify(C2_EXACT.subs(W, sp.Rational(1, 3))) == \
        sp.Rational(-1, 9)
    assert sp.nsimplify(C3_EXACT.subs(W, 0)) == sp.Rational(-94, 875)


def test_wrong_kappa_sign_killed() -> None:
    with pytest.raises(OmkNearFlrwError, match="invariance equation"):
        verify_kappa_candidate(2 / (3 * W + 5))
    verify_kappa_candidate(KAPPA_EXACT)


def test_system_checks_exact() -> None:
    checks = system_checks()
    assert checks["vacuum_anchor_stationary"] is True
    assert checks["curvature_source_coefficient_minus_one"] is True


def test_resonance_family_and_domain() -> None:
    assert resonance_w(1) == Fraction(-5, 3)
    assert resonance_w(2) == Fraction(-7, 9)
    assert resonance_w(3) == Fraction(-3, 5)
    # the family is monotone increasing toward -1/3, never entering it
    prev = Fraction(-2)
    for n in range(1, 60):
        wn = resonance_w(n)
        assert prev < wn < Fraction(-1, 3)
        prev = wn
    validate_declared_domain(DECLARED_DOMAIN)
    with pytest.raises(OmkNearFlrwError, match="resonance"):
        validate_declared_domain((Fraction(-1), Fraction(1)))
    with pytest.raises(OmkNearFlrwError, match="resonance"):
        validate_declared_domain((Fraction(-7, 10), Fraction(1)))
    # the adversarial-lane truncation hole: a sliver just below -1/3
    # contains only resonances with n far beyond any finite scan — the
    # exact monotone-inversion validator must still reject it
    with pytest.raises(OmkNearFlrwError, match="resonance"):
        validate_declared_domain((Fraction(-3340, 10000),
                                  Fraction(-3335, 10000)))
    # marginal boundaries are rejected on their own
    with pytest.raises(OmkNearFlrwError, match="marginal"):
        validate_declared_domain((Fraction(-1, 3), Fraction(2)))
    # a clean sub-domain passes
    validate_declared_domain((Fraction(0), Fraction(1, 2)))


def test_plateau_report_gate() -> None:
    validate_plateau_report({"claimed_c2": "-0.14857142857", "w": "0",
                             "probe_K": "1/100000"})
    with pytest.raises(OmkNearFlrwError, match="finite coefficient"):
        validate_plateau_report({"claimed_c2": "nan", "w": "0",
                                 "probe_K": "1/100000"})
    with pytest.raises(OmkNearFlrwError, match="outside the declared"):
        validate_plateau_report({"claimed_c2": "-34/605", "w": "2",
                                 "probe_K": "1/100000"})
    with pytest.raises(OmkNearFlrwError, match="positive probe"):
        validate_plateau_report({"claimed_c2": "-26/175", "w": "0",
                                 "probe_K": "0"})
    with pytest.raises(OmkNearFlrwError, match="not\na derivation|not "
                       "a derivation"):
        validate_plateau_report({"claimed_c2": "-0.2485714", "w": "0",
                                 "probe_K": "1/100000"})


def test_fd_plateau_rejects_empty_probe_set() -> None:
    with pytest.raises(OmkNearFlrwError, match="at least one probe"):
        fd_plateau(Fraction(0), probes=())


def test_fd_plateau_rejects_nonpositive_seed_magnitude() -> None:
    with pytest.raises(OmkNearFlrwError, match="strictly positive"):
        fd_plateau(Fraction(0), k0=Fraction(-1, 10 ** 8), branch=1)


def test_claim_and_caption_gates() -> None:
    validate_claim({"asserts": "asymptotic coefficient",
                    "fixed_background": "q0 = 1/2"})
    with pytest.raises(OmkNearFlrwError, match="global"):
        validate_claim({"asserts": "asymptotic coefficient"})
    with pytest.raises(OmkNearFlrwError, match="NOT recovered"):
        validate_claim({"asserts": "ceilings recovered",
                        "fixed_background": "q0 = 1/2"})
    # the adversarial-lane synonym: implication wording is also rejected
    with pytest.raises(OmkNearFlrwError, match="NOT recovered"):
        validate_claim({"asserts": "the historical finite-ceiling table "
                        "follows directly from this expansion",
                        "fixed_background": "q0 = 1/2"})
    text = generate_caption(Fraction(0))
    lint_caption(text)
    with pytest.raises(OmkNearFlrwError, match="outside the declared"):
        generate_caption(Fraction(2))
    for suffix in (" Holds for all" + " q.",
                   " The six finite" + " ceilings follow.",
                   " Matches the observed" + " shear."):
        with pytest.raises(OmkNearFlrwError, match="forbidden"):
            lint_caption(text + suffix)


def test_baseline_pin_resolves_and_fabrication_refused() -> None:
    import yaml
    spec_file = (REPO_ROOT /
                 "docs/research_program/long_horizon_rescue/"
                 "pr131_spec.yaml")
    spec = yaml.safe_load(spec_file.read_text(encoding="utf-8"))
    runner = _load_runner()
    runner._verify_baseline_commit(spec)
    with pytest.raises(SystemExit, match="does not resolve"):
        runner._verify_baseline_commit(
            {"baseline_commit": "221b374b" + "0" * 32})


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT /
             "scripts/codex_harness/run_pr131_omk_near_flrw.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_two_path_fd_singular() -> None:
    two_path = json.loads(
        (REPO_ROOT / "docs/generated/pr131_two_path_report.json")
        .read_text(encoding="utf-8"))
    signatures = {b["signature"] for b in two_path["path_b_branches"]}
    assert signatures == {1, -1}
    assert all(b["matches_path_a"] for b in two_path["path_b_branches"])
    fd = json.loads(
        (REPO_ROOT / "docs/generated/pr131_fd_plateau.json")
        .read_text(encoding="utf-8"))
    assert len(fd["runs"]) == 4
    branches = {(run["w"], run["branch"]) for run in fd["runs"]}
    assert branches == {("0", "biii_K_positive"), ("0", "ks_K_negative"),
                        ("1/3", "biii_K_positive"),
                        ("1/3", "ks_K_negative")}
    for run in fd["runs"]:
        assert len(run["probes"]) == 3
        assert all(p["within_envelopes"] for p in run["probes"])
    singular = json.loads(
        (REPO_ROOT / "docs/generated/pr131_singular_map.json")
        .read_text(encoding="utf-8"))
    assert [e["w"] for e in singular["entries"]] == \
        ["-5/3", "-7/9", "-3/5", "-1/3", "1"]
    assert singular["domain_validated"] is True
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr131_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    coeffs = json.loads(
        (REPO_ROOT / "docs/generated/pr131_coefficients.json")
        .read_text(encoding="utf-8"))
    assert coeffs["claimed_orders"] == ["kappa", "c2"]
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr131_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
