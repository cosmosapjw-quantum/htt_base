"""mio.decomposition.evidence_anatomy — HJ-04 channel decomposition."""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from common.contracts import ArtifactManifest, ClaimTier, ImplementationScope, Owner
from mio.diagnostics.predictive_residuals import (
    PredictiveResidualAtlas,
    predictive_residual_atlas_payload,
)
from mio.interface.manifest import MioPrerequisites, assess_mio_readiness
from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.tsc_overlay import TscAdequacyOverlay


DEFAULT_DOMAIN_CAVEAT = (
    "Evidence anatomy mirrors HTT-produced evidence deltas read-only and "
    "must not be reinterpreted as MIO adjudication output."
)
SAFE_DEFAULT_MODEL_LABEL = "htt_evidence_trace"
NARRATIVE_SCHEMA_VERSION = "mio.decomposition.evidence_anatomy_narrative.v1"
_NARRATIVE_CREATED_BY = (
    "mio.decomposition.evidence_anatomy.build_evidence_anatomy_narrative_report"
)
_EXPECTED_TRACE_STATUSES = {
    "prior_sweep_status": "prior_sweep_ready",
    "posterior_predictive_status": "posterior_predictive_ready",
    "loocv_status": "loocv_ready",
    "matched_null_status": "matched_null_ready",
}
_FORBIDDEN_TRACE_KEYS = {
    "combined_score",
    "mio_htt_score",
    "combined_mio_htt_score",
    "master_score",
    "posterior_odds",
    "mio_evidence",
    "mio_posterior",
    "mio_bayes_factor",
    "mio_lnb",
    "mio_ln_b",
}


@dataclass(frozen=True)
class EvidenceAnatomyContribution:
    """One channel's contribution to the total ``Δln B``."""

    name: str
    delta_lnB: float
    share_of_total: float
    sign_matches_total: bool


@dataclass(frozen=True)
class EvidenceAnatomyReport:
    """Channel-by-channel evidence decomposition summary."""

    model_label: str
    contributions: tuple[EvidenceAnatomyContribution, ...]
    total_delta_lnB: float
    reconstructed_delta_lnB: float
    residual_delta_lnB: float
    relative_residual: float
    consistency_tolerance: float
    consistent_with_total: bool


