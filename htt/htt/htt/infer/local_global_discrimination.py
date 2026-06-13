"""Local-boost/global-tilt response-library calibration helpers for VER2 HTT."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np

from common.contracts import (
    ArtifactManifest,
    AtlasEntryLite,
    DiscriminationMatrix,
    ObservableVector,
)
from htt.nulls.local_boost_depth_null import (
    GlobalTiltLocalNullGateDecision,
    LocalBoostNullFprReport,
    evaluate_global_tilt_local_null_gate,
)
from htt.nulls.selection_response_depth import (
    SurveySystematicNullFprReport,
    SurveySystematicNullGateDecision,
    evaluate_survey_systematic_null_gate,
)

__all__ = [
    "HypothesisResponseTemplate",
    "build_discrimination_matrix",
    "build_discrimination_matrix_stub",
    "default_response_library",
    "next_observable_recommendation",
    "whitened_inner_product",
]

_BASIS_ORDER = ("scalar_summary", "direction", "depth", "template", "BiPoSH", "EE", "BB")
_CONDITIONAL_OVERLAP_THRESHOLD = 0.9


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


def _pair_key(left: str, right: str) -> str:
    return "|".join(sorted((left, right)))


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


def whitened_inner_product(
    response_i: np.ndarray,
    response_j: np.ndarray,
    noise_variances: np.ndarray,
) -> float:
    """Return the diagonal-noise whitened inner product."""

    vector_i = np.asarray(response_i, dtype=float)
    vector_j = np.asarray(response_j, dtype=float)
    variances = np.asarray(noise_variances, dtype=float)
    if vector_i.shape != vector_j.shape or vector_i.shape != variances.shape:
        raise ValueError("response vectors and noise variances must share the same shape")
    precision = np.zeros_like(variances, dtype=float)
    finite = np.isfinite(variances) & (variances > 0.0)
    precision[finite] = 1.0 / variances[finite]
    return float(np.dot(vector_i, precision * vector_j))


def _normalized_overlap(
    response_i: np.ndarray,
    response_j: np.ndarray,
    noise_variances: np.ndarray,
) -> float:
    norm_i = whitened_inner_product(response_i, response_i, noise_variances)
    norm_j = whitened_inner_product(response_j, response_j, noise_variances)
    if norm_i <= 0.0 or norm_j <= 0.0:
        return float("nan")
    rho = whitened_inner_product(response_i, response_j, noise_variances) / np.sqrt(
        norm_i * norm_j
    )
    return float(np.clip(rho, -1.0, 1.0))


def _feature_support(
    observable_vector: ObservableVector,
    *,
    atlas_entry: AtlasEntryLite | None,
    morphology_atlas_ref: str | None,
) -> dict[str, float]:
    channels = set(observable_vector.channels)
    template_fit = (
        dict(observable_vector.template_fit)
        if isinstance(observable_vector.template_fit, Mapping)
        else {}
    )
    covariance_features = (
        dict(observable_vector.covariance_features)
        if isinstance(observable_vector.covariance_features, Mapping)
        else {}
    )
    local_global = covariance_features.get("local_global_degeneracy")
    local_global_payload = (
        dict(local_global) if isinstance(local_global, Mapping) else {}
    )
    distinguishing = {
        str(item)
        for item in local_global_payload.get("distinguishing_observables", ())
    }
    atlas_available = bool(
        morphology_atlas_ref
        or template_fit.get("atlas_ref")
        or (atlas_entry is not None and atlas_entry.atlas_id)
    )
    scalar_summary = 1.0 if ("TT" in channels or "scalar_summary" in channels) else 0.0
    direction = 1.0 if observable_vector.alm_features else scalar_summary
    depth = (
        1.0
        if (
            observable_vector.sky_support.selection_mode == "mock_calibrated"
            and observable_vector.sky_support.mock_coverage_status == "adequate"
        )
        else (
            0.4
            if observable_vector.sky_support.selection_mode == "mock_calibrated"
            else 0.0
        )
    )
    template = 1.0 if atlas_available else 0.0
    biposh = 1.0 if atlas_available and ("BiPoSH" in channels or "BiPoSH" in distinguishing) else 0.0
    ee = 1.0 if "EE" in channels else 0.0
    bb = 1.0 if ("BB" in channels or "BB" in distinguishing) else 0.0

    representation = str(covariance_features.get("representation", ""))
    basis_status = str(covariance_features.get("basis_reduction_status", ""))
    if representation == "sparse_mode_block_proxy":
        template *= 0.6
        biposh *= 0.6
    elif basis_status == "low_ell_harmonic_sparse_basis":
        template *= 0.9
        biposh *= 0.9

    return {
        "scalar_summary": scalar_summary,
        "direction": direction,
        "depth": depth,
        "template": template,
        "BiPoSH": biposh,
        "EE": ee,
        "BB": bb,
    }


def _response_vector(
    template: HypothesisResponseTemplate,
) -> np.ndarray:
    return np.asarray(
        [1.0 if basis in template.observable_basis else 0.0 for basis in _BASIS_ORDER],
        dtype=float,
    )


def _noise_variances(
    support: Mapping[str, float],
) -> np.ndarray:
    variances = []
    for basis in _BASIS_ORDER:
        value = float(support.get(basis, 0.0))
        variances.append(np.inf if value <= 0.0 else 1.0 / value)
    return np.asarray(variances, dtype=float)


def _pair_claim_tier(
    pair: tuple[str, str],
    *,
    overlap: float,
    support: Mapping[str, float],
    local_null_gate: GlobalTiltLocalNullGateDecision | None = None,
    survey_systematic_null_gate: SurveySystematicNullGateDecision | None = None,
) -> str:
    if not np.isfinite(overlap):
        return "blocked"
    ordered = tuple(sorted(pair))
    if ordered == ("global_tilt", "local_boost"):
        if local_null_gate is None or not local_null_gate.allowed:
            return "exploratory"
        if (
            survey_systematic_null_gate is None
            or not survey_systematic_null_gate.allowed
        ):
            return "exploratory"
        if (
            support.get("depth", 0.0) >= 0.95
            and support.get("template", 0.0) >= 0.75
            and (
                support.get("BiPoSH", 0.0) >= 0.5
                or support.get("BB", 0.0) >= 0.75
                or support.get("EE", 0.0) >= 0.75
            )
            and abs(overlap) < _CONDITIONAL_OVERLAP_THRESHOLD
        ):
            return "conditional"
    return "exploratory"


def _recommended_next_observable(
    pair: tuple[str, str],
    *,
    overlap: float,
    support: Mapping[str, float],
) -> str:
    if support.get("depth", 0.0) < 0.75:
        return "depth_direction_coherence"
    if support.get("template", 0.0) < 0.75 or support.get("BiPoSH", 0.0) < 0.5:
        return "atlas_template_biposh"
    if support.get("BB", 0.0) < 0.75 and support.get("EE", 0.0) < 0.75:
        return "TE_EE_BB_morphology"
    if np.isfinite(overlap) and abs(overlap) >= _CONDITIONAL_OVERLAP_THRESHOLD:
        return "null_mock_covariance"
    return next_observable_recommendation(pair)


def _calibrated_manifest(
    observable_vector: ObservableVector,
    *,
    claim_tier: str,
    production_status: str,
    caveats: list[str],
    morphology_atlas_ref: str | None,
    atlas_entry: AtlasEntryLite | None,
    support: Mapping[str, float],
    degeneracy_flags: Mapping[str, bool],
    recommendations: Mapping[str, str],
    claim_tier_by_pair: Mapping[str, str],
    local_null_gate: GlobalTiltLocalNullGateDecision | None,
    survey_systematic_null_gate: SurveySystematicNullGateDecision | None,
) -> ArtifactManifest:
    input_hashes = [observable_vector.manifest.artifact_id]
    if morphology_atlas_ref:
        input_hashes.append(str(morphology_atlas_ref))
    if atlas_entry is not None:
        input_hashes.append(atlas_entry.atlas_id)
    conditional_pairs = tuple(
        pair for pair, tier in sorted(claim_tier_by_pair.items()) if tier == "conditional"
    )
    blocked_pairs = tuple(
        pair for pair, tier in sorted(claim_tier_by_pair.items()) if tier == "blocked"
    )
    return ArtifactManifest(
        artifact_id="htt.discrimination_matrix",
        artifact_path="artifacts/htt/htt_discrimination_matrix.json",
        owner="HTT",
        implementation_scope="htt",
        claim_tier=claim_tier,  # type: ignore[arg-type]
        production_status=production_status,  # type: ignore[arg-type]
        created_by="htt.infer.local_global_discrimination.build_discrimination_matrix",
        git_commit=observable_vector.manifest.git_commit,
        config_hash=(
            "disc:"
            f"{observable_vector.manifest.config_hash}:"
            f"{observable_vector.sky_support.sky_support_hash}"
        ),
        input_hashes=input_hashes,
        code_version=observable_vector.manifest.code_version,
        schema_version=observable_vector.manifest.schema_version,
        caveats=caveats,
        statistics_definitions={
            "surface": "DiscriminationMatrix",
            "selection_mode": observable_vector.sky_support.selection_mode,
            "mock_coverage_status": observable_vector.sky_support.mock_coverage_status,
            "sky_support_hash": observable_vector.sky_support.sky_support_hash,
            "atlas_available": bool(morphology_atlas_ref or atlas_entry is not None),
            "support_profile": {basis: float(value) for basis, value in support.items()},
            "pair_claim_tier": dict(sorted(claim_tier_by_pair.items())),
            "pair_degeneracy_flags": dict(sorted(degeneracy_flags.items())),
            "pair_recommended_next_observable": dict(sorted(recommendations.items())),
            "conditional_pairs": list(conditional_pairs),
            "blocked_pairs": list(blocked_pairs),
            "transfer_source": "none",
            "null_mock_status": "local_and_survey_systematic_fpr_prerequisite_metadata",
            "ppc_status": "not_applicable",
            "loocv_status": "not_applicable",
            "authorization_scope": "local_global_discrimination_candidate_only",
            "claim_boundary": "survey_systematic_fpr_is_prerequisite_not_posterior_evidence",
            "native_morphology_atlas_status": "not_available_pre_native_solver",
            "local_null_fpr_gate": (
                None if local_null_gate is None else local_null_gate.to_metadata()
            ),
            "survey_systematic_null_fpr_gate": (
                None
                if survey_systematic_null_gate is None
                else survey_systematic_null_gate.to_metadata()
            ),
        },
    )


def build_discrimination_matrix(
    observable_vector: ObservableVector,
    *,
    atlas_entry: AtlasEntryLite | None = None,
    morphology_atlas_ref: str | None = None,
    local_null_fpr_report: LocalBoostNullFprReport | None = None,
    survey_systematic_null_fpr_report: SurveySystematicNullFprReport | None = None,
    local_null_report_hash: str | None = None,
    survey_systematic_null_config_hash: str | None = None,
    survey_systematic_null_input_hashes: tuple[str, ...] | None = None,
    survey_systematic_null_report_hash: str | None = None,
    response_overlap_config_hash: str | None = None,
    survey_response_overlap_config_hash: str | None = None,
    selection_metadata_hash: str | None = None,
    survey_axis_hash: str | None = None,
    hypotheses: tuple[str, ...] = ("local_boost", "global_tilt"),
) -> DiscriminationMatrix:
    """Build an observable-aware HTT discrimination matrix."""

    if len(hypotheses) < 2:
        raise ValueError("Need at least two hypotheses for a discrimination matrix")
    library = default_response_library()
    missing = [name for name in hypotheses if name not in library]
    if missing:
        raise ValueError(f"Unknown discrimination hypotheses: {missing}")

    support = _feature_support(
        observable_vector,
        atlas_entry=atlas_entry,
        morphology_atlas_ref=morphology_atlas_ref,
    )
    noise_variances = _noise_variances(support)
    responses = {
        name: _response_vector(library[name])
        for name in hypotheses
    }
    overlap = np.eye(len(hypotheses), dtype=float)
    response_norms = {
        name: whitened_inner_product(vector, vector, noise_variances)
        for name, vector in responses.items()
    }
    degeneracy_flags: dict[str, bool] = {}
    recommendations: dict[str, str] = {}
    claim_tier_by_pair: dict[str, str] = {}
    local_null_gate = evaluate_global_tilt_local_null_gate(
        local_null_fpr_report,
        config_hash=(
            None
            if local_null_fpr_report is None
            else local_null_fpr_report.bank.config.config_hash
        ),
        input_hashes=(
            None
            if local_null_fpr_report is None
            else local_null_fpr_report.bank.config.input_hashes
        ),
        report_hash=local_null_report_hash,
        response_overlap_config_hash=response_overlap_config_hash,
    )
    survey_systematic_null_gate = evaluate_survey_systematic_null_gate(
        survey_systematic_null_fpr_report,
        config_hash=survey_systematic_null_config_hash,
        input_hashes=survey_systematic_null_input_hashes,
        report_hash=survey_systematic_null_report_hash,
        response_overlap_config_hash=survey_response_overlap_config_hash,
        selection_metadata_hash=selection_metadata_hash,
        survey_axis_hash=survey_axis_hash,
        require_external_bindings=True,
    )

    for i, left in enumerate(hypotheses):
        for j, right in enumerate(hypotheses):
            if i == j:
                overlap[i, j] = 1.0 if response_norms[left] > 0.0 else 0.0
                continue
            if i > j:
                continue
            rho = _normalized_overlap(
                responses[left],
                responses[right],
                noise_variances,
            )
            overlap[i, j] = overlap[j, i] = 0.0 if not np.isfinite(rho) else rho
            pair = _pair_key(left, right)
            claim_tier = _pair_claim_tier(
                (left, right),
                overlap=rho,
                support=support,
                local_null_gate=local_null_gate,
                survey_systematic_null_gate=survey_systematic_null_gate,
            )
            claim_tier_by_pair[pair] = claim_tier
            degeneracy_flags[pair] = (not np.isfinite(rho)) or (
                abs(rho) >= _CONDITIONAL_OVERLAP_THRESHOLD
            )
            recommendations[pair] = _recommended_next_observable(
                (left, right),
                overlap=rho,
                support=support,
            )

    conditional_pair = claim_tier_by_pair.get("global_tilt|local_boost") == "conditional"
    caveats = [
        "pre_inference_only",
        "not_posterior_odds",
        "diagnostic_only_pre_native_solver",
        "survey_systematic_fpr_prerequisite_not_evidence",
        "native_morphology_atlas_not_available",
    ]
    if not conditional_pair:
        caveats.append("local_global_degeneracy_summary")
    if (
        "global_tilt" in hypotheses
        and "local_boost" in hypotheses
        and not local_null_gate.allowed
    ):
        caveats.append("local_boost_null_fpr_gate_not_satisfied")
        caveats.extend(
            f"local_null_gate_blocked:{reason}"
            for reason in local_null_gate.blocked_reasons
        )
    if (
        "global_tilt" in hypotheses
        and "local_boost" in hypotheses
        and not survey_systematic_null_gate.allowed
    ):
        caveats.append("survey_systematic_null_fpr_gate_not_satisfied")
        caveats.extend(
            f"survey_systematic_null_gate_blocked:{reason}"
            for reason in survey_systematic_null_gate.blocked_reasons
        )
    if support.get("template", 0.0) < 0.75:
        caveats.append("morphology_atlas_missing_or_weak")
    if support.get("BiPoSH", 0.0) < 0.75:
        caveats.append("basis_reduced_morphology_support")
    if support.get("depth", 0.0) < 0.75:
        caveats.append("mock_calibration_incomplete")

    claim_tier = "conditional" if conditional_pair else "exploratory"
    production_status = "diagnostic_only"
    manifest = _calibrated_manifest(
        observable_vector,
        claim_tier=claim_tier,
        production_status=production_status,
        caveats=list(dict.fromkeys(caveats)),
        morphology_atlas_ref=morphology_atlas_ref,
        atlas_entry=atlas_entry,
        support=support,
        degeneracy_flags=degeneracy_flags,
        recommendations=recommendations,
        claim_tier_by_pair=claim_tier_by_pair,
        local_null_gate=local_null_gate,
        survey_systematic_null_gate=survey_systematic_null_gate,
    )
    return DiscriminationMatrix(
        hypotheses=hypotheses,
        overlap_matrix=overlap,
        response_norms=response_norms,
        degeneracy_flags=degeneracy_flags,
        recommended_next_observable=recommendations,
        claim_tier_by_pair=claim_tier_by_pair,
        manifest=manifest,
    )


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
