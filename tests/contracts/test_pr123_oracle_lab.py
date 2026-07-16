from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import yaml

from common.oracle_lab import (
    FROZEN_MUTATION_IDS,
    OracleLabError,
    PropertyResult,
    make_outcome,
    validate_seed_ledger,
    validate_outcomes,
)
from common.oracle_references import (
    NumericInterval,
    asymmetric_rank_pvalues,
    callable_range_only_contains,
    conjugate_normal_log_bf,
    constrained_shell_weights,
    fitted_normal_score,
    pooled_rank_pvalues,
    quadrature_normal_bf,
    real_noise_rfft,
    rfft_special_plane_residual,
    unconstrained_bulk_weights,
    unconstrained_complex_rfft,
    validated_range_contains,
)
import common.oracle_references as oracle_references


REPO_ROOT = Path(__file__).resolve().parents[2]
LINEAGE = REPO_ROOT / "docs/generated/pr123_oracle_lineage_manifest.json"
SPEC = REPO_ROOT / "docs/research_program/long_horizon_rescue/pr123_spec.yaml"


def _rng(seed: int) -> np.random.Generator:
    return np.random.Generator(np.random.PCG64DXSM(np.random.SeedSequence(seed)))


def _expected_registry() -> dict:
    spec = yaml.safe_load(SPEC.read_text(encoding="utf-8"))
    return {
        row["mutation_id"]: {
            "lane_id": row["lane_id"],
            "property_ids": tuple(row["property_ids"]),
            "reference_symbol": row["reference_symbol"],
            "mutant_symbol": row["mutant_symbol"],
            "fixture_hash": "a" * 64,
            "reference_execution_count": 1,
            "mutant_execution_count": 1,
            "metric_keys": ("dummy_metric",),
        }
        for row in spec["mutation_registry"]
    }


def _bound_dummy_outcome(mutation_id: str, *, lane_override: str | None = None):
    expected = _expected_registry()[mutation_id]
    return make_outcome(
        mutation_id,
        lane_override or expected["lane_id"],
        tuple(
            PropertyResult(property_id, True, 0.0, 0.0, "fixture")
            for property_id in expected["property_ids"]
        ),
        reference_symbol=expected["reference_symbol"],
        mutant_symbol=expected["mutant_symbol"],
        fixture_hash="a" * 64,
        reference_execution_count=1,
        mutant_execution_count=1,
        mutant_failed_properties=(expected["property_ids"][0],),
        metrics={"dummy_metric": 0.0},
    )


def test_shell_reference_enforces_constraints_that_known_mutant_leaks() -> None:
    rng = _rng(10)
    directions = rng.normal(size=(24, 3))
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    radius = np.linspace(0.0, 1.0, 24)
    shells = np.column_stack((radius < 0.43, radius > 0.66)).astype(float)
    variances = 0.5 + rng.random(24)
    clean = constrained_shell_weights(directions, shells, variances)
    mutant = unconstrained_bulk_weights(directions, variances)
    assert np.allclose(clean @ directions, np.eye(3), atol=1e-12)
    assert np.allclose(clean @ shells, 0.0, atol=1e-12)
    assert np.max(np.abs(mutant @ shells)) > 1e-3


def test_real_field_rfft_reference_exposes_malformed_special_planes() -> None:
    clean_rng = _rng(21)
    mutant_rng = _rng(22)
    _, clean = real_noise_rfft(12, clean_rng)
    mutant = unconstrained_complex_rfft(12, mutant_rng)
    assert rfft_special_plane_residual(clean, 12) < 1e-12
    assert rfft_special_plane_residual(mutant, 12) > 1e-3


def test_pooled_rank_is_label_free_while_asymmetric_mutant_is_not() -> None:
    scores = np.array([0.13, 0.71, -0.4, 1.8, 0.02, 0.9])
    clean = pooled_rank_pvalues(scores)
    assert np.allclose(np.sort(clean), np.arange(1, 7) / 6.0)
    deltas = [
        np.max(np.abs(asymmetric_rank_pvalues(scores, index) - clean))
        for index in range(scores.size)
    ]
    assert max(deltas) >= 1.0 / scores.size


def test_conjugate_evidence_has_occam_term_and_independent_quadrature() -> None:
    log_bf = conjugate_normal_log_bf(8, 1.0, 2.0, 0.3)
    fitted = fitted_normal_score(8, 1.0, 0.3)
    quadrature = quadrature_normal_bf(8, 1.0, 2.0, 0.3)
    assert log_bf < 0.0 < fitted
    assert np.exp(log_bf) == pytest.approx(quadrature, abs=2e-5)
    assert conjugate_normal_log_bf(8, 1.0, 0.5, 0.3) != pytest.approx(log_bf)