def _non_empty(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _optional_non_empty(value: object | None, field_name: str) -> str | None:
    if value is None:
        return None
    return _non_empty(value, field_name)


def _finite_float(value: object, field_name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite")
    return out


def _non_empty_tuple(values: Sequence[object], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise ValueError(f"{field_name} must be a non-empty sequence")
    return tuple(_non_empty(value, field_name) for value in values)


def _canonical_key(value: object) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _scan_forbidden_trace_keys(value: object, path: str = "trace") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            canonical = _canonical_key(key)
            if canonical in _FORBIDDEN_TRACE_KEYS:
                raise ValueError(f"{path}.{canonical} would merge MIO and HTT")
            if canonical.startswith("mio_") and any(
                token in canonical
                for token in (
                    "evidence",
                    "posterior",
                    "score",
                    "truth",
                    "bayes_factor",
                    "ln_b",
                    "lnb",
                )
            ):
                raise ValueError(f"{path}.{canonical} would merge MIO and HTT")
            _scan_forbidden_trace_keys(item, f"{path}.{canonical}")
    elif isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            _scan_forbidden_trace_keys(item, f"{path}[{index}]")


def _json_ready(value: object) -> Any:
    if isinstance(value, (Owner, ImplementationScope, ClaimTier)):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("payload floats must be finite")
        return value
    if isinstance(value, (str, int, bool)) or value is None:
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


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


@dataclass(frozen=True)
class HttEvidenceTraceTerm:
    """One read-only HTT evidence contribution mirrored into MIO narrative."""

    channel: str
    delta_lnB: float
    source_ref: str
    source_owner: str = "HTT"

    def __post_init__(self) -> None:
        channel = _non_empty(self.channel, "channel")
        source_ref = _non_empty(self.source_ref, "source_ref")
        source_owner = _non_empty(self.source_owner, "source_owner")
        if source_owner != Owner.HTT.value:
            raise ValueError(
                "MIO diagnostic terms cannot be HTT evidence-trace inputs; "
                "source_owner must be HTT"
            )
        object.__setattr__(self, "channel", channel)
        object.__setattr__(self, "source_ref", source_ref)
        object.__setattr__(self, "source_owner", source_owner)
        object.__setattr__(
            self,
            "delta_lnB",
            _finite_float(self.delta_lnB, "delta_lnB"),
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "channel": self.channel,
            "delta_lnB": self.delta_lnB,
            "source_ref": self.source_ref,
            "source_owner": self.source_owner,
        }


@dataclass(frozen=True)
class HttEvidenceTrace:
    """Immutable HTT-owned evidence trace used as MIO read-only input."""

    trace_id: str
    model_label: str
    total_delta_lnB: float
    evidence_ref: str
    terms: tuple[HttEvidenceTraceTerm, ...]
    input_hashes: tuple[str, ...]
    config_hash: str
    prior_sweep_status: str
    posterior_predictive_status: str
    loocv_status: str
    matched_null_status: str
    owner: str = "HTT"
    implementation_scope: str = "htt"

    def __post_init__(self) -> None:
        owner = _non_empty(self.owner, "owner")
        scope = _non_empty(self.implementation_scope, "implementation_scope")
        if owner != Owner.HTT.value:
            raise ValueError("HttEvidenceTrace owner must be HTT")
        if scope != ImplementationScope.HTT.value:
            raise ValueError("HttEvidenceTrace implementation_scope must be htt")
        terms = tuple(self.terms)
        if not terms:
            raise ValueError("terms must contain at least one HTT evidence term")
        if any(not isinstance(term, HttEvidenceTraceTerm) for term in terms):
            raise TypeError("terms must contain HttEvidenceTraceTerm entries")
        channels = [term.channel for term in terms]
        if len(set(channels)) != len(channels):
            raise ValueError("terms must have unique channels")
        for field_name in _EXPECTED_TRACE_STATUSES:
            object.__setattr__(
                self,
                field_name,
                _non_empty(getattr(self, field_name), field_name),
            )
        object.__setattr__(self, "owner", owner)
        object.__setattr__(self, "implementation_scope", scope)
        object.__setattr__(self, "trace_id", _non_empty(self.trace_id, "trace_id"))
        object.__setattr__(
            self,
            "model_label",
            _non_empty(self.model_label, "model_label"),
        )
        object.__setattr__(
            self,
            "total_delta_lnB",
            _finite_float(self.total_delta_lnB, "total_delta_lnB"),
        )
        object.__setattr__(
            self,
            "evidence_ref",
            _non_empty(self.evidence_ref, "evidence_ref"),
        )
        object.__setattr__(self, "terms", terms)
        object.__setattr__(
            self,
            "input_hashes",
            _non_empty_tuple(self.input_hashes, "input_hashes"),
        )
        object.__setattr__(
            self,
            "config_hash",
            _non_empty(self.config_hash, "config_hash"),
        )

    @property
    def channel_contributions(self) -> dict[str, float]:
        return {
            term.channel: term.delta_lnB
            for term in sorted(self.terms, key=lambda item: item.channel)
        }

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        reasons: list[str] = []
        for field_name, expected in _EXPECTED_TRACE_STATUSES.items():
            if getattr(self, field_name) != expected:
                reasons.append(field_name.replace("_status", "_not_ready"))
        return tuple(reasons)

    @property
    def ready_for_diagnostic_narrative(self) -> bool:
        return not self.blocked_reasons

    def as_payload(self) -> dict[str, object]:
        return {
            "trace_id": self.trace_id,
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "model_label": self.model_label,
            "total_delta_lnB": self.total_delta_lnB,
            "evidence_ref": self.evidence_ref,
            "terms": [term.as_payload() for term in self.terms],
            "channel_contributions": self.channel_contributions,
            "input_hashes": list(self.input_hashes),
            "config_hash": self.config_hash,
            "prior_sweep_status": self.prior_sweep_status,
            "posterior_predictive_status": self.posterior_predictive_status,
            "loocv_status": self.loocv_status,
            "matched_null_status": self.matched_null_status,
            "ready_for_diagnostic_narrative": self.ready_for_diagnostic_narrative,
            "blocked_reasons": list(self.blocked_reasons),
        }


@dataclass(frozen=True)
class EvidenceAnatomyNarrativeReport:
    """MIO diagnostic narrative over a copied HTT evidence trace."""

    manifest: ArtifactManifest
    evidence_trace: HttEvidenceTrace
    anatomy: EvidenceAnatomyReport
    residual_context: Mapping[str, object] | None
    blocked_reasons: tuple[str, ...]
    report_hash: str
    generating_command: str
    worktree_state: str | None
    git_commit: str | None
    caveats: tuple[str, ...]

    @property
    def ready_for_diagnostic_narrative(self) -> bool:
        return not self.blocked_reasons

    def as_payload(self) -> dict[str, Any]:
        residual_payload = (
            dict(self.residual_context)
            if self.residual_context is not None
            else {"mio_role": "residual_context_not_supplied"}
        )
        return _json_ready(
            {
                "owner": Owner.MIO.value,
                "implementation_scope": ImplementationScope.MIO.value,
                "claim_tier": self.manifest.claim_tier.value,
                "production_status": self.manifest.production_status,
                "schema_version": NARRATIVE_SCHEMA_VERSION,
                "manifest": _manifest_payload(self.manifest),
                "transfer_source": "none",
                "config_hash": self.manifest.config_hash,
                "input_hashes": list(self.manifest.input_hashes),
                "sky_support_status": "not_directional",
                "null_mock_status": self.manifest.statistics_definitions[
                    "null_mock_status"
                ],
                "generating_command": self.generating_command,
                "git_commit_or_worktree_state": (
                    self.git_commit or self.worktree_state or "unknown"
                ),
                "git_commit": self.git_commit,
                "worktree_state": self.worktree_state,
                "report_hash": self.report_hash,
                "trace_source_owner": Owner.HTT.value,
                "mio_role": "diagnostic_narrative_only",
                "not_htt_evidence": True,
                "htt_evidence_modification_status": "read_only_copy",
                "single_score_status": "forbidden_no_owner_merge",
                "ready_for_diagnostic_narrative": self.ready_for_diagnostic_narrative,
                "blocked_reasons": list(self.blocked_reasons),
                "anatomy": {
                    "model_label": self.anatomy.model_label,
                    "contributions": [
                        asdict(item) for item in self.anatomy.contributions
                    ],
                    "total_delta_lnB": self.anatomy.total_delta_lnB,
                    "reconstructed_delta_lnB": self.anatomy.reconstructed_delta_lnB,
                    "residual_delta_lnB": self.anatomy.residual_delta_lnB,
                    "relative_residual": self.anatomy.relative_residual,
                    "consistent_with_total": self.anatomy.consistent_with_total,
                },
                "htt_evidence_trace": self.evidence_trace.as_payload(),
                "residual_context": residual_payload,
                "caveats": list(self.caveats),
                "claim_status": {
                    "owner": "MIO",
                    "surface": "evidence_anatomy_narrative",
                    "htt_status": "read_only_trace_copy",
                    "mio_status": "diagnostic_only_not_posterior",
                    "native_solver_status": "not_native_solver_output",
                    "family_status": "blocked_pre_native_atlas",
                },
            }
        )


def summarize_evidence_anatomy(
    channel_contributions: Mapping[str, float],
    *,
    model_label: str = SAFE_DEFAULT_MODEL_LABEL,
    total_delta_lnB: Optional[float] = None,
    consistency_tolerance: float = 0.10,
    residual_floor: float = 1e-3,
) -> EvidenceAnatomyReport:
    """Summarize a channel-by-channel ``Δln B`` decomposition."""
    if not channel_contributions:
        raise ValueError("channel_contributions must contain at least one channel")
    if consistency_tolerance < 0.0:
        raise ValueError("consistency_tolerance must be >= 0")
    if residual_floor <= 0.0:
        raise ValueError("residual_floor must be > 0")

    finite_contributions = {
        _non_empty(name, "channel_contributions.key"): _finite_float(
            value,
            f"channel_contributions[{name}]",
        )
        for name, value in channel_contributions.items()
    }
    reconstructed = float(sum(finite_contributions.values()))
    total = reconstructed if total_delta_lnB is None else float(total_delta_lnB)
    if not math.isfinite(total):
        raise ValueError("total_delta_lnB must be finite")
    residual = float(total - reconstructed)
    denom = max(abs(total), residual_floor)
    relative = abs(residual) / denom

    contribs = []
    for name in sorted(finite_contributions):
        value = finite_contributions[name]
        share = value / total if abs(total) >= residual_floor else 0.0
        sign_matches = math.copysign(1.0, value or 0.0) == math.copysign(1.0, total or 0.0)
        contribs.append(
            EvidenceAnatomyContribution(
                name=name,
                delta_lnB=value,
                share_of_total=float(share),
                sign_matches_total=bool(sign_matches),
            )
        )

    return EvidenceAnatomyReport(
        model_label=model_label,
        contributions=tuple(contribs),
        total_delta_lnB=total,
        reconstructed_delta_lnB=reconstructed,
        residual_delta_lnB=residual,
        relative_residual=float(relative),
        consistency_tolerance=float(consistency_tolerance),
        consistent_with_total=bool(relative <= consistency_tolerance),
    )


def build_htt_evidence_trace_from_payload(
    payload: Mapping[str, object],
) -> HttEvidenceTrace:
    """Copy an HTT evidence trace mapping into an immutable no-merge contract."""

    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")
    _scan_forbidden_trace_keys(payload)
    owner = str(payload.get("owner", Owner.HTT.value))
    if owner != Owner.HTT.value:
        raise ValueError("HTT evidence trace payload must be owned by HTT")
    scope = str(payload.get("implementation_scope", ImplementationScope.HTT.value))
    if scope != ImplementationScope.HTT.value:
        raise ValueError("HTT evidence trace payload implementation_scope must be htt")
    evidence_ref = _non_empty(
        payload.get("evidence_ref", payload.get("artifact_id", "htt.evidence.trace")),
        "evidence_ref",
    )
    term_payloads = payload.get("terms")
    terms: list[HttEvidenceTraceTerm] = []
    if isinstance(term_payloads, Sequence) and not isinstance(term_payloads, (str, bytes)):
        for index, item in enumerate(term_payloads):
            if not isinstance(item, Mapping):
                raise TypeError(f"terms[{index}] must be a mapping")
            terms.append(
                HttEvidenceTraceTerm(
                    channel=_non_empty(item.get("channel"), f"terms[{index}].channel"),
                    delta_lnB=_finite_float(
                        item.get("delta_lnB"),
                        f"terms[{index}].delta_lnB",
                    ),
                    source_ref=_non_empty(
                        item.get("source_ref", f"{evidence_ref}:term:{index}"),
                        f"terms[{index}].source_ref",
                    ),
                    source_owner=str(item.get("source_owner", Owner.HTT.value)),
                )
            )
    else:
        contributions = payload.get("channel_contributions")
        if not isinstance(contributions, Mapping) or not contributions:
            raise ValueError("payload requires terms or channel_contributions")
        for channel, value in sorted(contributions.items(), key=lambda item: str(item[0])):
            channel_text = _non_empty(channel, "channel_contributions.key")
            terms.append(
                HttEvidenceTraceTerm(
                    channel=channel_text,
                    delta_lnB=_finite_float(
                        value,
                        f"channel_contributions[{channel_text}]",
                    ),
                    source_ref=f"{evidence_ref}:{channel_text}",
                )
            )
    return HttEvidenceTrace(
        trace_id=_non_empty(payload.get("trace_id", evidence_ref), "trace_id"),
        model_label=_non_empty(
            payload.get("model_label", SAFE_DEFAULT_MODEL_LABEL),
            "model_label",
        ),
        total_delta_lnB=_finite_float(
            payload.get("total_delta_lnB"),
            "total_delta_lnB",
        ),
        evidence_ref=evidence_ref,
        terms=tuple(terms),
        input_hashes=_non_empty_tuple(
            tuple(payload.get("input_hashes", ())),
            "input_hashes",
        ),
        config_hash=_non_empty(payload.get("config_hash"), "config_hash"),
        prior_sweep_status=_non_empty(
            payload.get("prior_sweep_status"),
            "prior_sweep_status",
        ),
        posterior_predictive_status=_non_empty(
            payload.get("posterior_predictive_status"),
            "posterior_predictive_status",
        ),
        loocv_status=_non_empty(payload.get("loocv_status"), "loocv_status"),
        matched_null_status=_non_empty(
            payload.get("matched_null_status"),
            "matched_null_status",
        ),
        owner=owner,
        implementation_scope=scope,
    )


def build_evidence_anatomy_narrative_report(
    *,
    evidence_trace: HttEvidenceTrace,
    artifact_id: object,
    artifact_path: object,
    config_hash: object,
    input_hashes: Sequence[object],
    generating_command: object,
    residual_atlas: PredictiveResidualAtlas | None = None,
    worktree_state: object | None = None,
    git_commit: object | None = None,
    requested_single_score: bool = False,
    consistency_tolerance: float = 0.10,
    residual_floor: float = 1e-3,
    caveats: Sequence[object] = (),
) -> EvidenceAnatomyNarrativeReport:
    """Build a MIO narrative report over a read-only HTT evidence trace."""

    if requested_single_score:
        raise ValueError("PR-103 forbids a single combined MIO+HTT score")
    if not isinstance(evidence_trace, HttEvidenceTrace):
        raise TypeError("evidence_trace must be HttEvidenceTrace")
    artifact_id_text = _non_empty(artifact_id, "artifact_id")
    artifact_path_text = _non_empty(artifact_path, "artifact_path")
    config_hash_text = _non_empty(config_hash, "config_hash")
    input_hash_values = _non_empty_tuple(input_hashes, "input_hashes")
    command_text = _non_empty(generating_command, "generating_command")
    git_text = _optional_non_empty(git_commit, "git_commit")
    worktree_text = _optional_non_empty(worktree_state, "worktree_state")
    if git_text is None and worktree_text is None:
        raise ValueError("git_commit or worktree_state is required")

    anatomy = summarize_evidence_anatomy(
        evidence_trace.channel_contributions,
        model_label=evidence_trace.model_label,
        total_delta_lnB=evidence_trace.total_delta_lnB,
        consistency_tolerance=consistency_tolerance,
        residual_floor=residual_floor,
    )
    residual_payload = (
        predictive_residual_atlas_payload(residual_atlas)
        if residual_atlas is not None
        else None
    )
    blocked_reasons = list(evidence_trace.blocked_reasons)
    if not anatomy.consistent_with_total:
        blocked_reasons.append("evidence_trace_sum_rule_not_ready")
    ready = not blocked_reasons
    default_caveats = (
        DEFAULT_DOMAIN_CAVEAT,
        "mio_reads_htt_trace_without_modification",
        "single_owner_merged_score_forbidden",
        "not_htt_likelihood_or_posterior",
        "family_status_blocked_pre_native_atlas",
        "native_solver_status_not_claimed",
    )
    caveat_values = _dedupe(
        (*default_caveats, *tuple(_non_empty(item, "caveat") for item in caveats))
    )
    report_hash = _stable_hash(
        {
            "schema_version": NARRATIVE_SCHEMA_VERSION,
            "evidence_trace": evidence_trace.as_payload(),
            "anatomy": {
                "total_delta_lnB": anatomy.total_delta_lnB,
                "reconstructed_delta_lnB": anatomy.reconstructed_delta_lnB,
                "relative_residual": anatomy.relative_residual,
            },
            "residual_context": residual_payload or {},
            "config_hash": config_hash_text,
            "input_hashes": input_hash_values,
        }
    )
    manifest = ArtifactManifest(
        artifact_id=artifact_id_text,
        artifact_path=artifact_path_text,
        owner=Owner.MIO,
        implementation_scope=ImplementationScope.MIO,
        claim_tier=ClaimTier.DIAGNOSTIC_ONLY if ready else ClaimTier.BLOCKED,
        production_status=(
            "diagnostic_only" if ready else "blocked_provenance_mismatch"
        ),
        created_by=_NARRATIVE_CREATED_BY,
        git_commit=git_text,
        config_hash=config_hash_text,
        input_hashes=list(
            _dedupe(
                (
                    *input_hash_values,
                    *evidence_trace.input_hashes,
                    evidence_trace.evidence_ref,
                    report_hash,
                )
            )
        ),
        code_version=str(git_text or worktree_text),
        schema_version=NARRATIVE_SCHEMA_VERSION,
        caveats=list(caveat_values),
        required_gates=[
            "htt_evidence_trace_owner_checked",
            "read_only_trace_copy",
            "prior_ppc_loocv_ready",
            "matched_null_ready",
            "single_score_forbidden",
        ],
        passed_gates=[
            "htt_evidence_trace_owner_checked",
            "read_only_trace_copy",
            "single_score_forbidden",
            *(
                ["prior_ppc_loocv_ready"]
                if not {
                    "prior_sweep_not_ready",
                    "posterior_predictive_not_ready",
                    "loocv_not_ready",
                }
                & set(blocked_reasons)
                else []
            ),
            *(
                ["matched_null_ready"]
                if "matched_null_not_ready" not in blocked_reasons
                else []
            ),
        ],
        failed_gates=list(blocked_reasons),
        statistics_definitions={
            "surface": "evidence_anatomy_narrative",
            "null_mock_status": (
                "prior_ppc_loocv_recorded" if ready else "prior_ppc_loocv_blocked"
            ),
            "mio_role": "diagnostic_narrative_only",
            "trace_source_owner": Owner.HTT.value,
            "single_score_status": "forbidden_no_owner_merge",
            "residual_context_status": (
                "attached" if residual_payload is not None else "not_supplied"
            ),
        },
    )
    return EvidenceAnatomyNarrativeReport(
        manifest=manifest,
        evidence_trace=evidence_trace,
        anatomy=anatomy,
        residual_context=residual_payload,
        blocked_reasons=_dedupe(blocked_reasons),
        report_hash=report_hash,
        generating_command=command_text,
        worktree_state=worktree_text,
        git_commit=git_text,
        caveats=caveat_values,
    )


def to_mio_certificate(
    report: EvidenceAnatomyReport,
    *,
    channel: str = "channel_decomposition",
    domain_caveats: Optional[Sequence[str]] = None,
    generated_by: str = "mio.decomposition.evidence_anatomy v0.1",
    input_data_hashes: Optional[Sequence[str]] = None,
    config_hash: Optional[str] = None,
    artifact_path: str = "artifacts/mio/mio_evidence_anatomy_v1.json",
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> MioCertificate:
    """Pack a decomposition report into a ``MioCertificate``."""
    strongest = max(report.contributions, key=lambda item: abs(item.delta_lnB))
    departure = {
        "total_delta_lnB": float(report.total_delta_lnB),
        "reconstructed_delta_lnB": float(report.reconstructed_delta_lnB),
        "strongest_channel_delta_lnB": float(strongest.delta_lnB),
        "n_channels": float(len(report.contributions)),
    }
    adequacy = {
        "sum_rule_within_tolerance": bool(report.consistent_with_total),
        "residual_lt_10pct": bool(report.relative_residual <= 0.10),
    }
    consistency = {
        "residual_delta_lnB": float(report.residual_delta_lnB),
        "relative_residual": float(report.relative_residual),
        "consistency_tolerance": float(report.consistency_tolerance),
    }
    for item in report.contributions:
        key = item.name.lower()
        consistency[f"{key}_delta_lnB"] = float(item.delta_lnB)
        consistency[f"{key}_share"] = float(item.share_of_total)

    caveats = list(domain_caveats) if domain_caveats is not None else []
    if DEFAULT_DOMAIN_CAVEAT not in caveats:
        caveats.append(DEFAULT_DOMAIN_CAVEAT)
    readiness = assess_mio_readiness(MioPrerequisites(eligible_for_production=False))

    return build_mio_certificate(
        report_type="evidence_anatomy",
        probe_name=report.model_label,
        channel=channel,
        departure_variables=departure,
        adequacy_indicators=adequacy,
        consistency_metrics=consistency,
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by=generated_by,
        input_data_hashes=list(input_data_hashes) if input_data_hashes else [],
        config_hash=config_hash,
        htt_cross_check_suggested={
            "compare_to": "htt.core.analysis_extended.evidence_matrix_report_artifact",
            "expected_relation": "channel contributions should reconstruct the HTT total evidence within tolerance",
        },
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
        readiness=readiness,
        artifact_id="mio.evidence_anatomy.certificate",
        artifact_path=artifact_path,
        statistics_definitions={
            "report_type": "evidence_anatomy",
            "channel": channel,
        },
    )


ARTEFACT_FILENAME = "mio_evidence_anatomy_v1.json"


def emit_evidence_anatomy_artefact(
    out_path: Path,
    channel_contributions: Mapping[str, float],
    *,
    model_label: str = SAFE_DEFAULT_MODEL_LABEL,
    total_delta_lnB: Optional[float] = None,
    consistency_tolerance: float = 0.10,
    residual_floor: float = 1e-3,
    domain_caveats: Optional[Sequence[str]] = None,
    input_data_hashes: Optional[Sequence[str]] = None,
    tsc_overlay: TscAdequacyOverlay | None = None,
    tsc_overlay_ref: str | None = None,
) -> dict:
    """Persist a JSON artifact for channel-by-channel evidence anatomy."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if not out_path.name.startswith("mio_"):
        raise ValueError(
            f"artefact filename must start with 'mio_' (REG-02): got {out_path.name}"
        )

    report = summarize_evidence_anatomy(
        channel_contributions,
        model_label=model_label,
        total_delta_lnB=total_delta_lnB,
        consistency_tolerance=consistency_tolerance,
        residual_floor=residual_floor,
    )
    cert = to_mio_certificate(
        report,
        domain_caveats=domain_caveats,
        input_data_hashes=input_data_hashes,
        artifact_path=str(out_path),
        tsc_overlay=tsc_overlay,
        tsc_overlay_ref=tsc_overlay_ref,
    )

    payload = {
        "schema_version": "v1",
        "report": {
            "model_label": report.model_label,
            "contributions": [asdict(item) for item in report.contributions],
            "total_delta_lnB": report.total_delta_lnB,
            "reconstructed_delta_lnB": report.reconstructed_delta_lnB,
            "residual_delta_lnB": report.residual_delta_lnB,
            "relative_residual": report.relative_residual,
            "consistency_tolerance": report.consistency_tolerance,
            "consistent_with_total": report.consistent_with_total,
        },
        "certificate": certificate_to_payload(cert),
    }
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


__all__ = [
    "ARTEFACT_FILENAME",
    "DEFAULT_DOMAIN_CAVEAT",
    "EvidenceAnatomyContribution",
    "EvidenceAnatomyNarrativeReport",
    "EvidenceAnatomyReport",
    "HttEvidenceTrace",
    "HttEvidenceTraceTerm",
    "build_evidence_anatomy_narrative_report",
    "build_htt_evidence_trace_from_payload",
    "emit_evidence_anatomy_artefact",
    "summarize_evidence_anatomy",
    "to_mio_certificate",
]
