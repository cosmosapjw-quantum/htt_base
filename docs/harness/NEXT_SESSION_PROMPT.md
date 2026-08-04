# Next Session Prompt

PR-279 is canonically closed in the isolated worktree
`/home/cosmosapjw/worktrees/htt-pr279-retrace-20260804` on branch
`changeset/pr279-reverse-trace-invalidation`.

## Authority and current state

- Base and verified PR-278 merge:
  `1b0e4200ab4dd487909a8519d7808e81ad4b9169`.
- Canonical DAG: 241 valid cards, 174 completed, 36 pending, two terminal
  blocked, 28 dormant, no foreground card, and PR-151 background-only.
- Completion is 72.20%; dependency-weighted completion is 75.55%; critical
  path completion is 98.70%.
- PR-280 is the sole dependency-ready next node, but it must not start until
  the exact PR-279 delivery is reviewed and merged by the owner.
- Active PR-279 authority:
  `docs/research_program/post_pr275/pr279_spec.yaml`.
- The owner authorized one content commit, one closeout commit, and one final
  non-draft review PR. Approval, merge, force-push, ruleset mutation, data
  execution, capability promotion, and scientific public release remain
  unauthorized.

## Closed result

- Internal work-unit retrace: 222 historical rows exactly once and 19
  prospective rows in a separate section.
- GitHub publication/review index: 366 rows in a separate identity space.
- Lifecycle graph: 12 roots, 58 typed nodes, and 212 PR-277
  recalibration/reexecution edges; the theorem-registry root is dormant.
- Supersession: five typed edges; the PR-248/PR-252 exact-hash contradiction is
  explicitly withheld rather than rewritten.
- Data artifacts: 45 groups split 20 `REDO_REQUIRED`, 14 `REDO_UPGRADE`, five
  `PRESERVE`, and six `BLOCKED`.
- Failure debt and runbooks: 13 rows and seven lanes; zero admitted,
  authorized, or executed data lanes.
- Scientific status remains `OPEN_UNCHANGED`; public use is false. PR-279
  issues no `ClaimCapabilityDecision`, posterior/evidence result, native
  result, or Bianchi-family claim.

## Preserved review chronology

1. Mutable implementation review ended with a 30/30 terminal mutation PASS;
   it is pre-commit evidence only.
2. Exact content commit `404c4907...`, tree `e6c02f55...`, and seal
   `0a8c560e...` entered immutable review.
3. The first reviewer exposed prior PR-279 result paths during search, stopped
   immediately, and wrote `error/not_examined` coverage. It is not acceptance.
4. A fresh clean-room reviewer passed all 23 policy cells, all eight policy
   commands, and 23/23 temporary-copy mutations. Result `9633ded5...`,
   coverage `9e94a8f7...`, and oracle `911a78f5...` are strict-valid.

## Delivery continuation

The closeout commit changes canonical status, generated projections, and
handoff bytes. Seal and independently review the exact two-commit candidate,
rehearse it against the latest target, collect a fresh open-PR inventory, and
create exactly one non-draft review PR through the attended publisher. If that
PR already exists, do not recreate or mutate it: wait for owner review/merge.
After merge, verify remote ancestry and start PR-280 from a fresh isolated
worktree.

## Required verification

```bash
python -B scripts/codex_harness/run_pr279_reverse_trace.py check
python -B scripts/codex_harness/run_pr279_reverse_trace.py focused
python scripts/codex_harness/validate_pr_dag.py \
  docs/codex_handoff/pr_backlog.yaml \
  --status docs/codex_handoff/pr_status.yaml \
  --strict-rescue-slice
python scripts/codex_harness/sync_pr_dag_mirrors.py --check
python -B scripts/codex_harness/run_pr279_reverse_trace.py collect
python -B scripts/codex_harness/run_pr279_reverse_trace.py smoke
python scripts/check_claim_language.py
python scripts/claim_lint_research_surfaces.py
```

## Hard stops

- Any missing, duplicated, conflated, orphaned, or unknown PR/artifact/route.
- Any mutation of historical source text, receipt, or preserved failure.
- Any lifecycle edge outside the exact 12-root index or preserved artifact
  carrying an active invalidation root.
- Any admission/execution collapse, MIO posterior/evidence ownership, native
  promotion of external transfer, or pre-native family identification.
- Any direct push/PR command outside the single attended transaction.
