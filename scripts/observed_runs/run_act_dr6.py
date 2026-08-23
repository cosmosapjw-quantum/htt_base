#!/usr/bin/env python3
"""ACT DR6 validated-band worker and observation-free profile harness.

The attended mode consumes one exact PR-289 ACT admission only after the
transaction executor has written ``start.json``.  Synthetic profiling never
accepts an admission or data root and never opens the observed product.
"""

from __future__ import annotations

import os

THREAD_CONTROLS = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
for _name, _value in THREAD_CONTROLS.items():
    os.environ[_name] = _value

import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import json
import math
import multiprocessing
from pathlib import Path, PurePosixPath
import resource
import sys
import tempfile
import time
from typing import Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT / "htt", ROOT / "htt/src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from common.data_identity import (  # noqa: E402
    AdmissionStatus,
    DataIdentityError,
    _regular_beneath,
    _stream_sha256,
    load_lane_registry,
    replay_lane_admission_decision,
)
from obsstat.act_inband_modulation import (  # noqa: E402
    ActInbandModulationError,
    build_mask_design,
    extract_alm_features,
    observation_inclusive_loo_scores,
    pooled_upper_rank,
)


EXPECTED_SUPPORT = {
    "inequality": "40 < L < 763",
    "integer_min": 41,
    "integer_max": 762,
    "integer_count": 722,
    "endpoints_40_and_763_included": False,
    "coordinate_frame": "Equatorial",
}
FEATURE_ORDER = ("Y20", "Y21c", "Y21s", "Y22c", "Y22s")
EXACT_SIMULATION_COUNT = 400
PROFILE_ROWS = {"1": 1, "8": 8, "32": 32, "128": 128, "full": 400}
PROFILE_MODES = ("serial", "thread", "process")
REQUIRED_COMPONENTS = frozenset(
    {"product", "response", "mean_field", "noise", "mask", "simulation", "covariance"}
)
REGISTRY = ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
CHI2_5_95 = 11.070497693516351
COVERAGE_NOMINAL = 0.95
COVERAGE_Z_95 = 1.959963984540054
MINIMUM_RESPONSE_SINGULAR_VALUE_RATIO = 1.0e-8


class ActWorkerError(RuntimeError):
    """Raised when the frozen ACT worker contract fails closed."""


def _finite_matrix(
    value: Sequence[Sequence[float]] | np.ndarray,
    *,
    label: str,
    columns: int = 5,
) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[1] != columns or not np.all(np.isfinite(array)):
        raise ActWorkerError(f"{label} must be a finite matrix with {columns} columns")
    return array


