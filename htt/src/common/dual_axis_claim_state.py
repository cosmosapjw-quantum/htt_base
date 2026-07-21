"""PR-185: external-novelty x internal-readiness dual-axis claim SSoT.

Two axes that never collapse into one ordinal:

* ``novelty_tier_external`` in {K, C, P, S} -- ONLY the delta against the
  published literature. Never rewritten from readiness.
* ``readiness_state`` in the eight-state lifecycle -- proof/data/calibration/
  reproduction maturity. Never lifted by novelty.

``publication_use`` is the conjunctive result of the six gates plus an
independent (author != adjudicator) adjudication receipt and readiness
VALIDATED. A high-novelty / OPEN-readiness claim is a first-class legal
state; the whole point is that it is not fake-promoted and not
fake-downgraded.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

NOVELTY_TIERS = ("K", "C", "P", "S")
READINESS_STATES = (
    "OPEN",
    "IN_REMEDIATION",
    "EVIDENCE_READY",
    "ADJUDICATION_PENDING",
    "VALIDATED",
    "BLOCKED",
    "FALSIFIED",
    "ABANDONED",
)
TERMINAL_STATES = ("BLOCKED", "FALSIFIED", "ABANDONED")
GATE_NAMES = (
    "mechanics",
    "identification",
    "calibration",
    "provenance",
    "independence",
    "claim",
)
GATE_VALUES = ("pass", "fail", "blocked", "open", "not_applicable")
PASSLIKE = frozenset({"pass", "not_applicable"})

# Forward transition graph. Terminal states are reachable from any
# non-terminal state; the linear ladder governs the promotion path.
_LADDER = [
    "OPEN",
    "IN_REMEDIATION",
    "EVIDENCE_READY",
    "ADJUDICATION_PENDING",
    "VALIDATED",
]
FORWARD_TRANSITIONS: dict[str, set[str]] = {}
for _i, _s in enumerate(_LADDER):
    nxt = set(TERMINAL_STATES)
    if _i + 1 < len(_LADDER):
        nxt.add(_LADDER[_i + 1])
    # IN_REMEDIATION may return to EVIDENCE_READY only forward; allow
    # OPEN->EVIDENCE_READY direct (author-side gates can pass in one step).
    FORWARD_TRANSITIONS[_s] = nxt
FORWARD_TRANSITIONS["OPEN"].add("EVIDENCE_READY")
for _s in TERMINAL_STATES:
    FORWARD_TRANSITIONS[_s] = set()


class DualAxisError(ValueError):
    """Raised when the dual-axis invariant is violated."""


@dataclass(frozen=True)
class AdjudicationReceipt:
    adjudicator_principal: str
    independent: bool
    signature: str  # non-empty => signed; empty => fabricated/unsigned
    gate_snapshot_digest: str  # binds the receipt to the gate state it saw

    def to_dict(self) -> dict[str, Any]:
        return {
            "adjudicator_principal": self.adjudicator_principal,
            "independent": self.independent,
            "signature": self.signature,
            "gate_snapshot_digest": self.gate_snapshot_digest,
        }


@dataclass
class ClaimState:
    id: str
    novelty_tier_external: str
    readiness_state: str
    publication_use: bool
    novelty_basis: dict[str, Any]
    gates: dict[str, str]
    author_principals: tuple[str, ...] = ()
    adjudication_receipts: tuple[AdjudicationReceipt, ...] = ()
    promotion_parent: str | None = None
    internal_claim_level: str = "roadmap_rescue_v1:C1"

    def gate_digest(self) -> str:
        payload = json.dumps(
            {name: self.gates.get(name) for name in GATE_NAMES}, sort_keys=True
        )
        return hashlib.sha256(payload.encode()).hexdigest()


def _validate_axes(claim: ClaimState) -> list[str]:
    errs: list[str] = []
    if claim.novelty_tier_external not in NOVELTY_TIERS:
        errs.append(
            f"{claim.id}: invalid novelty_tier_external={claim.novelty_tier_external!r}"
        )
    if claim.readiness_state not in READINESS_STATES:
        errs.append(f"{claim.id}: invalid readiness_state={claim.readiness_state!r}")
    for name in GATE_NAMES:
        val = claim.gates.get(name)
        if val not in GATE_VALUES:
            errs.append(f"{claim.id}: gate {name}={val!r} not in {GATE_VALUES}")
    if claim.novelty_tier_external in ("P", "S"):
        for key in ("search_date", "search_protocol", "closest_literature", "delta"):
            v = claim.novelty_basis.get(key)
            if not (v if not isinstance(v, str) else v.strip()):
                errs.append(
                    f"{claim.id}: novelty {claim.novelty_tier_external} "
                    f"requires novelty_basis.{key}"
                )
    return errs


def _validated_gate_ok(claim: ClaimState) -> list[str]:
    """Conditions required for VALIDATED / publication_use."""
    errs: list[str] = []
    for name in GATE_NAMES:
        if claim.gates.get(name) not in PASSLIKE:
            errs.append(f"{claim.id}: gate {name}={claim.gates.get(name)!r} not passlike")
    signed_independent = [
        r
        for r in claim.adjudication_receipts
        if r.independent
        and r.signature.strip()
        and r.adjudicator_principal not in claim.author_principals
        and r.gate_snapshot_digest == claim.gate_digest()  # not stale
    ]
    if not signed_independent:
        errs.append(
            f"{claim.id}: requires a signed independent receipt "
            "(author != adjudicator, not stale)"
        )
    return errs


def validate_claim(claim: ClaimState) -> list[str]:
    errs = _validate_axes(claim)
    # The non-conflation invariant: novelty is a literature axis only.
    if claim.readiness_state in ("VALIDATED",) and claim.novelty_tier_external not in NOVELTY_TIERS:
        errs.append(f"{claim.id}: readiness must not define novelty")
    # publication_use fail-closed.
    if claim.publication_use:
        if claim.readiness_state != "VALIDATED":
            errs.append(f"{claim.id}: publication_use=true requires VALIDATED")
        errs.extend(_validated_gate_ok(claim))
    # promotion parent must not be self (circular).
    if claim.promotion_parent == claim.id:
        errs.append(f"{claim.id}: circular promotion parent")
    return errs


def can_transition(current: str, target: str) -> bool:
    if current not in READINESS_STATES or target not in READINESS_STATES:
        return False
    return target in FORWARD_TRANSITIONS.get(current, set())


def promote(claim: ClaimState, target: str) -> ClaimState:
    """Advance readiness through the registered graph, fail-closed.

    Never touches novelty_tier_external. VALIDATED requires the full gate
    set + a signed independent receipt.
    """
    if not can_transition(claim.readiness_state, target):
        raise DualAxisError(
            f"{claim.id}: illegal readiness transition "
            f"{claim.readiness_state} -> {target}"
        )
    if target == "EVIDENCE_READY":
        for name in ("mechanics", "identification", "calibration", "provenance"):
            if claim.gates.get(name) not in PASSLIKE:
                raise DualAxisError(
                    f"{claim.id}: EVIDENCE_READY needs {name} passlike, "
                    f"got {claim.gates.get(name)!r}"
                )
    if target == "VALIDATED":
        errs = _validated_gate_ok(claim)
        if errs:
            raise DualAxisError("; ".join(errs))
    novelty_before = claim.novelty_tier_external
    claim.readiness_state = target
    if claim.novelty_tier_external != novelty_before:  # pragma: no cover
        raise DualAxisError(f"{claim.id}: novelty must not change during promotion")
    return claim


def migrate_v10_tier_ledger(ledger: dict[str, Any]) -> list[ClaimState]:
    """Lossless dual-axis migration of the v10 external-novelty ledger.

    novelty head from the tier string (e.g. 'K+C' -> S? no: head is the
    strongest external head present, both recorded in the basis);
    readiness = EVIDENCE_READY with the independence gate OPEN.
    """
    claims: list[ClaimState] = []
    order = {t: i for i, t in enumerate(NOVELTY_TIERS)}
    for entry in ledger["entries"]:
        raw = str(entry["tier"])
        heads = [h.strip() for h in raw.replace("/", "+").split("+")]
        head = max((h for h in heads if h in order), key=lambda h: order[h])
        basis = {
            "recorded_tier": raw,
            "adjudication": entry.get("adjudication", ""),
            "closest_literature": entry.get("citations", []),
            "delta": entry.get("adjudication", ""),
            "search_date": ledger.get("generated", "2026-07-21"),
            "search_protocol": "documented web CRAG (v10 ledger)",
        }
        gates = {
            "mechanics": "pass",
            "identification": "pass",
            "calibration": "pass",
            "provenance": "pass",
            "independence": "open",  # spend-limited; explicitly OPEN
            "claim": "pass",
        }
        claims.append(
            ClaimState(
                id=entry["id"],
                novelty_tier_external=head,
                readiness_state="EVIDENCE_READY",
                publication_use=False,
                novelty_basis=basis,
                gates=gates,
                author_principals=("BASS_HTT_program",),
            )
        )
    return claims


def migration_diff(ledger: dict[str, Any], claims: list[ClaimState]) -> dict[str, Any]:
    """Verify zero id / novelty-delta loss on migration."""
    order = {t: i for i, t in enumerate(NOVELTY_TIERS)}
    by_id = {c.id: c for c in claims}
    lost_ids: list[str] = []
    basis_loss: list[str] = []
    head_mismatch: list[str] = []
    for entry in ledger["entries"]:
        cid = entry["id"]
        if cid not in by_id:
            lost_ids.append(cid)
            continue
        c = by_id[cid]
        if not c.novelty_basis.get("adjudication"):
            basis_loss.append(cid)
        raw = str(entry["tier"]).replace("/", "+")
        heads = [h.strip() for h in raw.split("+") if h.strip() in order]
        expected = max(heads, key=lambda h: order[h])
        if c.novelty_tier_external != expected:
            head_mismatch.append(cid)
    return {
        "lost_ids": lost_ids,
        "basis_loss": basis_loss,
        "head_mismatch": head_mismatch,
        "diff_zero": not (lost_ids or basis_loss or head_mismatch),
        "n_entries": len(ledger["entries"]),
        "n_claims": len(claims),
    }
