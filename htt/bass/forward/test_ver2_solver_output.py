from __future__ import annotations

import pytest

from common.contracts import ArtifactManifest

from bass.forward import (
    BassReleaseMetadata,
    build_solver_core_output,
    solver_core_output_from_payload,
    solver_core_output_to_payload,
)
from bass.los import PropagatorMode, SourcePropagatorConfig
from bass.runtime import (
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
)


def _manifest(**overrides) -> ArtifactManifest:
    base = dict(
        artifact_id="bass.ver2.solver.output",
        artifact_path="artifacts/bass/ver2_solver_output.json",
        owner="BASS",
        implementation_scope="canonical_BASS",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="deadbeef",
        config_hash="cfg-hash",
        input_hashes=["bg", "rad"],
        code_version="0.0-test",
        schema_version="ver2-v0",
    )
    base.update(overrides)
    return ArtifactManifest(**base)


def _controls() -> RuntimeControlBlock:
    return RuntimeControlBlock(
        tier=SolverTier.TIER_B_PSTF,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=6,
        rtol=1.0e-6,
        atol=1.0e-9,
        checkpoint=CheckpointPolicy(enabled=False),
        constraint_projection=ConstraintProjectionPolicy(enabled=False),
        random_seed=42,
    )


def _flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.DISABLED,
        checkpoint_restart=FeatureStatus.DISABLED,
    )


def test_solver_core_output_requires_bass_manifest_owner() -> None:
    with pytest.raises(ValueError, match="owned by BASS"):
        build_solver_core_output(
            manifest=_manifest(owner="HTT"),
            bianchi_type="I",
            tilt_enabled=False,
            harmonic_basis="pstf",
            eb_sign_convention="explicit_solver_state",
            thomson_mode="electron_frame_projected",
            runtime_controls=_controls(),
            feature_flags=_flags(),
            propagator=SourcePropagatorConfig(
                mode=PropagatorMode.ANISOTROPIC_FORWARD,
                temperature_transport=FeatureStatus.APPROXIMATE,
                polarization_rotation=FeatureStatus.APPROXIMATE,
            ),
            release=BassReleaseMetadata(
                release_stage="skeleton",
                run_label="tier-b-smoke",
                config_hash="cfg-hash",
                code_version="0.0-test",
                schema_version="ver2-v0",
                git_commit="deadbeef",
                random_seed=42,
            ),
        )


def test_solver_core_output_builder_attaches_required_metadata() -> None:
    output = build_solver_core_output(
        manifest=_manifest(),
        bianchi_type="VII_h",
        tilt_enabled=True,
        harmonic_basis="pstf",
        eb_sign_convention="explicit_solver_state",
        thomson_mode="electron_frame_projected",
        runtime_controls=_controls(),
        feature_flags=_flags(),
        propagator=SourcePropagatorConfig(
            mode=PropagatorMode.ANISOTROPIC_FORWARD,
            temperature_transport=FeatureStatus.APPROXIMATE,
            polarization_rotation=FeatureStatus.APPROXIMATE,
        ),
        release=BassReleaseMetadata(
            release_stage="skeleton",
            run_label="tier-b-smoke",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        deterministic_template={"kind": "pending"},
    )
    assert output.metadata["bianchi_type"] == "VII_h"
    assert output.metadata["observer_neutral"] is True
    assert output.metadata["multipole_cutoff"] == 6


def test_solver_core_output_payload_roundtrips() -> None:
    output = build_solver_core_output(
        manifest=_manifest(),
        bianchi_type="I",
        tilt_enabled=False,
        harmonic_basis="pstf",
        eb_sign_convention="explicit_solver_state",
        thomson_mode="electron_frame_projected",
        runtime_controls=_controls(),
        feature_flags=_flags(),
        propagator=SourcePropagatorConfig(
            mode=PropagatorMode.FLRW_VALIDATION,
            temperature_transport=FeatureStatus.EXACT,
            polarization_rotation=FeatureStatus.DISABLED,
            flrw_validation_only=True,
            kernel_family="flrw_scalar_validation",
        ),
        release=BassReleaseMetadata(
            release_stage="skeleton",
            run_label="tier-a-validation",
            config_hash="cfg-hash",
            code_version="0.0-test",
            schema_version="ver2-v0",
            git_commit="deadbeef",
            random_seed=42,
        ),
        deterministic_template={"kind": "pending"},
    )
    payload = solver_core_output_to_payload(output)
    restored = solver_core_output_from_payload(payload)
    assert restored.metadata == output.metadata
    assert restored.manifest.artifact_id == output.manifest.artifact_id
