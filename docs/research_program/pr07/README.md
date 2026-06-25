# PR07 Audit-Repair Programme

Folded execution of the 2026-06-25 PR04 adversarial audit
(`pr07_research_repair_execution_pack`, **MAJOR_REVISIONS**). The pack's harness
and CoVe protocol are mapped onto this repo's own agents/skills and modules; see
`AGENT_SKILL_MAP.md`.

## Map

- `PR_LIST.md` — the step-by-step PR list (P0..P3) with landed/blocked status.
- `AGENT_SKILL_MAP.md` — CoVe lanes → `.claude` agents + `htt-*` skills + the
  concise chain-of-checks schema.
- `BLOCKER_RESOLUTION_MATRIX.md` — finding → resolution → exit gate → status.
- `CLAIM_GATES.md` — what is allowed / requires Wolfram / requires data tickets /
  requires the native solver / always forbidden.
- `DEPENDENCY_SCHEDULE.md` — execution order.
- `PAPER_FREEZE_PR07_007_008.md` — PAPER-A/B freeze exit notes.
- `PR08-005_2MRS_CROSS_RECONSTRUCTION_CONTRACT.md` — independent cross-check spec.
- `WEB_CRAG_LEDGER.md` + `web_sources.json` — literature/novelty boundaries.
- `pr_registry.yaml` + `tickets/` — machine-readable DAG + blocked tickets.

## Run

```bash
make pr04-gates          # 23 regression gates + forbidden-deps + proofs
make pr07-gates          # 16 portable repair gates (real modules)
make pr07-wolfram        # local Wolfram/xAct symbolic gate (engine required)
python scripts/run_pr07_experiments.py && python scripts/cove_verify_pr07.py
pytest tests/contracts/test_pr07_audit_repair.py
```

Landed: PR07-001..006 + PR08-002 mechanics (rev-r116). Pending: PR07-007/008
paper freezes. Blocked (registered codes): PR08-001/003/004/006. Separate
project: PR10-001..006.
