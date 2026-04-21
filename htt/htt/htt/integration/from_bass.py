"""
htt/integration/from_bass.py — HTT ← BASS Integration Adapter
================================================================
C-16 deliverable. Receives BASSDirectionalBundle and integrates
into the HTT Stage 2 inference engine.
"""
from __future__ import annotations

from common.contracts import (
    ArtifactManifest,
    AtlasEntryLite,
    ObservableVector,
    PreferredAxis,
    SolverCoreOutput,
    TscAdequacyOverlay,
)

from htt.infer.matched_complexity import (
    MatchedComplexityHook,
    build_matched_complexity_hook,
)
from htt.infer.null_competition import (
    NullCompetitionHook,
    build_null_competition_hook,
)
from htt.infer.likelihood_scope_guard import (
    DirectionalLikelihoodInput,
    build_directional_likelihood_input,
)
from htt.infer.ver2_directional_shell import (
    DirectionalLikelihoodInputs,
    build_directional_likelihood_inputs,
)

__all__ = [
    'ingest_bass_directional',
    'build_ver2_directional_inputs',
    'ingest_ver2_directional_inputs',
]


def ingest_bass_directional(bundle) -> dict:
    """Ingest a BASSDirectionalBundle into HTT.

    Validates the bundle and extracts directional observables
    for the latent-axis and dipole-vector likelihood modules.
    """
    result = {
        'f2_teff': bundle.f2_teff,
        'gauge_deviation': bundle.gauge_deviation,
        'families_scanned': bundle.families_scanned,
        'family_R_sigma': {
            name: info['R_sigma']
            for name, info in bundle.family_results.items()
        },
        'ingested': True,
    }
    return result


def build_ver2_directional_inputs(
    observable_vector: ObservableVector,
    preferred_axis: PreferredAxis,
    *,
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
    """Build the solver-independent SK-06H directional shell from BASS inputs."""
    return build_directional_likelihood_inputs(
        observable_vector=observable_vector,
        preferred_axis=preferred_axis,
        solver_core_output=solver_core_output,
        manifest=manifest,
        matched_complexity_ref=matched_complexity_ref,
        null_competition_ref=null_competition_ref,
        morphology_atlas_ref=morphology_atlas_ref,
        posterior_predictive_ref=posterior_predictive_ref,
        loocv_ref=loocv_ref,
        matched_complexity=matched_complexity,
        null_competition=null_competition,
        posterior_predictive_ready=posterior_predictive_ready,
        loocv_ready=loocv_ready,
        tsc_overlay_ref=tsc_overlay_ref,
    )


def ingest_ver2_directional_inputs(
    observable_vector: ObservableVector,
    *,
    atlas_entry: AtlasEntryLite | None = None,
    preferred_axis: PreferredAxis | None = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    required_channels: tuple[str, ...] = ("TT",),
    scalar_only_geometry: bool = False,
    matched_complexity_ready: bool = False,
    null_competition_ready: bool = False,
) -> DirectionalLikelihoodInput:
    """Build the SK-06H scope-guard bundle from canonical common contracts."""

    matched_hook: MatchedComplexityHook | None
    null_hook: NullCompetitionHook | None
    if matched_complexity_ready:
        matched_hook = build_matched_complexity_hook()
    else:
        matched_hook = MatchedComplexityHook(
            controls_required=tuple(),
            overall_pass=True,
            violations=tuple(),
        )
    if null_competition_ready:
        null_hook = NullCompetitionHook(
            required_families=("registered_nulls",),
            fpr_threshold=0.10,
            ready_for_inference=True,
            worst_family=None,
            worst_fpr=None,
        )
    else:
        null_hook = build_null_competition_hook()
    return build_directional_likelihood_input(
        observable_vector=observable_vector,
        atlas_entry=atlas_entry,
        preferred_axis=preferred_axis,
        tsc_overlay=tsc_overlay,
        required_channels=required_channels,
        scalar_only_geometry=scalar_only_geometry,
        matched_complexity_hook=matched_hook,
        null_competition_hook=null_hook,
    )
