#!/usr/bin/env python3
"""Consolidated open-items ledger (REV-R180, post-v9 cycle).

Single dev-tier document ranking EVERY unfinished research item and every
external-audit item answered only by registration, ordered by earliest
executability. Sources: the egs3 ticket yamls, THEOREM_REGISTRY.yaml, and
BLOCKERS.md. Fail-closed: each cited ticket must exist and its on-disk
``state`` must match this builder's snapshot (drift = build error, so a
ticket-state change forces a ledger regeneration); every blocker code must
appear in BLOCKERS.md or in the cited ticket.

This is a DEV-tier planning artifact (process content allowed). It is NOT a
report artifact and is never rendered into any external-audit report.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from theorem_registry_v9_lib import load_registry, validate_registry  # noqa: E402

TICKET_DIR = REPO / "docs/research_program/egs3/tickets"
BLOCKERS_MD = REPO / "docs/research_program/BLOCKERS.md"
OUT_JSON = REPO / "docs/generated/open_items_ledger.json"
OUT_MD = REPO / "docs/research_program/OPEN_ITEMS_LEDGER.md"

GENERATED_AT = "2026-07-11"  # static: --check byte-stability

# executability vocabulary:
#   now           -- executable immediately, no external dependency
#   decision_only -- compute done or not required; waits on an explicit
#                    owner/user decision
#   blocked       -- waits on external data, access, or ownership
OPEN_ITEMS = [
    {
        "rank": 1,
        "item": "King-Ellis rotating-congruence rederivation (10-item program)",
        "source": "review R1 3.4 (2026-07-10); ticket EGS3-T3-king-ellis; "
                  "registry T3-full/T3-int reclassification (v9)",
        "ticket": "t3_king_ellis.yaml",
        "ticket_state": "constraint_witness_reclassified_lower_w2_withdrawn_"
                        "dynamics_deferred",
        "blocker": None,
        "executability": "now",
        "exit_gate": "items 1-10 discharged as dual-engine (SymPy + Wolfram) "
                     "seals: tilted-frame kinematics/constraints "
                     "(king_ellis_frame_seal) + conservation/evolution/local "
                     "development (king_ellis_dynamics_seal); ticket carries "
                     "per-item dispositions",
        "note": "pure symbolic GR + numerics; BV-DYN (REV-R178) supplies the "
                "dynamical integrator machinery. EXECUTING this cycle "
                "(REV-R179..R183).",
    },
    {
        "rank": 2,
        "item": "Anisotropic-Omega_k higher-order vorticity/curvature "
                "re-opening transfer (finite ceiling)",
        "source": "ticket EGS3-K5-omega-k-higher-order-ceiling (exit branch 1; "
                  "branch 2 executed as documented null, REV-R162)",
        "ticket": "k5_omega_k_higher_order_ceiling.yaml",
        "ticket_state": "blocked_on_higher_order_transfer",
        "blocker": "BLOCKED_HIGHER_ORDER_VORTICITY_CURVATURE_REOPENING",
        "executability": "now",
        "exit_gate": "registered higher-order Omega_k transfer producing a "
                     "finite anisotropic-curvature ceiling, emitted as a NEW "
                     "card artifact (frozen cards untouched)",
        "note": "substantial GR-transfer compute item, no external data; "
                "next candidate cycle after item 1.",
    },
    {
        "rank": 3,
        "item": "MES registry re-freeze decision (coefficient-branch "
                "promotion)",
        "source": "ticket EGS3-G8-mes-full-rederivation "
                  "(branch_registry_v9_2026_07_10); MES-BR seal (v9)",
        "ticket": "mes_full_rederivation.yaml",
        "ticket_state": "discrepancy_documented",
        "blocker": None,
        "executability": "decision_only",
        "exit_gate": "explicit owner sign-off selecting a coefficient branch; "
                     "then a re-freeze cycle with a new W2_max anchor",
        "note": "all compute done (3-branch registry, 3 labeled ceilings, "
                "eps1 attribution triple); registered values stay frozen "
                "until sign-off.",
    },
    {
        "rank": 4,
        "item": "Paper-A/B/C split of the audit-report material",
        "source": "registered plan (v9 report; user decision 2026-07-10: "
                  "plan-only this cycle)",
        "ticket": None,
        "ticket_state": None,
        "blocker": None,
        "executability": "decision_only",
        "exit_gate": "user instruction to execute the split",
        "note": None,
    },
    {
        "rank": 5,
        "item": "K1 E2E-systematics null + BipoSH E2E upgrade",
        "source": "ticket EGS3-C1-k1-ffp10-npipe; BLOCKERS.md section 1",
        "ticket": "k1_ffp10_npipe.yaml",
        "ticket_state": "blocked",
        "blocker": "BLOCKED_MISSING_PR4_E2E_ACCESS",
        "executability": "blocked",
        "exit_gate": "PLA FFP10/NPIPE E2E ensembles on disk (download in "
                     "flight, ~1TB); then the registered max-scan/global-p "
                     "mechanics run unchanged",
        "note": "PLA/PL3 downloads in progress (2026-07-11).",
    },
    {
        "rank": 6,
        "item": "K6 Hoffman-Ribak constrained-realization vorticity posterior",
        "source": "ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 2",
        "ticket": "cf4_wfcr.yaml",
        "ticket_state": "blocked",
        "blocker": "BLOCKED_MISSING_FIELD_REALIZATIONS",
        "executability": "blocked",
        "exit_gate": "owned CR ensemble over the CF4 3D WF field",
        "note": "WF mean-field curl-suppression no-go already established.",
    },
    {
        "rank": 7,
        "item": "K5 cosmic-variance coverage on release mocks",
        "source": "ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 3",
        "ticket": "cf4_wfcr.yaml",
        "ticket_state": "blocked",
        "blocker": "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
        "executability": "blocked",
        "exit_gate": "ownership of the CF4 release-mock pipeline "
                     "(selection/Malmquist/grouping/correlated field)",
        "note": "conditional coverage (fixed LCDM sigma_cv prior) already "
                "measured.",
    },
    {
        "rank": 8,
        "item": "PR08-006 joint posterior artifact",
        "source": "BLOCKERS.md section 4",
        "ticket": None,
        "ticket_state": None,
        "blocker": "BLOCKED_UPSTREAM",
        "executability": "blocked",
        "exit_gate": "close K1+K5+K6 first (items 5-7); then assemble with "
                     "explicit measured/partial/fail-closed sectors",
        "note": None,
    },
    {
        "rank": 9,
        "item": "Native low-ell Bianchi solver atlas (theory-g CMB likelihood)",
        "source": "BLOCKERS.md section 5; PR10 project",
        "ticket": None,
        "ticket_state": None,
        "blocker": "AWAITING_NATIVE_LOWELL_SOLVER",
        "executability": "blocked",
        "exit_gate": "PR10-scale separate solver project; fail-closed "
                     "OutOfScopeError firewall stays until then",
        "note": None,
    },
    {
        "rank": 10,
        "item": "MESb (PRD 51, 5942) internal rederivation",
        "source": "ticket EGS3-G8-mes-full-rederivation (remaining)",
        "ticket": "mes_full_rederivation.yaml",
        "ticket_state": "discrepancy_documented",
        "blocker": "BLOCKED_MISSING_MESb_PRINT_ONLY_PAPER_II",
        "executability": "blocked",
        "exit_gate": "legitimate access to the print-only journal PDF; then "
                     "the existing rederivation machinery applies",
        "note": "print-only (no arXiv/ADS/OA copy); SAG-1997 discrepancy "
                "already documented.",
    },
]

# tickets whose obligations are closed/held (represented for completeness)
CLOSED_TICKETS = [
    {"ticket": "gf_interval_latent_quotient_bug.yaml",
     "ticket_state": "resolved_in_successor_and_iff_retracted_superseded_by_"
                     "T2G",
     "note": "closed by the v8 successor + v9 T2G retraction cycle"},
    {"ticket": "psd_cone_redesign.yaml",
     "ticket_state": "reviewed_fixes_applied_behind_graded",
     "note": "representation-only redesign, shipped behind the graded "
             "comparator; dual review signed off (v8-update)"},
    {"ticket": "teff_representative_nonclaims.yaml",
     "ticket_state": "registered_nonclaims",
     "note": "future obligations discharged in the v8-update cycle; the "
             "nonclaims registration itself is the steady state"},
]


def _ticket_state_on_disk(name: str) -> str:
    # NOT yaml.safe_load: several tickets carry free prose with bare colons
    # (legal for human readers, not for a strict YAML parser)
    text = (TICKET_DIR / name).read_text()
    match = re.search(r"^state:\s*(\S+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else "<no-state-line>"


def _validate() -> list[str]:
    issues: list[str] = []
    registry = load_registry()
    issues += validate_registry(registry)

    blockers_text = BLOCKERS_MD.read_text()
    on_disk = {p.name for p in TICKET_DIR.glob("*.yaml")}
    cited = {row["ticket"] for row in OPEN_ITEMS + CLOSED_TICKETS
             if row.get("ticket")}
    for missing in sorted(on_disk - cited):
        issues.append(f"ticket not represented in ledger: {missing}")
    for ghost in sorted(cited - on_disk):
        issues.append(f"ledger cites nonexistent ticket: {ghost}")

    for row in OPEN_ITEMS + CLOSED_TICKETS:
        name = row.get("ticket")
        if not name or name not in on_disk:
            continue
        state = _ticket_state_on_disk(name)
        if state != row["ticket_state"]:
            issues.append(f"{name}: state drift (disk={state!r} vs "
                          f"ledger={row['ticket_state']!r})")
        code = row.get("blocker")
        if code and code not in blockers_text and \
                code not in (TICKET_DIR / name).read_text():
            issues.append(f"{name}: blocker code {code} unknown")
    for row in OPEN_ITEMS:
        if not row.get("ticket") and row.get("blocker") and \
                row["blocker"] not in blockers_text:
            issues.append(f"rank {row['rank']}: blocker code "
                          f"{row['blocker']} not in BLOCKERS.md")

    planned = [e["id"] for e in registry.get("entries", [])
               if e.get("status") == "PLANNED"]
    return issues + ([] if not planned else
                     [f"PLANNED registry entries not ranked: {planned}"]
                     if not any(p in json.dumps(OPEN_ITEMS) for p in planned)
                     else [])


def _payload() -> dict:
    issues = _validate()
    if issues:
        raise SystemExit("open-items ledger validation failed:\n  "
                         + "\n  ".join(issues))
    return {
        "schema": "htt.research_program.open_items_ledger.v1",
        "generated_at": GENERATED_AT,
        "tier": "DEV",
        "not_a_report_artifact": True,
        "sources": ["docs/research_program/egs3/tickets/*.yaml",
                    "docs/research_program/THEOREM_REGISTRY.yaml",
                    "docs/research_program/BLOCKERS.md"],
        "executability_vocabulary": {
            "now": "executable immediately, no external dependency",
            "decision_only": "waits on an explicit owner/user decision",
            "blocked": "waits on external data, access, or ownership",
        },
        "open_items": OPEN_ITEMS,
        "closed_or_held_tickets": CLOSED_TICKETS,
    }


def _markdown(payload: dict) -> str:
    lines = [
        "# Open-items ledger — every unfinished research item, ranked by "
        "earliest executability",
        "",
        f"_Generated {payload['generated_at']} by "
        "`scripts/build_open_items_ledger.py` (dev-tier planning artifact; "
        "never rendered into any report). Fail-closed against ticket-state "
        "drift._",
        "",
        "| # | Item | Source | State | Blocker | Executability | Exit gate |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in payload["open_items"]:
        lines.append(
            f"| {row['rank']} | {row['item']} | {row['source']} "
            f"| {row['ticket_state'] or '—'} | {row['blocker'] or '—'} "
            f"| **{row['executability']}** | {row['exit_gate']} |")
    lines += ["", "## Notes", ""]
    for row in payload["open_items"]:
        if row.get("note"):
            lines.append(f"- **{row['rank']}.** {row['note']}")
    lines += ["", "## Closed / held tickets (represented for completeness)",
              ""]
    for row in payload["closed_or_held_tickets"]:
        lines.append(f"- `{row['ticket']}` — state `{row['ticket_state']}`: "
                     f"{row['note']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    payload = _payload()
    exp_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    exp_md = _markdown(payload)
    if args.check:
        stale = [str(p) for p, c in ((OUT_JSON, exp_json), (OUT_MD, exp_md))
                 if not p.exists() or p.read_text() != c]
        if stale:
            print("stale open-items ledger:\n  " + "\n  ".join(stale),
                  file=sys.stderr)
            return 1
        print("open-items ledger current")
        return 0
    OUT_JSON.write_text(exp_json)
    OUT_MD.write_text(exp_md)
    print(f"wrote {OUT_JSON}\nwrote {OUT_MD} "
          f"({len(payload['open_items'])} open items)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
