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

from common.statistical_foundations import (
    BC1_LEGACY_PROJECTION,
    BC2_NO_REPRESENTATION_PROMOTION,
    DiagnosticScalarReport,
    LegacyProjectionReport,
    ScalarRange,
)
from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.tsc_overlay import TscAdequacyOverlay


DEFAULT_DOMAIN_CAVEAT = (
    "x_C is BC1_LEGACY_PROJECTION: an exact signed Gauss/Friedmann budget "
    "coordinate under its recorded inputs, not a departure distance, "
    "identified estimand, probability, occupancy, or evidence."
)

_XC_ALLOWED_USE = (
    "historical reproduction",
    "signed budget-coordinate reporting",
    "component bookkeeping audit",
)
_XC_FORBIDDEN_USE = (
    "departure distance",
    "identified estimand",
    "probability",
    "occupancy",
    "evidence",
    "claim-tier promotion",
    "family identification",
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
        sigma_names = {
            "sigma2_mio_sigma",
            "w2_sigma",
            "omega_tilt_sigma",
            "omega_k_aniso_sigma",
        }
        for name in (
            "sigma2_mio",
            "sigma2_mio_sigma",
            "w2",
            "w2_sigma",
            "omega_tilt",
            "omega_tilt_sigma",
            "omega_k_aniso",
            "omega_k_aniso_sigma",
        ):
            raw = getattr(self, name)
            if isinstance(raw, bool) or not isinstance(raw, (int, float)):
                raise TypeError(f"{name} must be a finite real number")
            value = float(raw)
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite; got {value}")
            if name in sigma_names and value < 0.0:
                raise ValueError(f"{name} must be >= 0; got {value}")
            object.__setattr__(self, name, value)


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
    legacy_projection: LegacyProjectionReport
    owner: str = "MIO"
    status: str = "diagnostic_only"
    classification: str = BC1_LEGACY_PROJECTION
    representation_policy: str = BC2_NO_REPRESENTATION_PROMOTION
    allowed_use: tuple[str, ...] = _XC_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _XC_FORBIDDEN_USE


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
    """Return the unchanged value inside an explicit BC1/BC2 report."""
    x_c, sigma_x = departure_parameter_estimate(inputs)
    significance = abs(x_c) / sigma_x if sigma_x > 0.0 else float("inf")
    legacy_projection = LegacyProjectionReport(
        x_C=DiagnosticScalarReport(
            name="x_C",
            value_range=ScalarRange(x_c, x_c),
            status=BC1_LEGACY_PROJECTION,
            null_calibration="not_applicable_legacy_signed_coordinate",
        )
    )
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
        legacy_projection=legacy_projection,
    )


def to_mio_certificate(
    report: XCReport,
    *,
    probe_name: str = "FLRW",
    channel: str = "xc_legacy_projection",
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.tension.xc_estimator v0.2",
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
    # A z-like component-uncertainty ratio is retained in ``departure`` for
    # byte/value compatibility, but it is not an adequacy or claim-promotion
    # gate.  BC1/BC2 therefore authorizes no sigma-threshold flags.
    adequacy: dict[str, bool] = {}
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
        report_type="legacy_projection",
        probe_name=probe_name,
        channel=channel,
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by=generated_by,
        input_data_hashes=list(input_data_hashes) if input_data_hashes else [],
        config_hash=config_hash,
        htt_cross_check_suggested={
            "compare_to": "htt.core.advanced_diagnostics.redshift_tomography_report_artifact",
            "expected_relation": (
                "component bookkeeping audit only; no non-zero-x_C tension, "
                "distance, occupancy, source, or morphology implication"
            ),
        },
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
        readiness=readiness,
        artifact_id="mio.xc_direct_estimate.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "legacy_projection",
            "channel": channel,
            "owner": report.owner,
            "status": report.status,
            "classification": report.classification,
            "representation_policy": report.representation_policy,
            "allowed_use": list(report.allowed_use),
            "forbidden_use": list(report.forbidden_use),
        },
    )


XC_ARTEFACT_FILENAME = "mio_xc_direct_estimate_v1.json"


def emit_xc_direct_estimate_artefact(
    out_path: Path,
    inputs: XCInputs,
    *,
    probe_name: str = "FLRW",
    channel: str = "xc_legacy_projection",
    domain_caveats: Optional[Sequence[str]] = None,
    input_data_hashes: Optional[Sequence[str]] = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
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
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
    )

    payload = {
        "schema_version": "v2",
        "inputs": asdict(inputs),
        "report": asdict(report),
        "certificate": certificate_to_payload(cert),
    }
    payload = json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))
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
