# Read first — PR-406 hardening overlay

This overlay is stacked on the live PR-406 head
`179ae4216082ca9b6c685f5bdba6bb269a0e273a` (tree
`1a3d61c8c5e44d130f2b3b01a1091bac1f426db3`) and does not modify a canonical
DAG file. The supplied audit package originally inspected
`3ffa49ab3edfcbad63ebce4aabed48c70f70684d`; its findings were revalidated
against the later self-review commit before this overlay was published.

Use these files as the controlling execution surface:

```text
docs/research_program/theory_promotion/audits/PR405_POST_EXECUTION_ADVERSARIAL_AUDIT.md
docs/research_program/theory_promotion/audits/PR406_PLAN_DIFFERENTIAL_AUDIT.md
docs/codex_handoff/theory_promotion_reconciliation/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/theory_promotion_reconciliation/AUDIT_COMPILED_EXEC_PLAN.yaml
docs/codex_handoff/THEORY_PROMOTION_RECONCILIATION_CODEX_HANDOFF.md
```

Where PR-406 and this overlay differ, the stricter fail-closed rule controls:

1. separate truth/evidence/replay/release fields;
2. append-only multi-work-unit implementation rather than one mega-PR;
3. typed Lean probability semantics or explicit arithmetic-only downgrade;
4. one content-bound fixture across CAS axes;
5. permanent separate regressions for PR-197/210/216/222/223;
6. no canonical PR number before a live DAG reread and generator allocation.

Do not execute either plan until PR-405 and all serial predecessors required by
the live DAG have exact terminal receipts.
