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
        "item": "Manuscript downstream reconciliation of the MES "
                "vorticity-ceiling correction (Saadeh-MES gap magnitude; "
                "ch09 W^2~1e-15 aside; ch04 atlas ~1e6 strip)",
        "source": "REV-R190 ch04 correction (registry MES-MESB-TRACE); "
                  "geodesic W2_max=3.3789e-13 changes the downstream numbers",
        "ticket": None,
        "ticket_state": None,
        "blocker": None,
        "executability": "now",
        "exit_gate": "recompute the Saadeh(9.01e-22)-vs-MES gap against the "
                     "geodesic W2_max=3.3789e-13 (~8-9 OOM, was quoted ~6) "
                     "and reconcile ch04 sec:atlas + ch09 Saadeh-MES gap "
                     "subsection; ch04 MES theorems already corrected",
        "note": "the refuted-value theorem correction (thm:MES-omega/udot, "
                "prop:ordering) is DONE this cycle; only the downstream "
                "gap-magnitude prose remains.",
    },
    {
        "rank": 2,
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
        "rank": 3,
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
        "rank": 4,
        "item": "K6 Hoffman-Ribak constrained-realization vorticity posterior",
        "source": "ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 2",
        "ticket": "cf4_wfcr.yaml",
        "ticket_state": "blocked",
        "blocker": "BLOCKED_MISSING_FIELD_REALIZATIONS",
        "executability": "blocked",
        "exit_gate": "the full WF residual covariance / operator for a true "
                     "Hoffman-Ribak CR ensemble; rev-r198 already quantified the "
                     "mean-field curl suppression on the real 3-D field + built a "
                     "correlated-residual CR (correlation-length-dependent)",
        "note": "REV-R198: cf4pp_vorticity_posterior.py QUANTIFIED the WF "
                "mean-field curl suppression on the REAL CF4++ 3-D field "
                "(RMS|curl|/RMS|div| = 0.009, potential flow -- the no-go "
                "confirmed) and built a CORRELATED-residual CR (upgrade over the "
                "per-cell-independent toy). The CR vorticity distribution is "
                "residual-dominated + correlation-length-dependent (14-48 "
                "(km/s)/Mpc across R=7.8-30 Mpc); a DEFINITIVE ensemble still "
                "needs the WF operator -- stays PARTIAL.",
    },
    {
        "rank": 5,
        "item": "K5 CF4 bulk-flow significance: nonlinear COLA/L-PICOLA "
                "refinement (in-house physical mock DELIVERED)",
        "source": "ticket EGS3-C2-cf4-wfcr; BLOCKERS.md section 3; registry "
                  "K5-MOCKSIG",
        "ticket": "cf4_wfcr.yaml",
        "ticket_state": "blocked",
        "blocker": "BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP",
        "executability": "blocked",
        "exit_gate": "the full nonlinear COLA/L-PICOLA survey-matched mock suite "
                     "(Qin+2021 CF4TF is request-only) to fold in nonlinear "
                     "velocity power + selection mode-coupling; the in-house "
                     "physical forward mock (rev-r197) already calibrates the "
                     "estimator and localises this residual",
        "note": "REV-R197: scripts/cf4_mock_calibrated_significance.py DELIVERS "
                "an in-house PHYSICAL forward-mock ensemble (linear GRF velocity "
                "field + super-sample mode + real per-object noise at the fixed "
                "CF4 geometry, htt/obsstat/pv_forward_mocks.py; 2000 survey-"
                "matched mocks). It reproduces the analytic linear bulk-flow "
                "covariance (mock/analytic ratio ~1) -> the estimator/geometry/"
                "noise do NOT inflate the significance; the gap to the literature "
                "~2-3 sigma is localised to nonlinear velocity power. Only the "
                "full nonlinear COLA refinement remains -- the 'no mock at all' "
                "state is discharged. (rev-r196 MV route: |B|(200)=405 km/s "
                "resolved rev-r195's withheld significance.)",
    },
    {
        "rank": 6,
        "item": "PR08-006 joint posterior artifact",
        "source": "BLOCKERS.md section 4",
        "ticket": None,
        "ticket_state": None,
        "blocker": "BLOCKED_UPSTREAM",
        "executability": "blocked",
        "exit_gate": "close K1+K5+K6 first (items 3-5); then assemble with "
                     "explicit measured/partial/fail-closed sectors",
        "note": None,
    },
    {
        "rank": 7,
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
        "rank": 8,
        "item": "DESI number-count dipole: clustering/kinematic separation "
                "(significance mock-calibrated)",
        "source": "ticket EGS3-H1-desi-number-count-dipole; registry EXT-DESI / "
                  "EXT-DESI-MOCK",
        "ticket": "desi_number_count_dipole.yaml",
        "ticket_state": "mock_calibrated_consistent_with_lcdm_clustering",
        "blocker": None,
        "executability": "blocked",
        "exit_gate": "higher-z tracers / density-cross-correlation to SEPARATE "
                     "the clustering dipole from the kinematic dipole at BGS "
                     "depths; the significance is already mock-calibrated "
                     "(rev-r198: consistent with LambdaCDM clustering)",
        "note": "REV-R192/R193: randoms downloaded, window-corrected dipole "
                "D=9.49e-3 MEASURED. REV-R198: significance MOCK-CALIBRATED "
                "(desi_dipole_mock_significance.py, an in-house LambdaCDM "
                "clustering mock) -- D is CLUSTERING-dominated (13.5 sigma above "
                "the shot-noise floor) and CONSISTENT with LambdaCDM clustering "
                "cosmic variance (p=0.90), NOT an excess; only the "
                "clustering/kinematic SEPARATION (BGS low-z) remains.",
    },
    {
        "rank": 9,
        "item": "ACT DR6 low-ell kappa isotropy: N0/N1 debias",
        "source": "ticket EGS3-H2-act-dr6-kappa-isotropy; registry EXT-ACT",
        "ticket": "act_dr6_kappa_isotropy.yaml",
        "ticket_state": "sims_downloaded_mean_field_debiased_isotropy_measured",
        "blocker": None,
        "executability": "blocked",
        "exit_gate": "a true realisation-dependent N0 (RDN0) debias needs the "
                     "quadratic-estimator pipeline / raw CMB maps -- only the "
                     "reconstructed kappa a_lm are on disk, so this is "
                     "blocked-on-QE (NOT runnable with kappa alone; the "
                     "sim-null already includes N0+N1 for the isotropy test)",
        "note": "REV-R192/R194: 400 sims downloaded; mean field subtracted; "
                "ell=2..10 debiased band power p=0.35 CONSISTENT with the "
                "isotropic sims. REV-R195 added a real 95% CL UPPER LIMIT on "
                "excess low-ell kappa power. REV-R198: confirmed the RDN0 debias "
                "is BLOCKED-on-QE -- only reconstructed kappa a_lm are available "
                "(a realisation-dependent N0 needs the QE inputs / raw CMB); the "
                "isotropy conclusion is unaffected (the sim-null handles N0+N1). "
                "Dipole ell=1 not measurable by ACT lensing.",
    },
    {
        "rank": 10,
        "item": "MESb (PRD 51, 5942) INTERNAL non-geodesic derivation "
                "(Eqs 30-36 algebra)",
        "source": "ticket EGS3-G8-mes-full-rederivation (residual)",
        "ticket": "mes_full_rederivation.yaml",
        "ticket_state": "web_traced_in_house_refuted_geodesic_readopted",
        "blocker": None,
        "executability": "blocked",
        "exit_gate": "legitimate access to the print-only journal PDF; the "
                     "accessible-range trace (REV-R190) already REFUTED the "
                     "in-house triples and re-adopted the geodesic anchor, "
                     "so only MESb's internal algebra remains",
        "note": "print-only (no arXiv/ADS/OA copy); the in-house "
                "(3/4,2,2/7)/(3/4,1,3/14) refutation + geodesic re-adoption "
                "is DONE; only MESb's own Eqs 30-36 derivation is blocked.",
    },
]

