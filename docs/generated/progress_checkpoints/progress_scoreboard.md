# Progress scoreboard

## Artifact metadata

- Owner: `COMMON`
- Implementation scope: `common`
- Claim tier: `diagnostic_only`
- Transfer source: `none`
- Config hash: `fffae7c53c7f2090dd140c3bf168071a785a92bbcdd261e8e6529bbf7ae4d271`
- Sky support / mask status: `not_applicable_governance`
- Covariance / null mock status: `not_applicable_governance`
- Generating command: `/usr/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json`
- Git commit / worktree state: `06083de0b575e19aada5d56ef10fb043f654faf2; dirty`
- Input hashes:
  - `docs/codex_handoff/pr_backlog.yaml:256cf1406cddf271d8b197dbf39e1ae1486b18f22c30e4551de40b55e2cc502d`
  - `docs/codex_handoff/pr_status.yaml:d1fef99858c2080e5c0c78509d21fa98498b1dd598d679897a07e6c1e4d873c8`
- Caveats:
  - Progress percentages count DAG bookkeeping only.
  - This artifact cannot establish scientific readiness, native transfer validation, posterior support, or family identification.

- Completed PRs: 109/130 = 83.85%
- Dependency-weighted completion: 90.25%
- Critical path completion: 50/56 = 89.29%
- Critical path: PR-000 -> PR-003 -> PR-004 -> PR-010 -> PR-014 -> PR-050 -> PR-051 -> PR-052 -> PR-053 -> PR-054 -> PR-055 -> PR-060 -> PR-061 -> PR-062 -> PR-063 -> PR-064 -> PR-065 -> PR-066 -> PR-111 -> PR-114 -> PR-115 -> PR-116 -> PR-117 -> PR-118 -> PR-119 -> PR-121 -> PR-122 -> PR-123 -> PR-124 -> PR-125 -> PR-126 -> PR-127 -> PR-128 -> PR-131 -> PR-132 -> PR-133 -> PR-134 -> PR-135 -> PR-137 -> PR-138 -> PR-139 -> PR-140 -> PR-141 -> PR-142 -> PR-143 -> PR-144 -> PR-145 -> PR-146 -> PR-147 -> PR-148 -> PR-155 -> PR-162 -> PR-163 -> PR-164 -> PR-165 -> PR-166
- Blocked PRs: PR-172
- Skipped PRs: none
- Dormant external PRs: PR-159, PR-160, PR-161, PR-162, PR-163, PR-164, PR-165, PR-166, PR-183
- Foreground in progress: none
- Background in progress: PR-151
- Unblocked next: none
- Hypothesis-only unblocked (not auto-scheduled): PR-174, PR-182
- Checkpoint due: no
- Next checkpoint at: 110
- Replan required: no
- Replan reason: checkpoint not due

Progress percentages count DAG bookkeeping only and are not scientific readiness evidence.
They do not validate native solver behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null calibration, morphology compatibility, or Bianchi family identification.
