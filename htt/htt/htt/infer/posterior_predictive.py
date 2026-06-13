"""HTT posterior-predictive adequacy gate for PR-065."""
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

_CREATED_BY = "htt.infer.posterior_predictive.build_posterior_predictive_report"
_DEFAULT_ARTIFACT_PATH = "memory://htt/infer/posterior_predictive.json"


@dataclass(frozen=True)
class PosteriorPredictiveReport:
    """Manifest-backed posterior-predictive adequacy report."""

    manifest: ArtifactManifest
    model: str
    observed: Mapping[str, float]
    predicted: Mapping[str, float]
    sigma: Mapping[str, float]
    pulls: Mapping[str, float]
    pvalue: float
    min_pvalue: float
    max_abs_pull: float
    max_abs_pull_observed: float
    posterior_predictive_status: str
    blocked_reasons: tuple[str, ...]
    report_hash: str
    generating_command: str
    worktree_state: str | None
    git_commit: str | None
    transfer_source: str = "none"

    @property
    def ready_for_claims(self) -> bool:
        return self.posterior_predictive_status == "posterior_predictive_ready"

    @property
    def ndof(self) -> int:
        return len(self.observed)

    def as_payload(self) -> dict[str, Any]:
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
                    "posterior_predictive_recorded"
                    if self.ready_for_claims
                    else "posterior_predictive_blocked"
                ),
                "generating_command": self.generating_command,
                "git_commit_or_worktree_state": self.git_commit or self.worktree_state or "unknown",
                "git_commit": self.git_commit,
                "worktree_state": self.worktree_state,
                "report_hash": self.report_hash,
                "model": self.model,
                "posterior_predictive_status": self.posterior_predictive_status,
                "ready_for_claims": self.ready_for_claims,
                "pvalue": self.pvalue,
                "min_pvalue": self.min_pvalue,
                "max_abs_pull": self.max_abs_pull,
                "max_abs_pull_observed": self.max_abs_pull_observed,
                "ndof": self.ndof,
                "observed": dict(self.observed),
                "predicted": dict(self.predicted),
                "sigma": dict(self.sigma),
                "pulls": dict(self.pulls),
                "blocked_reasons": list(self.blocked_reasons),
                "caveats": list(self.manifest.caveats),
                "claim_status": {
                    "owner": "HTT",
                    "surface": "posterior_predictive",
                    "mio_status": "not_mio_output",
                    "native_solver_status": "not_native_solver_output",
                    "family_status": "blocked_pre_native_atlas",
                },
            }
        )


def _aligned_observables(
    observed: Mapping[str, object],
    predicted: Mapping[str, object],
    sigma: Mapping[str, object],
) -> tuple[dict[str, float], dict[str, float], dict[str, float]]:
    obs = finite_mapping(observed, "observed")
    pred = finite_mapping(predicted, "predicted")
    sig = finite_mapping(sigma, "sigma")
    if set(obs) != set(pred) or set(obs) != set(sig):
        raise ValueError("observed, predicted, and sigma keys must match")
    for key, value in sig.items():
        if value <= 0.0:
            raise ValueError(f"sigma[{key}] must be positive")
    return obs, pred, sig


def _unit_interval(value: object, field_name: str) -> float:
    out = finite_float(value, field_name)
    if not (0.0 <= out <= 1.0):
        raise ValueError(f"{field_name} must be in [0, 1]")
    return out


def build_posterior_predictive_report(
    *,
    model: object,
    observed: Mapping[str, object],
    predicted: Mapping[str, object],
    sigma: Mapping[str, object],
    pvalue: object,
    min_pvalue: object,
    max_abs_pull: object,
    artifact_id: object,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    artifact_path: object = _DEFAULT_ARTIFACT_PATH,
    worktree_state: object | None = None,
    git_commit: object | None = None,
    transfer_source: object = "none",
    caveats: Sequence[object] = _DEFAULT_CAVEATS,
) -> PosteriorPredictiveReport:
    model_text = str(model).strip()
    if not model_text:
        raise ValueError("model must be non-empty")
    obs, pred, sig = _aligned_observables(observed, predicted, sigma)
    pvalue_float = _unit_interval(pvalue, "pvalue")
    min_p = positive_float(min_pvalue, "min_pvalue")
    if min_p > 1.0:
        raise ValueError("min_pvalue must be <= 1")
    max_pull_allowed = positive_float(max_abs_pull, "max_abs_pull")
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
    pulls = {key: (pred[key] - obs[key]) / sig[key] for key in sorted(obs)}
    max_pull_observed = max(abs(value) for value in pulls.values())
    blockers: list[str] = []
    if pvalue_float < min_p:
        blockers.append("posterior_predictive_pvalue_below_threshold")
    if max_pull_observed > max_pull_allowed:
        blockers.append("posterior_predictive_pull_exceeds_threshold")
    ready = not blockers
    status = "posterior_predictive_ready" if ready else "blocked_posterior_predictive"
    report_hash = stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "surface": "posterior_predictive",
            "model": model_text,
            "observed": obs,
            "predicted": pred,
            "sigma": sig,
            "pvalue": pvalue_float,
            "min_pvalue": min_p,
            "max_abs_pull": max_pull_allowed,
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
                "surface": "posterior_predictive",
                "model": model_text,
                "config_hash": meta["config_hash"],
                "min_pvalue": min_p,
                "max_abs_pull": max_pull_allowed,
            }
        ),
        input_hashes=list(dict.fromkeys([*meta["input_hashes"], report_hash])),  # type: ignore[arg-type]
        code_version=str(meta["git_commit"] or meta["worktree_state"]),
        schema_version=SCHEMA_VERSION,
        caveats=list(meta["caveats"]),  # type: ignore[arg-type]
        required_gates=[
            "finite_posterior_predictive_observables",
            "posterior_predictive_pvalue_above_threshold",
            "posterior_predictive_pulls_within_threshold",
            "manifest_metadata_present",
        ],
        passed_gates=[
            "finite_posterior_predictive_observables",
            "manifest_metadata_present",
            *(["posterior_predictive_pvalue_above_threshold"] if pvalue_float >= min_p else []),
            *(["posterior_predictive_pulls_within_threshold"] if max_pull_observed <= max_pull_allowed else []),
        ],
        failed_gates=list(blockers),
        statistics_definitions={
            "surface": "posterior_predictive",
            "model": model_text,
            "posterior_predictive_status": status,
            "pvalue": pvalue_float,
            "max_abs_pull_observed": max_pull_observed,
        },
    )
    return PosteriorPredictiveReport(
        manifest=manifest,
        model=model_text,
        observed=obs,
        predicted=pred,
        sigma=sig,
        pulls=pulls,
        pvalue=pvalue_float,
        min_pvalue=min_p,
        max_abs_pull=max_pull_allowed,
        max_abs_pull_observed=max_pull_observed,
        posterior_predictive_status=status,
        blocked_reasons=dedupe(blockers),
        report_hash=report_hash,
        generating_command=str(meta["generating_command"]),
        worktree_state=meta["worktree_state"],  # type: ignore[arg-type]
        git_commit=meta["git_commit"],  # type: ignore[arg-type]
        transfer_source=str(meta["transfer_source"]),
    )


__all__ = ["PosteriorPredictiveReport", "build_posterior_predictive_report"]
