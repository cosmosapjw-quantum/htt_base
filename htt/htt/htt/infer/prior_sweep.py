"""HTT prior-sensitivity and inference-adequacy gates for PR-065."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
)
from htt.infer.null_competition import (
    FamilyCompetitionResult,
    MatchedNullCompetitionReport,
    NullCompetitionHook,
    NullCompetitionResult,
    build_matched_null_competition_report,
)
from htt.infer.matched_complexity import MatchedComplexityHook

SCHEMA_VERSION = "htt.infer.inference_adequacy.v1"
_PRIOR_CREATED_BY = "htt.infer.prior_sweep.build_prior_sweep_report"
_ADEQUACY_CREATED_BY = "htt.infer.prior_sweep.build_inference_adequacy_report"
_DEFAULT_PRIOR_PATH = "memory://htt/infer/prior_sweep.json"
_DEFAULT_ADEQUACY_PATH = "memory://htt/infer/inference_adequacy.json"
_DEFAULT_CAVEATS = (
    "diagnostic_only_pre_solver_inference_adequacy",
    "prior_ppc_loocv_required_for_evidence_language",
    "matched_null_report_required_before_evidence_language",
    "no_native_solver_or_family_claim",
)


def json_ready(value: object) -> Any:
    if isinstance(value, np.ndarray):
        return [json_ready(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return json_ready(value.item())
    if isinstance(value, Mapping):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("payload floats must be finite")
        return value
    return value


def stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    payload = json_ready(asdict(manifest))
    if not isinstance(payload, dict):
        raise TypeError("manifest payload must be a mapping")
    return payload


def non_empty(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def input_hashes(values: Sequence[object], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise ValueError(f"{field_name} must be a non-empty sequence")
    return tuple(non_empty(value, field_name) for value in values)


def finite_float(value: object, field_name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite")
    return out


def positive_float(value: object, field_name: str) -> float:
    out = finite_float(value, field_name)
    if out <= 0.0:
        raise ValueError(f"{field_name} must be positive")
    return out


def finite_mapping(values: Mapping[str, object], field_name: str) -> dict[str, float]:
    if not values:
        raise ValueError(f"{field_name} must be non-empty")
    return {
        non_empty(name, f"{field_name}.key"): finite_float(
            value, f"{field_name}[{name}]"
        )
        for name, value in values.items()
    }


def dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def metadata(
    *,
    artifact_id: object,
    artifact_path: object,
    config_hash: object,
    input_hashes_value: Sequence[object],
    generating_command: object,
    worktree_state: object | None,
    git_commit: object | None,
    transfer_source: object,
    caveats: Sequence[object],
) -> dict[str, object]:
    worktree_text = (
        None if worktree_state is None else non_empty(worktree_state, "worktree_state")
    )
    git_text = None if git_commit is None else non_empty(git_commit, "git_commit")
    if worktree_text is None and git_text is None:
        raise ValueError("git_commit or worktree_state is required")
    transfer_text = non_empty(transfer_source, "transfer_source")
    if transfer_text != "none":
        raise ValueError("PR-065 adequacy reports only support transfer_source='none'")
    caveat_tuple = tuple(non_empty(item, "caveat") for item in caveats)
    if not caveat_tuple:
        raise ValueError("caveats must be non-empty")
    return {
        "artifact_id": non_empty(artifact_id, "artifact_id"),
        "artifact_path": non_empty(artifact_path, "artifact_path"),
        "config_hash": non_empty(config_hash, "config_hash"),
        "input_hashes": input_hashes(input_hashes_value, "input_hashes"),
        "generating_command": non_empty(generating_command, "generating_command"),
        "worktree_state": worktree_text,
        "git_commit": git_text,
        "transfer_source": transfer_text,
        "caveats": caveat_tuple,
    }


@dataclass(frozen=True)
class PriorSweepReport:
    """Manifest-backed prior-sensitivity gate for HTT evidence bundles."""

    manifest: ArtifactManifest
    model: str
    baseline_log_evidence: float
    sweep_log_evidences: Mapping[str, float]
    sensitivity_threshold: float
    max_abs_delta_log_evidence: float
    prior_sweep_status: str
    blocked_reasons: tuple[str, ...]
    report_hash: str
    generating_command: str
    worktree_state: str | None
    git_commit: str | None
    transfer_source: str = "none"

    @property
    def ready_for_claims(self) -> bool:
        return self.prior_sweep_status == "prior_sweep_ready"

    def as_payload(self) -> dict[str, Any]:
        sweep_points = {
            name: {
                "log_evidence": float(value),
                "delta_log_evidence": float(value - self.baseline_log_evidence),
                "abs_delta_log_evidence": abs(
                    float(value - self.baseline_log_evidence)
                ),
            }
            for name, value in sorted(self.sweep_log_evidences.items())
        }
        return json_ready(
            {
                "owner": Owner.HTT.value,
                "implementation_scope": ImplementationScope.HTT.value,
                "claim_tier": self.manifest.claim_tier.value,
                "production_status": self.manifest.production_status,
                "schema_version": SCHEMA_VERSION,
                "manifest": manifest_payload(self.manifest),
                "transfer_source": self.transfer_source,
                "config_hash": self.manifest.config_hash,
                "input_hashes": list(self.manifest.input_hashes),
                "sky_support_status": "not_directional",
                "null_mock_status": (
                    "prior_sweep_recorded"
                    if self.ready_for_claims
                    else "prior_sweep_blocked"
                ),
                "generating_command": self.generating_command,
                "git_commit_or_worktree_state": self.git_commit
                or self.worktree_state
                or "unknown",
                "git_commit": self.git_commit,
                "worktree_state": self.worktree_state,
                "report_hash": self.report_hash,
                "model": self.model,
                "baseline_log_evidence": self.baseline_log_evidence,
                "sensitivity_threshold": self.sensitivity_threshold,
                "max_abs_delta_log_evidence": self.max_abs_delta_log_evidence,
                "prior_sweep_status": self.prior_sweep_status,
                "ready_for_claims": self.ready_for_claims,
                "sweep_points": sweep_points,
                "blocked_reasons": list(self.blocked_reasons),
                "caveats": list(self.manifest.caveats),
                "claim_status": {
                    "owner": "HTT",
                    "surface": "prior_sweep",
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_output",
                    "family_status": "blocked_pre_native_atlas",
                },
            }
        )


@dataclass(frozen=True)
class InferenceAdequacyReport:
    """Composite PR-065 adequacy gate over prior, PPC, LOOCV, and matched nulls."""

    manifest: ArtifactManifest
    prior_sweep_report: PriorSweepReport | None
    posterior_predictive_report: object | None
    loocv_report: object | None
    matched_null_report: MatchedNullCompetitionReport | None
    matched_null_hook: NullCompetitionHook | None
    inference_adequacy_status: str
    decisive_evidence_language_status: str
    blocked_reasons: tuple[str, ...]
    report_hash: str
    decisive_claim_requested: bool
    generating_command: str
    worktree_state: str | None
    git_commit: str | None
    transfer_source: str = "none"

    @property
    def ready_for_claims(self) -> bool:
        return self.inference_adequacy_status == "inference_adequacy_ready"

    def as_payload(self) -> dict[str, Any]:
        matched_null = _canonical_matched_null_hook_payload(
            self.matched_null_hook,
            self.matched_null_report,
        )
        prior_status = status_of(
            self.prior_sweep_report,
            "prior_sweep_status",
            "missing_prior_sweep_report",
        )
        ppc_status = status_of(
            self.posterior_predictive_report,
            "posterior_predictive_status",
            "missing_posterior_predictive_report",
        )
        loocv_status = status_of(
            self.loocv_report,
            "loocv_status",
            "missing_loocv_report",
        )
        matched_status = (
            "missing_matched_null_hook"
            if matched_null is None
            else str(matched_null["matched_null_status"])
        )
        return json_ready(
            {
                "owner": Owner.HTT.value,
                "implementation_scope": ImplementationScope.HTT.value,
                "claim_tier": self.manifest.claim_tier.value,
                "production_status": self.manifest.production_status,
                "schema_version": SCHEMA_VERSION,
                "manifest": manifest_payload(self.manifest),
                "transfer_source": self.transfer_source,
                "config_hash": self.manifest.config_hash,
                "input_hashes": list(self.manifest.input_hashes),
                "sky_support_status": "not_directional",
                "null_mock_status": (
                    "prior_ppc_loocv_recorded"
                    if self.ready_for_claims
                    else "prior_ppc_loocv_blocked"
                ),
                "generating_command": self.generating_command,
                "git_commit_or_worktree_state": self.git_commit
                or self.worktree_state
                or "unknown",
                "git_commit": self.git_commit,
                "worktree_state": self.worktree_state,
                "report_hash": self.report_hash,
                "inference_adequacy_status": self.inference_adequacy_status,
                "decisive_evidence_language_status": self.decisive_evidence_language_status,
                "decisive_claim_requested": self.decisive_claim_requested,
                "ready_for_claims": self.ready_for_claims,
                "prior_sweep_status": prior_status,
                "posterior_predictive_status": ppc_status,
                "loocv_status": loocv_status,
                "matched_null_status": matched_status,
                "matched_null_hook": matched_null,
                "prior_sweep_ref": report_ref(self.prior_sweep_report),
                "posterior_predictive_ref": report_ref(
                    self.posterior_predictive_report
                ),
                "loocv_ref": report_ref(self.loocv_report),
                "matched_null_report_hash": (
                    None
                    if matched_null is None
                    else matched_null["matched_null_report_hash"]
                ),
                "matched_null_blocked_reasons": (
                    [] if matched_null is None else matched_null["blocked_reasons"]
                ),
                "blocked_reasons": list(self.blocked_reasons),
                "caveats": list(self.manifest.caveats),
                "claim_status": {
                    "owner": "HTT",
                    "surface": "inference_adequacy",
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_output",
                    "family_status": "blocked_pre_native_atlas",
                },
            }
        )


def report_ref(report: object | None) -> str | None:
    if report is None:
        return None
    report_type, _, _ = recognized_report_type(report)
    if type(report) is not report_type:
        raise TypeError(
            "inference adequacy reports require exact recognized report types"
        )
    return str(report.report_hash)  # type: ignore[attr-defined]


def status_of(report: object | None, field_name: str, missing: str) -> str:
    if report is None:
        return missing
    report_type, status_field, _ = recognized_report_type(report)
    if type(report) is not report_type or field_name != status_field:
        raise TypeError(
            "inference adequacy status requires an exact recognized report type"
        )
    return str(getattr(report, status_field))


def report_ready(report: object | None) -> bool:
    if report is None:
        return False
    report_type, status_field, ready_status = recognized_report_type(report)
    if type(report) is not report_type:
        raise TypeError(
            "inference adequacy readiness requires exact recognized report types"
        )
    return str(getattr(report, status_field)) == ready_status


def recognized_report_type(report: object) -> tuple[type[object], str, str]:
    """Return the canonical runtime type and status contract for a component.

    Imports are intentionally local: the PPC and LOOCV modules reuse helpers
    from this module, so importing their classes at module load time would
    create a cycle.  Exact type identity is required; subclasses and duck-typed
    namespaces are not evidence receipts.
    """

    from htt.infer.loocv import LoocvReport
    from htt.infer.posterior_predictive import PosteriorPredictiveReport

    if type(report) is PriorSweepReport:
        return PriorSweepReport, "prior_sweep_status", "prior_sweep_ready"
    if type(report) is PosteriorPredictiveReport:
        return (
            PosteriorPredictiveReport,
            "posterior_predictive_status",
            "posterior_predictive_ready",
        )
    if type(report) is LoocvReport:
        return LoocvReport, "loocv_status", "loocv_ready"
    raise TypeError(
        "inference adequacy components must be exact PriorSweepReport, "
        "PosteriorPredictiveReport, or LoocvReport instances"
    )


def _sha256_text(value: object, field_name: str) -> str:
    if type(value) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _rebuild_matched_null_report(
    report: MatchedNullCompetitionReport,
    *,
    config_hash: str,
    source_hashes: Sequence[str],
) -> MatchedNullCompetitionReport:
    manifest = report.manifest
    return build_matched_null_competition_report(
        null_result=report.null_result,
        matched_complexity_hook=report.matched_complexity_hook,
        alternative_complexity_score=report.alternative_complexity_score,
        null_flexibility_scores=report.null_flexibility_scores,
        artifact_id=manifest.artifact_id,
        artifact_path=manifest.artifact_path,
        config_hash=config_hash,
        input_hashes=source_hashes,
        generating_command=report.generating_command,
        fpr_threshold=report.fpr_threshold,
        candidate_log_bayes_factor=report.candidate_log_bayes_factor,
        headline_requested=report.headline_requested,
        worktree_state=report.worktree_state,
        git_commit=report.git_commit,
        transfer_source=report.transfer_source,
        caveats=tuple(manifest.caveats),
    )


def _validated_matched_null_report(
    report: object,
) -> tuple[frozenset[str], NullCompetitionHook]:
    """Rebuild the exact matched-null report and derive its only valid hook."""

    if type(report) is not MatchedNullCompetitionReport:
        raise TypeError(
            "matched-null adequacy requires an exact MatchedNullCompetitionReport"
        )
    if type(report.manifest) is not ArtifactManifest:
        raise TypeError("matched-null report manifest must be ArtifactManifest")
    if type(report.null_result) is not NullCompetitionResult:
        raise TypeError("matched-null report requires an exact NullCompetitionResult")
    if type(report.null_result.family_results) is not dict:
        raise TypeError("matched-null family_results must be a canonical dict")
    if any(
        type(result) is not FamilyCompetitionResult
        for result in report.null_result.family_results.values()
    ):
        raise TypeError(
            "matched-null family_results require exact FamilyCompetitionResult values"
        )
    if (
        report.matched_complexity_hook is not None
        and type(report.matched_complexity_hook) is not MatchedComplexityHook
    ):
        raise TypeError("matched-null report requires an exact MatchedComplexityHook")
    if type(report.null_flexibility_scores) is not dict:
        raise TypeError("matched-null flexibility scores must be a canonical dict")

    source_hashes = _component_source_hashes(report)
    candidates: set[str] = set()
    for candidate in source_hashes:
        try:
            rebuilt = _rebuild_matched_null_report(
                report,
                config_hash=candidate,
                source_hashes=source_hashes,
            )
        except (TypeError, ValueError):
            continue
        if rebuilt == report:
            candidates.add(candidate)
    if not candidates:
        raise ValueError(
            "MatchedNullCompetitionReport cannot be reproduced from canonical "
            "typed content, hashes, and source lineage"
        )

    matched_complexity_ready = bool(
        report.matched_complexity_hook is not None
        and report.matched_complexity_hook.overall_pass
        and report.matched_complexity_hook.controls_required
    )
    hook = NullCompetitionHook(
        required_families=tuple(report.null_result.family_results),
        fpr_threshold=float(report.fpr_threshold),
        ready_for_inference=report.evidence_claim_prerequisite_met,
        worst_family=report.null_result.worst_family,
        worst_fpr=float(report.null_result.worst_fpr),
        matched_complexity_ready=matched_complexity_ready,
        matched_null_report_hash=report.report_hash,
        matched_null_status=report.matched_null_status,
        blocked_reasons=tuple(report.blocked_reasons),
    )
    return frozenset(candidates), hook


def _canonical_matched_null_hook_payload(
    hook: NullCompetitionHook | None,
    report: MatchedNullCompetitionReport | None = None,
) -> dict[str, object] | None:
    """Validate and serialize the matched-null hook without duck typing.

    ``NullCompetitionHook`` is a compact pre-posterior summary, not the
    matched-null report itself.  Consequently the composite gate must bind
    every decision-bearing field and reject internally contradictory summaries
    rather than trusting only ``ready_for_inference``.
    """

    if hook is not None and type(hook) is not NullCompetitionHook:
        raise TypeError(
            "matched-null adequacy requires an exact NullCompetitionHook instance"
        )
    derived_hook: NullCompetitionHook | None = None
    if report is not None:
        _, derived_hook = _validated_matched_null_report(report)
        if hook is None:
            hook = derived_hook
    if hook is None:
        return None
    if type(hook.ready_for_inference) is not bool:
        raise TypeError("matched-null hook ready_for_inference must be bool")
    if type(hook.matched_complexity_ready) is not bool:
        raise TypeError("matched-null hook matched_complexity_ready must be bool")
    if hook.scope != "pre_posterior":
        raise ValueError("matched-null hook scope must be pre_posterior")

    families = hook.required_families
    if type(families) is not tuple or not families:
        raise ValueError(
            "matched-null hook required_families must be a non-empty tuple"
        )
    if any(
        type(family) is not str or not family or family != family.strip()
        for family in families
    ):
        raise ValueError(
            "matched-null hook required_families must contain canonical non-empty strings"
        )
    if len(families) != len(set(families)):
        raise ValueError("matched-null hook required_families must be unique")

    if type(hook.fpr_threshold) is not float:
        raise TypeError("matched-null hook fpr_threshold must be a canonical float")
    threshold = hook.fpr_threshold
    if not math.isfinite(threshold) or not (0.0 < threshold <= 1.0):
        raise ValueError("matched-null hook fpr_threshold must be finite and in (0, 1]")
    worst_family = hook.worst_family
    worst_fpr = hook.worst_fpr
    if (worst_family is None) != (worst_fpr is None):
        raise ValueError(
            "matched-null hook worst_family and worst_fpr must be present together"
        )
    if worst_family is not None:
        if type(worst_family) is not str or worst_family not in families:
            raise ValueError(
                "matched-null hook worst_family must belong to required_families"
            )
        if type(worst_fpr) is not float:
            raise TypeError("matched-null hook worst_fpr must be a canonical float")
        if not math.isfinite(worst_fpr) or not (0.0 <= worst_fpr <= 1.0):
            raise ValueError("matched-null hook worst_fpr must be finite and in [0, 1]")

    status = hook.matched_null_status
    if type(status) is not str or not status or status != status.strip():
        raise ValueError(
            "matched-null hook status must be a canonical non-empty string"
        )
    blocked_reasons = hook.blocked_reasons
    if type(blocked_reasons) is not tuple:
        raise TypeError("matched-null hook blocked_reasons must be a tuple")
    if any(
        type(reason) is not str or not reason or reason != reason.strip()
        for reason in blocked_reasons
    ):
        raise ValueError(
            "matched-null hook blocked_reasons must be canonical non-empty strings"
        )
    if len(blocked_reasons) != len(set(blocked_reasons)):
        raise ValueError("matched-null hook blocked_reasons must be unique")

    report_hash = hook.matched_null_report_hash
    canonical_report_hash = (
        None
        if report_hash is None
        else _sha256_text(report_hash, "matched-null hook report hash")
    )
    if hook.ready_for_inference:
        if report is None:
            raise ValueError(
                "ready matched-null hook requires an exact MatchedNullCompetitionReport"
            )
        if not hook.matched_complexity_ready:
            raise ValueError(
                "ready matched-null hook requires matched-complexity readiness"
            )
        if canonical_report_hash is None:
            raise ValueError("ready matched-null hook requires a canonical report hash")
        if worst_family is None or worst_fpr is None:
            raise ValueError(
                "ready matched-null hook requires a worst-family FPR result"
            )
        if worst_fpr > threshold:
            raise ValueError(
                "ready matched-null hook worst_fpr cannot exceed fpr_threshold"
            )
        if status != "matched_null_ready":
            raise ValueError(
                "ready matched-null hook status must be matched_null_ready"
            )
        if blocked_reasons:
            raise ValueError("ready matched-null hook cannot retain blocked_reasons")
    elif status == "matched_null_ready":
        raise ValueError(
            "blocked matched-null hook cannot carry matched_null_ready status"
        )
    if derived_hook is not None and hook != derived_hook:
        raise ValueError(
            "matched-null hook does not match the canonical report-derived hook"
        )

    return {
        "required_families": list(families),
        "fpr_threshold": threshold,
        "ready_for_inference": hook.ready_for_inference,
        "worst_family": worst_family,
        "worst_fpr": worst_fpr,
        "scope": hook.scope,
        "matched_complexity_ready": hook.matched_complexity_ready,
        "matched_null_report_hash": canonical_report_hash,
        "matched_null_status": status,
        "blocked_reasons": list(blocked_reasons),
    }


def _component_source_hashes(report: object) -> tuple[str, ...]:
    report_hash = _sha256_text(
        report.report_hash,  # type: ignore[attr-defined]
        f"{type(report).__name__}.report_hash",
    )
    manifest = report.manifest  # type: ignore[attr-defined]
    if type(manifest) is not ArtifactManifest:
        raise TypeError(f"{type(report).__name__}.manifest must be ArtifactManifest")
    hashes = tuple(
        _sha256_text(value, f"{type(report).__name__}.manifest.input_hashes")
        for value in manifest.input_hashes
    )
    if len(hashes) != len(set(hashes)):
        raise ValueError(
            f"{type(report).__name__}.manifest.input_hashes must be unique"
        )
    if hashes.count(report_hash) != 1:
        raise ValueError(
            f"{type(report).__name__}.report_hash must occur exactly once in manifest.input_hashes"
        )
    source_hashes = tuple(value for value in hashes if value != report_hash)
    if not source_hashes:
        raise ValueError(f"{type(report).__name__} requires source input lineage")
    return source_hashes


def _rebuild_component_report(
    report: object,
    *,
    config_hash: str,
    source_hashes: Sequence[str],
) -> object:
    """Recreate one component through its canonical builder.

    Whole-dataclass equality validates the report hash, derived statistics,
    manifest owner/scope/status, gates, and provenance without maintaining a
    second hand-written scientific oracle in the composite gate.
    """

    from htt.infer.loocv import LoocvReport, build_loocv_report
    from htt.infer.posterior_predictive import (
        PosteriorPredictiveReport,
        build_posterior_predictive_report,
    )

    manifest = report.manifest  # type: ignore[attr-defined]
    common = {
        "artifact_id": manifest.artifact_id,
        "artifact_path": manifest.artifact_path,
        "config_hash": config_hash,
        "input_hashes": source_hashes,
        "generating_command": report.generating_command,  # type: ignore[attr-defined]
        "worktree_state": report.worktree_state,  # type: ignore[attr-defined]
        "git_commit": report.git_commit,  # type: ignore[attr-defined]
        "transfer_source": report.transfer_source,  # type: ignore[attr-defined]
        "caveats": tuple(manifest.caveats),
    }
    if type(report) is PriorSweepReport:
        return build_prior_sweep_report(
            model=report.model,
            baseline_log_evidence=report.baseline_log_evidence,
            sweep_log_evidences=report.sweep_log_evidences,
            sensitivity_threshold=report.sensitivity_threshold,
            **common,
        )
    if type(report) is PosteriorPredictiveReport:
        return build_posterior_predictive_report(
            model=report.model,
            observed=report.observed,
            predicted=report.predicted,
            sigma=report.sigma,
            pvalue=report.pvalue,
            min_pvalue=report.min_pvalue,
            max_abs_pull=report.max_abs_pull,
            **common,
        )
    if type(report) is LoocvReport:
        return build_loocv_report(
            model=report.model,
            full_log_evidence=report.full_log_evidence,
            fold_log_evidences=report.fold_log_evidences,
            max_delta_threshold=report.max_delta_threshold,
            min_folds=report.min_folds,
            **common,
        )
    raise TypeError("unrecognized inference adequacy component")


def _validated_config_candidates(report: object) -> frozenset[str]:
    recognized_report_type(report)
    source_hashes = _component_source_hashes(report)
    candidates: set[str] = set()
    for candidate in source_hashes:
        try:
            rebuilt = _rebuild_component_report(
                report,
                config_hash=candidate,
                source_hashes=source_hashes,
            )
        except (TypeError, ValueError):
            continue
        if rebuilt == report:
            candidates.add(candidate)
    if not candidates:
        raise ValueError(
            f"{type(report).__name__} cannot be reproduced from canonical "
            "typed content, hashes, and source lineage"
        )
    return frozenset(candidates)


def _validate_component_lineage(
    *,
    prior_sweep_report: PriorSweepReport | None,
    posterior_predictive_report: object | None,
    loocv_report: object | None,
    matched_null_report: MatchedNullCompetitionReport | None,
    composite_config_hash: str,
    composite_input_hashes: Sequence[str],
    composite_git_commit: str | None,
    composite_worktree_state: str | None,
) -> None:
    reports = tuple(
        report
        for report in (
            prior_sweep_report,
            posterior_predictive_report,
            loocv_report,
        )
        if report is not None
    )
    candidate_sets: list[frozenset[str]] = []
    for report in reports:
        candidate_sets.append(_validated_config_candidates(report))
    if matched_null_report is not None:
        matched_candidates, _ = _validated_matched_null_report(matched_null_report)
        matched_provenance = (
            matched_null_report.git_commit,
            matched_null_report.worktree_state,
        )
        if matched_provenance != (
            composite_git_commit,
            composite_worktree_state,
        ):
            raise ValueError(
                "inference adequacy composite and matched-null code provenance must match"
            )
        matched_common = set(matched_candidates)
        matched_common.intersection_update(
            {_sha256_text(composite_config_hash, "inference adequacy config_hash")}
        )
        matched_common.intersection_update(
            _sha256_text(value, "inference adequacy input_hashes")
            for value in composite_input_hashes
        )
        if not matched_common:
            raise ValueError(
                "matched-null report requires the common recomputed config/input lineage hash"
            )
    if not reports:
        return
    models = {str(report.model) for report in reports}  # type: ignore[attr-defined]
    if len(models) != 1:
        raise ValueError("inference adequacy component model lineage must match")
    provenance = {
        (report.git_commit, report.worktree_state)  # type: ignore[attr-defined]
        for report in reports
    }
    if len(provenance) != 1:
        raise ValueError("inference adequacy component code provenance must match")
    if provenance != {(composite_git_commit, composite_worktree_state)}:
        raise ValueError(
            "inference adequacy composite and component code provenance must match"
        )
    common_candidates = set(candidate_sets[0])
    for candidates in candidate_sets[1:]:
        common_candidates.intersection_update(candidates)
    common_candidates.intersection_update(
        {_sha256_text(composite_config_hash, "inference adequacy config_hash")}
    )
    common_candidates.intersection_update(
        _sha256_text(value, "inference adequacy input_hashes")
        for value in composite_input_hashes
    )
    if not common_candidates:
        raise ValueError(
            "inference adequacy components require a common recomputed config/input lineage hash"
        )


def build_prior_sweep_report(
    *,
    model: object,
    baseline_log_evidence: object,
    sweep_log_evidences: Mapping[str, object],
    sensitivity_threshold: object,
    artifact_id: object,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    artifact_path: object = _DEFAULT_PRIOR_PATH,
    worktree_state: object | None = None,
    git_commit: object | None = None,
    transfer_source: object = "none",
    caveats: Sequence[object] = _DEFAULT_CAVEATS,
) -> PriorSweepReport:
    """Build a prior-sensitivity report.

    The report records whether evidence-like summaries are stable under a
    predeclared prior grid. It does not validate native solver output or allow
    family-identification language.
    """

    model_text = non_empty(model, "model")
    baseline = finite_float(baseline_log_evidence, "baseline_log_evidence")
    sweep = finite_mapping(sweep_log_evidences, "sweep_log_evidences")
    threshold = positive_float(sensitivity_threshold, "sensitivity_threshold")
    meta = metadata(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        config_hash=config_hash,
        input_hashes_value=input_hashes,
        generating_command=generating_command,
        worktree_state=worktree_state,
        git_commit=git_commit,
        transfer_source=transfer_source,
        caveats=caveats,
    )
    deltas = {name: value - baseline for name, value in sweep.items()}
    max_abs_delta = max(abs(delta) for delta in deltas.values())
    blockers: list[str] = []
    if max_abs_delta > threshold:
        blockers.append("prior_sensitivity_exceeds_threshold")
    ready = not blockers
    status = "prior_sweep_ready" if ready else "blocked_prior_sensitivity"
    report_hash = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "surface": "prior_sweep",
            "model": model_text,
            "baseline_log_evidence": baseline,
            "sweep_log_evidences": sweep,
            "sensitivity_threshold": threshold,
            "config_hash": meta["config_hash"],
            "input_hashes": list(meta["input_hashes"]),
        }
    )
    manifest = ArtifactManifest(
        artifact_id=str(meta["artifact_id"]),
        artifact_path=str(meta["artifact_path"]),
        owner=Owner.HTT,
        implementation_scope=ImplementationScope.HTT,
        claim_tier=ClaimTier.CONDITIONAL if ready else ClaimTier.BLOCKED,
        production_status="diagnostic_only" if ready else "blocked_provenance_mismatch",
        created_by=_PRIOR_CREATED_BY,
        git_commit=meta["git_commit"],  # type: ignore[arg-type]
        config_hash=stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "surface": "prior_sweep",
                "model": model_text,
                "threshold": threshold,
                "config_hash": meta["config_hash"],
            }
        ),
        input_hashes=list(dict.fromkeys([*meta["input_hashes"], report_hash])),  # type: ignore[arg-type]
        code_version=str(meta["git_commit"] or meta["worktree_state"]),
        schema_version=SCHEMA_VERSION,
        caveats=list(meta["caveats"]),  # type: ignore[arg-type]
        required_gates=[
            "prior_grid_predeclared",
            "finite_prior_sweep_evidence",
            "prior_sensitivity_within_threshold",
            "manifest_metadata_present",
        ],
        passed_gates=[
            "prior_grid_predeclared",
            "finite_prior_sweep_evidence",
            "manifest_metadata_present",
            *(["prior_sensitivity_within_threshold"] if ready else []),
        ],
        failed_gates=list(blockers),
        statistics_definitions={
            "surface": "prior_sweep",
            "model": model_text,
            "prior_sweep_status": status,
            "sensitivity_threshold": threshold,
            "max_abs_delta_log_evidence": max_abs_delta,
        },
    )
    return PriorSweepReport(
        manifest=manifest,
        model=model_text,
        baseline_log_evidence=baseline,
        sweep_log_evidences=sweep,
        sensitivity_threshold=threshold,
        max_abs_delta_log_evidence=max_abs_delta,
        prior_sweep_status=status,
        blocked_reasons=dedupe(blockers),
        report_hash=report_hash,
        generating_command=str(meta["generating_command"]),
        worktree_state=meta["worktree_state"],  # type: ignore[arg-type]
        git_commit=meta["git_commit"],  # type: ignore[arg-type]
        transfer_source=str(meta["transfer_source"]),
    )


def build_inference_adequacy_report(
    *,
    prior_sweep_report: PriorSweepReport | None,
    posterior_predictive_report: object | None,
    loocv_report: object | None,
    matched_null_hook: NullCompetitionHook | None,
    matched_null_report: MatchedNullCompetitionReport | None = None,
    artifact_id: object,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    decisive_claim_requested: bool = False,
    artifact_path: object = _DEFAULT_ADEQUACY_PATH,
    worktree_state: object | None = None,
    git_commit: object | None = None,
    transfer_source: object = "none",
    caveats: Sequence[object] = _DEFAULT_CAVEATS,
) -> InferenceAdequacyReport:
    """Build the composite PR-065 prior/PPC/LOOCV adequacy report.

    Component reports must include their source config digest in
    ``manifest.input_hashes``.  The same digest must be supplied as this
    composite's config hash and as one of its input hashes, making model,
    content, config, input, and code provenance mismatches fail closed.
    """

    if decisive_claim_requested and not (
        prior_sweep_report is not None
        and posterior_predictive_report is not None
        and loocv_report is not None
        and matched_null_hook is not None
        and matched_null_report is not None
    ):
        raise ValueError(
            "decisive evidence language requires prior-sweep, PPC, LOOCV, "
            "and matched-null adequacy reports"
        )
    meta = metadata(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        config_hash=config_hash,
        input_hashes_value=input_hashes,
        generating_command=generating_command,
        worktree_state=worktree_state,
        git_commit=git_commit,
        transfer_source=transfer_source,
        caveats=caveats,
    )
    matched_null = _canonical_matched_null_hook_payload(
        matched_null_hook,
        matched_null_report,
    )
    _validate_component_lineage(
        prior_sweep_report=prior_sweep_report,
        posterior_predictive_report=posterior_predictive_report,
        loocv_report=loocv_report,
        matched_null_report=matched_null_report,
        composite_config_hash=str(meta["config_hash"]),
        composite_input_hashes=meta["input_hashes"],  # type: ignore[arg-type]
        composite_git_commit=meta["git_commit"],  # type: ignore[arg-type]
        composite_worktree_state=meta["worktree_state"],  # type: ignore[arg-type]
    )
    blockers: list[str] = []
    if not report_ready(prior_sweep_report):
        blockers.append("prior_sweep_failed")
    if not report_ready(posterior_predictive_report):
        blockers.append("posterior_predictive_failed")
    if not report_ready(loocv_report):
        blockers.append("loocv_failed")
    if matched_null is None or not bool(matched_null["ready_for_inference"]):
        blockers.append("matched_null_not_ready")
        if matched_null is not None:
            blockers.extend(
                f"matched_null:{reason}"
                for reason in matched_null["blocked_reasons"]  # type: ignore[union-attr]
            )
    ready = not blockers
    status = "inference_adequacy_ready" if ready else "blocked_inference_adequacy"
    decisive_status = (
        "conditional_pre_solver"
        if ready and decisive_claim_requested
        else "blocked_until_prior_ppc_loocv_matched_null"
    )
    report_hash = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "surface": "inference_adequacy",
            "prior_sweep_ref": report_ref(prior_sweep_report),
            "posterior_predictive_ref": report_ref(posterior_predictive_report),
            "loocv_ref": report_ref(loocv_report),
            "matched_null_hook": matched_null,
            "decisive_claim_requested": bool(decisive_claim_requested),
            "config_hash": meta["config_hash"],
            "input_hashes": list(meta["input_hashes"]),
        }
    )
    manifest = ArtifactManifest(
        artifact_id=str(meta["artifact_id"]),
        artifact_path=str(meta["artifact_path"]),
        owner=Owner.HTT,
        implementation_scope=ImplementationScope.HTT,
        claim_tier=ClaimTier.CONDITIONAL if ready else ClaimTier.BLOCKED,
        production_status="diagnostic_only" if ready else "blocked_provenance_mismatch",
        created_by=_ADEQUACY_CREATED_BY,
        git_commit=meta["git_commit"],  # type: ignore[arg-type]
        config_hash=stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "surface": "inference_adequacy",
                "config_hash": meta["config_hash"],
                "prior_sweep_status": status_of(
                    prior_sweep_report,
                    "prior_sweep_status",
                    "missing_prior_sweep_report",
                ),
                "posterior_predictive_status": status_of(
                    posterior_predictive_report,
                    "posterior_predictive_status",
                    "missing_posterior_predictive_report",
                ),
                "loocv_status": status_of(
                    loocv_report,
                    "loocv_status",
                    "missing_loocv_report",
                ),
                "matched_null_hook": matched_null,
            }
        ),
        input_hashes=list(
            dict.fromkeys(
                [
                    *meta["input_hashes"],  # type: ignore[arg-type]
                    *(
                        ref
                        for ref in (
                            report_ref(prior_sweep_report),
                            report_ref(posterior_predictive_report),
                            report_ref(loocv_report),
                            (
                                None
                                if matched_null is None
                                else matched_null["matched_null_report_hash"]
                            ),
                            report_hash,
                        )
                        if ref is not None
                    ),
                ]
            )
        ),
        code_version=str(meta["git_commit"] or meta["worktree_state"]),
        schema_version=SCHEMA_VERSION,
        caveats=list(meta["caveats"]),  # type: ignore[arg-type]
        required_gates=[
            "matched_null_ready",
            "prior_sweep_ready",
            "posterior_predictive_ready",
            "loocv_ready",
            "manifest_metadata_present",
        ],
        passed_gates=[
            "manifest_metadata_present",
            *(
                ["matched_null_ready"]
                if matched_null is not None
                and bool(matched_null["ready_for_inference"])
                else []
            ),
            *(["prior_sweep_ready"] if report_ready(prior_sweep_report) else []),
            *(
                ["posterior_predictive_ready"]
                if report_ready(posterior_predictive_report)
                else []
            ),
            *(["loocv_ready"] if report_ready(loocv_report) else []),
        ],
        failed_gates=list(blockers),
        statistics_definitions={
            "surface": "inference_adequacy",
            "inference_adequacy_status": status,
            "decisive_evidence_language_status": decisive_status,
            "prior_sweep_status": status_of(
                prior_sweep_report,
                "prior_sweep_status",
                "missing_prior_sweep_report",
            ),
            "posterior_predictive_status": status_of(
                posterior_predictive_report,
                "posterior_predictive_status",
                "missing_posterior_predictive_report",
            ),
            "loocv_status": status_of(
                loocv_report,
                "loocv_status",
                "missing_loocv_report",
            ),
            "matched_null_status": (
                "missing_matched_null_hook"
                if matched_null is None
                else matched_null["matched_null_status"]
            ),
            "matched_null_hook": matched_null,
        },
    )
    return InferenceAdequacyReport(
        manifest=manifest,
        prior_sweep_report=prior_sweep_report,
        posterior_predictive_report=posterior_predictive_report,
        loocv_report=loocv_report,
        matched_null_report=matched_null_report,
        matched_null_hook=matched_null_hook,
        inference_adequacy_status=status,
        decisive_evidence_language_status=decisive_status,
        blocked_reasons=dedupe(blockers),
        report_hash=report_hash,
        decisive_claim_requested=bool(decisive_claim_requested),
        generating_command=str(meta["generating_command"]),
        worktree_state=meta["worktree_state"],  # type: ignore[arg-type]
        git_commit=meta["git_commit"],  # type: ignore[arg-type]
        transfer_source=str(meta["transfer_source"]),
    )


__all__ = [
    "PriorSweepReport",
    "InferenceAdequacyReport",
    "build_inference_adequacy_report",
    "build_prior_sweep_report",
]
