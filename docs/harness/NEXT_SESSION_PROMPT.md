# Next Session Prompt

Continue PR-277 in the isolated worktree
`/home/cosmosapjw/worktrees/htt-pr277-capability-engine-20260803` on branch
`changeset/pr277-evidence-conditioned-capability`.

## Authority and current state

- Base: merged remote HEAD `a6d3bd8b24e15727fbb6011c515d66d49cd4ba92`.
- PR-190 remains terminal `COMPLETED_FAILED_WITH_RECEIPT`; do not relabel it
  success or reopen PR-191/PR-205 success edges.
- PR-276 is merged and canonically complete.
- PR-277 is canonical `in_progress`; PR-278 and later nodes remain blocked on
  its successful closeout.
- Canonical DAG: 241 cards, 171 completed, 38 pending, 2 blocked, 28 dormant,
  and PR-151 background-only.
- Governing spec:
  `docs/research_program/post_pr275/pr277_spec.yaml`.
- The owner authorized exactly one PR-277 content commit, one closeout commit,
  and one attended non-draft review PR on 2026-08-04. The exact sealed-SHA
  branch push is permitted only inside that single PR-creation transaction.
  Force-push, approval, merge, ruleset mutation, data execution, capability
  promotion, and scientific public release remain unauthorized.

## Current implementation

- `ClaimCapabilityDecision` is factory-only and derives readiness, semantics,
  identification, provenance, allowed use, ceiling, and `granted` from exact
  evidence/adjudication inputs.
- The claim node binds capability, action, outcome, and ceiling inside the
  content-addressed evidence graph; cross-capability relabelling fails closed.
- Versioned theorem/data/mask/covariance/transfer/estimand identities preserve
  terminal history and exact supersession.
- Graph invalidation, recalibration, and reexecution edges automatically
  generate capability-scoped blockers even when the caller supplies none.
- Artifact-gate compatibility annotations cannot set readiness, claim tier,
  allowed use, production validation, manuscript use, or native status.
- Pre-native family identification and all data/publication capabilities remain
  blocked.

## Preserved review chronology

1. `pr277-prefreeze-review-20260803`: claim FAIL on capability relabelling and
   caller-omittable lifecycle blockers; regression FAIL on incomplete mapping
   coverage. Preserve both results.
2. `pr277-repair-review-20260803`: claim PASS on both repairs; regression found
   no runtime blocker but identified incomplete exact owner-set coverage.
3. The subsequent test-only repair executes all 55 capability/owner pairs.
4. Immutable content R1 preserved an exact claim PASS but could not form a
   valid aggregate because its second reviewer profile was not read-only.
5. Immutable content R2 preserved a claim PASS and a blocking physics/harness
   counterexample: the raw builder could fabricate granted pre-native family
   capability. The builder/token surfaces are removed.
6. Immutable content R3 preserved an exact claim PASS, but its other tool turn
   produced no registered result envelope; the abandoned run is not aggregate
   acceptance.
7. Immutable content R4 preserved a claim PASS and a blocking physics/harness
   counterexample: `object.__new__` plus copied fields could emit valid-looking
   pre-native family and MIO-owned inference records.
8. Immutable content R5 was bound to SHA `3be8d16e...` and seal `45793595...`.
   Both reviewers independently found the public-issuer closure marker before
   later broad prior-run searches invalidated blind-results. The run is
   abandoned, has no valid result envelopes, and is not acceptance evidence.
9. The current repair gives the public issuer no closure marker, binds direct
   registration to the exact issuer frame, and revalidates all trust-bearing
   fields from exact evidence on every public use. Registration alone cannot
   validate a relabelled record. The content history slot is amended in place;
   fresh exact review remains required.

## Required continuation

1. Verify live target ancestry and confirm the user main checkout/untracked
   inputs remain untouched.
2. Confirm the authorized content history still contains exactly one amended
   commit named `PR-277: Add evidence-conditioned capability engine`.
3. Rebuild shared context, seal the exact amended commit, and run registered
   blind claim/harness review against immutable bytes. Re-run the preserved
   R4/R5 oracles as negative controls. Do not count mutable or abandoned
   reviews as acceptance.
4. Address any concrete finding by amending/resealing; preserve every failed
   receipt.
5. Only after immutable PASS, mark PR-277 complete, regenerate status/handoff
   surfaces, create the separate closeout commit if required by the delivery
   policy, and perform latest-target integration.
6. Use the registered attended publisher exactly once to push the sealed SHA
   and create one non-draft review PR. Do not approve or merge it.

## Required commands

```bash
python scripts/codex_harness/run_pr277_capability_engine.py focused
python scripts/codex_harness/validate_pr_dag.py \
  docs/codex_handoff/pr_backlog.yaml \
  --status docs/codex_handoff/pr_status.yaml \
  --strict-rescue-slice
python scripts/codex_harness/sync_pr_dag_mirrors.py --check
python scripts/codex_harness/run_pr277_capability_engine.py collect
python scripts/codex_harness/run_pr277_capability_engine.py smoke
python scripts/check_claim_language.py
python scripts/claim_lint_research_surfaces.py
```

## Hard stops

- Do not grant a capability from completed status or caller readiness fields.
- Do not permit capability/action/outcome relabelling after adjudication.
- Do not omit or manually clear graph-derived lifecycle blockers.
- Do not modify historical PR-172/184/190 receipts or the frozen PR-270 CAS
  adjudication.
- Do not admit or execute a data lane without its separate human receipts.
- Do not claim native solver/atlas validation or Bianchi-family identification.
