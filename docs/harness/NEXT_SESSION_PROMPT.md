# Next Session Prompt

Verify or continue after the PR-258 open-set response-class change-set from the
isolated branch `changeset/pr258-open-set-integration`. Do not move, checkout,
clean, restart, or consume the canonical PR-151 acquisition path.

Read first:

- `AGENTS.md`
- `.agent-harness/generated/CONTEXT_PACK.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `.agents/skills/htt-statistical-hardening/SKILL.md`
- `.agents/skills/htt-family-identification-gate/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `docs/research_program/premise_anchor/pr258_spec.yaml`
- `docs/research_program/premise_anchor/pr258_publication_policy.json`
- `docs/research_program/STAT_FOUNDATIONS_JUSTIFICATION_20260728.md`
- `docs/PR_DELTAS/pr-258.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`

## Current state

- Baseline target:
  `origin/research/pr04-multicomponent@d62d63de6fdae1fbaf595ccce52b3abf532899e5`
  (merged GitHub PR #365 / internal PR-257).
- Internal work unit `PR-258`, change-set
  `CS-PR258-OPEN-SET-INTEGRATION`, publication group
  `PG-PR258-OPEN-SET-INTEGRATION`.
- Active DAG before PR-258 merge: 152/205 complete = 74.15%,
  dependency-weighted 80.72%, critical-path proxy 85.71%. PR-258 remains
  pending; PR-151 is background acquisition and PR-172 is blocked.
- The candidate adds finite analytic/synthetic response-class supports,
  covariance-supported squared-distance equivalence components, explicit
  dimensionless correlation-null residuals distinct from exact zero-variance
  structural constraints and supported nuisance orbits, exact class-contract
  binding, PR-256-derived source-separation gates bound to exact observable,
  covariance, nuisance, provider/response and transfer identities, open-set
  abstention, typed finite-support sensitivity, explicit frozen artifact
  metadata, and minimal reopening-observable reports. Future-native support
  remains schema-only at `NEEDS_NATIVE`.
- The frozen benchmark is synthetic-only with `transfer_source=none`.
  Twenty thousand held-out draws per registered cell validate only the
  declared software behavior. No observed sky, PR-151 partial data, old Rust
  science output, external/native transfer, likelihood, posterior, evidence
  term, FLRW-departure result, geometry, or family result is present.
- BC1 preserves historical `x_C` values only as legacy projections. BC2
  forbids representation-driven claim promotion. Machine claim tier remains
  `diagnostic_only`; roadmap `C2` is a separate planning level.
- Mutable-candidate validation passes 43 focused tests, 139 adjacent tests,
  isolated wheel/facade import, benchmark replay, executable oracle, claim
  scans, strict DAG/status, and legacy-reproduction TeX build. Broad
  packaging, full collection, and repo-wide no-mock failures remain recorded
  and must not be relabelled as passes.
- The post-commit sealed SHAs `9318fa1`, `b19d20e5`, `05005fc1`, and
  `80a481ee`
  failed independent review. Their accepted findings include
  nuisance/covariance-null separation, source-gate publication, metadata
  binding, status precedence, typed perturbation relations, signed-zero
  canonical identity, frozen Monte Carlo precision/cap semantics, SSOT count
  synchronization, exact structural-null unit congruence, and explicit
  owner/scope/artifact-mode/sky/null/covariance metadata, plus exact
  PR-256-to-PR-258 source-gate provenance binding. All old seals are
  invalidated; historical FAIL or provisional verdicts are not readiness
  evidence.

## Authority boundary

The owner authorized one commit and one push for this coherent PR-258 branch.
That authority does not include PR creation, approval, merge, branch deletion,
target mutation, or PR-258 completion. The exact pushed commit is authoritative
only if its candidate seal, registered read-only review, and latest-target
integration receipt all bind the same target, tree, diff, and changed-file set.

Before continuing:

1. verify the remote branch tip equals the exact candidate SHA in the seal;
2. verify the current registered review result and executable coverage;
3. verify latest-target integration against the same target and candidate;
4. verify no tracked or untracked candidate byte changed after sealing;
5. if PR-258 has not been human-reviewed and merged, stop without starting the
   next external GitHub PR;
6. after a human merge and head-branch deletion, update PR-258 to completed in
   a new change-set, rerun the DAG/progress tools, and select the next card
   from current dependencies rather than this historical prompt.

## Immediate verification

```bash
PYTHONPATH=htt/src:htt python -B scripts/codex_harness/run_pr258_integration.py focused
PYTHONPATH=htt/src:htt python -B scripts/codex_harness/run_pr258_integration.py benchmark
PYTHONPATH=htt/src:htt python -B scripts/codex_harness/run_pr258_open_set_oracle.py
PYTHONPATH=htt/src:htt python -B scripts/codex_harness/run_pr258_integration.py adjacent
PYTHONPATH=htt/src:htt python -B scripts/codex_harness/run_pr258_integration.py claim
python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice
python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
git diff --check
```

## External blockers

- Latest read-only PR-151 probe: 530/1000 EZmocks, 0/25 Abacus, 10/15 audit
  members; terminal false. No acquisition process is visible despite the
  retained writer lock, and the manifest records a transient failure with
  `continue_acquire_after_restart`. Do not infer terminality or consume
  partial support.
- PR-172 remains blocked and continues to prevent a broad source-layout
  collection pass.
- PR-120 continues to block a public/current manuscript build; legacy
  reproduction is compatibility evidence only.
- No authenticated native low-ell solver or morphology atlas exists.

Do not implement a substitute solver, label external transfer as native,
promote a response class to a Bianchi family, or use a scalar/stress/morphology
diagnostic as geometry evidence.
