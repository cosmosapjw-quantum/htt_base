<!-- checkpoint_meta {"completed": 90, "critical_path_percent_complete": 80.36, "dependency_weighted_percent_complete": 84.77, "percent_complete": 79.65, "replan_required": false, "total": 113} -->
# Progress checkpoint 090

## Artifact metadata

- Owner: `COMMON`
- Implementation scope: `common`
- Claim tier: `diagnostic_only`
- Transfer source: `none`
- Config hash: `b5a53d912895582c5d00c0f796b5c6195f57c0cefdb94984deb53402a7c00b33`
- Sky support / mask status: `not_applicable_governance`
- Covariance / null mock status: `not_applicable_governance`
- Generating command: `/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python scripts/codex_harness/progress_report.py machine_readable/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --write-checkpoint-dir docs/generated/progress_checkpoints`
- Git commit / worktree state: `f5bda7e621e7387fc8a978e0e97cf5dc2ad36284; dirty`
- Input hashes:
  - `machine_readable/pr_backlog.yaml:9693706872a5e13514c0eb3e4ca9dab9a281359edac4cda9877d26dae8c68f07`
  - `docs/codex_handoff/pr_status.yaml:f67148c016e47f2c049648ffc27e0f5564c07147728ba640411ba7dfc9d6bd2c`
- Caveats:
  - Progress percentages count DAG bookkeeping only.
  - This artifact cannot establish scientific readiness, native transfer validation, posterior support, or family identification.

- Completed PRs: 90/113 = 79.65%
- Dependency-weighted completion: 84.77%
- Critical path completion: 45/56 = 80.36%
- Critical path: PR-000 -> PR-003 -> PR-004 -> PR-010 -> PR-014 -> PR-050 -> PR-051 -> PR-052 -> PR-053 -> PR-054 -> PR-055 -> PR-060 -> PR-061 -> PR-062 -> PR-063 -> PR-064 -> PR-065 -> PR-066 -> PR-111 -> PR-114 -> PR-115 -> PR-116 -> PR-117 -> PR-118 -> PR-119 -> PR-121 -> PR-122 -> PR-123 -> PR-124 -> PR-125 -> PR-126 -> PR-127 -> PR-128 -> PR-131 -> PR-132 -> PR-133 -> PR-134 -> PR-135 -> PR-137 -> PR-138 -> PR-139 -> PR-140 -> PR-141 -> PR-142 -> PR-143 -> PR-144 -> PR-145 -> PR-146 -> PR-147 -> PR-148 -> PR-155 -> PR-162 -> PR-163 -> PR-164 -> PR-165 -> PR-166
- Blocked PRs: none
- Skipped PRs: none
- Dormant external PRs: PR-159, PR-160, PR-161, PR-162, PR-163, PR-164, PR-165, PR-166
- Unblocked next: PR-144, PR-149, PR-151, PR-152, PR-153
- Replan required: no
- Replan reason: progress advanced; no replan required

Progress percentages count DAG bookkeeping only and are not scientific readiness evidence.
They do not validate native solver behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null calibration, morphology compatibility, or Bianchi family identification.

## Checkpoint-090 statistical-foundation gate (PR-143)

Per the roadmap Checkpoint-090 instruction, authenticated data analysis may
begin only after PR-143. This gate records the required fields.

- **Method-ready count**: the integrated statistical foundation (the PR-141
  discrimination method under the PR-143 blind challenge) is method-ready on
  **6 of 7 DGP families** (known-null, local, global, systematic, weak-ID,
  dependent-mock) plus the computational-failure lane, and **BLOCKED on 1**
  (covariance-misspecified). Overall referee `method_verdict`: **block** (a
  single blocked family blocks the method for that criterion).
- **Failed / abstain count**: 1 blocked family (covariance-misspecified) — a
  genuine DIAGNOSTIC limitation: the linear-Gaussian PPC attributes the
  abstention to inadequacy only ~47% of the time. The method correctly
  ABSTAINS on the null, weak-ID, and dependent-mock families and never falsely
  discriminates.
- **Empirical size**: the measured null false-candidate rate over the 10-seed
  ensemble (150 null items) is **0.0067** — a small NON-ZERO value within the
  pre-registered level alpha = 0.10. It is reported as a measured size, never
  claimed to be exactly zero.
- **Empirical coverage**: simultaneous grid-conditional coverage was validated
  separately in PR-137 (Imbens-Manski + Bonferroni family-wise lower bound
  >= 0.94 at the least-favourable boundary); SBC rank uniformity in PR-138;
  identified-set classification in PR-136. These remain the coverage evidence;
  PR-143 adds the integrated size/recovery/abstention adjudication.
- **Independent referee verdict**: a NON-AUTHOR referee (distinct from the
  generator and the analyst) scored the blind, seed-sealed challenge and
  returned **block on covariance-misspecified**, recorded (not hidden) in the
  method-ready matrix.
- **Open P0 / P1**: **0**. Every P0/P1 surfaced by the PR-129..143 adversarial
  review lanes was fixed pre-commit (the PR-143 review fixed 3 P1 — a fake
  truth seal, a single-seed survivorship safety claim, and non-live guards).
- **Data readiness**: the statistical foundation is method-calibrated for the
  six ready families; any data PR requiring covariance-misspecification
  DIAGNOSIS from this method alone is BLOCKED. **Independently, PR4 data
  acquisition / reduction / analysis is OUT OF SCOPE by user directive and is
  not begun; 102 findings remain OPEN / 0 RESCUED.**

**Passing the synthetic challenge is METHOD READINESS, not observed validity.**
The measured size, recovery, abstention, and computational-failure results are
model/computation-conditional calibration mechanics; none is an observation, a
detection, a family identification, or a geometry claim. Gate verdict: **PASS
(with covariance-misspecification diagnosis BLOCKED and recorded).**
