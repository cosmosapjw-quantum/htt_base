"""Fail-closed remediation-state contracts for the long-horizon rescue DAG.

This module is governance substrate.  It deliberately keeps repository
workflow, terminal execution outcomes, and scientific adjudication on three
orthogonal axes.  In particular, successful execution is never scientific
evidence and a terminal negative receipt is usable only for adjudication
aggregation.

Claim levels are scheme-qualified.  The identically-spelled ``C1`` in the
family gate and roadmap planning schemes is not comparable, and governance
records use the separate ``NOT_APPLICABLE`` scheme.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from enum import Enum
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # pragma: no cover - exercised by the Python 3.10 replay

    class StrEnum(str, Enum):
        """Minimal stdlib-compatible fallback for the declared Python 3.10 floor."""

        def __str__(self) -> str:
            return str(self.value)


UTC = timezone.utc


class RemediationContractError(ValueError):
    """Base error for a fail-closed remediation contract violation."""


class AuthorityError(RemediationContractError):
    """Raised when a principal or adjudicator fails authority validation."""


class OrchestrationState(StrEnum):
    """Repository-workflow state only; this is not scientific readiness."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    TERMINAL = "TERMINAL"
    DORMANT_EXTERNAL = "DORMANT_EXTERNAL"


class ExecutionResolution(StrEnum):
    """Terminal process outcome, independent of scientific status."""

    COMPLETED_SUCCESS = "COMPLETED_SUCCESS"
    COMPLETED_FAILED_WITH_RECEIPT = "COMPLETED_FAILED_WITH_RECEIPT"
    BLOCKED_WITH_RECEIPT = "BLOCKED_WITH_RECEIPT"
    ABANDONED_WITH_RECEIPT = "ABANDONED_WITH_RECEIPT"


class ScientificStatus(StrEnum):
    """Scientific-remediation status requiring explicit transitions."""

    OPEN = "OPEN"
    IN_REMEDIATION = "IN_REMEDIATION"
    EVIDENCE_READY = "EVIDENCE_READY"
    ADJUDICATION_PENDING = "ADJUDICATION_PENDING"
    RESCUED = "RESCUED"
    CORRECTED_SUPERSEDED = "CORRECTED_SUPERSEDED"
    FALSIFIED = "FALSIFIED"
    BLOCKED = "BLOCKED"
    ABANDONED = "ABANDONED"


class ClaimLevelScheme(StrEnum):
    """Versioned namespaces for otherwise ambiguous claim-level labels."""

    FAMILY_GATE_V1 = "family_gate_v1"
    ROADMAP_RESCUE_V1 = "roadmap_rescue_v1"
    NOT_APPLICABLE_GOVERNANCE_V1 = "not_applicable_governance_v1"


class CanonicalClaimTier(Enum):
    """Canonical claim tiers are labels, not an ordinal ladder."""

    EXPLORATORY = "exploratory"
    CONDITIONAL = "conditional"
    DIAGNOSTIC_ONLY = "diagnostic_only"
    VALIDATED = "validated"
    BLOCKED = "blocked"

    @staticmethod
    def _unordered() -> None:
        raise RemediationContractError("canonical claim tiers are unordered")

    def __lt__(self, other: object) -> bool:
        self._unordered()

    def __le__(self, other: object) -> bool:
        self._unordered()

    def __gt__(self, other: object) -> bool:
        self._unordered()

    def __ge__(self, other: object) -> bool:
        self._unordered()


class DependencyMode(StrEnum):
    """Typed dependency semantics for the long-horizon DAG."""

    REQUIRES_SUCCESS = "requires_success"
    REQUIRES_TERMINAL_RECEIPT = "requires_terminal_receipt"
    REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT = "requires_authenticated_external_receipt"
    REQUIRES_ADJUDICATED_CLAIM_SET = "requires_adjudicated_claim_set"


_C_LEVELS = tuple(f"C{index}" for index in range(7))
_LEVELS_BY_SCHEME: Mapping[ClaimLevelScheme, tuple[str, ...]] = {
    ClaimLevelScheme.FAMILY_GATE_V1: _C_LEVELS,
    ClaimLevelScheme.ROADMAP_RESCUE_V1: _C_LEVELS,
    ClaimLevelScheme.NOT_APPLICABLE_GOVERNANCE_V1: ("NOT_APPLICABLE",),
}
_ADJUDICATED_SCIENTIFIC_STATUSES = {
    ScientificStatus.RESCUED,
    ScientificStatus.CORRECTED_SUPERSEDED,
    ScientificStatus.FALSIFIED,
    ScientificStatus.BLOCKED,
    ScientificStatus.ABANDONED,
}
_SCIENTIFIC_TRANSITIONS: Mapping[ScientificStatus, frozenset[ScientificStatus]] = {
    ScientificStatus.OPEN: frozenset({ScientificStatus.IN_REMEDIATION}),
    ScientificStatus.IN_REMEDIATION: frozenset({ScientificStatus.EVIDENCE_READY}),
    ScientificStatus.EVIDENCE_READY: frozenset({ScientificStatus.ADJUDICATION_PENDING}),
    ScientificStatus.ADJUDICATION_PENDING: frozenset(_ADJUDICATED_SCIENTIFIC_STATUSES),
}
_NEGATIVE_EXECUTION_RESOLUTIONS = {
    ExecutionResolution.COMPLETED_FAILED_WITH_RECEIPT,
    ExecutionResolution.BLOCKED_WITH_RECEIPT,
    ExecutionResolution.ABANDONED_WITH_RECEIPT,
}
_TERMINAL_EXECUTION_RESOLUTIONS = frozenset(ExecutionResolution)
_ACTIVE_OWNERS = frozenset({"COMMON", "HTT", "MIO", "BASS", "OBSSTAT"})
_FORBIDDEN_ACTIVE_OWNERS = frozenset(
    {"TSC", "TSC_LEGACY", "TEFF", "MANUSCRIPT", "BASS_PY"}
)
_INDEPENDENT_EXTERNAL_CLASSES = frozenset(
    {"independent_external", "authenticated_independent_external"}
)
_FINGERPRINT_RE = re.compile(r"[0-9a-f]{64}\Z")
CLAIM_IDENTITY_CANONICALIZATION = "sorted_compact_json_utf8_v1"
MAXIMUM_UNATTESTED_SCIENTIFIC_STATUS = ScientificStatus.ADJUDICATION_PENDING


def _enum_value(value: object) -> str:
    return str(value.value) if isinstance(value, Enum) else str(value)


def _nonempty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RemediationContractError(f"{field_name} must be a non-empty string")
    return value.strip()


def _exact_nonempty_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RemediationContractError(f"{field_name} must be a non-empty string")
    if value != value.strip():
        raise RemediationContractError(
            f"{field_name} must not contain leading or trailing whitespace"
        )
    return value


def _sha256_digest(value: object, field_name: str) -> str:
    digest = _exact_nonempty_text(value, field_name)
    if not _FINGERPRINT_RE.fullmatch(digest):
        raise RemediationContractError(
            f"{field_name} must be a lowercase SHA-256 hex digest"
        )
    return digest


def _authority_text(value: object, field_name: str) -> str:
    try:
        return _nonempty_text(value, field_name)
    except RemediationContractError as exc:
        raise AuthorityError(str(exc)) from exc


