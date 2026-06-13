"""HTT prior-sensitivity and inference-adequacy gates for PR-065."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
)
from htt.infer.null_competition import NullCompetitionHook

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
        non_empty(name, f"{field_name}.key"): finite_float(value, f"{field_name}[{name}]")
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
    worktree_text = None if worktree_state is None else non_empty(worktree_state, "worktree_state")
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
                "abs_delta_log_evidence": abs(float(value - self.baseline_log_evidence)),
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
                "git_commit_or_worktree_state": self.git_commit or self.worktree_state or "unknown",
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
            "matched_null_ready"
            if self.matched_null_hook is not None and self.matched_null_hook.ready_for_inference
            else (
                "missing_matched_null_hook"
                if self.matched_null_hook is None
                else self.matched_null_hook.matched_null_status
            )
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
                "git_commit_or_worktree_state": self.git_commit or self.worktree_state or "unknown",
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
                "prior_sweep_ref": report_ref(self.prior_sweep_report),
                "posterior_predictive_ref": report_ref(self.posterior_predictive_report),
                "loocv_ref": report_ref(self.loocv_report),
                "matched_null_report_hash": (
                    None if self.matched_null_hook is None else self.matched_null_hook.matched_null_report_hash
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
    return str(getattr(report, "report_hash"))


def status_of(report: object | None, field_name: str, missing: str) -> str:
    if report is None:
        return missing
    return str(getattr(report, field_name))


def report_ready(report: object | None) -> bool:
    return bool(report is not None and getattr(report, "ready_for_claims"))


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
    """Build the composite PR-065 prior/PPC/LOOCV adequacy report."""

    if decisive_claim_requested and not (
        prior_sweep_report is not None
        and posterior_predictive_report is not None
        and loocv_report is not None
        and matched_null_hook is not None
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
    blockers: list[str] = []
    if not report_ready(prior_sweep_report):
        blockers.append("prior_sweep_failed")
    if not report_ready(posterior_predictive_report):
        blockers.append("posterior_predictive_failed")
    if not report_ready(loocv_report):
        blockers.append("loocv_failed")
    if matched_null_hook is None or not matched_null_hook.ready_for_inference:
        blockers.append("matched_null_not_ready")
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
            "matched_null_report_hash": (
                None if matched_null_hook is None else matched_null_hook.matched_null_report_hash
            ),
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
            }
        ),
        input_hashes=list(
            dict.fromkeys(
                [
                    *meta["input_hashes"],  # type: ignore[arg-type]
                    *(ref for ref in (
                        report_ref(prior_sweep_report),
                        report_ref(posterior_predictive_report),
                        report_ref(loocv_report),
                        None if matched_null_hook is None else matched_null_hook.matched_null_report_hash,
                        report_hash,
                    ) if ref is not None),
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
            *(["matched_null_ready"] if matched_null_hook is not None and matched_null_hook.ready_for_inference else []),
            *(["prior_sweep_ready"] if report_ready(prior_sweep_report) else []),
            *(["posterior_predictive_ready"] if report_ready(posterior_predictive_report) else []),
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
                if matched_null_hook is None
                else matched_null_hook.matched_null_status
            ),
        },
    )
    return InferenceAdequacyReport(
        manifest=manifest,
        prior_sweep_report=prior_sweep_report,
        posterior_predictive_report=posterior_predictive_report,
        loocv_report=loocv_report,
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