# tickets whose obligations are closed/held (represented for completeness)
CLOSED_TICKETS = [
    {"ticket": "mes_full_rederivation.yaml",
     "ticket_state": "web_traced_in_house_refuted_geodesic_readopted",
     "note": "MES re-freeze EXECUTED (REV-R187/R188, registry MES-REFREEZE: "
             "geodesic derivation attached, W2_max 1.3087e-6 -> 3.3789e-13), "
             "then WEB-TRACED + the in-house non-geodesic triples REFUTED "
             "(REV-R190, registry MES-MESB-TRACE): they appear in no "
             "accessible source and exceed the companion's own reduced bound; "
             "the geodesic anchor SURVIVED five adversarial lanes and is "
             "re-adopted; ch04 corrected. Frozen anchor byte-identical; only "
             "MESb's internal Eqs 30-36 algebra stays print-only-blocked "
             "(rank 8)"},
    {"ticket": "k5_omega_k_higher_order_ceiling.yaml",
     "ticket_state": "branch1_executed_slaving_transfer_ceilings_registered",
     "note": "exit-gate branch 1 EXECUTED (REV-R184/R185, registry "
             "OMK-REOPEN): exact curvature->shear slaving kappa = -1/(2+q) "
             "on the LRS-III/KS slaved mode; six labeled attribution x era "
             "|Delta Omega_k| ceilings on a NEW card; the certified "
             "instantaneous null untouched; frozen U_k plugin NOT modified; "
             "nothing promoted"},
    {"ticket": "t3_king_ellis.yaml",
     "ticket_state": "ten_item_program_executed_lower_w2_withdrawal_upgraded"
                     "_to_dynamical",
     "note": "the ten-item rotating-congruence program EXECUTED "
             "(REV-R181/R182, registry KE-FRAME/KE-OBS/KE-DYN): rotating "
             "perfect-fluid development exists at Omega_k>0; at Omega_k=0 "
             "doubly obstructed (momentum constraint + dynamical "
             "irrotationality) -- the lower-endpoint W^2 withdrawal is now "
             "dynamical within the group-invariant perfect-fluid class; "
             "W^2 re-attribution stays a registered interpretive question"},
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
