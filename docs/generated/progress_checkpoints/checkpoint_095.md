<!-- checkpoint_meta {"completed": 95, "critical_path_percent_complete": 89.29, "dependency_weighted_percent_complete": 88.94, "percent_complete": 84.07, "replan_required": false, "total": 113} -->
# Progress checkpoint 095

## Artifact metadata

- Owner: `COMMON`
- Implementation scope: `common`
- Claim tier: `diagnostic_only`
- Transfer source: `none`
- Config hash: `b4a49ab8169425e6d0344047faea156fdced5a7d6e48182f459240f2bb26417d`
- Sky support / mask status: `not_applicable_governance`
- Covariance / null mock status: `not_applicable_governance`
- Generating command: `/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/codex_harness/progress_report.py machine_readable/pr_backlog.yaml machine_readable/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints`
- Git commit / worktree state: `8da1d195976420fcbac655cb8845446d9ab5c3aa; dirty`
- Input hashes:
  - `machine_readable/pr_backlog.yaml:9693706872a5e13514c0eb3e4ca9dab9a281359edac4cda9877d26dae8c68f07`
  - `machine_readable/pr_status.yaml:97a2e372172ee89a1fc17c34dbd398874e527061ecd6e39b156dd60aac8efcaf`
- Caveats:
  - Progress percentages count DAG bookkeeping only.
  - This artifact cannot establish scientific readiness, native transfer validation, posterior support, or family identification.

- Completed PRs: 95/113 = 84.07%
- Dependency-weighted completion: 88.94%
- Critical path completion: 50/56 = 89.29%
- Critical path: PR-000 -> PR-003 -> PR-004 -> PR-010 -> PR-014 -> PR-050 -> PR-051 -> PR-052 -> PR-053 -> PR-054 -> PR-055 -> PR-060 -> PR-061 -> PR-062 -> PR-063 -> PR-064 -> PR-065 -> PR-066 -> PR-111 -> PR-114 -> PR-115 -> PR-116 -> PR-117 -> PR-118 -> PR-119 -> PR-121 -> PR-122 -> PR-123 -> PR-124 -> PR-125 -> PR-126 -> PR-127 -> PR-128 -> PR-131 -> PR-132 -> PR-133 -> PR-134 -> PR-135 -> PR-137 -> PR-138 -> PR-139 -> PR-140 -> PR-141 -> PR-142 -> PR-143 -> PR-144 -> PR-145 -> PR-146 -> PR-147 -> PR-148 -> PR-155 -> PR-162 -> PR-163 -> PR-164 -> PR-165 -> PR-166
- Blocked PRs: none
- Skipped PRs: none
- Dormant external PRs: PR-159, PR-160, PR-161, PR-162, PR-163, PR-164, PR-165, PR-166
- Unblocked next: PR-149, PR-151, PR-152, PR-153
- Replan required: no
- Replan reason: progress advanced; no replan required

Progress percentages count DAG bookkeeping only and are not scientific readiness evidence.
They do not validate native solver behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null calibration, morphology compatibility, or Bianchi family identification.

## Checkpoint 095 freeze-gate verdict (PR-148)

- Findings: 102 OPEN / 0 RESCUED (research_remediation_state.yaml sha f16d9754...); 0 downclaimed/rebuild_required miscounted as rescued.
- Data-phase review (PR-144..148): raw CF4 lineage authenticated (PR-144 manifest, byte ranges); injection coverage self-consistency + noise-only under-coverage discrimination shipped (PR-145/146); effective-N participation ratio reported (~82 of 800, PR-146); common-window GLS/MV difference predicted (PR-147); same-data joint covariance MEASURED and positive-definite (PR-148); stale-consumer scan GREEN (quarantine clean at each PR).
- Both CF4 P0s (C1-K5-MV-F1, C3-K5-VCORR-ML-F1): PR-145 numerical success alone does NOT close them. They are raised only to AWAITING NON-AUTHOR ADJUDICATION (PR-157); no self-authored closure.
- No detection / anomaly / geometry / Bianchi-family / global-tilt claim across PR-144..148. Green tests are propagation/coverage self-consistency, NOT observational validity.
- Verdict: freeze gate PASS at 95/113; proceed to Wave 19 (PR-149).
