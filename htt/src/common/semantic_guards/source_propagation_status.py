"""Source/propagation/observable guard composition.

This module gives active packages a COMMON-owned way to state that a source
bridge is adequate, propagation is pending or validated, and observable
adequacy is still a separate status. It deliberately avoids TSC imports.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from common.contracts import ClaimTier
from common.semantic_guards.admissibility_status import (
    ObservableAdequacyStatus,
    PropagationAdequacyStatus,
    SemanticAdequacyRecord,
    SourceAdequacyStatus,
)


def _default_observable_caveat(
    *,
    source_status: SourceAdequacyStatus,
    propagation_status: PropagationAdequacyStatus,
    observable_status: ObservableAdequacyStatus,
) -> str:
    if observable_status is ObservableAdequacyStatus.ADEQUATE:
        return "observable adequacy explicitly established"
    if source_status is not SourceAdequacyStatus.ADEQUATE:
        return "source adequacy not established"
    if propagation_status is not PropagationAdequacyStatus.VALIDATED:
        return "propagation adequacy not validated"
    return "observable adequacy not established"


def _status_label(
    *,
    source_status: SourceAdequacyStatus,
    propagation_status: PropagationAdequacyStatus,
    observable_status: ObservableAdequacyStatus,
) -> str:
    return (
        f"source_{source_status.value}"
        f"__propagation_{propagation_status.value}"
        f"__observable_{observable_status.value}"
    )


def _claim_ceiling(
    *,
    source_status: SourceAdequacyStatus,
    propagation_status: PropagationAdequacyStatus,
    observable_status: ObservableAdequacyStatus,
) -> ClaimTier:
    if (
        source_status is SourceAdequacyStatus.INADEQUATE
        or propagation_status is PropagationAdequacyStatus.BLOCKED
        or observable_status in {
            ObservableAdequacyStatus.BLOCKED,
            ObservableAdequacyStatus.INADEQUATE,
        }
    ):
        return ClaimTier.BLOCKED
    return ClaimTier.DIAGNOSTIC_ONLY


def _claim_ceiling_default() -> ClaimTier:
    return ClaimTier.DIAGNOSTIC_ONLY


@dataclass(frozen=True)
class SourcePropagationStatus(SemanticAdequacyRecord):
    """COMMON status bundle with a deterministic label and diagnostic ceiling."""

    caveats: Sequence[str] = field(default_factory=tuple)
    labels: Sequence[str] = field(default_factory=tuple)
    claim_tier_ceiling: ClaimTier | str = field(
        default_factory=_claim_ceiling_default,
        init=False,
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        labels = tuple(self.labels)
        if not labels:
            labels = (
                _status_label(
                    source_status=self.source_status,
                    propagation_status=self.propagation_status,
                    observable_status=self.observable_status,
                ),
            )
            object.__setattr__(self, "labels", labels)
        caveats = tuple(self.caveats)
        if not caveats:
            caveats = (
                _default_observable_caveat(
                    source_status=self.source_status,
                    propagation_status=self.propagation_status,
                    observable_status=self.observable_status,
                ),
            )
            object.__setattr__(self, "caveats", caveats)
        object.__setattr__(
            self,
            "claim_tier_ceiling",
            _claim_ceiling(
                source_status=self.source_status,
                propagation_status=self.propagation_status,
                observable_status=self.observable_status,
            ),
        )

    @property
    def label(self) -> str:
        return self.labels[0]


def build_source_propagation_status(
    *,
    source_status: SourceAdequacyStatus | str,
    propagation_status: PropagationAdequacyStatus | str,
    observable_status: ObservableAdequacyStatus | str = ObservableAdequacyStatus.NOT_EVALUATED,
    caveats: Sequence[str] = (),
    labels: Sequence[str] = (),
) -> SourcePropagationStatus:
    """Build a guard record without collapsing source into observables."""

    return SourcePropagationStatus(
        source_status=source_status,
        propagation_status=propagation_status,
        observable_status=observable_status,
        caveats=caveats,
        labels=labels,
    )


__all__ = [
    "SourcePropagationStatus",
    "build_source_propagation_status",
]
