"""VER2 HTT directional inference shell contracts.

This module implants the solver-independent HTT shell requested by SK-06H.
It intentionally fixes contract shape, ownership, and hard gates without
claiming that live solver-coupled directional likelihood plumbing exists yet.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    DiscriminationMatrix,
    ObservableVector,
    PreferredAxis,
    ProductionStatus,
    SkySupport,
    SolverCoreOutput,
)
from htt.infer.local_global_discrimination import build_discrimination_matrix_stub
from htt.infer.local_global_discrimination import build_discrimination_matrix
from htt.infer.matched_complexity import (
    MatchedComplexityHook,
    build_matched_complexity_hook,
)
from htt.infer.null_competition import (
    NullCompetitionHook,
    build_null_competition_hook,
)

__all__ = [
    "DirectionalHypothesisSpec",
    "DirectionalResponseLibrary",
    "DirectionalInferencePolicy",
    "DirectionalEvidenceHooks",
    "ProductionAxisGateResult",
    "DirectionalLikelihoodInputs",
    "DirectionalReadiness",
    "DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY",
    "assess_directional_readiness",
    "build_directional_output_manifest",
    "evaluate_production_axis_gate",
    "build_directional_likelihood_inputs",
]

_REQUIRED_HYPOTHESES = {
    "flrw_isotropic_null",
    "local_boost",
    "global_tilt",
    "bianchi_geometry",
    "systematic_template",
}
_ALLOWED_RESPONSE_SIDES = {
    "null",
    "observer",
    "source_background",
    "geometry",
    "systematic",
}
_DEFAULT_DISCRIMINATION_AXES = (
    "depth_evolution",
    "directional_coherence",
    "off_diagonal_morphology",
)


@dataclass(frozen=True)
class DirectionalHypothesisSpec:
    """One hypothesis row in the HTT response library."""

    hypothesis_id: str
    label: str
    response_side: str
    observable_basis: tuple[str, ...]
    claim_role: str
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.hypothesis_id:
            raise ValueError("DirectionalHypothesisSpec.hypothesis_id must be non-empty")
        if self.response_side not in _ALLOWED_RESPONSE_SIDES:
            raise ValueError(
                f"Unknown response_side {self.response_side!r}; "
                f"expected one of {sorted(_ALLOWED_RESPONSE_SIDES)}"
            )
        if not self.observable_basis:
            raise ValueError(
                "DirectionalHypothesisSpec.observable_basis must be non-empty"
            )
        if not self.claim_role:
            raise ValueError("DirectionalHypothesisSpec.claim_role must be non-empty")


@dataclass(frozen=True)
class DirectionalResponseLibrary:
    """Distinct HTT response-library rows for directional competition."""

    hypotheses: tuple[DirectionalHypothesisSpec, ...]
    discrimination_axes: tuple[str, ...] = _DEFAULT_DISCRIMINATION_AXES
    morphology_mode: str = "diagnostic_only"

    def __post_init__(self) -> None:
        ids = tuple(spec.hypothesis_id for spec in self.hypotheses)
        missing = sorted(_REQUIRED_HYPOTHESES - set(ids))
        if missing:
            raise ValueError(
                "DirectionalResponseLibrary missing required hypotheses: "
                f"{missing}"
            )
        if len(set(ids)) != len(ids):
            raise ValueError("DirectionalResponseLibrary hypothesis ids must be unique")
        if "local_boost" not in ids or "global_tilt" not in ids:
            raise ValueError("local_boost and global_tilt must both be present")

        library = {spec.hypothesis_id: spec for spec in self.hypotheses}
        if library["local_boost"].response_side == library["global_tilt"].response_side:
            raise ValueError(
                "local_boost and global_tilt must remain distinct response sides"
            )
        if library["systematic_template"].claim_role == "geometry_claim":
            raise ValueError(
                "systematic_template must remain a control, not a geometry claim"
            )


@dataclass(frozen=True)
class DirectionalInferencePolicy:
    """Hard separation rules for HTT-owned posterior/evidence surfaces."""

    posterior_owner: str = "HTT"
    evidence_owner: str = "HTT"
    allow_mio_certificate_merge: bool = False
    allow_tsc_posterior_correction: bool = False

    def __post_init__(self) -> None:
        if self.posterior_owner != "HTT":
            raise ValueError("HTT directional posterior owner must remain 'HTT'")
        if self.evidence_owner != "HTT":
            raise ValueError("HTT directional evidence owner must remain 'HTT'")
        if self.allow_mio_certificate_merge:
            raise ValueError(
                "MIO certificate semantics cannot be merged into HTT posterior/evidence"
            )
        if self.allow_tsc_posterior_correction:
            raise ValueError(
                "TSC diagnostics cannot be injected as an HTT posterior correction"
            )


@dataclass(frozen=True)
class DirectionalEvidenceHooks:
    """Skeleton hook references for HTT directional competition."""

    matched_complexity_ref: str = "matched_complexity_report_v1.json"
    null_competition_ref: str = "null_competition_report_v1.json"
    morphology_atlas_ref: str | None = None
    posterior_predictive_ref: str = "posterior_predictive_v1.json"
    loocv_ref: str = "loocv_report_v1.json"
    matched_complexity: MatchedComplexityHook = field(
        default_factory=build_matched_complexity_hook
    )
    null_competition: NullCompetitionHook = field(
        default_factory=build_null_competition_hook
    )
    posterior_predictive_ready: bool = False
    loocv_ready: bool = False

    def __post_init__(self) -> None:
        if not self.matched_complexity_ref:
            raise ValueError(
                "DirectionalEvidenceHooks.matched_complexity_ref must be non-empty"
            )
        if not self.null_competition_ref:
            raise ValueError(
                "DirectionalEvidenceHooks.null_competition_ref must be non-empty"
            )
        if not self.posterior_predictive_ref:
            raise ValueError(
                "DirectionalEvidenceHooks.posterior_predictive_ref must be non-empty"
            )
        if not self.loocv_ref:
            raise ValueError("DirectionalEvidenceHooks.loocv_ref must be non-empty")
        if self.posterior_predictive_ready and not self.posterior_predictive_ref:
            raise ValueError(
                "posterior_predictive_ready=True requires a non-empty posterior_predictive_ref"
            )
        if self.loocv_ready and not self.loocv_ref:
            raise ValueError("loocv_ready=True requires a non-empty loocv_ref")


@dataclass(frozen=True)
class ProductionAxisGateResult:
    """Closed-fail decision for promoting a directional axis into production."""

    axis: PreferredAxis
    sky_support: SkySupport
    allowed: bool
    required_conditions: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    carry_forward: tuple[str, ...] = ()


@dataclass(frozen=True)
class DirectionalLikelihoodInputs:
    """Solver-independent HTT directional input shell."""

    observable_vector: ObservableVector
    preferred_axis: PreferredAxis
    axis_gate: ProductionAxisGateResult
    response_library: DirectionalResponseLibrary
    evidence_hooks: DirectionalEvidenceHooks
    discrimination_matrix: DiscriminationMatrix
    policy: DirectionalInferencePolicy = field(
        default_factory=DirectionalInferencePolicy
    )
    solver_core_output: SolverCoreOutput | None = None
    manifest: ArtifactManifest | None = None
    carry_forward: tuple[str, ...] = ()
    tsc_overlay_ref: str | None = None

    def __post_init__(self) -> None:
        if self.observable_vector.manifest.owner != "BASS":
            raise ValueError(
                "DirectionalLikelihoodInputs.observable_vector must come from BASS"
            )
        if (
            self.solver_core_output is not None
            and self.solver_core_output.manifest.owner != "BASS"
        ):
            raise ValueError(
                "DirectionalLikelihoodInputs.solver_core_output must come from BASS"
            )
        if self.axis_gate.axis != self.preferred_axis:
            raise ValueError("axis_gate.axis must match preferred_axis")
        if self.axis_gate.sky_support != self.observable_vector.sky_support:
            raise ValueError(
                "axis_gate.sky_support must match observable_vector.sky_support"
            )
        if self.manifest is not None and self.manifest.owner != "HTT":
            raise ValueError(
                "DirectionalLikelihoodInputs.manifest.owner must be 'HTT'"
            )


@dataclass(frozen=True)
class DirectionalReadiness:
    """Resolved VER2 production metadata for one HTT directional surface."""

    production_status: ProductionStatus
    claim_tier: ClaimTier
    required_gates: tuple[str, ...]
    passed_gates: tuple[str, ...]
    failed_gates: tuple[str, ...]
    caveats: tuple[str, ...]
    public_grade_label: str


DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY = DirectionalResponseLibrary(
    hypotheses=(
        DirectionalHypothesisSpec(
            hypothesis_id="flrw_isotropic_null",
            label="FLRW isotropic null",
            response_side="null",
            observable_basis=("directional_power", "lowell_alignment"),
            claim_role="null_competitor",
            notes=("reference isotropic baseline",),
        ),
        DirectionalHypothesisSpec(
            hypothesis_id="local_boost",
            label="Local boost",
            response_side="observer",
            observable_basis=("directional_power", "depth_evolution"),
            claim_role="posterior_competitor",
            notes=("observer-side velocity response",),
        ),
        DirectionalHypothesisSpec(
            hypothesis_id="global_tilt",
            label="Global tilt",
            response_side="source_background",
            observable_basis=("directional_power", "depth_evolution"),
            claim_role="posterior_competitor",
            notes=("source/background-side tilt response",),
        ),
        DirectionalHypothesisSpec(
            hypothesis_id="bianchi_geometry",
            label="Bianchi geometry",
            response_side="geometry",
            observable_basis=("directional_power", "off_diagonal_morphology"),
            claim_role="posterior_competitor",
            notes=("geometry-bearing response family",),
        ),
        DirectionalHypothesisSpec(
            hypothesis_id="systematic_template",
            label="Systematic template",
            response_side="systematic",
            observable_basis=("directional_power", "off_diagonal_morphology"),
            claim_role="systematic_control",
            notes=("diagnostic control, not a geometry claim",),
        ),
    ),
)


def evaluate_production_axis_gate(
    axis: PreferredAxis,
    sky_support: SkySupport,
) -> ProductionAxisGateResult:
    """Decide whether an axis may seed HTT production directional inference."""

    required = (
        "PreferredAxis.production_allowed=True",
        "PreferredAxis.source='fiducial_posterior'",
        "PreferredAxis.selection_mode='mock_calibrated'",
        "SkySupport.selection_mode='mock_calibrated'",
        "SkySupport.mock_coverage_status='adequate'",
    )
    blocked: list[str] = []
    if not axis.production_allowed:
        blocked.append("PreferredAxis.production_allowed=False")
    if axis.source != "fiducial_posterior":
        blocked.append(
            f"PreferredAxis.source={axis.source!r} is not 'fiducial_posterior'"
        )
    if axis.selection_mode != "mock_calibrated":
        blocked.append(
            "PreferredAxis.selection_mode must be 'mock_calibrated' for production"
        )
    if sky_support.selection_mode != "mock_calibrated":
        blocked.append(
            "SkySupport.selection_mode must be 'mock_calibrated' for production"
        )
    if axis.selection_mode != sky_support.selection_mode:
        blocked.append(
            "PreferredAxis.selection_mode and SkySupport.selection_mode must match"
        )
    if sky_support.mock_coverage_status != "adequate":
        blocked.append(
            "SkySupport.mock_coverage_status must be 'adequate' for production"
        )

    carry_forward: list[str] = []
    if not axis.provenance_hash:
        carry_forward.append(
            "Axis provenance hash is a skeleton placeholder until solver-coupled posterior wiring lands."
        )
    if not sky_support.scan_volume_hash:
        carry_forward.append(
            "Sky support scan-volume hash is still a placeholder until upstream observable export is promoted."
        )

    return ProductionAxisGateResult(
        axis=axis,
        sky_support=sky_support,
        allowed=not blocked,
        required_conditions=required,
        blocked_reasons=tuple(blocked),
        carry_forward=tuple(carry_forward),
    )


def build_directional_likelihood_inputs(
    *,
    observable_vector: ObservableVector,
    preferred_axis: PreferredAxis,
    solver_core_output: SolverCoreOutput | None = None,
    manifest: ArtifactManifest | None = None,
    matched_complexity_ref: str = "matched_complexity_report_v1.json",
    null_competition_ref: str = "null_competition_report_v1.json",
    morphology_atlas_ref: str | None = "template_morphology_atlas_v1.json",
    posterior_predictive_ref: str = "posterior_predictive_v1.json",
    loocv_ref: str = "loocv_report_v1.json",
    matched_complexity: MatchedComplexityHook | None = None,
    null_competition: NullCompetitionHook | None = None,
    posterior_predictive_ready: bool = False,
    loocv_ready: bool = False,
    tsc_overlay_ref: str | None = None,
) -> DirectionalLikelihoodInputs:
    """Create the SK-06H directional shell from canonical common contracts."""

    gate = evaluate_production_axis_gate(
        axis=preferred_axis,
        sky_support=observable_vector.sky_support,
    )
    carry_forward = list(gate.carry_forward)
    if solver_core_output is None:
        carry_forward.append(
            "Await SK-01S1 -> SK-03S3 solver-coupled likelihood payloads before enabling live directional inference."
        )
    if morphology_atlas_ref is None:
        carry_forward.append(
            "Template morphology atlas remains optional/diagnostic until PR-HTT-11 wiring is implemented."
        )

    return DirectionalLikelihoodInputs(
        observable_vector=observable_vector,
        preferred_axis=preferred_axis,
        axis_gate=gate,
        response_library=DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY,
        evidence_hooks=DirectionalEvidenceHooks(
            matched_complexity_ref=matched_complexity_ref,
            null_competition_ref=null_competition_ref,
            morphology_atlas_ref=morphology_atlas_ref,
            posterior_predictive_ref=posterior_predictive_ref,
            loocv_ref=loocv_ref,
            matched_complexity=matched_complexity
            if matched_complexity is not None
            else build_matched_complexity_hook(),
            null_competition=null_competition
            if null_competition is not None
            else build_null_competition_hook(),
            posterior_predictive_ready=posterior_predictive_ready,
            loocv_ready=loocv_ready,
        ),
        discrimination_matrix=build_discrimination_matrix(
            observable_vector,
            morphology_atlas_ref=morphology_atlas_ref,
        ),
        solver_core_output=solver_core_output,
        manifest=manifest,
        carry_forward=tuple(carry_forward),
        tsc_overlay_ref=tsc_overlay_ref,
    )


def _append_gate(
    *,
    gate_name: str,
    passed_gate: bool,
    required: list[str],
    passed: list[str],
    failed: list[str],
) -> None:
    required.append(gate_name)
    if passed_gate:
        passed.append(gate_name)
    else:
        failed.append(gate_name)


def assess_directional_readiness(
    inputs: DirectionalLikelihoodInputs,
    *,
    require_morphology_atlas: bool | None = None,
    eligible_for_production: bool | None = None,
    validated: bool = False,
) -> DirectionalReadiness:
    """Resolve production status, gates, and caveats for HTT-owned outputs."""

    if validated and eligible_for_production is False:
        raise ValueError(
            "validated directional outputs must remain eligible_for_production"
        )

    morphology_required = (
        inputs.response_library.morphology_mode != "diagnostic_only"
        if require_morphology_atlas is None
        else bool(require_morphology_atlas)
    )
    resolved_eligible = (
        inputs.axis_gate.allowed
        if eligible_for_production is None
        else bool(eligible_for_production)
    )

    required: list[str] = []
    passed: list[str] = []
    failed: list[str] = []
    caveats: list[str] = list(inputs.carry_forward)

    _append_gate(
        gate_name="policy_firewall_intact",
        passed_gate=(
            inputs.policy.posterior_owner == "HTT"
            and inputs.policy.evidence_owner == "HTT"
            and not inputs.policy.allow_mio_certificate_merge
            and not inputs.policy.allow_tsc_posterior_correction
        ),
        required=required,
        passed=passed,
        failed=failed,
    )
    if "policy_firewall_intact" in passed:
        caveats.append("mio_tsc_firewall_intact")

    axis_ok = inputs.axis_gate.allowed
    _append_gate(
        gate_name="production_axis_ready",
        passed_gate=axis_ok,
        required=required,
        passed=passed,
        failed=failed,
    )
    if not axis_ok:
        caveats.extend(inputs.axis_gate.blocked_reasons)

    matched_controls_present = bool(inputs.evidence_hooks.matched_complexity.controls_required)
    matched_ok = (
        matched_controls_present
        and inputs.evidence_hooks.matched_complexity.overall_pass
    )
    _append_gate(
        gate_name="matched_complexity_ready",
        passed_gate=matched_ok,
        required=required,
        passed=passed,
        failed=failed,
    )
    if not matched_controls_present:
        caveats.append("matched_complexity_hook_pending")
    if not inputs.evidence_hooks.matched_complexity.overall_pass:
        caveats.append("matched_complexity_failed")
    for violation in inputs.evidence_hooks.matched_complexity.violations:
        caveats.append(f"matched_complexity_violation:{violation}")
    if inputs.evidence_hooks.matched_complexity.scope != "pre_inference_only":
        caveats.append("matched_complexity_scope_unexpected")

    null_ok = inputs.evidence_hooks.null_competition.ready_for_inference
    _append_gate(
        gate_name="null_competition_ready",
        passed_gate=null_ok,
        required=required,
        passed=passed,
        failed=failed,
    )
    if not null_ok:
        caveats.append("null_competition_hook_pending")
    if inputs.evidence_hooks.null_competition.scope != "pre_posterior":
        caveats.append("null_competition_scope_unexpected")
    if inputs.evidence_hooks.null_competition.worst_family is not None:
        caveats.append(
            f"null_competition_worst_family={inputs.evidence_hooks.null_competition.worst_family}"
        )
    if inputs.evidence_hooks.null_competition.worst_fpr is not None:
        caveats.append(
            f"null_competition_worst_fpr={inputs.evidence_hooks.null_competition.worst_fpr:.3f}"
        )

    solver_ok = inputs.solver_core_output is not None
    _append_gate(
        gate_name="solver_payload_ready",
        passed_gate=solver_ok,
        required=required,
        passed=passed,
        failed=failed,
    )
    if not solver_ok:
        caveats.append("solver_coupled_wiring_pending")

    ppc_ok = (
        inputs.evidence_hooks.posterior_predictive_ready
        and bool(inputs.evidence_hooks.posterior_predictive_ref)
    )
    _append_gate(
        gate_name="posterior_predictive_ready",
        passed_gate=ppc_ok,
        required=required,
        passed=passed,
        failed=failed,
    )
    if not ppc_ok:
        caveats.append("posterior_predictive_hook_pending")

    loocv_ok = inputs.evidence_hooks.loocv_ready and bool(inputs.evidence_hooks.loocv_ref)
    _append_gate(
        gate_name="loocv_ready",
        passed_gate=loocv_ok,
        required=required,
        passed=passed,
        failed=failed,
    )
    if not loocv_ok:
        caveats.append("loocv_hook_pending")

    morphology_ok = True
    if morphology_required:
        morphology_ok = inputs.evidence_hooks.morphology_atlas_ref is not None
        _append_gate(
            gate_name="morphology_atlas_ready",
            passed_gate=morphology_ok,
            required=required,
            passed=passed,
            failed=failed,
        )
        if not morphology_ok:
            caveats.append("morphology_atlas_missing")

    if inputs.tsc_overlay_ref is not None:
        caveats.append(f"tsc_overlay_ref={inputs.tsc_overlay_ref}")
        caveats.append("tsc_overlay_caveat_only")

    base_ready = axis_ok and matched_ok and solver_ok and ppc_ok and loocv_ok
    all_required_pass = len(failed) == 0

    if base_ready and morphology_required and not morphology_ok:
        production_status: ProductionStatus = "blocked_missing_atlas"
    elif base_ready and not null_ok:
        production_status = "blocked_missing_null_mocks"
    elif all_required_pass and validated:
        production_status = "production_validated"
    elif all_required_pass and resolved_eligible:
        production_status = "production_candidate"
    else:
        production_status = "diagnostic_only"

    if production_status.startswith("blocked_"):
        claim_tier: ClaimTier = "blocked"
    elif production_status == "production_validated":
        claim_tier = "validated"
    elif production_status == "production_candidate":
        claim_tier = "conditional"
    else:
        claim_tier = "exploratory"

    public_grade_label = (
        "production-grade"
        if production_status in {"production_candidate", "production_validated"}
        else "diagnostic-only"
    )
    caveats.append(f"public_grade={public_grade_label}")
    caveats.append(f"production_status={production_status}")

    return DirectionalReadiness(
        production_status=production_status,
        claim_tier=claim_tier,
        required_gates=tuple(required),
        passed_gates=tuple(passed),
        failed_gates=tuple(failed),
        caveats=tuple(dict.fromkeys(caveats)),
        public_grade_label=public_grade_label,
    )


def build_directional_output_manifest(
    *,
    inputs: DirectionalLikelihoodInputs,
    artifact_id: str,
    artifact_path: str,
    model_name: str,
    posterior_ref: str,
    evidence_ref: str,
    output_role: str = "directional_posterior",
    cross_check_only: bool = False,
    posterior_predictive_ref: str | None = None,
    loocv_ref: str | None = None,
    require_morphology_atlas: bool | None = None,
    eligible_for_production: bool | None = None,
    validated: bool = False,
    created_by: str = "htt.infer.ver2_directional_shell.build_directional_output_manifest",
    git_commit: str | None = None,
    config_hash: str | None = None,
    input_hashes: Sequence[str] = (),
    code_version: str | None = None,
    schema_version: str | None = None,
    statistics_definitions: Mapping[str, object] | None = None,
) -> ArtifactManifest:
    """Materialize the HTT-owned manifest for one directional output surface."""

    readiness = assess_directional_readiness(
        inputs,
        require_morphology_atlas=require_morphology_atlas,
        eligible_for_production=eligible_for_production,
        validated=validated,
    )
    base_manifest = inputs.manifest or inputs.observable_vector.manifest
    resolved_ppc_ref = (
        posterior_predictive_ref
        if posterior_predictive_ref is not None
        else inputs.evidence_hooks.posterior_predictive_ref
    )
    resolved_loocv_ref = (
        loocv_ref if loocv_ref is not None else inputs.evidence_hooks.loocv_ref
    )

    merged_input_hashes = list(base_manifest.input_hashes)
    for ref in (
        base_manifest.artifact_id,
        inputs.observable_vector.manifest.artifact_id,
        None
        if inputs.solver_core_output is None
        else inputs.solver_core_output.manifest.artifact_id,
        inputs.discrimination_matrix.manifest.artifact_id,
        inputs.evidence_hooks.matched_complexity_ref,
        inputs.evidence_hooks.null_competition_ref,
        inputs.evidence_hooks.morphology_atlas_ref,
        resolved_ppc_ref,
        resolved_loocv_ref,
        posterior_ref,
        evidence_ref,
        *input_hashes,
    ):
        if ref is None:
            continue
        text = str(ref)
        if text and text not in merged_input_hashes:
            merged_input_hashes.append(text)

    merged_caveats = list(readiness.caveats)
    if cross_check_only:
        merged_caveats.append("mio_cross_check_only_export")
    merged_stats = dict(base_manifest.statistics_definitions)
    merged_stats.update(
        {
            "surface": output_role,
            "model_name": model_name,
            "posterior_ref": posterior_ref,
            "evidence_ref": evidence_ref,
            "posterior_predictive_ref": resolved_ppc_ref,
            "loocv_ref": resolved_loocv_ref,
            "cross_check_only": cross_check_only,
            "axis_label": inputs.preferred_axis.label,
            "axis_source": inputs.preferred_axis.source,
            "selection_mode": inputs.observable_vector.sky_support.selection_mode,
            "mock_coverage_status": inputs.observable_vector.sky_support.mock_coverage_status,
            "sky_support_hash": inputs.observable_vector.sky_support.sky_support_hash,
            "scan_volume_hash": inputs.observable_vector.sky_support.scan_volume_hash,
            "response_hypotheses": [
                spec.hypothesis_id for spec in inputs.response_library.hypotheses
            ],
            "discrimination_matrix_ref": inputs.discrimination_matrix.manifest.artifact_id,
        }
    )
    if statistics_definitions is not None:
        merged_stats.update(dict(statistics_definitions))

    resolved_code_version = code_version
    if resolved_code_version is None:
        if base_manifest.owner == "HTT":
            resolved_code_version = base_manifest.code_version
        else:
            resolved_code_version = "ver2-im06h"

    resolved_schema_version = schema_version
    if resolved_schema_version is None:
        if base_manifest.owner == "HTT":
            resolved_schema_version = base_manifest.schema_version
        else:
            resolved_schema_version = "ver2-v6"

    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner="HTT",
        implementation_scope="htt",
        claim_tier=readiness.claim_tier,
        production_status=readiness.production_status,
        created_by=created_by,
        git_commit=git_commit if git_commit is not None else base_manifest.git_commit,
        config_hash=config_hash if config_hash is not None else base_manifest.config_hash,
        input_hashes=merged_input_hashes,
        code_version=resolved_code_version,
        schema_version=resolved_schema_version,
        caveats=list(dict.fromkeys(merged_caveats)),
        required_gates=list(readiness.required_gates),
        passed_gates=list(readiness.passed_gates),
        failed_gates=list(readiness.failed_gates),
        statistics_definitions=merged_stats,
    )