@dataclass(frozen=True, eq=False)
class ClaimLevel:
    """A claim level qualified by its versioned semantic scheme."""

    scheme: ClaimLevelScheme | str
    level: str

    def __post_init__(self) -> None:
        try:
            scheme = ClaimLevelScheme(_enum_value(self.scheme))
        except ValueError as exc:
            raise RemediationContractError(
                f"unknown claim-level scheme {self.scheme!r}"
            ) from exc
        level = _exact_nonempty_text(self.level, "ClaimLevel.level")
        if level not in _LEVELS_BY_SCHEME[scheme]:
            raise RemediationContractError(
                f"claim level {level!r} is invalid for scheme {scheme.value!r}"
            )
        object.__setattr__(self, "scheme", scheme)
        object.__setattr__(self, "level", level)

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "ClaimLevel":
        """Parse a scheme-qualified record; a bare ``C`` label is invalid."""

        if not isinstance(value, Mapping):
            raise RemediationContractError(
                "claim level must be a mapping with scheme and level"
            )
        missing = {"scheme", "level"} - set(value)
        if missing:
            raise RemediationContractError(
                f"claim level is missing required fields: {sorted(missing)}"
            )
        unknown = set(value) - {"scheme", "level"}
        if unknown:
            raise RemediationContractError(
                f"claim level has unknown fields: {sorted(unknown)}"
            )
        return cls(scheme=value["scheme"], level=str(value["level"]))

    def compare(self, other: "ClaimLevel") -> int:
        """Compare only within one scheme; automatic crosswalks are forbidden."""

        if not isinstance(other, ClaimLevel):
            raise TypeError("ClaimLevel.compare requires another ClaimLevel")
        if self.scheme is not other.scheme:
            raise RemediationContractError(
                "cross-scheme claim-level comparison is forbidden: "
                f"{self.scheme.value!r} versus {other.scheme.value!r}"
            )
        values = _LEVELS_BY_SCHEME[self.scheme]
        left = values.index(self.level)
        right = values.index(other.level)
        return (left > right) - (left < right)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClaimLevel):
            return NotImplemented
        if self.scheme is not other.scheme:
            raise RemediationContractError(
                "cross-scheme claim-level equality comparison is forbidden: "
                f"{self.scheme.value!r} versus {other.scheme.value!r}"
            )
        return self.level == other.level

    def __hash__(self) -> int:
        return hash((self.scheme, self.level))


def compare_claim_levels(left: ClaimLevel, right: ClaimLevel) -> int:
    """Explicit same-scheme comparison helper."""

    return left.compare(right)


_CLAIM_IDENTITY_SEMANTIC_FIELDS = (
    "claim_id",
    "claim_text",
    "quantifier",
    "estimand",
    "target_population",
    "domain",
    "frame",
    "perturbative_order",
    "units",
    "data_release",
    "sky_support_mask_selection",
    "statistic_pipeline",
    "transfer_source",
    "nuisance_prior_null_multiplicity",
    "claim_level_scheme",
    "claim_level",
    "claim_tier_ceiling",
)


