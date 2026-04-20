"""VER2 `AtlasEntryLite` producer shells."""
from __future__ import annotations

from collections.abc import Mapping

from common.contracts import AtlasEntryLite, ObservableVector, SolverCoreOutput

from bass.observational._manifest import derive_manifest, sky_support_metadata

__all__ = ["build_atlas_entry_lite"]


def _coerce_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def build_atlas_entry_lite(
    solver_output: SolverCoreOutput,
    observable_vector: ObservableVector,
    *,
    atlas_id: str | None = None,
    theory_family: str | None = None,
    geometry_params: Mapping[str, float] | None = None,
    kinematic_params: Mapping[str, float] | None = None,
    tilt_params: Mapping[str, float] | None = None,
    response_blocks: Mapping[str, object] | None = None,
    validity_domain: Mapping[str, object] | None = None,
    interpolation_status: str = "skeleton_pending_calibration",
) -> AtlasEntryLite:
    """Build a low-footprint theory atlas shell from BASS outputs."""
    if solver_output.manifest.owner != "BASS":
        raise ValueError("AtlasEntryLite sources must be BASS-owned")
    if observable_vector.manifest.owner != "BASS":
        raise ValueError("AtlasEntryLite observable vectors must be BASS-owned")
    covariance_bundle = (
        dict(solver_output.anisotropic_covariance)
        if isinstance(solver_output.anisotropic_covariance, Mapping)
        else {}
    )
    response_payload = (
        dict(response_blocks)
        if response_blocks is not None
        else {
            "R_sigma_proxy": covariance_bundle.get("off_diagonal_blocks", {}),
            "R_covariance_proxy": covariance_bundle.get("anisotropy_tensor"),
        }
    )
    validity_payload = (
        dict(validity_domain)
        if validity_domain is not None
        else {
            "multipole_cutoff": int(solver_output.metadata["multipole_cutoff"]),
            "harmonic_basis": str(solver_output.metadata["harmonic_basis"]),
            "selection_mode": observable_vector.sky_support.selection_mode,
            "sky_support": sky_support_metadata(observable_vector.sky_support),
        }
    )
    atlas_name = atlas_id or f"{solver_output.manifest.artifact_id}.atlas_lite"
    manifest = derive_manifest(
        solver_output.manifest,
        artifact_id=atlas_name,
        artifact_path=f"artifacts/bass/{atlas_name.replace('.', '_')}.json",
        owner="BASS",
        implementation_scope="bass_py",
        claim_tier="conditional",
        production_status="diagnostic_only",
        caveats=(
            "theory_side_substrate_not_observational_data",
            "interpolation_only_not_posterior_update",
        ),
        statistics_definitions={
            "surface": "AtlasEntryLite",
            "sky_support": sky_support_metadata(observable_vector.sky_support),
        },
        extra_input_hashes=(observable_vector.manifest.artifact_id,),
    )
    return AtlasEntryLite(
        atlas_id=atlas_name,
        theory_family=theory_family or str(solver_output.metadata["bianchi_type"]),
        geometry_params=dict(geometry_params or _coerce_mapping(solver_output.metadata.get("geometry_params"))),
        kinematic_params=dict(
            kinematic_params or _coerce_mapping(solver_output.metadata.get("kinematic_params"))
        ),
        tilt_params=dict(tilt_params or _coerce_mapping(solver_output.metadata.get("tilt_params"))),
        solver_output_ref=solver_output.manifest.artifact_id,
        observable_vector_ref=observable_vector.manifest.artifact_id,
        response_blocks=response_payload,
        validity_domain=validity_payload,
        interpolation_status=interpolation_status,
        manifest=manifest,
    )
