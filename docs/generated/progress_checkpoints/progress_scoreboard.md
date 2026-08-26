# Progress scoreboard

## Artifact metadata

- Owner: `COMMON`
- Implementation scope: `common`
- Claim tier: `diagnostic_only`
- Transfer source: `none`
- Config hash: `0719fdbb5fa7ff6f050895e57734ea569d97d5a82f5df389c4cbfa818b681fe0`
- Sky support / mask status: `not_applicable_governance`
- Covariance / null mock status: `not_applicable_governance`
- Generating command: `/usr/bin/python3 scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints --write-scoreboard docs/generated/progress_checkpoints/progress_scoreboard.md`
- Git commit / worktree state: `e938756120bb084e28a678bb0fcd733a4a6158e5; dirty`
- Input hashes:
  - `docs/codex_handoff/pr_backlog.yaml:20c7c1ffe6328c09677222ad519f1075853a9a8a907a3d731f9e7f09eb65c9c6`
  - `docs/codex_handoff/pr_status.yaml:e23dc0e0ec5ce6691e29110c26a055069178cf456c227f28739ffb7f7ae149ba`
- Caveats:
  - Progress percentages count DAG bookkeeping only.
  - This artifact cannot establish scientific readiness, native transfer validation, posterior support, or family identification.

- Completed PRs: 205/273 = 75.09%
- Dependency-weighted completion: 80.28%
- Critical path completion: 75/81 = 92.59%
- Critical path: PR-000 -> PR-003 -> PR-004 -> PR-010 -> PR-014 -> PR-050 -> PR-051 -> PR-052 -> PR-053 -> PR-054 -> PR-055 -> PR-060 -> PR-061 -> PR-062 -> PR-063 -> PR-064 -> PR-065 -> PR-066 -> PR-111 -> PR-114 -> PR-115 -> PR-116 -> PR-117 -> PR-118 -> PR-119 -> PR-121 -> PR-122 -> PR-123 -> PR-124 -> PR-125 -> PR-126 -> PR-127 -> PR-128 -> PR-131 -> PR-132 -> PR-133 -> PR-134 -> PR-135 -> PR-137 -> PR-138 -> PR-139 -> PR-140 -> PR-141 -> PR-142 -> PR-143 -> PR-153 -> PR-154 -> PR-167 -> PR-172 -> PR-184 -> PR-185 -> PR-186 -> PR-187 -> PR-188 -> PR-189 -> PR-249 -> PR-190 -> PR-276 -> PR-277 -> PR-278 -> PR-279 -> PR-280 -> PR-295 -> PR-288 -> PR-299 -> PR-300 -> PR-302 -> PR-303 -> PR-304 -> PR-305 -> PR-306 -> PR-313 -> PR-308 -> PR-309 -> PR-310 -> PR-311 -> PR-317 -> PR-318 -> PR-319 -> PR-320 -> PR-321
- Blocked PRs: PR-172, PR-190, PR-280, PR-307, PR-312
- Skipped PRs: none
- Dormant external PRs: PR-159, PR-160, PR-161, PR-183, PR-229, PR-230, PR-231, PR-232, PR-233, PR-234, PR-235, PR-236, PR-237, PR-238, PR-239, PR-240, PR-241, PR-242, PR-243, PR-244, PR-245, PR-246, PR-162, PR-163, PR-164, PR-165, PR-166, PR-196
- Foreground in progress: PR-327
- Background in progress: PR-151
- Unblocked next: PR-301, PR-204, PR-292, PR-293, PR-319, PR-328
- Hypothesis-only unblocked (not auto-scheduled): none
- Checkpoint due: yes; satisfied by docs/generated/progress_checkpoints/checkpoint_205.md
- Next checkpoint at: 210
- Replan required: no
- Replan reason: progress advanced; no replan required

Progress percentages count DAG bookkeeping only and are not scientific readiness evidence.
They do not validate native solver behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null calibration, morphology compatibility, or Bianchi family identification.
