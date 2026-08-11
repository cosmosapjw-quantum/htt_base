"""PR-288 strict Bayesian semantics tests; legacy summary APIs are not authority."""

from __future__ import annotations

from copy import copy, deepcopy
import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml

from htt.infer.bayesian_semantics import (
    BayesianSemanticsReceipt,
    BayesianSemanticsError,
    EngineRunStatus,
    analytic_log_evidence,
    compare_independent_evidence,
    build_weighted_posterior_draws,
    build_bayesian_semantics_receipt,
    canonical_content_id,
    draw_conjugate_gaussian_posterior,
    load_registered_fixtures,
    run_dynesty_evidence,
    run_foldwise_loocv,
    run_posterior_draw_ppc,
    run_registered_posterior_predictive,
    run_scrambled_sobol_evidence,
    validate_engine_evidence_result,
    validate_bayesian_semantics_receipt,
    validate_loocv_receipt,
    validate_posterior_predictive_receipt,
)
from htt.infer import (
    BayesianSemanticsReceipt as PublicBayesianSemanticsReceipt,
    build_bayesian_semantics_receipt as public_build_receipt,
    validate_bayesian_semantics_receipt as public_validate_receipt,
)
import htt.infer.bayesian_semantics as bayesian_semantics


ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "docs/research_program/post_pr275/pr288_spec.yaml"
RUNNER = ROOT / "scripts/codex_harness/run_pr288_bayesian_semantics.py"


def _load_runner_module():
    module_spec = importlib.util.spec_from_file_location("pr288_runner_test", RUNNER)
    assert module_spec is not None and module_spec.loader is not None
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def test_strict_aggregate_api_is_reexported_without_replacing_legacy_api() -> None:
    assert PublicBayesianSemanticsReceipt is BayesianSemanticsReceipt
    assert public_build_receipt is build_bayesian_semantics_receipt
    assert public_validate_receipt is validate_bayesian_semantics_receipt


def test_registered_fixtures_freeze_normalization_rank_and_negative_control() -> None:
    fixtures = load_registered_fixtures(SPEC)
    assert tuple(fixtures) == (
        "PR288-NORMAL-MEAN-ANALYTIC",
        "PR288-NULL-EQUAL-MODELS-A",
        "PR288-NULL-EQUAL-MODELS-B",
        "PR288-REGISTERED-CORRELATED-NUISANCE",
        "PR288-MISSPECIFIED-NEGATIVE-CONTROL",
    )
    normal = fixtures["PR288-NORMAL-MEAN-ANALYTIC"]
    correlated = fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"]
    negative = fixtures["PR288-MISSPECIFIED-NEGATIVE-CONTROL"]
    assert normal.dimension == 1
    assert np.linalg.matrix_rank(correlated.design_matrix) == 3
    assert np.linalg.matrix_rank(correlated.covariance) == 4
    shift = abs(
        analytic_log_evidence(correlated)
        - analytic_log_evidence(negative)
    )
    assert shift >= 0.05
    assert negative.negative_control_terminal == (
        "MISSPECIFIED_NEGATIVE_CONTROL_VISIBLE"
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    (
        (
            lambda payload: payload.update({"claim_tier": "scientific"}),
            "claim boundary",
        ),
        (
            lambda payload: payload.update(
                {"family_identification_gate": "PASS"}
            ),
            "claim boundary",
        ),
        (
            lambda payload: payload["receipt_contract"][
                "required_metadata"
            ].remove("caveats"),
            "receipt metadata",
        ),
    ),
)
def test_frozen_spec_claim_and_receipt_contracts_fail_closed(
    tmp_path, mutate, message
) -> None:
    payload = deepcopy(yaml.safe_load(SPEC.read_text(encoding="utf-8")))
    mutate(payload)
    mutated = tmp_path / "pr288_spec.yaml"
    mutated.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    with pytest.raises(BayesianSemanticsError, match=message):
        load_registered_fixtures(mutated)


def test_scrambled_sobol_is_independent_linear_z_ensemble_with_accuracy() -> None:
    fixture = load_registered_fixtures(SPEC)["PR288-NORMAL-MEAN-ANALYTIC"]
    result = run_scrambled_sobol_evidence(fixture, spec_path=SPEC)
    assert result.status is EngineRunStatus.PASS
    assert result.engine_id == "SCIPY_SOBOL_QMC"
    assert result.effective_or_live_sample_count == 8 * 2**14
    assert len(result.independent_linear_evidence_estimates) == 8
    assert len(set(result.scramble_or_seed_inventory)) == 8
    expected = analytic_log_evidence(fixture)
    assert abs(result.log_evidence - expected) <= max(
        0.05, 3 * result.declared_standard_uncertainty
    )
    assert validate_engine_evidence_result(result) is result


