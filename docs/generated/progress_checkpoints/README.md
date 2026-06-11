# Progress Checkpoints

This directory stores generated five-PR checkpoint artifacts from
`scripts/codex_harness/progress_report.py`.

Generate a checkpoint from the repository root:

```bash
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints
```

Files are named `checkpoint_<N>.md`, where `<N>` is the zero-padded completed
PR-card count at the checkpoint, for example `checkpoint_005.md`.

Each checkpoint starts with a machine-readable metadata comment:

```text
<!-- checkpoint_meta {"completed": 5, "percent_complete": 8.06, ...} -->
```

The metadata is used only for later checkpoint comparison. If a later
checkpoint repeats the same completed count and percent complete, the generated
artifact marks `Replan required: yes` and includes an adversarial replan entry.

These artifacts are DAG bookkeeping evidence only. They are not scientific
validation, native solver readiness, transfer calibration, HTT posterior or
evidence validation, MIO diagnostic certification, null calibration, morphology
compatibility, or Bianchi family-identification evidence.
