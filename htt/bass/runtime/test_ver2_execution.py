from __future__ import annotations

import numpy as np
import pytest

from tsc.diagnostics.tangency import TangencyResult, TangentKind

from bass.runtime import (
    CanonicalDecision,
    CheckpointPolicy,
    ConstraintProjectionPolicy,
    CouplingMode,
    FeatureStatus,
    IntegratorFamily,
    RuntimeControlBlock,
    SolverFeatureFlags,
    SolverTier,
    ValidationMatrixSpec,
    build_runtime_reduction_decision,
    plan_solver_execution,
    derive_labels,
)


def _happy_tangency() -> TangencyResult:
    return TangencyResult(
        coefficients=np.zeros(3),
        tangent_norm_sq=1.0,
        total_norm_sq=1.0,
        D_sq=0.0,
        D=1.0e-9,
        relative_residual=1.0e-9,
        kind=TangentKind.ONE_FIELD,
        xi=0,
        eta=0.0,
        gram_matrix=np.eye(3),
        moment_vector=np.zeros(3),
    )


def _canonical_decision(
    *,
    beta_policy_pass: bool = True,
    sigma_min_above_floor: bool = True,
    source_Dge2_gate_pass: bool = True,
) -> CanonicalDecision:
    diagnostics = {
        "beta": {"fractional_slack": 0.1 if beta_policy_pass else -0.1},
        "sigma": {"sigma_min": 1.0e-5 if sigma_min_above_floor else 1.0e-9},
        "source": {
            "relative_residual": 1.0e-9 if source_Dge2_gate_pass else 0.5,
            "fraction_on_manifold": 1.0 if source_Dge2_gate_pass else 0.5,
        },
    }
    return CanonicalDecision(
        spec_version="v1.0-w3d1",
        beta_policy_pass=beta_policy_pass,
        sigma_min_above_floor=sigma_min_above_floor,
        source_Dge2_gate_pass=source_Dge2_gate_pass,
        allow_reduction=(
            beta_policy_pass and sigma_min_above_floor and source_Dge2_gate_pass
        ),
        emitted_labels=derive_labels(
            beta_policy_pass=beta_policy_pass,
            sigma_min_above_floor=sigma_min_above_floor,
            source_Dge2_gate_pass=source_Dge2_gate_pass,
            diagnostics=diagnostics,
        ),
        diagnostics=diagnostics,
    )


def _feature_flags() -> SolverFeatureFlags:
    return SolverFeatureFlags(
        background_dynamics=FeatureStatus.APPROXIMATE,
        photon_transport=FeatureStatus.APPROXIMATE,
        thomson_collision=FeatureStatus.APPROXIMATE,
        visibility_history=FeatureStatus.APPROXIMATE,
        source_propagator=FeatureStatus.DISABLED,
        checkpoint_restart=FeatureStatus.APPROXIMATE,
    )


def test_runtime_controls_require_explicit_l2_override() -> None:
    with pytest.raises(ValueError, match="L=2"):
        RuntimeControlBlock(
            tier=SolverTier.TIER_B_PSTF,
            integrator_family=IntegratorFamily.IMEX_SPLIT,
            coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
            multipole_cutoff=2,
            rtol=1.0e-6,
            atol=1.0e-9,
            checkpoint=CheckpointPolicy(enabled=False),
            constraint_projection=ConstraintProjectionPolicy(enabled=False),
        )


def test_checkpoint_policy_requires_stride_and_path_when_enabled() -> None:
    with pytest.raises(ValueError, match="path_template"):
        CheckpointPolicy(enabled=True, every_n_steps=10)


def test_runtime_reduction_decision_is_bass_owned_and_propagation_aware() -> None:
    canonical = _canonical_decision()
    decision = build_runtime_reduction_decision(
        canonical,
        propagation_status="blocked",
        reason="tier-a propagator not yet executable",
    )
    assert decision.owner == "BASS"
    assert decision.allow_reduction is False
    assert decision.source_status == "adequate"


def test_execution_plan_remains_observer_neutral() -> None:
    canonical = _canonical_decision()
    decision = build_runtime_reduction_decision(
        canonical,
        propagation_status="pending",
        reason="anisotropic propagator still skeleton-only",
    )
    controls = RuntimeControlBlock(
        tier=SolverTier.TIER_B_PSTF,
        integrator_family=IntegratorFamily.IMEX_SPLIT,
        coupling_mode=CouplingMode.BACKGROUND_THEN_RADIATION,
        multipole_cutoff=6,
        rtol=1.0e-6,
        atol=1.0e-9,
        checkpoint=CheckpointPolicy(
            enabled=True,
            every_n_steps=10,
            path_template="artifacts/checkpoints/step_{step}.npz",
        ),
        constraint_projection=ConstraintProjectionPolicy(
            enabled=True,
            every_n_steps=5,
            status=FeatureStatus.APPROXIMATE,
        ),
        random_seed=42,
    )
    plan = plan_solver_execution(
        runtime_controls=controls,
        feature_flags=_feature_flags(),
        runtime_decision=decision,
        validation_matrix=ValidationMatrixSpec(
            bianchi_types=("I", "V", "VII_h"),
        ),
    )
    assert plan.observer_neutral_output_required is True
    assert plan.statistics_interpretation_forbidden is True
    assert plan.validation_matrix.expected_rows == 3 * 2 * 4