def test_dynesty_is_mandatory_and_never_silently_skipped() -> None:
    fixture = load_registered_fixtures(SPEC)["PR288-NORMAL-MEAN-ANALYTIC"]
    result = run_dynesty_evidence(fixture, spec_path=SPEC)
    installed = importlib.util.find_spec("dynesty") is not None
    if installed:
        assert result.status is EngineRunStatus.PASS
        assert result.log_evidence is not None
        assert result.declared_standard_uncertainty is not None
    else:
        assert result.status is EngineRunStatus.BLOCKED_REQUIRED_ENGINE_UNAVAILABLE
        assert result.log_evidence is None
        assert result.declared_standard_uncertainty is None
        assert result.termination_status == "BLOCKED_REQUIRED_ENGINE_UNAVAILABLE"


def test_dynesty_below_registered_version_floor_blocks(monkeypatch) -> None:
    fixture = load_registered_fixtures(SPEC)["PR288-NORMAL-MEAN-ANALYTIC"]
    original_import = bayesian_semantics.importlib.import_module

    def import_module(name: str):
        if name == "dynesty":
            return SimpleNamespace(__version__="2.1.5")
        return original_import(name)

    monkeypatch.setattr(
        bayesian_semantics.importlib,
        "import_module",
        import_module,
    )
    result = run_dynesty_evidence(fixture, spec_path=SPEC)
    assert result.status is EngineRunStatus.BLOCKED_REQUIRED_ENGINE_UNAVAILABLE
    assert result.engine_version == "dynesty-2.1.5"


def test_engine_crosscheck_rejects_shared_estimate_or_identity_drift() -> None:
    fixture = load_registered_fixtures(SPEC)["PR288-NORMAL-MEAN-ANALYTIC"]
    sobol = run_scrambled_sobol_evidence(fixture, spec_path=SPEC)
    fake_dynesty = copy(sobol)
    object.__setattr__(fake_dynesty, "engine_id", "DYNESTY_NESTED")
    with pytest.raises(BayesianSemanticsError, match="independent estimate"):
        compare_independent_evidence(fake_dynesty, sobol, spec_path=SPEC)

    mutant = copy(sobol)
    object.__setattr__(mutant, "log_evidence", sobol.log_evidence + 1.0)
    with pytest.raises(BayesianSemanticsError, match="content identity drifted"):
        validate_engine_evidence_result(mutant)


def test_ppc_computes_weighted_replicates_and_counts_equality_in_tail() -> None:
    fixture = load_registered_fixtures(SPEC)[
        "PR288-REGISTERED-CORRELATED-NUISANCE"
    ]
    draws = draw_conjugate_gaussian_posterior(fixture, draw_count=512, seed=288201)
    counter = {"index": 0}

    def generator(theta, rng):
        del theta, rng
        index = counter["index"]
        counter["index"] += 1
        value = 1.0 if index < 256 else 0.0
        return np.array([value])

    receipt = run_posterior_draw_ppc(
        draws=draws,
        observed_data=np.array([1.0]),
        replicate_seed=288202,
        replicate_generator=generator,
        discrepancy=lambda values, theta: float(values[0]),
        discrepancy_statistic_identity="PR288-TEST-EQUALITY-DISCREPANCY-V1",
    )
    assert receipt.posterior_predictive_pvalue == pytest.approx(0.5)
    assert sum(receipt.comparison_indicators) == 256
    assert receipt.equality_rule == (
        "replicated_discrepancy_greater_or_equal_observed_counts_in_tail"
    )
    assert validate_posterior_predictive_receipt(receipt, draws=draws) is receipt
    assert "pvalue" not in inspect.signature(run_posterior_draw_ppc).parameters
    assert "predicted" not in inspect.signature(run_posterior_draw_ppc).parameters


def test_ppc_rejects_too_few_draws_and_draw_identity_drift() -> None:
    fixture = load_registered_fixtures(SPEC)["PR288-NORMAL-MEAN-ANALYTIC"]
    rng = np.random.default_rng(1)
    with pytest.raises(BayesianSemanticsError, match="at least 256"):
        build_weighted_posterior_draws(
            model_and_likelihood_identity=fixture.fixture_content_id,
            parameter_names=("mu",),
            samples=rng.normal(size=(255, 1)),
            weights=np.ones(255),
        )
    draws = build_weighted_posterior_draws(
        model_and_likelihood_identity=fixture.fixture_content_id,
        parameter_names=("mu",),
        samples=rng.normal(size=(256, 1)),
        weights=np.ones(256),
    )
    mutant = copy(draws)
    object.__setattr__(mutant, "posterior_sample_content_sha256", "sha256:" + "0" * 64)
    with pytest.raises(BayesianSemanticsError, match="draw identity drifted"):
        run_posterior_draw_ppc(
            draws=mutant,
            observed_data=np.array([0.0]),
            replicate_seed=4,
            replicate_generator=lambda theta, rng: np.array([theta[0] + rng.normal()]),
            discrepancy=lambda values, theta: abs(float(values[0])),
            discrepancy_statistic_identity="PR288-ABS-V1",
        )


