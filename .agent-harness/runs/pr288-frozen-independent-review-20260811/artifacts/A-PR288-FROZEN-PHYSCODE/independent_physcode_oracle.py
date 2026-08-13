#!/usr/bin/env python3
"""Independent frozen PR-288 physics/statistics/code oracle.

This oracle deliberately recomputes the mathematical checks from the registered
fixture arrays and serialized receipt rather than trusting status strings.
"""

from __future__ import annotations

import argparse
from copy import copy
import hashlib
import importlib
import importlib.metadata
import json
import math
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from scipy.stats import multivariate_normal, norm
import yaml


ROOT = Path(__file__).resolve().parents[5]
SPEC = ROOT / "docs/research_program/post_pr275/pr288_spec.yaml"
RECEIPT = ROOT / "docs/generated/pr288_bayesian_semantics_receipt.json"
RUNNER = ROOT / "scripts/codex_harness/run_pr288_bayesian_semantics.py"
EXPECTED_SOURCE_BINDINGS = (
    "docs/research_program/post_pr275/pr288_spec.yaml",
    "docs/research_program/post_pr275/pr288_publication_policy.json",
    "htt/htt/htt/infer/bayesian_semantics.py",
    "scripts/codex_harness/run_pr288_bayesian_semantics.py",
    "tests/htt/test_bayesian_semantics_repair.py",
    "docs/PR_DELTAS/pr-280.md",
    "docs/research_program/post_pr275/full_inventory_v4_receipt.json",
)


