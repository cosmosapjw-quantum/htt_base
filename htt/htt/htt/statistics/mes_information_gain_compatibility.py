"""Exact one-dimensional compatibility view of matrix response information.

The historical branch-bound compositor remains byte-for-byte unchanged in
``mes_information_gain.py`` for old result-pack replay.  This module is the
only active bridge from PR-255's matrix report to its legacy scalar report
shape, and it refuses every non-one-dimensional or covariance-null case.
"""

from __future__ import annotations

from collections.abc import Sequence
import math

from common.anchor_geometry import NormalizerSpec
from common.anchored_response_geometry import (
    SchurMorphologyInformationReport,
    revalidate_schur_morphology_information,
)
from common.contracts import ArtifactManifest, ClaimTier, ImplementationScope, Owner

from .mes_information_gain import (
    SCHEMA_VERSION,
    MesInformationGainBranch,
    MesInformationGainReport,
    _DEFAULT_ARTIFACT_PATH,
    _non_empty,
    _reject_overclaim_text,
    _require_hash,
    _require_input_hashes,
    _stable_hash,
)


def build_mes_information_gain_compatibility_view(
    *,
    matrix_report: SchurMorphologyInformationReport,
    normalizer: NormalizerSpec,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    worktree_state: object | None,
    git_commit: object | None = None,
    artifact_id: object | None = None,
    artifact_path: object = _DEFAULT_ARTIFACT_PATH,
    caveats: Sequence[object] = (
        "Exact one-dimensional compatibility view of a matrix-valued "
        "supported-quotient response report; not information from anchor scaling",
    ),
) -> MesInformationGainReport:
    """Derive the legacy scalar shape from an exact one-dimensional matrix case."""

    if type(matrix_report) is not SchurMorphologyInformationReport:
        raise TypeError(
            "matrix_report must be an exact SchurMorphologyInformationReport"
        )
    matrix_report = revalidate_schur_morphology_information(
        matrix_report,
        normalizer=normalizer,
    )
    if not matrix_report.exact_one_dimensional_reduction:
        raise ValueError(
            "MesInformationGainReport compatibility requires an exact "
            "one-dimensional baseline and joint matrix reduction"
        )
    baseline_information = float(matrix_report.baseline_information[0][0])
    joint_information = float(matrix_report.joint_information[0][0])
    if not (
        math.isfinite(baseline_information)
        and math.isfinite(joint_information)
        and baseline_information > 0.0
        and joint_information >= baseline_information
    ):
        raise ValueError(
            "one-dimensional information matrices must be finite, positive, "
            "and non-decreasing"
        )
    diagonal = 1.0 / math.sqrt(baseline_information)
    final = 1.0 / math.sqrt(joint_information)
    gain = diagonal / final

    config_hash_text = _require_hash(config_hash, "config_hash")
    input_hash_list = list(_require_input_hashes(input_hashes, "input_hashes"))
    command_text = _non_empty(generating_command, "generating_command")
    git_commit_text = (
        None if git_commit is None else _non_empty(git_commit, "git_commit")
    )
    worktree_text = (
        None
        if worktree_state is None
        else _non_empty(worktree_state, "worktree_state")
    )
    if git_commit_text is None and worktree_text is None:
        raise ValueError(
            "compatibility view requires git_commit or worktree_state"
        )
    caveat_list = tuple(_non_empty(item, "caveat") for item in caveats)
    _reject_overclaim_text(
        {
            "artifact_id": artifact_id or "",
            "artifact_path": artifact_path,
            "generating_command": command_text,
            "git_commit": git_commit_text or "",
            "worktree_state": worktree_text or "",
            "caveats": list(caveat_list),
        }
    )
    source_id = matrix_report.joint_covariance_content_id
    no_claim_reasons = (
        "exact_1d_matrix_compatibility_view_only",
        "anchor_scaling_is_not_information_gain",
        "not_a_posterior_evidence_or_family_classifier",
    )
    branches = (
        MesInformationGainBranch(
            name="diag",
            branch_role="one_dimensional_baseline_matrix",
            morphology_branch=False,
            bound=diagonal,
            raw_gain_ratio=1.0,
            information_gain=1.0,
            status="baseline",
            branch_valid=True,
            improvement_candidate=False,
            selected=False,
            source_artifact_id=source_id,
            source_production_status="diagnostic_only",
            no_claim_reasons=no_claim_reasons,
        ),
        MesInformationGainBranch(
            name="template",
            branch_role="legacy_template_branch_not_used",
            morphology_branch=True,
            bound=None,
            raw_gain_ratio=None,
            information_gain=None,
            status="missing",
            branch_valid=False,
            improvement_candidate=False,
            selected=False,
            source_artifact_id=None,
            source_production_status=None,
            no_claim_reasons=("legacy_branch_not_active",),
        ),
        MesInformationGainBranch(
            name="cov",
            branch_role="exact_1d_schur_matrix_reduction",
            morphology_branch=True,
            bound=final,
            raw_gain_ratio=gain,
            information_gain=gain,
            status="matrix_compatibility",
            branch_valid=True,
            improvement_candidate=gain > 1.0,
            selected=True,
            source_artifact_id=source_id,
            source_production_status="diagnostic_only",
            no_claim_reasons=no_claim_reasons,
        ),
        MesInformationGainBranch(
            name="dyn",
            branch_role="auxiliary_not_morphology_gain",
            morphology_branch=False,
            bound=None,
            raw_gain_ratio=None,
            information_gain=None,
            status="missing",
            branch_valid=False,
            improvement_candidate=False,
            selected=False,
            source_artifact_id=None,
            source_production_status=None,
            no_claim_reasons=("legacy_branch_not_active",),
        ),
    )
    stats_definitions = {
        "surface": "MesInformationGainReport",
        "compatibility_mode": "exact_1d_schur_matrix_reduction",
        "matrix_schema": "common.anchored_response_geometry",
        "normalizer_id": normalizer.normalizer_id,
        "normalizer_source_identity": normalizer.source_identity,
        "matrix_source_id": source_id,
        "diagonal_bound": diagonal,
        "morphology_final_bound": final,
        "i_morph": gain,
        "generating_command": command_text,
        "git_commit": git_commit_text,
        "worktree_state": worktree_text,
        "no_claim_reasons": list(no_claim_reasons),
        "anchor_scaling_information_gain": False,
        "parameter_dimension": 1,
        "baseline_rank": 1,
        "joint_rank": 1,
        "p_values_emitted": False,
    }
    manifest = ArtifactManifest(
        artifact_id=str(
            artifact_id
            or _stable_hash(
                {
                    "schema_version": SCHEMA_VERSION,
                    "compatibility_mode": (
                        "exact_1d_schur_matrix_reduction"
                    ),
                    "config_hash": config_hash_text,
                    "input_hashes": input_hash_list,
                    "matrix_source_id": source_id,
                }
            )
        ),
        artifact_path=_non_empty(artifact_path, "artifact_path"),
        owner=Owner.COMMON,
        implementation_scope=ImplementationScope.COMMON,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
        production_status="diagnostic_only",
        created_by=(
            "htt.statistics.mes_information_gain_compatibility."
            "build_mes_information_gain_compatibility_view"
        ),
        git_commit=git_commit_text,
        config_hash=config_hash_text,
        input_hashes=input_hash_list,
        code_version=git_commit_text or worktree_text or "unknown",
        schema_version=SCHEMA_VERSION,
        caveats=list(caveat_list),
        required_gates=[
            "exact_one_dimensional_matrix_reduction",
            "anchor_scaling_not_information_gain",
            "no_native_or_family_claim",
        ],
        passed_gates=[
            "exact_one_dimensional_matrix_reduction",
            "anchor_scaling_not_information_gain",
            "no_native_or_family_claim",
        ],
        failed_gates=[],
        statistics_definitions=stats_definitions,
    )
    return MesInformationGainReport(
        manifest=manifest,
        branches=branches,
        diagonal_bound=diagonal,
        morphology_final_bound=final,
        i_morph=gain,
        best_valid_branch="cov",
        morphology_gain_status="matrix_compatibility",
        improvement_candidate=gain > 1.0,
        no_claim_reasons=no_claim_reasons,
    )


__all__ = ["build_mes_information_gain_compatibility_view"]
