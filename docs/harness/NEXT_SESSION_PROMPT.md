# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base` at foreground PR-176
while PR-151 remains the sole background acquisition.

Read first:

- `AGENTS.md`
- `.agent-harness/generated/CONTEXT_PACK.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-local-global-discrimination/SKILL.md`
- `.agents/skills/htt-statistical-hardening/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/PR_DELTAS/pr-179.md`
- `docs/generated/progress_checkpoints/checkpoint_110_execution_sequence.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`

## Current state

- Active DAG: 130 cards, 108 completed (83.08%), dependency-weighted 90.04%,
  critical-path proxy 50/56 (89.29%). These are bookkeeping metrics only.
- PR-172 is terminal failed-with-receipt. PR-180 remains locked because its
  required-success edge is unsatisfied.
- PR-179 is complete at `H_ONLY_SELECTION_SYSTEMATICS_CONDITIONAL`. q is
  withheld; the `2/20000` H-only matched-null rank is supporting
  selection/systematics-conditional catalogue evidence only.
- PR-151 closing probe: 150/1000 EZmocks, 0/25 Abacus, 10/15 audit members,
  28 growing partials / 7,803,000,192 bytes, fresh log, 815.38 GiB free, sole
  acquisition lock PID 16695. It is non-terminal and must not be finalized or
  used scientifically yet.
- PR-176 is the single foreground PR. PR-174/175/182 remain hypothesis-only;
  PR-178 waits for terminal PR-151 and PR-155--158; PR-181 remains covariance
  deferred; PR-183 remains native-dependent.
- Planck PR3 raw data remain retained. Do not delete them before PR4 receipt
  preparation. PR4 simulations remain externally unavailable.

## PR-176 objective and hard terminal

Implement only the registered conservative-dependence channel falsifier using
PR-146, PR-148, and PR-173 authorities. Before PR-155 supplies an identified
joint covariance, do not multiply channel likelihoods or assume independence.
Use a conservative dependence bound, report channel-specific falsifiers, and
terminate `non_informative` if the admissible dependence envelope cannot
separate the alternatives. A null/upper bound/non-identification result is a
valid reproducible terminal.

Freeze conventions, inputs, estimand, dependence bound, null, thresholds, and
falsifiers before inspecting a result. Build the shared context pack before
spawning; register the four required roles; keep one main production writer;
run targeted and smoke tests, claim scan, exact artifact replay, scientific
validation, and adversarial review before commit and status transition.

## PR-151 switching rule

Probe PR-151 at PR-176 start/end, around commands over 30 minutes, and every 30
minutes during long work. Fast probes inspect records and `.part`/log growth;
do not full-rehash. Suspect a stall only after two probes at least 15 minutes
apart show zero growth in both log and partial bytes. Never start a duplicate
writer.

If PR-151 becomes terminal during PR-176, finish the atomic PR-176 result,
review, and commit first. Then stop opening new advocate PRs, finalize PR-151,
and run PR-155--158 before resuming the advocate queue. Terminal means all
1000 EZmocks, 25 Abacus mocks, observed authentication, 15 audits, full rehash,
and producer/runner write/check receipts.

## Hard scientific boundaries

- Do not implement or simulate the external native low-ell solver.
- Do not relabel external/AniCLASS/proxy transfer output as native.
- Do not infer family identification from scalar, covariance, BiPoSH, axis, or
  catalogue diagnostics.
- Keep MIO diagnostic certificates separate from HTT posterior/evidence.
- Do not promote H_cat/q_cat catalogue labels into physical fields.
- Do not use PR-151 partial mocks or infer a PR4 result.
- Preserve the known `fig_current_dag_progress.png` binary-pin regression as a
  visible pre-existing failure; do not suppress it inside PR-176.

## Immediate verification

```bash
python scripts/codex_harness/pr151_progress.py --compact
venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check
venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
python scripts/check_claim_language.py --dry-run --format json docs/PR_DELTAS/pr-179.md docs/generated/pr179_result_card.json
```