def canonical_id(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def without(row: dict[str, object], key: str) -> dict[str, object]:
    return {name: value for name, value in row.items() if name != key}


def assert_finite_tree(value: object, path: str = "$") -> None:
    if isinstance(value, float):
        assert math.isfinite(value), f"non-finite value at {path}"
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_finite_tree(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_finite_tree(item, f"{path}[{index}]")


def activate_sources() -> None:
    for path in reversed((ROOT / "htt", ROOT / "htt/src")):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def independent_fold_log_density(fixture, held_out_index: int) -> float:
    all_indices = np.arange(len(fixture.observations), dtype=int)
    train = all_indices[all_indices != held_out_index]
    covariance_train = fixture.covariance[np.ix_(train, train)]
    cross = fixture.covariance[held_out_index, train]
    gain = cross @ np.linalg.inv(covariance_train)
    conditional_variance = float(
        fixture.covariance[held_out_index, held_out_index]
        - gain @ fixture.covariance[train, held_out_index]
    )

    prior_precision = np.linalg.inv(fixture.prior_covariance)
    noise_precision = np.linalg.inv(covariance_train)
    design_train = fixture.design_matrix[train, :]
    posterior_covariance = np.linalg.inv(
        prior_precision + design_train.T @ noise_precision @ design_train
    )
    posterior_mean = posterior_covariance @ (
        prior_precision @ fixture.prior_mean
        + design_train.T @ noise_precision @ fixture.observations[train]
    )

    coefficient = fixture.design_matrix[held_out_index, :] - gain @ design_train
    offset = float(gain @ fixture.observations[train])
    predictive_mean = float(coefficient @ posterior_mean + offset)
    predictive_variance = float(
        conditional_variance
        + coefficient @ posterior_covariance @ coefficient
    )
    assert conditional_variance > 0.0 and predictive_variance > 0.0
    return float(
        norm.logpdf(
            fixture.observations[held_out_index],
            loc=predictive_mean,
            scale=math.sqrt(predictive_variance),
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.resolve().relative_to(ROOT.resolve())

    activate_sources()
    bs = importlib.import_module("htt.infer.bayesian_semantics")
    assert Path(bs.__file__).resolve() == (
        ROOT / "htt/htt/htt/infer/bayesian_semantics.py"
    ).resolve()

    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    frozen = json.loads(RECEIPT.read_text(encoding="utf-8"))
    assert_finite_tree(frozen)
    checks: dict[str, object] = {}

    # Byte/content bindings and all serialized component addresses.
    assert frozen["receipt_content_id"] == canonical_id(
        without(frozen, "receipt_content_id")
    )
    component_rules = (
        ("engine_results", "result_content_id"),
        ("mutation_results", "result_content_id"),
    )
    for collection, identity in component_rules:
        for row in frozen[collection]:
            assert row[identity] == canonical_id(without(row, identity))
    for name, identity in (
        ("degenerate_null_control", "control_content_id"),
        ("negative_control", "control_content_id"),
        ("posterior_draws", "draw_content_id"),
        ("posterior_predictive", "receipt_content_id"),
        ("loocv", "receipt_content_id"),
        ("dependency_receipt", "receipt_content_id"),
    ):
        row = frozen[name]
        assert row[identity] == canonical_id(without(row, identity))
    bindings = frozen["source_bindings"]
    assert tuple(row["path"] for row in bindings) == EXPECTED_SOURCE_BINDINGS
    for row in bindings:
        assert row["sha256"] == file_sha256(ROOT / row["path"])
    assert frozen["generation_identity"] == (
        "BOUND_SOURCE_WORKTREE:" + canonical_id(bindings)
    )
    checks["finite_and_content_addressed_receipt"] = True

    # Independent normalized Gaussian marginal evidence and unit/rank checks.
    fixtures = bs.load_registered_fixtures(SPEC)
    analytic: dict[str, float] = {}
    ranks: dict[str, object] = {}
    for fixture_id, fixture in fixtures.items():
        marginal_mean = fixture.design_matrix @ fixture.prior_mean
        marginal_covariance = (
            fixture.covariance
            + fixture.design_matrix
            @ fixture.prior_covariance
            @ fixture.design_matrix.T
        )
        independent = float(
            multivariate_normal.logpdf(
                fixture.observations,
                mean=marginal_mean,
                cov=marginal_covariance,
            )
        )
        assert math.isclose(
            independent,
            bs.analytic_log_evidence(fixture),
            rel_tol=0.0,
            abs_tol=2e-13,
        )
        assert fixture.units == "dimensionless_registered_synthetic"
        assert fixture.base_measure == "Lebesgue_parameter_and_observation_measure"
        assert np.all(np.linalg.eigvalsh(fixture.covariance) > 0.0)
        assert np.all(np.linalg.eigvalsh(fixture.prior_covariance) > 0.0)
        analytic[fixture_id] = independent
        ranks[fixture_id] = {
            "design_rank": int(np.linalg.matrix_rank(fixture.design_matrix)),
            "design_columns": int(fixture.design_matrix.shape[1]),
            "covariance_rank": int(np.linalg.matrix_rank(fixture.covariance)),
            "covariance_rows": int(fixture.covariance.shape[0]),
        }
        assert ranks[fixture_id]["design_rank"] == ranks[fixture_id]["design_columns"]
        assert ranks[fixture_id]["covariance_rank"] == ranks[fixture_id]["covariance_rows"]
    checks["independent_analytic_log_evidence"] = analytic
    checks["registered_ranks"] = ranks

    # Real independent engines, uncertainty calibration, and exact frozen replay.
    assert importlib.metadata.version("dynesty") == "3.0.0"
    live = bs.build_bayesian_semantics_receipt(SPEC, repository_root=ROOT)
    bs.validate_bayesian_semantics_receipt(
        live, spec_path=SPEC, repository_root=ROOT
    )
    assert live.payload() == frozen
    results = frozen["engine_results"]
    assert len(results) == 10
    node_ids = [row["sample_or_node_inventory_content_id"] for row in results]
    estimate_ids = [row["independent_estimate_content_id"] for row in results]
    assert len(set(node_ids)) == len(node_ids)
    assert len(set(estimate_ids)) == len(estimate_ids)
    for index in range(0, len(results), 2):
        dynesty_row, sobol_row = results[index : index + 2]
        assert dynesty_row["engine_id"] == "DYNESTY_NESTED"
        assert dynesty_row["engine_version"] == "dynesty-3.0.0"
        assert dynesty_row["status"] == "PASS"
        assert sobol_row["engine_id"] == "SCIPY_SOBOL_QMC"
        assert sobol_row["status"] == "PASS"
        assert dynesty_row["fixture_id"] == sobol_row["fixture_id"]
        assert dynesty_row["sample_or_node_inventory_content_id"] != sobol_row[
            "sample_or_node_inventory_content_id"
        ]
        assert dynesty_row["independent_estimate_content_id"] != sobol_row[
            "independent_estimate_content_id"
        ]
        estimates = np.asarray(
            sobol_row["independent_linear_evidence_estimates"], dtype=float
        )
        assert estimates.shape == (8,)
        assert np.all(np.isfinite(estimates)) and np.all(estimates > 0.0)
        linear_mean = float(np.mean(estimates))
        linear_se = float(np.std(estimates, ddof=1) / math.sqrt(8.0))
        assert math.isclose(
            sobol_row["log_evidence"], math.log(linear_mean), abs_tol=2e-15
        )
        assert math.isclose(
            sobol_row["declared_standard_uncertainty"],
            linear_se / linear_mean,
            rel_tol=2e-15,
            abs_tol=1e-18,
        )
        assert len(set(sobol_row["scramble_or_seed_inventory"])) == 8
        assert sobol_row["likelihood_call_count"] == 8 * 2**14
    checks["dynesty_3_and_scrambled_sobol_independence"] = True

    crosschecks = frozen["evidence_crosschecks"]
    for index, row in enumerate(crosschecks):
        first, second = results[2 * index : 2 * index + 2]
        expected_difference = abs(first["log_evidence"] - second["log_evidence"])
        expected_threshold = max(
            0.02,
            3.0
            * math.sqrt(
                first["declared_standard_uncertainty"] ** 2
                + second["declared_standard_uncertainty"] ** 2
            ),
        )
        assert math.isclose(row["absolute_log_evidence_difference"], expected_difference)
        assert math.isclose(row["threshold"], expected_threshold)
        assert expected_difference <= expected_threshold
        expected_analytic = analytic[row["fixture_id"]]
        assert math.isclose(row["analytic_log_evidence"], expected_analytic, abs_tol=2e-13)
        for engine in (first, second):
            assert abs(engine["log_evidence"] - expected_analytic) <= max(
                0.05, 3.0 * engine["declared_standard_uncertainty"]
            )
    checks["combined_uncertainty_and_analytic_thresholds"] = True

    # Identical-model null and covariance misspecification visibility.
    null = frozen["degenerate_null_control"]
    assert null["status"] == "PASS_DEGENERATE_NULL_COMPATIBLE_WITH_ZERO"
    for engine_id, bayes_factor in null["log_bayes_factors"].items():
        threshold = null["compatibility_thresholds"][engine_id]
        assert abs(bayes_factor) <= threshold
    negative = frozen["negative_control"]
    independent_shift = abs(
        analytic["PR288-REGISTERED-CORRELATED-NUISANCE"]
        - analytic["PR288-MISSPECIFIED-NEGATIVE-CONTROL"]
    )
    assert math.isclose(negative["analytic_log_evidence_shift"], independent_shift)
    assert independent_shift >= negative["required_minimum_shift"] == 0.05
    assert negative["status"] == "MISSPECIFIED_NEGATIVE_CONTROL_VISIBLE"
    checks["null_and_covariance_negative_controls"] = {
        "null_log_bayes_factors": null["log_bayes_factors"],
        "analytic_covariance_shift": independent_shift,
    }

    # Weighted replicated PPC with an equality-only contribution to the tail.
    ppc_fixture = fixtures["PR288-REGISTERED-CORRELATED-NUISANCE"]
    samples = np.zeros((256, ppc_fixture.dimension), dtype=float)
    raw_weights = np.arange(1.0, 257.0)
    draws = bs.build_weighted_posterior_draws(
        model_and_likelihood_identity=ppc_fixture.fixture_content_id,
        parameter_names=("signal", "nuisance_a", "nuisance_b"),
        samples=samples,
        weights=raw_weights,
    )
    counter = {"index": 0}

    def generator(theta, rng):
        del theta, rng
        index = counter["index"]
        counter["index"] += 1
        return np.array([1.0 if index < 64 else (2.0 if index < 128 else 0.0)])

    equality_ppc = bs.run_posterior_draw_ppc(
        draws=draws,
        observed_data=np.array([1.0]),
        replicate_seed=9917,
        replicate_generator=generator,
        discrepancy=lambda values, theta: float(values[0]),
        discrepancy_statistic_identity="PR288-INDEPENDENT-EQUALITY-ORACLE-V1",
    )
    expected_pvalue = float(np.sum(draws.normalized_weights[:128]))
    strict_only = float(np.sum(draws.normalized_weights[64:128]))
    assert math.isclose(equality_ppc.posterior_predictive_pvalue, expected_pvalue)
    assert not math.isclose(expected_pvalue, strict_only)
    assert tuple(equality_ppc.comparison_indicators[:128]) == (1,) * 128
    assert tuple(equality_ppc.comparison_indicators[128:]) == (0,) * 128
    registered_draws, registered_ppc = bs.run_registered_posterior_predictive(
        ppc_fixture, spec_path=SPEC
    )
    assert registered_ppc.unsigned_payload() == without(
        frozen["posterior_predictive"], "receipt_content_id"
    )
    assert registered_draws.unsigned_payload() == without(
        frozen["posterior_draws"], "draw_content_id"
    )
    checks["replicated_ppc_equality_tail"] = {
        "weighted_ge_pvalue": expected_pvalue,
        "strict_gt_only": strict_only,
        "registered_pvalue": registered_ppc.posterior_predictive_pvalue,
    }

    # Foldwise refit and conditional correlated holdout, checked against the
    # exact Gaussian posterior predictive distribution (not the MC draws).
    loocv = bs.run_foldwise_loocv(ppc_fixture, spec_path=SPEC)
    assert loocv.unsigned_payload() == without(frozen["loocv"], "receipt_content_id")
    exact_fold_values: dict[str, float] = {}
    errors: dict[str, float] = {}
    posterior_ids = []
    for index, row in enumerate(loocv.fold_results):
        exact = independent_fold_log_density(ppc_fixture, index)
        error = row.integrated_held_out_log_predictive_density - exact
        assert abs(error) < 0.02
        exact_fold_values[row.held_out_id] = exact
        errors[row.held_out_id] = error
        posterior_ids.append(row.posterior_draw_identity)
    assert len(set(posterior_ids)) == 4
    assert tuple(row.fold_seed for row in loocv.fold_results) == (
        288301,
        288302,
        288303,
        288304,
    )
    checks["foldwise_refit_conditional_loocv"] = {
        "exact_log_predictive_density": exact_fold_values,
        "monte_carlo_minus_exact": errors,
        "max_abs_error": max(abs(value) for value in errors.values()),
    }

    # Stable release policy rejects release candidates and dev versions.
    original_import = bs.importlib.import_module
    prerelease_statuses: dict[str, str] = {}
    fixture = fixtures["PR288-NORMAL-MEAN-ANALYTIC"]
    for version in ("3.0.0rc1", "3.0.0.dev1"):
        def fake_import(name: str, *, _version: str = version):
            if name == "dynesty":
                return SimpleNamespace(__version__=_version)
            return original_import(name)

        with patch.object(bs.importlib, "import_module", fake_import):
            blocked = bs.run_dynesty_evidence(fixture, spec_path=SPEC)
        assert blocked.status.value == "BLOCKED_REQUIRED_ENGINE_UNAVAILABLE"
        prerelease_statuses[version] = blocked.status.value
    checks["dynesty_prerelease_refusal"] = prerelease_statuses

    # The failed PR-280 terminal is accepted only as a terminal receipt and has
    # stronger precedence than otherwise successful engines.
    dependency = frozen["dependency_receipt"]
    assert dependency["resolution"] == "COMPLETED_FAILED_WITH_RECEIPT"
    assert dependency["success_dependency_satisfied"] is False
    assert dependency["status"] == "PASS_REQUIRED_TERMINAL_RECEIPT"
    blocked_terminal, blocked_reasons = bs._derive_terminal(
        dependency_receipt={"status": "BLOCKED_REQUIRED_TERMINAL_RECEIPT"},
        engine_results=live.engine_results,
        crosschecks=live.evidence_crosschecks,
        null_control=live.null_control,
        negative_control=live.negative_control,
        ppc=live.posterior_predictive,
        loocv=live.loocv,
        mutation_results=live.mutation_results,
    )
    assert blocked_terminal == "BLOCKED_DEPENDENCY_OR_ENGINE"
    assert "PR-280" in blocked_reasons[0]
    checks["pr280_failed_terminal_precedence"] = True

    # Missing system engine is a typed blocker, not a scientific FAIL.
    system = subprocess.run(
        ["/usr/bin/python3", "-B", str(RUNNER), "engines"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    assert system.returncode == 2
    system_payload = json.loads(system.stdout)
    assert system_payload["terminal"] == "BLOCKED_DEPENDENCY_OR_ENGINE"
    assert all(
        row["status"] == "BLOCKED_REQUIRED_ENGINE_UNAVAILABLE"
        for row in system_payload["engine_results"]
        if row["engine_id"] == "DYNESTY_NESTED"
    )
    checks["system_engine_typed_inconclusive"] = {
        "returncode": system.returncode,
        "terminal": system_payload["terminal"],
    }

    metadata = frozen["metadata"]
    assert metadata["owner"] == "HTT"
    assert metadata["claim_tier"] == "diagnostic_only"
    assert metadata["claim_level"] == {"scheme": "roadmap_rescue_v1", "level": "C2"}
    assert metadata["transfer_source"] == "none"
    assert metadata["observed_data_executed"] is False
    assert metadata["public_use"] is False
    assert metadata["family_identification_gate"] == "BLOCKED_PRE_NATIVE_ATLAS"
    assert metadata["scientific_status_effect"] == "OPEN_UNCHANGED"
    assert metadata["legacy_disposition"]["status"] == "LEGACY_REPRODUCTION_ONLY"
    assert "MIO posterior or MIO evidence" in metadata["forbidden_uses"]
    checks["ownership_legacy_and_family_gate"] = True

    assert frozen["terminal"] == "PASS_BAYESIAN_SEMANTICS_REPAIR"
    assert frozen["reasons"] == []
    assert len(frozen["mutation_results"]) == 15
    assert all(
        row["executed"] and row["activated"] and row["killed"]
        for row in frozen["mutation_results"]
    )
    checks["registered_mutations"] = {"executed_and_killed": 15}

    report = {
        "schema": "HTT_PR288_INDEPENDENT_PHYSCODE_ORACLE_V1",
        "candidate_sha": "dcde762d1ce3027e01edcf2744398f7588bb5fb1",
        "receipt_sha256": file_sha256(RECEIPT),
        "receipt_content_id": frozen["receipt_content_id"],
        "status": "PASS",
        "checks": checks,
    }
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
