"""COMMON-owned semantic adequacy guard records.

These helpers preserve the useful source/propagation/observable separation
from legacy TSC reports without giving TSC ownership over new artifacts.
They carry metadata and caveats only; they do not validate a solver, promote
observable claims, or create posterior/evidence terms.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from enum import Enum

try:  # Python 3.11+
    from enum import StrEnum
except ImportError:  # pragma: no cover - exercised by the Python 3.10 replay

    class StrEnum(str, Enum):
        """Minimal stdlib-compatible fallback for the declared Python floor."""

        def __str__(self) -> str:
            return str(self.value)


from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
    normalize_claim_tier,
    normalize_implementation_scope,
    normalize_owner,
)


class SourceAdequacyStatus(StrEnum):
    """Source-side adequacy status, independent of propagation and observables."""

    ADEQUATE = "adequate"
    INADEQUATE = "inadequate"
    PENDING = "pending"
    NOT_EVALUATED = "not_evaluated"


class PropagationAdequacyStatus(StrEnum):
    """Propagation-side adequacy status, independent of source and observables."""

    VALIDATED = "validated"
    PENDING = "pending"
    BLOCKED = "blocked"
    NOT_EVALUATED = "not_evaluated"


class ObservableAdequacyStatus(StrEnum):
    """Observable-side semantic status that must be asserted explicitly.

    This does not represent statistical validation, native atlas support,
    transfer provenance, response-rank adequacy, null calibration, or
    publication readiness.
    """

    ADEQUATE = "adequate"
    CONDITIONAL = "conditional"
    INADEQUATE = "inadequate"
    BLOCKED = "blocked"
    NOT_EVALUATED = "not_evaluated"


_BLOCKING_OBSERVABLE_STATUSES = {
    ObservableAdequacyStatus.INADEQUATE,
    ObservableAdequacyStatus.BLOCKED,
}
_SEMANTIC_GUARD_CLAIM_TIERS = {
    ClaimTier.DIAGNOSTIC_ONLY,
    ClaimTier.EXPLORATORY,
    ClaimTier.BLOCKED,
}
_CLAIM_TIER_RANK = {
    ClaimTier.BLOCKED: 0,
    ClaimTier.EXPLORATORY: 1,
    ClaimTier.DIAGNOSTIC_ONLY: 2,
    ClaimTier.CONDITIONAL: 3,
    ClaimTier.VALIDATED: 4,
}


def _normalize_status(
    enum_type: type[StrEnum], value: object, field_name: str
) -> StrEnum:
    raw = value.value if isinstance(value, StrEnum) else str(value)
    try:
        return enum_type(raw)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise ValueError(
            f"Unknown {field_name} {raw!r}; expected one of {allowed}"
        ) from exc


def _normalize_text_sequence(value: Sequence[str], field_name: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{field_name} must be a sequence of strings")
    normalized = tuple(str(item).strip() for item in value)
    if any(not item for item in normalized):
        raise ValueError(f"{field_name} entries must be non-empty strings")
    return normalized


@dataclass(frozen=True)
class SemanticAdequacyRecord:
    """Generic guard metadata for source, propagation, and observable status.

    The statuses are intentionally separate. A source can be adequate while
    propagation is pending, and both source and propagation can be acceptable
    while observable adequacy remains not evaluated.
    """

    source_status: SourceAdequacyStatus | str
    propagation_status: PropagationAdequacyStatus | str
    observable_status: ObservableAdequacyStatus | str
    caveats: Sequence[str] = field(default_factory=tuple)
    labels: Sequence[str] = field(default_factory=tuple)
    claim_tier_ceiling: ClaimTier | str = ClaimTier.DIAGNOSTIC_ONLY
    semantic_guard_owner: Owner = Owner.COMMON
    implementation_scope: ImplementationScope = ImplementationScope.COMMON

    def __post_init__(self) -> None:
        source_status = _normalize_status(
            SourceAdequacyStatus,
            self.source_status,
            "source_status",
        )
        propagation_status = _normalize_status(
            PropagationAdequacyStatus,
            self.propagation_status,
            "propagation_status",
        )
        observable_status = _normalize_status(
            ObservableAdequacyStatus,
            self.observable_status,
            "observable_status",
        )
        object.__setattr__(self, "source_status", source_status)
        object.__setattr__(self, "propagation_status", propagation_status)
        object.__setattr__(self, "observable_status", observable_status)
        object.__setattr__(
            self,
            "caveats",
            _normalize_text_sequence(self.caveats, "SemanticAdequacyRecord.caveats"),
        )
        object.__setattr__(
            self,
            "labels",
            _normalize_text_sequence(self.labels, "SemanticAdequacyRecord.labels"),
        )
        object.__setattr__(
            self,
            "claim_tier_ceiling",
            normalize_claim_tier(self.claim_tier_ceiling),
        )
        if self.claim_tier_ceiling not in _SEMANTIC_GUARD_CLAIM_TIERS:
            raise ValueError(
                "SemanticAdequacyRecord.claim_tier_ceiling must be "
                "diagnostic_only, exploratory, or blocked"
            )
        if (
            source_status is SourceAdequacyStatus.INADEQUATE
            or propagation_status is PropagationAdequacyStatus.BLOCKED
            or observable_status in _BLOCKING_OBSERVABLE_STATUSES
        ):
            object.__setattr__(
                self,
                "claim_tier_ceiling",
                ClaimTier.BLOCKED,
            )
        owner = normalize_owner(self.semantic_guard_owner)
        scope = normalize_implementation_scope(self.implementation_scope)
        object.__setattr__(self, "semantic_guard_owner", owner)
        object.__setattr__(self, "implementation_scope", scope)
        if owner is not Owner.COMMON:
            raise ValueError(
                "SemanticAdequacyRecord.semantic_guard_owner must be COMMON"
            )
        if scope is not ImplementationScope.COMMON:
            raise ValueError(
                "SemanticAdequacyRecord.implementation_scope must be common"
            )
        if observable_status is ObservableAdequacyStatus.ADEQUATE:
            if source_status is not SourceAdequacyStatus.ADEQUATE:
                raise ValueError(
                    "observable_status='adequate' requires source_status='adequate'"
                )
            if propagation_status is not PropagationAdequacyStatus.VALIDATED:
                raise ValueError(
                    "observable_status='adequate' requires "
                    "propagation_status='validated'"
                )

    @property
    def source_is_adequate(self) -> bool:
        return self.source_status is SourceAdequacyStatus.ADEQUATE

    @property
    def propagation_is_validated(self) -> bool:
        return self.propagation_status is PropagationAdequacyStatus.VALIDATED

    @property
    def observable_is_adequate(self) -> bool:
        return self.observable_status is ObservableAdequacyStatus.ADEQUATE

    @property
    def observable_is_blocked(self) -> bool:
        return self.observable_status in _BLOCKING_OBSERVABLE_STATUSES

    def to_metadata(self) -> dict[str, object]:
        """Return JSON-compatible COMMON semantic guard metadata."""

        return {
            "semantic_guard_owner": self.semantic_guard_owner.value,
            "implementation_scope": self.implementation_scope.value,
            "source_status": self.source_status.value,
            "propagation_status": self.propagation_status.value,
            "observable_status": self.observable_status.value,
            "claim_tier_ceiling": self.claim_tier_ceiling.value,
            "labels": list(self.labels),
            "caveats": list(self.caveats),
            "observable_status_is_explicit": True,
            "observable_adequacy_is_established": (
                self.observable_status is ObservableAdequacyStatus.ADEQUATE
            ),
            "observable_adequacy_scope": (
                "semantic_guard_only_not_statistical_validation"
            ),
            "statistical_validation_status": "not_represented",
            "does_not_establish": [
                "null_calibration",
                "mask_or_sky_support",
                "covariance_support",
                "response_rank_or_equivalence",
                "transfer_provenance",
                "native_morphology_atlas",
                "family_identification",
            ],
        }

    def to_caveats(self) -> tuple[str, ...]:
        """Render compact caveats suitable for ``ArtifactManifest.caveats``."""

        status_caveat = (
            "semantic_guard:"
            f"source={self.source_status.value};"
            f"propagation={self.propagation_status.value};"
            f"observable={self.observable_status.value}"
        )
        return (status_caveat, *self.caveats)


def attach_semantic_caveats(
    manifest: ArtifactManifest,
    record: SemanticAdequacyRecord,
    *,
    extra_caveats: Sequence[str] = (),
) -> ArtifactManifest:
    """Return ``manifest`` with COMMON semantic caveats appended.

    The artifact owner and implementation scope are preserved. This lets HTT,
    MIO, BASS, OBSSTAT, or COMMON artifacts carry trace/source caveats without
    creating a new TSC-owned output path.
    """

    extra = _normalize_text_sequence(extra_caveats, "extra_caveats")
    manifest_tier = normalize_claim_tier(manifest.claim_tier)
    if _CLAIM_TIER_RANK[manifest_tier] > _CLAIM_TIER_RANK[record.claim_tier_ceiling]:
        raise ValueError(
            "semantic caveats cannot support a manifest claim_tier above "
            f"{record.claim_tier_ceiling.value!r}"
        )
    return replace(
        manifest,
        caveats=[*manifest.caveats, *record.to_caveats(), *extra],
    )


__all__ = [
    "ObservableAdequacyStatus",
    "PropagationAdequacyStatus",
    "SemanticAdequacyRecord",
    "SourceAdequacyStatus",
    "attach_semantic_caveats",
]
