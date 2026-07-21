"""Gates for the rolling claim-adjudication harness."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
for e in (str(REPO/"htt"), str(REPO/"htt"/"src")):
    if e not in sys.path: sys.path.insert(0, e)
from common.claim_adjudication_harness import FAMILIES, classify, PROVENANCE_OVERRIDES  # noqa: E402
LEDGER = REPO/"docs/generated/claim_adjudication/adjudication_ledger.json"

def test_significance_is_ranking_not_a_gate():
    f = FAMILIES[0]
    complete = {"significance":"marginal","novelty_tier":"K","completeness":"complete",
                "verification":"verified","provenance_status":"cited_correct",
                "blocker_class":"independence_only","verdict_survives":True}
    a = classify(f, complete)
    assert a.unlock_status == "PROMOTABLE_ON_SINGLE_INDEPENDENCE_ADJUDICATION"

def test_incomplete_blocks_promotion():
    f = FAMILIES[0]
    partial = {"significance":"substantial","novelty_tier":"S","completeness":"partial",
               "verification":"verified","provenance_status":"cited_correct",
               "blocker_class":"independence_only","verdict_survives":True}
    assert classify(f, partial).unlock_status == "GENUINELY_INCOMPLETE"

def test_independence_never_fake_passed():
    l = json.loads(LEDGER.read_text())
    assert l["policy"]["independence_gate_never_fake_passed"] is True
    # no family is marked VALIDATED/public — the strongest status is promotable
    assert "VALIDATED" not in l["counts_by_unlock_status"]

def test_native_and_data_blockers_are_hard():
    l = json.loads(LEDGER.read_text())
    assert "D-DESI" in l["families_by_unlock_status"].get("BLOCKED_ON_DATA_PR151", [])
    assert set(l["families_by_unlock_status"].get("BLOCKED_ON_NATIVE_SOLVER", [])) >= {"II-NATIVE"}

def test_provenance_overrides_documented():
    assert set(PROVENANCE_OVERRIDES) == {"T-EGS", "D-CF4"}
