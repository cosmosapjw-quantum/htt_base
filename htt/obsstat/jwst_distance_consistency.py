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

import math

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
