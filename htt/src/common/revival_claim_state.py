"""PR-213: external novelty x internal readiness promotion state machine (RESCUE).

The full dual-axis SSoT + promotion engine is closed in PR-185. This module is
the clean-room LEGACY SUCCESSOR of the old mio/status_schema.py: external
novelty (K/C/P/S) and internal readiness (8-state) are independent axes, and
public_use opens only through a validated readiness state AND a proof-carrying
external adjudication receipt whose author differs from the adjudicator. High
novelty alone never opens public use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Novelty(str, Enum):
    K = "K"  # known / textbook-level
    C = "C"  # cross-check of a named study
    P = "P"  # potential delta over existing research
    S = "S"  # significant delta


class Readiness(str, Enum):
    OPEN = "OPEN"
    IN_REMEDIATION = "IN_REMEDIATION"
    EVIDENCE_READY = "EVIDENCE_READY"
    ADJUDICATION_PENDING = "ADJUDICATION_PENDING"
    VALIDATED = "VALIDATED"
    BLOCKED = "BLOCKED"
    FALSIFIED = "FALSIFIED"
    ABANDONED = "ABANDONED"


class ClaimStateError(ValueError):
    pass


@dataclass(frozen=True)
class AdjudicationReceipt:
    author: str
    adjudicator: str
    lineage: str
    signed: bool

    def is_valid(self) -> bool:
        return (self.signed and bool(self.lineage)
                and self.author != self.adjudicator)


@dataclass(frozen=True)
class ClaimState:
    novelty: Novelty
    readiness: Readiness
    public_use: bool = False
    receipt: AdjudicationReceipt | None = None

    def validate(self) -> None:
        # novelty and readiness never collapse to one ordinal: any combination is legal
        if self.public_use:
            if self.readiness is not Readiness.VALIDATED:
                raise ClaimStateError("public_use requires VALIDATED readiness")
            if self.receipt is None or not self.receipt.is_valid():
                raise ClaimStateError(
                    "public_use requires a signed external adjudication receipt "
                    "with author != adjudicator")


# forward-only readiness ladder (matches the PR-185 lattice shape)
_FORWARD = {
    Readiness.OPEN: {Readiness.IN_REMEDIATION, Readiness.EVIDENCE_READY,
                     Readiness.BLOCKED, Readiness.FALSIFIED, Readiness.ABANDONED},
    Readiness.IN_REMEDIATION: {Readiness.EVIDENCE_READY, Readiness.BLOCKED,
                               Readiness.FALSIFIED, Readiness.ABANDONED},
    Readiness.EVIDENCE_READY: {Readiness.ADJUDICATION_PENDING, Readiness.BLOCKED,
                               Readiness.FALSIFIED},
    Readiness.ADJUDICATION_PENDING: {Readiness.VALIDATED, Readiness.BLOCKED,
                                     Readiness.FALSIFIED},
    Readiness.VALIDATED: set(),
    Readiness.BLOCKED: {Readiness.IN_REMEDIATION, Readiness.ABANDONED},
    Readiness.FALSIFIED: set(),
    Readiness.ABANDONED: set(),
}


def can_transition(current: Readiness, target: Readiness) -> bool:
    return target in _FORWARD.get(current, set())


def promote(claim: ClaimState, target: Readiness,
            receipt: AdjudicationReceipt | None = None) -> ClaimState:
    """Advance readiness only along the forward ladder; novelty is untouched."""
    if not can_transition(claim.readiness, target):
        raise ClaimStateError(f"illegal readiness transition {claim.readiness}->{target}")
    new = ClaimState(claim.novelty, target, claim.public_use,
                     receipt if receipt is not None else claim.receipt)
    new.validate()
    return new
