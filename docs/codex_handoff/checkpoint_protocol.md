# Five-PR checkpoint protocol

Run after every five completed PRs.

1. Validate DAG.
2. Generate progress report.
3. Compute percent complete by total PR count, child-count weighted DAG proxy,
   and completed nodes on the script-selected longest dependency path.
4. List failed tests, skipped PRs, and repeated blockers. Skipped PRs must not
   increase completed counts or satisfy dependencies.
5. Ask: has the last five PRs produced new user-visible or reviewer-visible capability? If not, write an adversarial replan entry and do a replan PR.
6. Spawn or simulate three auditors: skeptical maintainer, physics/statistics reviewer, harness/reproducibility reviewer.
7. Close all completed subagent threads before continuing.

A checkpoint must produce `docs/generated/progress_checkpoints/checkpoint_<N>.md`.
Once written and committed, `checkpoint_<N>.md` is an immutable snapshot of
that completed count. A later DAG intake may change the total and percentages,
but it must not overwrite the historical checkpoint; the live scoreboard
records the new denominator until the next five-completion checkpoint.
The writer reuses an existing checkpoint only when the rendered bytes are
identical and otherwise fails rather than overwriting it. Every checkpoint and
live scoreboard carries owner/scope/claim/transfer/config/input/sky/null,
caveat, generating-command, and Git/worktree metadata.
Each progress run may also refresh
`docs/generated/progress_checkpoints/progress_scoreboard.md` with the current
blocked, skipped, dormant-external, unblocked-next, checkpoint, and replan
state. Dormant external cards and terminal negative receipts never increase
the completed count. A terminal negative receipt satisfies only an explicit
`requires_terminal_receipt` aggregation edge, never `requires_success`.
The checkpoint metrics are DAG bookkeeping only, not scientific validation,
solver readiness, transfer calibration, null/covariance adequacy, morphology
compatibility, or Bianchi family-identification evidence.