def test_validated_transfer_domain_rejects_stale_low_l_mutant() -> None:
    requested = NumericInterval(2.0, 10.0, True)
    callable_range = NumericInterval(2.0, 3000.0, True)
    validated = NumericInterval(40.0, 763.0, False)
    digest = "a" * 64
    assert not validated_range_contains(requested, callable_range, validated, digest, digest)
    assert callable_range_only_contains(requested, callable_range)
    assert not validated_range_contains(validated, callable_range, validated, "b" * 64, digest)


def test_fail_closed_aggregation_retains_a_surviving_lane() -> None:
    outcomes = [_bound_dummy_outcome(mid) for mid in FROZEN_MUTATION_IDS]
    row = outcomes[FROZEN_MUTATION_IDS.index("plugin_pseudo_ppc")]
    outcomes[FROZEN_MUTATION_IDS.index("plugin_pseudo_ppc")] = make_outcome(
        row.mutation_id,
        row.lane_id,
        row.properties,
        reference_symbol=row.reference_symbol,
        mutant_symbol=row.mutant_symbol,
        fixture_hash=row.fixture_hash,
        reference_execution_count=1,
        mutant_execution_count=1,
        mutant_failed_properties=(),
        metrics=row.metrics,
    )
    summary = validate_outcomes(outcomes, _expected_registry())
    assert summary["aggregate_status"] == "BLOCKED_MUTATION_LAB"
    assert summary["survivors"] == ["plugin_pseudo_ppc"]
    assert summary["scientific_status"] == "OPEN"
    assert summary["claim_promotion_allowed"] is False


def test_fail_closed_aggregation_rejects_registry_substitution() -> None:
    outcomes = [_bound_dummy_outcome(mid) for mid in FROZEN_MUTATION_IDS[:-1]]
    with pytest.raises(OracleLabError, match="registry mismatch"):
        validate_outcomes(outcomes, _expected_registry())


def test_fail_closed_aggregation_rejects_wrong_lane_property_or_symbol() -> None:
    outcomes = [_bound_dummy_outcome(mid) for mid in FROZEN_MUTATION_IDS]
    outcomes[0] = _bound_dummy_outcome(FROZEN_MUTATION_IDS[0], lane_override="WRONG-LANE")
    with pytest.raises(OracleLabError, match="lane_id"):
        validate_outcomes(outcomes, _expected_registry())

    outcomes = [_bound_dummy_outcome(mid) for mid in FROZEN_MUTATION_IDS]
    outcomes[0] = replace(
        outcomes[0],
        properties=(PropertyResult("WRONG-PROPERTY", True, 0, 0, "bad"),),
    )
    with pytest.raises(OracleLabError, match="property_ids"):
        validate_outcomes(outcomes, _expected_registry())

    outcomes = [_bound_dummy_outcome(mid) for mid in FROZEN_MUTATION_IDS]
    outcomes[0] = replace(outcomes[0], mutant_symbol="WRONG-MUTANT")
    with pytest.raises(OracleLabError, match="mutant_symbol"):
        validate_outcomes(outcomes, _expected_registry())


def test_fail_closed_aggregation_rejects_fixture_count_metric_or_receipt_tamper() -> None:
    for field, value, match in (
        ("fixture_hash", "z" * 64, "fixture_hash"),
        ("reference_execution_count", 2, "reference_execution_count"),
        ("metrics", {}, "metric_keys"),
        ("execution_receipt_hash", "f" * 64, "execution_receipt_hash"),
    ):
        outcomes = [_bound_dummy_outcome(mid) for mid in FROZEN_MUTATION_IDS]
        outcomes[0] = replace(outcomes[0], **{field: value})
        with pytest.raises(OracleLabError, match=match):
            validate_outcomes(outcomes, _expected_registry())


