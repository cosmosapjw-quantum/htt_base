# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base` with no foreground
PR while PR-151 remains the sole background acquisition.

Read first:

- `AGENTS.md`
- `.agent-harness/generated/CONTEXT_PACK.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/PR_DELTAS/pr-176.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`

## Current state

- Active DAG: 130 cards, 109 completed (83.85%), dependency-weighted 90.25%,
  critical-path proxy 50/56 (89.29%). These are bookkeeping metrics only.
- PR-176 is complete at `NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE`. Its affine
  coefficients are candidate diagnostics only; the separate frozen covariance
  self-consistency axis failed. No q/significance or accepted physical
  divergence measurement exists.
- PR-172 is terminal failed-with-receipt. PR-180 remains locked because its
  required-success edge is unsatisfied.
- PR-151 closing PR-176 probe: 160/1000 EZmocks, 0/25 Abacus, 10/15 audit
  members, 40 growing partials / 11,443,806,784 bytes, fresh log, 810.65 GiB
  free, sole acquisition lock PID 16695. It is non-terminal and must not be
  finalized or used scientifically yet.
- There is no foreground defensible PR. PR-174/175/182 remain hypothesis-only;
  PR-178 waits for terminal PR-151 and PR-155--158; PR-181 remains covariance
  deferred; PR-183 remains native-dependent.
- Canonical checkpoint 110 is not yet due at 109 completions. Do not rewrite
  the historical 108-card planned-sequence checkpoint as a canonical one.
- Planck PR3 raw data remain retained. Do not delete them before PR4 receipt
  preparation. PR4 simulations remain externally unavailable and no PR4 data
  analysis is authorized.

## Immediate action: monitor PR-151 only

Run the read-only fast probe at session start/end, around commands longer than
30 minutes, and every 30 minutes during long work:

```bash
python scripts/codex_harness/pr151_progress.py --compact
```

The probe inspects records, `.part` growth, log freshness, writer lock, and
free space. It must not full-rehash payloads. Suspect a stall only after two
probes at least 15 minutes apart show zero growth in both log and partial
bytes. Identify tmux, the phase-owner PID, and aria children before any
restart; never start a duplicate writer and never delete `.part` files.

Do not start an NVMe-heavy job below 300 GiB free; below 200 GiB, defer all new
large jobs. Preserve the active DESI acquisition over ACT or other competing
I/O. Preserve the retained Planck raw ensemble.

## PR-151 terminal and switching rule

PR-151 is terminal-eligible only when all conditions hold:

- 1,000 EZmocks and 25 Abacus mocks authenticated;
- observed-data authentication complete;
- 10 EZmock plus 5 Abacus random-index audits complete;
- final full payload rehash succeeds;
- producer write/check and runner write/check succeed.

Partial mocks never enter a rank, p-value, covariance, or significance. When
the fast probe first reports acquisition-ready, run `finalize`, not legacy
`all`, and preserve the exact target plus existing partial state. After the
terminal receipt is complete, execute PR-155 -> PR-156 -> PR-157 -> PR-158
atomically under the normal per-PR evidence/review/commit loop. Only then
consider PR-178.

## Closed/deferred lanes

- Do not auto-schedule PR-174, PR-175, or PR-182; they are hypothesis-only.
- Do not execute PR-180 through PR-172's failed required-success edge.
- Do not execute PR-181 until PR-155/PR-143 covariance closure is identified.
- Keep PR-159--166 and PR-183 dormant until authenticated native delivery.
- Do not implement or simulate the external native low-ell solver.
- Do not infer family identification from scalar, covariance, BiPoSH, axis, or
  catalogue diagnostics.
- Do not promote CF4 catalogue coefficients into physical fields or treat
  structural distinction as leakage immunity.

## Immediate verification

```bash
python scripts/codex_harness/pr151_progress.py --compact
venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check
venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
env PYTHONHASHSEED=0 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=htt:htt/src venv/bin/python -B scripts/codex_harness/run_pr176_affine_divergence.py --check
python scripts/check_claim_language.py --dry-run --format json docs/PR_DELTAS/pr-176.md docs/generated/pr176_result_card.json docs/generated/pr176_cross_falsifier_result.json
```
