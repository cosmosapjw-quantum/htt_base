"""VER2 HTT directional inference shell contracts.

This module implants the solver-independent HTT shell requested by SK-06H.
It intentionally fixes contract shape, ownership, and hard gates without
claiming that live solver-coupled directional likelihood plumbing exists yet.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from common.contracts import (
    ArtifactManifest,
    DiscriminationMatrix,
    ObservableVector,
    PreferredAxis,
    SkySupport,
    SolverCoreOutput,
)
from htt.infer.local_global_discrimination import build_discrimination_matrix_stub
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
    "DEFAULT_DIRECTIONAL_RESPONSE_LIBRARY",
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
    matched_complexity: MatchedComplexityHook = field(
        default_factory=build_matched_complexity_hook
    )
    null_competition: NullCompetitionHook = field(
        default_factory=build_null_competition_hook
    )

    def __post_init__(self) -> None:
        if not self.matched_complexity_ref:
            raise ValueError(
                "DirectionalEvidenceHooks.matched_complexity_ref must be non-empty"
            )
        if not self.null_competition_ref:
            raise ValueError(
                "DirectionalEvidenceHooks.null_competition_ref must be non-empty"
            )


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
        if self.observable_vector.manifest.owner not in {"BASS", "COMMON"}:
            raise ValueError(
                "DirectionalLikelihoodInputs.observable_vector must come from BASS or COMMON"
            )
        if (
            self.solver_core_output is not None
            and self.solver_core_output.manifest.owner not in {"BASS", "COMMON"}
        ):
            raise ValueError(
                "DirectionalLikelihoodInputs.solver_core_output must come from BASS or COMMON"
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
    mock_status = sky_support.mock_coverage_status.strip().lower()
    mock_coverage_ok = mock_status in {"adequate", "passed", "validated"}
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
    if not mock_coverage_ok:
        blocked.append(
            "SkySupport.mock_coverage_status must indicate adequate mock coverage for production"
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
        ),
        discrimination_matrix=build_discrimination_matrix_stub(),
        solver_core_output=solver_core_output,
        manifest=manifest,
        carry_forward=tuple(carry_forward),
        tsc_overlay_ref=tsc_overlay_ref,
    )
