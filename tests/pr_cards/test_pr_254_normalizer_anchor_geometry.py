"""PR-254 typed anchor geometry, CAS, and claim-boundary gates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import yaml
from common.anchor_geometry import (
    AnchorBodySpec,
    AnchorFamily,
    AnchorGaugeInterval,
    AnchorMarginReport,
    NormalizerBenchmarkReport,
    NormalizerPurpose,
    NormalizerSpec,
    j1_outer_envelope_counterexample,
    j2_dependence_counterexample,
)

from scripts.codex_harness.premise_anchor_gates import (
    REFUTED_OUTCOME,
    evaluate_conjecture_gate,
)
from scripts.codex_harness.run_pr254_counterexamples import build_payload
from scripts.codex_harness.run_pr254_normalizer_benchmark import (
    LIKELIHOOD_COVARIANCE,
    LIKELIHOOD_TOLERANCE,
    ZERO_DENOMINATOR_ERROR,
    _canonical_float,
    _gaussian_neg2loglikelihood_invariance_error,
    _run_zero_denominator_probe,
    _stress_ratio,
)
from scripts.codex_harness.run_pr254_normalizer_benchmark import (
    build_payload as build_benchmark_payload,
)

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/premise_anchor/pr254_spec.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
CONTRACT = (
    ROOT
    / "docs/generated/pr254_anchor_geometry/"
    "CAS_CONTRACT_PR254_ANCHOR_GEOMETRY.json"
)
COUNTEREXAMPLE_RECEIPT = (
    ROOT
    / "docs/generated/pr254_anchor_geometry/counterexample_oracle.json"
)
BENCHMARK_RECEIPT = (
    ROOT
    / "docs/generated/pr254_anchor_geometry/normalizer_benchmark.json"
)
PUBLICATION_POLICY = (
    ROOT
    / "docs/research_program/premise_anchor/pr254_publication_policy.json"
)
CAS_ADJUDICATION = (
    ROOT
    / "docs/generated/pr254_anchor_geometry/"
    "CAS_ADJUDICATION_PR254_ANCHOR_GEOMETRY.json"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_spec_fixes_one_way_scope_and_six_normalizer_kinds() -> None:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    assert spec["work_unit_id"] == "PR-254"
    assert spec["target_sha"] == "7e63eaba54c50589676a50449627f9ebc7fa7e8d"
    assert spec["claim_boundary"]["forbidden"] == [
        "FLRW proximity or converse",
        "source or Bianchi family identification",
        "observational validation",
        "native solver status",
        "automatic evidence or cross-lane evidence merge",
    ]
    assert {
        item["claim_id"] for item in spec["adopted_claims"]
    } == {
        "PA-THM-GAUGE-SUBLEVEL",
        "PA-THM-PRODUCT-BALL",
        "PA-THM-ONE-WAY-MES",
        "PA-THM-RANK-INVARIANCE",
    }
    assert all(
        item["ceiling"] == "conditional"
        for item in spec["adopted_claims"]
    )
    assert set(spec["normalizer_benchmark"]["required_kinds"]) == {
        "EXPANSION_NORMALIZED",
        "MES_ANCHORED",
        "FISHER_WHITENED",
        "TEMPLATE_LIMIT",
        "DYNAMICAL_BREAKDOWN",
        "PRIOR_QUANTILE",
    }
    assert "no universal scalar score" in spec["normalizer_benchmark"]["comparison"]


def test_pr254_closeout_is_methodology_only_and_review_bound() -> None:
    status = yaml.safe_load(STATUS.read_text(encoding="utf-8"))
    assert "PR-254" in status["completed"]
    assert "PR-254" not in status["pending"]
    assert status["execution_resolutions"]["PR-254"] == {
        "resolution": "COMPLETED_SUCCESS",
        "receipt": "docs/PR_DELTAS/pr-254.md",
        "review_receipt": (
            ".agent-harness/runs/"
            "premise-anchor-pr254-benchmark-evidence-final-r2-20260729/"
            "RUN_SUMMARY.json"
        ),
        "resolved_on": "2026-07-29",
        "scientific_status_effect": "none_methodology_conditional_only",
        "scientific_status_after": "OPEN",
        "scientific_artifact_mode": "methodology_conditional",
        "public_use": False,
        "success_dependency_satisfied": True,
    }


def test_publication_policy_uses_portable_python_first_runner() -> None:
    policy = json.loads(PUBLICATION_POLICY.read_text(encoding="utf-8"))
    commands = policy["required_commands"]
    assert {command["id"] for command in commands} == {
        "pr254-focused",
        "pr254-counterexample-oracle",
        "pr254-normalizer-benchmark",
        "pr04-regression",
        "pr07-regression",
        "dag-and-status",
    }
    assert all(command["argv"][0] == "{python}" for command in commands)
    runner_commands = commands[:-1]
    assert all(
        command["argv"][2]
        == "scripts/codex_harness/run_pr254_integration.py"
        for command in runner_commands
    )
    assert {command["argv"][3] for command in runner_commands} == {
        "focused",
        "counterexample",
        "benchmark",
        "pr04",
        "pr07",
    }


def test_common_contracts_are_the_same_public_objects_in_htt_and_mio() -> None:
    from mio import formalism as mio_formalism

    from htt import core as htt_core

    public = {
        "AnchorBodySpec": AnchorBodySpec,
        "AnchorFamily": AnchorFamily,
        "AnchorGaugeInterval": AnchorGaugeInterval,
        "AnchorMarginReport": AnchorMarginReport,
        "NormalizerBenchmarkReport": NormalizerBenchmarkReport,
        "NormalizerPurpose": NormalizerPurpose,
        "NormalizerSpec": NormalizerSpec,
    }
    for name, expected in public.items():
        assert getattr(htt_core, name) is expected
        assert getattr(mio_formalism, name) is expected


def test_counterexample_oracle_is_exact_independent_and_scope_bounded() -> None:
    frozen = json.loads(COUNTEREXAMPLE_RECEIPT.read_text(encoding="utf-8"))
    assert frozen == build_payload()
    assert frozen["arithmetic"] == "exact_fraction"
    assert all(frozen["checks"].values())
    assert frozen["j1_exact"]["rho_a"] == "1/2"
    assert frozen["j1_exact"]["rho_b"] == "1/4"
    assert frozen["j2_exact"]["comonotone_exceedance_probability"] == "0"
    assert (
        frozen["j2_exact"]["countermonotone_exceedance_probability"]
        == "1/2"
    )
    assert "claim no narrower physical MES theorem can exist" in (
        frozen["claim_boundary"]["forbidden"]
    )
    assert "claim every registered joint-law test is invalid" in (
        frozen["claim_boundary"]["forbidden"]
    )

    j1 = j1_outer_envelope_counterexample()
    j2 = j2_dependence_counterexample()
    assert j1.gate_outcome == j2.gate_outcome == "COUNTEREXAMPLE_FOUND"
    assert "outer-envelope implication" in j1.scope
    assert "joint-law-free" in j2.scope


def test_counterexamples_force_both_strong_conjectures_to_restricted() -> None:
    j1 = evaluate_conjecture_gate(
        "J1-EXACT",
        [
            {
                "obligation_id": "COUNTEREXAMPLE_ADJUDICATION",
                "outcome": "COUNTEREXAMPLE_FOUND",
            }
        ],
    )
    j2 = evaluate_conjecture_gate(
        "J2-UNIFORM",
        [
            {
                "obligation_id": "COUNTEREXAMPLE_ADJUDICATION",
                "outcome": "COUNTEREXAMPLE_FOUND",
            }
        ],
    )
    assert j1["status"] == j2["status"] == REFUTED_OUTCOME
    assert j1["ready"] is j2["ready"] is False
    assert j1["refuting_obligations"] == [
        "COUNTEREXAMPLE_ADJUDICATION"
    ]
    assert j2["refuting_obligations"] == [
        "COUNTEREXAMPLE_ADJUDICATION"
    ]


def test_synthetic_benchmark_replays_same_draws_and_meets_mc_precision() -> None:
    frozen = json.loads(BENCHMARK_RECEIPT.read_text(encoding="utf-8"))
    assert frozen == build_benchmark_payload()
    assert frozen["data_source"] == "synthetic_only"
    assert frozen["pr151_data_used"] is False
    assert frozen["diagnostics"]["status"] == "PASS"
    assert frozen["diagnostics"]["replicates"] >= 20_000
    assert frozen["diagnostics"]["replicates"] <= 400_000
    assert (
        frozen["diagnostics"]["diagnostic_screening_exceedance_mcse"]
        <= 0.0025
    )
    assert frozen["diagnostics"]["partial_id_coverage_mcse"] <= 0.0025
    assert frozen["configuration"]["serialized_significant_digits"] == 14
    assert frozen["configuration"]["numerical_zero_tolerance"] == 1e-12
    assert (
        frozen["configuration"]["likelihood_tolerance"]
        == LIKELIHOOD_TOLERANCE
    )
    assert frozen["diagnostics"]["size_pass"] is True
    assert frozen["diagnostics"]["coverage_pass"] is True
    assert (
        frozen["diagnostics"]["diagnostic_screening_exceedance_rate"]
        <= frozen["diagnostics"]["size_threshold_3mcse"]
    )
    assert (
        frozen["diagnostics"]["partial_id_coverage_rate"]
        >= frozen["diagnostics"]["coverage_threshold_3mcse"]
    )
    assert (
        frozen["benchmark"]["mes_disposition"]
        == "ONE_ANCHOR_AMONG_FAMILY"
    )
    assert frozen["benchmark"]["universal_winner"] is None
    assert frozen["benchmark"]["scalar_score"] is None
    receipts = {
        row["base_draws_receipt"] for row in frozen["evaluations"]
    }
    assert len(receipts) == 1
    assert receipts == {
        frozen["configuration"]["same_base_draws_receipt"]
    }
    assert all(
        row["rank_before"] == row["rank_after"]
        and row["denominator_zero_status"] == "FAIL_CLOSED"
        and row["likelihood_invariance_error"] <= LIKELIHOOD_TOLERANCE
        for row in frozen["evaluations"]
    )
    assert frozen["denominator_zero_probe"] == {
        "operation": "stress_ratio",
        "numerator": [1.0],
        "anchor_denominator": [0.0],
        "expected_exception_type": "ValueError",
        "expected_exception_message": ZERO_DENOMINATOR_ERROR,
        "observed_exception_type": "ValueError",
        "observed_exception_message": ZERO_DENOMINATOR_ERROR,
        "status": "FAIL_CLOSED",
    }
    assert frozen["likelihood_probe"]["covariance"] == [
        list(row) for row in LIKELIHOOD_COVARIANCE
    ]
    assert frozen["likelihood_probe"]["statistic"] == (
        "maximum_absolute_difference_in_gaussian_negative_2_log_likelihood"
    )
    assert (
        frozen["likelihood_probe"]["base_draws_receipt"]
        == frozen["configuration"]["same_base_draws_receipt"]
    )
    assert {
        row["normalizer_id"] for row in frozen["evaluations"]
    } == {
        "pr254.expansion_normalized",
        "pr254.mes_anchored",
        "pr254.fisher_whitened",
        "pr254.template_limit",
        "pr254.dynamical_breakdown",
        "pr254.prior_quantile",
    }


def test_benchmark_serialization_kills_last_bit_platform_drift() -> None:
    assert _canonical_float(5.159724562609037) == _canonical_float(
        5.1597245626090364
    )
    assert (
        _canonical_float(8.881784197001252e-16, zero_tolerance=1e-12)
        == 0.0
    )


def test_zero_denominator_status_is_derived_from_an_executed_refusal() -> None:
    status, receipt = _run_zero_denominator_probe()
    assert status.value == "FAIL_CLOSED"
    assert receipt["observed_exception_type"] == "ValueError"
    assert receipt["observed_exception_message"] == ZERO_DENOMINATOR_ERROR

    with pytest.raises(ValueError, match="strictly positive"):
        _stress_ratio(np.asarray([1.0]), np.asarray([0.0]))
    with pytest.raises(ValueError, match="strictly positive"):
        _stress_ratio(np.asarray([1.0]), np.asarray([-1.0]))
    with pytest.raises(ValueError, match="finite"):
        _stress_ratio(np.asarray([1.0]), np.asarray([np.nan]))
    with pytest.raises(ValueError, match="same shape"):
        _stress_ratio(np.asarray([1.0, 2.0]), np.asarray([1.0]))
    with pytest.raises(ValueError, match="non-empty"):
        _stress_ratio(np.asarray([]), np.asarray([]))


def test_gaussian_likelihood_probe_detects_a_broken_reparameterization() -> None:
    prediction = np.asarray([[0.2, -0.1, 0.4, 0.3]])
    observation = np.asarray([[0.5, -0.4, 0.2, 0.7]])
    covariance = np.asarray(LIKELIHOOD_COVARIANCE)
    assert _gaussian_neg2loglikelihood_invariance_error(
        prediction,
        prediction.copy(),
        observation,
        covariance,
    ) == 0.0

    broken = prediction.copy()
    broken[0, 0] += 0.25
    assert _gaussian_neg2loglikelihood_invariance_error(
        prediction,
        broken,
        observation,
        covariance,
    ) > LIKELIHOOD_TOLERANCE

    with pytest.raises(ValueError, match="positive definite"):
        _gaussian_neg2loglikelihood_invariance_error(
            prediction,
            prediction.copy(),
            observation,
            np.zeros((4, 4)),
        )
    nonsymmetric = covariance.copy()
    nonsymmetric[0, 1] += 0.2
    with pytest.raises(ValueError, match="symmetric"):
        _gaussian_neg2loglikelihood_invariance_error(
            prediction,
            prediction.copy(),
            observation,
            nonsymmetric,
        )


def test_cas_contract_is_source_bound_and_has_four_noncollapsible_axes() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["schema_version"] == 2
    assert contract["risk_tier"] == "R3"
    assert contract["required_axes"] == [
        "wolfram_xact",
        "sympy",
        "sage_singular",
        "lean",
    ]
    assert contract["identity"]["claim_ceiling"] == "conditional"
    assert set(contract["target"]["exact_test_obligations"]) == {
        "product_ball_max_ratio",
        "ellipsoid_unit_sublevel",
        "polytope_unit_sublevel",
        "one_way_outer_envelope",
        "invertible_scaling_rank",
        "transformed_response_identity",
        "j1_counterexample",
        "j2_dependence_counterexample",
    }
    for source in contract["identity"]["source_input_hashes"]:
        assert _sha256(ROOT / source["path"]) == source["sha256"]
    polytope_fixture = next(
        item
        for item in contract["target"]["numeric_test_vectors"]
        if item["id"] == "POLYTOPE-FIXTURE"
    )
    assert polytope_fixture["halfspace_normals"] == [
        ["1", "0"],
        ["-1", "0"],
        ["0", "1"],
        ["0", "-1"],
    ]
    assert polytope_fixture["halfspace_bounds"] == ["2", "2", "4", "4"]
    assert contract["exceptions_adjudication"]["preregistered_exceptions"] == []
    assert "No MES converse" in contract["semantics"]["exclusions"][0]


def test_runner_observed_four_axis_adjudication_passes_only_cas_component() -> None:
    adjudication = json.loads(CAS_ADJUDICATION.read_text(encoding="utf-8"))
    assert adjudication["contract_sha256"] == _sha256(CONTRACT)
    assert adjudication["aggregate_status"] == "CAS_4AXIS_PASS"
    assert adjudication["claim_promotion_cas_eligible"] is True
    assert (
        adjudication["claim_promotion_cas_requirement"]
        == "SATISFIED"
    )
    assert adjudication["evidence_origin"] == (
        "runner_observed_local_subprocess"
    )
    assert set(adjudication["axis_statuses"]) == {
        "wolfram_xact",
        "sympy",
        "sage_singular",
        "lean",
    }
    assert set(adjudication["axis_statuses"].values()) == {"PASS"}
    assert adjudication["errors"] == []
    assert all(
        row["solver_executed"] is True
        and row["preflight_probe"]["status"] == "PASS"
        for row in adjudication["execution_evidence"].values()
    )
    # CAS is one component only; the exact J1/J2 counterexamples still block
    # their strong promotion gates.
    assert j1_outer_envelope_counterexample().gate_outcome == (
        "COUNTEREXAMPLE_FOUND"
    )
    assert j2_dependence_counterexample().gate_outcome == (
        "COUNTEREXAMPLE_FOUND"
    )


def test_active_module_has_no_pr151_data_or_automatic_evalue_surface() -> None:
    source = (
        ROOT / "htt/src/common/anchor_geometry.py"
    ).read_text(encoding="utf-8")
    assert "PR-151" not in source
    assert "DESI" not in source
    assert "def e_value" not in source
    assert "class EValue" not in source
    assert "universal_winner: None = None" in source
    assert "scalar_score: None = None" in source
