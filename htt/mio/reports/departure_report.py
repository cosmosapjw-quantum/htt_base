"""Legacy manifest-backed MIO scalar report-card reproduction."""
from __future__ import annotations

import hashlib
import json
import math
import warnings
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
)
from common.enum_compat import StrEnum

LEGACY_REPRODUCTION_ONLY = True

warnings.warn(
    "mio.reports.departure_report is a legacy reproduction surface; "
    "use StatisticalFoundationResultCard for active reporting",
    DeprecationWarning,
    stacklevel=2,
)

SCHEMA_VERSION = "mio.departure_report.v1"
SCORE_ORDER = ("x_C", "Q", "Pi", "F", "G_F")
DEFAULT_REPORT_CAVEAT = (
    "DepartureReport is a diagnostic-only MIO report card that preserves "
    "separate x_C, Q, Pi, F, and G_F sections."
)

_AGGREGATING_KEYS = {
    "headline_score",
    "headline_number",
    "combined_score",
    "combined_mio_htt_score",
    "mio_score",
    "xqfg_score",
    "rank",
    "classification",
}
_RESERVED_KEYS = {
    "posterior",
    "posterior_odds",
    "log_evidence",
    "lnb",
    "likelihood",
    "evidence_weight",
    "model_weight",
    "htt_evidence",
    "mio_posterior",
    "truth_certificate",
    "best_family",
    "family_rank",
    "geometry_label",
}
_RESERVED_TERMS = (
    "posterior",
    "posterior odds",
    "evidence",
    "likelihood",
    "bayes factor",
    "model weight",
    "htt evidence",
    "mio posterior",
    "truth certificate",
    "certifies truth",
    "model independent proof",
    "family identification",
    "family identified",
    "family classification",
    "geometry",
    "class label",
    "solver result",
    "native solver result",
    "external transfer " + "validated as " + "native",
    "validated as native",
    "native validated",
)
_SKIP_VALUE_SCAN_KEYS = {
    "caveats",
    "claim boundary",
    "forbidden claims",
    "does not establish",
    "allowed use",
    "forbidden use",
    "legacy compatibility",
}


def _reserved_key_sets() -> tuple[set[str], tuple[str, ...]]:
    exact = {
        _normalise_claim_text(key)
        for key in (*_AGGREGATING_KEYS, *_RESERVED_KEYS)
    }
    patterns = (
        "posterior",
        "likelihood",
        "evidence",
        "lnb",
        "bayes factor",
        "model weight",
        "truth certificate",
        "htt evidence",
        "mio posterior",
        "headline",
        "combined score",
        "combined report score",
        "family id",
        "family rank",
        "family ranking",
        "best family",
        "geometry",
        "native solver",
        "solver result",
        "classification",
    )
    return exact, patterns


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} must be non-empty")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _optional_non_empty(value: object | None, name: str) -> str | None:
    if value is None:
        return None
    return _non_empty(value, name)


