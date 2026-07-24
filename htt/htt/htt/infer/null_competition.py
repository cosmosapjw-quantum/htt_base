"""
htt/infer/null_competition.py — Structured-Null Competition Engine
=====================================================================
Milestone M2.2 deliverable. Formally competes the shared-cause model
against each structured-null family at the DOF level.

The competition logic:
  1. For each null family, generate N synthetic datasets with β_true=0.
  2. Run the shared-cause test on each synthetic dataset.
  3. Record the false-positive rate (fraction where shared-cause is preferred).
  4. If ANY null family has FPR > threshold, the shared-cause detection
     is not robust against that systematic.

This is the adversarial complement to shared_cause.py: the null families
try to mimic the signal, and the competition engine measures how often
they succeed.
"""

from __future__ import annotations

import hashlib
import json
import math
import numpy as np
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from common.contracts import (
    AllowedUse,
    ArtifactManifest,
    ArtifactMode,
    ClaimTier,
    ImplementationScope,
    Owner,
)
from htt.infer.matched_complexity import MatchedComplexityHook
from htt.nulls import NULL_REGISTRY
from htt.nulls.common_interface import NullFamily
from htt.infer.dipole_vector_likelihood import DipoleVectorLikelihood

__all__ = [
    "NullCompetitionResult",
    "FamilyCompetitionResult",
    "NullCompetitionHook",
    "MatchedNullCompetitionReport",
    "GFMatchedNullForecastReport",
    "build_matched_null_competition_report",
    "build_gf_matched_null_forecast_report",
    "NullCompetitionEngine",
    "build_null_competition_hook",
    "run_null_competition",
]


SCHEMA_VERSION = "htt.infer.matched_null_competition.v1"
_CREATED_BY = "htt.infer.null_competition.build_matched_null_competition_report"
_DEFAULT_ARTIFACT_PATH = "memory://htt/infer/matched_null_competition.json"
_DEFAULT_CAVEATS = (
    "diagnostic_only_pre_solver_null_competition",
    "matched_complexity_required_before_evidence_language",
    "structured_null_fpr_is_gate_metadata_not_model_weight",
    "decisive_evidence_language_blocked_until_pr065_prior_ppc_loocv",
    "no_native_solver_or_family_claim",
)
_DEFAULT_GF_FORECAST_CAVEATS = (
    "forecast_only_matched_null_design_sensitivity",
    "not_observed_data_evidence",
    "does_not_authorize_global_tilt_wording",
    "does_not_authorize_native_solver_validation",
    "does_not_authorize_family_identification",
)


