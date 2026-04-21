"""mio.tension.xc_estimator — HJ-03b direct ``x_C`` estimator.

Parent plan: ``htt/docs/BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md`` §4.5.3.3.

The direct estimate follows the plan-level decomposition

    x_C = Σ²_MIO - W² + Ω_tilt + Ω_{k,aniso}

with uncertainties propagated in quadrature. This stays deliberately
agnostic about where the four ingredients came from; upstream HTT/TSC
surfaces are responsible for producing those calibrated components.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.tsc_overlay import TscAdequacyOverlay


DEFAULT_DOMAIN_CAVEAT = (
    "x_C is a transfer-level composite estimate; upstream component "
    "calibration must be validated separately."
)


@dataclass(frozen=True)
class XCInputs:
    """Inputs to the direct ``x_C`` estimator."""

    sigma2_mio: float
    sigma2_mio_sigma: float
    w2: float = 0.0
    w2_sigma: float = 0.0
    omega_tilt: float = 0.0
    omega_tilt_sigma: float = 0.0
    omega_k_aniso: float = 0.0
    omega_k_aniso_sigma: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "sigma2_mio_sigma",
            "w2_sigma",
            "omega_tilt_sigma",
            "omega_k_aniso_sigma",
        ):
            value = float(getattr(self, name))
            if value < 0.0:
                raise ValueError(f"{name} must be >= 0; got {value}")


@dataclass(frozen=True)
class XCReport:
    """Direct ``x_C`` estimate and its propagated uncertainty."""

    x_c: float
    sigma_x: float
    significance_sigma: float
    sigma2_mio: float
    w2: float
    omega_tilt: float
    omega_k_aniso: float
    sigma2_mio_sigma: float
    w2_sigma: float
    omega_tilt_sigma: float
    omega_k_aniso_sigma: float


def departure_parameter_estimate(inputs: XCInputs) -> Tuple[float, float]:
    """Return ``(x_C, sigma_x)`` from the direct-estimator ingredients."""
    x_c = (
        float(inputs.sigma2_mio)
        - float(inputs.w2)
        + float(inputs.omega_tilt)
        + float(inputs.omega_k_aniso)
    )
    sigma_x = math.sqrt(
        float(inputs.sigma2_mio_sigma) ** 2
        + float(inputs.w2_sigma) ** 2
        + float(inputs.omega_tilt_sigma) ** 2
        + float(inputs.omega_k_aniso_sigma) ** 2
    )
    return float(x_c), float(sigma_x)


def estimate_xc_report(inputs: XCInputs) -> XCReport:
    """Return the full direct-estimate report."""
    x_c, sigma_x = departure_parameter_estimate(inputs)
    significance = abs(x_c) / sigma_x if sigma_x > 0.0 else float("inf")
    return XCReport(
        x_c=x_c,
        sigma_x=sigma_x,
        significance_sigma=float(significance),
        sigma2_mio=float(inputs.sigma2_mio),
        w2=float(inputs.w2),
        omega_tilt=float(inputs.omega_tilt),
        omega_k_aniso=float(inputs.omega_k_aniso),
        sigma2_mio_sigma=float(inputs.sigma2_mio_sigma),
        w2_sigma=float(inputs.w2_sigma),
        omega_tilt_sigma=float(inputs.omega_tilt_sigma),
        omega_k_aniso_sigma=float(inputs.omega_k_aniso_sigma),
    )


def to_mio_certificate(
    report: XCReport,
    *,
    probe_name: str = "FLRW",
    channel: str = "xc_direct",
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.tension.xc_estimator v0.1",
    input_data_hashes: Optional[Sequence[str]] = None,
    config_hash: Optional[str] = None,
    artifact_path: str = "artifacts/mio/mio_xc_direct_estimate_v1.json",
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> MioCertificate:
    """Pack an ``XCReport`` into a ``MioCertificate``."""
    departure = {
        "x_C": float(report.x_c),
        "x_C_sigma": float(report.sigma_x),
        "x_C_significance_sigma": float(report.significance_sigma),
    }
    adequacy = {
        "x_C_abs_gt_2sigma": bool(report.significance_sigma >= 2.0),
        "x_C_abs_gt_3sigma": bool(report.significance_sigma >= 3.0),
    }
    consistency = {
        "sigma2_mio": float(report.sigma2_mio),
        "w2": float(report.w2),
        "omega_tilt": float(report.omega_tilt),
        "omega_k_aniso": float(report.omega_k_aniso),
        "sigma2_mio_sigma": float(report.sigma2_mio_sigma),
        "w2_sigma": float(report.w2_sigma),
        "omega_tilt_sigma": float(report.omega_tilt_sigma),
        "omega_k_aniso_sigma": float(report.omega_k_aniso_sigma),
    }

    caveats = list(domain_caveats) if domain_caveats is not None else []
    if DEFAULT_DOMAIN_CAVEAT not in caveats:
        caveats.append(DEFAULT_DOMAIN_CAVEAT)
    readiness = assess_mio_readiness(MioPrerequisites(eligible_for_production=False))

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
            "compare_to": "htt.core.advanced_diagnostics.redshift_tomography_report_artifact",
            "expected_relation": "non-zero x_C should coincide with directional-depth tension, not replace it",
        },
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
        readiness=readiness,
        artifact_id="mio.xc_direct_estimate.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "flrw_tension",
            "channel": channel,
        },
    )


XC_ARTEFACT_FILENAME = "mio_xc_direct_estimate_v1.json"


def emit_xc_direct_estimate_artefact(
    out_path: Path,
    inputs: XCInputs,
    *,
    probe_name: str = "FLRW",
    channel: str = "xc_direct",
    domain_caveats: Optional[Sequence[str]] = None,
    input_data_hashes: Optional[Sequence[str]] = None,
) -> dict:
    """Evaluate the direct estimator and persist a JSON artifact."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.name.startswith("mio_"):
        raise ValueError(
            f"artefact filename must start with 'mio_' (REG-02): got {out_path.name}"
        )

    report = estimate_xc_report(inputs)
    cert = to_mio_certificate(
        report,
        probe_name=probe_name,
        channel=channel,
        domain_caveats=domain_caveats,
        input_data_hashes=input_data_hashes,
        artifact_path=str(out_path),
    )

    payload = {
        "schema_version": "v1",
        "inputs": asdict(inputs),
        "report": asdict(report),
        "certificate": certificate_to_payload(cert),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "DEFAULT_DOMAIN_CAVEAT",
    "XC_ARTEFACT_FILENAME",
    "XCInputs",
    "XCReport",
    "departure_parameter_estimate",
    "emit_xc_direct_estimate_artefact",
    "estimate_xc_report",
    "to_mio_certificate",
]
