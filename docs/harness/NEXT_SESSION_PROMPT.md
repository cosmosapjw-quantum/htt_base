# Next Session Prompt

Verify the PR-276 delivery closeout in the isolated worktree
`/home/cosmosapjw/worktrees/htt-post-pr275-pr276-20260803` on branch
`changeset/pr276-ssot-chronology-reconciliation`.

## Authority and current state

- Base: merged remote HEAD `1f11d0df0f55b80439585cf56afef55e9d38599a`.
- PR-190: terminal `COMPLETED_FAILED_WITH_RECEIPT`; do not relabel it success.
- PR-276: canonically complete after immutable content R2 passed on exact
  content commit `3fa98dc3...`.
- Canonical DAG: 241 cards, 171 completed, 39 pending, 2 blocked, 28 dormant,
  PR-151 background-only.
- Governing spec: `docs/research_program/post_pr275/pr276_spec.yaml`.
- After reproducing policy drift, the owner authorized one additional named
  corrective commit and one final review-PR transaction. The transaction may
  internally push only the sealed SHA required to create that PR. GitHub
  ruleset change, force-push, approval, merge, data download, archive unpacking,
  observed execution, and any additional publication action remain unauthorized.

## Required continuation

1. Confirm the worktree still descends from `1f11d0df...` and that the main
   user checkout/untracked inputs remain untouched.
2. Preserve failed R1/R2/R4/R5 receipts, the byte-superseded R3 mutable PASS,
   the bounded R6 pre-freeze PASS, and failed immutable content review R1; none
   may be relabelled.
3. Rebuild `.agent-harness/generated/CONTEXT_PACK.md` before any subagent.
4. Confirm final history contains the preserved content and closeout commits,
   `PR-276: Restore attended PR delivery`, and the adversarially required
   nonce-ledger binding and frozen-ledger repairs. Preserve both failed replay
   review receipts.
5. Verify the corrected candidate through the latest seal, registered
   harness/claim review, and latest-target integration receipt.
6. Query the live remote ref and PR inventory. If both are absent, issue a
   current-turn `attended_explicit_user` authorization and invoke only the
   policy-registered `attended_pr_publisher.py` exactly once. The nonce ledger
   must be created during authorization issuance and its frozen filesystem
   identity must come from the HMAC-signed authorization; the publisher
   exposes no ledger override. If the branch or
   PR already matches the sealed authorization, verify rather than duplicate
   it. Any mismatched remote state is a hard stop.
7. Begin PR-277 only in a new delivery cycle after the PR-276 remote boundary
   is verified.

## Required commands

```bash
python scripts/codex_harness/validate_pr_dag.py \
  docs/codex_handoff/pr_backlog.yaml \
  --status docs/codex_handoff/pr_status.yaml \
  --strict-rescue-slice
python scripts/codex_harness/sync_pr_dag_mirrors.py --check
python scripts/codex_harness/progress_report.py \
  docs/codex_handoff/pr_backlog.yaml \
  docs/codex_handoff/pr_status.yaml --checkpoint-every 5
python scripts/codex_harness/run_pr276_reconciliation.py focused
python scripts/codex_harness/run_pr276_reconciliation.py collect
python scripts/codex_harness/run_pr276_reconciliation.py smoke
python scripts/check_claim_language.py
python scripts/claim_lint_research_surfaces.py
```

## Hard stops

- Do not relax PR-191 or PR-205's PR-190 success edge.
- Do not modify historical PR-172/184/190 proof receipts or move/reseal the
  frozen PR-270 CAS adjudication.
- Do not invent G9-G12.
- Do not auto-promote scalar x_C into typed state.
- Do not admit or execute any data lane without its separate human receipt.
- Do not claim native solver/atlas validation or Bianchi-family identification.
