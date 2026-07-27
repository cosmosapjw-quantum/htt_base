"""Legacy BASS scalar budget-ceiling policy reproduction.

This module preserves historical ``U_C`` candidates.  Active analysis uses
typed channel anchors and identified sets; these scalar candidates cannot
normalize a live departure estimand.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import math
import warnings
from typing import Any

from common.transfer_registry import TransferSource, validate_transfer_dependent_result
from mio.formalism.budget_spec import BudgetPolicy, BudgetSpec, BudgetUse

from .atlas_entry import AtlasEntryLite, validate_atlas_entry_lite_metadata

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id
LEGACY_REPRODUCTION_ONLY = True

warnings.warn(
    "bass.atlas.budget_ceiling_optimizer is a legacy scalar-policy surface",
    DeprecationWarning,
    stacklevel=2,
)

_SCHEMA_VERSION = "bass.budget_ceiling_policy.v1"
_RESULT_SCHEMA_VERSION = "bass.budget_ceiling_policy_result.v1"
_DEFAULT_CAVEAT = (
    "BASS budget ceiling policy metadata only; diagnostic pre-solver "
    "denominator interface, not native solver output or classification."
)
_EXTERNAL_SOURCES = {
    TransferSource.ANICLASS_EXTERNAL.value,
    TransferSource.EXTERNAL_TRANSFER.value,
    TransferSource.EMPIRICAL_PROXY.value,
}
_ALLOWED_NUMERIC_SOURCES = _EXTERNAL_SOURCES | {TransferSource.NONE.value}
_ALLOWED_ADMISSIBLE_SET_STATUSES = {
    "legacy_mes_admissible",
    "external_transfer_domain",
    "explicit_pre_solver",
    "depth_binned_pre_solver",
}
_ALLOWED_RANK_STATUSES = {
    "full_rank",
    "not_evaluated",
    "rank_deficient",
    "rank_not_applicable_certified_mes",
}
_HIDDEN_MARKERS = {"", "all", "default", "implicit", "none", "unknown"}
_FORBIDDEN_KEYS = {
    "certificate",
    "evidence",
    "family_id",
    "family_identified",
    "geometry_detected",
    "likelihood",
    "log_evidence",
    "mio_certificate",
    "posterior",
    "posterior_weight",
    "prior_weight",
    "truth",
}
_FORBIDDEN_KEY_PARTS = (
    "certificate",
    "evidence",
    "family_id",
    "family_ident",
    "geometry_detect",
    "likelihood",
    "posterior",
    "truth",
)
_FORBIDDEN_PHRASES = (
    "bayes factor",
    "bianchi family identified",
    "family identification",
    "family ranking",
    "geometry detected",
    "htt evidence",
    "mio posterior",
    "model-independent proof",
    "morphology compatibility",
    "native solver result",
    "native validated",
    "native validation",
    "truth certificate",
)
_NEGATING_MARKERS = (
    "blocked",
    "cannot",
    "not ",
    "not_",
    "not-",
    "no ",
    "non_",
    "non-",
    "without",
)
_DEPTH_GAP_REQUIRED_FIELDS = {
    "bin_edges",
    "covariance_status",
    "denominator_evolution_status",
    "depth_convention",
    "null_mock_status",
}


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "value"):
        return str(value.value)
    raise TypeError(f"metadata value {value!r} is not JSON-compatible")


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        _jsonable(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = _canonical_json(payload).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _non_empty(value: object, name: str) -> str:
    if value is None:
        raise ValueError(f"{name} must be non-empty")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _explicit_text(value: object, name: str) -> str:
    text = _non_empty(value, name)
    if text.lower() in _HIDDEN_MARKERS:
        raise ValueError(f"{name} must be explicit, not {text!r}")
    return text


def _positive_finite(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be positive finite") from exc
    if not math.isfinite(number) or number <= 0.0:
        raise ValueError(f"{name} must be positive finite")
    return number


def _finite(value: object, name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be finite") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def _hash_list(values: Sequence[object], name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a non-string sequence")
    result = tuple(_non_empty(value, name) for value in values)
    if not result:
        raise ValueError(f"{name} must contain at least one hash")
    return result


def _metadata_mapping(value: Mapping[str, Any], name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{name} must be a mapping")
    normalised = _jsonable(value)
    if not isinstance(normalised, dict) or not normalised:
        raise ValueError(f"{name} must be a non-empty mapping")
    _reject_claim_surface(normalised, name)
    return normalised


def _optional_metadata_mapping(
    value: Mapping[str, Any] | None,
    name: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    return _metadata_mapping(value, name)


def _optional_atlas_entry_metadata(
    value: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if value is None:
        return None
    normalised = _jsonable(value)
    if not isinstance(normalised, dict) or not normalised:
        raise ValueError("atlas_entry_metadata must be a non-empty mapping")
    validate_atlas_entry_lite_metadata(normalised)
    return normalised


def _caveats(values: Sequence[object]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("caveats must be a non-string sequence")
    normalised = tuple(_non_empty(value, "caveats") for value in values)
    for caveat in normalised:
        _reject_claim_surface(caveat, "caveats")
    if _DEFAULT_CAVEAT not in normalised:
        normalised = (_DEFAULT_CAVEAT, *normalised)
    return tuple(dict.fromkeys(normalised))


def _reject_claim_surface(value: object, name: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in _FORBIDDEN_KEYS or any(
                part in key_text for part in _FORBIDDEN_KEY_PARTS
            ):
                raise ValueError(f"{name} cannot carry inference or claim key {key!r}")
            _reject_claim_surface(item, name)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_claim_surface(item, name)
        return
    if not isinstance(value, str):
        return
    text = value.lower().replace("_", " ").replace("-", " ")
    for clause in _claim_clauses(text):
        for phrase in _FORBIDDEN_PHRASES:
            if phrase in clause and not _phrase_is_negated(clause, phrase):
                raise ValueError(
                    f"{name} cannot carry overclaim or inference phrase {phrase!r}"
                )
        if (
            "external transfer" in clause
            and "validated" in clause
            and "native" in clause
            and not _phrase_is_negated(clause, "external transfer")
        ):
            raise ValueError(
                f"{name} cannot carry external-transfer/native conflation language"
            )


def _claim_clauses(text: str) -> tuple[str, ...]:
    for separator in (";", "\n"):
        text = text.replace(separator, ".")
    return tuple(clause.strip() for clause in text.split(".") if clause.strip())


def _phrase_is_negated(clause: str, phrase: str) -> bool:
    index = clause.find(phrase)
    if index < 0:
        return False
    prefix = clause[:index]
    return any(marker in prefix for marker in _NEGATING_MARKERS)


def _valid_range(value: Mapping[str, Any]) -> dict[str, Any]:
    valid_range = _metadata_mapping(value, "valid_range")
    if {"k_min", "k_max", "ell_min", "ell_max"} <= set(valid_range):
        k_min = _positive_finite(valid_range["k_min"], "valid_range.k_min")
        k_max = _positive_finite(valid_range["k_max"], "valid_range.k_max")
        if k_max <= k_min:
            raise ValueError("valid_range.k_max must be greater than k_min")
        ell_min = int(valid_range["ell_min"])
        ell_max = int(valid_range["ell_max"])
        if ell_min < 0 or ell_max < ell_min:
            raise ValueError("valid_range ell bounds are invalid")
        return valid_range

    keys = set(valid_range)
    min_keys = sorted(key for key in keys if key.endswith("_min"))
    if not min_keys:
        raise ValueError("valid_range requires explicit bound pairs")
    for lower_key in min_keys:
        stem = lower_key[: -len("_min")]
        upper_key = f"{stem}_max"
        if upper_key not in valid_range:
            raise ValueError(f"valid_range missing {upper_key}")
        lower = _finite(valid_range[lower_key], f"valid_range.{lower_key}")
        upper = _finite(valid_range[upper_key], f"valid_range.{upper_key}")
        if upper < lower:
            raise ValueError(f"valid_range {upper_key} must be >= {lower_key}")
    return valid_range


def _budget_uses(values: Sequence[BudgetUse | str]) -> tuple[BudgetUse, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("admissible_uses must be a sequence")
    uses = tuple(BudgetUse(str(value)) for value in values)
    if not uses:
        raise ValueError("admissible_uses must contain at least one use")
    return tuple(dict.fromkeys(uses))


def _transfer_source(value: object) -> str:
    source = TransferSource(str(value))
    if source.value not in _ALLOWED_NUMERIC_SOURCES:
        raise ValueError(
            "numeric budget ceiling candidates require no transfer or current "
            "external/proxy transfer provenance"
        )
    return source.value


def _budget_policy_for_source(source: str) -> BudgetPolicy:
    if source == TransferSource.NONE.value:
        return BudgetPolicy.MES_LINEAR
    return BudgetPolicy.EXTERNAL_TRANSFER


def _depth_gap_metadata(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    metadata = _metadata_mapping(value, "depth_gap_metadata")
    missing = sorted(_DEPTH_GAP_REQUIRED_FIELDS - set(metadata))
    if missing:
        raise ValueError(
            "depth_gap_metadata missing required field(s): " + ", ".join(missing)
        )
    if metadata["covariance_status"] == "not_statistical":
        raise ValueError("depth_gap_metadata requires covariance_status")
    if metadata["null_mock_status"] == "not_statistical":
        raise ValueError("depth_gap_metadata requires null_mock_status")
    return metadata


def _rank_is_reference_adequate(candidate: "BudgetCeilingCandidate") -> bool:
    if candidate.rank_status == "full_rank":
        return (
            candidate.response_rank is not None
            and candidate.response_rank > 0
            and candidate.nuisance_projected_rank is not None
            and 0 < candidate.nuisance_projected_rank <= candidate.response_rank
            and candidate.condition_number is not None
        )
    return candidate.rank_status == "rank_not_applicable_certified_mes"


def _require_rank_for_mio_use(
    candidate: "BudgetCeilingCandidate",
    uses: tuple[BudgetUse, ...],
) -> None:
    if uses == (BudgetUse.DENOMINATOR_SENSITIVITY,):
        return
    if not _rank_is_reference_adequate(candidate):
        raise ValueError(
            "MIO ceiling references require rank_status='full_rank' with rank "
            "metadata or rank_not_applicable_certified_mes"
        )


@dataclass(frozen=True)
class CeilingPrior:
    """Explicit prior/measure metadata for a ceiling policy."""

    prior_id: str
    prior_hash: str
    prior_support: Mapping[str, Any]
    prior_measure: str
    prior_description: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "prior_id", _explicit_text(self.prior_id, "prior_id"))
        object.__setattr__(
            self,
            "prior_hash",
            _explicit_text(self.prior_hash, "prior_hash"),
        )
        object.__setattr__(
            self,
            "prior_support",
            _metadata_mapping(self.prior_support, "prior_support"),
        )
        object.__setattr__(
            self,
            "prior_measure",
            _explicit_text(self.prior_measure, "prior_measure"),
        )
        object.__setattr__(
            self,
            "prior_description",
            _explicit_text(self.prior_description, "prior_description"),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "prior_id": self.prior_id,
            "prior_hash": self.prior_hash,
            "prior_support": dict(self.prior_support),
            "prior_measure": self.prior_measure,
            "prior_description": self.prior_description,
        }


@dataclass(frozen=True)
class AdmissibleSetMetadata:
    """Explicit admissible-set metadata for a ceiling policy."""

    admissible_set_id: str
    admissible_set_hash: str
    admissible_set_status: str
    admissible_set_definition_ref: str
    parameter_bounds: Mapping[str, Any]
    constraints: Sequence[object] = ()
    exclusions: Sequence[object] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "admissible_set_id",
            _explicit_text(self.admissible_set_id, "admissible_set_id"),
        )
        object.__setattr__(
            self,
            "admissible_set_hash",
            _explicit_text(self.admissible_set_hash, "admissible_set_hash"),
        )
        status = _explicit_text(self.admissible_set_status, "admissible_set_status")
        if status not in _ALLOWED_ADMISSIBLE_SET_STATUSES:
            raise ValueError(
                "admissible_set_status must be explicit and one of: "
                + ", ".join(sorted(_ALLOWED_ADMISSIBLE_SET_STATUSES))
            )
        object.__setattr__(self, "admissible_set_status", status)
        object.__setattr__(
            self,
            "admissible_set_definition_ref",
            _explicit_text(
                self.admissible_set_definition_ref,
                "admissible_set_definition_ref",
            ),
        )
        object.__setattr__(
            self,
            "parameter_bounds",
            _metadata_mapping(self.parameter_bounds, "parameter_bounds"),
        )
        object.__setattr__(
            self,
            "constraints",
            tuple(
                _explicit_text(value, "constraints") for value in self.constraints
            ),
        )
        object.__setattr__(
            self,
            "exclusions",
            tuple(_explicit_text(value, "exclusions") for value in self.exclusions),
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "admissible_set_id": self.admissible_set_id,
            "admissible_set_hash": self.admissible_set_hash,
            "admissible_set_status": self.admissible_set_status,
            "admissible_set_definition_ref": self.admissible_set_definition_ref,
            "parameter_bounds": dict(self.parameter_bounds),
            "constraints": list(self.constraints),
            "exclusions": list(self.exclusions),
        }


@dataclass(frozen=True)
class BudgetCeilingCandidate:
    """One positive finite numeric ``U_C`` candidate plus provenance."""

    candidate_id: str
    U_C: float
    comparator: str
    frame: str
    units: str
    valid_range: Mapping[str, Any]
    transfer_source: str = "none"
    transfer_spec_id: str | None = None
    transfer_metadata: Mapping[str, Any] | None = None
    atlas_entry_metadata: Mapping[str, Any] | None = None
    candidate_metadata: Mapping[str, Any] = field(default_factory=dict)
    rank_status: str = "not_evaluated"
    response_rank: int | None = None
    nuisance_projected_rank: int | None = None
    condition_number: float | None = None

    def __post_init__(self) -> None:
        candidate_id = _explicit_text(self.candidate_id, "candidate_id")
        source = _transfer_source(self.transfer_source)
        transfer_spec_id = (
            None
            if self.transfer_spec_id is None
            else _explicit_text(self.transfer_spec_id, "transfer_spec_id")
        )
        transfer_metadata = _optional_metadata_mapping(
            self.transfer_metadata,
            "transfer_metadata",
        )
        atlas_entry_metadata = _optional_atlas_entry_metadata(self.atlas_entry_metadata)
        if source in _EXTERNAL_SOURCES:
            if transfer_spec_id is None:
                raise ValueError(
                    "external/proxy ceiling candidates require transfer_spec_id"
                )
            if transfer_metadata is None:
                raise ValueError(
                    "external/proxy ceiling candidates require transfer_metadata"
                )
            validate_transfer_dependent_result(transfer_metadata)
            if transfer_metadata.get("native_solver_result") is True:
                raise ValueError("external transfer ceiling cannot be native output")
            if str(transfer_metadata["transfer_source"]) != source:
                raise ValueError(
                    "BudgetCeilingCandidate transfer_source must match metadata"
                )
        elif transfer_spec_id is not None or transfer_metadata is not None:
            raise ValueError(
                "transfer_source='none' candidates must not carry transfer provenance"
            )
        valid_range = _valid_range(self.valid_range)
        candidate_metadata = _metadata_mapping(
            self.candidate_metadata or {"candidate_role": "explicit_ceiling"},
            "candidate_metadata",
        )
        rank_status = _explicit_text(self.rank_status, "rank_status")
        if rank_status not in _ALLOWED_RANK_STATUSES:
            raise ValueError(
                "rank_status must be one of: "
                + ", ".join(sorted(_ALLOWED_RANK_STATUSES))
            )
        response_rank = None if self.response_rank is None else int(self.response_rank)
        nuisance_rank = (
            None
            if self.nuisance_projected_rank is None
            else int(self.nuisance_projected_rank)
        )
        condition_number = (
            None
            if self.condition_number is None
            else _positive_finite(self.condition_number, "condition_number")
        )
        if response_rank is not None and response_rank < 0:
            raise ValueError("response_rank must be non-negative")
        if nuisance_rank is not None and nuisance_rank < 0:
            raise ValueError("nuisance_projected_rank must be non-negative")
        if rank_status == "full_rank":
            if response_rank is None or response_rank <= 0:
                raise ValueError("full_rank requires positive response_rank")
            if nuisance_rank is None or not (0 < nuisance_rank <= response_rank):
                raise ValueError(
                    "full_rank requires 0 < nuisance_projected_rank <= response_rank"
                )
            if condition_number is None:
                raise ValueError("full_rank requires condition_number")
        if rank_status == "rank_not_applicable_certified_mes" and source != "none":
            raise ValueError(
                "rank_not_applicable_certified_mes is only allowed for no-transfer "
                "MES ceilings"
            )

        object.__setattr__(self, "candidate_id", candidate_id)
        object.__setattr__(self, "U_C", _positive_finite(self.U_C, "U_C"))
        object.__setattr__(self, "comparator", _explicit_text(self.comparator, "comparator"))
        object.__setattr__(self, "frame", _explicit_text(self.frame, "frame"))
        object.__setattr__(self, "units", _explicit_text(self.units, "units"))
        object.__setattr__(self, "valid_range", valid_range)
        object.__setattr__(self, "transfer_source", source)
        object.__setattr__(self, "transfer_spec_id", transfer_spec_id)
        object.__setattr__(self, "transfer_metadata", transfer_metadata)
        object.__setattr__(self, "atlas_entry_metadata", atlas_entry_metadata)
        object.__setattr__(self, "candidate_metadata", candidate_metadata)
        object.__setattr__(self, "rank_status", rank_status)
        object.__setattr__(self, "response_rank", response_rank)
        object.__setattr__(self, "nuisance_projected_rank", nuisance_rank)
        object.__setattr__(self, "condition_number", condition_number)

    @classmethod
    def from_atlas_entry(
        cls,
        atlas_entry: AtlasEntryLite,
        *,
        candidate_id: str,
        U_C: float,
        comparator: str,
        frame: str,
        units: str,
        candidate_metadata: Mapping[str, Any] | None = None,
        rank_status: str = "not_evaluated",
        response_rank: int | None = None,
        nuisance_projected_rank: int | None = None,
        condition_number: float | None = None,
    ) -> "BudgetCeilingCandidate":
        """Build a numeric candidate from an external/proxy atlas entry."""

        if not isinstance(atlas_entry, AtlasEntryLite):
            raise TypeError("from_atlas_entry requires AtlasEntryLite")
        metadata = atlas_entry.to_metadata()
        validate_atlas_entry_lite_metadata(metadata)
        if atlas_entry.is_future_native_schema:
            raise ValueError(
                "schema-only future native AtlasEntryLite cannot provide numeric U_C"
            )
        return cls(
            candidate_id=candidate_id,
            U_C=U_C,
            comparator=comparator,
            frame=frame,
            units=units,
            valid_range=atlas_entry.transfer_metadata["valid_range"],
            transfer_source=atlas_entry.transfer_source,
            transfer_spec_id=atlas_entry.transfer_id,
            transfer_metadata=atlas_entry.transfer_metadata,
            atlas_entry_metadata=metadata,
            candidate_metadata=(
                {"candidate_role": "external_transfer_ceiling"}
                if candidate_metadata is None
                else candidate_metadata
            ),
            rank_status=rank_status,
            response_rank=response_rank,
            nuisance_projected_rank=nuisance_projected_rank,
            condition_number=condition_number,
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "U_C": self.U_C,
            "comparator": self.comparator,
            "frame": self.frame,
            "units": self.units,
            "valid_range": dict(self.valid_range),
            "transfer_source": self.transfer_source,
            "transfer_spec_id": self.transfer_spec_id,
            "transfer_metadata": self.transfer_metadata,
            "atlas_entry_hash": (
                None
                if self.atlas_entry_metadata is None
                else self.atlas_entry_metadata.get("entry_hash")
            ),
            "candidate_metadata": dict(self.candidate_metadata),
            "rank_status": self.rank_status,
            "response_rank": self.response_rank,
            "nuisance_projected_rank": self.nuisance_projected_rank,
            "condition_number": self.condition_number,
        }


@dataclass(frozen=True)
class BudgetCeilingPolicyResult:
    """Selected BASS ceiling policy result with MIO reference helpers."""

    ceiling_policy_id: str
    selected_candidate: BudgetCeilingCandidate
    prior: CeilingPrior
    admissible_set: AdmissibleSetMetadata
    selection_rule: str
    objective: str
    config_hash: str
    input_hashes: tuple[str, ...]
    generating_command: str
    git_commit_or_worktree_state: str
    rejected_candidates: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    depth_gap_metadata: Mapping[str, Any] | None = None
    caveats: Sequence[object] = field(default_factory=lambda: (_DEFAULT_CAVEAT,))
    owner: str = "BASS"
    implementation_scope: str = "bass_py"
    claim_tier: str = "diagnostic_only"
    production_status: str = "diagnostic_only"
    schema_version: str = _RESULT_SCHEMA_VERSION
    ceiling_result_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.selected_candidate, BudgetCeilingCandidate):
            raise TypeError("selected_candidate must be BudgetCeilingCandidate")
        if not isinstance(self.prior, CeilingPrior):
            raise TypeError("prior must be CeilingPrior")
        if not isinstance(self.admissible_set, AdmissibleSetMetadata):
            raise TypeError("admissible_set must be AdmissibleSetMetadata")
        if self.owner != "BASS":
            raise ValueError("BudgetCeilingPolicyResult owner must be BASS")
        if self.implementation_scope != "bass_py":
            raise ValueError(
                "BudgetCeilingPolicyResult implementation_scope must be bass_py"
            )
        if self.claim_tier != "diagnostic_only":
            raise ValueError(
                "BudgetCeilingPolicyResult claim_tier must be diagnostic_only"
            )
        if self.production_status != "diagnostic_only":
            raise ValueError(
                "BudgetCeilingPolicyResult production_status must be diagnostic_only"
            )
        if self.schema_version != _RESULT_SCHEMA_VERSION:
            raise ValueError("BudgetCeilingPolicyResult schema_version mismatch")
        rejected_candidates = tuple(
            _metadata_mapping(item, "rejected_candidates")
            for item in self.rejected_candidates
        )
        depth_gap = _depth_gap_metadata(self.depth_gap_metadata)
        caveats = _caveats(self.caveats)
        object.__setattr__(
            self,
            "ceiling_policy_id",
            _explicit_text(self.ceiling_policy_id, "ceiling_policy_id"),
        )
        object.__setattr__(
            self,
            "selection_rule",
            _explicit_text(self.selection_rule, "selection_rule"),
        )
        object.__setattr__(self, "objective", _explicit_text(self.objective, "objective"))
        object.__setattr__(
            self,
            "config_hash",
            _explicit_text(self.config_hash, "config_hash"),
        )
        object.__setattr__(
            self,
            "input_hashes",
            _hash_list(self.input_hashes, "input_hashes"),
        )
        object.__setattr__(
            self,
            "generating_command",
            _explicit_text(self.generating_command, "generating_command"),
        )
        object.__setattr__(
            self,
            "git_commit_or_worktree_state",
            _explicit_text(
                self.git_commit_or_worktree_state,
                "git_commit_or_worktree_state",
            ),
        )
        object.__setattr__(self, "rejected_candidates", rejected_candidates)
        object.__setattr__(self, "depth_gap_metadata", depth_gap)
        object.__setattr__(self, "caveats", caveats)
        object.__setattr__(
            self,
            "ceiling_result_hash",
            _hash_payload(self._hash_material()),
        )

    @property
    def U_C(self) -> float:
        return self.selected_candidate.U_C

    @property
    def transfer_source(self) -> str:
        return self.selected_candidate.transfer_source

    @property
    def transfer_spec_id(self) -> str | None:
        return self.selected_candidate.transfer_spec_id

    @property
    def budget_policy(self) -> BudgetPolicy:
        return _budget_policy_for_source(self.transfer_source)

    @property
    def is_certified_filling_admissible(self) -> bool:
        return (
            self.budget_policy is BudgetPolicy.MES_LINEAR
            and self.admissible_set.admissible_set_status == "legacy_mes_admissible"
        )

    def _hash_material(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ceiling_policy_id": self.ceiling_policy_id,
            "candidate": self.selected_candidate.to_metadata(),
            "prior": self.prior.to_metadata(),
            "admissible_set": self.admissible_set.to_metadata(),
            "selection_rule": self.selection_rule,
            "objective": self.objective,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
        }

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "ceiling_result_hash": self.ceiling_result_hash,
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "production_status": self.production_status,
            "ceiling_policy_id": self.ceiling_policy_id,
            "ceiling_policy_role": "diagnostic_pre_solver_denominator_policy",
            "U_C": self.U_C,
            "budget_policy": self.budget_policy.value,
            "selection_rule": self.selection_rule,
            "objective": self.objective,
            "transfer_source": self.transfer_source,
            "transfer_spec_id": self.transfer_spec_id,
            "transfer_metadata": self.selected_candidate.transfer_metadata,
            "valid_range": dict(self.selected_candidate.valid_range),
            "selected_candidate": self.selected_candidate.to_metadata(),
            "rejected_candidates": list(self.rejected_candidates),
            "prior": self.prior.to_metadata(),
            "admissible_set": self.admissible_set.to_metadata(),
            "rank_status": self.selected_candidate.rank_status,
            "response_rank": self.selected_candidate.response_rank,
            "nuisance_projected_rank": self.selected_candidate.nuisance_projected_rank,
            "condition_number": self.selected_candidate.condition_number,
            "depth_gap_metadata": self.depth_gap_metadata,
            "is_certified_filling_admissible": self.is_certified_filling_admissible,
            "mio_reference": self.to_mio_reference_payload(),
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "generating_command": self.generating_command,
            "git_commit_or_worktree_state": self.git_commit_or_worktree_state,
            "caveats": list(self.caveats),
        }

    def to_mio_reference_payload(
        self,
        *,
        admissible_uses: Sequence[BudgetUse | str] = (
            BudgetUse.DENOMINATOR_SENSITIVITY,
        ),
    ) -> dict[str, Any]:
        uses = _budget_uses(admissible_uses)
        return {
            "ceiling_policy_id": self.ceiling_policy_id,
            "ceiling_result_hash": self.ceiling_result_hash,
            "U_C": self.U_C,
            "budget_policy": self.budget_policy.value,
            "transfer_source": self.transfer_source,
            "transfer_spec_id": self.transfer_spec_id,
            "prior_id": self.prior.prior_id,
            "prior_hash": self.prior.prior_hash,
            "admissible_set_id": self.admissible_set.admissible_set_id,
            "admissible_set_hash": self.admissible_set.admissible_set_hash,
            "valid_range": dict(self.selected_candidate.valid_range),
            "admissible_uses": [use.value for use in uses],
            "rank_status": self.selected_candidate.rank_status,
            "depth_gap_metadata": (
                None if self.depth_gap_metadata is None else dict(self.depth_gap_metadata)
            ),
        }

    def to_mio_budget_spec(
        self,
        *,
        admissible_uses: Sequence[BudgetUse | str] = (
            BudgetUse.DENOMINATOR_SENSITIVITY,
        ),
        denominator_label: str | None = None,
        sky_support_status: str = "not_directional",
        covariance_status: str = "not_statistical",
        null_mock_status: str = "not_statistical",
    ) -> BudgetSpec:
        uses = _budget_uses(admissible_uses)
        _require_rank_for_mio_use(self.selected_candidate, uses)
        if BudgetUse.DEPTH_GAP_REFERENCE in uses:
            if self.depth_gap_metadata is None:
                raise ValueError(
                    "DEPTH_GAP_REFERENCE requires depth_gap_metadata"
                )
            covariance_status = str(self.depth_gap_metadata["covariance_status"])
            null_mock_status = str(self.depth_gap_metadata["null_mock_status"])
        is_admissible_ceiling = BudgetUse.CERTIFIED_FILLING_CEILING in uses
        if is_admissible_ceiling and not self.is_certified_filling_admissible:
            raise ValueError(
                f"{self.budget_policy.value} policy cannot certify filling before "
                "native validation gates"
            )

        assumptions = [
            f"ceiling_policy_id={self.ceiling_policy_id}",
            f"ceiling_result_hash={self.ceiling_result_hash}",
            f"prior_id={self.prior.prior_id}",
            f"admissible_set_id={self.admissible_set.admissible_set_id}",
            f"selection_rule={self.selection_rule}",
            f"objective={self.objective}",
        ]
        if BudgetUse.DEPTH_GAP_REFERENCE in uses and self.depth_gap_metadata:
            assumptions.append(
                "depth_gap_metadata_hash=" + _hash_payload(self.depth_gap_metadata)
            )

        kwargs: dict[str, Any] = {
            "policy": self.budget_policy,
            "denominator_value": self.U_C,
            "denominator_label": denominator_label
            or f"{self.ceiling_policy_id} U_C ceiling",
            "comparator": self.selected_candidate.comparator,
            "frame": self.selected_candidate.frame,
            "units": self.selected_candidate.units,
            "config_hash": self.config_hash,
            "input_hashes": self.input_hashes,
            "assumptions": tuple(assumptions),
            "source_description": (
                "BASS_PY budget ceiling policy interface; "
                f"candidate_id={self.selected_candidate.candidate_id}"
            ),
            "sky_support_status": sky_support_status,
            "covariance_status": covariance_status,
            "null_mock_status": null_mock_status,
            "is_admissible_ceiling": is_admissible_ceiling,
            "admissible_uses": uses,
            "caveats": self.caveats,
        }
        if self.budget_policy is BudgetPolicy.EXTERNAL_TRANSFER:
            kwargs.update(
                transfer_source=self.transfer_source,
                transfer_spec_id=self.transfer_spec_id,
                transfer_metadata=self.selected_candidate.transfer_metadata,
            )
        return BudgetSpec(**kwargs)


def optimize_budget_ceiling(
    candidates: Sequence[BudgetCeilingCandidate],
    *,
    ceiling_policy_id: str,
    prior: CeilingPrior,
    admissible_set: AdmissibleSetMetadata,
    selection_rule: str,
    objective: str,
    config_hash: str,
    input_hashes: Sequence[object],
    generating_command: str,
    git_commit_or_worktree_state: str,
    quantile: float | None = None,
    depth_gap_metadata: Mapping[str, Any] | None = None,
    caveats: Sequence[object] = (_DEFAULT_CAVEAT,),
) -> BudgetCeilingPolicyResult:
    """Select one reference ``U_C`` candidate with explicit policy metadata."""

    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be a sequence of BudgetCeilingCandidate")
    normalised = tuple(candidates)
    if not normalised:
        raise ValueError("optimize_budget_ceiling requires at least one candidate")
    if any(not isinstance(candidate, BudgetCeilingCandidate) for candidate in normalised):
        raise TypeError("all candidates must be BudgetCeilingCandidate objects")
    first = normalised[0]
    for candidate in normalised[1:]:
        if candidate.comparator != first.comparator:
            raise ValueError("all ceiling candidates must share comparator")
        if candidate.frame != first.frame:
            raise ValueError("all ceiling candidates must share frame")
        if candidate.units != first.units:
            raise ValueError("all ceiling candidates must share units")
        if candidate.transfer_source != first.transfer_source:
            raise ValueError("all ceiling candidates must share transfer_source")
        if candidate.transfer_spec_id != first.transfer_spec_id:
            raise ValueError("all ceiling candidates must share transfer_spec_id")
        if set(candidate.valid_range) != set(first.valid_range):
            raise ValueError("all ceiling candidates must share valid_range schema")
    selected = _select_candidate(
        normalised,
        selection_rule=selection_rule,
        quantile=quantile,
    )
    rejected = []
    for candidate in normalised:
        if candidate is selected:
            continue
        metadata = candidate.to_metadata()
        metadata["reason"] = "not_selected_by_policy_rule"
        rejected.append(metadata)
    return BudgetCeilingPolicyResult(
        ceiling_policy_id=ceiling_policy_id,
        selected_candidate=selected,
        prior=prior,
        admissible_set=admissible_set,
        selection_rule=selection_rule,
        objective=objective,
        config_hash=_explicit_text(config_hash, "config_hash"),
        input_hashes=_hash_list(input_hashes, "input_hashes"),
        generating_command=generating_command,
        git_commit_or_worktree_state=git_commit_or_worktree_state,
        rejected_candidates=tuple(rejected),
        depth_gap_metadata=depth_gap_metadata,
        caveats=caveats,
    )


def _select_candidate(
    candidates: tuple[BudgetCeilingCandidate, ...],
    *,
    selection_rule: str,
    quantile: float | None,
) -> BudgetCeilingCandidate:
    rule = _explicit_text(selection_rule, "selection_rule")
    if rule == "max_ceiling":
        return max(candidates, key=lambda candidate: candidate.U_C)
    if rule == "min_ceiling":
        return min(candidates, key=lambda candidate: candidate.U_C)
    if rule == "quantile_higher":
        if quantile is None:
            raise ValueError("quantile_higher selection requires quantile")
        q = _finite(quantile, "quantile")
        if not 0.0 <= q <= 1.0:
            raise ValueError("quantile must be in [0, 1]")
        ordered = tuple(sorted(candidates, key=lambda candidate: candidate.U_C))
        index = math.ceil(q * (len(ordered) - 1))
        return ordered[index]
    raise ValueError(
        "selection_rule must be one of: max_ceiling, min_ceiling, quantile_higher"
    )


__all__ = [
    "AdmissibleSetMetadata",
    "BudgetCeilingCandidate",
    "BudgetCeilingPolicyResult",
    "CeilingPrior",
    "optimize_budget_ceiling",
]
