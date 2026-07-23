"""PR-185 gates: dual-axis claim SSoT + promotion engine (R1)."""

from __future__ import annotations

import hashlib
import json
import subprocess
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
    promote,
    validate_claim,
)

CARD = REPO / "docs/generated/pr185_result_card.json"
LEDGER = REPO / "docs/generated/dual_axis_claim_ledger.json"
SPEC = REPO / "docs/research_program/strengthening/pr185_spec.yaml"


def _card() -> dict:
    return json.loads(CARD.read_text())


def _base_validated() -> ClaimState:
    gates = {name: "pass" for name in GATE_NAMES}
    c = ClaimState(
        id="BASE", novelty_tier_external="S", readiness_state="ADJUDICATION_PENDING",
        publication_use=False,
        novelty_basis={"search_date": "d", "search_protocol": "p",
                       "closest_literature": ["x"], "delta": "d"},
        gates=gates, author_principals=("author_A",),
    )
    c.adjudication_receipts = (
        AdjudicationReceipt("reviewer_B", True, "signed", c.gate_digest()),
    )
    return c


def test_spec_bound_and_terminal() -> None:
    card = _card()
    assert card["metadata"]["spec_sha256"] == hashlib.sha256(
        SPEC.read_bytes()
    ).hexdigest()
    assert card["metadata"]["public_use"] is False
    assert card["metadata"]["readiness_state"] == "EVIDENCE_READY"
    assert card["metadata"]["independence_gate"] == "OPEN"
    assert card["terminal"] == "DUAL_AXIS_SSOT_EVIDENCE_READY_INDEPENDENCE_OPEN"


def test_migration_diff_zero() -> None:
    r = _card()["result"]["migration_diff"]
    assert r["diff_zero"] is True
    assert r["n_entries"] == r["n_claims"]
    # every S-tier v10 entry survives as S / EVIDENCE_READY, publication_use false
    v10 = json.loads(
        (REPO / "docs/audits/v10_web_crag_20260721/tier_evidence.json").read_text()
    )
    ledger = json.loads(LEDGER.read_text())
    by_id = {c["id"]: c for c in ledger["claims"]}
    for e in v10["entries"]:
        head = max(
            (h.strip() for h in str(e["tier"]).replace("/", "+").split("+")
             if h.strip() in NOVELTY_TIERS),
            key=lambda h: NOVELTY_TIERS.index(h),
        )
        c = by_id[e["id"]]
        assert c["novelty_tier_external"] == head
        assert c["readiness_state"] == "EVIDENCE_READY"
        assert c["publication_use"] is False


def test_axes_never_conflate() -> None:
    # all 4x8 combinations are legal states
    assert _card()["result"]["legal_combos_total"] == 32
    assert _card()["result"]["legal_combos_all_accepted"] is True
    # S novelty with OPEN readiness is legal
    c = ClaimState(
        id="x", novelty_tier_external="S", readiness_state="OPEN",
        publication_use=False,
        novelty_basis={"search_date": "d", "search_protocol": "p",
                       "closest_literature": ["x"], "delta": "d"},
        gates={n: "open" for n in GATE_NAMES},
    )
    assert validate_claim(c) == []


def test_publication_fail_closed() -> None:
    battery = _card()["result"]["publication_mutation_battery"]
    assert battery["rejected"] == battery["total"] == 100
    # cannot skip the ladder
    assert not can_transition("OPEN", "VALIDATED")
    assert not can_transition("EVIDENCE_READY", "VALIDATED")


def test_named_kills_all_caught() -> None:
    kb = _card()["result"]["kill_battery"]
    assert all(kb.values())


def test_promote_never_changes_novelty_and_validated_needs_receipt() -> None:
    c = _base_validated()
    before = c.novelty_tier_external
    promote(c, "VALIDATED")
    assert c.novelty_tier_external == before
    # remove the independent receipt -> VALIDATED refused
    c2 = _base_validated()
    c2.adjudication_receipts = ()
    try:
        promote(c2, "VALIDATED")
        raised = False
    except DualAxisError:
        raised = True
    assert raised


def test_card_byte_stable_under_check() -> None:
    proc = subprocess.run(
        [str(REPO / "venv/bin/python"), "-B",
         str(REPO / "scripts/codex_harness/run_pr185_dual_axis.py"), "--check"],
        cwd=REPO, capture_output=True, text=True, timeout=300,
        env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True and payload["read_only"] is True