def _tuple_of_str(
    values: Sequence[object],
    name: str,
    *,
    require_non_empty: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    result = tuple(str(value).strip() for value in values)
    if require_non_empty and not result:
        raise ValueError(f"{name} must contain at least one entry")
    if any(not value for value in result):
        raise ValueError(f"{name} must contain only non-empty strings")
    return result


def _normalise_claim_text(value: object) -> str:
    return " ".join(str(value).lower().replace("_", " ").replace("-", " ").split())


_RESERVED_KEY_EXACT, _RESERVED_KEY_PATTERNS = _reserved_key_sets()


def _reject_reserved_key(key: object, name: str) -> None:
    text = _normalise_claim_text(key)
    if text in _RESERVED_KEY_EXACT:
        if text in {_normalise_claim_text(key) for key in _AGGREGATING_KEYS}:
            raise ValueError(
                f"{name} must not include headline aggregation key {key!r}"
            )
        raise ValueError(f"{name} must not include reserved inference key {key!r}")
    for pattern in _RESERVED_KEY_PATTERNS:
        if pattern in text:
            raise ValueError(f"{name} must not include reserved report key {key!r}")


def _plain_json(value: object) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Sequence):
        return [_plain_json(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("metadata floats must be finite")
        return value
    if isinstance(value, (int, bool)) or value is None:
        return value
    raise TypeError(f"value {value!r} is not JSON-compatible")


def _normalise_metadata(
    value: Mapping[str, object] | None,
    name: str,
) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a mapping")
    try:
        result = _plain_json(dict(value))
    except TypeError as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc
    if not isinstance(result, dict):
        raise ValueError(f"{name} must be a mapping")
    _ensure_json(result, name)
    _scan_reserved_language(result, name)
    return result


def _ensure_json(value: object, name: str) -> None:
    try:
        json.dumps(value, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be JSON-compatible") from exc


def _scan_reserved_language(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if (
                _normalise_claim_text(key) == "classification"
                and str(item) == "BC1_LEGACY_PROJECTION"
            ):
                continue
            _reject_reserved_key(key, name)
            _scan_reserved_language(item, name)
        return
    if isinstance(value, (str, bytes)):
        text = _normalise_claim_text(value)
        for term in _RESERVED_TERMS:
            if _normalise_claim_text(term) in text:
                raise ValueError(
                    f"{name} must not use reserved report language: {term}"
                )
        return
    if isinstance(value, Sequence):
        for item in value:
            _scan_reserved_language(item, name)


def _scan_section_payload_language(value: object, name: str) -> None:
    """Reject claim drift in arbitrary section payloads while allowing caveats."""

    if isinstance(value, Mapping):
        for key, item in value.items():
            if (
                _normalise_claim_text(key) == "classification"
                and str(item) == "BC1_LEGACY_PROJECTION"
            ):
                continue
            _reject_reserved_key(key, name)
            if _normalise_claim_text(key) in _SKIP_VALUE_SCAN_KEYS:
                continue
            _scan_section_payload_language(item, name)
        return
    if isinstance(value, (str, bytes)):
        text = _normalise_claim_text(value)
        for term in _RESERVED_TERMS:
            if _normalise_claim_text(term) in text:
                raise ValueError(
                    f"{name} must not use reserved report language: {term}"
                )
        return
    if isinstance(value, Sequence):
        for item in value:
            _scan_section_payload_language(item, name)


def _payload_from(value: object, name: str) -> dict[str, Any]:
    as_payload = getattr(value, "as_payload", None)
    if not callable(as_payload):
        raise TypeError(f"{name} must expose as_payload()")
    payload = as_payload()
    if not isinstance(payload, Mapping):
        raise TypeError(f"{name}.as_payload() must return a mapping")
    result = _plain_json(payload)
    if not isinstance(result, dict):
        raise TypeError(f"{name}.as_payload() must return a mapping")
    _ensure_json(result, f"{name}.payload")
    _require_mio_diagnostic_payload(result, name)
    _scan_section_payload_language(result, f"{name}.payload")
    return result


def _require_mio_diagnostic_payload(payload: Mapping[str, object], name: str) -> None:
    if payload.get("owner") != Owner.MIO.value:
        raise ValueError(f"{name} owner must be MIO")
    if payload.get("implementation_scope") != ImplementationScope.MIO.value:
        raise ValueError(f"{name} implementation_scope must be mio")
    if payload.get("claim_tier") != ClaimTier.DIAGNOSTIC_ONLY.value:
        raise ValueError(f"{name} claim_tier must be diagnostic_only")


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _unique_strings(values: Sequence[object]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values if str(value).strip()))


def _payload_hashes(payload: Mapping[str, object]) -> tuple[str, ...]:
    raw = payload.get("input_hashes", ())
    if raw is None:
        return ()
    if isinstance(raw, (str, bytes)):
        return (str(raw),)
    if isinstance(raw, Sequence):
        return _unique_strings(raw)
    raise ValueError("input_hashes must be a string sequence")


def _section_status(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if value is None:
        return "not_reported"
    return str(value)


def _extract_transfer_provenance(
    label: str,
    payload: Mapping[str, object] | None,
) -> dict[str, object]:
    if payload is None:
        return {"status": "not_provided", "transfer_source": "not_provided"}
    result: dict[str, object] = {
        "status": "available",
        "score_label": label,
        "transfer_source": str(payload.get("transfer_source", "none")),
    }
    for key in (
        "transfer_spec_id",
        "transfer_metadata",
        "departure_transfer_source",
        "departure_transfer_spec_id",
        "departure_transfer_metadata",
        "budget_transfer_source",
        "budget_transfer_spec_id",
        "budget_transfer_metadata",
        "departure_transfer_sources",
        "departure_transfer_spec_ids",
        "departure_transfer_metadata",
        "budget_transfer_sources",
        "budget_transfer_spec_ids",
        "budget_transfer_metadata",
        "source_transfer_sources",
        "source_transfer_spec_ids",
        "source_transfer_metadata",
        "transfer_spec_ids",
        "transfer_metadata_by_bin",
        "transfer_metadata_hash_by_bin",
    ):
        if key in payload:
            result[key] = payload[key]
    return result


def _transfer_source_summary(
    transfer_by_section: Mapping[str, Mapping[str, object]],
) -> str:
    sources = [
        str(value.get("transfer_source"))
        for value in transfer_by_section.values()
        if value.get("status") == "available" and value.get("transfer_source") not in {None, "none"}
    ]
    if not sources:
        return "none"
    unique = set(sources)
    if len(unique) == 1:
        return sources[0]
    return "mixed_by_section"


def _manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    payload = _plain_json(asdict(manifest))
    if not isinstance(payload, dict):
        raise TypeError("manifest payload must be a mapping")
    return payload


def _build_section(
    *,
    label: str,
    payload: Mapping[str, object] | None,
) -> "DepartureReportSection":
    if payload is None:
        return DepartureReportSection(
            score_label=label,
            status="not_provided",
            payload=None,
            transfer_provenance=_extract_transfer_provenance(label, None),
            config_hash=None,
            input_hashes=(),
            caveats=(),
            sky_support_status="not_reported",
            covariance_status="not_reported",
            null_mock_status="not_reported",
            mask_status="not_reported",
        )
    return DepartureReportSection(
        score_label=label,
        status="available",
        payload=dict(payload),
        transfer_provenance=_extract_transfer_provenance(label, payload),
        config_hash=(
            None if payload.get("config_hash") is None else str(payload["config_hash"])
        ),
        input_hashes=_payload_hashes(payload),
        caveats=_tuple_of_str(payload.get("caveats", ()), f"{label}.caveats"),
        sky_support_status=_section_status(payload, "sky_support_status"),
        covariance_status=_section_status(payload, "covariance_status"),
        null_mock_status=_section_status(payload, "null_mock_status"),
        mask_status=_section_status(payload, "mask_status"),
    )


@dataclass(frozen=True)
class DepartureReportSection:
    """One score section in a MIO departure report card."""

    score_label: str
    status: str
    payload: Mapping[str, object] | None
    transfer_provenance: Mapping[str, object]
    config_hash: str | None
    input_hashes: tuple[str, ...]
    caveats: tuple[str, ...]
    sky_support_status: str
    covariance_status: str
    null_mock_status: str
    mask_status: str

    def __post_init__(self) -> None:
        score_label = _non_empty(self.score_label, "score_label")
        if score_label not in SCORE_ORDER:
            raise ValueError(f"score_label must be one of {SCORE_ORDER}")
        status = _non_empty(self.status, "status")
        if status not in {"available", "not_provided"}:
            raise ValueError("section status must be available or not_provided")
        transfer_provenance = _plain_json(dict(self.transfer_provenance))
        if not isinstance(transfer_provenance, dict):
            raise ValueError("transfer_provenance must be a mapping")
        input_hashes = _tuple_of_str(self.input_hashes, "input_hashes")
        caveats = _tuple_of_str(self.caveats, "caveats")
        object.__setattr__(self, "score_label", score_label)
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "transfer_provenance", transfer_provenance)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "caveats", caveats)

    def as_payload(self) -> dict[str, object]:
        return {
            "score_label": self.score_label,
            "status": self.status,
            "payload": None if self.payload is None else dict(self.payload),
            "transfer_provenance": dict(self.transfer_provenance),
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "caveats": list(self.caveats),
            "sky_support_status": self.sky_support_status,
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
            "mask_status": self.mask_status,
        }


@dataclass(frozen=True)
class DepartureReport:
    """Diagnostic-only MIO report card over separate x/Q/Pi/F/G sections."""

    departure_bundle: object
    artifact_id: str
    artifact_path: str
    generating_command: str
    normalized_score: object | None = None
    exceedance_curve: object | None = None
    filling_fraction: object | None = None
    isotropy_gap: object | None = None
    git_commit: str | None = None
    worktree_state: str | None = None
    config_hash: str | None = None
    input_hashes: tuple[str, ...] | None = None
    artifact_metadata: Mapping[str, object] | None = None
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_REPORT_CAVEAT,))

    def __post_init__(self) -> None:
        artifact_id = _non_empty(self.artifact_id, "artifact_id")
        artifact_path = _non_empty(self.artifact_path, "artifact_path")
        generating_command = _non_empty(self.generating_command, "generating_command")
        git_commit = _optional_non_empty(self.git_commit, "git_commit")
        worktree_state = _optional_non_empty(self.worktree_state, "worktree_state")
        if git_commit is None and worktree_state is None:
            raise ValueError("DepartureReport requires git_commit or worktree_state")
        artifact_metadata = _normalise_metadata(
            self.artifact_metadata,
            "artifact_metadata",
        )
        caveats = tuple(dict.fromkeys(_tuple_of_str(self.caveats, "caveats")))
        if DEFAULT_REPORT_CAVEAT not in caveats:
            caveats = (DEFAULT_REPORT_CAVEAT, *caveats)
        _scan_reserved_language(caveats, "caveats")

        x_payload = _payload_from(self.departure_bundle, "departure_bundle")
        q_payload = (
            None
            if self.normalized_score is None
            else _payload_from(self.normalized_score, "normalized_score")
        )
        pi_payload = (
            None
            if self.exceedance_curve is None
            else _payload_from(self.exceedance_curve, "exceedance_curve")
        )
        f_payload = (
            None
            if self.filling_fraction is None
            else _payload_from(self.filling_fraction, "filling_fraction")
        )
        g_payload = (
            None
            if self.isotropy_gap is None
            else _payload_from(self.isotropy_gap, "isotropy_gap")
        )
        self._validate_score_bindings(x_payload=x_payload)

        sections = {
            "x_C": _build_section(label="x_C", payload=x_payload),
            "Q": _build_section(label="Q", payload=q_payload),
            "Pi": _build_section(label="Pi", payload=pi_payload),
            "F": _build_section(label="F", payload=f_payload),
            "G_F": _build_section(label="G_F", payload=g_payload),
        }
        derived_input_hashes = _unique_strings(
            [
                hash_value
                for label in SCORE_ORDER
                for hash_value in sections[label].input_hashes
            ]
        )
        input_hashes = (
            _tuple_of_str(self.input_hashes, "input_hashes", require_non_empty=True)
            if self.input_hashes is not None
            else derived_input_hashes
        )
        if not input_hashes:
            raise ValueError("DepartureReport input_hashes must not be empty")
        config_hash = (
            _non_empty(self.config_hash, "config_hash")
            if self.config_hash is not None
            else _stable_hash(
                {
                    "artifact_id": artifact_id,
                    "artifact_metadata": artifact_metadata,
                    "input_hashes": input_hashes,
                    "score_order": SCORE_ORDER,
                    "section_config_hashes": {
                        label: sections[label].config_hash for label in SCORE_ORDER
                    },
                    "schema_version": SCHEMA_VERSION,
                }
            )
        )
        manifest = ArtifactManifest(
            artifact_id=artifact_id,
            artifact_path=artifact_path,
            owner=Owner.MIO,
            implementation_scope=ImplementationScope.MIO,
            claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
            production_status="diagnostic_only",
            created_by="mio.reports.departure_report",
            git_commit=git_commit,
            config_hash=config_hash,
            input_hashes=list(input_hashes),
            code_version=git_commit or worktree_state or "unknown",
            schema_version=SCHEMA_VERSION,
            caveats=list(caveats),
            required_gates=[
                "mio_owner_scope",
                "diagnostic_only_claim_tier",
                "separate_score_sections",
                "transfer_provenance_by_section",
            ],
            passed_gates=[
                "mio_owner_scope",
                "diagnostic_only_claim_tier",
                "separate_score_sections",
                "transfer_provenance_by_section",
            ],
            failed_gates=[],
            statistics_definitions={
                "x_C": "signed comparator projection payload",
                "Q": "policy-normalized diagnostic payload",
                "Pi": "empirical exceedance-curve payload",
                "F": "certified filling-fraction payload when provided",
                "G_F": "depth-gap payload when provided",
            },
        )

        object.__setattr__(self, "artifact_id", artifact_id)
        object.__setattr__(self, "artifact_path", artifact_path)
        object.__setattr__(self, "generating_command", generating_command)
        object.__setattr__(self, "git_commit", git_commit)
        object.__setattr__(self, "worktree_state", worktree_state)
        object.__setattr__(self, "artifact_metadata", artifact_metadata)
        object.__setattr__(self, "caveats", caveats)
        object.__setattr__(self, "input_hashes", input_hashes)
        object.__setattr__(self, "config_hash", config_hash)
        object.__setattr__(self, "_sections", sections)
        object.__setattr__(self, "manifest", manifest)

    def _validate_score_bindings(self, *, x_payload: Mapping[str, object]) -> None:
        if self.normalized_score is None:
            return
        q_bundle = getattr(self.normalized_score, "departure_bundle", None)
        if q_bundle is None:
            raise ValueError("Q departure bundle provenance is missing")
        q_bundle_payload = _payload_from(q_bundle, "normalized_score.departure_bundle")
        if q_bundle_payload != dict(x_payload):
            raise ValueError("Q departure bundle must match x_C departure bundle")

    @property
    def owner(self) -> str:
        return Owner.MIO.value

    @property
    def implementation_scope(self) -> str:
        return ImplementationScope.MIO.value

    @property
    def claim_tier(self) -> str:
        return ClaimTier.DIAGNOSTIC_ONLY.value

    @property
    def production_status(self) -> str:
        return "diagnostic_only"

    @property
    def sections(self) -> dict[str, DepartureReportSection]:
        return dict(self._sections)

    @property
    def transfer_provenance_by_section(self) -> dict[str, dict[str, object]]:
        return {
            label: dict(self._sections[label].transfer_provenance)
            for label in SCORE_ORDER
        }

    @property
    def transfer_source_summary(self) -> str:
        return _transfer_source_summary(self.transfer_provenance_by_section)

    @property
    def f_status(self) -> dict[str, object]:
        section = self._sections["F"]
        if section.payload is None:
            return {"status": "not_provided", "reason": "not_supplied"}
        return {
            "status": "available",
            "score_label": "F",
            "score_kind": section.payload.get("score_kind"),
            "sample_count": section.payload.get("sample_count"),
            "valid_sample_count": section.payload.get("valid_sample_count"),
            "aggregation_method": section.payload.get("aggregation_method"),
            "ratio_of_means_used": section.payload.get("ratio_of_means_used"),
        }

    @property
    def g_status(self) -> dict[str, object]:
        section = self._sections["G_F"]
        if section.payload is None:
            return {"status": "not_provided", "reason": "not_supplied"}
        return {
            "status": "available",
            "score_label": "G_F",
            "score_kind": section.payload.get("score_kind"),
            "depth_bin_count": section.payload.get("depth_bin_count"),
            "reference_bin_id": section.payload.get("reference_bin_id"),
            "comparison_bin_id": section.payload.get("comparison_bin_id"),
            "floor_label": section.payload.get("floor_label"),
            "covariance_status": section.payload.get("covariance_status"),
            "null_mock_status": section.payload.get("null_mock_status"),
            "mask_status": section.payload.get("mask_status"),
        }

    def as_payload(self) -> dict[str, object]:
        section_payloads = {
            label: self._sections[label].as_payload() for label in SCORE_ORDER
        }
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "production_status": self.production_status,
            "report_role": "mio_diagnostic_report_card",
            "artifact_id": self.artifact_id,
            "artifact_path": self.artifact_path,
            "schema_version": SCHEMA_VERSION,
            "manifest": _manifest_payload(self.manifest),
            "score_order": list(SCORE_ORDER),
            "sections": section_payloads,
            "f_status": self.f_status,
            "g_status": self.g_status,
            "transfer_source_summary": self.transfer_source_summary,
            "transfer_provenance_by_section": self.transfer_provenance_by_section,
            "sky_support_status_by_section": {
                label: section_payloads[label]["sky_support_status"]
                for label in SCORE_ORDER
            },
            "covariance_status_by_section": {
                label: section_payloads[label]["covariance_status"]
                for label in SCORE_ORDER
            },
            "null_mock_status_by_section": {
                label: section_payloads[label]["null_mock_status"]
                for label in SCORE_ORDER
            },
            "mask_status_by_section": {
                label: section_payloads[label]["mask_status"]
                for label in SCORE_ORDER
            },
            "claim_boundary": [
                "diagnostic_only_separate_sections",
                "no_htt_inference_terms",
                "no_native_solver_claims",
                "no_family_or_geometry_claims",
            ],
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "artifact_metadata": dict(self.artifact_metadata),
            "caveats": list(self.caveats),
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        """Return a deterministic JSON representation of the report payload."""

        return json.dumps(
            self.as_payload(),
            sort_keys=True,
            indent=indent,
            allow_nan=False,
        )


