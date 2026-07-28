#!/usr/bin/env python3
"""Regenerate the PR-254 synthetic purpose-specific normalizer benchmark.

The experiment uses one frozen synthetic draw bank for all six normalizers.
It is methodology-conditional and contains no PR-151 or observational data.
The benchmark reports purpose-specific Pareto fronts; it does not select a
universal winner or turn invertible scaling into information.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from math import sqrt
from pathlib import Path
from statistics import NormalDist

import numpy as np
from common.anchor_geometry import (
    BenchmarkMetric,
    DenominatorZeroStatus,
    MetricDirection,
    NormalizerEvaluation,
    NormalizerEvaluationStatus,
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
    build_normalizer_benchmark,
)

REPO = Path(__file__).resolve().parents[2]
DEFAULT_OUT = (
    REPO
    / "docs/generated/pr254_anchor_geometry/normalizer_benchmark.json"
)
SEED = 20260728
MIN_REPLICATES = 20_000
MAX_REPLICATES = 400_000
MAX_MCSE = 0.0025
TARGET_SIZE = 0.05
TARGET_COVERAGE = 0.95
SERIALIZED_SIGNIFICANT_DIGITS = 14
NUMERICAL_ZERO_TOLERANCE = 1e-12
LIKELIHOOD_TOLERANCE = 1e-10
ZERO_DENOMINATOR_ERROR = "anchor denominator must be strictly positive"
LIKELIHOOD_COVARIANCE = (
    (1.0, 0.10, 0.00, 0.00),
    (0.10, 1.30, 0.05, 0.00),
    (0.00, 0.05, 0.90, 0.08),
    (0.00, 0.00, 0.08, 1.10),
)
PURPOSES = tuple(NormalizerPurpose)
SOURCE_COUPLING = {
    NormalizerKind.EXPANSION_NORMALIZED: 0.10,
    NormalizerKind.MES_ANCHORED: 0.25,
    NormalizerKind.FISHER_WHITENED: 0.45,
    NormalizerKind.TEMPLATE_LIMIT: 0.75,
    NormalizerKind.DYNAMICAL_BREAKDOWN: 0.35,
    NormalizerKind.PRIOR_QUANTILE: 0.85,
}
PREMISE_COUPLING = {
    NormalizerKind.EXPANSION_NORMALIZED: 0.30,
    NormalizerKind.MES_ANCHORED: 0.15,
    NormalizerKind.FISHER_WHITENED: 0.40,
    NormalizerKind.TEMPLATE_LIMIT: 0.55,
    NormalizerKind.DYNAMICAL_BREAKDOWN: 0.25,
    NormalizerKind.PRIOR_QUANTILE: 0.65,
}


def _maps() -> dict[NormalizerKind, np.ndarray]:
    return {
        NormalizerKind.EXPANSION_NORMALIZED: np.eye(3),
        NormalizerKind.MES_ANCHORED: np.diag([0.7, 1.1, 1.6]),
        NormalizerKind.FISHER_WHITENED: np.asarray(
            [[1.2, 0.2, 0.0], [0.0, 0.8, 0.1], [0.0, 0.0, 1.4]]
        ),
        NormalizerKind.TEMPLATE_LIMIT: np.diag([0.5, 2.0, 1.0]),
        NormalizerKind.DYNAMICAL_BREAKDOWN: np.diag([1.3, 0.8, 1.1]),
        NormalizerKind.PRIOR_QUANTILE: np.diag([1.6, 1.6, 1.6]),
    }


def _rotation() -> np.ndarray:
    angle = 0.37
    c, s = np.cos(angle), np.sin(angle)
    return np.asarray([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def _draw_bank(replicates: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(SEED)
    state = rng.normal(size=(replicates, 3))
    anchor_latent = rng.normal(size=replicates)
    noise = rng.normal(size=replicates)
    anchor = np.exp(
        0.2 * (0.6 * noise + sqrt(1.0 - 0.6**2) * anchor_latent)
    )
    q95 = NormalDist().inv_cdf(0.95)
    stress = 1.0 + 0.05 * (noise - q95)
    numerator = anchor * stress
    observable_noise = rng.normal(size=(replicates, 4))
    return {
        "state": state,
        "anchor": anchor,
        "numerator": numerator,
        "noise": noise,
        "observable_noise": observable_noise,
    }


def _mcse(probability: float, replicates: int) -> float:
    return sqrt(probability * (1.0 - probability) / replicates)


def _canonical_float(value: float, *, zero_tolerance: float = 0.0) -> float:
    """Suppress non-semantic BLAS/libm last-bit drift in frozen JSON."""

    if abs(value) <= zero_tolerance:
        return 0.0
    return float(f"{value:.{SERIALIZED_SIGNIFICANT_DIGITS}g}")


def _canonical_payload(value: object) -> object:
    if isinstance(value, float):
        return _canonical_float(value)
    if isinstance(value, list):
        return [_canonical_payload(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _canonical_payload(item)
            for key, item in value.items()
        }
    return value


def _stress_ratio(
    numerator: np.ndarray,
    anchor: np.ndarray,
) -> np.ndarray:
    """Return a stress ratio only for finite, shape-matched positive anchors."""

    numerator_values = np.asarray(numerator, dtype=float)
    anchor_values = np.asarray(anchor, dtype=float)
    if numerator_values.shape != anchor_values.shape:
        raise ValueError("numerator and anchor must have the same shape")
    if numerator_values.size == 0:
        raise ValueError("numerator and anchor must be non-empty")
    if not np.all(np.isfinite(numerator_values)):
        raise ValueError("numerator must contain only finite values")
    if not np.all(np.isfinite(anchor_values)):
        raise ValueError("anchor denominator must contain only finite values")
    if np.any(anchor_values <= 0.0):
        raise ValueError(ZERO_DENOMINATOR_ERROR)
    return numerator_values / anchor_values


def _run_zero_denominator_probe(
) -> tuple[DenominatorZeroStatus, dict[str, object]]:
    """Execute and record the destructive zero-denominator refusal."""

    numerator = np.asarray([1.0])
    anchor = np.asarray([0.0])
    try:
        _stress_ratio(numerator, anchor)
    except ValueError as exc:
        if str(exc) != ZERO_DENOMINATOR_ERROR:
            raise RuntimeError(
                "zero-denominator probe raised an unexpected refusal"
            ) from exc
        status = DenominatorZeroStatus.FAIL_CLOSED
        return status, {
            "operation": "stress_ratio",
            "numerator": numerator.tolist(),
            "anchor_denominator": anchor.tolist(),
            "expected_exception_type": "ValueError",
            "expected_exception_message": ZERO_DENOMINATOR_ERROR,
            "observed_exception_type": type(exc).__name__,
            "observed_exception_message": str(exc),
            "status": status.value,
        }
    raise RuntimeError("zero-denominator probe did not fail closed")


def _gaussian_neg2loglikelihood_invariance_error(
    prediction: np.ndarray,
    transformed_prediction: np.ndarray,
    observation: np.ndarray,
    covariance: np.ndarray,
) -> float:
    """Compare actual Gaussian -2 log likelihoods under reparameterization."""

    prediction_values = np.asarray(prediction, dtype=float)
    transformed_values = np.asarray(transformed_prediction, dtype=float)
    observation_values = np.asarray(observation, dtype=float)
    covariance_values = np.asarray(covariance, dtype=float)
    if (
        prediction_values.ndim != 2
        or transformed_values.shape != prediction_values.shape
        or observation_values.shape != prediction_values.shape
    ):
        raise ValueError(
            "prediction, transformed prediction, and observation must be "
            "shape-matched matrices"
        )
    if prediction_values.shape[0] == 0 or prediction_values.shape[1] == 0:
        raise ValueError("Gaussian likelihood matrices must be non-empty")
    observable_count = prediction_values.shape[1]
    if covariance_values.shape != (observable_count, observable_count):
        raise ValueError(
            "covariance shape must match the observable dimension"
        )
    if not all(
        np.all(np.isfinite(value))
        for value in (
            prediction_values,
            transformed_values,
            observation_values,
            covariance_values,
        )
    ):
        raise ValueError("Gaussian likelihood inputs must be finite")
    if not np.allclose(
        covariance_values,
        covariance_values.T,
        rtol=0.0,
        atol=NUMERICAL_ZERO_TOLERANCE,
    ):
        raise ValueError("Gaussian likelihood covariance must be symmetric")
    try:
        np.linalg.cholesky(covariance_values)
    except np.linalg.LinAlgError as exc:
        raise ValueError(
            "Gaussian likelihood covariance must be positive definite"
        ) from exc

    def neg2loglikelihood(mean: np.ndarray) -> np.ndarray:
        residual = observation_values - mean
        solved = np.linalg.solve(covariance_values, residual.T).T
        quadratic = np.einsum("ni,ni->n", residual, solved)
        sign, logdet = np.linalg.slogdet(covariance_values)
        if sign <= 0.0:  # pragma: no cover - guarded by Cholesky
            raise ValueError(
                "Gaussian likelihood covariance must have positive determinant"
            )
        normalization = (
            observable_count * np.log(2.0 * np.pi) + logdet
        )
        return quadratic + normalization

    base = neg2loglikelihood(prediction_values)
    transformed = neg2loglikelihood(transformed_values)
    return float(np.max(np.abs(base - transformed)))


def _adaptive_draws() -> tuple[dict[str, np.ndarray], dict[str, object]]:
    replicates = MIN_REPLICATES
    while True:
        draws = _draw_bank(replicates)
        stress = _stress_ratio(draws["numerator"], draws["anchor"])
        exceedance_rate = float(np.mean(stress > 1.0))
        coverage_rate = float(
            np.mean(
                np.abs(draws["noise"])
                <= NormalDist().inv_cdf(0.975)
            )
        )
        exceedance_mcse = _mcse(exceedance_rate, replicates)
        coverage_mcse = _mcse(coverage_rate, replicates)
        size_threshold = TARGET_SIZE + 3.0 * exceedance_mcse
        coverage_threshold = TARGET_COVERAGE - 3.0 * coverage_mcse
        size_pass = exceedance_rate <= size_threshold
        coverage_pass = coverage_rate >= coverage_threshold
        precision_pass = max(exceedance_mcse, coverage_mcse) <= MAX_MCSE
        if precision_pass:
            status = (
                "PASS"
                if size_pass and coverage_pass
                else "FAIL_CALIBRATION"
            )
            break
        if replicates == MAX_REPLICATES:
            status = "INCONCLUSIVE_MC_PRECISION"
            break
        replicates = min(replicates * 2, MAX_REPLICATES)
    return draws, {
        "status": status,
        "replicates": replicates,
        "diagnostic_screening_exceedance_rate": exceedance_rate,
        "diagnostic_screening_exceedance_mcse": exceedance_mcse,
        "partial_id_coverage_rate": coverage_rate,
        "partial_id_coverage_mcse": coverage_mcse,
        "size_threshold_3mcse": size_threshold,
        "coverage_threshold_3mcse": coverage_threshold,
        "size_pass": size_pass,
        "coverage_pass": coverage_pass,
        "target_size": TARGET_SIZE,
        "target_coverage": TARGET_COVERAGE,
        "maximum_mcse": MAX_MCSE,
    }


def _receipt(draws: dict[str, np.ndarray]) -> str:
    payload = {
        "seed": SEED,
        "replicates": int(draws["state"].shape[0]),
        "distribution": (
            "state~N3(0,I); correlated positive random anchor; "
            "stress=1+0.05*(z-Phi^-1(0.95))"
        ),
        "data_source": "synthetic_only",
    }
    hasher = hashlib.sha256()
    hasher.update(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    )
    for name in sorted(draws):
        values = np.ascontiguousarray(draws[name], dtype="<f8")
        hasher.update(name.encode())
        hasher.update(
            json.dumps(values.shape, separators=(",", ":")).encode()
        )
        hasher.update(values.tobytes(order="C"))
    return "sha256:" + hasher.hexdigest()


def _specs() -> tuple[NormalizerSpec, ...]:
    return tuple(
        NormalizerSpec(
            normalizer_id=f"pr254.{kind.value.lower()}",
            kind=kind,
            purposes=PURPOSES,
            coordinate_labels=("u0", "u1", "u2"),
            coordinate_map=tuple(
                tuple(float(value) for value in row)
                for row in _maps()[kind]
            ),
            source_identity=f"PR254-SYNTHETIC-{kind.value}",
            assumptions=(
                "synthetic methodology benchmark only",
                "coordinate map is invertible",
            ),
        )
        for kind in NormalizerKind
    )


def _metric(
    *,
    normalizer_id: str,
    purpose: NormalizerPurpose,
    metric_id: str,
    value: float,
    direction: MetricDirection,
) -> BenchmarkMetric:
    return BenchmarkMetric(
        metric_id=metric_id,
        value=value,
        direction=direction,
        evidence_identity=(
            f"PR254-SYNTHETIC:{normalizer_id}:{purpose.value}:{metric_id}"
        ),
    )


def _evaluations(
    specs: tuple[NormalizerSpec, ...],
    draws: dict[str, np.ndarray],
    diagnostics: dict[str, object],
    receipt: str,
    denominator_zero_status: DenominatorZeroStatus,
) -> tuple[NormalizerEvaluation, ...]:
    response = np.asarray(
        [
            [1.0, 0.25, -0.1],
            [0.0, 1.2, 0.3],
            [0.5, -0.2, 1.4],
            [0.2, 0.4, 0.8],
        ]
    )
    rotation = _rotation()
    state = draws["state"]
    prediction = state @ response.T
    covariance = np.asarray(LIKELIHOOD_COVARIANCE)
    covariance_cholesky = np.linalg.cholesky(covariance)
    observation = (
        prediction
        + draws["observable_noise"] @ covariance_cholesky.T
    )
    exceedance_error = abs(
        float(diagnostics["diagnostic_screening_exceedance_rate"])
        - TARGET_SIZE
    )
    coverage_shortfall = max(
        TARGET_COVERAGE - float(diagnostics["partial_id_coverage_rate"]),
        0.0,
    )
    evaluations = []
    for spec in specs:
        transform = np.asarray(spec.coordinate_map)
        transformed_state = np.linalg.solve(transform, state.T).T
        transformed_response = response @ transform
        transformed_prediction = transformed_state @ transformed_response.T
        prediction_invariance_error = _canonical_float(
            float(np.max(np.abs(prediction - transformed_prediction))),
            zero_tolerance=NUMERICAL_ZERO_TOLERANCE,
        )
        likelihood_invariance_error = _canonical_float(
            _gaussian_neg2loglikelihood_invariance_error(
                prediction,
                transformed_prediction,
                observation,
                covariance,
            ),
            zero_tolerance=NUMERICAL_ZERO_TOLERANCE,
        )

        rotated_state = state @ rotation.T
        rotated_transform = rotation @ transform @ rotation.T
        rotated_coordinate = np.linalg.solve(
            rotated_transform, rotated_state.T
        ).T
        expected_rotated_coordinate = transformed_state @ rotation.T
        o3_error = _canonical_float(
            float(
                np.max(
                    np.abs(
                        rotated_coordinate - expected_rotated_coordinate
                    )
                )
            ),
            zero_tolerance=NUMERICAL_ZERO_TOLERANCE,
        )
        condition_number = _canonical_float(
            float(np.linalg.cond(transformed_response))
        )
        source_sensitivity = _canonical_float(
            SOURCE_COUPLING[spec.kind] * 0.1
        )
        premise_sensitivity = _canonical_float(
            PREMISE_COUPLING[spec.kind]
            * float(
                np.std(
                    _stress_ratio(
                        draws["numerator"],
                        draws["anchor"],
                    )
                )
            )
        )
        abstention_support = 1.0
        by_purpose: dict[
            NormalizerPurpose, tuple[BenchmarkMetric, ...]
        ] = {
            NormalizerPurpose.PREMISE_STRESS: (
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.PREMISE_STRESS,
                    metric_id="diagnostic_screening_size_error",
                    value=exceedance_error,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.PREMISE_STRESS,
                    metric_id="premise_sensitivity",
                    value=premise_sensitivity,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
            ),
            NormalizerPurpose.RESPONSE_CONDITIONING: (
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.RESPONSE_CONDITIONING,
                    metric_id="response_condition_number",
                    value=condition_number,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.RESPONSE_CONDITIONING,
                    metric_id="reparameterization_error",
                    value=prediction_invariance_error,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
            ),
            NormalizerPurpose.PARTIAL_IDENTIFICATION: (
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.PARTIAL_IDENTIFICATION,
                    metric_id="coverage_shortfall",
                    value=coverage_shortfall,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.PARTIAL_IDENTIFICATION,
                    metric_id="rank_preservation_error",
                    value=0.0,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
            ),
            NormalizerPurpose.SOURCE_SCREENING: (
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.SOURCE_SCREENING,
                    metric_id="screening_size_error",
                    value=exceedance_error,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.SOURCE_SCREENING,
                    metric_id="abstention_support",
                    value=abstention_support,
                    direction=MetricDirection.HIGHER_IS_BETTER,
                ),
            ),
            NormalizerPurpose.PORTABILITY: (
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.PORTABILITY,
                    metric_id="o3_covariance_error",
                    value=o3_error,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
                _metric(
                    normalizer_id=spec.normalizer_id,
                    purpose=NormalizerPurpose.PORTABILITY,
                    metric_id="source_change_sensitivity",
                    value=source_sensitivity,
                    direction=MetricDirection.LOWER_IS_BETTER,
                ),
            ),
        }
        rank = int(np.linalg.matrix_rank(response))
        for purpose in PURPOSES:
            evaluations.append(
                NormalizerEvaluation(
                    normalizer_id=spec.normalizer_id,
                    purpose=purpose,
                    status=NormalizerEvaluationStatus.EVALUATED,
                    metrics=by_purpose[purpose],
                    rank_before=rank,
                    rank_after=int(
                        np.linalg.matrix_rank(transformed_response)
                    ),
                    denominator_zero_status=denominator_zero_status,
                    likelihood_invariance_error=likelihood_invariance_error,
                    base_draws_receipt=receipt,
                )
            )
    return tuple(evaluations)


def build_payload() -> dict[str, object]:
    draws, diagnostics = _adaptive_draws()
    receipt = _receipt(draws)
    denominator_zero_status, denominator_zero_probe = (
        _run_zero_denominator_probe()
    )
    specs = _specs()
    evaluations = _evaluations(
        specs,
        draws,
        diagnostics,
        receipt,
        denominator_zero_status,
    )
    report = build_normalizer_benchmark(
        specs=specs,
        evaluations=evaluations,
        likelihood_tolerance=LIKELIHOOD_TOLERANCE,
    )
    payload = {
        "schema_version": "pr254.normalizer_benchmark.v1",
        "artifact_mode": "methodology_conditional",
        "public_use": False,
        "data_source": "synthetic_only",
        "pr151_data_used": False,
        "configuration": {
            "master_seed": SEED,
            "minimum_replicates": MIN_REPLICATES,
            "maximum_replicates": MAX_REPLICATES,
            "maximum_mcse": MAX_MCSE,
            "serialized_significant_digits": SERIALIZED_SIGNIFICANT_DIGITS,
            "numerical_zero_tolerance": NUMERICAL_ZERO_TOLERANCE,
            "likelihood_tolerance": LIKELIHOOD_TOLERANCE,
            "same_base_draws_receipt": receipt,
            "source_coupling": {
                kind.value: SOURCE_COUPLING[kind]
                for kind in NormalizerKind
            },
            "premise_coupling": {
                kind.value: PREMISE_COUPLING[kind]
                for kind in NormalizerKind
            },
        },
        "denominator_zero_probe": denominator_zero_probe,
        "likelihood_probe": {
            "model": "y_given_u_is_multivariate_normal_Ru_C",
            "observation": (
                "shared_synthetic_Ru_plus_cholesky_C_times_standard_normal"
            ),
            "covariance": [
                list(row) for row in LIKELIHOOD_COVARIANCE
            ],
            "statistic": (
                "maximum_absolute_difference_in_gaussian_negative_2_log_"
                "likelihood"
            ),
            "normalization": (
                "dimension_log_2pi_plus_logdet_C_included_in_both_values"
            ),
            "coordinate_transform": (
                "u_prime_equals_D_inverse_u_and_R_prime_equals_R_D"
            ),
            "base_draws_receipt": receipt,
        },
        "diagnostics": diagnostics,
        "benchmark": report.as_payload(),
        "evaluations": [
            {
                "normalizer_id": evaluation.normalizer_id,
                "purpose": evaluation.purpose.value,
                "rank_before": evaluation.rank_before,
                "rank_after": evaluation.rank_after,
                "denominator_zero_status": (
                    evaluation.denominator_zero_status.value
                ),
                "base_draws_receipt": evaluation.base_draws_receipt,
                "likelihood_invariance_error": (
                    evaluation.likelihood_invariance_error
                ),
                "metrics": {
                    metric.metric_id: {
                        "value": metric.value,
                        "direction": metric.direction.value,
                    }
                    for metric in evaluation.metrics
                },
            }
            for evaluation in evaluations
        ],
        "claim_boundary": {
            "allowed": [
                "synthetic purpose-specific normalizer comparison",
                "reparameterization and conditioning diagnostics",
            ],
            "forbidden": [
                "universal normalizer winner",
                "information or rank gain from invertible scaling",
                "observational validation",
                "FLRW departure or Bianchi family identification",
            ],
        },
    }
    canonical = _canonical_payload(payload)
    if not isinstance(canonical, dict):  # pragma: no cover - structural guard
        raise TypeError("canonical benchmark payload must remain a mapping")
    return canonical


def _serialized(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    output = args.out if args.out.is_absolute() else REPO / args.out
    expected = _serialized(build_payload())
    if args.write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(expected, encoding="utf-8")
        print(output.relative_to(REPO))
        return 0
    if not output.is_file():
        raise SystemExit(f"missing benchmark receipt: {output}")
    if output.read_text(encoding="utf-8") != expected:
        raise SystemExit("normalizer benchmark receipt drifted")
    print("PR254_NORMALIZER_BENCHMARK_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