@dataclass(frozen=True)
class ClaimIdentity:
    """Immutable semantic identity for one adjudicable claim."""

    claim_id: str
    claim_text: str
    quantifier: str
    estimand: str
    target_population: str
    domain: str
    frame: str
    perturbative_order: str
    units: str
    data_release: str
    sky_support_mask_selection: str
    statistic_pipeline: str
    transfer_source: str
    nuisance_prior_null_multiplicity: str
    claim_level_scheme: ClaimLevelScheme | str
    claim_level: str
    claim_tier_ceiling: CanonicalClaimTier | str
    canonicalization: str = CLAIM_IDENTITY_CANONICALIZATION

    def __post_init__(self) -> None:
        for field_name in _CLAIM_IDENTITY_SEMANTIC_FIELDS:
            value = getattr(self, field_name)
            if field_name in {"claim_level_scheme", "claim_tier_ceiling"}:
                continue
            object.__setattr__(
                self, field_name, _exact_nonempty_text(value, field_name)
            )

        claim_level = ClaimLevel(self.claim_level_scheme, self.claim_level)
        object.__setattr__(self, "claim_level_scheme", claim_level.scheme)
        object.__setattr__(self, "claim_level", claim_level.level)
        try:
            claim_tier = CanonicalClaimTier(_enum_value(self.claim_tier_ceiling))
        except ValueError as exc:
            raise RemediationContractError(
                f"unknown claim tier {self.claim_tier_ceiling!r}; tiers are unordered"
            ) from exc
        object.__setattr__(self, "claim_tier_ceiling", claim_tier)
        if self.canonicalization != CLAIM_IDENTITY_CANONICALIZATION:
            raise RemediationContractError(
                f"unsupported ClaimIdentity canonicalization {self.canonicalization!r}"
            )

    @classmethod
    def from_record(cls, value: Mapping[str, object]) -> "ClaimIdentity":
        """Build from a loaded record and verify a supplied fingerprint, if any."""

        if not isinstance(value, Mapping):
            raise RemediationContractError("ClaimIdentity record must be a mapping")
        allowed = set(_CLAIM_IDENTITY_SEMANTIC_FIELDS) | {
            "canonicalization",
            "identity_fingerprint",
        }
        unknown = set(value) - allowed
        if unknown:
            raise RemediationContractError(
                f"ClaimIdentity record has unknown fields: {sorted(unknown)}"
            )
        missing = set(_CLAIM_IDENTITY_SEMANTIC_FIELDS) - set(value)
        if missing:
            raise RemediationContractError(
                f"ClaimIdentity record is missing fields: {sorted(missing)}"
            )
        kwargs = {name: value[name] for name in _CLAIM_IDENTITY_SEMANTIC_FIELDS}
        kwargs["canonicalization"] = value.get(
            "canonicalization", CLAIM_IDENTITY_CANONICALIZATION
        )
        identity = cls(**kwargs)  # type: ignore[arg-type]
        expected = value.get("identity_fingerprint")
        if expected is not None:
            identity.verify_fingerprint(str(expected))
        return identity

    def semantic_payload(self) -> dict[str, str]:
        """Return exactly the fields covered by the identity fingerprint."""

        return {
            name: _enum_value(getattr(self, name))
            for name in _CLAIM_IDENTITY_SEMANTIC_FIELDS
        }

    def canonical_bytes(self) -> bytes:
        """Return sorted, compact UTF-8 JSON for deterministic hashing."""

        return json.dumps(
            self.semantic_payload(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    @property
    def identity_fingerprint(self) -> str:
        return hashlib.sha256(self.canonical_bytes()).hexdigest()

    def verify_fingerprint(self, expected: str) -> None:
        expected = _exact_nonempty_text(expected, "identity_fingerprint")
        if not _FINGERPRINT_RE.fullmatch(expected):
            raise RemediationContractError(
                "identity_fingerprint must be a lowercase SHA-256 hex digest"
            )
        if self.identity_fingerprint != expected:
            raise RemediationContractError(
                "ClaimIdentity fingerprint does not match its semantic payload"
            )

    def to_record(self) -> dict[str, str]:
        return {
            **self.semantic_payload(),
            "canonicalization": self.canonicalization,
            "identity_fingerprint": self.identity_fingerprint,
        }


def canonical_claim_identity_payload(
    identity: ClaimIdentity | Mapping[str, object],
) -> bytes:
    """Return canonical bytes, validating mappings before hashing."""

    parsed = (
        identity
        if isinstance(identity, ClaimIdentity)
        else ClaimIdentity.from_record(identity)
    )
    return parsed.canonical_bytes()


def claim_identity_fingerprint(
    identity: ClaimIdentity | Mapping[str, object],
) -> str:
    """Return the stable SHA-256 identity digest for a claim record."""

    return hashlib.sha256(canonical_claim_identity_payload(identity)).hexdigest()


class ClaimCapability(StrEnum):
    """Named scientific-use capability; never inferred from DAG completion."""

    CONTRACT_VALIDATED = "CONTRACT_VALIDATED"
    THEOREM_PROVED_EXACT = "THEOREM_PROVED_EXACT"
    THEOREM_PROVED_CONDITIONAL = "THEOREM_PROVED_CONDITIONAL"
    METHOD_CALIBRATED = "METHOD_CALIBRATED"
    DATA_ADMITTED = "DATA_ADMITTED"
    OBSERVED_DESCRIPTIVE = "OBSERVED_DESCRIPTIVE"
    OBSERVED_INFERENTIAL = "OBSERVED_INFERENTIAL"
    SOURCE_SEPARATION_CANDIDATE = "SOURCE_SEPARATION_CANDIDATE"
    MORPHOLOGY_COMPATIBILITY = "MORPHOLOGY_COMPATIBILITY"
    FAMILY_IDENTIFICATION = "FAMILY_IDENTIFICATION"
    PUBLIC_RELEASE = "PUBLIC_RELEASE"


class CapabilityAction(StrEnum):
    GRANT = "GRANT"
    HOLD = "HOLD"
    SUPERSEDE = "SUPERSEDE"
    REVOKE = "REVOKE"
    DOWNGRADE = "DOWNGRADE"


class CapabilityOutcome(StrEnum):
    PASS = "PASS"
    PASS_WITH_CEILING = "PASS_WITH_CEILING"
    ABSTAIN = "ABSTAIN"
    BLOCK = "BLOCK"
    STALE_REPLACED = "STALE_REPLACED"


class CapabilityBlockerKind(StrEnum):
    PHYSICAL_HARD = "PHYSICAL_HARD"
    EVIDENCE_CONDITIONAL = "EVIDENCE_CONDITIONAL"
    LEGACY_SUPERSESSION = "LEGACY_SUPERSESSION"
    INFRASTRUCTURE_DEBT = "INFRASTRUCTURE_DEBT"


class IdentityDimension(StrEnum):
    THEOREM = "THEOREM"
    DATA = "DATA"
    MASK = "MASK"
    COVARIANCE = "COVARIANCE"
    TRANSFER = "TRANSFER"
    ESTIMAND = "ESTIMAND"


class ArtifactReadinessAxis(StrEnum):
    EVIDENCE_CLOSED = "EVIDENCE_CLOSED"
    EVIDENCE_INCOMPLETE = "EVIDENCE_INCOMPLETE"
    EVIDENCE_BLOCKED = "EVIDENCE_BLOCKED"


class CapabilityEvidenceBranch(StrEnum):
    CONTRACT = "CONTRACT"
    THEOREM = "THEOREM"
    METHOD = "METHOD"
    DATA = "DATA"
    OBSERVATION = "OBSERVATION"
    SOURCE_SEPARATION = "SOURCE_SEPARATION"
    MORPHOLOGY = "MORPHOLOGY"
    FAMILY = "FAMILY"
    RELEASE = "RELEASE"


class CapabilityScientificSemantics(StrEnum):
    CONTRACT_ONLY = "CONTRACT_ONLY"
    EXACT_THEOREM = "EXACT_THEOREM"
    CONDITIONAL_THEOREM = "CONDITIONAL_THEOREM"
    CALIBRATED_METHOD = "CALIBRATED_METHOD"
    DATA_ADMISSION_ONLY = "DATA_ADMISSION_ONLY"
    OBSERVED_DESCRIPTION = "OBSERVED_DESCRIPTION"
    OBSERVED_INFERENCE = "OBSERVED_INFERENCE"
    SOURCE_SEPARATION_CANDIDATE = "SOURCE_SEPARATION_CANDIDATE"
    MORPHOLOGY_COMPATIBILITY = "MORPHOLOGY_COMPATIBILITY"
    FAMILY_IDENTIFICATION = "FAMILY_IDENTIFICATION"
    PUBLICATION = "PUBLICATION"


class CapabilityIdentification(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PARTIAL_IDENTIFICATION = "PARTIAL_IDENTIFICATION"
    COMPATIBILITY_ONLY = "COMPATIBILITY_ONLY"
    NATIVE_ATLAS_REQUIRED = "NATIVE_ATLAS_REQUIRED"


class CapabilityProvenanceGrade(StrEnum):
    CONTENT_ADDRESSED_ADJUDICATED = "CONTENT_ADDRESSED_ADJUDICATED"


NON_RELAXABLE_CAPABILITY_RULES = (
    "CONVERSE_BAN",
    "P36_T2P_RETRACTION",
    "REFUTED_MES_TRIPLES",
    "LEGACY_PROJECTION_BC1_BC2",
    "OWNER_ROLE_FIREWALLS",
    "NATIVE_FAMILY_GATE",
    "ORBIT_GENERIC_COMPLETENESS_UNPROVEN",
    "STATE_CONTENT_IDENTITY",
    "CAS_FIVE_STATE_NO_MAJORITY",
    "STRICT_PDF_LINT",
    "ANTI_LAUNDERING",
)


_VERSIONED_IDENTITY_FACTORY_TOKEN = object()


def _identity_components(
    values: Mapping[IdentityDimension | str, str],
) -> Mapping[IdentityDimension, str]:
    if not isinstance(values, Mapping):
        raise RemediationContractError("component_fingerprints must be a mapping")
    normalized: dict[IdentityDimension, str] = {}
    for raw_dimension, raw_digest in values.items():
        try:
            dimension = IdentityDimension(_enum_value(raw_dimension))
        except ValueError as exc:
            raise RemediationContractError(
                f"unknown identity dimension {raw_dimension!r}"
            ) from exc
        if dimension in normalized:
            raise RemediationContractError(
                f"duplicate identity dimension {dimension.value}"
            )
        normalized[dimension] = _sha256_digest(
            raw_digest, f"component_fingerprints.{dimension.value}"
        )
    missing = set(IdentityDimension) - set(normalized)
    if missing:
        raise RemediationContractError(
            "component_fingerprints must cover every identity dimension: "
            f"missing={sorted(item.value for item in missing)}"
        )
    return MappingProxyType(
        dict(sorted(normalized.items(), key=lambda item: item[0].value))
    )


@dataclass(frozen=True, init=False)
class VersionedClaimIdentity:
    """Immutable claim identity with explicit theorem/data/estimand components."""

    version: str
    owner: str
    claim_identity: ClaimIdentity
    component_fingerprints: Mapping[IdentityDimension, str]
    predecessor_ref: str | None
    changed_dimensions: tuple[IdentityDimension, ...]

    def __init__(
        self,
        *,
        _factory_token: object,
        version: str,
        owner: str,
        claim_identity: ClaimIdentity,
        component_fingerprints: Mapping[IdentityDimension | str, str],
        predecessor_ref: str | None,
        changed_dimensions: Sequence[IdentityDimension | str],
    ) -> None:
        if _factory_token is not _VERSIONED_IDENTITY_FACTORY_TOKEN:
            raise RemediationContractError(
                "VersionedClaimIdentity is factory-only; use root() or successor()"
            )
        if not isinstance(claim_identity, ClaimIdentity):
            raise RemediationContractError(
                "claim_identity must be a validated ClaimIdentity"
            )
        normalized_owner = _exact_nonempty_text(owner, "owner")
        if normalized_owner not in _ACTIVE_OWNERS:
            raise RemediationContractError(
                f"unknown active remediation owner {normalized_owner!r}"
            )
        components = _identity_components(component_fingerprints)
        changed: list[IdentityDimension] = []
        for value in changed_dimensions:
            try:
                dimension = IdentityDimension(_enum_value(value))
            except ValueError as exc:
                raise RemediationContractError(
                    f"unknown changed identity dimension {value!r}"
                ) from exc
            if dimension in changed:
                raise RemediationContractError(
                    f"duplicate changed identity dimension {dimension.value}"
                )
            changed.append(dimension)
        changed_tuple = tuple(sorted(changed, key=lambda item: item.value))
        if predecessor_ref is None:
            if changed_tuple:
                raise RemediationContractError(
                    "a root identity cannot declare changed_dimensions"
                )
        else:
            predecessor_ref = _sha256_digest(predecessor_ref, "predecessor_ref")
            if not changed_tuple:
                raise RemediationContractError(
                    "a successor identity requires changed_dimensions"
                )
        object.__setattr__(self, "version", _exact_nonempty_text(version, "version"))
        object.__setattr__(self, "owner", normalized_owner)
        object.__setattr__(self, "claim_identity", claim_identity)
        object.__setattr__(self, "component_fingerprints", components)
        object.__setattr__(self, "predecessor_ref", predecessor_ref)
        object.__setattr__(self, "changed_dimensions", changed_tuple)

    @classmethod
    def root(
        cls,
        *,
        version: str,
        owner: str,
        claim_identity: ClaimIdentity,
        component_fingerprints: Mapping[IdentityDimension | str, str],
    ) -> "VersionedClaimIdentity":
        return cls(
            _factory_token=_VERSIONED_IDENTITY_FACTORY_TOKEN,
            version=version,
            owner=owner,
            claim_identity=claim_identity,
            component_fingerprints=component_fingerprints,
            predecessor_ref=None,
            changed_dimensions=(),
        )

    @classmethod
    def successor(
        cls,
        predecessor: "VersionedClaimIdentity",
        *,
        version: str,
        claim_identity: ClaimIdentity,
        component_fingerprints: Mapping[IdentityDimension | str, str],
    ) -> "VersionedClaimIdentity":
        if not isinstance(predecessor, VersionedClaimIdentity):
            raise TypeError("predecessor must be a VersionedClaimIdentity")
        if not isinstance(claim_identity, ClaimIdentity):
            raise RemediationContractError(
                "claim_identity must be a validated ClaimIdentity"
            )
        if claim_identity.claim_id != predecessor.claim_identity.claim_id:
            raise RemediationContractError(
                "a changed claim_id requires a new root identity, not a successor"
            )
        normalized_version = _exact_nonempty_text(version, "version")
        if normalized_version == predecessor.version:
            raise RemediationContractError("a successor must change version")
        components = _identity_components(component_fingerprints)
        changed = tuple(
            dimension
            for dimension in IdentityDimension
            if components[dimension]
            != predecessor.component_fingerprints[dimension]
        )
        if not changed:
            if (
                claim_identity.identity_fingerprint
                != predecessor.claim_identity.identity_fingerprint
            ):
                raise RemediationContractError(
                    "a semantic claim change must alter a declared identity component"
                )
            raise RemediationContractError("a no-op successor is forbidden")
        return cls(
            _factory_token=_VERSIONED_IDENTITY_FACTORY_TOKEN,
            version=normalized_version,
            owner=predecessor.owner,
            claim_identity=claim_identity,
            component_fingerprints=components,
            predecessor_ref=predecessor.identity_ref,
            changed_dimensions=changed,
        )

    def payload(self) -> dict[str, object]:
        return {
            "schema_version": "versioned_claim_identity_v1",
            "version": self.version,
            "owner": self.owner,
            "claim_identity": self.claim_identity.to_record(),
            "component_fingerprints": {
                dimension.value: digest
                for dimension, digest in self.component_fingerprints.items()
            },
            "predecessor_ref": self.predecessor_ref,
            "changed_dimensions": [item.value for item in self.changed_dimensions],
        }

    @property
    def identity_ref(self) -> str:
        return hashlib.sha256(
            json.dumps(
                self.payload(),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()

    def to_record(self) -> dict[str, object]:
        return {**self.payload(), "identity_ref": self.identity_ref}


@dataclass(frozen=True)
class CapabilityBlocker:
    """One typed blocker whose scope is an explicit capability subset."""

    blocker_id: str
    kind: CapabilityBlockerKind | str
    affected_capabilities: Sequence[ClaimCapability | str]
    evidence_ref: str

    def __post_init__(self) -> None:
        blocker_id = _exact_nonempty_text(self.blocker_id, "blocker_id")
        try:
            kind = CapabilityBlockerKind(_enum_value(self.kind))
        except ValueError as exc:
            raise RemediationContractError(
                f"unknown capability blocker kind {self.kind!r}"
            ) from exc
        if isinstance(self.affected_capabilities, (str, bytes)) or not isinstance(
            self.affected_capabilities, Sequence
        ):
            raise RemediationContractError(
                "affected_capabilities must be a sequence"
            )
        try:
            capabilities = tuple(
                sorted(
                    {
                        ClaimCapability(_enum_value(value))
                        for value in self.affected_capabilities
                    },
                    key=lambda item: item.value,
                )
            )
        except ValueError as exc:
            raise RemediationContractError(
                "affected_capabilities contains an unknown capability"
            ) from exc
        if not capabilities or len(capabilities) != len(self.affected_capabilities):
            raise RemediationContractError(
                "affected_capabilities must be non-empty and unique"
            )
        object.__setattr__(self, "blocker_id", blocker_id)
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "affected_capabilities", capabilities)
        object.__setattr__(
            self, "evidence_ref", _sha256_digest(self.evidence_ref, "evidence_ref")
        )

    def to_record(self) -> dict[str, object]:
        return {
            "blocker_id": self.blocker_id,
            "kind": self.kind.value,
            "affected_capabilities": [
                item.value for item in self.affected_capabilities
            ],
            "evidence_ref": self.evidence_ref,
        }


_ALLOWED_OUTCOMES_BY_ACTION: Mapping[
    CapabilityAction, frozenset[CapabilityOutcome]
] = MappingProxyType(
    {
        CapabilityAction.GRANT: frozenset(
            {CapabilityOutcome.PASS, CapabilityOutcome.PASS_WITH_CEILING}
        ),
        CapabilityAction.HOLD: frozenset(
            {CapabilityOutcome.ABSTAIN, CapabilityOutcome.BLOCK}
        ),
        CapabilityAction.SUPERSEDE: frozenset(
            {CapabilityOutcome.PASS, CapabilityOutcome.PASS_WITH_CEILING}
        ),
        CapabilityAction.REVOKE: frozenset(
            {CapabilityOutcome.BLOCK, CapabilityOutcome.STALE_REPLACED}
        ),
        CapabilityAction.DOWNGRADE: frozenset(
            {
                CapabilityOutcome.PASS_WITH_CEILING,
                CapabilityOutcome.ABSTAIN,
                CapabilityOutcome.BLOCK,
            }
        ),
    }
)


def _parse_datetime(value: datetime | date | str, field_name: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min, tzinfo=UTC)
    elif isinstance(value, str) and value.strip():
        raw = value.strip()
        if raw.endswith("Z"):
            raw = f"{raw[:-1]}+00:00"
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as exc:
            raise AuthorityError(f"{field_name} must be an ISO-8601 datetime") from exc
    else:
        raise AuthorityError(f"{field_name} must be an ISO-8601 datetime")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _normalized_unique_texts(
    values: Sequence[str], field_name: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise AuthorityError(f"{field_name} must be a sequence of strings")
    normalized = tuple(_authority_text(value, field_name) for value in values)
    if not allow_empty and not normalized:
        raise AuthorityError(f"{field_name} must not be empty")
    if len(normalized) != len(set(normalized)):
        raise AuthorityError(f"{field_name} contains duplicate values")
    return normalized


@dataclass(frozen=True)
class PrincipalRecord:
    """One bounded, verifiable, default-deny authority record."""

    principal_id: str
    identity_fingerprint: str
    aliases: Sequence[str]
    allowed_roles: Sequence[str]
    allowed_scopes: Sequence[str]
    independence_class: str
    valid_from: datetime | date | str
    valid_until: datetime | date | str
    revoked: bool
    verifier: str

    def __post_init__(self) -> None:
        principal_id = _authority_text(self.principal_id, "principal_id")
        fingerprint = _authority_text(self.identity_fingerprint, "identity_fingerprint")
        if not _FINGERPRINT_RE.fullmatch(fingerprint):
            raise AuthorityError(
                "principal identity_fingerprint must be a lowercase SHA-256 digest"
            )
        aliases = _normalized_unique_texts(self.aliases, "aliases", allow_empty=True)
        if principal_id in aliases:
            raise AuthorityError("aliases must not repeat principal_id")
        roles = _normalized_unique_texts(self.allowed_roles, "allowed_roles")
        scopes = _normalized_unique_texts(self.allowed_scopes, "allowed_scopes")
        independence_class = _authority_text(
            self.independence_class, "independence_class"
        )
        verifier = _authority_text(self.verifier, "verifier")
        if type(self.revoked) is not bool:
            raise AuthorityError("revoked must be a boolean")
        valid_from = _parse_datetime(self.valid_from, "valid_from")
        valid_until = _parse_datetime(self.valid_until, "valid_until")
        if valid_until <= valid_from:
            raise AuthorityError("valid_until must be later than valid_from")
        object.__setattr__(self, "principal_id", principal_id)
        object.__setattr__(self, "identity_fingerprint", fingerprint)
        object.__setattr__(self, "aliases", aliases)
        object.__setattr__(self, "allowed_roles", roles)
        object.__setattr__(self, "allowed_scopes", scopes)
        object.__setattr__(self, "independence_class", independence_class)
        object.__setattr__(self, "valid_from", valid_from)
        object.__setattr__(self, "valid_until", valid_until)
        object.__setattr__(self, "verifier", verifier)

    def validate_use(
        self,
        *,
        role: str,
        scope: str,
        at: datetime | date | str | None = None,
        identity_fingerprint: str | None = None,
    ) -> None:
        """Validate exact role/scope and the bounded attestation window."""

        role = _authority_text(role, "role")
        scope = _authority_text(scope, "scope")
        when = datetime.now(UTC) if at is None else _parse_datetime(at, "at")
        if self.revoked:
            raise AuthorityError(f"principal {self.principal_id!r} is revoked")
        if when < self.valid_from:
            raise AuthorityError(f"principal {self.principal_id!r} is not yet valid")
        if when >= self.valid_until:
            raise AuthorityError(f"principal {self.principal_id!r} is expired")
        if role not in self.allowed_roles:
            raise AuthorityError(
                f"principal {self.principal_id!r} is not allowed role {role!r}"
            )
        if scope not in self.allowed_scopes:
            raise AuthorityError(
                f"principal {self.principal_id!r} is not allowed scope {scope!r}"
            )
        if identity_fingerprint is not None:
            candidate = _authority_text(identity_fingerprint, "identity_fingerprint")
            if candidate != self.identity_fingerprint:
                raise AuthorityError(
                    f"principal {self.principal_id!r} fingerprint mismatch"
                )


class AuthorityRegistry:
    """Alias-aware principal registry with exact, default-deny authorization."""

    default_deny = True

    def __init__(
        self,
        principals: Sequence[PrincipalRecord] = (),
        *,
        verifiers: (
            Mapping[str, Callable[[PrincipalRecord, bytes, str], bool]] | None
        ) = None,
    ) -> None:
        if isinstance(principals, (str, bytes)) or not isinstance(principals, Sequence):
            raise TypeError("principals must be a sequence of PrincipalRecord")
        self._principals: dict[str, PrincipalRecord] = {}
        self._identifiers: dict[str, str] = {}
        self._fingerprints: dict[str, str] = {}
        if verifiers is not None and not isinstance(verifiers, Mapping):
            raise TypeError("verifiers must be a mapping of verifier callbacks")
        self._verifiers = dict(verifiers or {})
        if not all(
            isinstance(name, str) and name and callable(verifier)
            for name, verifier in self._verifiers.items()
        ):
            raise AuthorityError("verifiers must have non-empty names and callables")
        for principal in principals:
            self.register(principal)

    def register(self, principal: PrincipalRecord) -> PrincipalRecord:
        if not isinstance(principal, PrincipalRecord):
            raise TypeError("AuthorityRegistry requires PrincipalRecord values")
        identifiers = (principal.principal_id, *principal.aliases)
        collisions = [value for value in identifiers if value in self._identifiers]
        if collisions:
            raise AuthorityError(
                f"principal identifier collision: {sorted(collisions)!r}"
            )
        if principal.principal_id in self._principals:
            raise AuthorityError(f"duplicate principal_id {principal.principal_id!r}")
        fingerprint_owner = self._fingerprints.get(principal.identity_fingerprint)
        if fingerprint_owner is not None:
            raise AuthorityError(
                "principal identity_fingerprint collision between "
                f"{fingerprint_owner!r} and {principal.principal_id!r}"
            )
        self._principals[principal.principal_id] = principal
        self._fingerprints[principal.identity_fingerprint] = principal.principal_id
        for identifier in identifiers:
            self._identifiers[identifier] = principal.principal_id
        return principal

    def resolve(
        self,
        identifier: str,
        *,
        role: str,
        scope: str,
        at: datetime | date | str | None = None,
        identity_fingerprint: str | None = None,
    ) -> PrincipalRecord:
        """Resolve an ID or alias and validate its exact authorized use."""

        identifier = _authority_text(identifier, "principal identifier")
        canonical_id = self._identifiers.get(identifier)
        if canonical_id is None:
            raise AuthorityError(f"unknown principal or alias {identifier!r}")
        principal = self._principals[canonical_id]
        principal.validate_use(
            role=role,
            scope=scope,
            at=at,
            identity_fingerprint=identity_fingerprint,
        )
        return principal

    def all(self) -> tuple[PrincipalRecord, ...]:
        return tuple(self._principals.values())

    def verifier_bindings(
        self,
    ) -> Mapping[str, Callable[[PrincipalRecord, bytes, str], bool]]:
        """Return a read-only snapshot of the configured verifier callbacks.

        Callers which content-address an authority registry must bind the
        implementation of each trusted verifier, not merely the verifier name
        carried by a principal record.  A copy prevents callers from mutating
        the registry through this inspection surface.
        """

        return MappingProxyType(dict(self._verifiers))

    def verify_attestation(
        self,
        principal: PrincipalRecord,
        *,
        payload: bytes,
        attestation: str,
    ) -> None:
        """Verify receipt bytes through the principal's trusted verifier."""

        if not isinstance(principal, PrincipalRecord):
            raise TypeError("principal must be a PrincipalRecord")
        if not isinstance(payload, bytes) or not payload:
            raise AuthorityError("attestation payload must be non-empty bytes")
        attestation = _exact_nonempty_text(attestation, "attestation")
        verifier = self._verifiers.get(principal.verifier)
        if verifier is None:
            raise AuthorityError(
                f"no trusted verifier is registered for {principal.verifier!r}"
            )
        try:
            verified = verifier(principal, payload, attestation)
        except Exception as exc:
            raise AuthorityError("receipt attestation verifier failed") from exc
        if type(verified) is not bool or not verified:
            raise AuthorityError("receipt attestation verification failed")


def _require_independent_external(principal: PrincipalRecord, *, use: str) -> None:
    if principal.independence_class not in _INDEPENDENT_EXTERNAL_CLASSES:
        raise AuthorityError(
            f"{use} requires an independently authenticated external principal; "
            f"got independence_class {principal.independence_class!r}"
        )


def require_independent_external_principal(
    principal: PrincipalRecord, *, use: str
) -> None:
    """Public fail-closed guard for independently authenticated principals."""

    if not isinstance(principal, PrincipalRecord):
        raise TypeError("principal must be a PrincipalRecord")
    _require_independent_external(principal, use=_exact_nonempty_text(use, "use"))


def assert_distinct_author_adjudicator(
    registry: AuthorityRegistry,
    *,
    author: str,
    adjudicator: str,
    scope: str,
    at: datetime | date | str | None = None,
) -> tuple[PrincipalRecord, PrincipalRecord]:
    """Require distinct canonical identities after resolving aliases."""

    if not isinstance(registry, AuthorityRegistry):
        raise TypeError("registry must be an AuthorityRegistry")
    author_record = registry.resolve(author, role="author", scope=scope, at=at)
    adjudicator_record = registry.resolve(
        adjudicator, role="adjudicator", scope=scope, at=at
    )
    if (
        author_record.principal_id == adjudicator_record.principal_id
        or author_record.identity_fingerprint == adjudicator_record.identity_fingerprint
    ):
        raise AuthorityError(
            "author and adjudicator must have distinct canonical identities"
        )
    return author_record, adjudicator_record


@dataclass(frozen=True)
class AdjudicatedClaim:
    """One identity-bound claim outcome in an authorized adjudication receipt."""

    claim_id: str
    identity_fingerprint: str
    scientific_status: ScientificStatus | str

    def __post_init__(self) -> None:
        claim_id = _exact_nonempty_text(self.claim_id, "claim_id")
        fingerprint = _sha256_digest(
            self.identity_fingerprint, "claim identity_fingerprint"
        )
        try:
            status = ScientificStatus(_enum_value(self.scientific_status))
        except ValueError as exc:
            raise RemediationContractError(
                f"unknown adjudicated scientific status {self.scientific_status!r}"
            ) from exc
        if status not in _ADJUDICATED_SCIENTIFIC_STATUSES:
            raise RemediationContractError(
                "AdjudicatedClaim requires a terminal adjudicated scientific status"
            )
        object.__setattr__(self, "claim_id", claim_id)
        object.__setattr__(self, "identity_fingerprint", fingerprint)
        object.__setattr__(self, "scientific_status", status)


def _receipt_time_not_in_future(
    issued_at: datetime,
    evaluated_at: datetime | date | str | None,
) -> datetime:
    evaluation = (
        datetime.now(UTC)
        if evaluated_at is None
        else _parse_datetime(evaluated_at, "at")
    )
    if issued_at > evaluation:
        raise AuthorityError("receipt issued_at cannot be in the future")
    return evaluation


@dataclass(frozen=True)
class ExternalDeliveryReceipt:
    """Identity-bound receipt for a delivered external artifact.

    Authentication is established only when :meth:`validate` resolves the
    provider through the trusted authority registry with the exact external
    provider role, scope, identity fingerprint, and issuance time.
    """

    receipt_id: str
    provider: str
    provider_identity_fingerprint: str
    scope: str
    artifact_fingerprint: str
    issued_at: datetime | date | str
    attestation: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "receipt_id", _exact_nonempty_text(self.receipt_id, "receipt_id")
        )
        object.__setattr__(self, "provider", _authority_text(self.provider, "provider"))
        object.__setattr__(
            self,
            "provider_identity_fingerprint",
            _sha256_digest(
                self.provider_identity_fingerprint,
                "provider_identity_fingerprint",
            ),
        )
        object.__setattr__(self, "scope", _authority_text(self.scope, "scope"))
        object.__setattr__(
            self,
            "artifact_fingerprint",
            _sha256_digest(self.artifact_fingerprint, "artifact_fingerprint"),
        )
        object.__setattr__(
            self, "issued_at", _parse_datetime(self.issued_at, "issued_at")
        )
        object.__setattr__(
            self, "attestation", _exact_nonempty_text(self.attestation, "attestation")
        )

    def canonical_attestation_payload(self) -> bytes:
        payload = {
            "artifact_fingerprint": self.artifact_fingerprint,
            "issued_at": self.issued_at.isoformat(),
            "provider": self.provider,
            "provider_identity_fingerprint": self.provider_identity_fingerprint,
            "receipt_id": self.receipt_id,
            "receipt_type": "external_delivery_receipt_v1",
            "scope": self.scope,
        }
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    def validate(
        self,
        registry: AuthorityRegistry,
        *,
        expected_scope: str,
        at: datetime | date | str | None = None,
    ) -> PrincipalRecord:
        if not isinstance(registry, AuthorityRegistry):
            raise TypeError("registry must be an AuthorityRegistry")
        expected_scope = _authority_text(expected_scope, "expected_scope")
        if self.scope != expected_scope:
            raise AuthorityError(
                f"external receipt scope {self.scope!r} does not match "
                f"dependency scope {expected_scope!r}"
            )
        _receipt_time_not_in_future(self.issued_at, at)
        provider_record = registry.resolve(
            self.provider,
            role="external_receipt_provider",
            scope=self.scope,
            at=self.issued_at,
            identity_fingerprint=self.provider_identity_fingerprint,
        )
        _require_independent_external(provider_record, use="external delivery receipt")
        registry.verify_attestation(
            provider_record,
            payload=self.canonical_attestation_payload(),
            attestation=self.attestation,
        )
        return provider_record


@dataclass(frozen=True)
class AdjudicationReceipt:
    """Canonical-identity-bound non-author adjudication receipt."""

    receipt_id: str
    author: str
    author_identity_fingerprint: str
    adjudicator: str
    adjudicator_identity_fingerprint: str
    scope: str
    accepted_claims: Sequence[AdjudicatedClaim]
    issued_at: datetime | date | str
    attestation: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "receipt_id", _exact_nonempty_text(self.receipt_id, "receipt_id")
        )
        object.__setattr__(self, "author", _authority_text(self.author, "author"))
        object.__setattr__(
            self,
            "author_identity_fingerprint",
            _sha256_digest(
                self.author_identity_fingerprint,
                "author_identity_fingerprint",
            ),
        )
        object.__setattr__(
            self,
            "adjudicator",
            _authority_text(self.adjudicator, "adjudicator"),
        )
        object.__setattr__(
            self,
            "adjudicator_identity_fingerprint",
            _sha256_digest(
                self.adjudicator_identity_fingerprint,
                "adjudicator_identity_fingerprint",
            ),
        )
        object.__setattr__(self, "scope", _authority_text(self.scope, "scope"))
        if isinstance(self.accepted_claims, (str, bytes)) or not isinstance(
            self.accepted_claims, Sequence
        ):
            raise RemediationContractError(
                "accepted_claims must be a sequence of AdjudicatedClaim"
            )
        raw_claims = tuple(self.accepted_claims)
        if not all(isinstance(claim, AdjudicatedClaim) for claim in raw_claims):
            raise RemediationContractError(
                "accepted_claims must contain only AdjudicatedClaim values"
            )
        claims = tuple(sorted(raw_claims, key=lambda claim: claim.claim_id))
        claim_ids = tuple(claim.claim_id for claim in claims)
        claim_fingerprints = tuple(claim.identity_fingerprint for claim in claims)
        if len(claim_ids) != len(set(claim_ids)):
            raise RemediationContractError(
                "accepted_claims contains duplicate claim_id values"
            )
        if len(claim_fingerprints) != len(set(claim_fingerprints)):
            raise RemediationContractError(
                "accepted_claims contains duplicate identity_fingerprint values"
            )
        object.__setattr__(self, "accepted_claims", claims)
        object.__setattr__(
            self, "issued_at", _parse_datetime(self.issued_at, "issued_at")
        )
        object.__setattr__(
            self, "attestation", _exact_nonempty_text(self.attestation, "attestation")
        )

    def canonical_attestation_payload(self) -> bytes:
        payload = {
            "accepted_claims": [
                {
                    "claim_id": claim.claim_id,
                    "identity_fingerprint": claim.identity_fingerprint,
                    "scientific_status": claim.scientific_status.value,
                }
                for claim in self.accepted_claims
            ],
            "adjudicator": self.adjudicator,
            "adjudicator_identity_fingerprint": (self.adjudicator_identity_fingerprint),
            "author": self.author,
            "author_identity_fingerprint": self.author_identity_fingerprint,
            "issued_at": self.issued_at.isoformat(),
            "receipt_id": self.receipt_id,
            "receipt_type": "adjudication_receipt_v1",
            "scope": self.scope,
        }
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    def validate(
        self,
        registry: AuthorityRegistry,
        *,
        expected_scope: str,
        at: datetime | date | str | None = None,
    ) -> tuple[PrincipalRecord, PrincipalRecord]:
        if not isinstance(registry, AuthorityRegistry):
            raise TypeError("registry must be an AuthorityRegistry")
        expected_scope = _authority_text(expected_scope, "expected_scope")
        if self.scope != expected_scope:
            raise AuthorityError(
                f"adjudication scope {self.scope!r} does not match "
                f"dependency scope {expected_scope!r}"
            )
        _receipt_time_not_in_future(self.issued_at, at)
        author_record = registry.resolve(
            self.author,
            role="author",
            scope=self.scope,
            at=self.issued_at,
            identity_fingerprint=self.author_identity_fingerprint,
        )
        adjudicator_record = registry.resolve(
            self.adjudicator,
            role="adjudicator",
            scope=self.scope,
            at=self.issued_at,
            identity_fingerprint=self.adjudicator_identity_fingerprint,
        )
        if (
            author_record.principal_id == adjudicator_record.principal_id
            or author_record.identity_fingerprint
            == adjudicator_record.identity_fingerprint
        ):
            raise AuthorityError(
                "author and adjudicator must have distinct canonical identities"
            )
        registry.verify_attestation(
            adjudicator_record,
            payload=self.canonical_attestation_payload(),
            attestation=self.attestation,
        )
        return author_record, adjudicator_record


def validate_active_owner(owner: object) -> str:
    """Return an allowed active owner and reject legacy/quarantined aliases."""

    normalized = _exact_nonempty_text(_enum_value(owner), "owner")
    if normalized.upper() in _FORBIDDEN_ACTIVE_OWNERS:
        raise RemediationContractError(
            f"{normalized} is forbidden as an active remediation owner"
        )
    if normalized not in _ACTIVE_OWNERS:
        raise RemediationContractError(
            f"unknown active remediation owner {normalized!r}"
        )
    return normalized


def _normalized_state_axes(
    orchestration_state: OrchestrationState | str,
    scientific_status: ScientificStatus | str,
    execution_resolution: ExecutionResolution | str | None,
) -> tuple[OrchestrationState, ScientificStatus, ExecutionResolution | None]:
    try:
        orchestration = OrchestrationState(_enum_value(orchestration_state))
    except ValueError as exc:
        raise RemediationContractError(
            f"unknown orchestration state {orchestration_state!r}"
        ) from exc
    try:
        scientific = ScientificStatus(_enum_value(scientific_status))
    except ValueError as exc:
        raise RemediationContractError(
            f"unknown scientific status {scientific_status!r}"
        ) from exc
    resolution: ExecutionResolution | None
    if execution_resolution is None:
        resolution = None
    else:
        try:
            resolution = ExecutionResolution(_enum_value(execution_resolution))
        except ValueError as exc:
            raise RemediationContractError(
                f"unknown execution resolution {execution_resolution!r}"
            ) from exc
    if orchestration is OrchestrationState.TERMINAL and resolution is None:
        raise RemediationContractError(
            "TERMINAL orchestration state requires an execution resolution"
        )
    if orchestration is not OrchestrationState.TERMINAL and resolution is not None:
        raise RemediationContractError(
            "execution resolution is allowed only for TERMINAL orchestration state"
        )
    return orchestration, scientific, resolution


@dataclass(frozen=True, init=False)
class RemediationState:
    """Orthogonal workflow, execution, and scientific state tuple."""

    orchestration_state: OrchestrationState | str
    scientific_status: ScientificStatus | str = ScientificStatus.OPEN
    execution_resolution: ExecutionResolution | str | None = None

    def __init__(
        self,
        orchestration_state: OrchestrationState | str,
        scientific_status: ScientificStatus | str = ScientificStatus.OPEN,
        execution_resolution: ExecutionResolution | str | None = None,
    ) -> None:
        orchestration, scientific, resolution = _normalized_state_axes(
            orchestration_state, scientific_status, execution_resolution
        )
        if scientific is not ScientificStatus.OPEN:
            raise RemediationContractError(
                "direct RemediationState construction is initial OPEN state only; "
                "use validated scientific transitions"
            )
        object.__setattr__(self, "orchestration_state", orchestration)
        object.__setattr__(self, "scientific_status", scientific)
        object.__setattr__(self, "execution_resolution", resolution)

    def resolve_execution(
        self,
        resolution: ExecutionResolution | str,
        *,
        registry: AuthorityRegistry | None = None,
        external_receipt: ExternalDeliveryReceipt | None = None,
        scope: str | None = None,
        at: datetime | date | str | None = None,
    ) -> "RemediationState":
        """Terminate execution without changing the scientific-status axis."""

        if self.orchestration_state is OrchestrationState.TERMINAL:
            raise RemediationContractError("execution is already terminal")
        try:
            parsed_resolution = ExecutionResolution(_enum_value(resolution))
        except ValueError as exc:
            raise RemediationContractError(
                f"unknown execution resolution {resolution!r}"
            ) from exc
        if (
            self.orchestration_state is OrchestrationState.DORMANT_EXTERNAL
            and parsed_resolution is ExecutionResolution.COMPLETED_SUCCESS
        ):
            if (
                registry is None
                or not isinstance(external_receipt, ExternalDeliveryReceipt)
                or scope is None
            ):
                raise AuthorityError(
                    "DORMANT_EXTERNAL success requires an authenticated external "
                    "receipt, registry, and exact scope"
                )
            external_receipt.validate(registry, expected_scope=scope, at=at)
        return _build_validated_state(
            OrchestrationState.TERMINAL,
            self.scientific_status,
            parsed_resolution,
        )

    def transition_scientific(
        self,
        target: ScientificStatus | str,
        *,
        registry: AuthorityRegistry | None = None,
        attestation: AdjudicationReceipt | None = None,
        claim_id: str | None = None,
        claim_identity_fingerprint: str | None = None,
        scope: str | None = None,
        at: datetime | date | str | None = None,
    ) -> "RemediationState":
        """Transition science explicitly; execution state is never consulted."""

        validated = validate_scientific_transition(
            self.scientific_status,
            target,
            registry=registry,
            attestation=attestation,
            claim_id=claim_id,
            claim_identity_fingerprint=claim_identity_fingerprint,
            scope=scope,
            at=at,
        )
        return _build_validated_state(
            self.orchestration_state,
            validated,
            self.execution_resolution,
        )


def _build_validated_state(
    orchestration_state: OrchestrationState | str,
    scientific_status: ScientificStatus | str,
    execution_resolution: ExecutionResolution | str | None,
) -> RemediationState:
    """Internal constructor reached only after contract validation."""

    orchestration, scientific, resolution = _normalized_state_axes(
        orchestration_state, scientific_status, execution_resolution
    )
    value = object.__new__(RemediationState)
    object.__setattr__(value, "orchestration_state", orchestration)
    object.__setattr__(value, "scientific_status", scientific)
    object.__setattr__(value, "execution_resolution", resolution)
    return value


def validate_scientific_transition(
    current: ScientificStatus | str,
    target: ScientificStatus | str,
    *,
    registry: AuthorityRegistry | None = None,
    attestation: AdjudicationReceipt | None = None,
    claim_id: str | None = None,
    claim_identity_fingerprint: str | None = None,
    scope: str | None = None,
    at: datetime | date | str | None = None,
) -> ScientificStatus:
    """Validate an explicit scientific transition under the PR-119 ceiling.

    States through ``ADJUDICATION_PENDING`` can be recorded as workflow-local
    evidence preparation.  Any adjudicated status requires a verifiable
    attestation, canonical author/adjudicator inequality, and an explicitly
    registered ``scientific_status_promoter`` role.  Therefore a bootstrap
    registry with no promotion principal cannot exceed the approved ceiling.
    """

    try:
        current_status = ScientificStatus(_enum_value(current))
        target_status = ScientificStatus(_enum_value(target))
    except ValueError as exc:
        raise RemediationContractError("unknown scientific status") from exc
    if current_status is target_status:
        return target_status
    if current_status in _ADJUDICATED_SCIENTIFIC_STATUSES:
        raise RemediationContractError(
            "adjudicated scientific statuses are immutable in this contract"
        )
    if target_status not in _SCIENTIFIC_TRANSITIONS[current_status]:
        raise RemediationContractError(
            "scientific transition must follow OPEN -> IN_REMEDIATION -> "
            "EVIDENCE_READY -> ADJUDICATION_PENDING -> adjudicated status; "
            f"got {current_status.value} -> {target_status.value}"
        )
    if target_status not in _ADJUDICATED_SCIENTIFIC_STATUSES:
        return target_status
    if not isinstance(attestation, AdjudicationReceipt):
        raise AuthorityError(
            "scientific status above ADJUDICATION_PENDING requires a "
            "typed verifiable adjudication attestation"
        )
    if (
        registry is None
        or claim_id is None
        or claim_identity_fingerprint is None
        or scope is None
    ):
        raise AuthorityError(
            "scientific adjudication requires registry, scope, claim_id, and "
            "claim identity fingerprint"
        )
    expected_claim_id = _exact_nonempty_text(claim_id, "claim_id")
    expected_fingerprint = _sha256_digest(
        claim_identity_fingerprint, "claim_identity_fingerprint"
    )
    _, adjudicator_record = attestation.validate(registry, expected_scope=scope, at=at)
    matching_claims = tuple(
        claim
        for claim in attestation.accepted_claims
        if claim.claim_id == expected_claim_id
        and claim.identity_fingerprint == expected_fingerprint
        and claim.scientific_status is target_status
    )
    if len(matching_claims) != 1:
        raise AuthorityError(
            "adjudication attestation is not bound to the requested claim identity "
            "and target scientific status"
        )
    promotion_record = registry.resolve(
        adjudicator_record.principal_id,
        role="scientific_status_promoter",
        scope=attestation.scope,
        at=attestation.issued_at,
        identity_fingerprint=attestation.adjudicator_identity_fingerprint,
    )
    _require_independent_external(promotion_record, use="scientific status promotion")
    return target_status


@dataclass(frozen=True)
class DependencyEvidence:
    """Typed evidence presented to one dependency edge."""

    execution_resolution: ExecutionResolution | str | None = None
    external_receipt: ExternalDeliveryReceipt | None = None
    adjudication_receipt: AdjudicationReceipt | None = None

    def __post_init__(self) -> None:
        if self.execution_resolution is None:
            resolution = None
        else:
            try:
                resolution = ExecutionResolution(_enum_value(self.execution_resolution))
            except ValueError as exc:
                raise RemediationContractError(
                    f"unknown execution resolution {self.execution_resolution!r}"
                ) from exc
        if self.external_receipt is not None and not isinstance(
            self.external_receipt, ExternalDeliveryReceipt
        ):
            raise RemediationContractError(
                "external_receipt must be an ExternalDeliveryReceipt"
            )
        if self.adjudication_receipt is not None and not isinstance(
            self.adjudication_receipt, AdjudicationReceipt
        ):
            raise RemediationContractError(
                "adjudication_receipt must be an AdjudicationReceipt"
            )
        object.__setattr__(self, "execution_resolution", resolution)


@dataclass(frozen=True)
class DependencyDecision:
    """Fail-closed result of resolving one typed dependency edge."""

    mode: DependencyMode
    satisfied: bool
    scientific_input_allowed: bool
    allowed_use: str
    accepted_claims: tuple[AdjudicatedClaim, ...] = ()
    missing_state: OrchestrationState | None = None

    @property
    def accepted_claim_ids(self) -> tuple[str, ...]:
        return tuple(claim.claim_id for claim in self.accepted_claims)


def resolve_dependency(
    mode: DependencyMode | str,
    evidence: DependencyEvidence,
    *,
    registry: AuthorityRegistry | None = None,
    scope: str | None = None,
    at: datetime | date | str | None = None,
) -> DependencyDecision:
    """Resolve one typed dependency without inferring scientific success."""

    try:
        parsed_mode = DependencyMode(_enum_value(mode))
    except ValueError as exc:
        raise RemediationContractError(f"unknown dependency mode {mode!r}") from exc
    if not isinstance(evidence, DependencyEvidence):
        raise TypeError("evidence must be DependencyEvidence")

    if parsed_mode is DependencyMode.REQUIRES_SUCCESS:
        satisfied = (
            evidence.execution_resolution is ExecutionResolution.COMPLETED_SUCCESS
        )
        return DependencyDecision(
            mode=parsed_mode,
            satisfied=satisfied,
            scientific_input_allowed=False,
            allowed_use="orchestration_only",
        )

    if parsed_mode is DependencyMode.REQUIRES_TERMINAL_RECEIPT:
        satisfied = evidence.execution_resolution in _TERMINAL_EXECUTION_RESOLUTIONS
        return DependencyDecision(
            mode=parsed_mode,
            satisfied=satisfied,
            scientific_input_allowed=False,
            allowed_use="adjudication_aggregation_only",
        )

    if parsed_mode is DependencyMode.REQUIRES_AUTHENTICATED_EXTERNAL_RECEIPT:
        receipt = evidence.external_receipt
        if receipt is None:
            return DependencyDecision(
                mode=parsed_mode,
                satisfied=False,
                scientific_input_allowed=False,
                allowed_use="external_delivery_intake_only",
                missing_state=OrchestrationState.DORMANT_EXTERNAL,
            )
        if registry is None or scope is None:
            raise AuthorityError(
                "external receipt resolution requires a registry and exact scope"
            )
        receipt.validate(registry, expected_scope=scope, at=at)
        return DependencyDecision(
            mode=parsed_mode,
            satisfied=True,
            scientific_input_allowed=False,
            allowed_use="external_delivery_intake_only",
        )

    receipt = evidence.adjudication_receipt
    if receipt is None:
        return DependencyDecision(
            mode=parsed_mode,
            satisfied=False,
            scientific_input_allowed=False,
            allowed_use="accepted_claim_subset_only",
        )
    if registry is None or scope is None:
        raise AuthorityError(
            "adjudicated claim-set resolution requires a registry and exact scope"
        )
    _, adjudicator_record = receipt.validate(registry, expected_scope=scope, at=at)
    accepted = tuple(receipt.accepted_claims)
    if accepted:
        promotion_record = registry.resolve(
            adjudicator_record.principal_id,
            role="scientific_status_promoter",
            scope=receipt.scope,
            at=receipt.issued_at,
            identity_fingerprint=receipt.adjudicator_identity_fingerprint,
        )
        _require_independent_external(
            promotion_record, use="adjudicated scientific claim input"
        )
    return DependencyDecision(
        mode=parsed_mode,
        satisfied=True,
        scientific_input_allowed=bool(accepted),
        allowed_use="accepted_claim_subset_only",
        accepted_claims=accepted,
    )


def is_negative_execution_receipt(
    resolution: ExecutionResolution | str,
) -> bool:
    """Return whether a terminal receipt is non-successful (never science input)."""

    try:
        parsed = ExecutionResolution(_enum_value(resolution))
    except ValueError as exc:
        raise RemediationContractError(
            f"unknown execution resolution {resolution!r}"
        ) from exc
    return parsed in _NEGATIVE_EXECUTION_RESOLUTIONS


def __getattr__(name: str) -> object:
    """Lazily preserve the historical remediation-state import surface.

    The decision type and its issuer share one lexical authority in
    ``common.evidence_graph``.  Keeping the implementation there prevents a
    separately importable allocator from becoming a second construction path,
    while this alias preserves existing ``common.remediation_state`` imports.
    """

    if name == "ClaimCapabilityDecision":
        from common.evidence_graph import ClaimCapabilityDecision

        return ClaimCapabilityDecision
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "AdjudicatedClaim",
    "AdjudicationReceipt",
    "ArtifactReadinessAxis",
    "AuthorityError",
    "AuthorityRegistry",
    "CapabilityAction",
    "CapabilityBlocker",
    "CapabilityBlockerKind",
    "CapabilityEvidenceBranch",
    "CapabilityIdentification",
    "CapabilityOutcome",
    "CapabilityProvenanceGrade",
    "CapabilityScientificSemantics",
    "CanonicalClaimTier",
    "CLAIM_IDENTITY_CANONICALIZATION",
    "ClaimCapability",
    "ClaimCapabilityDecision",
    "ClaimIdentity",
    "ClaimLevel",
    "ClaimLevelScheme",
    "DependencyDecision",
    "DependencyEvidence",
    "DependencyMode",
    "ExecutionResolution",
    "ExternalDeliveryReceipt",
    "IdentityDimension",
    "MAXIMUM_UNATTESTED_SCIENTIFIC_STATUS",
    "NON_RELAXABLE_CAPABILITY_RULES",
    "OrchestrationState",
    "PrincipalRecord",
    "RemediationContractError",
    "RemediationState",
    "ScientificStatus",
    "VersionedClaimIdentity",
    "assert_distinct_author_adjudicator",
    "canonical_claim_identity_payload",
    "claim_identity_fingerprint",
    "compare_claim_levels",
    "is_negative_execution_receipt",
    "require_independent_external_principal",
    "resolve_dependency",
    "validate_active_owner",
    "validate_scientific_transition",
]
