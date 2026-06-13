"""HTT leave-one-out cross-validation adequacy gate for PR-065."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from common.contracts import ArtifactManifest, ClaimTier, ImplementationScope, Owner
from htt.infer.prior_sweep import (
    SCHEMA_VERSION,
    _DEFAULT_CAVEATS,
    dedupe,
    finite_float,
    finite_mapping,
    json_ready,
    manifest_payload,
    metadata,
    positive_float,
    stable_hash,
)

_CREATED_BY = "htt.infer.loocv.build_loocv_report"
_DEFAULT_ARTIFACT_PATH = "memory://htt/infer/loocv.json"


@dataclass(frozen=True)
class LoocvReport:
    """Manifest-backed LOOCV adequacy report."""

    manifest: ArtifactManifest
    model: str
    full_log_evidence: float
    fold_log_evidences: Mapping[str, float]
    fold_deltas: Mapping[str, float]
    max_delta_threshold: float
    min_folds: int
    max_abs_delta_log_evidence: float
    most_sensitive_fold: Mapping[str, object]
    loocv_status: str
    blocked_reasons: tuple[str, ...]
    report_hash: str
    generating_command: str
    worktree_state: str | None
    git_commit: str | None
    transfer_source: str = "none"

    @property
    def ready_for_claims(self) -> bool:
        return self.loocv_status == "loocv_ready"

    def as_payload(self) -> dict[str, Any]:
        folds = {
            name: {
                "fold_id": name,
                "log_evidence": float(self.fold_log_evidences[name]),
                "delta_log_evidence": float(delta),
                "abs_delta_log_evidence": abs(float(delta)),
            }
            for name, delta in sorted(self.fold_deltas.items())
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
                    "loocv_recorded"
                    if self.ready_for_claims
                    else "loocv_blocked"
                ),
                "generating_command": self.generating_command,
                "git_commit_or_worktree_state": self.git_commit or self.worktree_state or "unknown",
                "git_commit": self.git_commit,
                "worktree_state": self.worktree_state,
                "report_hash": self.report_hash,
                "model": self.model,
                "full_log_evidence": self.full_log_evidence,
                "loocv_status": self.loocv_status,
                "ready_for_claims": self.ready_for_claims,
                "min_folds": self.min_folds,
                "n_folds": len(self.fold_log_evidences),
                "max_delta_threshold": self.max_delta_threshold,
                "max_abs_delta_log_evidence": self.max_abs_delta_log_evidence,
                "most_sensitive_fold": dict(self.most_sensitive_fold),
                "folds": folds,
                "blocked_reasons": list(self.blocked_reasons),
                "caveats": list(self.manifest.caveats),
                "claim_status": {
                    "owner": "HTT",
                    "surface": "loocv",
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_output",
                    "family_status": "blocked_pre_native_atlas",
                },
            }
        )


def _positive_int(value: object, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be a positive integer")
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{field_name} must be a positive integer")
    out = int(value)
    if out <= 0:
        raise ValueError(f"{field_name} must be positive")
    return out


def build_loocv_report(
    *,
    model: object,
    full_log_evidence: object,
    fold_log_evidences: Mapping[str, object],
    max_delta_threshold: object,
    min_folds: object,
    artifact_id: object,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    artifact_path: object = _DEFAULT_ARTIFACT_PATH,
    worktree_state: object | None = None,
    git_commit: object | None = None,
    transfer_source: object = "none",
    caveats: Sequence[object] = _DEFAULT_CAVEATS,
) -> LoocvReport:
    model_text = str(model).strip()
    if not model_text:
        raise ValueError("model must be non-empty")
    full = finite_float(full_log_evidence, "full_log_evidence")
    folds = finite_mapping(fold_log_evidences, "fold_log_evidences")
    threshold = positive_float(max_delta_threshold, "max_delta_threshold")
    min_fold_count = _positive_int(min_folds, "min_folds")
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
    deltas = {name: full - value for name, value in folds.items()}
    max_abs_delta = max(abs(delta) for delta in deltas.values())
    most_name, most_delta = max(
        sorted(deltas.items()),
        key=lambda item: abs(item[1]),
    )
    most_sensitive = {
        "fold_id": most_name,
        "log_evidence": folds[most_name],
        "delta_log_evidence": most_delta,
        "abs_delta_log_evidence": abs(most_delta),
    }
    blockers: list[str] = []
    if len(folds) < min_fold_count:
        blockers.append("loocv_insufficient_folds")
    if max_abs_delta > threshold:
        blockers.append("loocv_delta_exceeds_threshold")
    ready = not blockers
    status = "loocv_ready" if ready else "blocked_loocv_instability"
    report_hash = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "surface": "loocv",
            "model": model_text,
            "full_log_evidence": full,
            "fold_log_evidences": folds,
            "max_delta_threshold": threshold,
            "min_folds": min_fold_count,
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
        created_by=_CREATED_BY,
        git_commit=meta["git_commit"],  # type: ignore[arg-type]
        config_hash=stable_hash(
            {
                "schema_version": SCHEMA_VERSION,
                "surface": "loocv",
                "model": model_text,
                "config_hash": meta["config_hash"],
                "max_delta_threshold": threshold,
                "min_folds": min_fold_count,
            }
        ),
        input_hashes=list(dict.fromkeys([*meta["input_hashes"], report_hash])),  # type: ignore[arg-type]
        code_version=str(meta["git_commit"] or meta["worktree_state"]),
        schema_version=SCHEMA_VERSION,
        caveats=list(meta["caveats"]),  # type: ignore[arg-type]
        required_gates=[
            "finite_loocv_evidence",
            "loocv_minimum_folds",
            "loocv_delta_within_threshold",
            "manifest_metadata_present",
        ],
        passed_gates=[
            "finite_loocv_evidence",
            "manifest_metadata_present",
            *(["loocv_minimum_folds"] if len(folds) >= min_fold_count else []),
            *(["loocv_delta_within_threshold"] if max_abs_delta <= threshold else []),
        ],
        failed_gates=list(blockers),
        statistics_definitions={
            "surface": "loocv",
            "model": model_text,
            "loocv_status": status,
            "max_abs_delta_log_evidence": max_abs_delta,
            "most_sensitive_fold": most_sensitive,
        },
    )
    return LoocvReport(
        manifest=manifest,
        model=model_text,
        full_log_evidence=full,
        fold_log_evidences=folds,
        fold_deltas=deltas,
        max_delta_threshold=threshold,
        min_folds=min_fold_count,
        max_abs_delta_log_evidence=max_abs_delta,
        most_sensitive_fold=most_sensitive,
        loocv_status=status,
        blocked_reasons=dedupe(blockers),
        report_hash=report_hash,
        generating_command=str(meta["generating_command"]),
        worktree_state=meta["worktree_state"],  # type: ignore[arg-type]
        git_commit=meta["git_commit"],  # type: ignore[arg-type]
        transfer_source=str(meta["transfer_source"]),
    )


__all__ = ["LoocvReport", "build_loocv_report"]
