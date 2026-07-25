"""mio.tension.flrw_tension — HJ-03a FLRW-null tail helpers.

Parent plan: ``htt/docs/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md`` §4.5.3.3.

This module is deliberately narrow: it evaluates empirical tail
probabilities from caller-supplied observed test statistics and caller-
supplied FLRW mock ensembles. The mock generator and null calibration stay
outside MIO so this layer remains a pure diagnostic/reporting surface.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from obsstat.null_ensembles import validate_null_feature_payload
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.tsc_overlay import TscAdequacyOverlay


DEFAULT_DOMAIN_CAVEAT = (
    "FLRW null predictive tail summaries require an externally generated "
    "and calibrated FLRW mock ensemble; this module only scores caller-"
    "supplied statistics."
)
_NULL_PREDICTIVE_CAVEAT = (
    "MIO FLRW tail summaries are diagnostic-only and do not provide HTT "
    "model-dependent inference outputs or validation."
)
_FLRW_NULL_FEATURE_TARGET = "flrw_null_predictive_check"
_TAIL_TO_NULL_PAYLOAD_TAIL = {
    "greater": "upper_tail",
    "less": "lower_tail",
    "two-sided": "two_sided",
}
_COVARIANCE_READY_STATUSES = frozenset(
    {
        "matched_covariance_calibrated",
    }
)
_NULL_MOCK_READY_STATUSES = frozenset(
    {
        "matched_null_mocks_calibrated",
    }
)
_MASK_READY_STATUSES = frozenset(
    {
        "matched_mask_hash",
    }
)
_NOISE_MODEL_READY_STATUSES = frozenset(
    {
        "matched_noise_model",
    }
)
_SKY_SUPPORT_COMPLETE_STATUSES = frozenset({"complete"})


@dataclass(frozen=True)
class FlrwPppStatistic:
    """PPP summary for one caller-defined test statistic."""

    name: str
    observed_value: float
    tail: str
    p_value: float
    corrected_p_value: float
    mock_mean: float
    mock_std: float
    n_mock: int


@dataclass(frozen=True)
class FlrwPppReport:
    """Collection of PPP results with a global look-elsewhere summary."""

    statistics: tuple[FlrwPppStatistic, ...]
    look_elsewhere_method: str
    strongest_statistic: str
    min_raw_p_value: float
    min_corrected_p_value: float


@dataclass(frozen=True)
class _NullPredictiveGate:
    ready: bool
    covariance_ready: bool
    null_mocks_ready: bool
    requires_covariance: bool
    requires_sky_support: bool
    sky_support_status: str
    required_gates: tuple[str, ...]
    passed_gates: tuple[str, ...]
    failed_gates: tuple[str, ...]
    caveats: tuple[str, ...]
    metadata: dict[str, Any]


def _validate_mock_values(mock_values: Sequence[float]) -> np.ndarray:
    arr = np.asarray(mock_values, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"mock_values must be 1-D; got ndim={arr.ndim}")
    if arr.size == 0:
        raise ValueError("mock_values must contain at least one sample")
    if not np.all(np.isfinite(arr)):
        raise ValueError("mock_values contains non-finite entries")
    return arr


def posterior_predictive_pvalue(
    observed_value: float,
    mock_values: Sequence[float],
    *,
    tail: str = "greater",
) -> float:
    """Return an empirical tail probability using additive smoothing.

    The function name is retained for legacy callers. No posterior-generating
    process is implied by this helper.

    Parameters
    ----------
    observed_value
        Statistic measured on the real data.
    mock_values
        Same statistic measured on FLRW mocks.
    tail
        One of ``greater`` / ``less`` / ``two-sided``.
    """
    arr = _validate_mock_values(mock_values)
    obs = float(observed_value)
    if not math.isfinite(obs):
        raise ValueError("observed_value must be finite")

    if tail == "greater":
        exceed = int(np.sum(arr >= obs))
    elif tail == "less":
        exceed = int(np.sum(arr <= obs))
    elif tail == "two-sided":
        center = float(np.median(arr))
        exceed = int(np.sum(np.abs(arr - center) >= abs(obs - center)))
    else:
        raise ValueError(
            f"tail must be one of 'greater', 'less', 'two-sided'; got {tail!r}"
        )
    return float((exceed + 1) / (arr.size + 1))


def evaluate_flrw_tension(
    observed_statistics: Mapping[str, float],
    mock_statistics: Mapping[str, Sequence[float]],
    *,
    tails: Optional[Mapping[str, str]] = None,
    correction_method: str = "bonferroni",
) -> FlrwPppReport:
    """Score multiple test statistics against caller-supplied FLRW mocks."""
    obs_keys = tuple(sorted(observed_statistics))
    mock_keys = tuple(sorted(mock_statistics))
    if not obs_keys:
        raise ValueError("observed_statistics must contain at least one entry")
    if obs_keys != mock_keys:
        raise ValueError(
            "observed_statistics and mock_statistics must share identical keys; "
            f"got {obs_keys} vs {mock_keys}"
        )
    if correction_method != "bonferroni":
        raise ValueError(
            f"unsupported correction_method {correction_method!r}; "
            "only 'bonferroni' is implemented"
        )

    tail_map = dict(tails) if tails is not None else {}
    n_test = len(obs_keys)
    stats = []
    for name in obs_keys:
        tail = tail_map.get(name, "greater")
        mock_arr = _validate_mock_values(mock_statistics[name])
        raw_p = posterior_predictive_pvalue(
            float(observed_statistics[name]),
            mock_arr,
            tail=tail,
        )
        corrected = float(min(raw_p * n_test, 1.0))
        stats.append(
            FlrwPppStatistic(
                name=name,
                observed_value=float(observed_statistics[name]),
                tail=tail,
                p_value=raw_p,
                corrected_p_value=corrected,
                mock_mean=float(np.mean(mock_arr)),
                mock_std=float(np.std(mock_arr, ddof=1)) if mock_arr.size > 1 else 0.0,
                n_mock=int(mock_arr.size),
            )
        )

    stats_tuple = tuple(stats)
    strongest = min(
        stats_tuple,
        key=lambda item: (item.corrected_p_value, item.p_value, item.name),
    )
    return FlrwPppReport(
        statistics=stats_tuple,
        look_elsewhere_method=correction_method,
        strongest_statistic=strongest.name,
        min_raw_p_value=float(min(item.p_value for item in stats_tuple)),
        min_corrected_p_value=float(
            min(item.corrected_p_value for item in stats_tuple)
        ),
    )


def _status_is_ready(value: object, *, allowed: frozenset[str]) -> bool:
    return str(value or "").strip() in allowed


def _sky_support_from_payload(value: object) -> str:
    text = str(value or "").strip()
    if text in _SKY_SUPPORT_COMPLETE_STATUSES:
        return "complete"
    if not text or text == "missing":
        return "not_applicable"
    return "partial"


def _tail_summary(report: FlrwPppReport) -> dict[str, float | str | int]:
    return {
        "minimum_corrected_tail_probability": float(report.min_corrected_p_value),
        "strongest_statistic": report.strongest_statistic,
        "statistic_count": int(len(report.statistics)),
    }


def _statistics_payload(report: FlrwPppReport) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    for item in report.statistics:
        rows.append(
            {
                "name": item.name,
                "observed_value": float(item.observed_value),
                "tail": item.tail,
                "empirical_tail_probability": float(item.p_value),
                "tail_probability_role": "descriptive_empirical_tail_not_flrw_tension",
                "corrected_tail_probability": float(item.corrected_p_value),
                "mock_mean": float(item.mock_mean),
                "mock_std": float(item.mock_std),
                "n_mock": int(item.n_mock),
            }
        )
    return rows


def _validate_null_predictive_payload(
    report: FlrwPppReport,
    null_predictive_payload: Mapping[str, object] | None,
    *,
    null_mocks_calibrated: bool,
) -> _NullPredictiveGate:
    if null_predictive_payload is None:
        metadata = {
            "null_predictive_distribution_status": "missing",
            "legacy_null_mocks_calibrated_flag": bool(null_mocks_calibrated),
            "null_family": None,
            "null_ensemble_ref": None,
            "null_mock_status": "missing",
            "null_calibration_status": "missing",
            "covariance_status": "missing",
            "sky_support_status": "not_applicable",
            "mask_status": "missing",
            "noise_model_status": "missing",
            "look_elsewhere_status": "missing",
            "scan_volume_hash": None,
            "tail_definitions": {},
            "tail_probability_export_status": "descriptive_only_blocked",
            "raw_anomaly_pvalue_status": "not_exported_as_flrw_tension",
            "claim_scope": "diagnostic_only_flrw_null_predictive_check",
            "transfer_source": "none",
            "required_gates": ["null_mocks_ready"],
            "passed_gates": [],
            "failed_gates": ["null_mocks_ready"],
            "caveats": ["null_predictive_payload_missing"],
        }
        return _NullPredictiveGate(
            ready=False,
            covariance_ready=False,
            null_mocks_ready=False,
            requires_covariance=False,
            requires_sky_support=False,
            sky_support_status="not_applicable",
            required_gates=("null_mocks_ready",),
            passed_gates=tuple(),
            failed_gates=("null_mocks_ready",),
            caveats=("null_predictive_payload_missing",),
            metadata=metadata,
        )

    validate_null_feature_payload(null_predictive_payload)
    payload = dict(null_predictive_payload)
    if payload["null_family"] != "flrw_mask_noise":
        raise ValueError("null_predictive_payload.null_family must be flrw_mask_noise")
    if _FLRW_NULL_FEATURE_TARGET not in payload["feature_targets"]:
        raise ValueError(
            "null_predictive_payload.feature_targets must include "
            "flrw_null_predictive_check"
        )

    report_stats = {item.name: item for item in report.statistics}
    payload_p_values = {
        str(key): float(value)
        for key, value in dict(payload["p_values"]).items()  # type: ignore[arg-type]
    }
    if set(payload_p_values) != set(report_stats):
        raise ValueError("null_predictive_payload.p_values must match report statistic keys")

    expected_tails = {
        name: _TAIL_TO_NULL_PAYLOAD_TAIL[item.tail]
        for name, item in report_stats.items()
    }
    tail_definitions = {
        str(key): str(value)
        for key, value in dict(payload["tail_definitions"]).items()  # type: ignore[arg-type]
    }
    for name, expected_tail in expected_tails.items():
        if tail_definitions.get(name) != expected_tail:
            raise ValueError("null_predictive_payload.tail_definitions must match report tails")

    for name, expected in payload_p_values.items():
        observed = report_stats[name].corrected_p_value
        if not math.isclose(expected, observed, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(
                "null_predictive_payload.p_values must match report corrected "
                "tail probabilities"
            )

    mock_counts = {item.n_mock for item in report.statistics}
    payload_mock_count = int(payload["mock_count"])
    if len(mock_counts) != 1 or payload_mock_count != next(iter(mock_counts)):
        raise ValueError("null_predictive_payload.mock_count must match report mock count")

    required = [
        "null_predictive_payload_attached",
        "flrw_null_family",
        "statistic_key_match",
        "tail_definition_match",
        "mock_count_match",
        "tail_probability_match",
        "global_look_elsewhere_ready",
        "covariance_ready",
        "null_mocks_ready",
        "sky_support_complete",
        "mask_ready",
        "noise_model_ready",
    ]
    passed = required[:6]
    failed: list[str] = []
    caveats: list[str] = []

    look_elsewhere_status = str(payload["look_elsewhere_status"])
    global_ready = look_elsewhere_status == "global_corrected"
    if global_ready:
        passed.append("global_look_elsewhere_ready")
    else:
        failed.append("global_look_elsewhere_ready")
        caveats.append("look_elsewhere_not_global_corrected")

    covariance_ready = _status_is_ready(
        payload["covariance_status"],
        allowed=_COVARIANCE_READY_STATUSES,
    )
    if covariance_ready:
        passed.append("covariance_ready")
    else:
        failed.append("covariance_ready")
        caveats.append("covariance_status_not_ready")

    null_mocks_ready = _status_is_ready(
        payload["null_mock_status"],
        allowed=_NULL_MOCK_READY_STATUSES,
    )
    if null_mocks_ready:
        passed.append("null_mocks_ready")
    else:
        failed.append("null_mocks_ready")
        caveats.append("null_mock_status_not_ready")

    sky_support_status = _sky_support_from_payload(payload["sky_support_status"])
    if sky_support_status == "complete":
        passed.append("sky_support_complete")
    else:
        failed.append("sky_support_complete")
        caveats.append("sky_support_not_complete")

    mask_ready = _status_is_ready(
        payload["mask_status"],
        allowed=_MASK_READY_STATUSES,
    )
    if mask_ready:
        passed.append("mask_ready")
    else:
        failed.append("mask_ready")
        caveats.append("mask_status_not_ready")

    noise_ready = _status_is_ready(
        payload["noise_model_status"],
        allowed=_NOISE_MODEL_READY_STATUSES,
    )
    if noise_ready:
        passed.append("noise_model_ready")
    else:
        failed.append("noise_model_ready")
        caveats.append("noise_model_status_not_ready")

    ready = not failed
    status = "calibrated_matched"
    if not global_ready:
        status = "not_global_corrected"
    elif not ready:
        status = "support_metadata_incomplete"

    metadata = {
        "null_predictive_distribution_status": status,
        "legacy_null_mocks_calibrated_flag": bool(null_mocks_calibrated),
        "null_family": payload["null_family"],
        "null_ensemble_ref": payload["null_ensemble_ref"],
        "null_mock_status": payload["null_mock_status"],
        "null_calibration_status": (
            "matched_null_mocks_available" if ready else "not_claim_ready"
        ),
        "covariance_status": payload["covariance_status"],
        "sky_support_status": payload["sky_support_status"],
        "mask_status": payload["mask_status"],
        "noise_model_status": payload["noise_model_status"],
        "look_elsewhere_status": look_elsewhere_status,
        "look_elsewhere_trials": payload["look_elsewhere_trials"],
        "scan_volume_hash": payload["scan_volume_hash"],
        "tail_definitions": dict(tail_definitions),
        "p_value_role": "look_elsewhere_corrected_tail_probability",
        "p_value_keys": sorted(payload_p_values),
        "mock_count": payload_mock_count,
        "config_hash": payload["config_hash"],
        "input_hashes": list(payload["input_hashes"]),  # type: ignore[arg-type]
        "generating_command": payload["generating_command"],
        "git_commit": payload.get("git_commit"),
        "worktree_state": payload.get("worktree_state"),
        "tail_probability_export_status": (
            "null_predictive_calibrated" if ready else "descriptive_only_blocked"
        ),
        "raw_anomaly_pvalue_status": "not_exported_as_flrw_tension",
        "claim_scope": "diagnostic_only_flrw_null_predictive_check",
        "transfer_source": payload["transfer_source"],
        "does_not_establish": list(payload.get("does_not_establish", ())),
        "required_gates": list(required),
        "passed_gates": list(passed),
        "failed_gates": list(failed),
        "caveats": list(caveats),
    }
    return _NullPredictiveGate(
        ready=ready,
        covariance_ready=covariance_ready,
        null_mocks_ready=null_mocks_ready and global_ready,
        requires_covariance=True,
        requires_sky_support=True,
        sky_support_status=sky_support_status,
        required_gates=tuple(required),
        passed_gates=tuple(passed),
        failed_gates=tuple(failed),
        caveats=tuple(caveats),
        metadata=metadata,
    )


def to_mio_certificate(
    report: FlrwPppReport,
    *,
    probe_name: str = "FLRW",
    channel: str = "ppp",
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.tension.flrw_tension v0.1",
    input_data_hashes: Optional[Sequence[str]] = None,
    config_hash: Optional[str] = None,
    null_mocks_calibrated: bool = False,
    null_predictive_payload: Mapping[str, object] | None = None,
    artifact_path: str = "artifacts/mio/mio_flrw_tension_ppp_v1.json",
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> MioCertificate:
    """Pack a PPP report into a ``MioCertificate``."""
    stats_by_name = {item.name: item for item in report.statistics}
    strongest = stats_by_name[report.strongest_statistic]

    departure = {
        "strongest_observed_statistic": float(strongest.observed_value),
        "n_test_statistics": float(len(report.statistics)),
    }
    adequacy = {
        "corrected_tail_probability_lt_0p05": bool(report.min_corrected_p_value < 0.05),
        "corrected_tail_probability_lt_0p01": bool(report.min_corrected_p_value < 0.01),
    }
    consistency: Dict[str, float] = {
        "minimum_corrected_tail_probability": float(report.min_corrected_p_value),
    }
    for item in report.statistics:
        key = item.name.lower()
        consistency[f"{key}_observed"] = float(item.observed_value)
        consistency[f"{key}_corrected_tail_probability"] = float(item.corrected_p_value)
        consistency[f"{key}_mock_mean"] = float(item.mock_mean)
        consistency[f"{key}_mock_std"] = float(item.mock_std)
        consistency[f"{key}_n_mock"] = float(item.n_mock)

    caveats = list(domain_caveats) if domain_caveats is not None else []
    if DEFAULT_DOMAIN_CAVEAT not in caveats:
        caveats.append(DEFAULT_DOMAIN_CAVEAT)
    if _NULL_PREDICTIVE_CAVEAT not in caveats:
        caveats.append(_NULL_PREDICTIVE_CAVEAT)
    gate = _validate_null_predictive_payload(
        report,
        null_predictive_payload,
        null_mocks_calibrated=null_mocks_calibrated,
    )
    resolved_config_hash = config_hash
    resolved_input_hashes = list(input_data_hashes) if input_data_hashes else []
    if null_predictive_payload is not None:
        payload_config_hash = str(gate.metadata["config_hash"])
        payload_input_hashes = [str(item) for item in gate.metadata["input_hashes"]]
        if config_hash is not None and config_hash != payload_config_hash:
            raise ValueError("config_hash must match null_predictive_payload.config_hash")
        if input_data_hashes is not None and list(input_data_hashes) != payload_input_hashes:
            raise ValueError(
                "input_data_hashes must match null_predictive_payload.input_hashes"
            )
        resolved_config_hash = payload_config_hash
        resolved_input_hashes = payload_input_hashes
    readiness = assess_mio_readiness(
        MioPrerequisites(
            requires_covariance=gate.requires_covariance,
            has_covariance=gate.covariance_ready,
            requires_null_mocks=True,
            has_null_mocks=gate.null_mocks_ready,
            requires_sky_support=gate.requires_sky_support,
            sky_support_status=gate.sky_support_status,  # type: ignore[arg-type]
            eligible_for_production=True,
        )
    )
    adequacy["null_predictive_distribution_ready"] = bool(
        readiness.production_status == "production_candidate" and gate.ready
    )
    status_metadata = dict(gate.metadata)
    status_metadata.update(
        {
            "manifest_required_gates": list(readiness.required_gates),
            "manifest_passed_gates": list(readiness.passed_gates),
            "manifest_failed_gates": list(readiness.failed_gates),
            "required_gates": list(
                dict.fromkeys((*gate.required_gates, *readiness.required_gates))
            ),
            "passed_gates": list(
                dict.fromkeys((*gate.passed_gates, *readiness.passed_gates))
            ),
            "failed_gates": list(
                dict.fromkeys((*gate.failed_gates, *readiness.failed_gates))
            ),
            "production_status": readiness.production_status,
            "claim_tier": readiness.claim_tier,
            "public_grade_label": readiness.public_grade_label,
            "readiness_scope": "manifest_prerequisites_only_not_scientific_validation",
        }
    )

    return build_mio_certificate(
        report_type="flrw_tension",
        probe_name=probe_name,
        channel=channel,
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by=generated_by,
        input_data_hashes=resolved_input_hashes,
        config_hash=resolved_config_hash,
        htt_cross_check_suggested={
            "compare_to": "htt.core.advanced_diagnostics.posterior_predictive_report_artifact",
            "expected_relation": (
                "MIO empirical tails and HTT predictive residual alarms "
                "should agree in sign"
            ),
        },
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
        readiness=readiness,
        artifact_id="mio.flrw_tension.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "flrw_tension",
            "channel": channel,
            "certificate_status_metadata": status_metadata,
        },
    )


ARTEFACT_FILENAME = "mio_flrw_tension_ppp_v1.json"


def emit_flrw_tension_artefact(
    out_path: Path,
    observed_statistics: Mapping[str, float],
    mock_statistics: Mapping[str, Sequence[float]],
    *,
    tails: Optional[Mapping[str, str]] = None,
    probe_name: str = "FLRW",
    channel: str = "ppp",
    domain_caveats: Optional[Sequence[str]] = None,
    input_data_hashes: Optional[Sequence[str]] = None,
    null_mocks_calibrated: bool = False,
    null_predictive_payload: Mapping[str, object] | None = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> dict:
    """Evaluate PPP statistics and persist a JSON artifact."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.name.startswith("mio_"):
        raise ValueError(
            f"artefact filename must start with 'mio_' (REG-02): got {out_path.name}"
        )

    report = evaluate_flrw_tension(
        observed_statistics,
        mock_statistics,
        tails=tails,
    )
    cert = to_mio_certificate(
        report,
        probe_name=probe_name,
        channel=channel,
        domain_caveats=domain_caveats,
        input_data_hashes=input_data_hashes,
        null_mocks_calibrated=null_mocks_calibrated,
        null_predictive_payload=null_predictive_payload,
        artifact_path=str(out_path),
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
    )
    status_metadata = cert.manifest.statistics_definitions[
        "certificate_status_metadata"
    ]

    payload = {
        "schema_version": "v1",
        "look_elsewhere_method": report.look_elsewhere_method,
        "strongest_statistic": report.strongest_statistic,
        "tail_probability_summary": {
            **_tail_summary(report),
            "tail_probability_export_status": status_metadata[
                "tail_probability_export_status"
            ],
        },
        "statistics": _statistics_payload(report),
        "null_predictive_gate": dict(status_metadata),
        "null_predictive_payload": (
            dict(null_predictive_payload)
            if null_predictive_payload is not None
            else None
        ),
        "certificate": certificate_to_payload(cert),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "ARTEFACT_FILENAME",
    "DEFAULT_DOMAIN_CAVEAT",
    "FlrwPppReport",
    "FlrwPppStatistic",
    "emit_flrw_tension_artefact",
    "evaluate_flrw_tension",
    "posterior_predictive_pvalue",
    "to_mio_certificate",
]
