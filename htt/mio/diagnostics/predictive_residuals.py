"""mio.diagnostics.predictive_residuals — SK-07M residual-atlas skeleton.

This module intentionally stops at packaging and status plumbing. It
accepts caller-supplied residual summaries, records the worst model /
channel slices, and emits a manifest-backed `MioCertificate` whose
production status is blocked until atlas and covariance prerequisites are
explicitly declared.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional, Sequence

from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from workspace.contracts.mio_certificate import MioCertificate


DEFAULT_DOMAIN_CAVEAT = (
    "Predictive residual atlas is a model-agnostic residual shell; "
    "final ranking remains blocked until atlas and covariance prerequisites "
    "are explicitly declared."
)


@dataclass(frozen=True)
class ResidualChannelSlice:
    """One model / channel / multipole residual summary."""

    model_label: str
    channel: str
    ell_min: int
    ell_max: int
    rms_residual: float
    max_abs_residual: float
    n_modes: int

    def __post_init__(self) -> None:
        if self.ell_max < self.ell_min:
            raise ValueError("ell_max must be >= ell_min")
        if self.n_modes <= 0:
            raise ValueError("n_modes must be positive")


@dataclass(frozen=True)
class PredictiveResidualAtlas:
    """Skeleton residual-atlas summary suitable for manifest-backed export."""

    slices: tuple[ResidualChannelSlice, ...]
    atlas_ref: str | None
    covariance_ref: str | None
    worst_model_label: str
    worst_channel: str
    worst_max_abs_residual: float
    mean_rms_residual: float


def build_predictive_residual_atlas(
    slices: Sequence[ResidualChannelSlice],
    *,
    atlas_ref: str | None = None,
    covariance_ref: str | None = None,
) -> PredictiveResidualAtlas:
    """Build a residual-atlas shell from caller-supplied residual slices."""
    if not slices:
        raise ValueError("slices must contain at least one residual summary")
    slice_tuple = tuple(slices)
    worst = max(
        slice_tuple,
        key=lambda item: (abs(item.max_abs_residual), item.model_label, item.channel),
    )
    mean_rms = sum(float(item.rms_residual) for item in slice_tuple) / float(len(slice_tuple))
    return PredictiveResidualAtlas(
        slices=slice_tuple,
        atlas_ref=atlas_ref,
        covariance_ref=covariance_ref,
        worst_model_label=worst.model_label,
        worst_channel=worst.channel,
        worst_max_abs_residual=float(worst.max_abs_residual),
        mean_rms_residual=float(mean_rms),
    )


def to_mio_certificate(
    atlas: PredictiveResidualAtlas,
    *,
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.diagnostics.predictive_residuals v0.1-skeleton",
    input_data_hashes: Optional[Sequence[str]] = None,
    config_hash: Optional[str] = None,
    has_atlas: Optional[bool] = None,
    has_covariance: Optional[bool] = None,
    artifact_path: str = "artifacts/mio/mio_predictive_residuals_v1.json",
) -> MioCertificate:
    """Package a residual-atlas shell into a manifest-backed certificate."""
    atlas_ready = atlas.atlas_ref is not None if has_atlas is None else bool(has_atlas)
    covariance_ready = (
        atlas.covariance_ref is not None if has_covariance is None else bool(has_covariance)
    )
    readiness = assess_mio_readiness(
        MioPrerequisites(
            requires_atlas=True,
            has_atlas=atlas_ready,
            requires_covariance=True,
            has_covariance=covariance_ready,
            eligible_for_production=True,
        )
    )
    departure = {
        "worst_max_abs_residual": float(atlas.worst_max_abs_residual),
        "mean_rms_residual": float(atlas.mean_rms_residual),
        "n_slices": float(len(atlas.slices)),
    }
    adequacy = {
        "atlas_ready": bool(atlas_ready),
        "covariance_ready": bool(covariance_ready),
    }
    consistency = {
        "n_models": float(len({item.model_label for item in atlas.slices})),
        "n_channels": float(len({item.channel for item in atlas.slices})),
    }
    for index, item in enumerate(atlas.slices):
        prefix = f"slice_{index}"
        consistency[f"{prefix}_rms"] = float(item.rms_residual)
        consistency[f"{prefix}_max_abs"] = float(item.max_abs_residual)
        consistency[f"{prefix}_n_modes"] = float(item.n_modes)

    caveats = list(domain_caveats) if domain_caveats is not None else []
    if DEFAULT_DOMAIN_CAVEAT not in caveats:
        caveats.append(DEFAULT_DOMAIN_CAVEAT)

    return build_mio_certificate(
        report_type="residual_atlas",
        probe_name="model_agnostic",
        channel="predictive_residuals",
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by=generated_by,
        input_data_hashes=list(input_data_hashes) if input_data_hashes else [],
        config_hash=config_hash,
        htt_cross_check_suggested={
            "compare_to": "htt.core.advanced_diagnostics.posterior_predictive_report_artifact",
            "expected_relation": "large residual slices should line up with HTT posterior-predictive stress points",
        },
        readiness=readiness,
        artifact_id="mio.predictive_residuals.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "residual_atlas",
            "channel": "predictive_residuals",
        },
    )


ARTEFACT_FILENAME = "mio_predictive_residuals_v1.json"


def emit_predictive_residuals_artefact(
    out_path: str | Path,
    slices: Sequence[ResidualChannelSlice],
    *,
    atlas_ref: str | None = None,
    covariance_ref: str | None = None,
    domain_caveats: Optional[Sequence[str]] = None,
    input_data_hashes: Optional[Sequence[str]] = None,
) -> dict:
    """Write a residual-atlas artifact from caller-supplied residual slices."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.name.startswith("mio_"):
        raise ValueError("MIO artefact filename must start with 'mio_'")

    atlas = build_predictive_residual_atlas(
        slices,
        atlas_ref=atlas_ref,
        covariance_ref=covariance_ref,
    )
    cert = to_mio_certificate(
        atlas,
        domain_caveats=domain_caveats,
        input_data_hashes=input_data_hashes,
        artifact_path=str(out),
    )
    payload = {
        "artifact_name": ARTEFACT_FILENAME,
        "atlas": {
            "atlas_ref": atlas.atlas_ref,
            "covariance_ref": atlas.covariance_ref,
            "worst_model_label": atlas.worst_model_label,
            "worst_channel": atlas.worst_channel,
            "worst_max_abs_residual": atlas.worst_max_abs_residual,
            "mean_rms_residual": atlas.mean_rms_residual,
            "slices": [asdict(item) for item in atlas.slices],
        },
        "certificate": certificate_to_payload(cert),
    }
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "ARTEFACT_FILENAME",
    "DEFAULT_DOMAIN_CAVEAT",
    "PredictiveResidualAtlas",
    "ResidualChannelSlice",
    "build_predictive_residual_atlas",
    "emit_predictive_residuals_artefact",
    "to_mio_certificate",
]
