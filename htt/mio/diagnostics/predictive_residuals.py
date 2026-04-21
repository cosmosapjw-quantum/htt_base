"""mio.diagnostics.predictive_residuals — IM-07M predictive residual atlas.

This module now supports two layers:

1. low-level packaging of caller-supplied residual summaries;
2. live residual-slice construction from the shared VER2 prediction/data
   schema (`ObservableVector` + `HttForwardOutput`).

The resulting atlas remains diagnostic until atlas/covariance
prerequisites are explicit, and it stays advisory only: no posterior,
evidence, or truth-certification semantics are introduced here.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence

import numpy as np

from workspace.contracts import (
    AtlasEntryLite,
    HttForwardOutput,
    ObservableVector,
    TscAdequacyOverlay,
)
from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from workspace.contracts.mio_certificate import MioCertificate


DEFAULT_DOMAIN_CAVEAT = (
    "Predictive residual atlas is a diagnostic model/data comparison "
    "surface; it must not be merged with HTT posterior evidence or "
    "reinterpreted as a truth certificate."
)
SHARED_SCHEMA_DOMAIN_CAVEAT = (
    "Shared prediction/data schema is consumed for residual comparison "
    "only; model disagreement remains advisory and owner-separated."
)
SUPPORTED_SPECTRUM_CHANNELS = ("TT", "TE", "EE")


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
    """Residual-atlas summary suitable for manifest-backed export."""

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
    """Build a residual atlas from caller-supplied residual slices."""
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


def _as_float_array(values: object, *, label: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{label} must be 1-D")
    if array.size == 0:
        raise ValueError(f"{label} must be non-empty")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{label} must contain only finite values")
    return array


def _normalize_ell_bins(
    ell: np.ndarray,
    ell_bins: Sequence[tuple[int, int]] | None,
) -> tuple[tuple[int, int], ...]:
    if ell_bins is None:
        return ((int(ell[0]), int(ell[-1])),)
    normalized: list[tuple[int, int]] = []
    for lo, hi in ell_bins:
        lo_i = int(lo)
        hi_i = int(hi)
        if hi_i < lo_i:
            raise ValueError(f"ell bin upper bound must be >= lower bound: {(lo, hi)}")
        normalized.append((lo_i, hi_i))
    if not normalized:
        raise ValueError("ell_bins must be non-empty when provided")
    return tuple(normalized)


def build_residual_slices_from_shared_schema(
    observable_vector: ObservableVector,
    forward_outputs: Sequence[HttForwardOutput],
    *,
    ell_bins: Sequence[tuple[int, int]] | None = None,
) -> tuple[ResidualChannelSlice, ...]:
    """Build model/channel residual slices from shared prediction/data contracts."""
    if observable_vector.manifest.owner != "BASS":
        raise ValueError("observable_vector must be BASS-owned")
    if not forward_outputs:
        raise ValueError("forward_outputs must contain at least one model prediction")

    slices: list[ResidualChannelSlice] = []
    for forward_output in forward_outputs:
        if forward_output.manifest is not None and forward_output.manifest.owner != "BASS":
            raise ValueError("forward_outputs must remain BASS-owned theory bundles")
        ell = np.asarray(forward_output.ell, dtype=int)
        if ell.ndim != 1 or ell.size == 0:
            raise ValueError("forward_output.ell must be a non-empty 1-D integer array")
        if np.any(np.diff(ell) < 0):
            raise ValueError("forward_output.ell must be sorted in ascending order")

        channel_predictions = {
            "TT": _as_float_array(
                forward_output.C_ell_TT,
                label=f"{forward_output.model_name}.C_ell_TT",
            ),
            "TE": _as_float_array(
                forward_output.C_ell_TE,
                label=f"{forward_output.model_name}.C_ell_TE",
            ),
            "EE": _as_float_array(
                forward_output.C_ell_EE,
                label=f"{forward_output.model_name}.C_ell_EE",
            ),
        }
        bins = _normalize_ell_bins(ell, ell_bins)
        for channel in SUPPORTED_SPECTRUM_CHANNELS:
            if channel not in observable_vector.cl:
                continue
            observed = _as_float_array(
                observable_vector.cl[channel],
                label=f"observable_vector.cl[{channel!r}]",
            )
            prediction = channel_predictions[channel]
            if prediction.shape != ell.shape:
                raise ValueError(
                    f"{forward_output.model_name} {channel} prediction shape "
                    f"{prediction.shape} != ell shape {ell.shape}"
                )
            if ell[0] < 0 or int(ell[-1]) >= observed.size:
                raise ValueError(
                    f"{forward_output.model_name} {channel} ell support exceeds "
                    "observable_vector channel length"
                )
            residual = prediction - observed[ell]
            for lo, hi in bins:
                mask = (ell >= lo) & (ell <= hi)
                if not np.any(mask):
                    continue
                residual_bin = residual[mask]
                slices.append(
                    ResidualChannelSlice(
                        model_label=forward_output.model_name,
                        channel=channel,
                        ell_min=int(ell[mask][0]),
                        ell_max=int(ell[mask][-1]),
                        rms_residual=float(np.sqrt(np.mean(residual_bin ** 2))),
                        max_abs_residual=float(np.max(np.abs(residual_bin))),
                        n_modes=int(mask.sum()),
                    )
                )
    if not slices:
        raise ValueError(
            "shared-schema residual atlas found no overlapping TT/TE/EE channels"
        )
    return tuple(slices)


def build_predictive_residual_atlas_from_shared_schema(
    observable_vector: ObservableVector,
    forward_outputs: Sequence[HttForwardOutput],
    *,
    atlas_entry: AtlasEntryLite | None = None,
    ell_bins: Sequence[tuple[int, int]] | None = None,
    atlas_ref: str | None = None,
    covariance_ref: str | None = None,
) -> PredictiveResidualAtlas:
    """Build a residual atlas directly from shared BASS/HTT schema objects."""
    if atlas_entry is not None and atlas_entry.manifest.owner != "BASS":
        raise ValueError("atlas_entry must be BASS-owned")
    resolved_atlas_ref = atlas_ref
    if resolved_atlas_ref is None and atlas_entry is not None:
        resolved_atlas_ref = atlas_entry.manifest.artifact_id
    slices = build_residual_slices_from_shared_schema(
        observable_vector,
        forward_outputs,
        ell_bins=ell_bins,
    )
    return build_predictive_residual_atlas(
        slices,
        atlas_ref=resolved_atlas_ref,
        covariance_ref=covariance_ref,
    )


def _shared_schema_input_refs(
    observable_vector: ObservableVector,
    forward_outputs: Sequence[HttForwardOutput],
    *,
    atlas_entry: AtlasEntryLite | None = None,
) -> list[str]:
    refs = [observable_vector.manifest.artifact_id]
    refs.extend(
        output.manifest.artifact_id
        if output.manifest is not None
        else f"htt_forward:{output.model_name}:{output.config_hash}"
        for output in forward_outputs
    )
    if atlas_entry is not None:
        refs.append(atlas_entry.manifest.artifact_id)
    return list(dict.fromkeys(refs))


def to_mio_certificate(
    atlas: PredictiveResidualAtlas,
    *,
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.diagnostics.predictive_residuals v0.2",
    input_data_hashes: Optional[Sequence[str]] = None,
    config_hash: Optional[str] = None,
    has_atlas: Optional[bool] = None,
    has_covariance: Optional[bool] = None,
    artifact_path: str = "artifacts/mio/mio_predictive_residuals_v1.json",
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> MioCertificate:
    """Package a residual atlas into a manifest-backed certificate."""
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
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
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


def emit_predictive_residuals_shared_schema_artefact(
    out_path: str | Path,
    observable_vector: ObservableVector,
    forward_outputs: Sequence[HttForwardOutput],
    *,
    atlas_entry: AtlasEntryLite | None = None,
    ell_bins: Sequence[tuple[int, int]] | None = None,
    atlas_ref: str | None = None,
    covariance_ref: str | None = None,
    domain_caveats: Optional[Sequence[str]] = None,
    input_data_hashes: Optional[Sequence[str]] = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> dict:
    """Write a predictive-residual artifact from shared prediction/data schema."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.name.startswith("mio_"):
        raise ValueError("MIO artefact filename must start with 'mio_'")

    atlas = build_predictive_residual_atlas_from_shared_schema(
        observable_vector,
        forward_outputs,
        atlas_entry=atlas_entry,
        ell_bins=ell_bins,
        atlas_ref=atlas_ref,
        covariance_ref=covariance_ref,
    )
    caveats = list(domain_caveats) if domain_caveats is not None else []
    if SHARED_SCHEMA_DOMAIN_CAVEAT not in caveats:
        caveats.append(SHARED_SCHEMA_DOMAIN_CAVEAT)
    cert = to_mio_certificate(
        atlas,
        domain_caveats=caveats,
        input_data_hashes=(
            list(input_data_hashes)
            if input_data_hashes is not None
            else _shared_schema_input_refs(
                observable_vector,
                forward_outputs,
                atlas_entry=atlas_entry,
            )
        ),
        artifact_path=str(out),
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
    )
    payload = {
        "artifact_name": ARTEFACT_FILENAME,
        "shared_schema_inputs": {
            "observable_vector_ref": observable_vector.manifest.artifact_id,
            "forward_output_refs": [
                output.manifest.artifact_id
                if output.manifest is not None
                else f"htt_forward:{output.model_name}:{output.config_hash}"
                for output in forward_outputs
            ],
            "atlas_entry_ref": (
                atlas_entry.manifest.artifact_id if atlas_entry is not None else None
            ),
        },
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
    "build_predictive_residual_atlas_from_shared_schema",
    "build_residual_slices_from_shared_schema",
    "emit_predictive_residuals_artefact",
    "emit_predictive_residuals_shared_schema_artefact",
    "SHARED_SCHEMA_DOMAIN_CAVEAT",
    "SUPPORTED_SPECTRUM_CHANNELS",
    "to_mio_certificate",
]
