#!/usr/bin/env python3
"""Deterministic numerical validation for the EGS3 rank-two endpoint path.

This command performs four diagnostic-only checks without writing artifacts:

* an independent geometric oracle for linear extrema over a two-dimensional
  ellipsoid intersected with an axis-aligned box;
* a metamorphic sweep under independent positive column reparameterisations;
* a large-origin translation sweep with represented box corners as its oracle;
  and
* an arbitrary-response translation sweep recentered exactly from the encoded
  floats before applying the independent geometric oracle.

The oracle uses an eigendecomposition and ellipse angles.  It deliberately
does not share the production endpoint implementation.  These checks validate
numerical mechanics only; they do not validate a physical model, observational
claim, native solver, novelty claim, or publication result.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

import numpy as np
from scipy import stats


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from htt.obsstat.egs3_identified_set import (  # noqa: E402
    STATUS_FEASIBLE,
    identified_set_report,
)


SCHEMA = "htt.egs3.endpoint_integrity_validation.v1"
ORACLE_CASES = 300
ORACLE_SEED = 20260722
REPARAMETERIZATION_CASES = 500
REPARAMETERIZATION_SEED = 20260723
TRANSLATION_CASES = 200
TRANSLATION_SEED = 20260724
TRANSLATED_GEOMETRY_CASES = 200
TRANSLATED_GEOMETRY_SEED = 20260725
ORACLE_TOLERANCE = 2.0e-10
REPARAMETERIZATION_TOLERANCE = 2.0e-10
TRANSLATION_TOLERANCE = 2.0e-10
TRANSLATED_GEOMETRY_TOLERANCE = 2.0e-6
MAX_RECORDED_FAILURES = 8

MODULE_PATH = REPO_ROOT / "htt/obsstat/egs3_identified_set.py"
SCRIPT_PATH = Path(__file__).resolve()


@dataclass(frozen=True)
class EndpointCase:
    """A finite, full-rank two-component endpoint problem."""

    response: np.ndarray
    observed: np.ndarray
    comparator: np.ndarray
    lower: np.ndarray
    upper: np.ndarray
    alpha2: float
    case_id: str


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _rng(seed: int) -> np.random.Generator:
    """Pin the bit generator so the case corpus is version-explicit."""
    return np.random.Generator(np.random.PCG64(int(seed)))


def _positive_radius_case(
    rng: np.random.Generator,
    *,
    case_id: str,
) -> EndpointCase:
    while True:
        m = int(rng.integers(3, 9))
        response = rng.normal(size=(m, 2))
        if float(np.linalg.cond(response)) < 20.0:
            break

    truth = rng.uniform(-1.0, 1.0, size=2)
    comparator = rng.normal(size=2)
    if float(np.linalg.norm(comparator)) < 0.2:
        comparator[0] += 1.0

    alpha2 = float(rng.uniform(0.7, 0.999))
    tau2 = float(stats.chi2.ppf(1.0 - alpha2, 2))
    gram_inverse = np.linalg.inv(response.T @ response)
    coordinate_spans = np.sqrt(
        np.maximum(0.0, tau2 * np.diag(gram_inverse))
    )
    factors = rng.uniform(0.05, 1.5, size=(2, 2))
    lower = truth - coordinate_spans * factors[:, 0] - 1.0e-3
    upper = truth + coordinate_spans * factors[:, 1] + 1.0e-3
    return EndpointCase(
        response=response,
        observed=response @ truth,
        comparator=comparator,
        lower=lower,
        upper=upper,
        alpha2=alpha2,
        case_id=case_id,
    )


def _population_case(
    rng: np.random.Generator,
    *,
    case_id: str,
) -> EndpointCase:
    while True:
        m = int(rng.integers(3, 9))
        response = rng.normal(size=(m, 2))
        if float(np.linalg.cond(response)) < 20.0:
            break

    truth = rng.uniform(-1.0, 1.0, size=2)
    comparator = rng.normal(size=2)
    if float(np.linalg.norm(comparator)) < 0.2:
        comparator[0] += 1.0
    factors = rng.uniform(0.05, 1.5, size=(2, 2))
    lower = truth - factors[:, 0] - 1.0e-3
    upper = truth + factors[:, 1] + 1.0e-3
    return EndpointCase(
        response=response,
        observed=response @ truth,
        comparator=comparator,
        lower=lower,
        upper=upper,
        alpha2=1.0,
        case_id=case_id,
    )


def _rank_two_regression_case() -> EndpointCase:
    response = np.array(
        [
            [-2.096448201956982, 0.6797168074778418],
            [-0.0061956409920737, 0.49144967908892995],
            [-0.7442459285597672, -0.2698996510417867],
            [0.467697641812884, 0.04126766552408576],
            [1.73079173903801, 0.4882029838598173],
        ],
        dtype=float,
    )
    truth = np.array([0.0064878758068284, -1.2558494528493926])
    return EndpointCase(
        response=response,
        observed=response @ truth,
        comparator=np.array([-0.7601256832753791, -0.28079962967403027]),
        lower=np.array([-0.02110834962419701, -1.303923960594401]),
        upper=np.array([0.11769164191755827, -1.22158450893779]),
        alpha2=0.9517027729528782,
        case_id="rank_two_face_regression",
    )


def _bound_scale_regression_case() -> tuple[EndpointCase, np.ndarray]:
    response = np.array(
        [
            [0.8798084941547671, 0.041842441409790085],
            [-0.05724763553143051, -1.0812645699206391],
            [-1.118541004266105, 0.45177410139994284],
        ],
        dtype=float,
    )
    truth = np.array([-0.6584074484182041, -0.981319192706561])
    case = EndpointCase(
        response=response,
        observed=response @ truth,
        comparator=np.array([1.0931103541154148, -0.5751086946412933]),
        lower=np.array([-1.0848741170595766, -1.0243292442329566]),
        upper=np.array([0.029915924518696735, -0.4300734428128443]),
        alpha2=0.7585303518326602,
        case_id="physical_bound_slack_regression",
    )
    scales = np.array([579675638156.3582, 9.412188543901518])
    return case, scales


def _independent_level(case: EndpointCase) -> tuple[np.ndarray, float]:
    centre, *_ = np.linalg.lstsq(
        case.response, case.observed, rcond=None
    )
    residual = case.response @ centre - case.observed
    residual_squared = float(residual @ residual)
    tau2 = (
        0.0
        if case.alpha2 == 1.0
        else float(stats.chi2.ppf(1.0 - case.alpha2, 2))
    )
    return centre, residual_squared + tau2


def rank_two_geometric_oracle(
    case: EndpointCase,
) -> tuple[float, float, bool]:
    """Find extrema via ellipse angles and box intersections.

    The production endpoint route is not used.  In original coordinates the
    boundary is parameterised as ``centre + B @ (cos(theta), sin(theta))``.
    Candidate angles comprise the two unconstrained support directions and all
    ellipse intersections with the four box lines.  Feasible box corners cover
    the complementary case in which the ellipse contains a box extremum.
    """
    response = case.response
    centre, level = _independent_level(case)
    centre_residual = response @ centre - case.observed
    radius_squared = float(level - centre_residual @ centre_residual)
    arithmetic_scale = max(
        1.0,
        abs(level),
        float(np.linalg.norm(response, ord=2)) ** 2
        * max(1.0, float(np.linalg.norm(centre)) ** 2),
    )
    numeric_slack = 512.0 * np.finfo(float).eps * arithmetic_scale
    if radius_squared < -numeric_slack:
        raise ValueError("independent oracle received an empty ellipsoid")
    radius_squared = max(radius_squared, 0.0)

    candidates: list[np.ndarray] = []
    unconstrained_candidates: list[np.ndarray] = []
    if radius_squared == 0.0:
        candidates.append(centre)
        unconstrained_candidates.append(centre)
    else:
        gram = response.T @ response
        eigenvalues, eigenvectors = np.linalg.eigh(gram)
        if np.any(eigenvalues <= 0.0):
            raise ValueError(
                "independent oracle requires a positive-definite Gram matrix"
            )
        ellipse_map = eigenvectors @ np.diag(
            np.sqrt(radius_squared / eigenvalues)
        )

        objective_direction = ellipse_map.T @ case.comparator
        objective_angle = math.atan2(
            float(objective_direction[1]),
            float(objective_direction[0]),
        )
        for angle in (objective_angle, objective_angle + math.pi):
            unit = np.array([math.cos(angle), math.sin(angle)])
            candidate = centre + ellipse_map @ unit
            candidates.append(candidate)
            unconstrained_candidates.append(candidate)

        angle_slack = 256.0 * np.finfo(float).eps
        for coordinate in (0, 1):
            row = ellipse_map[coordinate]
            row_norm = float(np.linalg.norm(row))
            row_angle = math.atan2(float(row[1]), float(row[0]))
            for bound in (
                case.lower[coordinate],
                case.upper[coordinate],
            ):
                ratio = float((bound - centre[coordinate]) / row_norm)
                if ratio < -1.0 - angle_slack or ratio > 1.0 + angle_slack:
                    continue
                offset = math.acos(float(np.clip(ratio, -1.0, 1.0)))
                for angle in (row_angle - offset, row_angle + offset):
                    unit = np.array([math.cos(angle), math.sin(angle)])
                    candidates.append(centre + ellipse_map @ unit)

        for first in (case.lower[0], case.upper[0]):
            for second in (case.lower[1], case.upper[1]):
                candidates.append(np.array([first, second]))

    coordinate_scale = max(
        1.0,
        float(np.max(np.abs(case.lower))),
        float(np.max(np.abs(case.upper))),
        max(float(np.max(np.abs(candidate))) for candidate in candidates),
    )
    bound_slack = 512.0 * np.finfo(float).eps * coordinate_scale
    values: list[float] = []
    for candidate in candidates:
        if (
            np.any(candidate < case.lower - bound_slack)
            or np.any(candidate > case.upper + bound_slack)
        ):
            continue
        residual = response @ candidate - case.observed
        residual_squared = float(residual @ residual)
        residual_scale = max(1.0, abs(level), abs(residual_squared))
        residual_slack = 1024.0 * np.finfo(float).eps * residual_scale
        if residual_squared <= level + residual_slack:
            values.append(float(case.comparator @ candidate))
    if not values:
        raise ValueError("independent oracle found no feasible extremum candidate")

    box_active = any(
        np.any(candidate < case.lower - bound_slack)
        or np.any(candidate > case.upper + bound_slack)
        for candidate in unconstrained_candidates
    )
    return min(values), max(values), box_active


def _record_failure(
    failures: list[dict[str, Any]],
    failure: dict[str, Any],
) -> None:
    if len(failures) < MAX_RECORDED_FAILURES:
        failures.append(failure)


def run_rank_two_oracle(
    *,
    cases: int = ORACLE_CASES,
    seed: int = ORACLE_SEED,
) -> dict[str, Any]:
    if cases <= 0:
        raise ValueError("oracle cases must be positive")
    rng = _rng(seed)
    corpus = [_rank_two_regression_case()]
    corpus.extend(
        _positive_radius_case(rng, case_id=f"oracle_random_{index:03d}")
        for index in range(1, cases)
    )

    failures: list[dict[str, Any]] = []
    max_error = 0.0
    box_active_cases = 0
    for index, case in enumerate(corpus):
        try:
            report = identified_set_report(
                case.observed,
                case.response,
                case.comparator,
                case.lower,
                case.upper,
                alpha2=case.alpha2,
            )
            oracle_lo, oracle_hi, box_active = rank_two_geometric_oracle(case)
            box_active_cases += int(box_active)
            error = max(
                abs(report.reachable_lo - oracle_lo),
                abs(report.reachable_hi - oracle_hi),
            )
            max_error = max(max_error, float(error))
            if (
                report.status != STATUS_FEASIBLE
                or report.rank != 2
                or not math.isfinite(error)
                or error > ORACLE_TOLERANCE
            ):
                _record_failure(
                    failures,
                    {
                        "case": index,
                        "case_id": case.case_id,
                        "error": float(error),
                        "kind": "endpoint_mismatch",
                        "rank": int(report.rank),
                        "status": report.status,
                    },
                )
        except Exception as exc:  # fail closed with deterministic JSON evidence
            _record_failure(
                failures,
                {
                    "case": index,
                    "case_id": case.case_id,
                    "exception": type(exc).__name__,
                    "kind": "exception",
                    "message": str(exc),
                },
            )

    sufficient_box_activity = box_active_cases >= cases // 2
    if not sufficient_box_activity:
        _record_failure(
            failures,
            {
                "box_active_cases": box_active_cases,
                "kind": "insufficient_box_activity",
                "required": cases // 2,
            },
        )
    return {
        "box_active_cases": box_active_cases,
        "cases": cases,
        "failures": failures,
        "independent_method": "original_coordinate_eigen_angle_enumeration",
        "max_abs_endpoint_error": max_error,
        "passed": not failures,
        "seed": int(seed),
        "tolerance": ORACLE_TOLERANCE,
    }


def _reparameterized_case(
    case: EndpointCase,
    scales: np.ndarray,
) -> EndpointCase:
    return EndpointCase(
        response=case.response * scales,
        observed=case.observed.copy(),
        comparator=case.comparator * scales,
        lower=case.lower / scales,
        upper=case.upper / scales,
        alpha2=case.alpha2,
        case_id=case.case_id + "_reparameterized",
    )


def run_reparameterization_sweep(
    *,
    cases: int = REPARAMETERIZATION_CASES,
    seed: int = REPARAMETERIZATION_SEED,
) -> dict[str, Any]:
    if cases <= 0:
        raise ValueError("reparameterization cases must be positive")
    rng = _rng(seed)
    failures: list[dict[str, Any]] = []
    max_error = 0.0
    min_scale = math.inf
    max_scale = 0.0
    population_cases = 0
    positive_radius_cases = 0

    fixed_case, fixed_scales = _bound_scale_regression_case()
    for index in range(cases):
        if index == 0:
            case = fixed_case
            scales = fixed_scales
        else:
            population = index % 3 == 0
            if population:
                case = _population_case(
                    rng, case_id=f"reparameterization_{index:03d}"
                )
            else:
                case = _positive_radius_case(
                    rng, case_id=f"reparameterization_{index:03d}"
                )
            if index == 1:
                scales = np.array([1.0e-12, 1.0e12])
            elif index == 2:
                scales = np.array([1.0e12, 1.0e-12])
            else:
                scales = np.power(10.0, rng.uniform(-12.0, 12.0, size=2))

        population_cases += int(case.alpha2 == 1.0)
        positive_radius_cases += int(case.alpha2 != 1.0)
        min_scale = min(min_scale, float(np.min(scales)))
        max_scale = max(max_scale, float(np.max(scales)))
        transformed = _reparameterized_case(case, scales)
        try:
            baseline = identified_set_report(
                case.observed,
                case.response,
                case.comparator,
                case.lower,
                case.upper,
                alpha2=case.alpha2,
            )
            stressed = identified_set_report(
                transformed.observed,
                transformed.response,
                transformed.comparator,
                transformed.lower,
                transformed.upper,
                alpha2=transformed.alpha2,
            )
            error = max(
                abs(baseline.reachable_lo - stressed.reachable_lo),
                abs(baseline.reachable_hi - stressed.reachable_hi),
            )
            max_error = max(max_error, float(error))
            invariant_metadata = (
                baseline.status == stressed.status == STATUS_FEASIBLE
                and baseline.rank == stressed.rank == 2
                and baseline.df_reachable == stressed.df_reachable == 2
                and baseline.df_residual == stressed.df_residual
                and baseline.tau.r == stressed.tau.r
            )
            if (
                not invariant_metadata
                or not math.isfinite(error)
                or error > REPARAMETERIZATION_TOLERANCE
            ):
                _record_failure(
                    failures,
                    {
                        "case": index,
                        "case_id": case.case_id,
                        "error": float(error),
                        "kind": "reparameterization_mismatch",
                        "scales": [float(value) for value in scales],
                    },
                )
        except Exception as exc:  # fail closed with deterministic JSON evidence
            _record_failure(
                failures,
                {
                    "case": index,
                    "case_id": case.case_id,
                    "exception": type(exc).__name__,
                    "kind": "exception",
                    "message": str(exc),
                    "scales": [float(value) for value in scales],
                },
            )

    return {
        "cases": cases,
        "failures": failures,
        "max_abs_endpoint_difference": max_error,
        "max_column_scale": max_scale,
        "min_column_scale": min_scale,
        "passed": not failures,
        "population_cases": population_cases,
        "positive_radius_cases": positive_radius_cases,
        "seed": int(seed),
        "tolerance": REPARAMETERIZATION_TOLERANCE,
        "transformation": "A_j*s_j, g_j/s_j, c_j*s_j, bounds_j/s_j",
    }


def run_translation_sweep(
    *,
    cases: int = TRANSLATION_CASES,
    seed: int = TRANSLATION_SEED,
) -> dict[str, Any]:
    """Check origin invariance against an exact represented-corner oracle.

    Every generated box is strictly contained in the ellipsoid.  The sharp
    endpoints are therefore the two comparator-selected corners, computed
    directly from the represented bounds.  Residual margins are checked in
    local delta coordinates, independently of the production endpoint path.
    """
    if cases <= 0:
        raise ValueError("translation cases must be positive")
    rng = _rng(seed)
    response = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]])
    comparator = np.array([1.0, -1.0])
    alpha2 = 0.9
    tau2 = float(stats.chi2.ppf(1.0 - alpha2, 2))
    failures: list[dict[str, Any]] = []
    max_error = 0.0
    min_margin = math.inf
    min_magnitude = math.inf
    max_magnitude = 0.0

    for index in range(cases):
        if index == 0:
            translation = 1.0e8
            half_widths = np.array([0.1, 0.1])
        else:
            magnitude = float(10.0 ** rng.uniform(5.0, 9.0))
            translation = magnitude if rng.integers(0, 2) else -magnitude
            half_widths = rng.uniform(0.01, 0.15, size=2)
        centre = np.array([translation, translation])
        lower = centre - half_widths
        upper = centre + half_widths
        observed = response @ centre

        corner_residuals = []
        for first in (lower[0], upper[0]):
            for second in (lower[1], upper[1]):
                delta = np.array([first, second]) - centre
                residual = response @ delta
                corner_residuals.append(float(residual @ residual))
        margin = tau2 - max(corner_residuals)
        min_margin = min(min_margin, margin)
        magnitude = abs(translation)
        min_magnitude = min(min_magnitude, magnitude)
        max_magnitude = max(max_magnitude, magnitude)

        try:
            if margin <= 0.0:
                raise ValueError("translation corpus box is not strictly feasible")
            report = identified_set_report(
                observed,
                response,
                comparator,
                lower,
                upper,
                alpha2=alpha2,
            )
            expected_lo = float(lower[0] - upper[1])
            expected_hi = float(upper[0] - lower[1])
            error = max(
                abs(report.reachable_lo - expected_lo),
                abs(report.reachable_hi - expected_hi),
            )
            max_error = max(max_error, float(error))
            if (
                report.status != STATUS_FEASIBLE
                or report.rank != 2
                or not math.isfinite(error)
                or error > TRANSLATION_TOLERANCE
            ):
                _record_failure(
                    failures,
                    {
                        "case": index,
                        "error": float(error),
                        "kind": "translation_mismatch",
                        "translation": float(translation),
                    },
                )
        except Exception as exc:  # fail closed with deterministic JSON evidence
            _record_failure(
                failures,
                {
                    "case": index,
                    "exception": type(exc).__name__,
                    "kind": "exception",
                    "message": str(exc),
                    "translation": float(translation),
                },
            )

    return {
        "cases": cases,
        "failures": failures,
        "independent_method": "represented_box_corners_with_local_residuals",
        "max_abs_endpoint_error": max_error,
        "max_translation_magnitude": max_magnitude,
        "min_strict_feasibility_margin": min_margin,
        "min_translation_magnitude": min_magnitude,
        "passed": not failures,
        "seed": int(seed),
        "tolerance": TRANSLATION_TOLERANCE,
        "transformation": "g -> g + (t,t), y -> y + A@(t,t)",
    }


def _translated_support_regression() -> tuple[EndpointCase, np.ndarray]:
    """Return the arbitrary-response case that exposed absolute-centre loss."""
    case = EndpointCase(
        response=np.array([
            [0.1203131746035526, -0.5112050203640084],
            [-0.4053974550451821, -0.40150597869556093],
            [0.9030299412747598, 0.025656376123362527],
            [-0.8399725668667812, -1.3273615652740685],
            [-1.3068623229665421, 0.38352359763066873],
            [-1.2501010214077322, -0.2959033940717367],
        ]),
        observed=np.array([
            146338482.12332046,
            -421819897.35554087,
            968760131.05824077,
            -857374811.354383,
            -1416101651.1345346,
            -1332356880.2300694,
        ]),
        comparator=np.array([0.3476191044133548, 0.1329409460497445]),
        lower=np.array([1073741823.4535451, -33554433.588397063]),
        upper=np.array([1073741824.1514452, -33554432.864288345]),
        alpha2=0.7428981753119477,
        case_id="translated_box_inactive_support_regression",
    )
    return case, np.array([1073741824.0, -33554432.0])


def _translated_case(
    case: EndpointCase,
    translation: np.ndarray,
) -> EndpointCase:
    return EndpointCase(
        response=case.response.copy(),
        observed=case.observed + case.response @ translation,
        comparator=case.comparator.copy(),
        lower=case.lower + translation,
        upper=case.upper + translation,
        alpha2=case.alpha2,
        case_id=case.case_id + "_translated",
    )


def _exactly_recenter_encoded_case(
    case: EndpointCase,
    translation: np.ndarray,
) -> tuple[EndpointCase, Fraction]:
    """Recenter encoded floats using exact rational arithmetic."""
    translation_fractions = [
        Fraction.from_float(float(value)) for value in translation
    ]
    local_observed = []
    for row, observed in zip(case.response, case.observed):
        translated_prediction = sum(
            (
                Fraction.from_float(float(coefficient))
                * displacement
                for coefficient, displacement in zip(
                    row, translation_fractions
                )
            ),
            start=Fraction(0),
        )
        local_observed.append(float(
            Fraction.from_float(float(observed)) - translated_prediction
        ))
    local_lower = np.array([
        float(Fraction.from_float(float(bound)) - displacement)
        for bound, displacement in zip(case.lower, translation_fractions)
    ])
    local_upper = np.array([
        float(Fraction.from_float(float(bound)) - displacement)
        for bound, displacement in zip(case.upper, translation_fractions)
    ])
    objective_translation = sum(
        (
            Fraction.from_float(float(coefficient)) * displacement
            for coefficient, displacement in zip(
                case.comparator, translation_fractions
            )
        ),
        start=Fraction(0),
    )
    local_case = EndpointCase(
        response=case.response.copy(),
        observed=np.asarray(local_observed),
        comparator=case.comparator.copy(),
        lower=local_lower,
        upper=local_upper,
        alpha2=case.alpha2,
        case_id=case.case_id + "_exactly_recentered",
    )
    return local_case, objective_translation


def run_translated_geometry_sweep(
    *,
    cases: int = TRANSLATED_GEOMETRY_CASES,
    seed: int = TRANSLATED_GEOMETRY_SEED,
) -> dict[str, Any]:
    """Validate translated arbitrary-response ellipsoid/box endpoints."""
    if cases <= 0:
        raise ValueError("translated-geometry cases must be positive")
    rng = _rng(seed)
    failures: list[dict[str, Any]] = []
    max_error = 0.0
    max_error_arithmetic_ulps = 0.0
    box_active_cases = 0
    min_translation = math.inf
    max_translation = 0.0

    fixed_case, fixed_translation = _translated_support_regression()
    for index in range(cases):
        if index == 0:
            case = fixed_case
            translation = fixed_translation
        else:
            base = _positive_radius_case(
                rng, case_id=f"translated_geometry_{index:03d}"
            )
            exponents = rng.integers(17, 31, size=2)
            signs = np.where(rng.integers(0, 2, size=2) == 0, -1.0, 1.0)
            translation = signs * np.exp2(exponents.astype(float))
            case = _translated_case(base, translation)

        magnitude = float(np.max(np.abs(translation)))
        min_translation = min(min_translation, magnitude)
        max_translation = max(max_translation, magnitude)
        try:
            local_case, objective_translation = _exactly_recenter_encoded_case(
                case, translation
            )
            local_lo, local_hi, box_active = rank_two_geometric_oracle(
                local_case
            )
            box_active_cases += int(box_active)
            expected_lo = float(
                objective_translation + Fraction.from_float(local_lo)
            )
            expected_hi = float(
                objective_translation + Fraction.from_float(local_hi)
            )
            report = identified_set_report(
                case.observed,
                case.response,
                case.comparator,
                case.lower,
                case.upper,
                alpha2=case.alpha2,
            )
            error = max(
                abs(report.reachable_lo - expected_lo),
                abs(report.reachable_hi - expected_hi),
            )
            objective_arithmetic_scale = float(np.sum(
                np.abs(case.comparator)
                * np.maximum(np.abs(case.lower), np.abs(case.upper))
            ))
            arithmetic_ulp = math.ulp(objective_arithmetic_scale)
            max_error_arithmetic_ulps = max(
                max_error_arithmetic_ulps,
                float(error / arithmetic_ulp),
            )
            max_error = max(max_error, float(error))
            if (
                report.status != STATUS_FEASIBLE
                or report.rank != 2
                or not math.isfinite(error)
                or error > TRANSLATED_GEOMETRY_TOLERANCE
            ):
                _record_failure(
                    failures,
                    {
                        "case": index,
                        "case_id": case.case_id,
                        "error": float(error),
                        "kind": "translated_geometry_mismatch",
                        "tolerance": TRANSLATED_GEOMETRY_TOLERANCE,
                        "translation": [
                            float(value) for value in translation
                        ],
                    },
                )
        except Exception as exc:  # fail closed with deterministic JSON evidence
            _record_failure(
                failures,
                {
                    "case": index,
                    "case_id": case.case_id,
                    "exception": type(exc).__name__,
                    "kind": "exception",
                    "message": str(exc),
                    "translation": [float(value) for value in translation],
                },
            )

    return {
        "box_active_cases": box_active_cases,
        "cases": cases,
        "failures": failures,
        "independent_method": (
            "exact_Fraction_recenter_then_eigen_angle_geometry"
        ),
        "max_abs_endpoint_error": max_error,
        "max_error_objective_arithmetic_ulps": max_error_arithmetic_ulps,
        "max_translation_magnitude": max_translation,
        "min_translation_magnitude": min_translation,
        "passed": not failures,
        "seed": int(seed),
        "tolerance": TRANSLATED_GEOMETRY_TOLERANCE,
    }


def build_report() -> dict[str, Any]:
    oracle = run_rank_two_oracle()
    reparameterization = run_reparameterization_sweep()
    translation = run_translation_sweep()
    translated_geometry = run_translated_geometry_sweep()
    passed = bool(
        oracle["passed"]
        and reparameterization["passed"]
        and translation["passed"]
        and translated_geometry["passed"]
    )
    return {
        "claim_scope": (
            "diagnostic numerical-method validation only; no physical-model, "
            "observational, native-solver, novelty, or publication claim"
        ),
        "input_hashes": {
            MODULE_PATH.relative_to(REPO_ROOT).as_posix(): _sha256(MODULE_PATH),
            SCRIPT_PATH.relative_to(REPO_ROOT).as_posix(): _sha256(SCRIPT_PATH),
        },
        "oracle": oracle,
        "reparameterization": reparameterization,
        "schema": SCHEMA,
        "status": "PASS" if passed else "FAIL",
        "translation": translation,
        "translated_geometry": translated_geometry,
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
