"""Diagnostic MES branch information-gain compositor.

This module aggregates the already-gated PR-090 template branch and PR-091
covariance/BiPoSH branch reports.  It does not recompute branch bounds, create
HTT evidence, consume MIO certificates, or promote native-solver/family claims.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
import re
from typing import Any

import numpy as np

from common.contracts import ArtifactManifest, ClaimTier, ImplementationScope, Owner

from .mes_cov_bound import MesCovarianceBoundResult
from .mes_template_bound import MesTemplateBoundResult

__all__ = [
    "MesInformationGainBranch",
    "MesInformationGainReport",
    "build_mes_information_gain_report",
]


SCHEMA_VERSION = "htt.statistics.mes_information_gain.v1"
_CREATED_BY = "htt.statistics.mes_information_gain.build_mes_information_gain_report"
_DEFAULT_ARTIFACT_PATH = "memory://htt.statistics/mes-information-gain"
_DEFAULT_CAVEAT = (
    "COMMON diagnostic-only MES branch compositor; invalid and no-gain branches "
    "are not improvement candidates"
)
_REQUIRED_GATES = (
    "diagonal_bound_positive_finite",
    "source_branch_provenance_matches",
    "source_branch_bounds_positive_finite",
    "branch_separation_reported",
    "invalid_or_no_gain_not_plotted_as_improvement",
    "no_native_or_family_claim",
)
_FORBIDDEN_TEXT_PARTS = (
    "posterior",
    "likelihood",
    "evidence",
    "bayes",
    "certificate",
    "truth",
    "native solver result",
    "native validation",
    "transfer validated",
    "geometry detected",
    "detected geometry",
    "family identified",
    "family " + "identification",
    "family ranking",
    "morphology " + "compatibility",
    "universal " + "mes",
    "replaces diagonal",
    "strictly stronger",
)


@dataclass(frozen=True)
class MesInformationGainBranch:
    """One branch row in the diagnostic MES information-gain report."""

    name: str
    branch_role: str
    morphology_branch: bool
    bound: float | None
    raw_gain_ratio: float | None
    information_gain: float | None
    status: str
    branch_valid: bool
    improvement_candidate: bool
    selected: bool
    source_artifact_id: str | None
    source_production_status: str | None
    no_claim_reasons: tuple[str, ...]

    def as_payload(self) -> dict[str, Any]:
        return _json_ready(
            {
                "name": self.name,
                "branch_role": self.branch_role,
                "morphology_branch": self.morphology_branch,
                "bound": self.bound,
                "raw_gain_ratio": self.raw_gain_ratio,
                "information_gain": self.information_gain,
                "status": self.status,
                "branch_valid": self.branch_valid,
                "improvement_candidate": self.improvement_candidate,
                "selected": self.selected,
                "source_artifact_id": self.source_artifact_id,
                "source_production_status": self.source_production_status,
                "no_claim_reasons": list(self.no_claim_reasons),
            }
        )


@dataclass(frozen=True)
class MesInformationGainReport:
    """COMMON diagnostic report for branch-separated MES tightening ratios."""

    manifest: ArtifactManifest
    branches: tuple[MesInformationGainBranch, ...]
    diagonal_bound: float
    morphology_final_bound: float | None
    i_morph: float | None
    best_valid_branch: str | None
    morphology_gain_status: str
    improvement_candidate: bool
    no_claim_reasons: tuple[str, ...]
    transfer_source: str = "none"

    def as_payload(self) -> dict[str, Any]:
        definitions = self.manifest.statistics_definitions
        return _json_ready(
            {
                "owner": Owner.COMMON.value,
                "implementation_scope": ImplementationScope.COMMON.value,
                "claim_tier": self.manifest.claim_tier.value,
                "production_status": self.manifest.production_status,
                "schema_version": SCHEMA_VERSION,
                "manifest": _manifest_payload(self.manifest),
                "transfer_source": self.transfer_source,
                "diagonal_bound": self.diagonal_bound,
                "morphology_final_bound": self.morphology_final_bound,
                "i_morph": self.i_morph,
                "best_valid_branch": self.best_valid_branch,
                "morphology_gain_status": self.morphology_gain_status,
                "improvement_candidate": self.improvement_candidate,
                "branches": {
                    branch.name: branch.as_payload() for branch in self.branches
                },
                "branch_separation": {
                    "diag_branch": "diagonal_baseline",
                    "template_branch": "synthetic_template_mean",
                    "cov_branch": "synthetic_covariance_biposh",
                    "dyn_branch": "auxiliary_not_morphology_gain",
                    "merged_statistic_allowed": False,
                },
                "claim_status": {
                    "inference_status": "not_model_input",
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_result",
                    "geometry_status": "blocked_pre_native_atlas",
                    "family_status": "blocked_pre_native_atlas",
                },
                "generating_command": definitions.get("generating_command"),
                "git_commit": self.manifest.git_commit,
                "worktree_state": definitions.get("worktree_state"),
                "no_claim_reasons": list(self.no_claim_reasons),
                "caveats": list(self.manifest.caveats),
            }
        )


def build_mes_information_gain_report(
    *,
    template_result: MesTemplateBoundResult | None = None,
    covariance_result: MesCovarianceBoundResult | None = None,
    diagonal_bound: object | None = None,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    worktree_state: object | None,
    git_commit: object | None = None,
    artifact_id: object | None = None,
    artifact_path: object = _DEFAULT_ARTIFACT_PATH,
    caveats: Sequence[object] = (_DEFAULT_CAVEAT,),
) -> MesInformationGainReport:
    """Build a branch-separated diagnostic information-gain report."""

    if template_result is None and covariance_result is None:
        raise ValueError("at least one MES branch result is required")
    config_hash_text = _require_hash(config_hash, "config_hash")
    input_hash_list = list(_require_input_hashes(input_hashes, "input_hashes"))
    command_text = _non_empty(generating_command, "generating_command")
    git_commit_text = None if git_commit is None else _non_empty(git_commit, "git_commit")
    worktree_text = (
        None if worktree_state is None else _non_empty(worktree_state, "worktree_state")
    )
    if git_commit_text is None and worktree_text is None:
        raise ValueError(
            "build_mes_information_gain_report requires git_commit or worktree_state"
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

    source_reports = [
        result.report
        for result in (template_result, covariance_result)
        if result is not None
    ]
    diagonal = (
        _positive_finite(diagonal_bound, "diagonal_bound")
        if diagonal_bound is not None
        else _positive_finite(source_reports[0].diagonal_bound, "source diagonal_bound")
    )

    branches: list[MesInformationGainBranch] = [
        MesInformationGainBranch(
            name="diag",
            branch_role="diagonal_baseline",
            morphology_branch=False,
            bound=diagonal,
            raw_gain_ratio=1.0,
            information_gain=1.0,
            status="baseline",
            branch_valid=True,
            improvement_candidate=False,
            selected=False,
            source_artifact_id=None,
            source_production_status="diagnostic_only",
            no_claim_reasons=(),
        )
    ]
    no_claim_reasons: list[str] = []

    template_branch = _source_branch(
        name="template",
        branch_role="synthetic_template_mean",
        result=template_result,
        diagonal_bound=diagonal,
        config_hash=config_hash_text,
        input_hashes=input_hash_list,
    )
    covariance_branch = _source_branch(
        name="cov",
        branch_role="synthetic_covariance_biposh",
        result=covariance_result,
        diagonal_bound=diagonal,
        config_hash=config_hash_text,
        input_hashes=input_hash_list,
    )
    branches.extend((template_branch, covariance_branch))
    branches.append(
        _dynamical_branch(
            (template_result, covariance_result),
            diagonal_bound=diagonal,
        )
    )

    for branch in branches:
        if branch.morphology_branch and branch.status != "missing":
            no_claim_reasons.extend(branch.no_claim_reasons)

    provenance_blocked = any(_is_provenance_reason(reason) for reason in no_claim_reasons)
    valid_morphology = [
        branch
        for branch in branches
        if (
            not provenance_blocked
            and branch.morphology_branch
            and branch.branch_valid
            and branch.bound is not None
        )
    ]
    selected_name: str | None = None
    morphology_final_bound: float | None = None
    i_morph: float | None = None
    morphology_gain_status = "no_claim"
    improvement_candidate = False
    if valid_morphology:
        selected = min(valid_morphology, key=lambda branch: float(branch.bound))
        selected_name = selected.name
        morphology_final_bound = selected.bound
        i_morph = selected.information_gain
        improvement_candidate = bool(selected.improvement_candidate)
        morphology_gain_status = "improvement" if improvement_candidate else "no_gain"
        branches = [
            _with_selected(branch, selected=branch.name == selected_name)
            for branch in branches
        ]
    else:
        no_claim_reasons.append("no_valid_morphology_branch")

    no_claim_reasons = tuple(dict.fromkeys(no_claim_reasons))
    claim_tier = (
        ClaimTier.DIAGNOSTIC_ONLY
        if valid_morphology
        else ClaimTier.BLOCKED
    )
    production_status = _production_status(valid_morphology, no_claim_reasons)
    gates = _gate_status(
        has_valid_morphology_branch=bool(valid_morphology),
        no_claim_reasons=no_claim_reasons,
    )
    stats_definitions = {
        "surface": "MesInformationGainReport",
        "branch_role": "branch_separated_mes_information_gain",
        "transfer_source": "none",
        "diagonal_bound": diagonal,
        "morphology_final_bound": morphology_final_bound,
        "i_morph": i_morph,
        "best_valid_branch": selected_name,
        "morphology_gain_status": morphology_gain_status,
        "improvement_candidate": improvement_candidate,
        "branch_statuses": {branch.name: branch.status for branch in branches},
        "source_artifact_ids": {
            branch.name: branch.source_artifact_id
            for branch in branches
            if branch.source_artifact_id is not None
        },
        "sky_support_status": _collect_source_status(
            (template_result, covariance_result),
            "sky_support_status",
        ),
        "mask_status": _collect_source_status(
            (template_result, covariance_result),
            "mask_status",
        ),
        "covariance_status": _collect_source_status(
            (template_result, covariance_result),
            "covariance_status",
        ),
        "null_mock_status": _collect_source_status(
            (template_result, covariance_result),
            "null_mock_status",
        ),
        "generating_command": command_text,
        "git_commit": git_commit_text,
        "worktree_state": worktree_text,
        "no_claim_reasons": list(no_claim_reasons),
        "does_not_replace_diagonal_mes": True,
        "invalid_or_no_gain_plotted_as_improvement": False,
        "p_values_emitted": False,
    }
    manifest = ArtifactManifest(
        artifact_id=str(artifact_id or _stable_hash({
            "schema_version": SCHEMA_VERSION,
            "config_hash": config_hash_text,
            "input_hashes": input_hash_list,
            "source_artifact_ids": stats_definitions["source_artifact_ids"],
        })),
        artifact_path=_non_empty(artifact_path, "artifact_path"),
        owner=Owner.COMMON,
        implementation_scope=ImplementationScope.COMMON,
        claim_tier=claim_tier,
        production_status=production_status,
        created_by=_CREATED_BY,
        git_commit=git_commit_text,
        config_hash=config_hash_text,
        input_hashes=input_hash_list,
        code_version=git_commit_text or worktree_text or "unknown",
        schema_version=SCHEMA_VERSION,
        caveats=list(caveat_list),
        required_gates=list(_REQUIRED_GATES),
        passed_gates=gates["passed"],
        failed_gates=gates["failed"],
        statistics_definitions=stats_definitions,
    )
    return MesInformationGainReport(
        manifest=manifest,
        branches=tuple(branches),
        diagonal_bound=diagonal,
        morphology_final_bound=morphology_final_bound,
        i_morph=i_morph,
        best_valid_branch=selected_name,
        morphology_gain_status=morphology_gain_status,
        improvement_candidate=improvement_candidate,
        no_claim_reasons=no_claim_reasons,
    )


def _source_branch(
    *,
    name: str,
    branch_role: str,
    result: MesTemplateBoundResult | MesCovarianceBoundResult | None,
    diagonal_bound: float,
    config_hash: str,
    input_hashes: Sequence[str],
) -> MesInformationGainBranch:
    if result is None:
        return MesInformationGainBranch(
            name=name,
            branch_role=branch_role,
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
            no_claim_reasons=(f"{name}_branch_missing",),
        )
    report = result.report
    source_reasons = list(getattr(result, "no_claim_reasons", ()))
    source_reasons.extend(
        _source_manifest_reasons(
            name=name,
            report=report,
            diagonal_bound=diagonal_bound,
            config_hash=config_hash,
            input_hashes=input_hashes,
        )
    )
    source_reasons.extend(_failed_gate_reasons(name, report))
    if source_reasons or not bool(getattr(result, "synthetic_bound_available", False)):
        if not source_reasons:
            source_reasons.append(f"{name}_source_no_claim")
        return MesInformationGainBranch(
            name=name,
            branch_role=branch_role,
            morphology_branch=True,
            bound=None,
            raw_gain_ratio=None,
            information_gain=None,
            status="no_claim",
            branch_valid=False,
            improvement_candidate=False,
            selected=False,
            source_artifact_id=report.manifest.artifact_id,
            source_production_status=report.manifest.production_status,
            no_claim_reasons=tuple(dict.fromkeys(source_reasons)),
        )
    bound = _positive_finite(report.covariance_bound, f"{name} covariance_bound")
    _positive_finite(report.final_bound, f"{name} final_bound")
    raw_gain = diagonal_bound / bound
    if bound < diagonal_bound:
        status = "improvement"
        information_gain = raw_gain
        improvement_candidate = True
    else:
        status = "no_gain"
        information_gain = 1.0
        improvement_candidate = False
    return MesInformationGainBranch(
        name=name,
        branch_role=branch_role,
        morphology_branch=True,
        bound=bound,
        raw_gain_ratio=raw_gain,
        information_gain=information_gain,
        status=status,
        branch_valid=True,
        improvement_candidate=improvement_candidate,
        selected=False,
        source_artifact_id=report.manifest.artifact_id,
        source_production_status=report.manifest.production_status,
        no_claim_reasons=(),
    )


def _dynamical_branch(
    results: Sequence[MesTemplateBoundResult | MesCovarianceBoundResult | None],
    *,
    diagonal_bound: float,
) -> MesInformationGainBranch:
    candidates: list[tuple[float, str, str]] = []
    for result in results:
        if result is None:
            continue
        dyn = result.report.dynamical_bound
        if dyn is None:
            continue
        bound = _positive_finite(dyn, "dynamical_bound")
        candidates.append(
            (
                bound,
                result.report.manifest.artifact_id,
                result.report.manifest.production_status,
            )
        )
    if not candidates:
        return MesInformationGainBranch(
            name="dyn",
            branch_role="auxiliary_dynamical_bound",
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
            no_claim_reasons=("dynamical_branch_missing",),
        )
    bound, artifact_id, production_status = min(candidates, key=lambda item: item[0])
    raw_gain = diagonal_bound / bound
    return MesInformationGainBranch(
        name="dyn",
        branch_role="auxiliary_dynamical_bound",
        morphology_branch=False,
        bound=bound,
        raw_gain_ratio=raw_gain,
        information_gain=raw_gain if bound < diagonal_bound else 1.0,
        status="auxiliary_tightening" if bound < diagonal_bound else "auxiliary_no_gain",
        branch_valid=True,
        improvement_candidate=False,
        selected=False,
        source_artifact_id=artifact_id,
        source_production_status=production_status,
        no_claim_reasons=(),
    )


def _source_manifest_reasons(
    *,
    name: str,
    report: Any,
    diagonal_bound: float,
    config_hash: str,
    input_hashes: Sequence[str],
) -> list[str]:
    reasons: list[str] = []
    manifest = report.manifest
    if manifest.owner != Owner.COMMON:
        reasons.append(f"{name}_owner_mismatch")
    if manifest.implementation_scope != ImplementationScope.COMMON:
        reasons.append(f"{name}_scope_mismatch")
    if manifest.config_hash != config_hash:
        reasons.append(f"{name}_config_hash_mismatch")
    if list(manifest.input_hashes) != list(input_hashes):
        reasons.append(f"{name}_input_hashes_mismatch")
    try:
        source_diagonal = _positive_finite(report.diagonal_bound, f"{name} diagonal_bound")
    except ValueError as exc:
        raise ValueError(f"{name} diagonal_bound must be positive finite") from exc
    if not math.isclose(source_diagonal, diagonal_bound, rel_tol=1.0e-12, abs_tol=1.0e-12):
        reasons.append(f"{name}_diagonal_bound_mismatch")
    transfer_source = manifest.statistics_definitions.get("transfer_source")
    if transfer_source != "none":
        reasons.append(f"{name}_transfer_source_not_none")
    return reasons


def _failed_gate_reasons(name: str, report: Any) -> list[str]:
    return [
        f"{name}_failed_gate_{failed_gate}"
        for failed_gate in report.manifest.failed_gates
    ]


def _with_selected(
    branch: MesInformationGainBranch,
    *,
    selected: bool,
) -> MesInformationGainBranch:
    return MesInformationGainBranch(
        name=branch.name,
        branch_role=branch.branch_role,
        morphology_branch=branch.morphology_branch,
        bound=branch.bound,
        raw_gain_ratio=branch.raw_gain_ratio,
        information_gain=branch.information_gain,
        status=branch.status,
        branch_valid=branch.branch_valid,
        improvement_candidate=branch.improvement_candidate,
        selected=selected,
        source_artifact_id=branch.source_artifact_id,
        source_production_status=branch.source_production_status,
        no_claim_reasons=branch.no_claim_reasons,
    )


def _production_status(
    valid_morphology: Sequence[MesInformationGainBranch],
    no_claim_reasons: Sequence[str],
) -> str:
    if valid_morphology:
        return "diagnostic_only"
    if any(_is_provenance_reason(reason) for reason in no_claim_reasons):
        return "blocked_provenance_mismatch"
    if any("null" in reason for reason in no_claim_reasons):
        return "blocked_missing_null_mocks"
    if any("rank" in reason or "zero_projected_response" in reason for reason in no_claim_reasons):
        return "blocked_rank_deficient"
    if any("covariance" in reason for reason in no_claim_reasons):
        return "blocked_missing_covariance"
    return "blocked_provenance_mismatch"


def _gate_status(
    *,
    has_valid_morphology_branch: bool,
    no_claim_reasons: Sequence[str],
) -> dict[str, list[str]]:
    passed = [
        "diagonal_bound_positive_finite",
        "branch_separation_reported",
        "invalid_or_no_gain_not_plotted_as_improvement",
        "no_native_or_family_claim",
    ]
    failed: list[str] = []
    if has_valid_morphology_branch:
        passed.extend(
            [
                "source_branch_provenance_matches",
                "source_branch_bounds_positive_finite",
            ]
        )
    else:
        failed.extend(
            [
                "source_branch_provenance_matches",
                "source_branch_bounds_positive_finite",
            ]
        )
    if any("mismatch" in reason for reason in no_claim_reasons):
        failed.append("source_branch_provenance_matches")
    return {"passed": list(dict.fromkeys(passed)), "failed": list(dict.fromkeys(failed))}


def _is_provenance_reason(reason: str) -> bool:
    return any(
        marker in reason
        for marker in (
            "mismatch",
            "owner_",
            "scope_",
            "transfer_source_not_none",
        )
    )


def _collect_source_status(
    results: Sequence[MesTemplateBoundResult | MesCovarianceBoundResult | None],
    key: str,
) -> list[str]:
    values: list[str] = []
    for result in results:
        if result is None:
            continue
        value = result.report.manifest.statistics_definitions.get(key)
        if isinstance(value, str) and value not in values:
            values.append(value)
    return values


def _positive_finite(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be positive finite") from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be positive finite")
    return number


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} is required")
    return text


def _require_hash(value: object, name: str) -> str:
    text = _non_empty(value, name)
    if not text.startswith("sha256:"):
        raise ValueError(f"{name} must start with sha256:")
    return text


def _require_input_hashes(values: Sequence[object], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    hashes = tuple(_require_hash(value, f"{name} entry") for value in values)
    if not hashes:
        raise ValueError(f"{name} must contain at least one entry")
    return hashes


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    return {
        "artifact_id": manifest.artifact_id,
        "artifact_path": manifest.artifact_path,
        "owner": manifest.owner.value,
        "implementation_scope": manifest.implementation_scope.value,
        "claim_tier": manifest.claim_tier.value,
        "production_status": manifest.production_status,
        "created_by": manifest.created_by,
        "git_commit": manifest.git_commit,
        "config_hash": manifest.config_hash,
        "input_hashes": list(manifest.input_hashes),
        "code_version": manifest.code_version,
        "schema_version": manifest.schema_version,
        "caveats": list(manifest.caveats),
        "required_gates": list(manifest.required_gates),
        "passed_gates": list(manifest.passed_gates),
        "failed_gates": list(manifest.failed_gates),
        "statistics_definitions": _json_ready(manifest.statistics_definitions),
    }


def _json_ready(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return _json_ready(value.tolist())
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("payload floats must be finite")
        return value
    return value


def _normalise_text(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _reject_overclaim_text(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_overclaim_text(key)
            if str(key) == "does_not_establish":
                continue
            _reject_overclaim_text(item)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            _reject_overclaim_text(item)
        return
    if not isinstance(value, (str, bytes)):
        return
    text = _normalise_text(value)
    for forbidden in _FORBIDDEN_TEXT_PARTS:
        if forbidden in text:
            raise ValueError(f"forbidden PR-092 claim text: {value!r}")
