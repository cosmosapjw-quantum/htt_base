# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base`.

Pre-read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-xqpi-fg-formalism/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-031.md`
- `docs/generated/progress_checkpoints/checkpoint_025.md`
- `docs/generated/progress_checkpoints/progress_scoreboard.md`
- `docs/generated/status_snapshot.json`

Current state:

- Completed PRs: PR-000, PR-001, PR-002, PR-003, PR-004, PR-005, PR-020,
  PR-010, PR-021, PR-011, PR-013, PR-014, PR-040, PR-012, PR-022, PR-070,
  PR-015, PR-050, PR-041, PR-023, PR-071, PR-080, PR-030, PR-113, PR-051,
  PR-042, PR-072, PR-081, and PR-031.
- Latest progress after PR-031: 29/62 = 46.77% complete;
  dependency-weighted completion = 51.79%; critical path = 7/21 = 33.33%.
- Checkpoint 025 remains the latest checkpoint; the next completed PR will
  reach 30 completed PRs and must run the five-PR checkpoint procedure.
- Latest unblocked candidates: `PR-052`, `PR-043`, `PR-073`, `PR-082`, and
  `PR-032`.

Important PR-031 boundary:

- `common.semantic_guards.admissibility_status` and
  `common.semantic_guards.source_propagation_status` are COMMON-owned guard
  metadata only.
- Source, propagation, and observable status are separate; source status never
  auto-promotes observable status.
- `attach_semantic_caveats()` preserves artifact owner/scope and rejects
  manifest claim tiers above the semantic record ceiling.
- `SourcePropagationStatus` computes only diagnostic-only or blocked ceilings;
  it cannot mint conditional or validated claims.
- The COMMON no-overclaim scanner now catches source-to-observable conflation
  across punctuation and adjacent wrapped prose.
- PR-031 does not provide statistical observable validation, null/mock support,
  mask/covariance support, response-rank/equivalence evidence, transfer
  provenance, native solver validation, HTT evidence, MIO certificates,
  morphology compatibility, or geometry/family evidence.

Rules:

- Do not implement a native low-ell Bianchi solver in this repo.
- Do not label external transfer as native.
- Do not merge MIO diagnostics with HTT posterior/evidence semantics.
- Do not make Bianchi family-ID claims before native low-ell morphology atlas
  plus null/mask/covariance/equivalence/rank/PPC gates.
- Q/F/Pi/G_F PRs must consume the PR-051 MIO contract directly.
- After the next completed PR, run:
  `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5`.

Immediate commands:

```bash
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
venv/bin/python scripts/codex_harness/run_subset.py package
venv/bin/python scripts/codex_harness/run_subset.py smoke
```
