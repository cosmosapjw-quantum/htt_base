"""PR-185 runner: dual-axis claim SSoT migration + gate battery (--write/--check)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.dual_axis_claim_state import (  # noqa: E402
    AdjudicationReceipt,
    ClaimState,
    DualAxisError,
    GATE_NAMES,
    NOVELTY_TIERS,
    READINESS_STATES,
    can_transition,
    migrate_v10_tier_ledger,
    migration_diff,
    promote,
    validate_claim,
)

SPEC = REPO / "docs/research_program/strengthening/pr185_spec.yaml"
V10_LEDGER = REPO / "docs/audits/v10_web_crag_20260721/tier_evidence.json"
LEDGER_OUT = REPO / "docs/generated/dual_axis_claim_ledger.json"
CARD = REPO / "docs/generated/pr185_result_card.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validated_claim() -> ClaimState:
    """A syntactically complete legacy receipt used as a mutation base."""
    gates = {name: "pass" for name in GATE_NAMES}
    claim = ClaimState(
        id="BASE",
        novelty_tier_external="S",
        readiness_state="ADJUDICATION_PENDING",
        publication_use=False,
        novelty_basis={
            "search_date": "2026-07-21",
            "search_protocol": "documented CRAG",
            "closest_literature": ["ref"],
            "delta": "delta",
        },
        gates=gates,
        author_principals=("author_A",),
    )
    receipt = AdjudicationReceipt(
        adjudicator_principal="reviewer_B",
        independent=True,
        signature="signed",
        gate_snapshot_digest=claim.gate_digest(),
    )
    claim.adjudication_receipts = (receipt,)
    return claim


def _legal_combos() -> dict[str, bool]:
    """Every (novelty, readiness) combination is a legal state (no conflation)."""
    results = {}
    for nov in NOVELTY_TIERS:
        for rs in READINESS_STATES:
            basis = {
                "search_date": "2026-07-21",
                "search_protocol": "CRAG",
                "closest_literature": ["x"],
                "delta": "d",
            }
            gates = {name: "open" for name in GATE_NAMES}
            claim = ClaimState(
                id=f"{nov}-{rs}",
                novelty_tier_external=nov,
                readiness_state=rs,
                publication_use=False,
                novelty_basis=basis,
                gates=gates,
            )
            results[f"{nov}+{rs}"] = validate_claim(claim) == []
    return results


def _publication_mutation_battery(n: int = 100) -> dict[str, int]:
    """n publication_use=true mutations, each missing a gate or receipt.

    Every one must be rejected (fail-closed)."""
    rejected = 0
    total = 0
    base = _validated_claim()
    base.readiness_state = "VALIDATED"
    for i in range(n):
        c = replace(base)
        c.publication_use = True
        # rotate a defect through gates/receipts deterministically
        defect = i % 8
        if defect == 0:
            c.gates = {**c.gates, "independence": "open"}
        elif defect == 1:
            c.gates = {**c.gates, "mechanics": "fail"}
        elif defect == 2:
            c.gates = {**c.gates, "calibration": "blocked"}
        elif defect == 3:
            c.adjudication_receipts = ()
        elif defect == 4:
            c.adjudication_receipts = (
                AdjudicationReceipt("reviewer_B", False, "signed", c.gate_digest()),
            )
        elif defect == 5:  # author == adjudicator
            c.adjudication_receipts = (
                AdjudicationReceipt("author_A", True, "signed", c.gate_digest()),
            )
        elif defect == 6:  # fabricated / unsigned
            c.adjudication_receipts = (
                AdjudicationReceipt("reviewer_B", True, "", c.gate_digest()),
            )
        else:  # stale receipt (digest of a different gate state)
            c.adjudication_receipts = (
                AdjudicationReceipt("reviewer_B", True, "signed", "stale-digest"),
            )
        total += 1
        if validate_claim(c) != []:
            rejected += 1
    return {"total": total, "rejected": rejected}


def _kill_battery() -> dict[str, bool]:
    """The four named adversarial kills must each be caught."""
    base = _validated_claim()
    base.readiness_state = "VALIDATED"

    # author == adjudicator
    c1 = replace(base, publication_use=True)
    c1.adjudication_receipts = (
        AdjudicationReceipt("author_A", True, "signed", c1.gate_digest()),
    )
    author_kill = validate_claim(c1) != []

    # fabricated (unsigned) receipt
    c2 = replace(base, publication_use=True)
    c2.adjudication_receipts = (
        AdjudicationReceipt("reviewer_B", True, "", c2.gate_digest()),
    )
    fabricated_kill = validate_claim(c2) != []

    # circular promotion parent
    c3 = replace(base)
    c3.promotion_parent = c3.id
    circular_kill = validate_claim(c3) != []

    # stale gate receipt (digest mismatch)
    c4 = replace(base, publication_use=True)
    c4.adjudication_receipts = (
        AdjudicationReceipt("reviewer_B", True, "signed", "old-digest"),
    )
    stale_kill = validate_claim(c4) != []

    # illegal transition (no ordinal collapse: cannot jump OPEN->VALIDATED)
    illegal_jump = not can_transition("OPEN", "VALIDATED")

    return {
        "author_equals_adjudicator_killed": author_kill,
        "fabricated_receipt_killed": fabricated_kill,
        "circular_parent_killed": circular_kill,
        "stale_gate_killed": stale_kill,
        "no_open_to_validated_jump": illegal_jump,
    }


def build_ledger() -> tuple[dict, list[ClaimState]]:
    ledger = json.loads(V10_LEDGER.read_text())
    claims = migrate_v10_tier_ledger(ledger)
    return ledger, claims


def build_payload() -> tuple[dict, dict]:
    ledger, claims = build_ledger()
    diff = migration_diff(ledger, claims)
    combos = _legal_combos()
    pub = _publication_mutation_battery()
    kills = _kill_battery()
    try:
        promote(_validated_claim(), "VALIDATED")
        authenticated_receipt_authority_available = True
    except DualAxisError:
        authenticated_receipt_authority_available = False

    dual_ledger = {
        "schema": "htt.dual_axis_claim_ledger.v1",
        "source_ledger": "docs/audits/v10_web_crag_20260721/tier_evidence.json",
        "source_sha256": _sha(V10_LEDGER),
        "readiness_principle": (
            "each migrated claim carries EVIDENCE_READY with the independence "
            "gate OPEN (adjudication capacity spend-limited); publication_use "
            "false; external novelty is a separate axis and is not downgraded "
            "by the OPEN independence gate."
        ),
        "claims": [
            {
                "id": c.id,
                "novelty_tier_external": c.novelty_tier_external,
                "readiness_state": c.readiness_state,
                "publication_use": c.publication_use,
                "novelty_basis": c.novelty_basis,
                "gates": c.gates,
                "adjudication_receipts": [],
            }
            for c in claims
        ],
    }

    card = {
        "schema": "htt.pr185.result_card.v1",
        "pr_id": "PR-185",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr185_dual_axis.py --write"
            ),
        },
        "result": {
            "migration_diff": diff,
            "legal_combos_total": len(combos),
            "legal_combos_all_accepted": all(combos.values()),
            "publication_mutation_battery": pub,
            "publication_mutations_all_rejected": pub["rejected"] == pub["total"],
            "kill_battery": kills,
            "kill_battery_all_caught": all(kills.values()),
            "authenticated_receipt_authority_available": (
                authenticated_receipt_authority_available
            ),
            "dual_ledger_sha256": hashlib.sha256(
                (json.dumps(dual_ledger, sort_keys=True, indent=1) + "\n").encode()
            ).hexdigest(),
        },
        "terminal": (
            "BLOCKED_AUTHENTICATED_RECEIPT_UNAVAILABLE"
            if not authenticated_receipt_authority_available
            else (
                "DUAL_AXIS_SSOT_EVIDENCE_READY_INDEPENDENCE_OPEN"
                if (
                    diff["diff_zero"]
                    and all(combos.values())
                    and pub["rejected"] == pub["total"]
                    and all(kills.values())
                )
                else "BLOCKED_GATE_FAILURE"
            )
        ),
        "forbidden_claims_reaffirmed": [
            "novelty and readiness are never a single ordinal",
            "no publication_use without VALIDATED + independent signed receipt",
            "external novelty never downgraded by an internal blocker",
        ],
    }
    return dual_ledger, card


def _render(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=1) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    dual_ledger, card = build_payload()
    if args.write:
        if card["terminal"] != "DUAL_AXIS_SSOT_EVIDENCE_READY_INDEPENDENCE_OPEN":
            print(
                "refusing to overwrite frozen historical outputs without an "
                "authenticated external receipt verifier",
                file=sys.stderr,
            )
            return 2
        LEDGER_OUT.write_bytes(_render(dual_ledger))
        CARD.write_bytes(_render(card))
        print(f"wrote {LEDGER_OUT.name} + {CARD.name}; terminal={card['terminal']}")
        return 0
    ok = (
        LEDGER_OUT.exists()
        and CARD.exists()
        and LEDGER_OUT.read_bytes() == _render(dual_ledger)
        and CARD.read_bytes() == _render(card)
    )
    print(json.dumps({"mode": "check", "ok": ok, "read_only": True,
                      "terminal": card["terminal"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
