# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base` only after reading:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-physics-math-audit/SKILL.md`
- `.agents/skills/htt-statistical-hardening/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`
- `docs/audits/jcap_prd_adversarial_audit_20260714/final_referee_report.md`
- `docs/audits/jcap_prd_adversarial_audit_20260714/executive_summary_ko.md`
- `docs/audits/jcap_prd_adversarial_audit_20260714/criticism_response_matrix.json`
- `docs/audits/jcap_prd_adversarial_audit_20260714/next_dag_candidates.json`
- `docs/generated/progress_checkpoints/checkpoint_065.md`

## Current state

- The active DAG is 65/65 complete: 100% by count, dependency weight, and
  critical path. This is bookkeeping only, not scientific readiness.
- The as-shipped manuscript decision is unanimous `REJECT` (1.0-1.5/10).
- A distinct pre-solver methods/negative-audit submission is only potentially
  defensible after major rebuild (5.0-6.5/10).
- Prior findings remain 55 `KNOWN_OPEN` (`P0 2 / P1 14 / P2 17 / P3 22`),
  with 14 audit gaps and 33 new open atomic deltas (`P1 22 / P2 11`).
- The advocate program contains 32 candidates, a 12-candidate bounded final
  CRAG, and a 102-row criticism-response matrix.
- No production scientific result or manuscript number was repaired by the
  audit. Raw `legacy/` and the two original GPT-5.6 ZIPs remain untracked.

## Authority boundary

There is no active next DAG card. `AUD-R01A` through `AUD-R05C` are staged proposals,
not authorized implementation work. Before starting one, add it through an
explicit DAG intake/review that assigns owner, dependencies, tests, claim
ceiling, decisive inputs, and kill conditions.

Recommended first intake is `AUD-R01A`: quarantine the two open P0-dependent
CF4 headline/correction paths and rebuild estimator/downstream propagation.
Its entry gate is authenticated CF4 row/group/selection lineage plus a
preregistered injection/coverage design. It may yield only estimator
validation or an identified-region result.

## Hard boundaries

- Do not implement a native low-ell Bianchi solver in this repository.
- Do not label external/AniCLASS output as native or validated transfer.
- Do not merge MIO diagnostics into HTT posterior/evidence semantics.
- Do not replace production numbers from audit-only sensitivity reruns.
- Keep every family/geometry counterfactual `hypothesis_only=true` and
  `public_use=false` until native atlas, matched masks/nulls/covariance,
  family equivalence, rank, and external validation gates all pass.

## Immediate verification

```bash
venv/bin/python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
venv/bin/python -B scripts/audits/jcap_prd_20260714.py validate --final
venv/bin/python -B -m pytest -p no:cacheprovider tests/contracts/test_jcap_prd_adversarial_audit.py -q
```
