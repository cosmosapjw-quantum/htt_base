# Next Session Prompt

Verify the PR-277 delivery closeout in the isolated worktree
`/home/cosmosapjw/worktrees/htt-pr277-capability-engine-20260803` on branch
`changeset/pr277-evidence-conditioned-capability`.

## Authority and current state

- Base: merged remote HEAD `a6d3bd8b24e15727fbb6011c515d66d49cd4ba92`.
- PR-190 remains terminal `COMPLETED_FAILED_WITH_RECEIPT`; do not relabel it
  success or reopen PR-191/PR-205 success edges.
- PR-276 is merged and canonically complete.
- PR-277 is canonical `COMPLETED_SUCCESS` after exact content R6 passed;
  PR-278 is the sole dependency-ready next card but waits for owner review and
  merge of this delivery.
- Canonical DAG: 241 cards, 172 completed, 38 pending, 2 blocked, 28 dormant,
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
   validate a relabelled record. The content history slot is amended in place.
10. Exact content R6 passed all 19 cells on `a19d98e5...` and seal
    `73df6790...`. Its 54-check independent oracle, 111 capability tests, 308
    focused tests, collection, smoke, DAG, mirrors, context, claim scans, and
    diff integrity passed with no blocker. The normally closed run summary is
    the canonical content-review receipt.
11. A premature main-coordinator zero-result merge attempt is preserved as
    `PREMATURE_ZERO_RESULT_MERGE.json`; it is process-error evidence only. The
    valid aggregate was generated after the reviewer envelope and must not be
    conflated with that attempt.

## Required continuation

1. Verify live target ancestry and confirm the user main checkout/untracked
   inputs remain untouched.
2. Confirm history contains exactly the content commit
   `PR-277: Add evidence-conditioned capability engine` and the closeout commit
   `PR-277: Close evidence-conditioned capability delivery`; do not add a
   third commit.
3. Rebuild shared context, seal the exact two-commit closeout candidate, and
   consume only the owner-authorized final-review rereview exception for one
   registered read-only reviewer. Require all 19 cells, closeout/status/mirror
   checks, and exact candidate integrity.
4. Create and verify latest-target integration plus a fresh open-PR inventory.
   Any target drift, overlap, or failed required command is a hard stop.
5. Bind the exact title/body, seal, final review, integration, inventory, and a
   fresh one-use external nonce to the attended authorization.
6. Use the registered attended publisher exactly once to push the sealed SHA
   and create one non-draft review PR. Do not approve or merge it. If the
   transaction is partial, inspect its receipt and remote state before any
   further action; never retry blindly.

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