def test_registered_ppc_uses_gaussian_replicates_and_drawwise_residuals() -> None:
    fixture = load_registered_fixtures(SPEC)[
        "PR288-REGISTERED-CORRELATED-NUISANCE"
    ]
    draws, receipt = run_registered_posterior_predictive(
        fixture, spec_path=SPEC
    )
    assert len(draws.samples) == 512
    assert receipt.posterior_draw_content_id == draws.draw_content_id
    assert len(receipt.observed_discrepancies) == 512
    assert len(receipt.replicated_discrepancies) == 512
    assert 0.0 <= receipt.posterior_predictive_pvalue <= 1.0
    assert receipt.model_and_likelihood_identity == fixture.fixture_content_id
    assert validate_posterior_predictive_receipt(receipt, draws=draws) is receipt


def test_loocv_refits_each_registered_fold_and_integrates_draw_density() -> None:
    fixture = load_registered_fixtures(SPEC)[
        "PR288-REGISTERED-CORRELATED-NUISANCE"
    ]
    receipt = run_foldwise_loocv(fixture, spec_path=SPEC)
    assert receipt.registered_fold_order == (
        "CHANNEL-1",
        "CHANNEL-2",
        "CHANNEL-3",
        "CHANNEL-4",
    )
    assert tuple(row.held_out_id for row in receipt.fold_results) == (
        "CHANNEL-1",
        "CHANNEL-2",
        "CHANNEL-3",
        "CHANNEL-4",
    )
    assert all(row.posterior_draw_count == 512 for row in receipt.fold_results)
    assert len({row.training_input_identity for row in receipt.fold_results}) == 4
    assert len({row.posterior_draw_identity for row in receipt.fold_results}) == 4
    assert all(row.fit_status == "PASS_FOLDWISE_NUISANCE_REFIT" for row in receipt.fold_results)
    assert receipt.aggregate_log_predictive_density == pytest.approx(
        sum(row.integrated_held_out_log_predictive_density for row in receipt.fold_results)
    )
    assert validate_loocv_receipt(receipt, fixture=fixture, spec_path=SPEC) is receipt


def test_loocv_rejects_full_posterior_reuse_and_fold_inventory_drift() -> None:
    fixture = load_registered_fixtures(SPEC)[
        "PR288-REGISTERED-CORRELATED-NUISANCE"
    ]
    receipt = run_foldwise_loocv(fixture, spec_path=SPEC)
    mutant = copy(receipt)
    object.__setattr__(mutant, "fold_results", receipt.fold_results[:-1])
    with pytest.raises(BayesianSemanticsError, match="fold inventory"):
        validate_loocv_receipt(mutant, fixture=fixture, spec_path=SPEC)

    reused = copy(receipt)
    second = copy(receipt.fold_results[1])
    object.__setattr__(
        second,
        "posterior_draw_identity",
        receipt.fold_results[0].posterior_draw_identity,
    )
    object.__setattr__(
        reused,
        "fold_results",
        (receipt.fold_results[0], second, *receipt.fold_results[2:]),
    )
    with pytest.raises(BayesianSemanticsError, match="posterior draw identity"):
        validate_loocv_receipt(reused, fixture=fixture, spec_path=SPEC)
    assert "fold_log_evidence" not in inspect.signature(run_foldwise_loocv).parameters
    assert "full_posterior" not in inspect.signature(run_foldwise_loocv).parameters


def _independent_test_dynesty(fixture, *, spec_path):
    """Deterministic unit substitute; acceptance still requires real Dynesty."""

    sobol = run_scrambled_sobol_evidence(fixture, spec_path=spec_path)
    result = copy(sobol)
    object.__setattr__(result, "engine_id", "DYNESTY_NESTED")
    object.__setattr__(result, "engine_version", "dynesty-3.0.0-test-double")
    object.__setattr__(result, "termination_status", "COMPLETED_DLOGZ_THRESHOLD")
    registered_seed = bayesian_semantics._engine_config(
        spec_path, "DYNESTY_NESTED"
    )["fixture_seeds"][fixture.fixture_id]
    object.__setattr__(result, "scramble_or_seed_inventory", (registered_seed,))
    object.__setattr__(
        result,
        "sample_or_node_inventory_content_id",
        canonical_content_id(
            {"domain": "PR288_TEST_DYNESTY_SAMPLES", "fixture": fixture.fixture_content_id}
        ),
    )
    object.__setattr__(
        result,
        "independent_estimate_content_id",
        canonical_content_id(
            {"domain": "PR288_TEST_DYNESTY_ESTIMATE", "fixture": fixture.fixture_content_id}
        ),
    )
    object.__setattr__(result, "independent_linear_evidence_estimates", ())
    object.__setattr__(
        result,
        "result_content_id",
        canonical_content_id(result.unsigned_payload()),
    )
    return validate_engine_evidence_result(result)


