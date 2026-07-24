"""PR-213 runner: dual-axis claim-state successor + PR-185 cross-ref (RESCUE)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.revival_claim_state import (  # noqa: E402
    AdjudicationReceipt,
    ClaimState,
    ClaimStateError,
    Novelty,
    Readiness,
    can_transition,
)

SPEC = REPO / "docs/research_program/revival/pr213_spec.yaml"
CARD = REPO / "docs/generated/pr213_result_card.json"
PR185_CARD = REPO / "docs/generated/pr185_result_card.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _legal_combos() -> dict:
    """Every (novelty, readiness) is legal with public_use=false (independent axes)."""
    total = accepted = 0
    for nov, rd in product(Novelty, Readiness):
        total += 1
        try:
            ClaimState(nov, rd, public_use=False).validate()
            accepted += 1
        except ClaimStateError:
            pass
    return {"total": total, "accepted": accepted, "all_accepted": accepted == total}


def _kill_battery() -> dict:
    valid = AdjudicationReceipt("A", "B", "lineage-x", signed=True)
    kills = {}

    def rejected(fn) -> bool:
        try:
            fn()
            return False
        except ClaimStateError:
            return True

    # S novelty alone must NOT open public_use
    kills["S_novelty_alone_rejected"] = rejected(
        lambda: ClaimState(Novelty.S, Readiness.OPEN, public_use=True).validate())
    # VALIDATED without a receipt rejected
    kills["validated_without_receipt_rejected"] = rejected(
        lambda: ClaimState(Novelty.S, Readiness.VALIDATED, public_use=True).validate())
    # author == adjudicator rejected
    kills["author_equals_adjudicator_rejected"] = rejected(
        lambda: ClaimState(Novelty.S, Readiness.VALIDATED, public_use=True,
                           receipt=AdjudicationReceipt("A", "A", "l", True)).validate())
    # unsigned receipt rejected
    kills["unsigned_receipt_rejected"] = rejected(
        lambda: ClaimState(Novelty.S, Readiness.VALIDATED, public_use=True,
                           receipt=AdjudicationReceipt("A", "B", "l", False)).validate())
    # This legacy boolean/string receipt cannot authenticate external authority.
    # Public use remains blocked until a trusted verifier path is supplied.
    kills["legal_public_use_accepted"] = not rejected(
        lambda: ClaimState(
            Novelty.S,
            Readiness.VALIDATED,
            public_use=True,
            receipt=valid,
        ).validate()
    )
    return kills


def _forward_only() -> dict:
    # a backward transition (VALIDATED -> OPEN) is illegal; forward is allowed
    return {"forward_ready_to_pending": can_transition(Readiness.EVIDENCE_READY,
                                                       Readiness.ADJUDICATION_PENDING),
            "backward_validated_to_open_rejected": not can_transition(Readiness.VALIDATED,
                                                                      Readiness.OPEN)}


def _crossref_pr185() -> dict:
    card = json.loads(PR185_CARD.read_text(encoding="utf-8"))
    res = card.get("result", {})
    return {"pr185_terminal": card.get("terminal"),
            "kill_battery_all_caught": res.get("kill_battery_all_caught"),
            "publication_mutations_all_rejected": res.get("publication_mutations_all_rejected"),
            "legal_combos_total": res.get("legal_combos_total")}


def build_payload() -> dict:
    combos = _legal_combos()
    kills = _kill_battery()
    fwd = _forward_only()
    xref = _crossref_pr185()
    ok = (combos["all_accepted"] and all(kills.values()) and all(fwd.values())
          and xref["kill_battery_all_caught"] and xref["publication_mutations_all_rejected"])
    terminal = ("DUAL_AXIS_SUCCESSOR_CERTIFIED_PR185_CONSISTENT"
                if ok else "BLOCKED_CLAIM_STATE_GATE_FAILURE")
    return {
        "schema": "htt.pr213.result_card.v1",
        "pr_id": "PR-213",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "disposition": "LITERAL_RESCUE",
            "cross_references": ["PR-185"],
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr213_claim_state.py --write"
            ),
        },
        "result": {"legal_combos": combos, "kill_battery": kills,
                   "forward_only_ladder": fwd, "pr185_crossref": xref},
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "high external novelty never opens public_use by itself",
            "novelty and readiness are independent axes; neither auto-changes the other",
            "public_use requires VALIDATED + a signed author!=adjudicator receipt",
        ],
    }


def _render(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=1) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload()
    if args.write:
        CARD.write_bytes(_render(payload))
        print(f"wrote {CARD.name}; terminal={payload['terminal']}")
        return 0
    ok = CARD.exists() and CARD.read_bytes() == _render(payload)
    print(json.dumps({"mode": "check", "ok": ok, "read_only": True,
                      "terminal": payload["terminal"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
