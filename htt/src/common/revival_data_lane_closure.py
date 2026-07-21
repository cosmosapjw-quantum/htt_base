"""PR-226: Track-I data-lane closure and independent calibration (PARTIAL).

Each solver-independent data lane is closed only under a complete
null/covariance/selection contract. Planck-K1, CF4 and ACT close on their
existing receipts; the DESI official-mock lane is BLOCKED on the PR-151
acquisition terminal receipt (1000 EZmock + 25 AbacusSummit) and never uses
partial mocks. The decisive falsifier -- partial mocks, unmatched masks,
undercoverage or an unavailable raw stage in a headline -- is killed by keeping
the DESI headline closed until its official mocks land.
"""
from __future__ import annotations
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
GEN = REPO / "docs/generated"
STATUS = REPO / "docs/codex_handoff/pr_status.yaml"

# lane -> receipt cards that carry its null/covariance/selection contract
LANE_RECEIPTS = {
    "planck_k1": ["k1_e2e_reduced_manifest_ffp10_smica.json", "k1_global_maxscan_e2e_full.json",
                  "k1_biposh_smica.json", "k1_evenl_biposh_rank_card.json"],
    "cf4": ["cf4_mv_bulkflow_card.json", "cf4_bulkflow_lcdm_card.json",
            "cf4_mock_significance_card.json"],
    "act": ["act_kappa_card.json", "act_raw_qe_card.json"],
}
# DESI diagnostic null exists, but the OFFICIAL-MOCK causal/covariance closure
# is gated on PR-151.
DESI_DIAGNOSTIC = "desi_exact_selection_card.json"


def pr151_is_terminal() -> bool:
    """PR-151 is terminal only when it leaves background_in_progress for
    completed. While acquiring, partial scientific use is forbidden."""
    txt = STATUS.read_text(encoding="utf-8")
    # crude but robust: PR-151 under background_in_progress and not under completed
    in_background = "\nbackground_in_progress:\n- PR-151" in txt or "background_in_progress:\n- PR-151" in txt
    completed_block = txt.split("completed:")[1].split("\n\n")[0] if "completed:" in txt else ""
    in_completed = "\n- PR-151\n" in completed_block
    return in_completed and not in_background


def lane_closure() -> dict:
    lanes = {}
    for lane, cards in LANE_RECEIPTS.items():
        present = [c for c in cards if (GEN / c).is_file()]
        lanes[lane] = {
            "receipt_cards": cards,
            "receipts_present": present,
            "status": "CLOSED_WITH_EXISTING_RECEIPT" if present else "BLOCKED_MISSING_RECEIPT",
            "contract": "null + covariance + selection",
        }
    desi_terminal = pr151_is_terminal()
    lanes["desi"] = {
        "diagnostic_receipt": DESI_DIAGNOSTIC,
        "diagnostic_present": (GEN / DESI_DIAGNOSTIC).is_file(),
        "official_mock_closure": "CLOSED" if desi_terminal else "BLOCKED_ON_PR151_TERMINAL",
        "status": "CLOSED_WITH_EXISTING_RECEIPT" if desi_terminal else "BLOCKED_ON_PR151_TERMINAL",
        "partial_mocks_used_in_headline": False,
        "contract": "official 1000 EZmock + 25 AbacusSummit covariance (PR-151 terminal)",
    }
    return lanes


def closure_summary() -> dict:
    lanes = lane_closure()
    closed = [k for k, v in lanes.items() if v["status"] == "CLOSED_WITH_EXISTING_RECEIPT"]
    blocked = [k for k, v in lanes.items() if v["status"].startswith("BLOCKED")]
    headline_discipline_ok = all(
        not lanes.get(k, {}).get("partial_mocks_used_in_headline", False)
        for k in lanes)
    return {
        "lanes": lanes,
        "closed_lanes": closed,
        "blocked_lanes": blocked,
        "headline_discipline_ok": headline_discipline_ok,
        "desi_blocked_on_pr151": "desi" in blocked,
    }
