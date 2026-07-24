"""PR-204 strict-band post-reconstruction injection calibration.

This module calibrates the PR-177 observable extractor only.  Its injections
start from released reconstructed-kappa alms; they are not pre-QE injections,
raw-QE reproduction, transfer validation, or cosmological inference.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from obsstat.act_inband_modulation import (
    ActInbandModulationError,
    MaskDesign,
    fractional_variance_features,
    strict_band_alm,
)

AXIS_NAMES = ("Y20", "Y21c", "Y21s", "Y22c", "Y22s")
AMPLITUDE_MAGNITUDE = 0.08
INTEGER_MIN = 41
INTEGER_MAX = 762


@dataclass(frozen=True)
class InjectionAssignment:
    simulation_id: int
    axis_index: int
    axis_name: str
    within_axis_index: int
    amplitude: float
    split: str


def injection_assignment(simulation_id: int) -> InjectionAssignment:
    """Return the frozen balanced axis/sign/split assignment."""

    if isinstance(simulation_id, bool) or not isinstance(simulation_id, int):
        raise ActInbandModulationError("simulation_id must be an integer")
    if not 1 <= simulation_id <= 400:
        raise ActInbandModulationError("simulation_id must lie in 1..400")
    zero_based = simulation_id - 1
    axis_index = zero_based % len(AXIS_NAMES)
    within_axis = zero_based // len(AXIS_NAMES)
    sign = 1.0 if within_axis % 2 == 0 else -1.0
    if within_axis < 20:
        split = "response_fit"
    elif within_axis < 40:
        split = "coverage_calibration"
    else:
        split = "evaluation"
    return InjectionAssignment(
        simulation_id=simulation_id,
        axis_index=axis_index,
        axis_name=AXIS_NAMES[axis_index],
        within_axis_index=within_axis,
        amplitude=sign * AMPLITUDE_MAGNITUDE,
        split=split,
    )


def full_sky_real_y2_templates(nside: int) -> np.ndarray:
    """Return the five physical real-Y2 basis maps in the PR-177 order."""

    import healpy as hp

    if isinstance(nside, bool) or not isinstance(nside, int) or nside < 1:
        raise ActInbandModulationError("nside must be a positive integer")
    pixels = np.arange(hp.nside2npix(nside), dtype=np.int64)
    x, y, z = hp.pix2vec(nside, pixels, nest=False)
    templates = np.empty((5, pixels.size), dtype=np.float32)
    templates[0] = math.sqrt(5.0 / (16.0 * math.pi)) * (3.0 * z * z - 1.0)
    templates[1] = math.sqrt(15.0 / (4.0 * math.pi)) * x * z
    templates[2] = math.sqrt(15.0 / (4.0 * math.pi)) * y * z
    templates[3] = math.sqrt(15.0 / (16.0 * math.pi)) * (x * x - y * y)
    templates[4] = math.sqrt(15.0 / (4.0 * math.pi)) * x * y
    if not np.all(np.isfinite(templates)):
        raise ActInbandModulationError("real-Y2 templates are non-finite")
    return templates


def injected_unit_features(
    full_alm: Sequence[complex],
    design: MaskDesign,
    template: Sequence[float],
    amplitude: float,
    *,
    map2alm_iterations: int = 0,
) -> dict[str, object]:
    """Extract paired baseline/injected features with a hard band reprojection."""

    import healpy as hp

    if not np.isfinite(amplitude) or abs(amplitude) != AMPLITUDE_MAGNITUDE:
        raise ActInbandModulationError("amplitude must equal the frozen signed magnitude")
    template_map = np.asarray(template, dtype=np.float64)
    expected_pixels = hp.nside2npix(design.nside)
    if template_map.shape != (expected_pixels,) or not np.all(
        np.isfinite(template_map)
    ):
        raise ActInbandModulationError("template map is malformed")
    compact = strict_band_alm(
        full_alm,
        integer_min=INTEGER_MIN,
        integer_max=INTEGER_MAX,
    )
    baseline_map = hp.alm2map(
        compact,
        nside=design.nside,
        lmax=INTEGER_MAX,
        mmax=INTEGER_MAX,
        pol=False,
    )
    baseline = fractional_variance_features(baseline_map, design)
    variance_factor = 1.0 + amplitude * template_map
    minimum_factor = float(np.min(variance_factor))
    if minimum_factor <= 0.0:
        raise ActInbandModulationError("variance-modulation factor is not positive")
    modulated_map = baseline_map * np.sqrt(variance_factor)
    modulated_alm = hp.map2alm(
        modulated_map,
        lmax=INTEGER_MAX,
        mmax=INTEGER_MAX,
        iter=map2alm_iterations,
        pol=False,
        use_pixel_weights=False,
    )
    reprojected_alm = strict_band_alm(
        modulated_alm,
        integer_min=INTEGER_MIN,
        integer_max=INTEGER_MAX,
    )
    reprojected_map = hp.alm2map(
        reprojected_alm,
        nside=design.nside,
        lmax=INTEGER_MAX,
        mmax=INTEGER_MAX,
        pol=False,
    )
    injected = fractional_variance_features(reprojected_map, design)
    return {
        "baseline": baseline,
        "injected": injected,
        "minimum_variance_factor": minimum_factor,
        "hard_reprojected_integer_support": [INTEGER_MIN, INTEGER_MAX],
        "map2alm_iterations": map2alm_iterations,
        "pixel_weights": False,
    }


def _matrix(records: Sequence[Mapping[str, object]], feature: str) -> np.ndarray:
    rows = []
    for record in records:
        baseline = np.asarray(record["baseline"][feature], dtype=float)
        injected = np.asarray(record["injected"][feature], dtype=float)
        if baseline.shape != (5,) or injected.shape != (5,):
            raise ActInbandModulationError("injection feature vector is malformed")
        rows.append(injected - baseline)
    values = np.asarray(rows, dtype=float)
    if values.shape != (400, 5) or not np.all(np.isfinite(values)):
        raise ActInbandModulationError("exactly 400 finite injection deltas required")
    return values


def _response_matrix(
    deltas: np.ndarray,
    assignments: Sequence[InjectionAssignment],
) -> np.ndarray:
    response = np.empty((5, 5), dtype=float)
    for axis in range(5):
        selected = np.asarray(
            [
                row.axis_index == axis and row.split == "response_fit"
                for row in assignments
            ],
            dtype=bool,
        )
        amplitudes = np.asarray(
            [row.amplitude for row in assignments], dtype=float
        )[selected]
        if selected.sum() != 20 or np.count_nonzero(amplitudes > 0) != 10:
            raise ActInbandModulationError("response-fit assignment is unbalanced")
        response[:, axis] = (
            amplitudes @ deltas[selected]
        ) / float(amplitudes @ amplitudes)
    return response


def _amplitude_recovery(
    deltas: np.ndarray,
    assignments: Sequence[InjectionAssignment],
    response: np.ndarray,
) -> dict[str, object]:
    recovered = np.empty(400, dtype=float)
    amplitudes = np.asarray([row.amplitude for row in assignments], dtype=float)
    for index, assignment in enumerate(assignments):
        column = response[:, assignment.axis_index]
        norm2 = float(column @ column)
        if not np.isfinite(norm2) or norm2 <= 0.0:
            raise ActInbandModulationError("response column has zero norm")
        recovered[index] = float(column @ deltas[index] / norm2)
    errors = recovered - amplitudes
    per_axis = []
    for axis in range(5):
        calibration = np.asarray(
            [
                row.axis_index == axis and row.split == "coverage_calibration"
                for row in assignments
            ],
            dtype=bool,
        )
        evaluation = np.asarray(
            [
                row.axis_index == axis and row.split == "evaluation"
                for row in assignments
            ],
            dtype=bool,
        )
        calibration_scores = np.sort(np.abs(errors[calibration]))
        if calibration_scores.size != 20 or evaluation.sum() != 40:
            raise ActInbandModulationError("coverage split is incomplete")
        threshold = float(calibration_scores[18])
        evaluation_errors = errors[evaluation]
        coverage_count = int(np.count_nonzero(np.abs(evaluation_errors) <= threshold))
        per_axis.append(
            {
                "axis": AXIS_NAMES[axis],
                "coverage_calibration_count": 20,
                "evaluation_count": 40,
                "absolute_error_threshold": threshold,
                "evaluation_coverage_count": coverage_count,
                "evaluation_coverage": float(coverage_count / 40),
                "evaluation_bias": float(np.mean(evaluation_errors)),
                "evaluation_rmse": float(
                    np.sqrt(np.mean(evaluation_errors * evaluation_errors))
                ),
            }
        )
    return {
        "recovered_amplitudes": [float(value) for value in recovered],
        "per_axis": per_axis,
    }


def analyze_injection_records(
    records: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Compute frozen response, split-coverage, and mask-sensitivity gates."""

    if len(records) != 400:
        raise ActInbandModulationError("exactly 400 injection records required")
    assignments = [injection_assignment(index) for index in range(1, 401)]
    for record, assignment in zip(records, assignments, strict=True):
        if int(record.get("simulation_id", -1)) != assignment.simulation_id:
            raise ActInbandModulationError("injection record order drift")
        if record.get("assignment") != {
            "axis_index": assignment.axis_index,
            "axis_name": assignment.axis_name,
            "within_axis_index": assignment.within_axis_index,
            "amplitude": assignment.amplitude,
            "split": assignment.split,
        }:
            raise ActInbandModulationError("injection assignment drift")
    controlled = _matrix(records, "q_controlled")
    raw = _matrix(records, "q_raw")
    controlled_response = _response_matrix(controlled, assignments)
    raw_response = _response_matrix(raw, assignments)
    recovery = _amplitude_recovery(controlled, assignments, controlled_response)

    diagonal = np.diag(controlled_response)
    off_diagonal = controlled_response.copy()
    np.fill_diagonal(off_diagonal, 0.0)
    response_condition = float(np.linalg.cond(controlled_response))
    response_pass = bool(
        np.all((diagonal >= 0.8) & (diagonal <= 1.2))
        and np.max(np.abs(off_diagonal)) <= 0.2
        and response_condition <= 2.0
    )
    coverage_pass = all(
        row["evaluation_coverage"] >= 0.9
        and abs(row["evaluation_bias"]) <= 0.01
        for row in recovery["per_axis"]
    )

    mask_ratios = []
    for index, assignment in enumerate(assignments):
        if assignment.split != "evaluation":
            continue
        signal_norm = float(np.linalg.norm(controlled[index]))
        if signal_norm <= 0.0:
            raise ActInbandModulationError("controlled injection delta has zero norm")
        mask_ratios.append(float(np.linalg.norm(raw[index] - controlled[index]) / signal_norm))
    mask_p95 = float(np.quantile(mask_ratios, 0.95, method="higher"))
    mask_pass = mask_p95 <= 0.5
    return {
        "controlled_response_matrix": controlled_response.tolist(),
        "raw_response_matrix": raw_response.tolist(),
        "controlled_response_diagonal": diagonal.tolist(),
        "controlled_maximum_absolute_off_diagonal": float(
            np.max(np.abs(off_diagonal))
        ),
        "controlled_response_condition_number": response_condition,
        "response_gate_passed": response_pass,
        "split_coverage": recovery["per_axis"],
        "coverage_gate_passed": coverage_pass,
        "evaluation_mask_sensitivity_ratio_p95": mask_p95,
        "mask_sensitivity_gate_passed": mask_pass,
        "raw_qe_reproduction": False,
        "injection_stage": "post_reconstruction_strict_band_hard_reprojected",
    }


def terminal_from_analysis(analysis: Mapping[str, object]) -> str:
    if not analysis.get("response_gate_passed"):
        return "BLOCKED_INBAND_INJECTION_RESPONSE_FAILURE"
    if not analysis.get("coverage_gate_passed"):
        return "BLOCKED_INBAND_INJECTION_COVERAGE_FAILURE"
    if not analysis.get("mask_sensitivity_gate_passed"):
        return "BLOCKED_MASK_SENSITIVITY_COMPARABLE_TO_INJECTION"
    return "AUTHOR_EVIDENCE_READY_VALIDATED_BAND_RESPONSE_CALIBRATED"