def build_departure_report(
    *,
    departure_bundle: object,
    artifact_id: str,
    artifact_path: str,
    generating_command: str,
    normalized_score: object | None = None,
    exceedance_curve: object | None = None,
    filling_fraction: object | None = None,
    isotropy_gap: object | None = None,
    git_commit: str | None = None,
    worktree_state: str | None = None,
    config_hash: str | None = None,
    input_hashes: Sequence[object] | None = None,
    artifact_metadata: Mapping[str, object] | None = None,
    caveats: Sequence[object] | None = None,
) -> DepartureReport:
    """Build a validated MIO diagnostic report card over x/Q/Pi/F/G sections."""

    return DepartureReport(
        departure_bundle=departure_bundle,
        normalized_score=normalized_score,
        exceedance_curve=exceedance_curve,
        filling_fraction=filling_fraction,
        isotropy_gap=isotropy_gap,
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        generating_command=generating_command,
        git_commit=git_commit,
        worktree_state=worktree_state,
        config_hash=config_hash,
        input_hashes=(
            None
            if input_hashes is None
            else _tuple_of_str(input_hashes, "input_hashes", require_non_empty=True)
        ),
        artifact_metadata=artifact_metadata,
        caveats=(DEFAULT_REPORT_CAVEAT,) if caveats is None else tuple(caveats),
    )


__all__ = [
    "DEFAULT_REPORT_CAVEAT",
    "DepartureReport",
    "DepartureReportSection",
    "SCORE_ORDER",
    "SCHEMA_VERSION",
    "build_departure_report",
]
