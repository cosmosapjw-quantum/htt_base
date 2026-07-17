"""PR-129 contract tests: NTA3 estimator/domain registry."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from common.nta3_estimator_registry import (
    PREREGISTERED_TOLERANCE_ABS,
    EstimatorSpec,
    Nta3RegistryError,
    alm_real_dof,
    chi_square_dispersion_squared,
    generate_caption,
    lint_caption,
    moment_dispersion_squared,
    run_seeded_mc,
    validate_separation,
    verify_quadrupole_dispersion,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

QUAD_PAYLOAD = {
    "estimator_id": "quadrupole_power_ideal",
    "statistic": "C2_hat = (1/5) * sum_m |a_2m|^2",
    "sky": "full_sky",
    "noise": "none",
    "field": "isotropic_gaussian",
    "ell": 2,
    "dof": 5,
    "dispersion_squared_exact": "2/5",
}


def _quad() -> EstimatorSpec:
    return EstimatorSpec.from_payload(QUAD_PAYLOAD)


def test_exact_dispersion_three_ways() -> None:
    assert chi_square_dispersion_squared(5) == Fraction(2, 5)
    assert moment_dispersion_squared(2) == Fraction(2, 5)
    assert alm_real_dof(2) == 5
    assert verify_quadrupole_dispersion(_quad()) == Fraction(2, 5)
    # the moment derivation is a genuine function of ell, not of dof:
    assert moment_dispersion_squared(3) == Fraction(2, 7)
    assert moment_dispersion_squared(0) == Fraction(2, 1)


def test_wrong_dof_is_killed_structurally() -> None:
    with pytest.raises(Nta3RegistryError, match="reality-condition count"):
        verify_quadrupole_dispersion(
            EstimatorSpec.from_payload(dict(QUAD_PAYLOAD, dof=4)))


def test_naive_complex_miscount_dof9_is_killed() -> None:
    # dof=9 with self-consistent 2/9 passes bare chi-square arithmetic;
    # only the structural 2*ell+1 check kills it (adversarial finding 1).
    with pytest.raises(Nta3RegistryError, match="reality-condition count"):
        verify_quadrupole_dispersion(EstimatorSpec.from_payload(
            dict(QUAD_PAYLOAD, dof=9, dispersion_squared_exact="2/9")))


def test_unspecified_estimator_fails_closed() -> None:
    with pytest.raises(Nta3RegistryError, match="missing fields"):
        EstimatorSpec.from_payload({"estimator_id": "mystery",
                                    "statistic": "S", "dof": 5})
    with pytest.raises(Nta3RegistryError, match="non-empty"):
        EstimatorSpec.from_payload(dict(QUAD_PAYLOAD, sky="  "))
    with pytest.raises(Nta3RegistryError, match="requires the multipole"):
        EstimatorSpec.from_payload(
            {k: v for k, v in QUAD_PAYLOAD.items() if k != "ell"})


def test_separation_validator_rejects_all_conflation_variants() -> None:
    validate_separation({"cites": "sqrt(2/5)",
                         "as": "single-estimator sampling dispersion"})
    validate_separation({"cites": "multi-multipole Fisher information",
                         "as": "joint low-l Fisher information"})
    for claim in (
            {"cites": "sqrt(2/5)", "as": "multi-multipole Fisher floor"},
            {"cites": "sqrt(2 / 5)", "as": "Fisher floor"},
            {"cites": "sqrt(2/5)", "as": "Cramér-Rao floor"},
            {"cites": "sqrt(2/5)",
             "as": "minimax lower bound over all estimators"},
            {"cites": "0.632", "as": "multi-multipole Fisher floor"},
            {"cites": "0.632", "as": "universal floor"},
            {"cites": "the Fisher information",
             "as": "the estimator dispersion"},
    ):
        with pytest.raises(Nta3RegistryError, match="conflation rejected"):
            validate_separation(claim)


def test_mc_module_pin_rejects_widening_on_real_path() -> None:
    with pytest.raises(Nta3RegistryError, match="post-hoc"):
        run_seeded_mc(_quad(), seed=20260718, replicates=1000,
                      tolerance_abs=PREREGISTERED_TOLERANCE_ABS * 10)


def test_seeded_estimator_mc_within_preregistered_tolerance() -> None:
    result = run_seeded_mc(_quad(), seed=20260718, replicates=200000,
                           tolerance_abs=PREREGISTERED_TOLERANCE_ABS)
    assert result["within_tolerance"] is True
    assert result["abs_deviation"] < PREREGISTERED_TOLERANCE_ABS
    assert result["simulation"] == \
        "gaussian_alm_reality_condition_estimator_draws"


def test_caption_lint_kills_floor_and_paraphrase_language() -> None:
    text = generate_caption(_quad())
    lint_caption(text)  # generated captions are clean
    for suffix in (" This is the universal" + " floor.",
                   " The best" + " achievable dispersion.",
                   " No estimator" + " does better.",
                   " The Cramér-Rao" + " floor."):
        with pytest.raises(Nta3RegistryError, match="forbidden"):
            lint_caption(text + suffix)


def _load_runner():
    spec_path = (REPO_ROOT /
                 "scripts/codex_harness/run_pr129_nta3_registry.py")
    module_spec = importlib.util.spec_from_file_location(
        "run_pr129", spec_path)
    runner = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(runner)
    return runner


def test_negative_scan_sentinel_policy_and_allowlist() -> None:
    runner = _load_runner()
    banned = "universal" + " floor"
    text = "\n".join([
        "clean line",
        f"# {runner.SENTINEL_BEGIN}",
        f"registry line with {banned}",
        f"# {runner.SENTINEL_END}",
        "another clean line",
    ])
    report = runner._scan_text(text, [banned], frozenset(), True)
    assert report["hits"] == []
    assert report["sentinel_block_count"] == 1
    with pytest.raises(SystemExit, match="not allowed"):
        runner._scan_text(text, [banned], frozenset(), False)
    unguarded = runner._scan_text(f"claims the {banned}", [banned],
                                  frozenset(), False)
    assert len(unguarded["hits"]) == 1
    import hashlib
    line = f"NOT the {banned} in an allowlisted negation"
    allow = frozenset({hashlib.sha256(line.encode()).hexdigest()})
    allowed = runner._scan_text(line, [banned], allow, False)
    assert allowed["hits"] == []
    assert allowed["allowlisted_lines"] == 1


def test_tolerance_pins_and_cross_list_gate() -> None:
    import yaml
    runner = _load_runner()
    spec = yaml.safe_load(runner.SPEC_PATH.read_text(encoding="utf-8"))
    assert float(spec["monte_carlo"]["preregistered_tolerance_abs"]) == \
        PREREGISTERED_TOLERANCE_ABS
    assert runner._verify_prohibition_cross_list(spec) == \
        len(spec["negative_scan"]["forbidden_patterns"])


def test_runner_check_mode_is_current() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr129_nta3_registry.py"),
         "--check"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_artifacts_scan_mutations_and_manifest() -> None:
    scan = json.loads(
        (REPO_ROOT / "docs/generated/pr129_negative_scan.json")
        .read_text(encoding="utf-8"))
    assert scan["total_hits"] == 0
    assert len(scan["targets"]) == 8
    assert scan["allowlisted_lines_total"] == 3
    module_target = scan["targets"][
        "htt/src/common/nta3_estimator_registry.py"]
    assert module_target["sentinel_block_count"] == 1
    assert module_target["sentinel_block_sha256"] == \
        scan["sentinel_policy"]["block_sha256"]
    report = json.loads(
        (REPO_ROOT / "docs/generated/pr129_mutation_report.json")
        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    assert all(m["killed"] for m in report["mutations"])
    mc = json.loads(
        (REPO_ROOT / "docs/generated/pr129_mc_report.json")
        .read_text(encoding="utf-8"))
    assert mc["result"]["abs_deviation"] < 0.004
    assert mc["result"]["simulation"] == \
        "gaussian_alm_reality_condition_estimator_draws"
    assert mc["tolerance_provenance"] == \
        "dual_pinned_spec_and_module_never_widened"
    manifest = json.loads(
        (REPO_ROOT / "docs/generated/pr129_artifact_manifest.json")
        .read_text(encoding="utf-8"))
    assert all(sha for sha in manifest["artifacts"].values())
    registry = json.loads(
        (REPO_ROOT / "docs/generated/pr129_estimator_registry.json")
        .read_text(encoding="utf-8"))
    ids = [e["estimator_id"] for e in registry["entries"]]
    assert ids == ["quadrupole_power_ideal", "multi_multipole_fisher_toy"]
    check = registry["exact_analytic_check"]
    assert check["registered_dispersion_squared"] == "2/5"
    assert check["gaussian_moment_derivation"] == "2/5"
    assert check["structural_dof_2ell_plus_1"] == 5
    assert check["three_way_agreement"] is True
