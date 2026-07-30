<!-- checkpoint_meta {"completed": 160, "critical_path_percent_complete": 89.61, "dependency_weighted_percent_complete": 79.54, "percent_complete": 72.07, "replan_required": false, "total": 222} -->
# Progress checkpoint 160

## Artifact metadata

- Owner: `COMMON`
- Implementation scope: `common`
- Claim tier: `diagnostic_only`
- Transfer source: `none`
- Config hash: `f2ec574a1e9a2e4126f020220a1f5f120339ac7e7df9847536edbfbd30376212`
- Sky support / mask status: `not_applicable_governance`
- Covariance / null mock status: `not_applicable_governance`
- Generating command: `/usr/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md --json`
- Git commit / worktree state: `0081f9d45fd73f8715e1f471e6206c53e7aa20d5; dirty`
- Input hashes:
  - `docs/codex_handoff/pr_backlog.yaml:49d8f09bcbab9d99adc36a51e7c32288adbd6e44da346df4a5a23b52f906cf8e`
  - `docs/codex_handoff/pr_status.yaml:3c0c0a6f8c3ffa2768898ae189672e79e689180098f390e15445be5611e23401`
- Caveats:
  - Progress percentages count DAG bookkeeping only.
  - This artifact cannot establish scientific readiness, native transfer validation, posterior support, or family identification.

- Completed PRs: 160/222 = 72.07%
- Dependency-weighted completion: 79.54%
- Critical path completion: 69/77 = 89.61%
- Critical path: PR-000 -> PR-003 -> PR-004 -> PR-010 -> PR-014 -> PR-050 -> PR-051 -> PR-052 -> PR-053 -> PR-054 -> PR-055 -> PR-060 -> PR-061 -> PR-062 -> PR-063 -> PR-064 -> PR-065 -> PR-066 -> PR-111 -> PR-114 -> PR-115 -> PR-116 -> PR-117 -> PR-118 -> PR-119 -> PR-121 -> PR-122 -> PR-123 -> PR-124 -> PR-125 -> PR-126 -> PR-127 -> PR-128 -> PR-131 -> PR-132 -> PR-133 -> PR-134 -> PR-135 -> PR-137 -> PR-138 -> PR-139 -> PR-140 -> PR-141 -> PR-142 -> PR-143 -> PR-153 -> PR-154 -> PR-167 -> PR-172 -> PR-184 -> PR-185 -> PR-186 -> PR-187 -> PR-188 -> PR-189 -> PR-200 -> PR-250 -> PR-251 -> PR-252 -> PR-253 -> PR-254 -> PR-255 -> PR-256 -> PR-258 -> PR-259 -> PR-260 -> PR-261 -> PR-262 -> PR-264 -> PR-265 -> PR-267 -> PR-268 -> PR-269 -> PR-270 -> PR-273 -> PR-274 -> PR-275
- Blocked PRs: PR-172
- Skipped PRs: none
- Dormant external PRs: PR-159, PR-160, PR-161, PR-183, PR-229, PR-230, PR-231, PR-232, PR-233, PR-234, PR-235, PR-236, PR-237, PR-238, PR-239, PR-240, PR-241, PR-242, PR-243, PR-244, PR-245, PR-246, PR-162, PR-163, PR-164, PR-165, PR-166, PR-196
- Foreground in progress: none
- Background in progress: PR-151
- Unblocked next: PR-204, PR-266, PR-190
- Hypothesis-only unblocked (not auto-scheduled): none
- Replan required: no
- Replan reason: progress advanced; no replan required

Progress percentages count DAG bookkeeping only and are not scientific readiness evidence.
They do not validate native solver behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null calibration, morphology compatibility, or Bianchi family identification.
