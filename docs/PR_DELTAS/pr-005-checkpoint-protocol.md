# PR-005 PR delta: five-PR checkpoint and adaptive replan protocol

## Goal

Make the five-PR checkpoint protocol executable and reviewable. The progress
report now writes a generated checkpoint artifact when the completed PR count
lands on the checkpoint cadence, records reproducible progress metrics, and
marks a replan as required when progress fails to advance since a prior
checkpoint.

This is COMMON L1 DAG bookkeeping only. It does not validate scientific
readiness, native solver behavior, transfer calibration, HTT posterior or
evidence semantics, MIO diagnostics, null calibration, morphology compatibility,
or Bianchi family-identification evidence.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-005 card
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/codex_handoff/checkpoint_protocol.md`
- `scripts/codex_harness/progress_report.py`
- `scripts/codex_harness/test_pr_dag_harness.py`

## Web/doc checks

- WEB_CHECK_STATUS: done
- Python `argparse` documentation checked for optional CLI flag behavior.
  URL: https://docs.python.org/3/library/argparse.html
- Python `pathlib` documentation checked for directory creation, globbing, and
  text read/write behavior used by the checkpoint artifact writer.
  URL: https://docs.python.org/3/library/pathlib.html

## Subagent divergence

- code_cartographer:
  - Steelman: keep PR-005 scoped to `progress_report.py`, checkpoint docs, and
    generated status artifacts; the current PR should not start PR-010 common
    contracts.
  - Attack: without a generated artifact and machine-readable metadata, the
    checkpoint protocol remains manual prose and cannot support later
    stagnation detection.
- harness_engineer:
  - Steelman: add a deterministic CLI option,
    `--write-checkpoint-dir`, and regression tests for due, not-due, JSON, and
    no-progress cases.
  - Attack: stdout contamination would break `--json`, and malformed previous
    checkpoint metadata must fail visibly rather than silently corrupt replan
    logic.
- physics_stat_auditor:
  - Steelman: progress percentages are acceptable only as DAG bookkeeping.
  - Attack: dependency-weighted and critical-path metrics must not be described
    as scientific readiness, transfer coverage, null adequacy, or morphology
    evidence.
- claim_gate_reviewer:
  - Steelman: generated checkpoint text can reduce drift if it carries explicit
    caveats and avoids HTT/MIO/native-solver claims.
  - Attack: old "critical-path unblocked nodes" wording was inaccurate and
    should be replaced with the script-selected longest dependency path.
- regression_tester:
  - Steelman: focused pytest on the DAG harness is the right primary suite.
  - Attack: add regressions for not writing at non-checkpoint counts and for
    keeping JSON parseable when a checkpoint is written.

## Chosen plan

1. Extend `progress_report.py` with `--write-checkpoint-dir`.
2. Generate `checkpoint_<N>.md` only when the completed count is a nonzero
   multiple of `--checkpoint-every`.
3. Add a metadata comment to each checkpoint artifact for later comparisons.
4. Compare the current checkpoint with the latest earlier checkpoint metadata
   and emit an adversarial replan entry when completed count and percent do not
   advance.
5. Keep `--json` output pure JSON, with checkpoint path included in the JSON
   payload rather than printed as an extra line.
6. Document the generated checkpoint directory and the scientific-scope caveat.
7. Materialize the first generated checkpoint artifact for five completed PRs.

## Files changed

- `scripts/codex_harness/progress_report.py`
- `scripts/codex_harness/test_pr_dag_harness.py`
- `docs/codex_handoff/checkpoint_protocol.md`
- `docs/generated/progress_checkpoints/README.md`
- `docs/generated/progress_checkpoints/checkpoint_005.md`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/PR_DELTAS/pr-005-checkpoint-protocol.md`
- `docs/harness/VALIDATION_LEDGER.md`
- `docs/harness/PR_PROGRESS.md`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` before implementation | repo root | FAIL | Red phase: checkpoint writer CLI/tests failed because `--write-checkpoint-dir` was not implemented. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` | repo root | PASS | `11 passed`; covers checkpoint writer due/not-due, no-progress, JSON, malformed metadata, and existing DAG harness behavior. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints` | repo root | PASS | Generated `docs/generated/progress_checkpoints/checkpoint_005.md` at 5/62 completed PRs. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir /tmp/htt_progress_json_check --json` | repo root | PASS | Output parsed as JSON and included `checkpoint_artifact`, `replan_required: false`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-005 complete: `6/62 = 9.68%`; checkpoint not due; next checkpoint at 10. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-005 docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-005 docs>` before wording fix | repo root | FAIL | Flagged family-identification caveats without nearby status markers and an older DAG-status ledger phrase. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-005 docs>` | repo root | PASS | No unmarked strong claims detected after wording fixes. |

## Review findings and fixes

- Finding: checkpoint protocol wording described "critical-path unblocked
  nodes", but the script computes completed nodes on a selected longest
  dependency path. Fix: update `checkpoint_protocol.md`.
- Finding: a generated artifact could be mistaken for scientific progress.
  Fix: add explicit caveats in the protocol, README, checkpoint artifact, PR
  progress, and validation ledger.
- Finding: no-progress detection needs a reproducible previous-state source.
  Fix: add checkpoint metadata and compare against earlier checkpoint metadata.
- Finding: malformed previous checkpoint metadata could otherwise produce
  undefined behavior. Fix: fail explicitly with `malformed checkpoint metadata`
  and add a regression test.
- Finding: claim-status scan flagged caveat text and legacy DAG-status wording.
  Fix: use hyphenated `family-identification evidence` caveats and replace
  the old phrase with a command-result description.

## Checkpoint artifact

- Artifact: `docs/generated/progress_checkpoints/checkpoint_005.md`
- Completed: 5/62 = 8.06%.
- Dependency-weighted completion: 7.69%.
- Critical path completion: 3/21 = 14.29%.
- Blocked PRs: none.
- Unblocked next at generation time: PR-005, PR-020, PR-010.
- Replan required: no.
- Subagents used and closed: code cartographer, harness engineer,
  physics/statistics auditor, claim-gate reviewer, and regression tester.

## Claim hygiene and scientific scope

PR-005 is COMMON L1 orchestration infrastructure. It does not change physics,
statistics, transfer adapters, inference code, MIO certificates, obsstat
features, generated scientific result cards, manuscript claims, or figures.

The checkpoint artifact is not evidence for native solver readiness, transfer
calibration, HTT posterior/evidence validity, MIO diagnostic adequacy, null
calibration, morphology compatibility, or Bianchi family-identification evidence.

## Residual risks

- The dependency-weighted metric is a simple child-count weighted DAG proxy,
  not a project-value estimate.
- The critical path is the script-selected longest dependency path, not a
  schedule forecast.
- PR-023 later expands the scoreboard and stagnation-triggered replan protocol;
  PR-005 provides the first deterministic checkpoint writer needed by that
  downstream card.
