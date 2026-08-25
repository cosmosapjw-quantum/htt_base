"""PR-153 published-table JWST distance-method consistency measurements.

The primary input is a source-checked transcription of two author-supplied
arXiv LaTeX host tables.  A second input records two source-reported aggregate
comparisons that expand the sample coverage.  Aggregate rows are replayed as
published and are never promoted to host-level reanalyses or pooled across
overlapping samples.  This module does not fit H0, infer cosmology, or use the
distances to identify a preferred sky geometry.

The primary uncertainty is the between-host standard error and Student-t
interval.  A fixed-effect inverse-variance estimate is supplied as a labelled
sensitivity because the compact source tables do not provide their shared
NGC 4258 anchor covariance.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np
from scipy.stats import binomtest, chi2, norm, t

SCHEMA_VERSION = "pr153.jwst_distance_consistency.v3"

_AGGREGATE_CONTRACTS = {
    "li2024_jwst_trgb_hst_cepheid": {
        "source_arxiv": "2408.00065", "parent_count": 10,
        "parent_count_unit": "SN", "paired_count": 8,
        "paired_count_unit": "host", "method_a": "JWST_TRGB",
        "method_b": "HST_Cepheid",
    },
    "li2025_complete_trgb_hst_cepheid": {
        "source_arxiv": "2504.08921", "parent_count": 35,
        "parent_count_unit": "SN", "paired_count": 20,
        "paired_count_unit": "object", "method_a": "HST_plus_JWST_TRGB",
        "method_b": "HST_Cepheid",
    },
}


class JWSTDistanceError(ValueError):
    """Raised when a source table or inference contract is violated."""


def _finite(rows: list[dict], key: str) -> np.ndarray:
    values = np.asarray([float(row[key]) for row in rows], dtype=float)
    if values.ndim != 1 or values.size < 3 or not np.all(np.isfinite(values)):
        raise JWSTDistanceError(f"{key} must contain at least three finite values")
    return values


def paired_consistency(rows: list[dict], *, dataset: str,
                       comparison_value_mag: float | None = None) -> dict:
    """Return transparent paired host-level consistency statistics.

    ``delta = method_a - method_b``.  Hosts are the independent sampling unit
    for the primary Student-t result.  The inverse-variance result treats the
    tabulated method errors as independent and is therefore sensitivity-only.
    """
    selected = [row for row in rows if str(row["dataset"]) == dataset]
    if not selected:
        raise JWSTDistanceError(f"no rows for dataset {dataset}")
    hosts = [str(row["host"]) for row in selected]
    if len(hosts) != len(set(hosts)):
        raise JWSTDistanceError(f"duplicate host in {dataset}")
    a = _finite(selected, "mu_a_mag")
    b = _finite(selected, "mu_b_mag")
    sa = _finite(selected, "sigma_a_mag")
    sb = _finite(selected, "sigma_b_mag")
    if np.any(sa <= 0) or np.any(sb <= 0):
        raise JWSTDistanceError("tabulated uncertainties must be positive")
    delta = a - b
    n = int(delta.size)
    mean = float(np.mean(delta))
    sd = float(np.std(delta, ddof=1))
    sem = sd / math.sqrt(n)
    df = n - 1
    q = float(t.ppf(0.975, df))
    t_zero = mean / sem

    # Fixed-effect sensitivity.  The table does not expose the shared-anchor
    # covariance, so this is never promoted to the primary uncertainty.
    var_independent = sa ** 2 + sb ** 2
    weights = 1.0 / var_independent
    weighted_mean = float(np.sum(weights * delta) / np.sum(weights))
    weighted_se = float(1.0 / math.sqrt(np.sum(weights)))
    cochran_q = float(np.sum(weights * (delta - weighted_mean) ** 2))

    negative = int(np.sum(delta < 0.0))
    positive = int(np.sum(delta > 0.0))
    sign_n = negative + positive
    sign_p = (float(binomtest(min(negative, positive), sign_n, 0.5,
                              alternative="two-sided").pvalue)
              if sign_n else 1.0)

    loo = [float(np.mean(np.delete(delta, i))) for i in range(n)]
    result = {
        "dataset": dataset,
        "n_unique_hosts": n,
        "method_a": str(selected[0]["method_a"]),
        "method_b": str(selected[0]["method_b"]),
        "delta_definition": "method_a_minus_method_b_mag",
        "host_deltas_mag": [
            {"host": host, "delta_mag": float(value),
             "sigma_independence_approximation_mag": float(math.sqrt(var))}
            for host, value, var in zip(hosts, delta, var_independent)
        ],
        "primary_host_level": {
            "mean_delta_mag": mean,
            "sample_sd_mag": sd,
            "standard_error_mag": sem,
            "student_t_95pct_interval_mag": [mean - q * sem, mean + q * sem],
            "two_sided_p_for_zero_mean": float(2.0 * t.sf(abs(t_zero), df)),
            "t_statistic_for_zero_mean": float(t_zero),
            "degrees_of_freedom": df,
            "rms_delta_mag": float(math.sqrt(np.mean(delta ** 2))),
            "mean_fractional_distance_offset": float(10.0 ** (mean / 5.0) - 1.0),
            "leave_one_host_mean_range_mag": [min(loo), max(loo)],
            "sampling_assumption": "host_deltas_treated_as_independent",
            "covariance_status": "shared_anchor_covariance_unavailable",
            "uncertainty_scope": (
                "between_host_sampling_error_conditional_on_excluding_shared_"
                "anchor_and_common_systematic_uncertainty"),
            "total_uncertainty": False,
        },
        "distribution_free_sign_sensitivity": {
            "n_negative": negative,
            "n_positive": positive,
            "two_sided_sign_p_for_zero_median": sign_p,
        },
        "inverse_variance_sensitivity_only": {
            "mean_delta_mag": weighted_mean,
            "standard_error_mag": weighted_se,
            "cochran_q": cochran_q,
            "cochran_q_df": df,
            "cochran_q_p": float(chi2.sf(cochran_q, df)),
            "covariance_assumption": "tabulated method errors treated as independent",
            "primary_inference": False,
        },
    }
    if comparison_value_mag is not None:
        target = float(comparison_value_mag)
        statistic = (mean - target) / sem
        n_below = int(np.sum(delta < target))
        n_above = int(np.sum(delta > target))
        result["registered_shift_comparison"] = {
            "comparison_shift_mag": target,
            "mean_minus_comparison_mag": mean - target,
            "t_statistic": float(statistic),
            "one_sided_p_mean_at_least_comparison": float(t.cdf(statistic, df)),
            "n_host_deltas_below_comparison": n_below,
            "n_host_deltas_above_comparison": n_above,
            "one_sided_sign_p_median_at_least_comparison": float(
                binomtest(n_below, n, 0.5, alternative="greater").pvalue),
        }
    return result


def published_aggregate_consistency(rows: list[dict], *,
                                    comparison_value_mag: float) -> dict:
    """Replay source-reported means and statistical standard errors.

    No host rows or cross-sample covariance are available in this compact
    input.  The normal-reference calculations are therefore transparent
    transformations of published aggregates, not independent fits.
    """
    if len(rows) != len(_AGGREGATE_CONTRACTS):
        raise JWSTDistanceError("exact registered published aggregate rows required")
    datasets = [str(row["dataset"]) for row in rows]
    if len(datasets) != len(set(datasets)):
        raise JWSTDistanceError("duplicate published aggregate dataset")
    target = float(comparison_value_mag)
    if not math.isfinite(target):
        raise JWSTDistanceError("comparison value must be finite")
    results = []
    for row in rows:
        mean = float(row["mean_delta_mag"])
        se = float(row["stat_standard_error_mag"])
        parent_n = int(row["parent_sn_calibrator_count"])
        paired_n = int(row["paired_object_count"])
        parent_unit = str(row["parent_count_unit"])
        paired_unit = str(row["paired_count_unit"])
        sample_definition = str(row["paired_sample_definition"])
        if not all(math.isfinite(v) for v in (mean, se)) or se <= 0:
            raise JWSTDistanceError("aggregate mean and positive standard error required")
        if parent_unit not in {"SN", "host", "object"} or paired_unit not in {
                "SN", "host", "object"}:
            raise JWSTDistanceError("aggregate count unit is not registered")
        if not sample_definition.strip():
            raise JWSTDistanceError("aggregate paired sample definition is missing")
        contract = _AGGREGATE_CONTRACTS.get(str(row["dataset"]))
        if contract is None or {
                "source_arxiv": str(row["source_arxiv"]),
                "parent_count": parent_n,
                "parent_count_unit": parent_unit,
                "paired_count": paired_n,
                "paired_count_unit": paired_unit,
                "method_a": str(row["method_a"]),
                "method_b": str(row["method_b"]),
        } != contract:
            raise JWSTDistanceError("aggregate count/unit/source contract mismatch")
        z_zero = mean / se
        z_shift = (mean - target) / se
        results.append({
            "dataset": str(row["dataset"]),
            "source_arxiv": str(row["source_arxiv"]),
            "source_locator": str(row["source_locator"]),
            "parent_sample_description": str(row["parent_sample_description"]),
            "parent_sn_calibrator_count": parent_n,
            "parent_count_unit": parent_unit,
            "paired_object_count": paired_n,
            "paired_count_unit": paired_unit,
            "paired_sample_definition": sample_definition,
            "method_a": str(row["method_a"]),
            "method_b": str(row["method_b"]),
            "delta_definition": str(row["delta_definition"]),
            "published_mean_delta_mag": mean,
            "published_stat_standard_error_mag": se,
            "normal_reference_95pct_interval_mag": [
                mean - float(norm.ppf(0.975)) * se,
                mean + float(norm.ppf(0.975)) * se,
            ],
            "normal_reference_z_for_zero": z_zero,
            "normal_reference_two_sided_p_for_zero": float(
                2.0 * norm.sf(abs(z_zero))),
            "registered_shift_comparison": {
                "comparison_shift_mag": target,
                "normal_reference_z": z_shift,
                "one_sided_p_mean_at_least_comparison": float(norm.cdf(z_shift)),
            },
            "analysis_level": "source_reported_aggregate_replay_not_host_level_reanalysis",
            "uncertainty_scope": "published_statistical_standard_error",
            "covariance_status": "source_reported_aggregate_covariance_unavailable",
            "null_mock_status": "not_applicable_source_reported_aggregate",
        })
    return {
        "rows": results,
        "n_registered_aggregates": len(results),
        "cross_sample_combination_performed": False,
        "reason_not_combined": (
            "samples overlap and share an anchor; cross-sample covariance is unavailable"),
    }


def build_distance_result(rows: list[dict], aggregate_rows: list[dict]) -> dict:
    """Build host-level analyses and registered published-aggregate replays."""
    cchp = paired_consistency(rows, dataset="cchp_trgb_jagb")
    # The source paper plots this magnitude displacement as the approximate
    # shift needed to move 67.5 to 73 km/s/Mpc.  Register the formula rather
    # than rounding it to 0.17 mag.
    tension_shift = 5.0 * math.log10(73.0 / 67.5)
    shoes = paired_consistency(
        rows, dataset="shoes_jwst_hst", comparison_value_mag=tension_shift)
    return {
        "schema": "pr153.distance_consistency.v3",
        "module_schema": SCHEMA_VERSION,
        "status": "PUBLISHED_TABLE_CONDITIONAL_RESULT",
        "claim_tier": "conditional",
        "cchp_trgb_minus_jagb_consistency": cchp,
        "shoes_jwst_minus_hst_consistency": shoes,
        "expanded_source_reported_aggregates": published_aggregate_consistency(
            aggregate_rows, comparison_value_mag=tension_shift),
        "registered_tension_shift_formula": "5*log10(73.0/67.5)",
        "covariance_status": "shared_anchor_covariance_unavailable",
        "null_mock_status": "not_applicable_published_table_measurement",
        "claim_boundary": (
            "published-table host-distance consistency measurement; no H0 fit, "
            "cosmological inference, anisotropy claim, or family identification"),
        "caveats": [
            "the host tables do not provide a full shared-anchor covariance matrix",
            "host-level Student-t inference is primary; inverse-variance pooling is sensitivity-only",
            "failure to reject zero offset is a consistency result, not proof of method equality",
            "expanded aggregate rows are source-reported statistical summaries, not host-level refits",
            "overlapping aggregate samples are not combined without their covariance",
        ],
    }


# PR-309 current-stack closure.  This surface is intentionally separate from
# the historical PR-153 published-table result builders above: it consumes an
# exact PR-289 row-level admission and never reuses a PR-153/154 number.
PR309_FEATURE_ORDER = (
    "MONOPOLE",
    "GALACTIC_X",
    "GALACTIC_Y",
    "GALACTIC_Z",
    "REDSHIFT_CENTERED",
    "DEPTH_CENTERED",
)
PR309_COMPETITOR_ORDER = ("CF4", "2MRS")
PR309_HOST_LINKAGE_BASES = frozenset(
    {
        "SOURCE_REPORTED_HOST_IDENTITY",
        "NON_POSITIONAL_CATALOGUE_CROSS_ID",
        "AMBIGUOUS_HOST_MARGINALIZED",
    }
)
PR309_MINIMUM_SINGULAR_VALUE_RATIO = 1.0e-6
PR309_MAXIMUM_COVARIANCE_CONDITION = 1.0e10
PR309_OBSERVABLE_CONTRACT = {
    "observable_delta_definition": "METHOD_A_MINUS_METHOD_B_MAG",
    "observable_delta_unit": "mag",
}
PR309_SEMANTIC_CONTRACT = {
    "coordinate_frame": "GALACTIC_IAU_1958",
    "direction_unit": "degree",
    "redshift_frame": "CMB",
    "redshift_definition": "SOURCE_REPORTED_HOST_REDSHIFT_TRANSFORMED_TO_CMB",
    "depth_definition": "SOURCE_REPORTED_DISTANCE",
    "depth_unit": "Mpc",
}
PR309_COMPETITOR_SEMANTIC_CONTRACTS = {
    "CF4": {
        "input_frame": "CMB",
        "template_frame": "CMB",
        "template_unit": "mag",
        "template_definition": "METHOD_A_MINUS_METHOD_B_MAG_RESPONSE_TEMPLATE",
        "coordinate_role": "NATIVE_CMB_FRAME_FORWARD_MODEL",
    },
    "2MRS": {
        "input_frame": "GALACTIC_COMOVING_CARTESIAN",
        "template_frame": "CMB",
        "template_unit": "km/s",
        "template_definition": "RADIAL_PECULIAR_VELOCITY_RESPONSE_TEMPLATE",
        "coordinate_role": "NATIVE_CMB_FRAME_NEURAL_VELOCITY_FIELD",
    },
}
PR319_2MRS_GRID_SHAPE = (128, 128, 128)
PR319_2MRS_BOX_SIDE_HMPC = 400.0
PR319_2MRS_CELL_SIZE_HMPC = 3.125
PR319_2MRS_VALID_RADIUS_HMPC = 200.0
PR319_2MRS_HUBBLE_H = 0.6711
PR319_2MRS_FIELD_COMPONENT_ORDER = (
    "density.npy",
    "xVelocity.npy",
    "yVelocity.npy",
    "zVelocity.npy",
    "density_error.npy",
    "xVelocity_error.npy",
    "yVelocity_error.npy",
    "zVelocity_error.npy",
)
PR319_2MRS_NEURAL_FIELD_MEMBER_SHA256 = {
    "density.npy": "sha256:fe6afc85a42458dcc6f3a740cc575aaf0387944fad8f039045ae4eeea3b59c09",
    "xVelocity.npy": "sha256:50edf12e9dd8a79959071eda57ccd197f2cfba2bae5233210ab6243541aa4643",
    "yVelocity.npy": "sha256:c125f3d97aa8f9ed34110285e018df0849d955b62f0a472cebb34d196e2cb447",
    "zVelocity.npy": "sha256:ae1e0dfadf48c27afcf7f30c53c2e978f7edeab3506c9e446ed7f73770b207d6",
    "density_error.npy": "sha256:634639062221acff6a52db9185c7745abdecfcce5cd051bfbaff76981b9cda4d",
    "xVelocity_error.npy": "sha256:71cb34d1639f48a6cc22ba76d0f5c56756cc89f4b9f714c719a718c531a60114",
    "yVelocity_error.npy": "sha256:76396094a770b5874bc82779e4a95ad1ef5ad4683ba7cf321981cd377de26e26",
    "zVelocity_error.npy": "sha256:5b53329d64107503ddf93e69f0df52c26de109e87a2bc97c6b3c8b18e6c0c846",
}
PR319_2MRS_NEURAL_FIELD_CONTRACT = {
    "model_identity": "LILOW_GANESHAIAH_VEENA_NUSSER_2024_2MRS_NEURAL_VELOCITY_FIELD",
    "source_release": "PUBLIC_2MRS_NEURALNET_ARRAYS_ACCESSED_2026_08_25",
    "paper_identity": "arXiv:2404.02278v2",
    "publisher_doi": "10.1051/0004-6361/202450219",
    "repository_url": "https://github.com/rlilow/2MRS-NeuralNet",
    "repository_commit": "c4c141357f6c99d0d0f30784a1116afa204d91f6",
    "coordinate_frame": "GALACTIC_COMOVING_CARTESIAN",
    "velocity_frame": "CMB",
    "grid_shape": list(PR319_2MRS_GRID_SHAPE),
    "box_side_hmpc": PR319_2MRS_BOX_SIDE_HMPC,
    "cell_size_hmpc": PR319_2MRS_CELL_SIZE_HMPC,
    "grid_center_convention": "CELL_CENTER_Q_N_EQUALS_N_MINUS_63_5_TIMES_3_125_HMPC",
    "gaussian_smoothing_width_hmpc": 3.0,
    "valid_radius_hmpc": PR319_2MRS_VALID_RADIUS_HMPC,
    "hubble_h": PR319_2MRS_HUBBLE_H,
    "row_evaluation_rule": "TRILINEAR_THEN_OUTWARD_GALACTIC_RADIAL_PROJECTION",
    "radial_sign_convention": "POSITIVE_AWAY_FROM_OBSERVER",
    "uncertainty_role": "POINTWISE_VALIDATION_RMSE_NOT_COVARIANCE",
    "field_byte_license_status": "UNRESOLVED_NO_REDISTRIBUTION",
}


class JWSTSNCurrentStackError(ValueError):
    """Raised when the PR-309 row/covariance contract fails closed."""


@dataclass(frozen=True)
class JWSTSNCurrentStackInputs:
    """Typed, ordered JWST-SN rows and their complete covariance model."""

    row_ids: tuple[str, ...]
    row_report: tuple[dict[str, object], ...]
    observable_delta_mag: np.ndarray
    host_linkage_sigma_mag: np.ndarray
    redshift: np.ndarray
    depth_mpc: np.ndarray
    direction_unit_vectors: np.ndarray
    individual_sigma_mag: np.ndarray
    calibration_groups: tuple[str, ...]
    shared_zero_point_covariance_mag2: np.ndarray
    peculiar_velocity_covariance_mag2: np.ndarray
    total_covariance_mag2: np.ndarray
    competitor_order: tuple[str, ...]
    competitor_templates: dict[str, np.ndarray]
    competitor_metadata: dict[str, dict[str, object]]
    competitor_mode: str
    semantic_contract: dict[str, str]
    feature_order: tuple[str, ...] = PR309_FEATURE_ORDER


def _mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise JWSTSNCurrentStackError(f"{label} must be a mapping")
    return value


def _nonempty(value: object, *, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JWSTSNCurrentStackError(f"{label} must be non-empty text")
    return value


def _finite_number(value: object, *, label: str) -> float:
    if isinstance(value, bool):
        raise JWSTSNCurrentStackError(f"{label} must be finite")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise JWSTSNCurrentStackError(f"{label} must be finite") from exc
    if not math.isfinite(result):
        raise JWSTSNCurrentStackError(f"{label} must be finite")
    return result


def _ordered_rows(
    payload: object,
    *,
    label: str,
) -> tuple[tuple[str, ...], list[Mapping[str, object]]]:
    document = _mapping(payload, label=label)
    if set(document) != {"row_order", "rows"}:
        raise JWSTSNCurrentStackError(f"{label} fields drifted")
    order = document["row_order"]
    rows = document["rows"]
    if (
        isinstance(order, (str, bytes))
        or not isinstance(order, Sequence)
        or isinstance(rows, (str, bytes))
        or not isinstance(rows, Sequence)
        or len(order) != len(rows)
        or len(order) < len(PR309_FEATURE_ORDER) + 1
    ):
        raise JWSTSNCurrentStackError(f"{label} row order is incomplete")
    row_ids = tuple(_nonempty(value, label=f"{label} row id") for value in order)
    if len(row_ids) != len(set(row_ids)):
        raise JWSTSNCurrentStackError(f"{label} row order contains duplicates")
    normalized = [_mapping(row, label=f"{label} row") for row in rows]
    if tuple(row.get("row_id") for row in normalized) != row_ids:
        raise JWSTSNCurrentStackError(f"{label} row order and rows differ")
    return row_ids, normalized


def _finite_matrix(value: object, *, size: int, label: str) -> np.ndarray:
    try:
        matrix = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise JWSTSNCurrentStackError(f"{label} must be a finite square matrix") from exc
    if matrix.shape != (size, size) or not np.all(np.isfinite(matrix)):
        raise JWSTSNCurrentStackError(f"{label} must be a finite square matrix")
    if not np.allclose(matrix, matrix.T, atol=1.0e-14, rtol=1.0e-12):
        raise JWSTSNCurrentStackError(f"{label} must be symmetric")
    eigenvalues = np.linalg.eigvalsh(0.5 * (matrix + matrix.T))
    if eigenvalues[0] < -1.0e-12 * max(1.0, float(np.max(np.abs(eigenvalues)))):
        raise JWSTSNCurrentStackError(f"{label} must be positive semidefinite")
    return 0.5 * (matrix + matrix.T)


def _has_off_diagonal(matrix: np.ndarray) -> bool:
    off_diagonal = matrix - np.diag(np.diag(matrix))
    return bool(np.any(np.abs(off_diagonal) > 1.0e-15))


def _galactic_unit_vectors(longitude_deg: np.ndarray, latitude_deg: np.ndarray) -> np.ndarray:
    longitude = np.radians(longitude_deg)
    latitude = np.radians(latitude_deg)
    cosine = np.cos(latitude)
    return np.column_stack(
        (cosine * np.cos(longitude), cosine * np.sin(longitude), np.sin(latitude))
    )


def evaluate_pr319_2mrs_neural_radial_velocity(
    *,
    x_velocity: object,
    y_velocity: object,
    z_velocity: object,
    galactic_l_deg: object,
    galactic_b_deg: object,
    depth_mpc: object,
    hubble_h: float,
) -> np.ndarray:
    """Evaluate the 2024 2MRS NN field without inventing a magnitude model.

    The released Cartesian CMB-frame components are interpolated at the
    source-reported host position and projected onto the outward Galactic
    radial unit vector.  Pointwise RMSE arrays are deliberately not accepted:
    they are not a spatial or cross-component covariance.
    """

    if not math.isclose(
        float(hubble_h), PR319_2MRS_HUBBLE_H, rel_tol=0.0, abs_tol=0.0
    ):
        raise JWSTSNCurrentStackError("2MRS neural field hubble-h identity drifted")
    fields: list[np.ndarray] = []
    for value, label in (
        (x_velocity, "xVelocity.npy"),
        (y_velocity, "yVelocity.npy"),
        (z_velocity, "zVelocity.npy"),
    ):
        try:
            field = np.asarray(value)
        except (TypeError, ValueError) as exc:
            raise JWSTSNCurrentStackError(
                f"2MRS neural field {label} is malformed"
            ) from exc
        if field.shape != PR319_2MRS_GRID_SHAPE or field.dtype.kind not in "fc":
            raise JWSTSNCurrentStackError(
                f"2MRS neural field {label} shape or dtype drifted"
            )
        fields.append(field)
    try:
        longitude = np.asarray(galactic_l_deg, dtype=float)
        latitude = np.asarray(galactic_b_deg, dtype=float)
        depth = np.asarray(depth_mpc, dtype=float)
    except (TypeError, ValueError) as exc:
        raise JWSTSNCurrentStackError("2MRS neural field query is malformed") from exc
    if (
        longitude.ndim != 1
        or longitude.shape != latitude.shape
        or longitude.shape != depth.shape
        or longitude.size == 0
        or not np.all(np.isfinite(longitude))
        or not np.all(np.isfinite(latitude))
        or not np.all(np.isfinite(depth))
        or np.any((longitude < 0.0) | (longitude >= 360.0))
        or np.any((latitude < -90.0) | (latitude > 90.0))
        or np.any(depth <= 0.0)
    ):
        raise JWSTSNCurrentStackError("2MRS neural field query is malformed")
    directions = _galactic_unit_vectors(longitude, latitude)
    positions_hmpc = directions * (depth * PR319_2MRS_HUBBLE_H)[:, None]
    radii = np.linalg.norm(positions_hmpc, axis=1)
    if np.any(radii >= PR319_2MRS_VALID_RADIUS_HMPC - 1.0e-12):
        raise JWSTSNCurrentStackError("2MRS neural field query leaves valid sphere")
    fractional = (
        positions_hmpc / PR319_2MRS_CELL_SIZE_HMPC
        + (PR319_2MRS_GRID_SHAPE[0] - 1) / 2.0
    )
    lower = np.floor(fractional).astype(int)
    upper = lower + 1
    if np.any(lower < 0) or np.any(upper >= PR319_2MRS_GRID_SHAPE[0]):
        raise JWSTSNCurrentStackError("2MRS neural field interpolation is out of bounds")
    weights = fractional - lower
    velocity = np.empty((longitude.size, 3), dtype=float)
    for row_index in range(longitude.size):
        for component, field in enumerate(fields):
            value = 0.0
            for dx in (0, 1):
                for dy in (0, 1):
                    for dz in (0, 1):
                        index = (
                            lower[row_index, 0] + dx,
                            lower[row_index, 1] + dy,
                            lower[row_index, 2] + dz,
                        )
                        corner = float(field[index])
                        if not math.isfinite(corner):
                            raise JWSTSNCurrentStackError(
                                "2MRS neural field interpolation touches invalid support"
                            )
                        weight = (
                            (weights[row_index, 0] if dx else 1.0 - weights[row_index, 0])
                            * (weights[row_index, 1] if dy else 1.0 - weights[row_index, 1])
                            * (weights[row_index, 2] if dz else 1.0 - weights[row_index, 2])
                        )
                        value += weight * corner
            velocity[row_index, component] = value
    return np.einsum("ij,ij->i", velocity, directions)


def build_pr309_inputs(
    *,
    source_rows: object,
    host_rows: object,
    individual_errors: object,
    covariance: object,
    competitor_model: object,
    competitor_mode: str,
) -> JWSTSNCurrentStackInputs:
    """Validate and join the exact five-component PR-289 JWST-SN bundle."""

    if competitor_mode not in {"SYNTHETIC_CONTRACT", "ADMITTED_FIELD"}:
        raise JWSTSNCurrentStackError("competitor mode is not registered")

    row_ids, sources = _ordered_rows(source_rows, label="source rows")
    host_order, hosts = _ordered_rows(host_rows, label="host rows")
    error_order, errors = _ordered_rows(individual_errors, label="individual errors")
    if host_order != row_ids or error_order != row_ids:
        raise JWSTSNCurrentStackError("JWST-SN component row order drifted")
    count = len(row_ids)

    source_values: list[float] = []
    source_provenance: list[dict[str, str]] = []
    for row in sources:
        if set(row) != {
            "row_id",
            "source_id",
            "source_release",
            "source_locator",
            *PR309_OBSERVABLE_CONTRACT,
            "observable_delta_mag",
        }:
            raise JWSTSNCurrentStackError("source row fields drifted")
        if any(
            row.get(key) != value
            for key, value in PR309_OBSERVABLE_CONTRACT.items()
        ):
            raise JWSTSNCurrentStackError("observable semantic contract drifted")
        try:
            provenance = {
                "source_id": _nonempty(row["source_id"], label="source provenance"),
                "source_release": _nonempty(
                    row["source_release"], label="source provenance"
                ),
                "source_locator": _nonempty(
                    row["source_locator"], label="source provenance"
                ),
            }
        except JWSTSNCurrentStackError as exc:
            raise JWSTSNCurrentStackError("source provenance is incomplete") from exc
        source_provenance.append(provenance)
        source_values.append(
            _finite_number(row["observable_delta_mag"], label="observable delta")
        )

    host_ids: list[str] = []
    linkage_bases: list[str] = []
    linkage_probabilities: list[float] = []
    linkage_sigma: list[float] = []
    redshift: list[float] = []
    depth: list[float] = []
    longitude: list[float] = []
    latitude: list[float] = []
    for row in hosts:
        if set(row) != {
            "row_id",
            "host_id",
            "host_linkage_basis",
            "host_linkage_probability",
            "host_linkage_sigma_mag",
            "redshift",
            "depth_mpc",
            "galactic_l_deg",
            "galactic_b_deg",
            *PR309_SEMANTIC_CONTRACT,
        }:
            raise JWSTSNCurrentStackError("host row fields drifted")
        host_ids.append(_nonempty(row["host_id"], label="host identity"))
        basis = _nonempty(row["host_linkage_basis"], label="host linkage basis")
        if basis not in PR309_HOST_LINKAGE_BASES:
            raise JWSTSNCurrentStackError(
                "positional coincidence is not a physical host identity"
            )
        linkage_bases.append(basis)
        probability = _finite_number(
            row["host_linkage_probability"], label="host linkage probability"
        )
        sigma = _finite_number(
            row["host_linkage_sigma_mag"], label="host linkage uncertainty"
        )
        if (
            not 0.0 < probability <= 1.0
            or sigma < 0.0
            or (probability < 1.0 and sigma <= 0.0)
        ):
            raise JWSTSNCurrentStackError("host linkage uncertainty is invalid")
        linkage_probabilities.append(probability)
        linkage_sigma.append(sigma)
        if any(row.get(key) != value for key, value in PR309_SEMANTIC_CONTRACT.items()):
            raise JWSTSNCurrentStackError(
                "redshift/depth/direction semantic contract drifted"
            )
        redshift_value = _finite_number(row["redshift"], label="redshift")
        depth_value = _finite_number(row["depth_mpc"], label="depth")
        lon_value = _finite_number(row["galactic_l_deg"], label="Galactic longitude")
        lat_value = _finite_number(row["galactic_b_deg"], label="Galactic latitude")
        if (
            redshift_value <= 0.0
            or depth_value <= 0.0
            or not 0.0 <= lon_value < 360.0
            or not -90.0 <= lat_value <= 90.0
        ):
            raise JWSTSNCurrentStackError("redshift/depth/direction support is invalid")
        redshift.append(redshift_value)
        depth.append(depth_value)
        longitude.append(lon_value)
        latitude.append(lat_value)

    individual_sigma: list[float] = []
    calibration_groups: list[str] = []
    for row in errors:
        if set(row) != {"row_id", "sigma_individual_mag", "calibration_group"}:
            raise JWSTSNCurrentStackError("individual-error row fields drifted")
        sigma = _finite_number(
            row["sigma_individual_mag"], label="individual uncertainty"
        )
        if sigma <= 0.0:
            raise JWSTSNCurrentStackError("individual uncertainty must be positive")
        individual_sigma.append(sigma)
        calibration_groups.append(
            _nonempty(row["calibration_group"], label="calibration group")
        )

    covariance_payload = _mapping(covariance, label="covariance")
    if set(covariance_payload) != {
        "row_order",
        "calibration_group_order",
        "shared_zero_point_covariance_mag2",
        "peculiar_velocity_covariance_mag2",
        "maximum_condition_number",
    }:
        raise JWSTSNCurrentStackError("covariance fields drifted")
    if tuple(covariance_payload["row_order"]) != row_ids:
        raise JWSTSNCurrentStackError("covariance row order drifted")
    group_order_raw = covariance_payload["calibration_group_order"]
    if isinstance(group_order_raw, (str, bytes)) or not isinstance(
        group_order_raw, Sequence
    ):
        raise JWSTSNCurrentStackError("calibration-group order is malformed")
    group_order = tuple(
        _nonempty(value, label="calibration group") for value in group_order_raw
    )
    if (
        len(group_order) != len(set(group_order))
        or set(group_order) != set(calibration_groups)
    ):
        raise JWSTSNCurrentStackError("calibration-group identity drifted")
    group_covariance = _finite_matrix(
        covariance_payload["shared_zero_point_covariance_mag2"],
        size=len(group_order),
        label="shared zero-point covariance",
    )
    peculiar_covariance = _finite_matrix(
        covariance_payload["peculiar_velocity_covariance_mag2"],
        size=count,
        label="peculiar-velocity covariance",
    )
    group_index = {group: index for index, group in enumerate(group_order)}
    design = np.zeros((count, len(group_order)), dtype=float)
    design[np.arange(count), [group_index[group] for group in calibration_groups]] = 1.0
    shared_covariance = design @ group_covariance @ design.T
    if not _has_off_diagonal(shared_covariance) or not _has_off_diagonal(
        peculiar_covariance
    ):
        raise JWSTSNCurrentStackError(
            "shared zero-point and peculiar-velocity covariance require off-diagonal support"
        )
    total_covariance = (
        np.diag(np.square(individual_sigma) + np.square(linkage_sigma))
        + shared_covariance
        + peculiar_covariance
    )
    maximum_condition = _finite_number(
        covariance_payload["maximum_condition_number"],
        label="maximum covariance condition number",
    )
    condition = float(np.linalg.cond(total_covariance))
    eigenvalues = np.linalg.eigvalsh(total_covariance)
    if (
        maximum_condition != PR309_MAXIMUM_COVARIANCE_CONDITION
        or eigenvalues[0] <= 0.0
        or not math.isfinite(condition)
        or condition > maximum_condition
    ):
        raise JWSTSNCurrentStackError("full covariance is singular or ill-conditioned")

    competitor_payload = _mapping(competitor_model, label="competitor model")
    if set(competitor_payload) != {"row_order", "competitors"}:
        raise JWSTSNCurrentStackError("competitor-model fields drifted")
    if tuple(competitor_payload["row_order"]) != row_ids:
        raise JWSTSNCurrentStackError("competitor-model row order drifted")
    competitor_rows = competitor_payload["competitors"]
    if isinstance(competitor_rows, (str, bytes)) or not isinstance(
        competitor_rows, Sequence
    ):
        raise JWSTSNCurrentStackError("CF4 and 2MRS competitors are required separately")
    normalized_competitors = [
        _mapping(row, label="competitor row") for row in competitor_rows
    ]
    competitor_order = tuple(row.get("competitor_id") for row in normalized_competitors)
    if competitor_order != PR309_COMPETITOR_ORDER:
        raise JWSTSNCurrentStackError("CF4 and 2MRS competitors are required separately")
    if len({row.get("model_identity") for row in normalized_competitors}) != len(
        normalized_competitors
    ):
        raise JWSTSNCurrentStackError("competitor model identities must remain distinct")
    templates: dict[str, np.ndarray] = {}
    metadata: dict[str, dict[str, object]] = {}
    common_fields = {
        "competitor_id",
        "model_identity",
        "source_release",
        "model_role",
        "input_frame",
        "template_frame",
        "template_unit",
        "template_definition",
        "coordinate_role",
        "coordinate_identity",
        "template_value_source",
        "template_values",
    }
    for row in normalized_competitors:
        competitor_id = str(row["competitor_id"])
        neural_fields = set(PR319_2MRS_NEURAL_FIELD_CONTRACT) | {
            "field_component_order",
            "field_component_sha256",
        }
        expected_fields = common_fields | (neural_fields if competitor_id == "2MRS" else set())
        if set(row) != expected_fields:
            raise JWSTSNCurrentStackError("competitor fields drifted")
        if row["model_role"] != "SEPARATE_DIRECTION_DEPTH_COMPETITOR":
            raise JWSTSNCurrentStackError("competitors cannot be pooled")
        semantic_contract = PR309_COMPETITOR_SEMANTIC_CONTRACTS[competitor_id]
        if any(row.get(key) != value for key, value in semantic_contract.items()):
            raise JWSTSNCurrentStackError(
                "2MRS neural field frame or template semantics drifted"
                if competitor_id == "2MRS"
                else "competitor frame or template semantics drifted"
            )
        expected_template_source = (
            "SYNTHETIC_CONTRACT_ORACLE"
            if competitor_mode == "SYNTHETIC_CONTRACT"
            else (
                "LILOW_2024_FIELD_TRILINEAR_RADIAL_PROJECTION"
                if competitor_id == "2MRS"
                else "ADMITTED_CF4_FORWARD_MODEL"
            )
        )
        if row["template_value_source"] != expected_template_source:
            raise JWSTSNCurrentStackError("competitor template source drifted")
        try:
            template = np.asarray(row["template_values"], dtype=float)
        except (TypeError, ValueError) as exc:
            raise JWSTSNCurrentStackError("competitor template is malformed") from exc
        if template.shape != (count,) or not np.all(np.isfinite(template)):
            raise JWSTSNCurrentStackError("competitor template is malformed")
        model_identity = _nonempty(
            row["model_identity"], label="competitor model identity"
        )
        source_release = _nonempty(
            row["source_release"], label="competitor source release"
        )
        coordinate_identity = _nonempty(
            row["coordinate_identity"],
            label="competitor coordinate identity",
        )
        extra_metadata: dict[str, object] = {}
        if competitor_id == "2MRS":
            if any(
                row.get(key) != value
                for key, value in PR319_2MRS_NEURAL_FIELD_CONTRACT.items()
            ):
                raise JWSTSNCurrentStackError("2MRS neural field identity drifted")
            component_order = row["field_component_order"]
            member_hashes = row["field_component_sha256"]
            if (
                isinstance(component_order, (str, bytes))
                or not isinstance(component_order, Sequence)
                or list(component_order) != list(PR319_2MRS_FIELD_COMPONENT_ORDER)
            ):
                raise JWSTSNCurrentStackError("2MRS neural field member order drifted")
            if member_hashes != PR319_2MRS_NEURAL_FIELD_MEMBER_SHA256:
                raise JWSTSNCurrentStackError("2MRS neural field member hashes drifted")
            extra_metadata = {
                **PR319_2MRS_NEURAL_FIELD_CONTRACT,
                "field_component_order": list(PR319_2MRS_FIELD_COMPONENT_ORDER),
                "field_component_sha256": dict(
                    PR319_2MRS_NEURAL_FIELD_MEMBER_SHA256
                ),
            }
        templates[competitor_id] = template
        metadata[competitor_id] = {
            "model_identity": model_identity,
            "source_release": source_release,
            "model_role": "SEPARATE_DIRECTION_DEPTH_COMPETITOR",
            **semantic_contract,
            "coordinate_identity": coordinate_identity,
            "template_value_source": expected_template_source,
            **extra_metadata,
        }
    if np.allclose(
        templates["CF4"], templates["2MRS"], atol=0.0, rtol=0.0
    ):
        raise JWSTSNCurrentStackError("competitor templates must remain distinct")

    directions = _galactic_unit_vectors(
        np.asarray(longitude, dtype=float), np.asarray(latitude, dtype=float)
    )
    row_report = tuple(
        {
            "row_id": row_id,
            **source_provenance[index],
            "host_id": host_ids[index],
            "host_linkage_basis": linkage_bases[index],
            "host_linkage_probability": linkage_probabilities[index],
            "host_linkage_sigma_mag": linkage_sigma[index],
            "individual_sigma_mag": individual_sigma[index],
            "calibration_group": calibration_groups[index],
            "redshift": redshift[index],
            "depth_mpc": depth[index],
            "galactic_l_deg": longitude[index],
            "galactic_b_deg": latitude[index],
            "host_identity_status": (
                "MARGINALIZED_LINKAGE_NOT_IDENTITY"
                if linkage_bases[index] == "AMBIGUOUS_HOST_MARGINALIZED"
                or linkage_probabilities[index] < 1.0
                else "ADMITTED_NON_POSITIONAL_IDENTITY_EVIDENCE"
            ),
            **PR309_OBSERVABLE_CONTRACT,
            **PR309_SEMANTIC_CONTRACT,
        }
        for index, row_id in enumerate(row_ids)
    )
    return JWSTSNCurrentStackInputs(
        row_ids=row_ids,
        row_report=row_report,
        observable_delta_mag=np.asarray(source_values, dtype=float),
        host_linkage_sigma_mag=np.asarray(linkage_sigma, dtype=float),
        redshift=np.asarray(redshift, dtype=float),
        depth_mpc=np.asarray(depth, dtype=float),
        direction_unit_vectors=directions,
        individual_sigma_mag=np.asarray(individual_sigma, dtype=float),
        calibration_groups=tuple(calibration_groups),
        shared_zero_point_covariance_mag2=shared_covariance,
        peculiar_velocity_covariance_mag2=peculiar_covariance,
        total_covariance_mag2=total_covariance,
        competitor_order=PR309_COMPETITOR_ORDER,
        competitor_templates=templates,
        competitor_metadata=metadata,
        competitor_mode=competitor_mode,
        semantic_contract={**PR309_SEMANTIC_CONTRACT, **PR309_OBSERVABLE_CONTRACT},
    )


def _center_scale(values: np.ndarray) -> np.ndarray:
    centered = np.asarray(values, dtype=float) - float(np.mean(values))
    scale = float(np.linalg.norm(centered))
    return centered / scale if scale > 0.0 else np.zeros_like(centered)


def _response_design(inputs: JWSTSNCurrentStackInputs) -> np.ndarray:
    rows = len(inputs.row_ids)
    directions = np.asarray(inputs.direction_unit_vectors, dtype=float)
    if directions.shape != (rows, 3) or not np.all(np.isfinite(directions)):
        raise JWSTSNCurrentStackError("direction response is malformed")
    return np.column_stack(
        (
            np.ones(rows),
            directions,
            _center_scale(inputs.redshift),
            _center_scale(inputs.depth_mpc),
        )
    )


def _whitened_rank(
    design: np.ndarray,
    covariance: np.ndarray,
    *,
    minimum_ratio: float = PR309_MINIMUM_SINGULAR_VALUE_RATIO,
) -> dict[str, object]:
    try:
        whitened = np.linalg.solve(np.linalg.cholesky(covariance), design)
    except np.linalg.LinAlgError as exc:
        raise JWSTSNCurrentStackError("response whitening failed") from exc
    column_norms = np.linalg.norm(whitened, axis=0)
    if not np.all(np.isfinite(column_norms)):
        raise JWSTSNCurrentStackError("response column normalization failed")
    nonzero_columns = column_norms > np.finfo(float).eps
    scaled = np.zeros_like(whitened)
    scaled[:, nonzero_columns] = (
        whitened[:, nonzero_columns] / column_norms[nonzero_columns]
    )
    try:
        singular_values = np.linalg.svd(scaled, compute_uv=False)
    except np.linalg.LinAlgError as exc:
        raise JWSTSNCurrentStackError("response rank factorization failed") from exc
    expected = int(design.shape[1])
    largest = float(singular_values[0]) if singular_values.size else 0.0
    threshold = largest * minimum_ratio
    rank = int(np.sum(singular_values > threshold)) if largest > 0.0 else 0
    ratio = float(singular_values[-1] / largest) if largest > 0.0 else 0.0
    return {
        "rank": rank,
        "expected_rank": expected,
        "minimum_singular_value_ratio": ratio,
        "threshold_ratio": minimum_ratio,
        "whitening": "cholesky_left",
        "column_scaling": "covariance_whitened_l2",
        "threshold_basis": "largest_singular_value_after_column_scaling",
        "status": "FULL_RANK" if rank == expected else "RANK_DEFICIENT_ABSTAIN",
    }


def _competitor_diagnostic(
    *,
    inputs: JWSTSNCurrentStackInputs,
    base_design: np.ndarray,
    competitor_id: str,
) -> dict[str, object]:
    augmented = np.column_stack(
        (base_design, inputs.competitor_templates[competitor_id])
    )
    rank = _whitened_rank(augmented, inputs.total_covariance_mag2)
    if rank["rank"] != rank["expected_rank"]:
        return {
            "status": "NON_IDENTIFIED_ABSTAIN",
            "response_rank": rank,
        }
    return {
        "status": "NUMERICALLY_FULL_RANK_DIAGNOSTIC_ONLY",
        "response_rank": rank,
        **inputs.competitor_metadata[competitor_id],
    }


def _host_linkage_blocked_rows(inputs: JWSTSNCurrentStackInputs) -> list[str]:
    blocked_row_ids: list[str] = []
    for row in inputs.row_report:
        row_id = row.get("row_id")
        if not isinstance(row_id, str) or not row_id:
            raise JWSTSNCurrentStackError("host-linkage row identity drifted")
        if row.get("host_identity_status") != "ADMITTED_NON_POSITIONAL_IDENTITY_EVIDENCE":
            blocked_row_ids.append(row_id)
    return blocked_row_ids


def analyze_pr309_current_stack(
    inputs: JWSTSNCurrentStackInputs,
    *,
    observed: bool,
) -> dict[str, object]:
    """Return separate response-rank diagnostics or an explicit abstention.

    PR-309 closes input, covariance, and response preparation only.  It does
    not fit competitor amplitudes; model-conditioned point inference requires
    a separately registered HTT analysis contract.
    """

    if type(observed) is not bool:
        raise JWSTSNCurrentStackError("observed state must be one boolean")
    if observed and inputs.competitor_mode != "ADMITTED_FIELD":
        raise JWSTSNCurrentStackError(
            "observed execution requires admitted competitor field templates"
        )
    blocked_host_rows = _host_linkage_blocked_rows(inputs)
    response_rank: dict[str, object] | None = None
    diagnostics: dict[str, dict[str, object]] = {}
    if blocked_host_rows:
        terminal = "HOST_LINKAGE_COVARIATE_MARGINALIZATION_REQUIRED"
    else:
        base_design = _response_design(inputs)
        response_rank = _whitened_rank(base_design, inputs.total_covariance_mag2)
        if response_rank["rank"] != response_rank["expected_rank"]:
            terminal = "RANK_DEFICIENT_ABSTAIN"
        else:
            diagnostics = {
                competitor_id: _competitor_diagnostic(
                    inputs=inputs,
                    base_design=base_design,
                    competitor_id=competitor_id,
                )
                for competitor_id in inputs.competitor_order
            }
            if any(
                item["status"] == "NON_IDENTIFIED_ABSTAIN"
                for item in diagnostics.values()
            ):
                terminal = "WEAK_COMPETITOR_IDENTIFICATION_ABSTAIN"
            else:
                terminal = (
                    "OBSERVED_DESCRIPTIVE_OPERATOR_COMPLETE"
                    if observed
                    else "SYNTHETIC_OPERATOR_CLOSURE_PASS"
                )
    return {
        "format": "JWST_SN_CURRENT_STACK_TYPED_REPORT",
        "lane": "JWST_SN",
        "row_count": len(inputs.row_ids),
        "row_order": list(inputs.row_ids),
        "row_report": list(inputs.row_report),
        "feature_order": list(inputs.feature_order),
        "semantic_contract": dict(inputs.semantic_contract),
        "covariance": {
            "status": "FULL_SHARED_COVARIANCE_VALID",
            "shape": list(inputs.total_covariance_mag2.shape),
            "condition_number": float(np.linalg.cond(inputs.total_covariance_mag2)),
            "shared_zero_point_off_diagonal": _has_off_diagonal(
                inputs.shared_zero_point_covariance_mag2
            ),
            "peculiar_velocity_off_diagonal": _has_off_diagonal(
                inputs.peculiar_velocity_covariance_mag2
            ),
        },
        "response_rank": response_rank,
        "competitor_order": list(inputs.competitor_order),
        "competitor_mode": inputs.competitor_mode,
        "competitor_combination_performed": False,
        "competitor_conditioned_diagnostics": diagnostics,
        "terminal_disposition": terminal,
        "forced_source_label": None,
        "p_value": None,
        "family_identification": "FORBIDDEN",
        "claim_boundary": (
            "row-provenance and shared-covariance diagnostic only; no host identity "
            "promotion, source attribution, cosmological inference, or family identification"
        ),
        "observed_statistic_seen": observed,
        "observed_science_executed": observed,
    }
