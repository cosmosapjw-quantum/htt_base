"""VER2 `ObservableVector` extraction shells."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np

from common.contracts import ObservableVector, SkySupport, SolverCoreOutput

from bass.observational._manifest import (
    derive_manifest,
    sky_support_metadata,
    stable_payload_hash,
)
from bass.observational.covariance_sparse import (
    build_covariance_feature_summary,
    build_sparse_covariance_proxy,
)

__all__ = ["build_observable_vector_from_solver_output"]


def _mapping_or_none(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _default_cl(
    solver_output: SolverCoreOutput,
    covariance_bundle: Mapping[str, object] | None,
) -> dict[str, object]:
    if covariance_bundle is not None and isinstance(covariance_bundle.get("C_ell"), Mapping):
        return {
            channel: np.asarray(values, dtype=float)
            for channel, values in covariance_bundle["C_ell"].items()  # type: ignore[index]
        }
    return {}


def _default_alm_features(
    solver_output: SolverCoreOutput,
    covariance_bundle: Mapping[str, object] | None,
) -> dict[str, object]:
    preferred_axis = None
    if covariance_bundle is not None and covariance_bundle.get("preferred_axis") is not None:
        preferred_axis = tuple(
            float(value)
            for value in np.asarray(covariance_bundle["preferred_axis"], dtype=float)
        )
    return {
        "harmonic_basis": str(solver_output.metadata["harmonic_basis"]),
        "eb_sign_convention": str(solver_output.metadata["eb_sign_convention"]),
        "observer_neutral": bool(solver_output.metadata.get("observer_neutral", True)),
        "preferred_axis": preferred_axis,
        "deterministic_template_present": solver_output.deterministic_template is not None,
    }


def _default_scan_volume(
    solver_output: SolverCoreOutput,
    sky_support: SkySupport,
    *,
    ell_max: int,
    channels: tuple[str, ...],
) -> dict[str, object]:
    base = {
        "definition": "lowell_observable_vector_skeleton",
        "ell_max": ell_max,
        "channels": list(channels),
        "harmonic_basis": str(solver_output.metadata["harmonic_basis"]),
        "selection_mode": sky_support.selection_mode,
        "thomson_mode": str(solver_output.metadata["thomson_mode"]),
    }
    base["scan_volume_hash"] = stable_payload_hash(base)
    return base


def build_observable_vector_from_solver_output(
    solver_output: SolverCoreOutput,
    *,
    sky_support: SkySupport,
    cl: Mapping[str, object] | None = None,
    alm_features: Mapping[str, object] | None = None,
    biposh: Mapping[str, object] | None = None,
    template_fit: Mapping[str, object] | None = None,
    covariance_features: Mapping[str, object] | None = None,
    scan_volume: Mapping[str, object] | None = None,
) -> ObservableVector:
    """Build a descriptive low-ell observable shell from a solver output."""
    if solver_output.manifest.owner != "BASS":
        raise ValueError("ObservableVector sources must be BASS-owned")
    covariance_bundle = _mapping_or_none(solver_output.anisotropic_covariance)
    cl_payload = dict(cl) if cl is not None else _default_cl(solver_output, covariance_bundle)
    channels = tuple(
        channel
        for channel in ("TT", "TE", "EE", "BB", "TB", "EB")
        if channel in cl_payload
    ) or ("scalar_summary",)
    ell_max = int(solver_output.metadata.get("multipole_cutoff", 0))
    if cl_payload:
        ell_max = max(
            ell_max,
            max(int(np.asarray(values).shape[0] - 1) for values in cl_payload.values()),
        )
    biposh_payload = dict(biposh) if biposh is not None else None
    covariance_payload = dict(covariance_features) if covariance_features is not None else None
    if covariance_bundle is not None:
        if biposh_payload is None:
            biposh_payload = build_sparse_covariance_proxy(
                covariance_bundle,
                harmonic_convention=str(solver_output.metadata["harmonic_basis"]),
            )
        if covariance_payload is None:
            covariance_payload = build_covariance_feature_summary(
                covariance_bundle,
                harmonic_convention=str(solver_output.metadata["harmonic_basis"]),
            )
    template_payload = dict(template_fit) if template_fit is not None else None
    if template_payload is None and solver_output.deterministic_template is not None:
        template_payload = dict(solver_output.deterministic_template)
        template_payload.setdefault("descriptive_only", True)
    feature_payload = (
        dict(alm_features)
        if alm_features is not None
        else _default_alm_features(solver_output, covariance_bundle)
    )
    scan_payload = (
        dict(scan_volume)
        if scan_volume is not None
        else _default_scan_volume(
            solver_output,
            sky_support,
            ell_max=ell_max,
            channels=channels,
        )
    )
    scan_payload.setdefault("scan_volume_hash", stable_payload_hash(scan_payload))
    artifact_id = f"{solver_output.manifest.artifact_id}.observable_vector"
    artifact_path = (
        f"artifacts/bass/{artifact_id.replace('.', '_')}.json"
    )
    manifest = derive_manifest(
        solver_output.manifest,
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner="BASS",
        implementation_scope="bass_py",
        claim_tier="conditional",
        production_status="diagnostic_only",
        caveats=(
            "descriptive_only_observable_substrate",
            "no_posterior_or_evidence_semantics",
        ),
        statistics_definitions={
            "surface": "ObservableVector",
            "channels": list(channels),
            "ell_max": ell_max,
            "scan_volume_hash": str(scan_payload["scan_volume_hash"]),
            "sky_support": sky_support_metadata(sky_support),
        },
    )
    return ObservableVector(
        ell_max=ell_max,
        channels=channels,
        cl=cl_payload,
        alm_features=feature_payload,
        biposh=biposh_payload,
        template_fit=template_payload,
        covariance_features=covariance_payload,
        scan_volume=scan_payload,
        sky_support=sky_support,
        manifest=manifest,
    )