def _finite_vector(value: Sequence[float] | np.ndarray, *, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (5,) or not np.all(np.isfinite(array)):
        raise ActWorkerError(f"{label} must be one finite five-vector")
    return array


def _cross_fit_mean_field(
    observed: Sequence[float] | np.ndarray,
    nulls: Sequence[Sequence[float]] | np.ndarray,
    *,
    exact_count: int = EXACT_SIMULATION_COUNT,
) -> tuple[np.ndarray, np.ndarray]:
    """Subtract each unit's mean over the other 400 exchangeable units."""

    observed_row = np.asarray(observed, dtype=float)
    null_rows = np.asarray(nulls, dtype=float)
    if (
        observed_row.ndim != 1
        or null_rows.ndim != 2
        or null_rows.shape != (exact_count, observed_row.size)
        or observed_row.size == 0
        or exact_count < 2
        or not np.all(np.isfinite(observed_row))
        or not np.all(np.isfinite(null_rows))
    ):
        raise ActWorkerError(f"cross-fit mean field requires exactly {exact_count} null rows")
    combined = np.vstack([observed_row, null_rows])
    total = combined.sum(axis=0)
    corrected = combined - (total - combined) / exact_count
    return corrected[0], corrected[1:]


def _full_covariance(
    nulls: Sequence[Sequence[float]] | np.ndarray,
    *,
    maximum_condition_number: float = 1.0e8,
) -> dict[str, object]:
    rows = _finite_matrix(nulls, label="null features")
    if rows.shape[0] <= rows.shape[1] + 2:
        raise ActWorkerError("full covariance has insufficient null rows")
    covariance = np.cov(rows, rowvar=False, ddof=1)
    covariance = 0.5 * (covariance + covariance.T)
    eigenvalues = np.linalg.eigvalsh(covariance)
    condition = float(np.linalg.cond(covariance))
    rank = int(np.linalg.matrix_rank(covariance))
    if (
        not np.all(np.isfinite(covariance))
        or not np.all(np.isfinite(eigenvalues))
        or eigenvalues[0] <= 0.0
        or not math.isfinite(condition)
        or condition > maximum_condition_number
        or rank != rows.shape[1]
    ):
        raise ActWorkerError("full covariance is singular or ill-conditioned")
    return {
        "matrix": covariance.tolist(),
        "feature_order": list(FEATURE_ORDER),
        "null_rows": int(rows.shape[0]),
        "rank": rank,
        "minimum_eigenvalue": float(eigenvalues[0]),
        "condition_number": condition,
        "diagonalized": False,
        "status": "FULL_COVARIANCE_VALID",
    }


def _response_rank(
    response: Sequence[Sequence[float]] | np.ndarray,
    covariance: Sequence[Sequence[float]] | np.ndarray,
) -> dict[str, object]:
    matrix = _finite_matrix(response, label="response")
    covariance_matrix = _finite_matrix(covariance, label="covariance")
    if matrix.shape != (5, 5) or covariance_matrix.shape != (5, 5):
        raise ActWorkerError("response and covariance must both be five by five")
    try:
        whitened = np.linalg.solve(np.linalg.cholesky(covariance_matrix), matrix)
    except np.linalg.LinAlgError as exc:
        raise ActWorkerError("response covariance is not positive definite") from exc
    singular = np.linalg.svd(whitened, compute_uv=False)
    tolerance = float(max(whitened.shape) * np.finfo(float).eps * singular[0])
    rank = int(np.count_nonzero(singular > tolerance))
    ratio = float(singular[-1] / singular[0]) if singular[0] > 0.0 else 0.0
    if rank != 5:
        status = "RANK_DEFICIENT_ABSTAIN"
    elif ratio < MINIMUM_RESPONSE_SINGULAR_VALUE_RATIO:
        status = "WEAK_RESPONSE_ABSTAIN"
    else:
        status = "FINITE_RESPONSE_RANK"
    return {
        "rank": rank,
        "columns": 5,
        "singular_values": singular.tolist(),
        "minimum_to_maximum_singular_value_ratio": ratio,
        "minimum_required_singular_value_ratio": MINIMUM_RESPONSE_SINGULAR_VALUE_RATIO,
        "rank_tolerance": tolerance,
        "covariance_whitened": True,
        "status": status,
    }


def _injection_coverage(
    truth: Sequence[Sequence[float]] | np.ndarray,
    estimates: Sequence[Sequence[float]] | np.ndarray,
    *,
    response: Sequence[Sequence[float]] | np.ndarray,
    covariance: Sequence[Sequence[float]] | np.ndarray,
) -> dict[str, object]:
    truth_rows = _finite_matrix(truth, label="injection truth")
    estimate_rows = _finite_matrix(estimates, label="injection estimates")
    response_matrix = _finite_matrix(response, label="injection response")
    covariance_matrix = _finite_matrix(covariance, label="injection covariance")
    if (
        truth_rows.shape != estimate_rows.shape
        or truth_rows.shape[0] < 20
        or response_matrix.shape != (5, 5)
        or covariance_matrix.shape != (5, 5)
    ):
        raise ActWorkerError("injection coverage contract is malformed")
    residual = estimate_rows - truth_rows @ response_matrix.T
    try:
        solved = np.linalg.solve(covariance_matrix, residual.T).T
    except np.linalg.LinAlgError as exc:
        raise ActWorkerError("injection covariance is singular") from exc
    squared = np.einsum("ni,ni->n", residual, solved)
    hits = int(np.count_nonzero(squared <= CHI2_5_95))
    count = int(truth_rows.shape[0])
    fraction = float(hits / count)
    z2 = COVERAGE_Z_95 * COVERAGE_Z_95
    denominator = 1.0 + z2 / count
    center = (fraction + z2 / (2.0 * count)) / denominator
    half_width = (
        COVERAGE_Z_95
        * math.sqrt(fraction * (1.0 - fraction) / count + z2 / (4.0 * count * count))
        / denominator
    )
    interval = [max(0.0, center - half_width), min(1.0, center + half_width)]
    passed = interval[0] <= COVERAGE_NOMINAL <= interval[1]
    return {
        "injection_count": count,
        "dimension": 5,
        "coverage_probability": COVERAGE_NOMINAL,
        "coverage_confidence_level": 0.95,
        "chi_square_threshold": CHI2_5_95,
        "coverage_fraction": fraction,
        "acceptance_interval": interval,
        "interval_method": "WILSON_SCORE_TWO_SIDED",
        "full_covariance_used": True,
        "injection_stage": "PRE_QE_OR_END_TO_END_ONLY",
        "status": "INJECTION_COVERAGE_PASS" if passed else "INJECTION_COVERAGE_FAILED_ABSTAIN",
    }


def analyze_feature_ensemble(
    observed: Sequence[float] | np.ndarray,
    simulations: Sequence[Sequence[float]] | np.ndarray,
    *,
    response: Sequence[Sequence[float]] | np.ndarray,
    injection_truth: Sequence[Sequence[float]] | np.ndarray,
    injection_estimates: Sequence[Sequence[float]] | np.ndarray,
    emit_rank: bool = False,
    observed_execution: bool = False,
) -> dict[str, object]:
    if (
        type(emit_rank) is not bool
        or type(observed_execution) is not bool
        or emit_rank != observed_execution
    ):
        raise ActWorkerError("observed/rank state must be one exact boolean decision")
    observed_row = _finite_vector(observed, label="observed feature")
    simulation_rows = _finite_matrix(simulations, label="simulation features")
    if simulation_rows.shape != (EXACT_SIMULATION_COUNT, 5):
        raise ActWorkerError("analysis requires exactly 400 ordered release simulations")
    corrected_observed, corrected_nulls = _cross_fit_mean_field(
        observed_row, simulation_rows
    )
    covariance = _full_covariance(corrected_nulls)
    response_receipt = _response_rank(response, covariance["matrix"])
    coverage = _injection_coverage(
        injection_truth,
        injection_estimates,
        response=response,
        covariance=covariance["matrix"],
    )
    if response_receipt["status"] != "FINITE_RESPONSE_RANK":
        disposition = str(response_receipt["status"])
    elif coverage["status"] != "INJECTION_COVERAGE_PASS":
        disposition = "INJECTION_COVERAGE_FAILED_ABSTAIN"
    else:
        disposition = (
            "ACT_VALIDATED_BAND_DIAGNOSTIC_COMPLETE"
            if observed_execution
            else "SYNTHETIC_OPERATOR_CLOSURE_PASS"
        )
    rank_receipt: dict[str, object] | None = None
    p_value: float | None = None
    if emit_rank and disposition == "ACT_VALIDATED_BAND_DIAGNOSTIC_COMPLETE":
        scores = observation_inclusive_loo_scores(
            np.vstack([corrected_observed, corrected_nulls])
        )["scores"]
        rank_receipt = pooled_upper_rank(scores)
        p_value = float(rank_receipt["rank"])
    return {
        "capability": "ACT_DR6_VALIDATED_BAND_OPERATOR_AND_400_SIM_CLOSURE",
        "analysis_support": EXPECTED_SUPPORT,
        "feature_order": list(FEATURE_ORDER),
        "operator_identity": "IDENTICAL_RELEASE_KAPPA_MASK_STRICT_BAND_FEATURE_OPERATOR",
        "mean_field": {
            "method": "OBSERVATION_INCLUSIVE_401_UNIT_LEAVE_ONE_OUT_FEATURE_SPACE",
            "observed_reference_rows": 400,
            "null_reference_rows": 400,
            "permutation_equivariant": True,
        },
        "simulation_count": EXACT_SIMULATION_COUNT,
        "covariance": covariance,
        "response_rank": response_receipt,
        "injection_coverage": coverage,
        "release_simulation_rank": rank_receipt,
        "p_value": p_value,
        "scientific_result": None,
        "terminal_disposition": disposition,
        "global_claim_boundary": "NO_GLOBAL_RESPONSE_NO_GLOBAL_CLAIM",
        "observed_statistic_seen": bool(observed_execution),
        "observed_science_executed": bool(observed_execution),
    }


def _validate_sha256(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ActWorkerError(f"{label} is not text")
    text = value
    if text.startswith("sha256:"):
        text = text[7:]
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ActWorkerError(f"{label} is not SHA-256")
    return "sha256:" + text


def _relative_path(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ActWorkerError(f"{label} is not a relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ActWorkerError(f"{label} is not a safe relative path")
    return path.as_posix()


def _validate_simulation_inventory(payload: Mapping[str, object]) -> list[dict[str, object]]:
    if set(payload) != {"release_id", "variant", "ordered_simulations"}:
        raise ActWorkerError("simulation inventory fields drifted")
    rows = payload["ordered_simulations"]
    if (
        payload["release_id"] != "ACT_DR6_LENSING_V1"
        or payload["variant"] != "baseline"
        or not isinstance(rows, list)
        or len(rows) != EXACT_SIMULATION_COUNT
    ):
        raise ActWorkerError("simulation inventory must be exact ACT DR6 baseline 400")
    result: list[dict[str, object]] = []
    for index, raw in enumerate(rows, 1):
        if not isinstance(raw, Mapping) or set(raw) != {
            "simulation_id",
            "relative_path",
            "byte_size",
            "content_sha256",
        }:
            raise ActWorkerError("simulation inventory row fields drifted")
        size = raw["byte_size"]
        row = {
            "simulation_id": raw["simulation_id"],
            "relative_path": _relative_path(raw["relative_path"], label="simulation path"),
            "byte_size": size,
            "content_sha256": _validate_sha256(raw["content_sha256"], label="simulation hash"),
        }
        if row["simulation_id"] != f"{index:04d}" or type(size) is not int or size <= 0:
            raise ActWorkerError("simulation inventory order or size drifted")
        result.append(row)
    if len({row["relative_path"] for row in result}) != EXACT_SIMULATION_COUNT:
        raise ActWorkerError("simulation inventory paths are not unique")
    return result


def _synthetic_row(index: int) -> list[float]:
    rng = np.random.default_rng(30_800_000 + index)
    base = rng.normal(size=5)
    base[1] += 0.35 * base[0]
    base[3] += 0.20 * base[2]
    return base.tolist()


def _max_rss_bytes() -> int:
    values = [resource.getrusage(resource.RUSAGE_SELF).ru_maxrss]
    try:
        values.append(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    except (AttributeError, ValueError):
        pass
    maximum = int(max(values))
    return maximum if sys.platform == "darwin" else maximum * 1024


def synthetic_profile(*, rows: str, mode: str, workers: int) -> dict[str, object]:
    if rows not in PROFILE_ROWS or mode not in PROFILE_MODES or type(workers) is not int or workers < 1:
        raise ActWorkerError("synthetic profile selection is invalid")
    count = PROFILE_ROWS[rows]
    started = time.perf_counter()
    ordinals = list(range(count))
    if mode == "serial":
        generated = [_synthetic_row(index) for index in ordinals]
    elif mode == "thread":
        with ThreadPoolExecutor(max_workers=workers) as pool:
            generated = list(pool.map(_synthetic_row, ordinals))
    else:
        context = multiprocessing.get_context("fork")
        with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
            generated = list(pool.map(_synthetic_row, ordinals))
    feature_seconds = time.perf_counter() - started
    closure_started = time.perf_counter()
    closure = "PROFILE_ONLY_INCOMPLETE_ENSEMBLE_NO_RANK_OR_P_VALUE"
    if count == EXACT_SIMULATION_COUNT:
        simulations = np.asarray(generated)
        rng = np.random.default_rng(30_800_401)
        covariance = np.cov(simulations, rowvar=False, ddof=1)
        truth = rng.normal(scale=0.08, size=(100, 5))
        estimates = truth + rng.multivariate_normal(np.zeros(5), covariance, size=100)
        report = analyze_feature_ensemble(
            rng.normal(size=5),
            simulations,
            response=np.eye(5),
            injection_truth=truth,
            injection_estimates=estimates,
        )
        closure = str(report["terminal_disposition"])
    closure_seconds = time.perf_counter() - closure_started
    return {
        "capability": "ACT_DR6_VALIDATED_BAND_OPERATOR_AND_400_SIM_CLOSURE",
        "profile_kind": "SYNTHETIC_FEATURE_OPERATOR_ONLY",
        "row_label": rows,
        "row_count": count,
        "mode": mode,
        "workers": workers,
        "thread_controls": THREAD_CONTROLS,
        "analysis_support": EXPECTED_SUPPORT,
        "closure_status": closure,
        "stage_seconds": {
            "synthetic_features": feature_seconds,
            "covariance_rank_coverage": closure_seconds,
        },
        "wall_seconds": feature_seconds + closure_seconds,
        "max_rss_bytes": _max_rss_bytes(),
        "observed_statistic_seen": False,
        "observed_science_executed": False,
    }


def _strict_json(path: Path, *, label: str) -> Mapping[str, object]:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ActWorkerError(f"{label} contains duplicate key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> object:
        raise ActWorkerError(f"{label} contains non-finite JSON constant {value}")

    try:
        payload = json.loads(
            path.read_bytes(), object_pairs_hook=unique, parse_constant=reject_constant
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ActWorkerError(f"{label} is not strict JSON") from exc
    if not isinstance(payload, Mapping):
        raise ActWorkerError(f"{label} must be a JSON object")
    return payload


def _load_admission(path: Path):
    try:
        registry = load_lane_registry(REGISTRY)
        decision = replay_lane_admission_decision(
            _strict_json(path, label="ACT admission"),
            registry=registry,
        )
    except (DataIdentityError, ActWorkerError) as exc:
        raise ActWorkerError(f"ACT admission replay failed: {exc}") from exc
    if (
        decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
        or decision.lane_id != "ACT"
        or tuple(record.component_id for record in decision.records)
        != tuple(registry.lane("ACT").expected_component_sequence)
        or decision.lane_admission_bundle_id is None
    ):
        raise ActWorkerError("ACT admission is not complete identity admission")
    return decision


def _mark_observed_data_open_attempt() -> None:
    output_text = os.environ.get("HTT_ATTENDED_OUTPUT_DIR", "")
    output = Path(output_text)
    marker = output / "observed_data_opened.json"
    if (
        os.environ.get("HTT_ATTENDED_START_WRITTEN") != "1"
        or not output_text
        or not output.is_absolute()
        or output.is_symlink()
        or not output.is_dir()
        or not (output / "start.json").is_file()
        or os.environ.get("HTT_ATTENDED_DATA_OPEN_MARKER") != str(marker)
        or marker.exists()
        or marker.is_symlink()
    ):
        raise ActWorkerError("attended output/start/data-open binding is invalid")
    _write_json(marker, {"state": "OBSERVED_DATA_OPEN_ATTEMPTED"})


def _admitted_paths(decision, *, data_root: Path) -> dict[str, Path]:
    if (
        not data_root.is_absolute()
        or data_root.is_symlink()
        or not data_root.is_dir()
        or data_root.resolve() != data_root
    ):
        raise ActWorkerError("data root must be an absolute regular directory")
    bindings = decision.records[0].native_identity_profile.get("component_bindings")
    if not isinstance(bindings, Sequence) or len(bindings) != len(REQUIRED_COMPONENTS):
        raise ActWorkerError("ACT native component bindings drifted")
    records = {record.component_id: record for record in decision.records}
    if set(records) != REQUIRED_COMPONENTS:
        raise ActWorkerError("ACT admitted component inventory is incomplete")
    result: dict[str, Path] = {}
    for binding in bindings:
        if not isinstance(binding, Mapping):
            raise ActWorkerError("ACT component binding is malformed")
        component = binding.get("component_id")
        relative = binding.get("relative_path")
        if component not in records or not isinstance(relative, str):
            raise ActWorkerError("ACT component binding identity drifted")
        try:
            path, info = _regular_beneath(data_root, Path(relative), f"ACT {component}")
            digest = "sha256:" + _stream_sha256(
                path, field_name=f"ACT {component}", expected_info=info
            )
        except DataIdentityError as exc:
            raise ActWorkerError(f"ACT {component} is not an exact admitted file") from exc
        record = records[str(component)]
        if info.st_size != record.byte_size or digest != record.content_sha256:
            raise ActWorkerError(f"ACT {component} no longer matches admission")
        result[str(component)] = path
    return result


def _release_contracts(paths: Mapping[str, Path]) -> tuple[Mapping[str, object], list[dict[str, object]]]:
    response = _strict_json(paths["response"], label="ACT response")
    mean_field = _strict_json(paths["mean_field"], label="ACT mean field")
    noise = _strict_json(paths["noise"], label="ACT noise")
    covariance = _strict_json(paths["covariance"], label="ACT covariance")
    inventory = _validate_simulation_inventory(
        _strict_json(paths["simulation"], label="ACT simulation inventory")
    )
    required_response = {
        "release_id",
        "variant",
        "analysis_support",
        "feature_order",
        "injection_stage",
        "minimum_response_singular_value_ratio",
        "response_matrix",
        "injection_truth",
        "injection_estimates",
    }
    if (
        set(response) != required_response
        or response["release_id"] != "ACT_DR6_LENSING_V1"
        or response["variant"] != "baseline"
        or response["analysis_support"] != EXPECTED_SUPPORT
        or response["feature_order"] != list(FEATURE_ORDER)
        or response["minimum_response_singular_value_ratio"]
        != MINIMUM_RESPONSE_SINGULAR_VALUE_RATIO
        or response["injection_stage"]
        not in {"PRE_QE_END_TO_END", "END_TO_END_RELEASE_RECONSTRUCTION"}
    ):
        raise ActWorkerError("ACT response/support/injection contract drifted")
    if dict(mean_field) != {
        "method": "OBSERVATION_INCLUSIVE_401_UNIT_LEAVE_ONE_OUT_FEATURE_SPACE",
        "ordered_simulation_count": 400,
        "total_exchangeable_units": 401,
        "per_unit_reference_rows": 400,
    }:
        raise ActWorkerError("ACT cross-fit mean-field contract drifted")
    if dict(noise) != {
        "forecast_noise_curve_used": False,
        "role": "RELEASE_RECONSTRUCTION_SIMULATION_ENSEMBLE",
    }:
        raise ActWorkerError("ACT noise contract drifted")
    if dict(covariance) != {
        "adaptive_regularization": False,
        "diagonalized": False,
        "dimension": 5,
        "maximum_condition_number": 100000000.0,
        "method": "FULL_EMPIRICAL_CROSS_FIT_FEATURE_COVARIANCE",
        "ordered_simulation_count": 400,
    }:
        raise ActWorkerError("ACT full-covariance contract drifted")
    return response, inventory


def _nested_simulation_paths(
    rows: Sequence[Mapping[str, object]], *, data_root: Path
) -> list[Path]:
    result: list[Path] = []
    for row in rows:
        try:
            path, info = _regular_beneath(
                data_root,
                Path(str(row["relative_path"])),
                f"ACT simulation {row['simulation_id']}",
            )
            digest = "sha256:" + _stream_sha256(
                path,
                field_name=f"ACT simulation {row['simulation_id']}",
                expected_info=info,
            )
        except DataIdentityError as exc:
            raise ActWorkerError("ACT nested simulation identity failed") from exc
        if info.st_size != row["byte_size"] or digest != row["content_sha256"]:
            raise ActWorkerError("ACT nested simulation no longer matches inventory")
        result.append(path)
    return result


def _mask_design(path: Path):
    try:
        import healpy as hp

        mask = np.asarray(hp.read_map(path, field=0, dtype=float, verbose=False))
        source_nside = int(hp.get_nside(mask))
        if source_nside != 1024:
            mask = hp.ud_grade(
                mask,
                nside_out=1024,
                order_in="RING",
                order_out="RING",
                power=0,
            )
        return build_mask_design(mask, nside=1024, threshold=0.99)
    except (OSError, ValueError, ActInbandModulationError) as exc:
        raise ActWorkerError("ACT release mask cannot build the frozen design") from exc


def _extract_feature(path: Path, design) -> np.ndarray:
    try:
        import healpy as hp

        alm = hp.read_alm(path)
        feature = extract_alm_features(
            alm,
            design,
            integer_min=EXPECTED_SUPPORT["integer_min"],
            integer_max=EXPECTED_SUPPORT["integer_max"],
        )
    except (OSError, ValueError, ActInbandModulationError) as exc:
        raise ActWorkerError("ACT reconstructed-kappa feature extraction failed") from exc
    return _finite_vector(feature["q_controlled"], label="ACT controlled feature")


def _run_admitted(*, admission_path: Path, data_root: Path) -> dict[str, object]:
    decision = _load_admission(admission_path)
    _mark_observed_data_open_attempt()
    paths = _admitted_paths(decision, data_root=data_root)
    response, inventory = _release_contracts(paths)
    simulations = _nested_simulation_paths(inventory, data_root=data_root)
    design = _mask_design(paths["mask"])
    observed_feature = _extract_feature(paths["product"], design)
    simulation_features = np.asarray(
        [_extract_feature(path, design) for path in simulations], dtype=float
    )
    result = analyze_feature_ensemble(
        observed_feature,
        simulation_features,
        response=response["response_matrix"],
        injection_truth=response["injection_truth"],
        injection_estimates=response["injection_estimates"],
        emit_rank=True,
        observed_execution=True,
    )
    result.update(
        admission_bundle_id=decision.lane_admission_bundle_id,
        ordered_record_ids=[record.record_id for record in decision.records],
        owner="OBSSTAT",
        claim_tier="diagnostic_only",
        transfer_source="none",
        public_use=False,
        source_release="ACT DR6 lensing v1 baseline",
        source_url="https://lambda.gsfc.nasa.gov/product/act/actadv_dr6_lensing_maps_info.html",
        forbidden_uses=[
            "L below 41 interpretation",
            "raw-QE or pre-QE injection claim without end-to-end evidence",
            "cosmological source attribution",
            "Bianchi family identification",
        ],
    )
    return result


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="ascii") as handle:
            json.dump(payload, handle, sort_keys=True, separators=(",", ":"), allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic-profile", action="store_true")
    mode.add_argument("--run-admitted", action="store_true")
    parser.add_argument("--rows", choices=tuple(PROFILE_ROWS), default="full")
    parser.add_argument("--mode", choices=PROFILE_MODES, default="serial")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.synthetic_profile:
            if args.admission is not None or args.data_root is not None:
                raise ActWorkerError("synthetic profile forbids admission and data root")
            payload = synthetic_profile(rows=args.rows, mode=args.mode, workers=args.workers)
        else:
            if args.admission is None or args.data_root is None:
                raise ActWorkerError("admitted run requires admission and data root")
            payload = _run_admitted(
                admission_path=args.admission,
                data_root=args.data_root,
            )
        _write_json(args.output, payload)
        return 0
    except (ActWorkerError, OSError, ValueError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