def _json_ready(value: object) -> Any:
    if isinstance(value, np.ndarray):
        return [_json_ready(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_ready(value.item())
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("payload floats must be finite")
        return value
    return value


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    payload = _json_ready(asdict(manifest))
    if not isinstance(payload, dict):
        raise TypeError("manifest payload must be a mapping")
    return payload


def _non_empty(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _input_hashes(
    values: tuple[object, ...] | list[object], field_name: str
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise ValueError(f"{field_name} must be a non-empty sequence")
    return tuple(_non_empty(value, field_name) for value in values)


def _fpr_threshold(value: object) -> float:
    threshold = float(value)
    if not math.isfinite(threshold) or threshold <= 0.0 or threshold > 1.0:
        raise ValueError("fpr_threshold must be finite and in (0, 1]")
    return threshold


def _finite_optional(value: object | None, field_name: str) -> float | None:
    if value is None:
        return None
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite when provided")
    return out


def _complexity_score(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be an integer complexity score")
    try:
        numeric = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer complexity score") from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise ValueError(f"{field_name} must be an integer complexity score")
    score = int(numeric)
    if score < 0:
        raise ValueError(f"{field_name} must be non-negative")
    return score


def _dedupe(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def _primary_provenance_state(
    *,
    git_commit: str | None,
    worktree_state: str | None,
) -> str:
    if worktree_state and (git_commit is None or worktree_state != git_commit):
        return worktree_state
    return git_commit or worktree_state or "unknown"


def _wilson_interval(k: int, n: int, *, z: float) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("Wilson interval requires n > 0")
    if k < 0 or k > n:
        raise ValueError("Wilson interval requires 0 <= k <= n")
    if not math.isfinite(float(z)) or float(z) <= 0.0:
        raise ValueError("Wilson z must be positive finite")
    z_value = float(z)
    p_hat = k / n
    z2 = z_value * z_value
    denom = 1.0 + z2 / n
    center = (p_hat + z2 / (2.0 * n)) / denom
    half_width = (
        z_value / denom * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z2 / (4.0 * n * n)))
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


@dataclass(frozen=True)
class FamilyCompetitionResult:
    """Result of competing one null family against shared-cause."""

    family_name: str
    n_realizations: int
    n_false_positives: int  # times shared-cause preferred on null data
    fpr: float  # false-positive rate
    mean_lnB_null: float  # mean ln B(shared-cause vs null) on null data
    std_lnB_null: float
    robust: bool  # True if fpr < threshold
    status: str = "diagnostic_only"

    def __post_init__(self) -> None:
        if not self.family_name:
            raise ValueError("family_name must be non-empty")
        if self.status != "diagnostic_only":
            raise ValueError("family competition status must be diagnostic_only")
        if type(self.robust) is not bool:
            raise TypeError("robust must be bool")
        if int(self.n_realizations) <= 0:
            raise ValueError("n_realizations must be positive")
        if int(self.n_false_positives) < 0:
            raise ValueError("n_false_positives must be non-negative")
        if int(self.n_false_positives) > int(self.n_realizations):
            raise ValueError("n_false_positives cannot exceed n_realizations")
        for field_name in ("fpr", "mean_lnB_null", "std_lnB_null"):
            value = float(getattr(self, field_name))
            if not math.isfinite(value):
                raise ValueError(f"{field_name} must be finite")
        if not (0.0 <= float(self.fpr) <= 1.0):
            raise ValueError("fpr must be in [0, 1]")
        implied = int(self.n_false_positives) / int(self.n_realizations)
        if not math.isclose(float(self.fpr), implied, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("fpr must match n_false_positives / n_realizations")


@dataclass(frozen=True)
class NullCompetitionResult:
    """Full competition result across all null families."""

    families_tested: int
    families_robust: int
    families_vulnerable: int
    worst_family: str
    worst_fpr: float
    overall_robust: bool  # True if ALL families are robust
    family_results: Dict[str, FamilyCompetitionResult] = field(default_factory=dict)
    status: str = "diagnostic_only"

    def __post_init__(self) -> None:
        if self.status != "diagnostic_only":
            raise ValueError("null competition status must be diagnostic_only")
        if type(self.overall_robust) is not bool:
            raise TypeError("overall_robust must be bool")
        if int(self.families_tested) <= 0:
            raise ValueError("families_tested must be positive")
        if int(self.families_robust) < 0 or int(self.families_vulnerable) < 0:
            raise ValueError("family counts must be non-negative")
        if int(self.families_robust) + int(self.families_vulnerable) != int(
            self.families_tested
        ):
            raise ValueError(
                "family robust/vulnerable counts must sum to families_tested"
            )
        if not self.worst_family:
            raise ValueError("worst_family must be non-empty")
        if not math.isfinite(float(self.worst_fpr)) or not (
            0.0 <= float(self.worst_fpr) <= 1.0
        ):
            raise ValueError("worst_fpr must be finite and in [0, 1]")
        if not self.family_results:
            raise ValueError("family_results must be non-empty")
        if len(self.family_results) != int(self.families_tested):
            raise ValueError("family_results length must match families_tested")
        for family_name, family_result in self.family_results.items():
            if not isinstance(family_result, FamilyCompetitionResult):
                raise TypeError("family_results values must be FamilyCompetitionResult")
            if family_name != family_result.family_name:
                raise ValueError("family_results keys must match family_name")
        robust_count = sum(
            1 for result in self.family_results.values() if result.robust
        )
        if robust_count != int(self.families_robust):
            raise ValueError("families_robust must match family_results")
        if int(self.families_tested) - robust_count != int(self.families_vulnerable):
            raise ValueError("families_vulnerable must match family_results")
        if self.worst_family not in self.family_results:
            raise ValueError("worst_family must be present in family_results")
        worst_result = self.family_results[self.worst_family]
        if not math.isclose(
            float(self.worst_fpr),
            float(worst_result.fpr),
            rel_tol=0.0,
            abs_tol=1.0e-12,
        ):
            raise ValueError("worst_fpr must match worst_family result")
        if bool(self.overall_robust) != (int(self.families_vulnerable) == 0):
            raise ValueError("overall_robust must match family vulnerability counts")


@dataclass(frozen=True)
class NullCompetitionHook:
    """Pre-posterior readiness summary for structured-null competition."""

    required_families: tuple[str, ...]
    fpr_threshold: float
    ready_for_inference: bool
    worst_family: str | None
    worst_fpr: float | None
    scope: str = "pre_posterior"
    matched_complexity_ready: bool = False
    matched_null_report_hash: str | None = None
    matched_null_status: str = "pending"
    blocked_reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        threshold = _fpr_threshold(self.fpr_threshold)
        object.__setattr__(self, "fpr_threshold", threshold)
        object.__setattr__(self, "required_families", tuple(self.required_families))
        if not self.required_families:
            object.__setattr__(self, "ready_for_inference", False)
            object.__setattr__(
                self,
                "blocked_reasons",
                _dedupe((*self.blocked_reasons, "null_family_set_empty")),
            )
        if self.worst_fpr is not None:
            worst_fpr = float(self.worst_fpr)
            if not math.isfinite(worst_fpr) or not (0.0 <= worst_fpr <= 1.0):
                raise ValueError("worst_fpr must be finite and in [0, 1]")
            object.__setattr__(self, "worst_fpr", worst_fpr)
        if self.ready_for_inference and not self.matched_complexity_ready:
            object.__setattr__(self, "ready_for_inference", False)
            object.__setattr__(
                self,
                "blocked_reasons",
                _dedupe((*self.blocked_reasons, "matched_complexity_report_missing")),
            )
            object.__setattr__(
                self, "matched_null_status", "blocked_missing_matched_complexity"
            )
        if self.ready_for_inference and not self.matched_null_report_hash:
            object.__setattr__(self, "ready_for_inference", False)
            object.__setattr__(
                self,
                "blocked_reasons",
                _dedupe((*self.blocked_reasons, "matched_null_report_hash_missing")),
            )
            object.__setattr__(
                self, "matched_null_status", "blocked_missing_report_hash"
            )
        if self.ready_for_inference:
            object.__setattr__(self, "matched_null_status", "matched_null_ready")
        elif self.matched_null_status == "matched_null_ready":
            object.__setattr__(
                self, "matched_null_status", "blocked_matched_null_prerequisites"
            )
            object.__setattr__(
                self,
                "blocked_reasons",
                _dedupe((*self.blocked_reasons, "matched_null_not_ready")),
            )


@dataclass(frozen=True)
class MatchedNullCompetitionReport:
    """Manifest-backed PR-064 matched-complexity null competition report."""

    manifest: ArtifactManifest
    null_result: NullCompetitionResult
    matched_complexity_hook: MatchedComplexityHook | None
    alternative_complexity_score: int
    null_flexibility_scores: Mapping[str, int]
    report_hash: str
    matched_null_status: str
    blocked_reasons: tuple[str, ...]
    candidate_log_bayes_factor: float | None
    headline_requested: bool
    headline_bayes_factor_allowed: bool
    fpr_threshold: float
    generating_command: str
    worktree_state: str | None
    git_commit: str | None
    transfer_source: str = "none"

    def as_payload(self) -> dict[str, Any]:
        family_payloads: dict[str, dict[str, object]] = {}
        for family_name, result in sorted(self.null_result.family_results.items()):
            score = self.null_flexibility_scores.get(family_name)
            family_payloads[family_name] = {
                "family_name": family_name,
                "n_realizations": int(result.n_realizations),
                "n_false_positives": int(result.n_false_positives),
                "fpr": float(result.fpr),
                "fpr_threshold": self.fpr_threshold,
                "mean_lnB_null": float(result.mean_lnB_null),
                "std_lnB_null": float(result.std_lnB_null),
                "robust": bool(result.robust),
                "status": result.status,
                "null_flexibility": {
                    "complexity_score": None if score is None else int(score),
                    "matched_to_alternative": (
                        False
                        if score is None
                        else int(score) == self.alternative_complexity_score
                    ),
                },
                "matched_complexity_gap": (
                    None
                    if score is None
                    else int(score - self.alternative_complexity_score)
                ),
            }
        return _json_ready(
            {
                "owner": Owner.HTT.value,
                "implementation_scope": ImplementationScope.HTT.value,
                "claim_tier": self.manifest.claim_tier.value,
                "production_status": self.manifest.production_status,
                "schema_version": SCHEMA_VERSION,
                "manifest": _manifest_payload(self.manifest),
                "transfer_source": self.transfer_source,
                "config_hash": self.manifest.config_hash,
                "input_hashes": list(self.manifest.input_hashes),
                "sky_support_status": "not_directional",
                "null_mock_status": (
                    "matched_complexity_null_competition_recorded"
                    if self.evidence_claim_prerequisite_met
                    else "matched_complexity_null_competition_blocked"
                ),
                "generating_command": self.generating_command,
                "git_commit_or_worktree_state": _primary_provenance_state(
                    git_commit=self.git_commit,
                    worktree_state=self.worktree_state,
                ),
                "git_commit": self.git_commit,
                "worktree_state": self.worktree_state,
                "report_hash": self.report_hash,
                "matched_null_status": self.matched_null_status,
                "evidence_claim_prerequisite_met": self.evidence_claim_prerequisite_met,
                "headline_bayes_factor_allowed": self.headline_bayes_factor_allowed,
                "matched_null_headline_gate_passed": bool(
                    self.evidence_claim_prerequisite_met and self.headline_requested
                ),
                "candidate_log_bayes_factor": self.candidate_log_bayes_factor,
                "decisive_evidence_status": "blocked_until_pr065_prior_ppc_loocv",
                "alternative_flexibility": {
                    "complexity_score": int(self.alternative_complexity_score),
                    "source": "matched_complexity_hook",
                    "matched_complexity_ready": bool(
                        self.matched_complexity_hook
                        and self.matched_complexity_hook.overall_pass
                    ),
                },
                "matched_complexity": {
                    "present": self.matched_complexity_hook is not None,
                    "overall_pass": bool(
                        self.matched_complexity_hook
                        and self.matched_complexity_hook.overall_pass
                    ),
                    "controls_required": (
                        []
                        if self.matched_complexity_hook is None
                        else list(self.matched_complexity_hook.controls_required)
                    ),
                    "violations": (
                        ["matched_complexity_report_missing"]
                        if self.matched_complexity_hook is None
                        else list(self.matched_complexity_hook.violations)
                    ),
                    "scope": (
                        None
                        if self.matched_complexity_hook is None
                        else self.matched_complexity_hook.scope
                    ),
                },
                "null_competition": {
                    "families_tested": int(self.null_result.families_tested),
                    "families_robust": int(self.null_result.families_robust),
                    "families_vulnerable": int(self.null_result.families_vulnerable),
                    "worst_family": self.null_result.worst_family,
                    "worst_fpr": float(self.null_result.worst_fpr),
                    "overall_robust": bool(self.null_result.overall_robust),
                    "status": self.null_result.status,
                },
                "family_results": family_payloads,
                "blocked_reasons": list(self.blocked_reasons),
                "caveats": list(self.manifest.caveats),
                "claim_status": {
                    "owner": "HTT",
                    "surface": "matched_complexity_null_competition",
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_output",
                    "family_status": "blocked_pre_native_atlas",
                    "posterior_status": "not_authorized_until_pr065",
                },
            }
        )

    @property
    def evidence_claim_prerequisite_met(self) -> bool:
        return self.matched_null_status == "matched_null_ready"


@dataclass(frozen=True)
class GFMatchedNullForecastReport:
    """Forecast-only wrapper for future G_F matched-null discrimination tests."""

    manifest: ArtifactManifest
    matched_null_report: MatchedNullCompetitionReport
    threshold_config_hash: str
    threshold_selection_rationale: str
    confidence_z: float
    report_hash: str
    matched_null_status: str
    blocked_reasons: tuple[str, ...]
    generating_command: str
    worktree_state: str | None
    git_commit: str | None
    forecast_source_kind: str = "deterministic_current_code_fixture"
    forecast_source_description: str = (
        "Deterministic current-code synthetic demonstration fixture; not "
        "production mocks and not observed-data evidence."
    )
    threshold_pre_registered: bool = True
    retuning_after_failure: bool = False
    forecast_only: bool = True
    observed_data_evidence: bool = False
    authorization_scope: str = "design_sensitivity_only"
    local_global_separation_status: str = "blocked_existing_null_bank_insufficient"
    global_tilt_wording_allowed: bool = False

    @property
    def claim_tier(self) -> str:
        return self.manifest.claim_tier.value

    @property
    def production_status(self) -> str:
        return str(self.manifest.production_status)

    @property
    def false_positive_rate_statement(self) -> dict[str, object]:
        result = self.matched_null_report.null_result.family_results[
            self.matched_null_report.null_result.worst_family
        ]
        lower, upper = _wilson_interval(
            int(result.n_false_positives),
            int(result.n_realizations),
            z=self.confidence_z,
        )
        return {
            "kind": "count_with_wilson_upper_bound",
            "family_name": result.family_name,
            "false_positive_count": int(result.n_false_positives),
            "false_positive_denominator": int(result.n_realizations),
            "point_estimate": float(result.fpr),
            "wilson_interval": [lower, upper],
            "wilson_upper_bound": upper,
            "confidence_z": self.confidence_z,
            "source_kind": self.forecast_source_kind,
            "source_description": self.forecast_source_description,
            "wording": (
                f"{int(result.n_false_positives)}/{int(result.n_realizations)} "
                "forecast false-positive crossings; Wilson upper bound "
                f"{upper:.6g} at z={self.confidence_z:g}."
            ),
        }

    def as_payload(self) -> dict[str, Any]:
        manifest_payload = _manifest_payload(self.manifest)
        return _json_ready(
            {
                "owner": Owner.HTT.value,
                "implementation_scope": ImplementationScope.HTT.value,
                "claim_tier": self.claim_tier,
                "production_status": self.production_status,
                "artifact_mode": ArtifactMode.FORECAST_ONLY.value,
                "allowed_use": AllowedUse.EXTERNAL_AUDIT.value,
                "schema_version": "htt.infer.gf_matched_null_forecast.v1",
                "manifest": manifest_payload,
                "artifact_id": self.manifest.artifact_id,
                "artifact_path": self.manifest.artifact_path,
                "transfer_source": "none",
                "sky_support_status": "not_directional",
                "null_mock_status": self.matched_null_status,
                "config_hash": self.manifest.config_hash,
                "input_hashes": list(self.manifest.input_hashes),
                "generating_command": self.generating_command,
                "git_commit_or_worktree_state": _primary_provenance_state(
                    git_commit=self.git_commit,
                    worktree_state=self.worktree_state,
                ),
                "git_commit": self.git_commit,
                "worktree_state": self.worktree_state,
                "report_hash": self.report_hash,
                "forecast_source_kind": self.forecast_source_kind,
                "forecast_source_description": self.forecast_source_description,
                "forecast_only": self.forecast_only,
                "observed_data_evidence": self.observed_data_evidence,
                "authorization_scope": self.authorization_scope,
                "matched_null_status": self.matched_null_status,
                "matched_null_report_hash": self.matched_null_report.report_hash,
                "matched_null_report": self.matched_null_report.as_payload(),
                "local_global_separation_status": self.local_global_separation_status,
                "global_tilt_wording_allowed": self.global_tilt_wording_allowed,
                "decisive_evidence_status": (
                    "blocked_forecast_only_not_observed_evidence"
                ),
                "threshold_pre_registered": self.threshold_pre_registered,
                "threshold_config_hash": self.threshold_config_hash,
                "threshold_selection_rationale": self.threshold_selection_rationale,
                "retuning_after_failure": self.retuning_after_failure,
                "false_positive_rate_statement": self.false_positive_rate_statement,
                "blocked_reasons": list(self.blocked_reasons),
                "claim_status": {
                    "owner": "HTT",
                    "surface": "G_F_matched_null_forecast",
                    "mio_status": "not_mio_output",
                    "observed_data_status": "not_observed_evidence",
                    "native_solver_status": "not_native_solver_output",
                    "family_status": "blocked_pre_native_atlas",
                    "posterior_status": "not_authorized",
                    "global_tilt_wording_status": "blocked_forecast_only",
                },
                "caveats": list(self.manifest.caveats),
            }
        )


def _family_payload(result: FamilyCompetitionResult) -> dict[str, object]:
    return {
        "family_name": result.family_name,
        "n_realizations": int(result.n_realizations),
        "n_false_positives": int(result.n_false_positives),
        "fpr": float(result.fpr),
        "mean_lnB_null": float(result.mean_lnB_null),
        "std_lnB_null": float(result.std_lnB_null),
        "robust": bool(result.robust),
        "status": result.status,
    }


def _matched_hook_payload(hook: MatchedComplexityHook | None) -> dict[str, object]:
    if hook is None:
        return {
            "present": False,
            "overall_pass": False,
            "controls_required": [],
            "violations": ["matched_complexity_report_missing"],
            "scope": None,
        }
    return {
        "present": True,
        "overall_pass": bool(hook.overall_pass),
        "controls_required": list(hook.controls_required),
        "violations": list(hook.violations),
        "scope": hook.scope,
    }


def _report_hash_payload(
    *,
    null_result: NullCompetitionResult,
    matched_complexity_hook: MatchedComplexityHook | None,
    alternative_complexity_score: int,
    null_flexibility_scores: Mapping[str, int],
    fpr_threshold: float,
    candidate_log_bayes_factor: float | None,
    config_hash: str,
    input_hashes: tuple[str, ...],
) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "null_result": {
            "families_tested": int(null_result.families_tested),
            "families_robust": int(null_result.families_robust),
            "families_vulnerable": int(null_result.families_vulnerable),
            "worst_family": null_result.worst_family,
            "worst_fpr": float(null_result.worst_fpr),
            "overall_robust": bool(null_result.overall_robust),
            "family_results": {
                family_name: _family_payload(result)
                for family_name, result in sorted(null_result.family_results.items())
            },
            "status": null_result.status,
        },
        "matched_complexity_hook": _matched_hook_payload(matched_complexity_hook),
        "alternative_complexity_score": int(alternative_complexity_score),
        "null_flexibility_scores": {
            str(name): int(score)
            for name, score in sorted(null_flexibility_scores.items())
        },
        "fpr_threshold": fpr_threshold,
        "candidate_log_bayes_factor": candidate_log_bayes_factor,
        "config_hash": config_hash,
        "input_hashes": list(input_hashes),
    }


def _matched_null_blockers(
    *,
    null_result: NullCompetitionResult,
    matched_complexity_hook: MatchedComplexityHook | None,
    alternative_complexity_score: int,
    null_flexibility_scores: Mapping[str, int],
) -> tuple[str, ...]:
    blockers: list[str] = []
    if matched_complexity_hook is None:
        blockers.append("matched_complexity_report_missing")
    elif not matched_complexity_hook.overall_pass:
        blockers.append("matched_complexity_failed")
        blockers.extend(
            f"matched_complexity_violation:{violation}"
            for violation in matched_complexity_hook.violations
        )
    elif not matched_complexity_hook.controls_required:
        blockers.append("matched_complexity_controls_missing")
    if not null_result.overall_robust:
        blockers.append("structured_nulls_not_robust")
    missing_scores = sorted(
        set(null_result.family_results) - set(null_flexibility_scores)
    )
    if missing_scores:
        blockers.append("null_flexibility_scores_missing:" + ",".join(missing_scores))
    for family_name, score in sorted(null_flexibility_scores.items()):
        if family_name not in null_result.family_results:
            blockers.append(f"null_flexibility_unknown_family:{family_name}")
        if int(score) != int(alternative_complexity_score):
            blockers.append(f"matched_complexity_gap:{family_name}")
    return _dedupe(blockers)


def build_matched_null_competition_report(
    *,
    null_result: NullCompetitionResult,
    matched_complexity_hook: MatchedComplexityHook | None,
    alternative_complexity_score: int,
    null_flexibility_scores: Mapping[str, int],
    artifact_id: object,
    config_hash: object,
    input_hashes: tuple[object, ...] | list[object],
    generating_command: object,
    fpr_threshold: object = 0.10,
    candidate_log_bayes_factor: object | None = None,
    headline_requested: bool = False,
    artifact_path: object = _DEFAULT_ARTIFACT_PATH,
    worktree_state: object | None = None,
    git_commit: object | None = None,
    transfer_source: object = "none",
    caveats: tuple[object, ...] | list[object] = _DEFAULT_CAVEATS,
) -> MatchedNullCompetitionReport:
    """Build a manifest-backed PR-064 matched-null competition report.

    The report is a gate artifact. It records null FPR and flexibility
    comparisons, but it does not authorize decisive evidence wording; PR-065
    still owns prior-sweep, PPC, and LOOCV gates.
    """

    if type(null_result) is not NullCompetitionResult:
        raise TypeError("null_result must be an exact NullCompetitionResult")
    if (
        matched_complexity_hook is not None
        and type(matched_complexity_hook) is not MatchedComplexityHook
    ):
        raise TypeError(
            "matched_complexity_hook must be an exact MatchedComplexityHook"
        )
    threshold = _fpr_threshold(fpr_threshold)
    for family_name, result in null_result.family_results.items():
        if type(result) is not FamilyCompetitionResult:
            raise TypeError(
                "null_result family_results require exact FamilyCompetitionResult values"
            )
        if type(result.robust) is not bool:
            raise TypeError(f"family robust flag must be bool: {family_name}")
        if result.robust != (float(result.fpr) < threshold):
            raise ValueError(
                "family robust flag must equal the strict fpr < fpr_threshold rule"
            )
    artifact_id_text = _non_empty(artifact_id, "artifact_id")
    artifact_path_text = _non_empty(artifact_path, "artifact_path")
    config_hash_text = _non_empty(config_hash, "config_hash")
    input_hash_tuple = _input_hashes(input_hashes, "input_hashes")
    command_text = _non_empty(generating_command, "generating_command")
    worktree_text = (
        None if worktree_state is None else _non_empty(worktree_state, "worktree_state")
    )
    git_commit_text = (
        None if git_commit is None else _non_empty(git_commit, "git_commit")
    )
    if worktree_text is None and git_commit_text is None:
        raise ValueError("git_commit or worktree_state is required")
    transfer_source_text = _non_empty(transfer_source, "transfer_source")
    if transfer_source_text != "none":
        raise ValueError(
            "PR-064 matched null report only supports transfer_source='none'"
        )
    caveat_tuple = tuple(_non_empty(item, "caveat") for item in caveats)
    if not caveat_tuple:
        raise ValueError("caveats must be non-empty")
    candidate_ln_b = _finite_optional(
        candidate_log_bayes_factor,
        "candidate_log_bayes_factor",
    )
    if (
        headline_requested
        and candidate_ln_b is not None
        and matched_complexity_hook is None
    ):
        raise ValueError(
            "headline evidence language requires a matched-complexity report"
        )

    alt_score = _complexity_score(
        alternative_complexity_score,
        "alternative_complexity_score",
    )
    null_scores = {
        str(name): _complexity_score(score, f"null_flexibility_scores[{name}]")
        for name, score in null_flexibility_scores.items()
    }
    blockers = _matched_null_blockers(
        null_result=null_result,
        matched_complexity_hook=matched_complexity_hook,
        alternative_complexity_score=alt_score,
        null_flexibility_scores=null_scores,
    )
    ready = not blockers
    status = (
        "matched_null_ready"
        if ready
        else (
            "blocked_missing_matched_complexity"
            if "matched_complexity_report_missing" in blockers
            else "blocked_matched_null_prerequisites"
        )
    )
    report_hash = _stable_hash(
        _report_hash_payload(
            null_result=null_result,
            matched_complexity_hook=matched_complexity_hook,
            alternative_complexity_score=alt_score,
            null_flexibility_scores=null_scores,
            fpr_threshold=threshold,
            candidate_log_bayes_factor=candidate_ln_b,
            config_hash=config_hash_text,
            input_hashes=input_hash_tuple,
        )
    )
    claim_tier = ClaimTier.CONDITIONAL if ready else ClaimTier.BLOCKED
    production_status = "diagnostic_only" if ready else "blocked_provenance_mismatch"
    passed_gates = [
        "manifest_metadata_present",
        "headline_evidence_blocked_until_pr065",
    ]
    if ready:
        passed_gates.extend(["matched_complexity_ready", "structured_nulls_robust"])
    failed_gates = list(blockers)
    manifest = ArtifactManifest(
        artifact_id=artifact_id_text,
        artifact_path=artifact_path_text,
        owner=Owner.HTT,
        implementation_scope=ImplementationScope.HTT,
        claim_tier=claim_tier,
        production_status=production_status,  # type: ignore[arg-type]
        created_by=_CREATED_BY,
        git_commit=git_commit_text,
        config_hash=_stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "artifact_id": artifact_id_text,
                "config_hash": config_hash_text,
                "fpr_threshold": threshold,
                "families": sorted(null_result.family_results),
                "alternative_complexity_score": alt_score,
                "null_flexibility_scores": null_scores,
            }
        ),
        input_hashes=list(dict.fromkeys([*input_hash_tuple, report_hash])),
        code_version=_primary_provenance_state(
            git_commit=git_commit_text,
            worktree_state=worktree_text,
        ),
        schema_version=SCHEMA_VERSION,
        caveats=list(caveat_tuple),
        required_gates=[
            "matched_complexity_ready",
            "structured_nulls_robust",
            "alternative_null_flexibility_matched",
            "headline_evidence_blocked_until_pr065",
            "manifest_metadata_present",
        ],
        passed_gates=passed_gates,
        failed_gates=failed_gates,
        statistics_definitions={
            "surface": "MatchedNullCompetitionReport",
            "matched_null_status": status,
            "fpr_threshold": threshold,
            "candidate_log_bayes_factor_status": (
                "diagnostic_input_only"
                if candidate_ln_b is not None
                else "not_supplied"
            ),
            "decisive_evidence_status": "blocked_until_pr065_prior_ppc_loocv",
            "null_family_count": int(null_result.families_tested),
            "worst_family": null_result.worst_family,
            "worst_fpr": float(null_result.worst_fpr),
        },
    )
    return MatchedNullCompetitionReport(
        manifest=manifest,
        null_result=null_result,
        matched_complexity_hook=matched_complexity_hook,
        alternative_complexity_score=alt_score,
        null_flexibility_scores=null_scores,
        report_hash=report_hash,
        matched_null_status=status,
        blocked_reasons=blockers,
        candidate_log_bayes_factor=candidate_ln_b,
        headline_requested=bool(headline_requested),
        headline_bayes_factor_allowed=False,
        fpr_threshold=threshold,
        generating_command=command_text,
        worktree_state=worktree_text,
        git_commit=git_commit_text,
        transfer_source=transfer_source_text,
    )


def build_gf_matched_null_forecast_report(
    *,
    null_result: NullCompetitionResult,
    matched_complexity_hook: MatchedComplexityHook | None,
    alternative_complexity_score: int,
    null_flexibility_scores: Mapping[str, int],
    artifact_id: object,
    config_hash: object,
    input_hashes: tuple[object, ...] | list[object],
    generating_command: object,
    threshold_config_hash: object,
    threshold_selection_rationale: object,
    fpr_threshold: object = 0.10,
    artifact_path: object = "docs/generated/gf_matched_null_forecast_report.json",
    worktree_state: object | None = None,
    git_commit: object | None = None,
    confidence_z: object = 1.0,
    caveats: tuple[object, ...] | list[object] = _DEFAULT_GF_FORECAST_CAVEATS,
) -> GFMatchedNullForecastReport:
    """Build a forecast-only G_F matched-null report.

    This wrapper is deliberately weaker than
    :func:`build_matched_null_competition_report`: even a passing forecast
    remains design-sensitivity metadata and does not authorize observed-data
    local/global wording.
    """

    threshold_hash = _non_empty(
        threshold_config_hash,
        "threshold_config_hash",
    )
    threshold_rationale = _non_empty(
        threshold_selection_rationale,
        "threshold_selection_rationale",
    )
    z_value = float(confidence_z)
    if not math.isfinite(z_value) or z_value <= 0.0:
        raise ValueError("confidence_z must be positive finite")
    caveat_tuple = tuple(_non_empty(item, "caveat") for item in caveats)
    for required_caveat in _DEFAULT_GF_FORECAST_CAVEATS:
        if required_caveat not in caveat_tuple:
            caveat_tuple = (*caveat_tuple, required_caveat)

    base_report = build_matched_null_competition_report(
        null_result=null_result,
        matched_complexity_hook=matched_complexity_hook,
        alternative_complexity_score=alternative_complexity_score,
        null_flexibility_scores=null_flexibility_scores,
        artifact_id=f"{_non_empty(artifact_id, 'artifact_id')}.matched_null_gate",
        config_hash=config_hash,
        input_hashes=input_hashes,
        generating_command=generating_command,
        fpr_threshold=fpr_threshold,
        artifact_path="memory://htt/infer/gf_matched_null_forecast_gate.json",
        worktree_state=worktree_state,
        git_commit=git_commit,
        caveats=_DEFAULT_CAVEATS,
    )
    passed = base_report.evidence_claim_prerequisite_met
    status = (
        "forecast_matched_null_passed" if passed else "forecast_matched_null_blocked"
    )
    blocked = list(base_report.blocked_reasons)
    if not passed:
        blocked.append("forecast_matched_null_fpr_threshold_not_met")
    # This forecast never authorizes observed-data separation language.
    blocked.append("forecast_only_not_observed_evidence")
    blocked.append("global_tilt_wording_blocked")
    blocked_reasons = _dedupe(blocked)
    artifact_id_text = _non_empty(artifact_id, "artifact_id")
    artifact_path_text = _non_empty(artifact_path, "artifact_path")
    config_hash_text = _non_empty(config_hash, "config_hash")
    input_hash_tuple = _input_hashes(input_hashes, "input_hashes")
    command_text = _non_empty(generating_command, "generating_command")
    worktree_text = (
        None if worktree_state is None else _non_empty(worktree_state, "worktree_state")
    )
    git_commit_text = (
        None if git_commit is None else _non_empty(git_commit, "git_commit")
    )
    if worktree_text is None and git_commit_text is None:
        raise ValueError("git_commit or worktree_state is required")
    report_hash = _stable_hash(
        {
            "schema_version": "htt.infer.gf_matched_null_forecast.v1",
            "matched_null_report_hash": base_report.report_hash,
            "threshold_config_hash": threshold_hash,
            "threshold_selection_rationale": threshold_rationale,
            "confidence_z": z_value,
            "status": status,
            "blocked_reasons": blocked_reasons,
        }
    )
    claim_tier = ClaimTier.DIAGNOSTIC_ONLY if passed else ClaimTier.BLOCKED
    production_status = "diagnostic_only" if passed else "blocked_provenance_mismatch"
    required_gates = [
        "threshold_pre_registered",
        "matched_complexity_ready",
        "structured_nulls_robust",
        "forecast_only_not_observed_evidence",
        "global_tilt_wording_blocked",
    ]
    passed_gates = [
        "threshold_pre_registered",
        "forecast_only_not_observed_evidence",
        "global_tilt_wording_blocked",
    ]
    if passed:
        passed_gates.extend(["matched_complexity_ready", "structured_nulls_robust"])
    manifest = ArtifactManifest(
        artifact_id=artifact_id_text,
        artifact_path=artifact_path_text,
        owner=Owner.HTT,
        implementation_scope=ImplementationScope.HTT,
        claim_tier=claim_tier,
        production_status=production_status,  # type: ignore[arg-type]
        created_by="htt.infer.null_competition.build_gf_matched_null_forecast_report",
        git_commit=git_commit_text,
        config_hash=report_hash,
        input_hashes=list(dict.fromkeys([*input_hash_tuple, report_hash])),
        code_version=_primary_provenance_state(
            git_commit=git_commit_text,
            worktree_state=worktree_text,
        ),
        schema_version="htt.infer.gf_matched_null_forecast.v1",
        caveats=list(caveat_tuple),
        required_gates=required_gates,
        passed_gates=passed_gates,
        failed_gates=[] if passed else list(blocked_reasons),
        statistics_definitions={
            "G_F": "forecast-only matched-null discrimination input label",
            "matched_null_status": status,
            "false_positive_rate_statement": (
                "count plus Wilson upper bound; never rendered as zero-rate shorthand"
            ),
        },
        artifact_mode=ArtifactMode.FORECAST_ONLY,
        allowed_use=AllowedUse.EXTERNAL_AUDIT,
        caption_policy=[
            "must_state_forecast_only",
            "must_state_not_observed_evidence",
            "must_state_no_global_tilt_wording",
            "must_state_no_native_low_ell_solver_output",
            "must_state_no_family_identification",
        ],
        numeric_payload_path=artifact_path_text,
        promotion_blockers=[
            "observed_matched_null_stack_absent",
            "native_morphology_atlas_absent",
            "prior_ppc_loocv_not_bound",
            "forecast_only_not_observed_evidence",
        ],
    )
    return GFMatchedNullForecastReport(
        manifest=manifest,
        matched_null_report=base_report,
        threshold_config_hash=threshold_hash,
        threshold_selection_rationale=threshold_rationale,
        confidence_z=z_value,
        report_hash=report_hash,
        matched_null_status=status,
        blocked_reasons=blocked_reasons,
        generating_command=command_text,
        worktree_state=worktree_text,
        git_commit=git_commit_text,
    )


class NullCompetitionEngine:
    """Runs the full structured-null competition.

    For each null family in the registry, generates synthetic datasets
    and tests whether the shared-cause model produces false positives.
    """

    def __init__(
        self,
        n_realizations: int = 50,
        fpr_threshold: float = 0.10,
        obs_base: Optional[dict] = None,
    ):
        """
        Parameters
        ----------
        n_realizations : int
            Number of synthetic datasets per null family.
        fpr_threshold : float
            Maximum acceptable false-positive rate (default 10%).
        obs_base : dict, optional
            Base observational parameters for null generation.
        """
        self.n_realizations = n_realizations
        self.fpr_threshold = fpr_threshold
        self.excluded_channels = ("c",)
        self.cf4_channel_status = "QUARANTINED_OPEN_FINDINGS"

        if obs_base is not None:
            self.obs_base = obs_base
        else:
            # Load from canonical obs_defaults.json
            import json
            from pathlib import Path

            obs_path = (
                Path(__file__).resolve().parent.parent.parent.parent
                / "workspace"
                / "data"
                / "obs_defaults.json"
            )
            if obs_path.exists():
                with open(obs_path) as f:
                    self.obs_base = json.load(f)
            else:
                # Minimal fallback for testing
                self.obs_base = {
                    "dipole_observations": {
                        "catwise_bohme_2025": {
                            "eps1": 1.5e-2,
                            "sigma_stat": 3e-3,
                            "sigma_sys": 1e-3,
                        },
                        "radio_secrest_2021": {
                            "eps1": 1.3e-2,
                            "sigma_stat": 4e-3,
                            "sigma_sys": 2e-3,
                        },
                        "rho_CW_radio": 0.0,
                    },
                    "planck2018": {"eps1": 1.2336e-3},
                }

    def compete_family(self, family_name: str) -> FamilyCompetitionResult:
        """Compete one null family against the shared-cause model."""
        if family_name not in NULL_REGISTRY:
            raise KeyError(f"Unknown null family: {family_name}")

        FamilyClass = NULL_REGISTRY[family_name]
        family = FamilyClass()

        lnB_values = []
        false_positives = 0

        for i in range(self.n_realizations):
            # Generate null data (β_true = 0 + systematic)
            null_data = family.generate(seed=i, obs_base=self.obs_base)

            # Convert NullDataset → obs_data format for shared-cause test
            obs_data = {
                "dipole_observations": {
                    "catwise_bohme_2025": {
                        "eps1": null_data.e1_CW,
                        "sigma_stat": null_data.e1_CW_s,
                        "sigma_sys": 0.0,
                    },
                    "radio_secrest_2021": {
                        "eps1": null_data.e1_rad,
                        "sigma_stat": null_data.e1_rad_s,
                        "sigma_sys": 0.0,
                    },
                    "rho_CW_radio": null_data.rho_CW_radio,
                },
            }

            # Active null diagnostic uses only CatWISE+Radio amplitudes and
            # directions. It is not the historical three-survey shared-cause
            # result and must not be promoted as observed-data evidence.
            likelihood = DipoleVectorLikelihood(obs_data=obs_data, control="C1")
            active_amplitudes = np.asarray(
                [null_data.e1_CW, null_data.e1_rad], dtype=float
            )
            active_sigmas = np.asarray(
                [null_data.e1_CW_s, null_data.e1_rad_s], dtype=float
            )
            weights = 1.0 / np.square(active_sigmas)
            amplitude = float(np.sum(weights * active_amplitudes) / np.sum(weights))
            lnB = likelihood.directional_log_likelihood(
                likelihood.CMB_L,
                likelihood.CMB_B,
                amplitude,
            ) - likelihood.scalar_log_likelihood(0.0)

            lnB_values.append(lnB)
            if lnB > 5.0:
                false_positives += 1

        lnB_arr = np.array(lnB_values)
        fpr = false_positives / self.n_realizations

        return FamilyCompetitionResult(
            family_name=family_name,
            n_realizations=self.n_realizations,
            n_false_positives=false_positives,
            fpr=fpr,
            mean_lnB_null=float(lnB_arr.mean()),
            std_lnB_null=float(lnB_arr.std()),
            robust=fpr < self.fpr_threshold,
        )

    def run_all(self) -> NullCompetitionResult:
        """Run competition across all null families."""
        results = {}
        for name in NULL_REGISTRY:
            results[name] = self.compete_family(name)

        n_robust = sum(1 for r in results.values() if r.robust)
        n_vuln = len(results) - n_robust
        worst = max(results.values(), key=lambda r: r.fpr)

        return NullCompetitionResult(
            families_tested=len(results),
            families_robust=n_robust,
            families_vulnerable=n_vuln,
            worst_family=worst.family_name,
            worst_fpr=worst.fpr,
            overall_robust=n_vuln == 0,
            family_results=results,
        )


def run_null_competition(
    n_realizations: int = 50, fpr_threshold: float = 0.10
) -> NullCompetitionResult:
    """Convenience function to run full null competition."""
    engine = NullCompetitionEngine(
        n_realizations=n_realizations,
        fpr_threshold=fpr_threshold,
    )
    return engine.run_all()


def build_null_competition_hook(
    result: NullCompetitionResult | None = None,
    *,
    required_families: List[str] | None = None,
    fpr_threshold: float = 0.10,
    matched_complexity_hook: MatchedComplexityHook | None = None,
    matched_null_report: MatchedNullCompetitionReport | None = None,
    matched_null_report_hash: str | None = None,
) -> NullCompetitionHook:
    if matched_null_report is not None:
        if type(matched_null_report) is not MatchedNullCompetitionReport:
            raise TypeError(
                "matched_null_report must be an exact MatchedNullCompetitionReport"
            )
        result = matched_null_report.null_result
        matched_complexity_hook = matched_null_report.matched_complexity_hook
        matched_null_report_hash = matched_null_report.report_hash
        required_families = list(result.family_results)
        fpr_threshold = matched_null_report.fpr_threshold
    families = tuple(
        required_families
        or (
            list(result.family_results)
            if result is not None and result.family_results
            else list(NULL_REGISTRY)
        )
    )
    matched_ready = bool(
        matched_complexity_hook is not None
        and matched_complexity_hook.overall_pass
        and matched_complexity_hook.controls_required
    )
    report_hash = (
        matched_null_report_hash
        if matched_null_report_hash is not None
        else (
            matched_null_report.report_hash if matched_null_report is not None else None
        )
    )
    if matched_null_report is not None:
        ready = matched_null_report.evidence_claim_prerequisite_met
        blocked = list(matched_null_report.blocked_reasons)
    else:
        ready = bool(result and result.overall_robust and matched_ready and report_hash)
        blocked = []
        if result is None:
            blocked.append("null_competition_result_missing")
        elif not result.overall_robust:
            blocked.append("structured_nulls_not_robust")
        if matched_complexity_hook is None:
            blocked.append("matched_complexity_report_missing")
        elif not matched_complexity_hook.overall_pass:
            blocked.append("matched_complexity_failed")
            blocked.extend(
                f"matched_complexity_violation:{violation}"
                for violation in matched_complexity_hook.violations
            )
        elif not matched_complexity_hook.controls_required:
            blocked.append("matched_complexity_controls_missing")
        if result is not None and matched_ready and not report_hash:
            blocked.append("matched_null_report_hash_missing")
    return NullCompetitionHook(
        required_families=families,
        fpr_threshold=float(fpr_threshold),
        ready_for_inference=ready,
        worst_family=None if result is None else result.worst_family,
        worst_fpr=None if result is None else float(result.worst_fpr),
        matched_complexity_ready=matched_ready,
        matched_null_report_hash=report_hash,
        matched_null_status=(
            matched_null_report.matched_null_status
            if matched_null_report is not None
            else (
                "matched_null_ready" if ready else "blocked_matched_null_prerequisites"
            )
        ),
        blocked_reasons=_dedupe(blocked),
    )
