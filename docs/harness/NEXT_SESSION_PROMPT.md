# Next Session Prompt

Continue PR-278 in the isolated worktree
`/home/cosmosapjw/worktrees/htt-pr278-tier-a-adjudication-20260804` on branch
`changeset/pr278-tier-a-per-lane-adjudication`.

## Authority and current state

- Base and verified PR-277 merge: `a7800430660c5a4bd532d8655fc63df03b21496e`.
- Canonical DAG: 241 valid cards, 172 completed, PR-278 in progress, 37
  pending, 2 terminal blocked, 28 dormant, and PR-151 background-only.
- Active delivery authority:
  `docs/research_program/post_pr275/tier_a_adjudication/pr278_delivery_spec_v2.yaml`.
- The predecessor `pr278_spec.yaml` and v1 policy are closed-panel inputs. Do
  not rewrite them; closed assignments bind their exact bytes.
- The owner authorized one content history slot, one closeout commit, and one
  final non-draft review PR. Push is allowed only inside that single attended
  transaction. Approval, merge, force-push, ruleset mutation, data execution,
  capability promotion, and scientific public release remain unauthorized.

## Current result

- Frozen source: 28 family rows, 20 candidates, 19 independently reviewable,
  T-OMK held for PR-192, and eight event-gated families.
- Exact dual-axis terminal-receipt crosswalks: zero of 62. All 62 rows remain
  individually `INCONCLUSIVE`.
- Family ledger: 14 `GRANT`, 12 `HOLD`, D-ACT `DOWNGRADE`, and D-K1
  `INCONCLUSIVE`.
- `GRANT` means only exact-receipt admissibility for later PR-157. It grants no
  `ClaimCapabilityDecision`, readiness, scientific status, CF4 P0 rescue,
  public use, native status, posterior/evidence result, or family identity.
- The frozen source resolves changed backlog/status paths through Git snapshot
  commit `a780043...` plus exact blob hashes; never reinterpret live bytes as
  the old evidence.

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
   re-adjudicated exactly the six affected rows. Result SHA
   `13ef70783b74f4fe3520d604be234ca62e1ac05c2d02651015337a889c655a49`
   is strict-valid and binds exact reviewer/author principals.
5. Complete repaired pre-freeze review result `1578b8f7...` passed. Immutable
   content R1 then failed on exact commit `f5e2ff7a...`: `check-source` read
   live status against its frozen base hash. Strict result `aef9ad24...` and
   coverage `13f3027f...` preserve the blocker. The current repair resolves
   DAG sources from Git snapshot `a780043...`, promotes mapper result identity
   into a tracked compact receipt, and adds `check-source` to policy/tests.

## Required continuation

1. Run the complete repaired validation set below.
2. Amend the authorized content slot in place, verify the branch remains one
   PR-278 commit ahead, and create a fresh candidate seal.
3. Register a new exact-content blind review. Preserve any finding and do not
   use R1 or majority vote as acceptance.
4. Only after a PASS, mark PR-278 complete, synchronize mirrors/generated
   status/handoffs, and use the one separate closeout commit.
5. Seal and review the exact two-commit candidate, rehearse against the latest
   target, inventory open PRs, then use the single attended review-PR
   transaction. Do not merge or approve it.

## Required commands

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
