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
from scripts.codex_harness import run_pr185_dual_axis as runner  # noqa: E402

CARD = REPO / "docs/generated/pr185_result_card.json"
LEDGER = REPO / "docs/generated/dual_axis_claim_ledger.json"
SPEC = REPO / "docs/research_program/strengthening/pr185_spec.yaml"
RUNNER = REPO / "scripts/codex_harness/run_pr185_dual_axis.py"


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


def test_self_issued_receipt_cannot_validate() -> None:
    c = _base_validated()
    before = c.novelty_tier_external
    try:
        promote(c, "VALIDATED")
        raised = False
    except DualAxisError:
        raised = True
    assert raised
    assert c.novelty_tier_external == before
    assert c.readiness_state == "ADJUDICATION_PENDING"
    # Removing even the diagnostic receipt remains refused.
    c2 = _base_validated()
    c2.adjudication_receipts = ()
    try:
        promote(c2, "VALIDATED")
        raised = False
    except DualAxisError:
        raised = True
    assert raised


def test_direct_validated_state_requires_authenticated_receipt() -> None:
    c = _base_validated()
    c.readiness_state = "VALIDATED"
    errors = validate_claim(c)
    assert any("signed independent receipt" in error for error in errors)


def test_historical_card_preserves_pre_review_terminal() -> None:
    assert _card()["terminal"] == "DUAL_AXIS_SSOT_EVIDENCE_READY_INDEPENDENCE_OPEN"


def test_current_check_blocks_without_authenticated_verifier() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "--check"],
        cwd=REPO, capture_output=True, text=True, timeout=300,
        env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False and payload["read_only"] is True
    assert payload["terminal"] == "BLOCKED_AUTHENTICATED_RECEIPT_UNAVAILABLE"


def test_write_refuses_to_overwrite_historical_outputs() -> None:
    before_card = hashlib.sha256(CARD.read_bytes()).hexdigest()
    before_ledger = hashlib.sha256(LEDGER.read_bytes()).hexdigest()
    proc = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "--write"],
        cwd=REPO, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 2
    assert "refusing to overwrite" in proc.stderr
    assert hashlib.sha256(CARD.read_bytes()).hexdigest() == before_card
    assert hashlib.sha256(LEDGER.read_bytes()).hexdigest() == before_ledger
