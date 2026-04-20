"""Local-boost/global-tilt response-library skeletons for VER2 HTT."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from common.contracts import ArtifactManifest, DiscriminationMatrix

__all__ = [
    "HypothesisResponseTemplate",
    "build_discrimination_matrix_stub",
    "default_response_library",
    "next_observable_recommendation",
]


@dataclass(frozen=True)
class HypothesisResponseTemplate:
    hypothesis: str
    physical_side: str
    observable_basis: tuple[str, ...]
    amplitude_normalization: str
    orientation_convention: str
    validity_domain: tuple[str, ...]
    solver_coupled: bool = False


def _manifest(artifact_id: str) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=f"artifacts/htt/{artifact_id}.json",
        owner="HTT",
        implementation_scope="htt",
        claim_tier="exploratory",
        production_status="diagnostic_only",
        created_by="htt.infer.local_global_discrimination",
        git_commit=None,
        config_hash="skeleton",
        input_hashes=[],
        code_version="ver2-skeleton",
        schema_version="ver2-v1",
        caveats=["skeleton_only", "pre_inference_only", "not_posterior_odds"],
    )


def default_response_library() -> dict[str, HypothesisResponseTemplate]:
    return {
        "flrw_isotropic_null": HypothesisResponseTemplate(
            hypothesis="flrw_isotropic_null",
            physical_side="null",
            observable_basis=("scalar_summary",),
            amplitude_normalization="null_baseline",
            orientation_convention="none",
            validity_domain=("diagnostic_only",),
        ),
        "local_boost": HypothesisResponseTemplate(
            hypothesis="local_boost",
            physical_side="observer_side",
            observable_basis=("scalar_summary", "direction", "depth"),
            amplitude_normalization="beta_local",
            orientation_convention="observer_velocity_axis",
            validity_domain=("low_z", "observer_frame"),
        ),
        "global_tilt": HypothesisResponseTemplate(
            hypothesis="global_tilt",
            physical_side="source_background_side",
            observable_basis=("scalar_summary", "direction", "depth", "template"),
            amplitude_normalization="beta_global",
            orientation_convention="matter_vs_geometry_frame",
            validity_domain=("low_ell", "atlas_required"),
            solver_coupled=True,
        ),
        "bianchi_geometry": HypothesisResponseTemplate(
            hypothesis="bianchi_geometry",
            physical_side="geometry_side",
            observable_basis=("template", "BiPoSH", "EE", "BB"),
            amplitude_normalization="atlas_response_block",
            orientation_convention="tetrad_to_sky",
            validity_domain=("atlas_required", "solver_required"),
            solver_coupled=True,
        ),
        "systematic_template": HypothesisResponseTemplate(
            hypothesis="systematic_template",
            physical_side="systematic_side",
            observable_basis=("scalar_summary", "direction", "template"),
            amplitude_normalization="nuisance_template",
            orientation_convention="survey_axis",
            validity_domain=("null_mock_required",),
        ),
    }


def next_observable_recommendation(pair: tuple[str, str]) -> str:
    ordered = tuple(sorted(pair))
    if ordered == ("global_tilt", "local_boost"):
        return "depth_direction_coherence"
    if "bianchi_geometry" in ordered:
        return "atlas_template_biposh"
    return "null_mock_covariance"


def build_discrimination_matrix_stub(
    hypotheses: tuple[str, ...] = ("local_boost", "global_tilt"),
    *,
    overlap_strength: float = 0.8,
) -> DiscriminationMatrix:
    if len(hypotheses) < 2:
        raise ValueError("Need at least two hypotheses for a discrimination matrix")
    overlap = np.eye(len(hypotheses), dtype=float)
    for i in range(len(hypotheses)):
        for j in range(i + 1, len(hypotheses)):
            overlap[i, j] = overlap[j, i] = overlap_strength
    pair_key = "|".join(hypotheses[:2])
    return DiscriminationMatrix(
        hypotheses=hypotheses,
        overlap_matrix=overlap,
        response_norms={hyp: 1.0 for hyp in hypotheses},
        degeneracy_flags={pair_key: abs(overlap_strength) >= 0.75},
        recommended_next_observable={
            pair_key: next_observable_recommendation((hypotheses[0], hypotheses[1]))
        },
        claim_tier_by_pair={pair_key: "exploratory"},
        manifest=_manifest("htt.discrimination_matrix_stub"),
    )
