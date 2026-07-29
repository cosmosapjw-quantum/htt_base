# Next Session Prompt

Verify or continue after the PR-255 anchored-response-geometry change-set from
the isolated worktree
`/home/cosmosapjw/worktrees/htt-anchored-response-pr255-20260729`, branch
`changeset/pr255-anchored-response-geometry`. Do not move, checkout, or clean
the canonical PR-151 acquisition path.

Read first:

- `AGENTS.md`
- `.agent-harness/generated/CONTEXT_PACK.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `.agents/skills/htt-physics-math-audit/SKILL.md`
- `.agents/skills/htt-statistical-hardening/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `docs/research_program/premise_anchor/pr255_spec.yaml`
- `docs/research_program/premise_anchor/pr255_publication_policy.json`
- `docs/PR_DELTAS/pr-255.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`

## Current state

- Baseline target:
  `origin/research/pr04-multicomponent@090525951cc30ad29da7fa8ae0a11bd4553f5b4f`.
- Internal work unit `PR-255`, change-set
  `CS-PR255-RESPONSE-GEOMETRY`, publication group
  `PG-PR255-RESPONSE-GEOMETRY`.
- Active DAG: 205 cards, 150 conditionally complete (73.17%),
  dependency-weighted 79.69%, critical-path proxy 85.71%. PR-151 remains the
  background acquisition and PR-172 remains blocked. Checkpoint 150 exists.
- PR-255 implements supported-quotient anchored response geometry,
  same-covariance Schur information, structural contraction states, a typed
  eight-cell synthetic nonlinearity phase report, and a direct-Fisher oracle.
- Candidates r1 through r4 under
  `.agent-harness/runs/premise-anchor-pr255-candidate-r*-20260729/` are
  preserved FAIL reviews. The exact closeout authority is only a PASS run at
  `.agent-harness/runs/premise-anchor-pr255-candidate-r5-20260729/` plus its
  candidate seal and latest-target integration receipt. Verify all identities
  before relying on the status transition.
- No partial PR-151 data, observational catalogue, external/native transfer,
  old Rust science result, posterior, geometry, or family result was used.

## Authority boundary

The owner authorized one commit and push for the current coherent PR-255
candidate. That authority does not include PR creation, approval, merge, or
other GitHub PR mutation. Ordinary agents never act as publisher.

Before continuing:

1. verify the branch is clean and the pushed SHA equals the candidate seal;
2. verify all three registered review results and coverage matrices;
3. verify the integration receipt against the same target and candidate;
4. if any tracked byte changed, invalidate all evidence and do not reuse it;
5. if PR-255 has been human-reviewed and merged and its branch deleted, create
   one isolated PR-256 worktree at the latest target. Otherwise stop.

## Immediate verification

```bash
PYTHONPATH="$PWD/htt/src:$PWD/htt:$PWD/htt/htt" /home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B -m pytest -p no:cacheprovider -q htt/src/common/test_anchored_response_geometry.py tests/pr_cards/test_pr_255_anchored_response_geometry.py
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B scripts/codex_harness/run_pr255_response_geometry_benchmark.py
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B scripts/codex_harness/run_pr255_response_geometry_oracle.py
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B .agent-harness/scripts/validate_harness.py
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --strict
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check
/home/cosmosapjw/Dropbox/bianchi/htt_base/venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5
git diff --check
```

Do not start PR-256 before PR-255 merge and branch deletion. Do not start
PR-257 before PR-256, or PR-258 before PR-256 and PR-257. Do not alter PR-151
acquisition state, run partial-data science, implement a native solver, or
promote any observational, transfer, geometry, family, or publication claim
from this diagnostic methodology.
