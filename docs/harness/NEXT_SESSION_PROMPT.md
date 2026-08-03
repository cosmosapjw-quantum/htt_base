# Next Session Prompt

PR-278 is canonically closed in the isolated worktree
`/home/cosmosapjw/worktrees/htt-pr278-tier-a-adjudication-20260804` on branch
`changeset/pr278-tier-a-per-lane-adjudication`.

## Authority and current state

- Base and verified PR-277 merge: `a7800430660c5a4bd532d8655fc63df03b21496e`.
- Canonical DAG: 241 valid cards, 173 completed, no foreground card, 37
  pending, 2 terminal blocked, 28 dormant, and PR-151 background-only.
- PR-279 is the sole dependency-ready next node, but it must not start until
  the exact PR-278 delivery is reviewed and merged by the owner.
- Active PR-278 authority:
  `docs/research_program/post_pr275/tier_a_adjudication/pr278_delivery_spec_v2.yaml`.
- The predecessor `pr278_spec.yaml` and v1 policy are closed-panel inputs. Do
  not rewrite them; closed assignments bind their exact bytes.
- The owner authorized one content history slot, one closeout commit, and one
  final non-draft review PR. Approval, merge, force-push, ruleset mutation,
  data execution, capability promotion, and scientific public release remain
  unauthorized.

## Closed result

- Frozen source: 28 family rows, 20 candidates, 19 independently reviewable,
  T-OMK held for PR-192, and eight event-gated families.
- Exact dual-axis terminal-receipt crosswalks: zero of 62. All 62 rows remain
  individually `INCONCLUSIVE`.
- Family ledger: 14 `GRANT`, 12 `HOLD`, D-ACT `DOWNGRADE`, and D-K1
  `INCONCLUSIVE`.
- `GRANT` means only exact-receipt admissibility for later PR-157. It grants no
  `ClaimCapabilityDecision`, readiness, scientific status, CF4 P0 rescue,
  public use, native status, posterior/evidence result, or family identity.
- Scientific status is `OPEN_UNCHANGED`; public use is false.

## Preserved review chronology

1. Source mapper `pr278-evidence-map-r2-20260804` found zero exact crosswalks
   for all 62 dual-axis rows.
2. The first three blind family panels produced 19 rows. The original
   data/method result is preserved but superseded because it omitted reviewer
   and author principals.
3. Pre-freeze run `pr278-prefreeze-review-r1-20260804` failed on the stale v1
   delivery-policy pointer and synthesized reviewer identity. Both strict-valid
   failures are preserved; do not vote them away.
4. Remediation run `pr278-principal-remediation-r1-20260804` independently
   re-adjudicated exactly the six affected rows. Its strict-valid result binds
   exact reviewer/author principals.
5. Immutable content R1 failed on exact commit `f5e2ff7a...`: `check-source`
   read live status against its frozen base hash. Its strict result and normally
   closed run preserve the blocker.
6. The amended content resolves historical inputs from Git snapshot
   `a780043...`, carries a compact self-addressed mapper receipt, and requires
   `check-source`. Immutable content R2 passed all 21 policy cells on exact
   content commit `34ec32aa...`, seal `35fae6bf...`, result `c5ddc511...`, and
   normally closed run summary `2fed1a5e...`.

## Delivery continuation

This handoff is intentionally frozen before the owner-authorized attended
delivery transaction. If no PR exists, seal and independently review the exact
two-commit candidate, rehearse it against the latest target, bind a fresh open-
PR inventory, and create exactly one non-draft review PR through the attended
publisher. If that PR already exists, do not recreate or mutate it: wait for
owner review/merge. After merge, verify remote ancestry and begin PR-279 from a
fresh isolated worktree.

## Required verification

```bash
python -B scripts/codex_harness/run_pr278_tier_a_adjudication.py probe
python -B scripts/codex_harness/run_pr278_tier_a_adjudication.py verify-frozen-source
python -B scripts/codex_harness/run_pr278_tier_a_adjudication.py check-source
python -B scripts/codex_harness/run_pr278_tier_a_adjudication.py verify-panel
python -B scripts/codex_harness/run_pr278_tier_a_adjudication.py verify-ledger
python -B scripts/codex_harness/run_pr278_tier_a_adjudication.py focused
python scripts/codex_harness/validate_pr_dag.py \
  docs/codex_handoff/pr_backlog.yaml \
  --status docs/codex_handoff/pr_status.yaml \
  --strict-rescue-slice
python scripts/codex_harness/sync_pr_dag_mirrors.py --check
python -B scripts/codex_harness/run_pr278_tier_a_adjudication.py collect
python -B scripts/codex_harness/run_pr278_tier_a_adjudication.py smoke
python scripts/check_claim_language.py
python scripts/claim_lint_research_surfaces.py
```

## Hard stops

- Missing, synthesized, assignment-mismatched, or author-equal reviewer
  principal.
- Missing or drifted source/receipt identity, invented dual-axis crosswalk, or
  bulk verdict.
- Any event-gated family promotion, nonzero CF4 P0 rescue, or PR-157 boundary
  bypass.
- Any capability/readiness/status/public-use effect from a lane disposition.
- Any native-solver, native-atlas, MIO posterior/evidence, or Bianchi-family
  identification claim.
