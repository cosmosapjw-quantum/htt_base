"""Deterministic Task-7A evidence for the WU-011 processed boost response.

This module packages the reviewed finite, linear, Jacobian, nuisance, and
historical-parity paths into one content-bound synthetic evidence object.  It
adds no observed-data path and performs no empirical velocity fit.  Full-sky
identity-transfer cases are compared with the exact irrep spectrum through an
explicit HEALPix resolution ladder rather than being mislabelled as machine-
exact at development resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import csv
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Mapping

import numpy as np

from .planck_pr3_operator import build_joint_cutsky_operator, fit_joint_cutsky_alm
from .processed_boost_jacobian import (
    ProcessedBoostJacobian,
    build_processed_boost_jacobian,
    full_sky_metric_reference,
    metric_whitened_matrix,
)
from .processed_boost_linearization import (
    FiniteToLinearDiagnostic,
    MutationOrderDiagnostic,
    finite_to_linear_diagnostic,
    mutation_order_diagnostic,
)
from .processed_boost_operator import ProcessedBoostOperator
from .processed_boost_parity import (
    HistoricalFixedAxisParity,
    WeightedFWLParity,
    historical_fixed_axis_parity,
    weighted_fwl_retained_solution,
)
from .processed_boost_response import (
    FIT_LMAX,
    RETAINED_LMIN,
    SOURCE_LMAX,
    PositiveAbsoluteSkySpec,
    ProcessedBoostError,
    healpix_sky_directions,
    joint_to_scientific_real,
    source_convolved_finite_map,
)


_EVIDENCE_SCHEMA = "HTT_WU011_TASK7A_EVIDENCE_V2"
_TERMINAL_SCHEMA = "HTT_WU011_TASK7A_TERMINAL_V2"
_ARTIFACT_SCHEMA = "HTT_WU011_TASK7A_ARTIFACT_SET_V2"
_REVISION_RE = re.compile(r"^[0-9a-f]{40}$")
_CASE_IDS = (
    "FULL_N8_L7_IDENTITY",
    "FULL_N16_L7_IDENTITY",
    "FULL_N32_L7_IDENTITY",
    "FULL_N32_L12_IDENTITY",
    "CUT_N16_L12_REFERENCE",
)
_MIN_RESOLUTION_IMPROVEMENT = 3.5
_HIGHRES_SPECTRUM_CEILING = 6.0e-4
_HIGHRES_TRACE_CEILING = 1.0e-7
_HIGHRES_CONDITION_RELATIVE_CEILING = 1.0e-6
_HIGHRES_ALIAS_RATIO_CEILING = 4.0e-4
_RESOLUTION_DRIFT_CEILING = 8.0e-4
_CUTOFF_DRIFT_CEILING = 1.0e-8
_FULLSKY_NULL_CEILING = 2.0e-8
_MONOPOLE_REPLAY_RELATIVE_CEILING = 5.0e-4
_MIN_CUT_TO_MATCHED_FULL_ALIAS_RATIO = 10.0
_MIN_CUT_ALIAS_NORM = 1.0e-10
_MIN_TRANSFER_ORDER_RELATIVE_DIFFERENCE = 1.0e-8
_FWL_RESIDUAL_CEILING = 3.0e-12
_HISTORICAL_PARITY_CEILING = 2.0e-3
_SIGN_KILL_FLOOR = 1.5


class Task7ATerminal(str, Enum):
    """Typed terminal states for the bounded Task-7A evidence node."""

    PASS_TASK7A_CORE_EVIDENCE = "PASS_TASK7A_CORE_EVIDENCE"
    BLOCKED_BY_FULLSKY_ORACLE_MISMATCH = "BLOCKED_BY_FULLSKY_ORACLE_MISMATCH"
    BLOCKED_BY_RESOLUTION_NONCONVERGENCE = "BLOCKED_BY_RESOLUTION_NONCONVERGENCE"
    BLOCKED_BY_CUTOFF_NONCONVERGENCE = "BLOCKED_BY_CUTOFF_NONCONVERGENCE"
    BLOCKED_BY_LINEARIZATION_FAILURE = "BLOCKED_BY_LINEARIZATION_FAILURE"
    BLOCKED_BY_MUTATION_SURVIVAL = "BLOCKED_BY_MUTATION_SURVIVAL"
    BLOCKED_BY_FWL_PARITY_FAILURE = "BLOCKED_BY_FWL_PARITY_FAILURE"
    BLOCKED_BY_HISTORICAL_PARITY_FAILURE = "BLOCKED_BY_HISTORICAL_PARITY_FAILURE"
    BLOCKED_BY_ALIAS_UNCONTROLLED = "BLOCKED_BY_ALIAS_UNCONTROLLED"
    BLOCKED_BY_ARTIFACT_INTEGRITY = "BLOCKED_BY_ARTIFACT_INTEGRITY"


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _content_id(payload: Mapping[str, object]) -> str:
    return "sha256:" + hashlib.sha256(
        b"htt-wu011-task7a\0" + _canonical_json(payload)
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stored_real_metric(lmin: int, lmax: int) -> np.ndarray:
    values: list[float] = []
    for ell in range(lmin, lmax + 1):
        values.append(1.0)
        values.extend([2.0] * (2 * ell))
    result = np.asarray(values, dtype=np.float64)
    result.setflags(write=False)
    return result


def _scientific_norm(values: object, metric_diagonal: object) -> float:
    vector = np.asarray(values, dtype=np.float64)
    metric = np.asarray(metric_diagonal, dtype=np.float64)
    if (
        vector.shape != metric.shape
        or vector.ndim != 1
        or not np.all(np.isfinite(vector))
        or not np.all(np.isfinite(metric))
        or np.any(metric <= 0.0)
    ):
        raise ProcessedBoostError("scientific norm inputs are invalid")
    return math.sqrt(max(0.0, float(np.dot(metric, vector * vector))))


def _block_metric_norm(
    block: object,
    *,
    output_metric_diagonal: object,
    source_ell: int,
) -> float:
    array = np.asarray(block, dtype=np.float64)
    output_metric = np.asarray(output_metric_diagonal, dtype=np.float64)
    source_width = 2 * source_ell + 1
    if array.shape != (3, 32, source_width):
        raise ProcessedBoostError("processed response block has the wrong shape")
    source_metric = _stored_real_metric(source_ell, source_ell)
    whitened = metric_whitened_matrix(
        array.reshape(96, source_width),
        source_metric_diagonal=source_metric,
        output_metric_diagonal=np.tile(output_metric, 3),
    )
    return float(np.linalg.norm(whitened))


def _monopole_metric_norm(
    leakage: object,
    *,
    output_metric_diagonal: object,
) -> float:
    array = np.asarray(leakage, dtype=np.float64)
    metric = np.tile(np.asarray(output_metric_diagonal, dtype=np.float64), 3)
    if array.shape != (3, 32):
        raise ProcessedBoostError("monopole replay leakage has the wrong shape")
    vector = array.reshape(96)
    return math.sqrt(
        max(0.0, float(np.dot(metric, vector * vector)) / (4.0 * math.pi))
    )


def _relative_matrix_drift(left: np.ndarray, right: np.ndarray) -> float:
    denominator = max(float(np.linalg.norm(right)), np.finfo(float).tiny)
    return float(np.linalg.norm(left - right) / denominator)


def full_sky_expected_singular_values() -> np.ndarray:
    """Return the descending 48-sector spectrum followed by the T0 null."""

    reference = full_sky_metric_reference()
    values: list[float] = []
    for sigma_squared, multiplicity in zip(
        reference.sigma_squared_by_source_ell,
        reference.multiplicities,
    ):
        values.extend([math.sqrt(sigma_squared)] * multiplicity)
    values.sort(reverse=True)
    values.append(0.0)
    result = np.asarray(values, dtype=np.float64)
    result.setflags(write=False)
    return result


def _reference_source_sky() -> PositiveAbsoluteSkySpec:
    coefficients = np.zeros(48, dtype=np.float64)
    coefficients[0:3] = (0.004, -0.003, 0.002)
    coefficients[3:8] = (0.018, -0.011, 0.007, 0.013, -0.009)
    ell5_start = sum(2 * ell + 1 for ell in range(1, 5))
    coefficients[ell5_start] = 0.006
    coefficients[ell5_start + 5] = -0.004
    ell6_start = sum(2 * ell + 1 for ell in range(1, 6))
    coefficients[ell6_start + 2] = 0.002
    return PositiveAbsoluteSkySpec(2.7255, coefficients, SOURCE_LMAX, "K_CMB")


def _build_operator(
    *,
    nside: int,
    processing_lmax: int,
    mask_kind: str,
    transfer_kind: str,
) -> ProcessedBoostOperator:
    directions = healpix_sky_directions(nside)
    if mask_kind == "FULL":
        mask = np.ones(directions.shape[0], dtype=np.float64)
    elif mask_kind == "APODIZED_Z":
        mask = np.clip((directions[:, 2] + 0.45) / 0.9, 0.0, 1.0)
    else:
        raise ProcessedBoostError("Task-7A mask kind is outside the registry")
    joint = build_joint_cutsky_operator(
        mask,
        lmin=0,
        lmax=FIT_LMAX,
        retained_lmin=RETAINED_LMIN,
    )
    ell = np.arange(processing_lmax + 1, dtype=np.float64)
    if transfer_kind == "IDENTITY":
        source_beam = np.ones_like(ell)
        source_pixel = np.ones_like(ell)
        target_beam = np.ones_like(ell)
        target_pixel = np.ones_like(ell)
    elif transfer_kind == "REFERENCE_GAUSSIAN":
        source_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.075**2)
        source_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.025**2)
        target_beam = np.exp(-0.5 * ell * (ell + 1.0) * 0.11**2)
        target_pixel = np.exp(-0.5 * ell * (ell + 1.0) * 0.04**2)
    else:
        raise ProcessedBoostError("Task-7A transfer kind is outside the registry")
    return ProcessedBoostOperator.from_components(
        mask=mask,
        joint_operator=joint,
        processing_lmax=processing_lmax,
        source_beam=source_beam,
        source_pixel_window=source_pixel,
        target_beam=target_beam,
        target_pixel_window=target_pixel,
    )


@dataclass(frozen=True)
class Task7ACase:
    case_id: str
    nside: int
    processing_lmax: int
    mask_kind: str
    transfer_kind: str
    jacobian: ProcessedBoostJacobian
    fullsky_spectrum_max_relative_error: float | None
    fullsky_trace_relative_error: float | None
    fullsky_null_relative: float
    ell6_neighbor_norm: float
    ell6_alias_norm: float
    ell6_decomposition_norm: float
    ell6_alias_to_neighbor: float
    monopole_replay_metric_norm: float
    monopole_relative_to_nonmonopole_max: float

    def scalar_record(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "nside": self.nside,
            "processing_lmax": self.processing_lmax,
            "mask_kind": self.mask_kind,
            "transfer_kind": self.transfer_kind,
            "jacobian_content_id": self.jacobian.content_id,
            "operator_id": self.jacobian.operator_id,
            "metric_whitened_rank": self.jacobian.metric_whitened_rank,
            "metric_whitened_condition": (
                "INF"
                if math.isinf(self.jacobian.metric_whitened_condition_number)
                else self.jacobian.metric_whitened_condition_number
            ),
            "metric_whitened_nonzero_condition": (
                self.jacobian.metric_whitened_nonzero_condition_number
            ),
            "fullsky_spectrum_max_relative_error": (
                self.fullsky_spectrum_max_relative_error
            ),
            "fullsky_trace_relative_error": self.fullsky_trace_relative_error,
            "fullsky_null_relative": self.fullsky_null_relative,
            "ell6_neighbor_norm": self.ell6_neighbor_norm,
            "ell6_alias_norm": self.ell6_alias_norm,
            "ell6_decomposition_norm": self.ell6_decomposition_norm,
            "ell6_alias_to_neighbor": self.ell6_alias_to_neighbor,
            "monopole_replay_metric_norm": self.monopole_replay_metric_norm,
            "monopole_relative_to_nonmonopole_max": (
                self.monopole_relative_to_nonmonopole_max
            ),
        }


def _build_case(
    case_id: str,
    *,
    nside: int,
    processing_lmax: int,
    mask_kind: str,
    transfer_kind: str,
) -> tuple[Task7ACase, ProcessedBoostOperator]:
    operator = _build_operator(
        nside=nside,
        processing_lmax=processing_lmax,
        mask_kind=mask_kind,
        transfer_kind=transfer_kind,
    )
    jacobian = build_processed_boost_jacobian(operator)
    expected = full_sky_expected_singular_values()
    numerical = np.asarray(jacobian.metric_whitened_singular_values, dtype=np.float64)
    if numerical.shape != expected.shape:
        raise ProcessedBoostError("Task-7A singular spectrum shape drifted")
    if mask_kind == "FULL" and transfer_kind == "IDENTITY":
        positive = expected[:-1]
        spectrum_error = float(
            np.max(np.abs(numerical[:-1] - positive) / positive)
        )
        exact_trace = float(np.sum(positive * positive))
        numerical_trace = float(np.sum(numerical[:-1] * numerical[:-1]))
        trace_error = abs(numerical_trace - exact_trace) / exact_trace
    else:
        spectrum_error = None
        trace_error = None
    fullsky_null = abs(float(numerical[-1])) / max(
        float(numerical[0]), np.finfo(float).tiny
    )
    neighbor_norm = _block_metric_norm(
        jacobian.ell6_expected_neighbor_l5_block,
        output_metric_diagonal=jacobian.output_metric_diagonal,
        source_ell=6,
    )
    alias_norm = _block_metric_norm(
        jacobian.ell6_cutsky_alias_residual,
        output_metric_diagonal=jacobian.output_metric_diagonal,
        source_ell=6,
    )
    decomposition_norm = _block_metric_norm(
        jacobian.ell6_decomposition_residual,
        output_metric_diagonal=jacobian.output_metric_diagonal,
        source_ell=6,
    )
    case = Task7ACase(
        case_id=case_id,
        nside=nside,
        processing_lmax=processing_lmax,
        mask_kind=mask_kind,
        transfer_kind=transfer_kind,
        jacobian=jacobian,
        fullsky_spectrum_max_relative_error=spectrum_error,
        fullsky_trace_relative_error=trace_error,
        fullsky_null_relative=fullsky_null,
        ell6_neighbor_norm=neighbor_norm,
        ell6_alias_norm=alias_norm,
        ell6_decomposition_norm=decomposition_norm,
        ell6_alias_to_neighbor=alias_norm / max(neighbor_norm, np.finfo(float).tiny),
        monopole_replay_metric_norm=_monopole_metric_norm(
            jacobian.monopole_replay_leakage,
            output_metric_diagonal=jacobian.output_metric_diagonal,
        ),
        monopole_relative_to_nonmonopole_max=(
            jacobian.monopole_relative_to_nonmonopole_max
        ),
    )
    return case, operator


def _fit_mutated_source_map(
    source_sky: PositiveAbsoluteSkySpec,
    operator: ProcessedBoostOperator,
    beta: np.ndarray,
    *,
    mutation: str | None,
) -> np.ndarray:
    source_map = source_convolved_finite_map(
        source_sky,
        beta,
        nside=operator.nside,
        processing_lmax=operator.processing_lmax,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
        mutation=mutation,
    )
    fit = fit_joint_cutsky_alm(
        source_map.pixel_map,
        mask=operator.mask,
        operator=operator.joint_operator,
        source_beam=operator.source_beam,
        source_pixel_window=operator.source_pixel_window,
        target_beam=operator.target_beam,
        target_pixel_window=operator.target_pixel_window,
    )
    return joint_to_scientific_real(
        fit.retained_coefficients,
        lmin=RETAINED_LMIN,
        lmax=FIT_LMAX,
    )


def _transfer_order_difference(
    source_sky: PositiveAbsoluteSkySpec,
    operator: ProcessedBoostOperator,
) -> float:
    beta = np.asarray([0.012, -0.007, 0.009], dtype=np.float64)
    zero = np.zeros(3, dtype=np.float64)
    correct = _fit_mutated_source_map(source_sky, operator, beta, mutation=None)
    correct_zero = _fit_mutated_source_map(source_sky, operator, zero, mutation=None)
    mutated = _fit_mutated_source_map(
        source_sky,
        operator,
        beta,
        mutation="TRANSFER_BEFORE_BOOST",
    )
    mutated_zero = _fit_mutated_source_map(
        source_sky,
        operator,
        zero,
        mutation="TRANSFER_BEFORE_BOOST",
    )
    correct_increment = correct - correct_zero
    mutated_increment = mutated - mutated_zero
    metric = _stored_real_metric(RETAINED_LMIN, FIT_LMAX)
    numerator = _scientific_norm(correct_increment - mutated_increment, metric)
    denominator = _scientific_norm(correct_increment, metric)
    return numerator / max(denominator, np.finfo(float).tiny)


@dataclass(frozen=True)
class Task7AEvidence:
    source_revision: str
    profile: str
    cases: tuple[Task7ACase, ...]
    fullsky_resolution_relative_drifts: tuple[float, float]
    fullsky_cutoff_relative_drift: float
    finite_to_linear: FiniteToLinearDiagnostic
    mutations: MutationOrderDiagnostic
    fwl: WeightedFWLParity
    historical: HistoricalFixedAxisParity
    transfer_order_relative_difference: float
    terminal: Task7ATerminal
    content_id: str = field(init=False)

    def __post_init__(self) -> None:
        if _REVISION_RE.fullmatch(self.source_revision) is None:
            raise ProcessedBoostError("Task-7A source revision must be a 40-hex identity")
        if self.profile != "CI_CORE":
            raise ProcessedBoostError("Task-7A profile is outside the frozen registry")
        if tuple(case.case_id for case in self.cases) != _CASE_IDS:
            raise ProcessedBoostError("Task-7A case registry drifted")
        if len(self.fullsky_resolution_relative_drifts) != 2:
            raise ProcessedBoostError("Task-7A resolution-drift registry drifted")
        object.__setattr__(
            self,
            "content_id",
            _content_id(self.scalar_record(include_content_id=False)),
        )

    def scalar_record(self, *, include_content_id: bool = True) -> dict[str, object]:
        n8, n16, n32, _n32_high, _cut = self.cases
        spectrum_errors = [
            float(n8.fullsky_spectrum_max_relative_error or 0.0),
            float(n16.fullsky_spectrum_max_relative_error or 0.0),
            float(n32.fullsky_spectrum_max_relative_error or 0.0),
        ]
        alias_ratios = [
            n8.ell6_alias_to_neighbor,
            n16.ell6_alias_to_neighbor,
            n32.ell6_alias_to_neighbor,
        ]
        record: dict[str, object] = {
            "schema": _EVIDENCE_SCHEMA,
            "source_revision": self.source_revision,
            "profile": self.profile,
            "terminal": self.terminal.value,
            "cases": [case.scalar_record() for case in self.cases],
            "fullsky_resolution_relative_drifts": list(
                self.fullsky_resolution_relative_drifts
            ),
            "fullsky_cutoff_relative_drift": self.fullsky_cutoff_relative_drift,
            "fullsky_spectrum_convergence_orders": [
                math.log(spectrum_errors[0] / spectrum_errors[1], 2.0),
                math.log(spectrum_errors[1] / spectrum_errors[2], 2.0),
            ],
            "fullsky_alias_convergence_orders": [
                math.log(alias_ratios[0] / alias_ratios[1], 2.0),
                math.log(alias_ratios[1] / alias_ratios[2], 2.0),
            ],
            "finite_to_linear": {
                "amplitudes": list(self.finite_to_linear.amplitudes),
                "residual_norms": list(self.finite_to_linear.residual_norms),
                "scaled_quadratic_norms": list(
                    self.finite_to_linear.scaled_quadratic_norms
                ),
                "residual_slope": self.finite_to_linear.residual_slope,
                "scaled_plateau_relative_spread": (
                    self.finite_to_linear.scaled_plateau_relative_spread
                ),
            },
            "mutations": {
                "amplitudes": list(self.mutations.amplitudes),
                "wrong_sign_retained_norms": list(
                    self.mutations.wrong_sign_retained_norms
                ),
                "omitted_l1_pixel_norms": list(
                    self.mutations.omitted_l1_pixel_norms
                ),
                "wrong_sign_retained_slope": (
                    self.mutations.wrong_sign_retained_slope
                ),
                "omitted_l1_pixel_slope": self.mutations.omitted_l1_pixel_slope,
                "omitted_l1_retained_relative_norm": (
                    self.mutations.omitted_l1_retained_relative_norm
                ),
            },
            "fwl": {
                "content_id": self.fwl.content_id,
                "nuisance_rank": self.fwl.nuisance_rank,
                "schur_rank": self.fwl.schur_rank,
                "schur_condition_number": self.fwl.schur_condition_number,
                "full_solve_max_abs_residual": self.fwl.full_solve_max_abs_residual,
            },
            "historical": {
                "content_id": self.historical.content_id,
                "relative_increment_residual": (
                    self.historical.relative_increment_residual
                ),
                "sign_mutation_relative_residual": (
                    self.historical.sign_mutation_relative_residual
                ),
                "generic_increment_norm": self.historical.generic_increment_norm,
                "legacy_increment_norm": self.historical.legacy_increment_norm,
                "max_abs_increment_residual": (
                    self.historical.max_abs_increment_residual
                ),
            },
            "transfer_order_relative_difference": (
                self.transfer_order_relative_difference
            ),
            "claim_boundary": {
                "synthetic_processed_local_observer_scalar_response": True,
                "fullsky_numerical_oracle": "RESOLUTION_CONVERGENT_NOT_MACHINE_EXACT",
                "raw_planck_absolute_temperature_admitted": False,
                "observed_rank": False,
                "empirical_beta": False,
                "boost_subtraction": False,
                "global_tilt": False,
                "polarization_result": False,
                "foreground_exclusion": False,
                "bianchi_attribution": False,
                "formal_P01_P27_replay": False,
                "merge_authorized": False,
            },
        }
        if include_content_id:
            record["content_id"] = self.content_id
        return record


def _terminal_for(
    cases: tuple[Task7ACase, ...],
    *,
    resolution_drifts: tuple[float, float],
    cutoff_drift: float,
    finite: FiniteToLinearDiagnostic,
    mutations: MutationOrderDiagnostic,
    fwl: WeightedFWLParity,
    historical: HistoricalFixedAxisParity,
    transfer_order_relative_difference: float,
) -> Task7ATerminal:
    n8, n16, n32, n32_high, cut = cases
    full = (n8, n16, n32, n32_high)
    if any(
        case.fullsky_spectrum_max_relative_error is None
        or case.fullsky_trace_relative_error is None
        or case.fullsky_null_relative > _FULLSKY_NULL_CEILING
        or case.jacobian.metric_whitened_rank != 48
        or not math.isinf(case.jacobian.metric_whitened_condition_number)
        for case in full
    ):
        return Task7ATerminal.BLOCKED_BY_FULLSKY_ORACLE_MISMATCH

    spectrum_errors = np.asarray(
        [
            n8.fullsky_spectrum_max_relative_error,
            n16.fullsky_spectrum_max_relative_error,
            n32.fullsky_spectrum_max_relative_error,
        ],
        dtype=np.float64,
    )
    alias_ratios = np.asarray(
        [n8.ell6_alias_to_neighbor, n16.ell6_alias_to_neighbor, n32.ell6_alias_to_neighbor],
        dtype=np.float64,
    )
    exact_condition = math.sqrt(63.0 / 8.0)
    condition_error = abs(
        n32.jacobian.metric_whitened_nonzero_condition_number - exact_condition
    ) / exact_condition
    if not (
        np.all(spectrum_errors[:-1] > spectrum_errors[1:])
        and np.all(
            spectrum_errors[:-1] / spectrum_errors[1:]
            >= _MIN_RESOLUTION_IMPROVEMENT
        )
        and spectrum_errors[-1] <= _HIGHRES_SPECTRUM_CEILING
        and float(n32.fullsky_trace_relative_error) <= _HIGHRES_TRACE_CEILING
        and float(n32_high.fullsky_spectrum_max_relative_error)
        <= _HIGHRES_SPECTRUM_CEILING
        and float(n32_high.fullsky_trace_relative_error) <= _HIGHRES_TRACE_CEILING
        and condition_error <= _HIGHRES_CONDITION_RELATIVE_CEILING
        and np.all(alias_ratios[:-1] > alias_ratios[1:])
        and np.all(
            alias_ratios[:-1] / alias_ratios[1:]
            >= _MIN_RESOLUTION_IMPROVEMENT
        )
        and alias_ratios[-1] <= _HIGHRES_ALIAS_RATIO_CEILING
        and resolution_drifts[0] > resolution_drifts[1]
        and resolution_drifts[0] / resolution_drifts[1]
        >= _MIN_RESOLUTION_IMPROVEMENT
        and resolution_drifts[1] <= _RESOLUTION_DRIFT_CEILING
    ):
        return Task7ATerminal.BLOCKED_BY_RESOLUTION_NONCONVERGENCE
    if cutoff_drift > _CUTOFF_DRIFT_CEILING:
        return Task7ATerminal.BLOCKED_BY_CUTOFF_NONCONVERGENCE
    if not (
        1.8 <= finite.residual_slope <= 2.2
        and finite.scaled_plateau_relative_spread <= 0.35
    ):
        return Task7ATerminal.BLOCKED_BY_LINEARIZATION_FAILURE
    if not (
        0.8 <= mutations.wrong_sign_retained_slope <= 1.2
        and 0.8 <= mutations.omitted_l1_pixel_slope <= 1.2
        and mutations.omitted_l1_retained_relative_norm <= 2.0e-8
        and historical.sign_mutation_relative_residual >= _SIGN_KILL_FLOOR
        and transfer_order_relative_difference
        >= _MIN_TRANSFER_ORDER_RELATIVE_DIFFERENCE
    ):
        return Task7ATerminal.BLOCKED_BY_MUTATION_SURVIVAL
    if fwl.full_solve_max_abs_residual > _FWL_RESIDUAL_CEILING:
        return Task7ATerminal.BLOCKED_BY_FWL_PARITY_FAILURE
    if historical.relative_increment_residual > _HISTORICAL_PARITY_CEILING:
        return Task7ATerminal.BLOCKED_BY_HISTORICAL_PARITY_FAILURE
    if (
        cut.ell6_alias_norm
        <= _MIN_CUT_TO_MATCHED_FULL_ALIAS_RATIO
        * max(n16.ell6_alias_norm, np.finfo(float).tiny)
        or cut.ell6_alias_norm <= _MIN_CUT_ALIAS_NORM
        or cut.monopole_relative_to_nonmonopole_max
        > _MONOPOLE_REPLAY_RELATIVE_CEILING
    ):
        return Task7ATerminal.BLOCKED_BY_ALIAS_UNCONTROLLED
    return Task7ATerminal.PASS_TASK7A_CORE_EVIDENCE


def build_task7a_evidence(
    *,
    source_revision: str,
    profile: str = "CI_CORE",
) -> Task7AEvidence:
    """Build the bounded deterministic Task-7A core evidence object."""

    if _REVISION_RE.fullmatch(source_revision) is None:
        raise ProcessedBoostError("Task-7A source revision must be a 40-hex identity")
    if profile != "CI_CORE":
        raise ProcessedBoostError("Task-7A profile is outside the frozen registry")

    n8, _ = _build_case(
        "FULL_N8_L7_IDENTITY",
        nside=8,
        processing_lmax=7,
        mask_kind="FULL",
        transfer_kind="IDENTITY",
    )
    n16, _ = _build_case(
        "FULL_N16_L7_IDENTITY",
        nside=16,
        processing_lmax=7,
        mask_kind="FULL",
        transfer_kind="IDENTITY",
    )
    n32, _ = _build_case(
        "FULL_N32_L7_IDENTITY",
        nside=32,
        processing_lmax=7,
        mask_kind="FULL",
        transfer_kind="IDENTITY",
    )
    n32_high, _ = _build_case(
        "FULL_N32_L12_IDENTITY",
        nside=32,
        processing_lmax=12,
        mask_kind="FULL",
        transfer_kind="IDENTITY",
    )
    cut, cut_operator = _build_case(
        "CUT_N16_L12_REFERENCE",
        nside=16,
        processing_lmax=12,
        mask_kind="APODIZED_Z",
        transfer_kind="REFERENCE_GAUSSIAN",
    )
    cases = (n8, n16, n32, n32_high, cut)
    resolution_drifts = (
        _relative_matrix_drift(
            n8.jacobian.metric_whitened_stacked_matrix,
            n16.jacobian.metric_whitened_stacked_matrix,
        ),
        _relative_matrix_drift(
            n16.jacobian.metric_whitened_stacked_matrix,
            n32.jacobian.metric_whitened_stacked_matrix,
        ),
    )
    cutoff_drift = _relative_matrix_drift(
        n32.jacobian.metric_whitened_stacked_matrix,
        n32_high.jacobian.metric_whitened_stacked_matrix,
    )

    source = _reference_source_sky()
    direction = np.asarray([0.4, -0.2, 0.3], dtype=np.float64)
    direction /= np.linalg.norm(direction)
    finite = finite_to_linear_diagnostic(
        source,
        cut_operator,
        beta_direction=direction,
        amplitudes=(3.2e-2, 1.6e-2, 8.0e-3, 4.0e-3),
    )
    mutations = mutation_order_diagnostic(
        source,
        cut_operator,
        beta_direction=direction,
        amplitudes=(8.0e-4, 4.0e-4, 2.0e-4, 1.0e-4),
    )
    parity_beta = np.asarray([0.012, -0.007, 0.009], dtype=np.float64)
    parity_map = source_convolved_finite_map(
        source,
        parity_beta,
        nside=cut_operator.nside,
        processing_lmax=cut_operator.processing_lmax,
        source_beam=cut_operator.source_beam,
        source_pixel_window=cut_operator.source_pixel_window,
    )
    fwl = weighted_fwl_retained_solution(parity_map.pixel_map, cut_operator)
    historical = historical_fixed_axis_parity(
        source,
        nside=16,
        lmax=12,
        beta=0.02,
    )
    transfer_difference = _transfer_order_difference(source, cut_operator)
    terminal = _terminal_for(
        cases,
        resolution_drifts=resolution_drifts,
        cutoff_drift=cutoff_drift,
        finite=finite,
        mutations=mutations,
        fwl=fwl,
        historical=historical,
        transfer_order_relative_difference=transfer_difference,
    )
    return Task7AEvidence(
        source_revision=source_revision,
        profile=profile,
        cases=cases,
        fullsky_resolution_relative_drifts=resolution_drifts,
        fullsky_cutoff_relative_drift=cutoff_drift,
        finite_to_linear=finite,
        mutations=mutations,
        fwl=fwl,
        historical=historical,
        transfer_order_relative_difference=transfer_difference,
        terminal=terminal,
    )


@dataclass(frozen=True)
class Task7AArtifactBundle:
    output_dir: Path
    file_sha256: dict[str, str]
    manifest_sha256: str


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n",
        encoding="ascii",
    )


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ProcessedBoostError("Task-7A CSV table may not be empty")
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0].keys()),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _gate_rows(report: Task7AEvidence) -> list[dict[str, object]]:
    n8, n16, n32, n32_high, cut = report.cases
    spectrum_improvement = min(
        float(n8.fullsky_spectrum_max_relative_error)
        / float(n16.fullsky_spectrum_max_relative_error),
        float(n16.fullsky_spectrum_max_relative_error)
        / float(n32.fullsky_spectrum_max_relative_error),
    )
    alias_improvement = min(
        n8.ell6_alias_to_neighbor / n16.ell6_alias_to_neighbor,
        n16.ell6_alias_to_neighbor / n32.ell6_alias_to_neighbor,
    )
    drift_improvement = (
        report.fullsky_resolution_relative_drifts[0]
        / report.fullsky_resolution_relative_drifts[1]
    )
    exact_condition = math.sqrt(63.0 / 8.0)
    condition_error = abs(
        n32.jacobian.metric_whitened_nonzero_condition_number - exact_condition
    ) / exact_condition
    return [
        {
            "gate": "highres_spectrum",
            "normalized_margin": max(
                float(n32.fullsky_spectrum_max_relative_error),
                float(n32_high.fullsky_spectrum_max_relative_error),
            )
            / _HIGHRES_SPECTRUM_CEILING,
        },
        {
            "gate": "highres_trace",
            "normalized_margin": max(
                float(n32.fullsky_trace_relative_error),
                float(n32_high.fullsky_trace_relative_error),
            )
            / _HIGHRES_TRACE_CEILING,
        },
        {
            "gate": "condition_oracle",
            "normalized_margin": condition_error
            / _HIGHRES_CONDITION_RELATIVE_CEILING,
        },
        {
            "gate": "spectrum_convergence",
            "normalized_margin": _MIN_RESOLUTION_IMPROVEMENT
            / spectrum_improvement,
        },
        {
            "gate": "alias_convergence",
            "normalized_margin": _MIN_RESOLUTION_IMPROVEMENT / alias_improvement,
        },
        {
            "gate": "matrix_convergence",
            "normalized_margin": max(
                report.fullsky_resolution_relative_drifts[1]
                / _RESOLUTION_DRIFT_CEILING,
                _MIN_RESOLUTION_IMPROVEMENT / drift_improvement,
            ),
        },
        {
            "gate": "processing_cutoff",
            "normalized_margin": report.fullsky_cutoff_relative_drift
            / _CUTOFF_DRIFT_CEILING,
        },
        {
            "gate": "highres_alias",
            "normalized_margin": n32.ell6_alias_to_neighbor
            / _HIGHRES_ALIAS_RATIO_CEILING,
        },
        {
            "gate": "cut_alias_detection",
            "normalized_margin": (
                _MIN_CUT_TO_MATCHED_FULL_ALIAS_RATIO
                * n16.ell6_alias_norm
                / max(cut.ell6_alias_norm, np.finfo(float).tiny)
            ),
        },
        {
            "gate": "monopole_replay",
            "normalized_margin": cut.monopole_relative_to_nonmonopole_max
            / _MONOPOLE_REPLAY_RELATIVE_CEILING,
        },
        {
            "gate": "finite_slope",
            "normalized_margin": abs(report.finite_to_linear.residual_slope - 2.0)
            / 0.2,
        },
        {
            "gate": "fwl_parity",
            "normalized_margin": report.fwl.full_solve_max_abs_residual
            / _FWL_RESIDUAL_CEILING,
        },
        {
            "gate": "historical_parity",
            "normalized_margin": report.historical.relative_increment_residual
            / _HISTORICAL_PARITY_CEILING,
        },
        {
            "gate": "sign_kill",
            "normalized_margin": _SIGN_KILL_FLOOR
            / max(
                report.historical.sign_mutation_relative_residual,
                np.finfo(float).tiny,
            ),
        },
        {
            "gate": "transfer_order_kill",
            "normalized_margin": _MIN_TRANSFER_ORDER_RELATIVE_DIFFERENCE
            / max(report.transfer_order_relative_difference, np.finfo(float).tiny),
        },
    ]


def _write_plots(report: Task7AEvidence, output_dir: Path) -> None:
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt

    metadata = {"Software": "htt_base WU011 Task7A"}
    expected = full_sky_expected_singular_values()[:-1]
    x = np.arange(1, expected.size + 1)
    plt.figure(figsize=(7.2, 4.8))
    plt.plot(x, expected, label="Exact irrep spectrum")
    for case, marker in zip(report.cases[:4], ("o", "s", "^", "x")):
        numerical = np.asarray(
            case.jacobian.metric_whitened_singular_values[:-1],
            dtype=np.float64,
        )
        plt.plot(
            x,
            numerical,
            marker=marker,
            markersize=2.3,
            label=case.case_id,
        )
    plt.xlabel("Descending nonzero singular-value index")
    plt.ylabel("Metric-whitened singular value")
    plt.title("WU-011 exact and HEALPix full-sky spectra")
    plt.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(
        output_dir / "metric_spectrum_exact_vs_numerical.png",
        dpi=180,
        metadata=metadata,
    )
    plt.close()

    nsides = np.asarray([8.0, 16.0, 32.0])
    resolution_cases = report.cases[:3]
    spectrum_errors = np.asarray(
        [case.fullsky_spectrum_max_relative_error for case in resolution_cases],
        dtype=np.float64,
    )
    trace_errors = np.asarray(
        [case.fullsky_trace_relative_error for case in resolution_cases],
        dtype=np.float64,
    )
    alias_ratios = np.asarray(
        [case.ell6_alias_to_neighbor for case in resolution_cases],
        dtype=np.float64,
    )
    plt.figure(figsize=(6.8, 4.8))
    plt.loglog(nsides, spectrum_errors, marker="o", label="Max spectrum error")
    plt.loglog(nsides, trace_errors, marker="s", label="Trace error")
    plt.loglog(nsides, alias_ratios, marker="^", label="ell=7 alias / ell=5 neighbour")
    plt.xlabel("HEALPix nside")
    plt.ylabel("Relative full-sky error")
    plt.title("WU-011 full-sky resolution convergence")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        output_dir / "fullsky_resolution_convergence.png",
        dpi=180,
        metadata=metadata,
    )
    plt.close()

    amplitudes = np.asarray(report.finite_to_linear.amplitudes, dtype=np.float64)
    residuals = np.asarray(report.finite_to_linear.residual_norms, dtype=np.float64)
    quadratic = residuals[0] * (amplitudes / amplitudes[0]) ** 2
    plt.figure(figsize=(6.8, 4.8))
    plt.loglog(amplitudes, residuals, marker="o", label="Finite - zero - linear")
    plt.loglog(amplitudes, quadratic, label="O(beta^2) reference")
    plt.xlabel("Boost amplitude |beta|")
    plt.ylabel("Retained scientific residual norm")
    plt.title("WU-011 finite-to-linear convergence")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        output_dir / "finite_to_linear_scaling.png",
        dpi=180,
        metadata=metadata,
    )
    plt.close()

    labels = [case.case_id for case in report.cases]
    axis = np.arange(len(labels))
    floor = np.finfo(float).tiny
    plt.figure(figsize=(8.0, 4.8))
    plt.plot(
        axis,
        [max(case.ell6_neighbor_norm, floor) for case in report.cases],
        marker="o",
        label="Physical ell=6 to ell=5",
    )
    plt.plot(
        axis,
        [max(case.ell6_alias_norm, floor) for case in report.cases],
        marker="s",
        label="Raised ell=7 processed alias",
    )
    plt.plot(
        axis,
        [max(case.ell6_decomposition_norm, floor) for case in report.cases],
        marker="^",
        label="Numerical decomposition residual",
    )
    plt.plot(
        axis,
        [max(case.monopole_replay_metric_norm, floor) for case in report.cases],
        marker="x",
        label="Metric-whitened monopole replay",
    )
    plt.yscale("log")
    plt.xticks(axis, labels, rotation=18, ha="right")
    plt.ylabel("Metric-whitened response norm")
    plt.title("WU-011 processed response channels")
    plt.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(
        output_dir / "processed_channel_norms.png",
        dpi=180,
        metadata=metadata,
    )
    plt.close()

    gate_rows = _gate_rows(report)
    gate_labels = [str(row["gate"]) for row in gate_rows]
    margins = [
        max(float(row["normalized_margin"]), floor) for row in gate_rows
    ]
    plt.figure(figsize=(9.0, 4.8))
    plt.bar(np.arange(len(gate_labels)), margins)
    plt.axhline(1.0, linestyle="--")
    plt.yscale("log")
    plt.xticks(np.arange(len(gate_labels)), gate_labels, rotation=38, ha="right")
    plt.ylabel("Normalized failure margin (<=1 passes)")
    plt.title("WU-011 Task-7A gate margins")
    plt.tight_layout()
    plt.savefig(
        output_dir / "normalized_gate_margins.png",
        dpi=180,
        metadata=metadata,
    )
    plt.close()


def write_task7a_artifacts(
    report: Task7AEvidence,
    output_dir: Path,
) -> Task7AArtifactBundle:
    """Write one deterministic, checksum-addressed Task-7A evidence package."""

    if type(report) is not Task7AEvidence:
        raise ProcessedBoostError("Task-7A artifact writer requires an exact evidence object")
    output = Path(output_dir)
    if output.exists() and any(output.iterdir()):
        raise ProcessedBoostError("Task-7A output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)

    terminal = {
        "schema": _TERMINAL_SCHEMA,
        "terminal": report.terminal.value,
        "source_revision": report.source_revision,
        "profile": report.profile,
        "report_content_id": report.content_id,
        "claim_promotion": False,
        "merge_authorized": False,
    }
    _write_json(output / "terminal.json", terminal)
    _write_json(output / "summary.json", report.scalar_record())
    _write_csv(output / "cases.csv", [case.scalar_record() for case in report.cases])

    expected = full_sky_expected_singular_values()
    spectrum_rows: list[dict[str, object]] = []
    for index, exact in enumerate(expected):
        spectrum_rows.append(
            {
                "descending_index": index + 1,
                "exact": float(exact),
                "full_n8_l7": float(
                    report.cases[0].jacobian.metric_whitened_singular_values[index]
                ),
                "full_n16_l7": float(
                    report.cases[1].jacobian.metric_whitened_singular_values[index]
                ),
                "full_n32_l7": float(
                    report.cases[2].jacobian.metric_whitened_singular_values[index]
                ),
                "full_n32_l12": float(
                    report.cases[3].jacobian.metric_whitened_singular_values[index]
                ),
                "structural_null": index == expected.size - 1,
            }
        )
    _write_csv(output / "fullsky_singular_spectrum.csv", spectrum_rows)
    _write_csv(
        output / "fullsky_resolution_convergence.csv",
        [
            {
                "nside": case.nside,
                "processing_lmax": case.processing_lmax,
                "max_spectrum_relative_error": (
                    case.fullsky_spectrum_max_relative_error
                ),
                "trace_relative_error": case.fullsky_trace_relative_error,
                "ell6_alias_to_neighbor": case.ell6_alias_to_neighbor,
                "monopole_replay_relative": (
                    case.monopole_relative_to_nonmonopole_max
                ),
            }
            for case in report.cases[:4]
        ],
    )
    _write_csv(
        output / "finite_to_linear_scaling.csv",
        [
            {
                "amplitude": amplitude,
                "residual_norm": residual,
                "residual_over_beta_squared": scaled,
            }
            for amplitude, residual, scaled in zip(
                report.finite_to_linear.amplitudes,
                report.finite_to_linear.residual_norms,
                report.finite_to_linear.scaled_quadratic_norms,
            )
        ],
    )
    _write_csv(output / "gate_ratios.csv", _gate_rows(report))

    for case in report.cases:
        np.save(
            output / f"{case.case_id}_scientific_jacobian.npy",
            np.asarray(case.jacobian.tensor, dtype="<f8"),
            allow_pickle=False,
        )
    cut = report.cases[4]
    np.save(
        output / "CUT_N16_L12_REFERENCE_raw_replay_jacobian.npy",
        np.asarray(cut.jacobian.raw_replay_tensor, dtype="<f8"),
        allow_pickle=False,
    )
    np.save(
        output / "CUT_N16_L12_REFERENCE_ell6_neighbor.npy",
        np.asarray(cut.jacobian.ell6_expected_neighbor_l5_block, dtype="<f8"),
        allow_pickle=False,
    )
    np.save(
        output / "CUT_N16_L12_REFERENCE_ell6_alias.npy",
        np.asarray(cut.jacobian.ell6_cutsky_alias_residual, dtype="<f8"),
        allow_pickle=False,
    )
    np.save(
        output / "CUT_N16_L12_REFERENCE_ell6_decomposition.npy",
        np.asarray(cut.jacobian.ell6_decomposition_residual, dtype="<f8"),
        allow_pickle=False,
    )
    _write_plots(report, output)

    files = sorted(path for path in output.iterdir() if path.is_file())
    hashes = {path.name: _file_sha256(path) for path in files}
    manifest = "".join(f"{digest}  {name}\n" for name, digest in sorted(hashes.items()))
    (output / "SHA256SUMS").write_text(manifest, encoding="ascii")
    return Task7AArtifactBundle(
        output_dir=output,
        file_sha256=hashes,
        manifest_sha256=_file_sha256(output / "SHA256SUMS"),
    )


def verify_task7a_artifacts(output_dir: Path) -> dict[str, object]:
    """Fail closed unless every manifest entry and terminal binding agrees."""

    output = Path(output_dir)
    manifest_path = output / "SHA256SUMS"
    if not output.is_dir() or not manifest_path.is_file() or manifest_path.is_symlink():
        raise ProcessedBoostError("Task-7A artifact manifest is missing or unsafe")
    entries: dict[str, str] = {}
    for line in manifest_path.read_text(encoding="ascii").splitlines():
        parts = line.split("  ", 1)
        if len(parts) != 2 or re.fullmatch(r"[0-9a-f]{64}", parts[0]) is None:
            raise ProcessedBoostError("Task-7A artifact manifest is malformed")
        digest, name = parts
        if Path(name).name != name or name in entries:
            raise ProcessedBoostError("Task-7A artifact manifest path is unsafe")
        path = output / name
        if not path.is_file() or path.is_symlink() or _file_sha256(path) != digest:
            raise ProcessedBoostError("Task-7A artifact hash verification failed")
        entries[name] = digest
    required = {
        "terminal.json",
        "summary.json",
        "cases.csv",
        "fullsky_singular_spectrum.csv",
        "fullsky_resolution_convergence.csv",
        "finite_to_linear_scaling.csv",
        "gate_ratios.csv",
        "metric_spectrum_exact_vs_numerical.png",
        "fullsky_resolution_convergence.png",
        "finite_to_linear_scaling.png",
        "processed_channel_norms.png",
        "normalized_gate_margins.png",
    }
    if not required.issubset(entries):
        raise ProcessedBoostError("Task-7A artifact set is incomplete")
    terminal = json.loads((output / "terminal.json").read_text(encoding="ascii"))
    summary = json.loads((output / "summary.json").read_text(encoding="ascii"))
    if (
        terminal.get("schema") != _TERMINAL_SCHEMA
        or summary.get("schema") != _EVIDENCE_SCHEMA
        or terminal.get("terminal") != summary.get("terminal")
        or terminal.get("source_revision") != summary.get("source_revision")
        or terminal.get("profile") != summary.get("profile")
        or terminal.get("report_content_id") != summary.get("content_id")
        or terminal.get("claim_promotion") is not False
        or terminal.get("merge_authorized") is not False
    ):
        raise ProcessedBoostError("Task-7A terminal and summary binding differs")
    return {
        "schema": _ARTIFACT_SCHEMA,
        "terminal": terminal["terminal"],
        "source_revision": terminal["source_revision"],
        "profile": terminal["profile"],
        "report_content_id": terminal["report_content_id"],
        "manifest_entries": len(entries),
        "manifest_sha256": _file_sha256(manifest_path),
    }


__all__ = [
    "Task7AArtifactBundle",
    "Task7ACase",
    "Task7AEvidence",
    "Task7ATerminal",
    "build_task7a_evidence",
    "full_sky_expected_singular_values",
    "verify_task7a_artifacts",
    "write_task7a_artifacts",
]