def test_fail_closed_aggregation_recomputes_clean_and_kill_state() -> None:
    expected = _expected_registry()[FROZEN_MUTATION_IDS[0]]
    properties = tuple(
        PropertyResult(
            property_id,
            property_id != expected["property_ids"][0],
            0.0,
            0.0,
            "derived-state fixture",
        )
        for property_id in expected["property_ids"]
    )
    failed_clean = make_outcome(
        FROZEN_MUTATION_IDS[0],
        expected["lane_id"],
        properties,
        reference_symbol=expected["reference_symbol"],
        mutant_symbol=expected["mutant_symbol"],
        fixture_hash="a" * 64,
        reference_execution_count=1,
        mutant_execution_count=1,
        mutant_failed_properties=(expected["property_ids"][0],),
        metrics={"dummy_metric": 0.0},
    )
    outcomes = [_bound_dummy_outcome(mid) for mid in FROZEN_MUTATION_IDS]
    outcomes[0] = replace(
        failed_clean,
        clean_passed=True,
        status="PASS_MECHANICS_C2",
    )
    with pytest.raises(OracleLabError, match="clean_passed"):
        validate_outcomes(outcomes, _expected_registry())

    survivor = make_outcome(
        FROZEN_MUTATION_IDS[0],
        expected["lane_id"],
        tuple(
            PropertyResult(property_id, True, 0.0, 0.0, "survivor fixture")
            for property_id in expected["property_ids"]
        ),
        reference_symbol=expected["reference_symbol"],
        mutant_symbol=expected["mutant_symbol"],
        fixture_hash="a" * 64,
        reference_execution_count=1,
        mutant_execution_count=1,
        mutant_failed_properties=(),
        metrics={"dummy_metric": 0.0},
    )
    outcomes[0] = replace(
        survivor,
        mutant_killed=True,
        status="PASS_MECHANICS_C2",
    )
    with pytest.raises(OracleLabError, match="mutant_killed"):
        validate_outcomes(outcomes, _expected_registry())


def test_seed_ledger_replays_spawn_key_role_generator_and_hash() -> None:
    root_seed = 202607123
    children = np.random.SeedSequence(root_seed).spawn(2)
    slots = [
        {"lane_id": "lane", "role": "role", "replicate": index, "spawn_key": [index]}
        for index in range(2)
    ]
    rows = [
        {
            **slot,
            "root_entropy": root_seed,
            "bit_generator": "PCG64DXSM",
            "stream_hash": hashlib.sha256(child.generate_state(4).tobytes()).hexdigest(),
        }
        for slot, child in zip(slots, children, strict=True)
    ]
    assert len(validate_seed_ledger(
        rows, root_seed=root_seed, bit_generator="PCG64DXSM", expected_slots=slots
    )) == 2
    tampered = [dict(row) for row in rows]
    tampered[0]["stream_hash"] = "0" * 64
    with pytest.raises(OracleLabError, match="replay mismatch"):
        validate_seed_ledger(
            tampered, root_seed=root_seed, bit_generator="PCG64DXSM", expected_slots=slots
        )
    bool_aliased = [dict(row) for row in rows]
    bool_aliased[1]["replicate"] = True
    bool_aliased[1]["spawn_key"] = [True]
    with pytest.raises(OracleLabError, match="exact-type mismatch"):
        validate_seed_ledger(
            bool_aliased,
            root_seed=root_seed,
            bit_generator="PCG64DXSM",
            expected_slots=slots,
        )


def test_broken_shell_reference_cannot_false_green(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        oracle_references,
        "constrained_shell_weights",
        lambda directions, shells, variances: np.zeros((3, len(directions))),
    )
    outcomes, _ = oracle_references.run_non_k6_reference_cases(
        root_seed=202607123, replicates=4, ppc_draws=256
    )
    shell = next(row for row in outcomes if row.mutation_id == "shell_monopole_leak")
    assert shell.clean_passed is False
    assert shell.status == "BLOCKED_PROPERTY_FAILURE"
    assert next(p for p in shell.properties if p.property_id == "uniform_flow").passed is False


def test_checked_in_lineage_is_complete_and_internally_downclaimed() -> None:
    payload = json.loads(LINEAGE.read_text(encoding="utf-8"))
    assert payload["all_rows_valid"] is True
    assert payload["automated_scan_failures"] == []
    assert len(payload["lineage_rows"]) == len(FROZEN_MUTATION_IDS) == 9
    for row in payload["lineage_rows"]:
        assert all(row["automated_scan_checks"].values())
        assert row["reference_metrics"]["sloc"] <= row["complexity_budget"]["max_sloc"]
        assert row["evaluator_metrics"]["sloc"] <= row["complexity_budget"]["max_evaluator_sloc"]
        assert row["manual_algorithm_adjudication"]["decision"] == "distinct_with_disclosed_correlation"
        assert "process_correlation" in row["independence_class"]
        assert row["shared_lineage_disclosures"]
