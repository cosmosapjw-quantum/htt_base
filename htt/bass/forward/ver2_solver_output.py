"""VER2 observer-neutral solver-output builders for the BASS S3 lane."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from common.contracts import ArtifactManifest, SolverCoreOutput

from bass.los.ver2_source_propagator import SourcePropagatorConfig
from bass.runtime.ver2_execution import RuntimeControlBlock, SolverFeatureFlags

__all__ = [
    "BassReleaseMetadata",
    "build_solver_core_output",
    "solver_core_output_to_payload",
    "solver_core_output_from_payload",
]


@dataclass(frozen=True)
class BassReleaseMetadata:
    """Release and reproducibility metadata for one solver run."""

    release_stage: str
    run_label: str
    config_hash: str
    code_version: str
    schema_version: str
    git_commit: str | None
    random_seed: int | None = None

    def __post_init__(self) -> None:
        if not self.release_stage:
            raise ValueError("release_stage must be non-empty")
        if not self.run_label:
            raise ValueError("run_label must be non-empty")
        if not self.config_hash:
            raise ValueError("config_hash must be non-empty")
        if not self.code_version:
            raise ValueError("code_version must be non-empty")
        if not self.schema_version:
            raise ValueError("schema_version must be non-empty")
        if self.random_seed is not None and self.random_seed < 0:
            raise ValueError("random_seed must be non-negative when provided")


def build_solver_core_output(
    *,
    manifest: ArtifactManifest,
    bianchi_type: str,
    tilt_enabled: bool,
    harmonic_basis: str,
    eb_sign_convention: str,
    thomson_mode: str,
    runtime_controls: RuntimeControlBlock,
    feature_flags: SolverFeatureFlags,
    propagator: SourcePropagatorConfig,
    release: BassReleaseMetadata,
    alm_T: object | None = None,
    alm_E: object | None = None,
    alm_B: object | None = None,
    map_T: object | None = None,
    map_Q: object | None = None,
    map_U: object | None = None,
    deterministic_template: dict[str, Any] | None = None,
    anisotropic_covariance: object | None = None,
) -> SolverCoreOutput:
    """Build the canonical observer-neutral `SolverCoreOutput` shell."""
    if manifest.owner != "BASS":
        raise ValueError("SolverCoreOutput manifests must be owned by BASS")
    metadata = {
        "bianchi_type": bianchi_type,
        "harmonic_basis": harmonic_basis,
        "eb_sign_convention": eb_sign_convention,
        "multipole_cutoff": runtime_controls.multipole_cutoff,
        "tilt_enabled": tilt_enabled,
        "thomson_mode": thomson_mode,
        "solver_tier": runtime_controls.tier.value,
        "integrator_family": runtime_controls.integrator_family.value,
        "coupling_mode": runtime_controls.coupling_mode.value,
        "propagator_mode": propagator.mode.value,
        "feature_flags": {key: value.value for key, value in asdict(feature_flags).items()},
        "release_stage": release.release_stage,
        "run_label": release.run_label,
        "observer_neutral": True,
        "forbidden_products": ("posterior", "likelihood", "p_value"),
    }
    return SolverCoreOutput(
        alm_T=alm_T,
        alm_E=alm_E,
        alm_B=alm_B,
        map_T=map_T,
        map_Q=map_Q,
        map_U=map_U,
        deterministic_template=deterministic_template,
        anisotropic_covariance=anisotropic_covariance,
        metadata=metadata,
        manifest=manifest,
    )


def solver_core_output_to_payload(output: SolverCoreOutput) -> dict[str, Any]:
    """Return a JSON-ready payload for a neutral solver output."""
    return {
        "alm_T": output.alm_T,
        "alm_E": output.alm_E,
        "alm_B": output.alm_B,
        "map_T": output.map_T,
        "map_Q": output.map_Q,
        "map_U": output.map_U,
        "deterministic_template": output.deterministic_template,
        "anisotropic_covariance": output.anisotropic_covariance,
        "metadata": dict(output.metadata),
        "manifest": asdict(output.manifest),
    }


def solver_core_output_from_payload(payload: dict[str, Any]) -> SolverCoreOutput:
    """Reconstruct a `SolverCoreOutput` from a serialized payload."""
    manifest = ArtifactManifest(**payload["manifest"])
    return SolverCoreOutput(
        alm_T=payload.get("alm_T"),
        alm_E=payload.get("alm_E"),
        alm_B=payload.get("alm_B"),
        map_T=payload.get("map_T"),
        map_Q=payload.get("map_Q"),
        map_U=payload.get("map_U"),
        deterministic_template=payload.get("deterministic_template"),
        anisotropic_covariance=payload.get("anisotropic_covariance"),
        metadata=payload["metadata"],
        manifest=manifest,
    )