def test_aggregate_receipt_recomputes_all_registered_components_and_mutations(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        bayesian_semantics,
        "run_dynesty_evidence",
        _independent_test_dynesty,
    )
    receipt = build_bayesian_semantics_receipt(
        SPEC,
        repository_root=ROOT,
        generation_identity="UNIT_TEST_DOUBLE_NOT_ACCEPTANCE_EVIDENCE",
    )
    assert isinstance(receipt, BayesianSemanticsReceipt)
    assert receipt.terminal == "PASS_BAYESIAN_SEMANTICS_REPAIR"
    assert tuple(row.mutation_id for row in receipt.mutation_results) == tuple(
        row["mutation_id"]
        for row in bayesian_semantics._load_spec(SPEC)["mutation_registry"]
    )
    assert all(
        row.executed and row.activated and row.killed
        for row in receipt.mutation_results
    )
    assert receipt.null_control.status == "PASS_DEGENERATE_NULL_COMPATIBLE_WITH_ZERO"
    assert receipt.negative_control.status == "MISSPECIFIED_NEGATIVE_CONTROL_VISIBLE"
    assert validate_bayesian_semantics_receipt(
        receipt,
        spec_path=SPEC,
        repository_root=ROOT,
    ) is receipt


def test_aggregate_receipt_fails_closed_on_mutation_omission_and_claim_promotion(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        bayesian_semantics,
        "run_dynesty_evidence",
        _independent_test_dynesty,
    )
    receipt = build_bayesian_semantics_receipt(
        SPEC,
        repository_root=ROOT,
        generation_identity="UNIT_TEST_DOUBLE_NOT_ACCEPTANCE_EVIDENCE",
    )
    omitted = copy(receipt)
    object.__setattr__(omitted, "mutation_results", receipt.mutation_results[:-1])
    with pytest.raises(BayesianSemanticsError, match="mutation inventory"):
        validate_bayesian_semantics_receipt(
            omitted,
            spec_path=SPEC,
            repository_root=ROOT,
        )

    promoted = copy(receipt)
    promoted_metadata = dict(receipt.metadata)
    promoted_metadata["observed_data_executed"] = True
    object.__setattr__(promoted, "metadata", promoted_metadata)
    with pytest.raises(BayesianSemanticsError, match="claim metadata"):
        validate_bayesian_semantics_receipt(
            promoted,
            spec_path=SPEC,
            repository_root=ROOT,
        )


def test_builder_revalidates_mutation_executor_output(monkeypatch) -> None:
    monkeypatch.setattr(
        bayesian_semantics,
        "run_dynesty_evidence",
        _independent_test_dynesty,
    )
    original = bayesian_semantics._run_registered_mutations

    def omit_last_mutation(**kwargs):
        return original(**kwargs)[:-1]

    monkeypatch.setattr(
        bayesian_semantics,
        "_run_registered_mutations",
        omit_last_mutation,
    )
    with pytest.raises(BayesianSemanticsError, match="mutation inventory"):
        build_bayesian_semantics_receipt(
            SPEC,
            repository_root=ROOT,
            generation_identity="UNIT_TEST_DOUBLE_NOT_ACCEPTANCE_EVIDENCE",
        )


def test_runner_rejects_hardlinked_destination_before_computation(
    monkeypatch, tmp_path
) -> None:
    runner = _load_runner_module()
    generated = tmp_path / "docs/generated"
    generated.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("preserve", encoding="utf-8")
    destination = generated / "receipt.json"
    destination.hardlink_to(outside)
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "OUTPUT", destination)

    def must_not_build():
        raise AssertionError("builder ran before destination preflight")

    monkeypatch.setattr(runner, "_build", must_not_build)
    assert runner._write() == 1
    assert outside.read_text(encoding="utf-8") == "preserve"


def test_aggregate_receipt_blocks_when_required_dynesty_is_unavailable() -> None:
    if importlib.util.find_spec("dynesty") is not None:
        pytest.skip("system environment has the required engine")
    receipt = build_bayesian_semantics_receipt(
        SPEC,
        repository_root=ROOT,
        generation_identity="SYSTEM_REQUIRED_ENGINE_PROBE",
    )
    assert receipt.terminal == "BLOCKED_DEPENDENCY_OR_ENGINE"
    assert any(
        row.status is EngineRunStatus.BLOCKED_REQUIRED_ENGINE_UNAVAILABLE
        for row in receipt.engine_results
    )
    assert validate_bayesian_semantics_receipt(
        receipt,
        spec_path=SPEC,
        repository_root=ROOT,
    ) is receipt
