"""mio.tension.flrw_tension — HJ-03a FLRW-null PPP helpers.

Parent plan: ``htt/docs/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md`` §4.5.3.3.

This module is deliberately narrow: it evaluates posterior-predictive
p-values from caller-supplied observed test statistics and caller-
supplied FLRW mock ensembles. The mock generator stays outside MIO so
this layer remains a pure diagnostic/reporting surface.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Mapping, Optional, Sequence

import numpy as np

from mio.interface.mio_certificate import build_mio_certificate
from workspace.contracts.mio_certificate import MioCertificate


DEFAULT_DOMAIN_CAVEAT = (
    "FLRW PPP requires an externally generated FLRW mock ensemble; "
    "this module only scores caller-supplied statistics."
)


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
    """Return the PPP p-value using additive smoothing.

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


def to_mio_certificate(
    report: FlrwPppReport,
    *,
    probe_name: str = "FLRW",
    channel: str = "ppp",
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.tension.flrw_tension v0.1",
    input_data_hashes: Optional[Sequence[str]] = None,
    config_hash: Optional[str] = None,
) -> MioCertificate:
    """Pack a PPP report into a ``MioCertificate``."""
    stats_by_name = {item.name: item for item in report.statistics}
    strongest = stats_by_name[report.strongest_statistic]

    departure = {
        "min_raw_ppp_pvalue": float(report.min_raw_p_value),
        "min_corrected_ppp_pvalue": float(report.min_corrected_p_value),
        "strongest_observed_statistic": float(strongest.observed_value),
        "n_test_statistics": float(len(report.statistics)),
    }
    adequacy = {
        "ppp_raw_p_lt_0p05": bool(report.min_raw_p_value < 0.05),
        "ppp_corrected_p_lt_0p05": bool(report.min_corrected_p_value < 0.05),
        "ppp_corrected_p_lt_0p01": bool(report.min_corrected_p_value < 0.01),
    }
    consistency: Dict[str, float] = {}
    for item in report.statistics:
        key = item.name.lower()
        consistency[f"{key}_observed"] = float(item.observed_value)
        consistency[f"{key}_pvalue"] = float(item.p_value)
        consistency[f"{key}_corrected_pvalue"] = float(item.corrected_p_value)
        consistency[f"{key}_mock_mean"] = float(item.mock_mean)
        consistency[f"{key}_mock_std"] = float(item.mock_std)
        consistency[f"{key}_n_mock"] = float(item.n_mock)

    caveats = list(domain_caveats) if domain_caveats is not None else []
    if DEFAULT_DOMAIN_CAVEAT not in caveats:
        caveats.append(DEFAULT_DOMAIN_CAVEAT)

    return build_mio_certificate(
        report_type="flrw_tension",
        probe_name=probe_name,
        channel=channel,
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="theory-approximate",
        generated_by=generated_by,
        input_data_hashes=list(input_data_hashes) if input_data_hashes else [],
        config_hash=config_hash,
        htt_cross_check_suggested={
            "compare_to": "htt.core.advanced_diagnostics.posterior_predictive_report_artifact",
            "expected_relation": "MIO PPP and HTT predictive residual alarms should agree in sign",
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
    )

    payload = {
        "schema_version": "v1",
        "look_elsewhere_method": report.look_elsewhere_method,
        "strongest_statistic": report.strongest_statistic,
        "min_raw_p_value": report.min_raw_p_value,
        "min_corrected_p_value": report.min_corrected_p_value,
        "statistics": [asdict(item) for item in report.statistics],
        "certificate": {
            "report_type": cert.report_type,
            "probe_name": cert.probe_name,
            "channel": cert.channel,
            "departure_variables": cert.departure_variables,
            "adequacy_indicators": cert.adequacy_indicators,
            "consistency_metrics": cert.consistency_metrics,
            "domain_caveats": cert.domain_caveats,
            "reduction_status": cert.reduction_status,
            "generated_by": cert.generated_by,
            "git_commit": cert.git_commit,
            "config_hash": cert.config_hash,
        },
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
